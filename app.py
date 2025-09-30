from datetime import timedelta
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.concurrency import asynccontextmanager
from fastapi.security import OAuth2PasswordRequestForm
import uvicorn
from api import report, query, admin
from tortoise import Tortoise
from config import CONFIG
from starlette.types import ASGIApp, Scope, Receive, Send
from fastapi.logger import logger

from utils.security import authenticate_user, create_access_token, require_login


class AuthMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            if cookie_header := headers.get(b"cookie"):
                cookie_str = cookie_header.decode()
                cookies = {}
                for item in cookie_str.split(";"):
                    if "=" in item:
                        k, v = item.strip().split("=", 1)
                        cookies[k.strip()] = v.strip()

                auth_token = cookies.get("Authorization")
                if auth_token and b"authorization" not in headers:
                    if not auth_token.startswith("Bearer "):
                        auth_token = f"Bearer {auth_token}"
                    scope["headers"].append((b"authorization", auth_token.encode()))

        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await Tortoise.init(db_url="sqlite://cloudban.db", modules={"models": ["models"]})
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


if CONFIG.DEBUG:
    app = FastAPI(lifespan=lifespan)
else:
    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

app.add_middleware(AuthMiddleware)  # 认证中间件
# 注册路由
app.include_router(
    report.router,
    prefix="/api",
    tags=["上报接口"],
)
app.include_router(
    query.router,
    prefix="/api",
    tags=["查询接口"],
)
app.include_router(
    admin.router,
    prefix="/api/admin",
    tags=["后台接口"],
    dependencies=[Depends(require_login)],
)


@app.post("/login")
async def _(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=CONFIG.ACCESS_TOKEN_EXPIRE_MINUTES)

    response.set_cookie(
        key="Authorization",
        value=create_access_token(
            data={"sub": user}, expires_delta=access_token_expires
        ),
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
    )
    return {"message": "登录成功"}


if __name__ == "__main__":
    if CONFIG.DEBUG:
        logger.info("*************************************************************")
        logger.info(f"文档地址: http://{CONFIG.HOST}:{CONFIG.PORT}/docs")
        logger.info(f"ReDoc文档地址: http://{CONFIG.HOST}:{CONFIG.PORT}/redoc")
        logger.info("*************************************************************")
    uvicorn.run(
        app,
        host=CONFIG.HOST,
        port=CONFIG.PORT,
    )
