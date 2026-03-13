"""Integration test conftest — patches get_session to use test DB."""

import pytest
from unittest.mock import patch
from contextlib import asynccontextmanager

from app.repo.transaction_repo import TransactionRepository
from app.services.transaction_service import TransactionBusinessService
from app.queue.sqs_publisher import SQSPublisher


@pytest.fixture
def patched_get_session(async_session_factory):
    """Patch app.db.session.get_session to use the test database."""

    @asynccontextmanager
    async def _test_get_session():
        async with async_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    with patch("app.repo.transaction_repo.get_session", _test_get_session):
        yield _test_get_session


@pytest.fixture
def repo(patched_get_session):
    """TransactionRepository using the test database."""
    return TransactionRepository()


@pytest.fixture
def integration_service(patched_get_session, mock_sqs_publisher):
    """TransactionBusinessService using real DB repo + mocked SQS."""
    service = TransactionBusinessService.__new__(TransactionBusinessService)
    service.repo = TransactionRepository()
    service.publisher = mock_sqs_publisher
    return service
