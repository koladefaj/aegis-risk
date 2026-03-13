from redis.asyncio import Redis
from aegis_shared.utils.logging import get_logger

logger = get_logger("redis")

redis_client: Redis | None = None


def init_redis(redis_url: str) -> None:
    global redis_client

    redis_client = Redis.from_url(
        redis_url,
        decode_response=True,
    )

    redis_client.ping()

    logger.info("Redis client initialized")

def get_redis() -> Redis:
    if redis_client is None:
        logger.error("Redis not initialized")
        raise RuntimeError("Redis not initialzied")
    
    return redis_client


