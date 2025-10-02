from redis import asyncio as aioredis
from config import CONFIG

_redis = None


async def get_redis():
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(
            f"redis://{CONFIG.REDIS_HOST}:{CONFIG.REDIS_PORT}",
            db=CONFIG.REDIS_DB,
            password=CONFIG.REDIS_PASSWORD or None,
            encoding="utf-8",
        )
    return _redis


async def redis_get(key: str):
    redis = await get_redis()
    return await redis.get(key)


async def redis_set(key: str, value: str, expire: int = 300):
    redis = await get_redis()
    await redis.set(key, value, ex=expire)
