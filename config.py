from pathlib import Path
from pydantic import BaseModel
import ujson
import secrets

Root = Path.cwd()


class Config(BaseModel):
    HOST: str = "127.0.0.1"
    """监听地址"""
    PORT: int = 8080
    """端口"""
    DEBUG: bool = False
    """是否开启调试模式"""
    SECRET_KEY: str = secrets.token_hex(16)
    """密钥"""
    USERNAME: str = "admin"
    """用户名"""
    PASSWORD: str = "admin"
    """密码"""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 300
    """token过期时间"""


try:
    with open(Root / "config.json", encoding="utf8") as file:
        config = ujson.load(file)
    CONFIG = Config(**config)
except Exception:
    CONFIG = Config()
finally:
    with open(Root / "config.json", "w", encoding="utf8") as file:
        file.write(ujson.dumps(CONFIG.model_dump(), indent=4, ensure_ascii=False))