from redis.asyncio import Redis
from config import config

async def init_redis(db: int = 0) -> Redis:
    redis = Redis(host=config.DB_HOST,
                  port=config.REDIS_PORT,
                  db=db,
                  password=config.REDIS_PASSWORD,
                  decode_responses=True)
    try:
        await redis.ping()
    except Exception as e:
        raise ConnectionError(f"Не удалось подключиться к Redis: {e}")
    return redis
