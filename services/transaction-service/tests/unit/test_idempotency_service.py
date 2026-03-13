"""Unit tests for IdempotencyService."""

import json
import pytest
import asyncio


@pytest.mark.asyncio
async def test_check_returns_none_when_not_cached(idempotency_service, mock_redis):
    """Returns None when key doesn't exist in Redis."""

    result = await idempotency_service.check("new-key")

    assert result is None
    mock_redis.get.assert_called_once_with("idempotency:new-key")


@pytest.mark.asyncio
async def test_check_returns_cached_data(idempotency_service, mock_redis):
    """Returns parsed JSON when key exists in Redis."""

    cached = {"transaction_id": "123", "status": "COMPLETED"}
    await mock_redis.set("idempotency:existing-key", json.dumps(cached))

    result = await idempotency_service.check("existing-key")

    assert result == cached
    mock_redis.get.assert_called_once_with("idempotency:existing-key")


@pytest.mark.asyncio
async def test_check_fails_open_on_redis_error(idempotency_service, mock_redis):
    """Returns None (fail-open) when Redis is down."""

    async def _fail(*args, **kwargs):
        raise Exception("redis connection refused")
    mock_redis.get = _fail

    result = await idempotency_service.check("any-key")

    assert result is None


@pytest.mark.asyncio
async def test_store_caches_response(idempotency_service, mock_redis):
    """Stores response with TTL in Redis."""

    data = {"transaction_id": "123", "status": "RECEIVED"}

    await idempotency_service.store("store-key", data)

    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args[0]
    assert call_args[0] == "idempotency:response:store-key"
    assert call_args[1] == 86400  # TTL


@pytest.mark.asyncio
async def test_store_fails_silently_on_redis_error(idempotency_service, mock_redis):
    """Store failure is non-fatal — no exception raised."""

    async def _fail(*args, **kwargs):
        raise Exception("redis write error")
    mock_redis.setex = _fail

    # Should not raise
    await idempotency_service.store("fail-key", {"data": "value"})


@pytest.mark.asyncio
async def test_check_handles_corrupt_json(idempotency_service, mock_redis):
    """Returns None when cached value is not valid JSON."""

    await mock_redis.set("idempotency:corrupt-key", "not-valid-json{{")

    result = await idempotency_service.check("corrupt-key")

    assert result is None


@pytest.mark.asyncio
async def test_acquire_lock_success(idempotency_service, mock_redis):
    """acquire_lock returns True when lock is acquired."""

    result = await idempotency_service.acquire_lock("lock-key")

    assert result is True


@pytest.mark.asyncio
async def test_acquire_lock_already_held(idempotency_service, mock_redis):
    """acquire_lock returns False when lock is already held."""

    await mock_redis.set("idempotency:lock:lock-key", "processing")

    result = await idempotency_service.acquire_lock("lock-key")

    assert result is False


@pytest.mark.asyncio
async def test_acquire_lock_fails_open(idempotency_service, mock_redis):
    """acquire_lock returns True (fail-open) when Redis errors."""

    async def _fail(*args, **kwargs):
        raise Exception("redis error")
    mock_redis.set = _fail

    result = await idempotency_service.acquire_lock("lock-key")

    assert result is True


@pytest.mark.asyncio
async def test_concurrent_checks(idempotency_service):
    """Concurrent check calls don't explode."""

    async def check():
        return await idempotency_service.check("concurrent-key")

    tasks = [check() for _ in range(50)]
    results = await asyncio.gather(*tasks)

    assert all(r is None for r in results)