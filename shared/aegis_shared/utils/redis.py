from redis.asyncio import Redis
from aegis_shared.utils.logging import get_logger

logger = get_logger("redis")

redis_client: Redis | None = None


async def init_redis(redis_url: str) -> None:
    global redis_client

    redis_client = Redis.from_url(
        redis_url,
        decode_responses=True,
    )

    await redis_client.ping()

    logger.info("Redis client initialized")

def get_redis() -> Redis:
    if redis_client is None:
        logger.error("Redis not initialized")
        raise RuntimeError("Redis not initialzied")
    
    return redis_client

async def close_redis() -> None:
    """Close the connection pool on service shutdown.
    
    Redis itself keeps running — this just releases this service's
    connections back. Without this, connections leak and Redis will
    eventually hit max_clients.
    """
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None
        logger.info("redis_closed")
