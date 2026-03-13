from redis.asyncio import Redis

def get_redis(redis_url: str) -> Redis:
    
    redis_client = Redis.from_url(
        redis_url,
        decode_response=True,
    )

    return redis_client