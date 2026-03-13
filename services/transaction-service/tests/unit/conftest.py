"""Unit test conftest — fixtures for isolated unit testing with fully mocked dependencies."""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.idempotency_service import IdempotencyService
from app.services.transaction_service import TransactionBusinessService
from app.grpc_server.servicer import TransactionServicer


# ─────────────────────────────────────
# IDEMPOTENCY SERVICE (with mock redis)
# ─────────────────────────────────────

@pytest.fixture
def idempotency_service(mock_redis):
    """IdempotencyService backed by mock Redis."""
    service = IdempotencyService.__new__(IdempotencyService)
    service.redis_client = mock_redis
    return service


# ─────────────────────────────────────
# TRANSACTION BUSINESS SERVICE (mocked)
# ─────────────────────────────────────

@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def transaction_service(mock_repo, mock_sqs_publisher):
    """TransactionBusinessService with mocked repo and publisher."""
    service = TransactionBusinessService.__new__(TransactionBusinessService)
    service.repo = mock_repo
    service.publisher = mock_sqs_publisher
    return service


# ─────────────────────────────────────
# GRPC SERVICER (mocked dependencies)
# ─────────────────────────────────────

@pytest.fixture
def mock_transaction_service():
    return AsyncMock(spec=TransactionBusinessService)


@pytest.fixture
def servicer(mock_transaction_service, mock_idempotency_service):
    """TransactionServicer with mocked business service and idempotency."""
    return TransactionServicer(
        transaction_service=mock_transaction_service,
        idempotency_service=mock_idempotency_service,
    )
