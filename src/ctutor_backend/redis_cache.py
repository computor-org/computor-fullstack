import os
from aiocache import Cache

_redis_cache = Cache(
    Cache.REDIS,
    endpoint=os.environ.get("REDIS_URL"),
    port=6379,
    password=os.environ.get("REDIS_PASSWORD"),
    pool_max_size=10,
    db=0
)

async def get_redis_client() -> Cache:
    return _redis_cache