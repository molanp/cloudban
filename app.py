from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
import uvicorn
from api import report, query, admin
from tortoise import Tortoise
from config import CONFIG

# from fastapi.staticfiles import StaticFiles
from starlette.types import ASGIApp, Scope, Receive, Send

# 挂载后台前端
# app.mount("/admin", StaticFiles(directory="public/admin", html=True), name="admin")


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
async def lifespan(app: FastAPI):
    # 初始化 Tortoise ORM
    await Tortoise.init(db_url="sqlite://cloudban.db", modules={"models": ["models"]})
    await Tortoise.generate_schemas()
    yield
    # 应用关闭时的清理代码
    await Tortoise.close_connections()


if CONFIG.DEBUG:
    app = FastAPI(lifespan=lifespan)
else:
    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

app.add_middleware(AuthMiddleware)  # 认证中间件
# 注册路由
app.include_router(report.router, prefix="/api", tags=["上报接口"])
app.include_router(query.router, prefix="/api", tags=["查询接口"])
app.include_router(admin.router, prefix="/api/admin", tags=["后台接口"])


if __name__ == "__main__":
    if CONFIG.DEBUG:
        print(f"文档地址: http://{CONFIG.HOST}:{CONFIG.PORT}/docs")
        print(f"ReDoc文档地址: http://{CONFIG.HOST}:{CONFIG.PORT}/redoc")
    uvicorn.run(
        app,
        host=CONFIG.HOST,
        port=CONFIG.PORT,
    )
