"""Integration tests for TransactionRepository against a real (SQLite) database."""

import pytest
from decimal import Decimal
from datetime import datetime, UTC

from aegis_shared.enums import TransactionStatus


@pytest.mark.asyncio
async def test_create_and_find_by_id(repo, sample_transaction_data):
    """Round-trip: create a transaction and retrieve it by ID."""

    data = {
        **sample_transaction_data,
        "status": TransactionStatus.RECEIVED.value,
        "created_at": datetime.now(UTC),
    }

    created = await repo.create(data)

    assert created.transaction_id is not None
    assert created.amount == sample_transaction_data["amount"]
    assert created.currency == sample_transaction_data["currency"]

    found = await repo.find_by_id(created.transaction_id)

    assert found is not None
    assert found.transaction_id == created.transaction_id
    assert found.sender_id == sample_transaction_data["sender_id"]


@pytest.mark.asyncio
async def test_find_by_idempotency_key(repo, sample_transaction_data):
    """Lookup by idempotency key returns the correct transaction."""

    data = {
        **sample_transaction_data,
        "status": TransactionStatus.RECEIVED.value,
        "created_at": datetime.now(UTC),
    }

    created = await repo.create(data)
    found = await repo.find_by_idempotency_key(sample_transaction_data["idempotency_key"])

    assert found is not None
    assert found.transaction_id == created.transaction_id


@pytest.mark.asyncio
async def test_find_by_idempotency_key_not_found(repo):
    """Returns None when idempotency key doesn't exist."""

    found = await repo.find_by_idempotency_key("nonexistent-key-000")

    assert found is None


@pytest.mark.asyncio
async def test_find_by_id_not_found(repo):
    """Returns None when transaction ID doesn't exist."""
    from uuid import uuid4

    found = await repo.find_by_id(uuid4())

    assert found is None


@pytest.mark.asyncio
async def test_update_status_valid_transition(repo, sample_transaction_data):
    """Valid transition: RECEIVED → PROCESSING."""

    data = {
        **sample_transaction_data,
        "status": TransactionStatus.RECEIVED.value,
        "created_at": datetime.now(UTC),
    }

    created = await repo.create(data)

    result = await repo.update_status(
        created.transaction_id,
        TransactionStatus.PROCESSING.value,
        "Starting fraud check",
    )

    assert result["success"] is True
    assert result["previous_status"] == TransactionStatus.RECEIVED.value
    assert result["new_status"] == TransactionStatus.PROCESSING.value


@pytest.mark.asyncio
async def test_update_status_invalid_transition(repo, sample_transaction_data):
    """Invalid transition: RECEIVED → COMPLETED raises ValueError."""

    data = {
        **sample_transaction_data,
        "status": TransactionStatus.RECEIVED.value,
        "created_at": datetime.now(UTC),
    }

    created = await repo.create(data)

    with pytest.raises(ValueError, match="Invalid transition"):
        await repo.update_status(
            created.transaction_id,
            TransactionStatus.COMPLETED.value,
        )


@pytest.mark.asyncio
async def test_update_status_not_found(repo):
    """Updating a non-existent transaction raises ValueError."""
    from uuid import uuid4

    with pytest.raises(ValueError, match="not found"):
        await repo.update_status(uuid4(), TransactionStatus.PROCESSING.value)


@pytest.mark.asyncio
async def test_update_status_chain(repo, sample_transaction_data):
    """Valid chain: RECEIVED → PROCESSING → COMPLETED."""

    data = {
        **sample_transaction_data,
        "status": TransactionStatus.RECEIVED.value,
        "created_at": datetime.now(UTC),
    }

    created = await repo.create(data)

    # First transition
    result1 = await repo.update_status(
        created.transaction_id,
        TransactionStatus.PROCESSING.value,
    )
    assert result1["success"] is True

    # Second transition
    result2 = await repo.update_status(
        created.transaction_id,
        TransactionStatus.COMPLETED.value,
    )
    assert result2["success"] is True
    assert result2["previous_status"] == TransactionStatus.PROCESSING.value
    assert result2["new_status"] == TransactionStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_terminal_state_cannot_transition(repo, sample_transaction_data):
    """COMPLETED is terminal — cannot transition further."""

    data = {
        **sample_transaction_data,
        "status": TransactionStatus.RECEIVED.value,
        "created_at": datetime.now(UTC),
    }

    created = await repo.create(data)

    await repo.update_status(created.transaction_id, TransactionStatus.PROCESSING.value)
    await repo.update_status(created.transaction_id, TransactionStatus.COMPLETED.value)

    with pytest.raises(ValueError, match="Invalid transition"):
        await repo.update_status(created.transaction_id, TransactionStatus.RECEIVED.value)
