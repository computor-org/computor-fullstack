import os
from aiocache import RedisCache

_redis_cache = RedisCache(
    endpoint=os.environ.get("REDIS_URL"),
    port=6379,
    password=os.environ.get("REDIS_PASSWORD"),
    pool_max_size=10,
    db=0
)

async def get_redis_client() -> RedisCache:
    return _redis_cache