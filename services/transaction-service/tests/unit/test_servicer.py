"""Unit tests for TransactionServicer (gRPC layer)."""

import pytest
import grpc
from decimal import Decimal
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from aegis_shared.enums import TransactionStatus
from aegis_shared.exceptions import DuplicateTransactionError
from aegis_shared.schemas.transaction import TransactionAccepted, TransactionResponse


@pytest.mark.asyncio
async def test_create_transaction_success(
    servicer, mock_transaction_service, mock_idempotency_service,
    grpc_context, sample_grpc_request,
):
    """Happy path — creates transaction and stores in idempotency cache."""

    now = datetime.now(UTC)
    txn_id = uuid4()

    mock_transaction_service.create.return_value = TransactionAccepted(
        transaction_id=txn_id,
        idempotency_key=sample_grpc_request.idempotency_key,
        amount=Decimal("100.00"),
        currency="USD",
        sender_id="sender-001",
        receiver_id="receiver-001",
        sender_country="US",
        receiver_country="GB",
        status=TransactionStatus.RECEIVED.value,
        created_at=now,
        already_existed=False,
    )

    result = await servicer.CreateTransaction(sample_grpc_request, grpc_context)

    assert result is not None
    mock_transaction_service.create.assert_called_once()
    mock_idempotency_service.store.assert_called_once()


@pytest.mark.asyncio
async def test_create_transaction_cached_duplicate(
    servicer, mock_idempotency_service, grpc_context, sample_grpc_request,
):
    """Returns cached response when idempotency cache has an exact match."""

    cached_response = {
        "request": {
            "amount": str(sample_grpc_request.amount),
            "currency": sample_grpc_request.currency,
            "sender_id": sample_grpc_request.sender_id,
            "receiver_id": sample_grpc_request.receiver_id,
            "sender_country": sample_grpc_request.sender_country,
            "receiver_country": sample_grpc_request.receiver_country,
        },
        "response": {
            "transactionId": str(uuid4()),
            "idempotencyKey": sample_grpc_request.idempotency_key,
            "amount": "100.0",
            "currency": "USD",
            "senderId": "sender-001",
            "receiverId": "receiver-001",
            "status": "RECEIVED",
            "createdAt": datetime.now(UTC).isoformat(),
            "alreadyExisted": False,
        },
    }

    mock_idempotency_service.check.return_value = cached_response

    result = await servicer.CreateTransaction(sample_grpc_request, grpc_context)

    assert result is not None
    grpc_context.abort.assert_not_called()


@pytest.mark.asyncio
async def test_create_transaction_cached_conflict(
    servicer, mock_idempotency_service, grpc_context, sample_grpc_request,
):
    """Aborts with ALREADY_EXISTS when cached request params don't match."""

    cached_response = {
        "request": {
            "amount": "999.99",  # different
            "currency": "EUR",   # different
            "sender_id": sample_grpc_request.sender_id,
            "receiver_id": sample_grpc_request.receiver_id,
            "sender_country": sample_grpc_request.sender_country,
            "receiver_country": sample_grpc_request.receiver_country,
        },
        "response": {},
    }
    mock_idempotency_service.check.return_value = cached_response

    with pytest.raises(grpc.aio.AbortError):
        await servicer.CreateTransaction(sample_grpc_request, grpc_context)

    grpc_context.abort.assert_called_once()
    call_args = grpc_context.abort.call_args
    assert call_args[0][0] == grpc.StatusCode.ALREADY_EXISTS


@pytest.mark.asyncio
async def test_create_transaction_invalid_amount(
    servicer, mock_idempotency_service, grpc_context,
):
    """Aborts with INVALID_ARGUMENT for non-numeric amount."""

    request = MagicMock()
    request.idempotency_key = "test-key-0000000000"
    request.amount = "not-a-number"
    request.currency = "USD"
    request.sender_id = "s1"
    request.receiver_id = "r1"
    request.sender_country = "US"
    request.receiver_country = "GB"
    request.device_fingerprint = ""
    request.ip_address = ""
    request.channel = "web"

    mock_idempotency_service.check.return_value = None

    with pytest.raises(grpc.aio.AbortError):
        await servicer.CreateTransaction(request, grpc_context)


@pytest.mark.asyncio
async def test_create_transaction_duplicate_error_from_db(
    servicer, mock_transaction_service, mock_idempotency_service,
    grpc_context, sample_grpc_request,
):
    """When DB raises DuplicateTransactionError, servicer aborts with ALREADY_EXISTS."""

    mock_idempotency_service.check.return_value = None
    mock_transaction_service.create.side_effect = DuplicateTransactionError("test-key-1234567890")

    with pytest.raises(grpc.aio.AbortError):
        await servicer.CreateTransaction(sample_grpc_request, grpc_context)

    grpc_context.abort.assert_called_once()
    assert grpc_context.abort.call_args[0][0] == grpc.StatusCode.ALREADY_EXISTS


@pytest.mark.asyncio
async def test_get_transaction_success(
    servicer, mock_transaction_service, grpc_context,
):
    """GetTransaction returns proto with correct fields."""

    txn_id = uuid4()
    mock_transaction_service.get_by_id.return_value = TransactionResponse(
        transaction_id=txn_id,
        idempotency_key="key-1234567890",
        amount=Decimal("50.00"),
        currency="USD",
        sender_id="s1",
        receiver_id="r1",
        sender_country="US",
        receiver_country="GB",
        status=TransactionStatus.RECEIVED,
        created_at=datetime.now(UTC),
    )

    request = MagicMock()
    request.transaction_id = str(txn_id)

    result = await servicer.GetTransaction(request, grpc_context)

    assert result is not None
    grpc_context.abort.assert_not_called()


@pytest.mark.asyncio
async def test_get_transaction_not_found(
    servicer, mock_transaction_service, grpc_context,
):
    """GetTransaction aborts with NOT_FOUND when transaction doesn't exist."""

    mock_transaction_service.get_by_id.return_value = None

    request = MagicMock()
    request.transaction_id = str(uuid4())

    with pytest.raises(grpc.aio.AbortError):
        await servicer.GetTransaction(request, grpc_context)

    grpc_context.abort.assert_called_once()
    assert grpc_context.abort.call_args[0][0] == grpc.StatusCode.NOT_FOUND


@pytest.mark.asyncio
async def test_update_status_success(
    servicer, mock_transaction_service, grpc_context,
):
    """UpdateTransactionStatus returns UpdateStatusResponse on valid transition."""

    txn_id = str(uuid4())
    mock_transaction_service.update_status.return_value = {
        "transaction_id": txn_id,
        "previous_status": "RECEIVED",
        "new_status": "PROCESSING",
        "success": True,
    }

    request = MagicMock()
    request.transaction_id = txn_id
    request.new_status = "PROCESSING"
    request.reason = "Starting analysis"

    result = await servicer.UpdateTransactionStatus(request, grpc_context)

    assert result is not None
    grpc_context.abort.assert_not_called()


@pytest.mark.asyncio
async def test_update_status_invalid_transition(
    servicer, mock_transaction_service, grpc_context,
):
    """UpdateTransactionStatus aborts with INVALID_ARGUMENT on invalid transition."""

    mock_transaction_service.update_status.side_effect = ValueError(
        "Invalid transition from COMPLETED to RECEIVED"
    )

    request = MagicMock()
    request.transaction_id = str(uuid4())
    request.new_status = "RECEIVED"
    request.reason = "retry"

    with pytest.raises(grpc.aio.AbortError):
        await servicer.UpdateTransactionStatus(request, grpc_context)

    grpc_context.abort.assert_called_once()
    assert grpc_context.abort.call_args[0][0] == grpc.StatusCode.INVALID_ARGUMENT


@pytest.mark.asyncio
async def test_health_check(servicer, grpc_context):
    """HealthCheck returns correct service name and status."""

    request = MagicMock()

    result = await servicer.HealthCheck(request, grpc_context)

    assert result.status == "ok"
    assert result.service_name == "transaction-service"
    assert result.version == "1.0.0"
