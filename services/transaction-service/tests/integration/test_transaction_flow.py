"""Integration tests — end-to-end transaction flows using real DB + mocked SQS."""

import pytest
from decimal import Decimal
from datetime import datetime, UTC

from aegis_shared.enums import TransactionStatus
from aegis_shared.exceptions import DuplicateTransactionError


@pytest.mark.asyncio
async def test_full_create_and_retrieve_flow(integration_service, sample_transaction_data):
    """Create a transaction, then retrieve it by ID — full round trip."""

    result = await integration_service.create(**sample_transaction_data)

    assert result.already_existed is False
    assert result.status == TransactionStatus.RECEIVED.value
    assert result.currency == "USD"
    assert result.sender_id == sample_transaction_data["sender_id"]

    # Now retrieve it
    fetched = await integration_service.get_by_id(str(result.transaction_id))

    assert fetched is not None
    assert fetched.transaction_id == result.transaction_id
    assert fetched.amount == sample_transaction_data["amount"]


@pytest.mark.asyncio
async def test_create_and_status_update_flow(integration_service, sample_transaction_data):
    """Create → update to PROCESSING → update to COMPLETED."""

    result = await integration_service.create(**sample_transaction_data)
    txn_id = str(result.transaction_id)

    # Transition to PROCESSING
    update1 = await integration_service.update_status(txn_id, TransactionStatus.PROCESSING.value, "Analyzing")

    assert update1["success"] is True
    assert update1["new_status"] == TransactionStatus.PROCESSING.value

    # Transition to COMPLETED
    update2 = await integration_service.update_status(txn_id, TransactionStatus.COMPLETED.value, "Clean")

    assert update2["success"] is True
    assert update2["new_status"] == TransactionStatus.COMPLETED.value

    # Verify final state
    fetched = await integration_service.get_by_id(txn_id)
    assert fetched.status == TransactionStatus.COMPLETED


@pytest.mark.asyncio
async def test_idempotent_create_flow(integration_service, sample_transaction_data):
    """Create same transaction twice → second call returns existing with already_existed=True."""

    first = await integration_service.create(**sample_transaction_data)
    second = await integration_service.create(**sample_transaction_data)

    assert first.already_existed is False
    assert second.already_existed is True
    assert first.transaction_id == second.transaction_id


@pytest.mark.asyncio
async def test_strict_idempotency_rejects_different_params(integration_service, sample_transaction_data):
    """Same key + different params → raises DuplicateTransactionError."""

    await integration_service.create(**sample_transaction_data)

    # Same key, different amount
    conflicting_data = {**sample_transaction_data, "amount": Decimal("999.99")}

    with pytest.raises(DuplicateTransactionError):
        await integration_service.create(**conflicting_data)


@pytest.mark.asyncio
async def test_sqs_publish_called_on_create(integration_service, mock_sqs_publisher, sample_transaction_data):
    """Verifies that creating a transaction publishes an SQS event."""

    await integration_service.create(**sample_transaction_data)

    mock_sqs_publisher.publish_transaction_queued.assert_called_once()
    call_payload = mock_sqs_publisher.publish_transaction_queued.call_args[0][0]
    assert "transaction_id" in call_payload


@pytest.mark.asyncio
async def test_get_nonexistent_returns_none(integration_service):
    """Getting a non-existent transaction returns None."""
    from uuid import uuid4

    result = await integration_service.get_by_id(str(uuid4()))

    assert result is None


@pytest.mark.asyncio
async def test_invalid_status_transition_raises(integration_service, sample_transaction_data):
    """Attempting an invalid status transition raises ValueError."""

    result = await integration_service.create(**sample_transaction_data)
    txn_id = str(result.transaction_id)

    with pytest.raises(ValueError, match="Invalid transition"):
        await integration_service.update_status(txn_id, TransactionStatus.COMPLETED.value)
