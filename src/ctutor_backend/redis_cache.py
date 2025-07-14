import os
from aiocache import Cache

# Get Redis configuration from environment
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')

_redis_cache = Cache(
    Cache.REDIS,
    endpoint=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD if REDIS_PASSWORD else None,
    pool_max_size=10,
    db=0
)

async def get_redis_client() -> Cache:
    return _redis_cache