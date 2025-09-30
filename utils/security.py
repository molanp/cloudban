from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from config import CONFIG


SECRET_KEY = CONFIG.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def authenticate_user(username: str, password: str):
    if username != CONFIG.USERNAME or password != CONFIG.PASSWORD:
        return False
    return CONFIG.USERNAME


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError as e:
        raise credentials_exception from e
    if username == CONFIG.USERNAME:
        return username
    else:
        raise credentials_exception


def is_login(Authorization: str):
    try:
        if not Authorization:
            return False
        # 检查是否是 Bearer token 格式
        if not Authorization.startswith("Bearer "):
            return False
        # 提取 token
        token = Authorization.split(" ")[1]
        return get_current_user(token)
    except Exception:
        return False


def require_login(Authorization: str = Header(...)):
    if not Authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if user := is_login(Authorization):
        return user
    else:
        raise HTTPException(status_code=403, detail="Invalid token")
