"""Root conftest — shared fixtures for all transaction-service tests."""

# Pre-load common.proto into the protobuf descriptor pool before any
# service module imports transaction_pb2 (which depends on it).
import aegis_shared.generated.common_pb2  # noqa: F401

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from datetime import datetime, UTC
from uuid import uuid4

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, UUID

@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(type_, compiler, **kw):
    return 'JSON'

@compiles(UUID, 'sqlite')
def compile_uuid_sqlite(type_, compiler, **kw):
    return 'VARCHAR(36)'

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.services.idempotency_service import IdempotencyService
from app.queue.sqs_publisher import SQSPublisher


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ─────────────────────────────────────
# DATABASE ENGINE (shared across tests)
# ─────────────────────────────────────

@pytest.fixture(scope="session")
def engine():
    return create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="session")
def async_session_factory(engine):
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest.fixture(autouse=True)
async def setup_db(engine):
    """Create all tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(async_session_factory):
    async with async_session_factory() as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
async def close_engine(engine):
    yield
    await engine.dispose()


# ─────────────────────────────────────
# REDIS MOCK (in-memory dict backend)
# ─────────────────────────────────────

@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    storage: dict[str, str] = {}

    async def get_val(key):
        return storage.get(key)

    async def set_val(key, value, *args, **kwargs):
        nx = kwargs.get('nx', False)
        if nx and key in storage:
            return None
        storage[key] = value
        return True

    async def setex_val(key, ttl, value):
        storage[key] = value

    async def delete_val(key):
        storage.pop(key, None)

    redis.get = AsyncMock(side_effect=get_val)
    redis.set = AsyncMock(side_effect=set_val)
    redis.setex = AsyncMock(side_effect=setex_val)
    redis.delete = AsyncMock(side_effect=delete_val)
    redis.ping = AsyncMock(return_value=True)
    redis.aclose = AsyncMock()

    return redis


# ─────────────────────────────────────
# MOCK SERVICES
# ─────────────────────────────────────

@pytest.fixture
def mock_idempotency_service():
    service = AsyncMock(spec=IdempotencyService)
    service.check.return_value = None
    service.store.return_value = None
    service.acquire_lock.return_value = True
    return service


@pytest.fixture
def mock_sqs_publisher():
    publisher = AsyncMock(spec=SQSPublisher)
    publisher.publish_transaction_queued.return_value = "mock-message-id"
    return publisher


# ─────────────────────────────────────
# GRPC CONTEXT MOCK
# ─────────────────────────────────────

@pytest.fixture
def grpc_context():
    """Mock gRPC service context that simulates context.abort() by raising."""
    import grpc

    context = AsyncMock()

    async def mock_abort(code, details):
        error = grpc.aio.AbortError(code, details)
        raise error

    context.abort = AsyncMock(side_effect=mock_abort)
    context.set_code = MagicMock()
    context.set_details = MagicMock()
    context.code.return_value = None
    context.invocation_metadata.return_value = []

    return context


# ─────────────────────────────────────
# SAMPLE TEST DATA
# ─────────────────────────────────────

@pytest.fixture
def sample_transaction_data():
    """Standard transaction data for tests."""
    return {
        "idempotency_key": "test-key-1234567890",
        "amount": Decimal("100.00"),
        "currency": "USD",
        "sender_id": "sender-001",
        "receiver_id": "receiver-001",
        "sender_country": "US",
        "receiver_country": "GB",
        "device_fingerprint": "fp-abc123",
        "ip_address": "192.168.1.1",
        "channel": "web",
    }


@pytest.fixture
def sample_grpc_request(sample_transaction_data):
    """Mock gRPC CreateTransactionRequest."""
    request = MagicMock()
    request.idempotency_key = sample_transaction_data["idempotency_key"]
    request.amount = float(sample_transaction_data["amount"])
    request.currency = sample_transaction_data["currency"]
    request.sender_id = sample_transaction_data["sender_id"]
    request.receiver_id = sample_transaction_data["receiver_id"]
    request.sender_country = sample_transaction_data["sender_country"]
    request.receiver_country = sample_transaction_data["receiver_country"]
    request.device_fingerprint = sample_transaction_data["device_fingerprint"]
    request.ip_address = sample_transaction_data["ip_address"]
    request.channel = sample_transaction_data["channel"]
    return request