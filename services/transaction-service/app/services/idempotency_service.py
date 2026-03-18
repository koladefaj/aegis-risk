"""Idempotency service — Redis-backed cache for preventing duplicate processing."""

import json
from redis.asyncio import Redis
from aegis_shared.utils.redis import get_redis
from aegis_shared.utils.logging import get_logger

logger = get_logger("idempotency_service")

IDEMPOTENCY_TTL_SECONDS = 86400  # 24 hours
PROCESSING_TTL_SECONDS = 60  # lock expiry


class IdempotencyService:
    """Redis-backed idempotency check for transactions.

    Caches transaction responses by idempotency_key to prevent
    duplicate processing. TTL ensures cache doesn't grow unbounded.
    """

    def __init__(self, redis_client: Redis):
        self.redis_client = redis_client

    async def acquire_lock(self, idempotency_key: str) -> bool:
        """
        Attempt to acquire processing lock.
        
        Returns:
            True if lock acquired (safe to process)
            False if another request is already processing
        """
        key = f"idempotency:lock:{idempotency_key}"

        try:
            result = await self.redis_client.set(
                key,
                "processing",
                nx=True,
                ex=PROCESSING_TTL_SECONDS,
            )

            return result is True
        except Exception as e:
            logger.error("idempotency_lock_failed", error=str(e))
            return True

    async def check(self, idempotency_key: str) -> dict | None:
        """Check if an idempotency key has been seen before.

        Args:
            idempotency_key: Client-provided unique key.

        Returns:
            Cached response dict if duplicate, None if new.
        """
        key = f"idempotency:{idempotency_key}"
        try:
            cached = await self.redis_client.get(key)
            if cached:
                logger.info("idempotency_cache_hit", idempotency_key=idempotency_key)
                return json.loads(cached)
            return None
        except Exception as e:
            logger.error("idempotency_check_failed", error=str(e))
            return None

    async def store(self, idempotency_key: str, response: dict) -> None:
        """Store a response for an idempotency key.

        Args:
            idempotency_key: Client-provided unique key.
            response: Response dict to cache.
        """
        key = f"idempotency:{idempotency_key}"
        try:
            await self.redis_client.setex(
                key,
                IDEMPOTENCY_TTL_SECONDS,
                json.dumps(response, default=str),
            )
            logger.info("idempotency_cached", idempotency_key=idempotency_key)
        except Exception as e:
            logger.error("idempotency_store_failed", error=str(e))


    async def close(self) -> None:
        """Close Redis connection. Call during app shutdown."""
        await self.redis_client.aclose()