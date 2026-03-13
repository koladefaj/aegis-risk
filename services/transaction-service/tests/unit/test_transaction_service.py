"""Unit tests for TransactionBusinessService."""

import pytest
from decimal import Decimal
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from aegis_shared.enums import TransactionStatus
from aegis_shared.exceptions import DuplicateTransactionError


@pytest.mark.asyncio
async def test_create_new_transaction(transaction_service, mock_repo, mock_sqs_publisher, sample_transaction_data):
    """Happy path — new transaction is persisted and event published."""

    fake_txn = MagicMock()
    fake_txn.transaction_id = uuid4()
    fake_txn.idempotency_key = sample_transaction_data["idempotency_key"]
    fake_txn.amount = sample_transaction_data["amount"]
    fake_txn.currency = sample_transaction_data["currency"]
    fake_txn.sender_id = sample_transaction_data["sender_id"]
    fake_txn.receiver_id = sample_transaction_data["receiver_id"]
    fake_txn.sender_country = sample_transaction_data["sender_country"]
    fake_txn.receiver_country = sample_transaction_data["receiver_country"]
    fake_txn.status = TransactionStatus.RECEIVED.value
    fake_txn.created_at = datetime.now(UTC)
    fake_txn.device_fingerprint = sample_transaction_data["device_fingerprint"]
    fake_txn.ip_address = sample_transaction_data["ip_address"]
    fake_txn.channel = sample_transaction_data["channel"]

    mock_repo.find_by_idempotency_key.return_value = None
    mock_repo.create.return_value = fake_txn

    result = await transaction_service.create(**sample_transaction_data)

    assert result.already_existed is False
    assert result.status == TransactionStatus.RECEIVED.value
    assert result.currency == "USD"
    mock_repo.create.assert_called_once()
    mock_sqs_publisher.publish_transaction_queued.assert_called_once()


@pytest.mark.asyncio
async def test_create_duplicate_same_params(transaction_service, mock_repo, sample_transaction_data):
    """Idempotent replay — same key + same params returns existing transaction."""

    existing = MagicMock()
    existing.transaction_id = uuid4()
    existing.idempotency_key = sample_transaction_data["idempotency_key"]
    existing.amount = sample_transaction_data["amount"]
    existing.currency = sample_transaction_data["currency"]
    existing.sender_id = sample_transaction_data["sender_id"]
    existing.receiver_id = sample_transaction_data["receiver_id"]
    existing.sender_country = sample_transaction_data["sender_country"]
    existing.receiver_country = sample_transaction_data["receiver_country"]
    existing.status = TransactionStatus.RECEIVED.value
    existing.created_at = datetime.now(UTC)

    mock_repo.find_by_idempotency_key.return_value = existing

    result = await transaction_service.create(**sample_transaction_data)

    assert result.already_existed is True
    assert str(result.transaction_id) == str(existing.transaction_id)
    mock_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_duplicate_different_params(transaction_service, mock_repo, sample_transaction_data):
    """Strict idempotency — same key but different params raises DuplicateTransactionError."""

    existing = MagicMock()
    existing.transaction_id = uuid4()
    existing.idempotency_key = sample_transaction_data["idempotency_key"]
    existing.amount = Decimal("999.99")  # <-- different amount
    existing.currency = "EUR"  # <-- different currency
    existing.sender_id = sample_transaction_data["sender_id"]
    existing.receiver_id = sample_transaction_data["receiver_id"]
    existing.sender_country = sample_transaction_data["sender_country"]
    existing.receiver_country = sample_transaction_data["receiver_country"]
    existing.status = TransactionStatus.RECEIVED.value
    existing.created_at = datetime.now(UTC)

    mock_repo.find_by_idempotency_key.return_value = existing

    with pytest.raises(DuplicateTransactionError):
        await transaction_service.create(**sample_transaction_data)

    mock_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_publish_failure_still_returns(transaction_service, mock_repo, mock_sqs_publisher, sample_transaction_data):
    """SQS failure is non-fatal — transaction is still returned."""

    fake_txn = MagicMock()
    fake_txn.transaction_id = uuid4()
    fake_txn.idempotency_key = sample_transaction_data["idempotency_key"]
    fake_txn.amount = sample_transaction_data["amount"]
    fake_txn.currency = sample_transaction_data["currency"]
    fake_txn.sender_id = sample_transaction_data["sender_id"]
    fake_txn.receiver_id = sample_transaction_data["receiver_id"]
    fake_txn.sender_country = sample_transaction_data["sender_country"]
    fake_txn.receiver_country = sample_transaction_data["receiver_country"]
    fake_txn.status = TransactionStatus.RECEIVED.value
    fake_txn.created_at = datetime.now(UTC)
    fake_txn.device_fingerprint = ""
    fake_txn.ip_address = ""
    fake_txn.channel = "web"

    mock_repo.find_by_idempotency_key.return_value = None
    mock_repo.create.return_value = fake_txn
    mock_sqs_publisher.publish_transaction_queued.side_effect = RuntimeError("SQS down")

    result = await transaction_service.create(**sample_transaction_data)

    # Should still return successfully even though publish failed
    assert result is not None
    assert result.status == TransactionStatus.RECEIVED.value


@pytest.mark.asyncio
async def test_get_by_id_found(transaction_service, mock_repo):
    """get_by_id returns TransactionResponse when found."""

    txn_id = uuid4()
    fake_txn = MagicMock()
    fake_txn.transaction_id = txn_id
    fake_txn.idempotency_key = "key-1234567890"
    fake_txn.amount = Decimal("50.00")
    fake_txn.currency = "USD"
    fake_txn.sender_id = "s1"
    fake_txn.receiver_id = "r1"
    fake_txn.sender_country = "US"
    fake_txn.receiver_country = "GB"
    fake_txn.status = TransactionStatus.RECEIVED.value
    fake_txn.created_at = datetime.now(UTC)
    fake_txn.updated_at = None

    mock_repo.find_by_id.return_value = fake_txn

    result = await transaction_service.get_by_id(str(txn_id))

    assert result is not None
    assert result.transaction_id == txn_id


@pytest.mark.asyncio
async def test_get_by_id_not_found(transaction_service, mock_repo):
    """get_by_id returns None when not found."""

    mock_repo.find_by_id.return_value = None

    result = await transaction_service.get_by_id(str(uuid4()))

    assert result is None


@pytest.mark.asyncio
async def test_update_status_delegates_to_repo(transaction_service, mock_repo):
    """update_status passes through to repo correctly."""

    txn_id = str(uuid4())
    expected = {
        "transaction_id": txn_id,
        "previous_status": "RECEIVED",
        "new_status": "PROCESSING",
        "success": True,
    }
    mock_repo.update_status.return_value = expected

    result = await transaction_service.update_status(txn_id, "PROCESSING", "Starting analysis")

    import uuid
    mock_repo.update_status.assert_called_once_with(uuid.UUID(txn_id), "PROCESSING", "Starting analysis")
    assert result == expected
