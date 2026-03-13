"""Transaction business logic service."""

from decimal import Decimal
from datetime import datetime, UTC

from aegis_shared.schemas.transaction import TransactionAccepted, TransactionResponse, TransactionUpdate
from app.repo.transaction_repo import TransactionRepository
from app.queue.sqs_publisher import SQSPublisher
from aegis_shared.enums import TransactionStatus
from aegis_shared.exceptions import DuplicateTransactionError
from aegis_shared.utils.logging import get_logger

logger = get_logger("transaction_business_service")


class TransactionBusinessService:
    """Core business logic for transaction operations."""

    def __init__(self):
        self.repo = TransactionRepository()
        self.publisher = SQSPublisher()

    async def create(
        self,
        idempotency_key: str,
        amount: Decimal,
        currency: str,
        sender_id: str,
        receiver_id: str,
        sender_country: str,
        receiver_country: str,
        device_fingerprint: str = "",
        ip_address: str = "",
        channel: str = "web",
    ) -> TransactionAccepted:
        
        # Check if already exists (belt-and-suspenders with idempotency service)
        existing = await self.repo.find_by_idempotency_key(idempotency_key)

        request_data = {
            "amount": amount,
            "currency": currency,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "sender_country": sender_country,
            "receiver_country": receiver_country,
        }

        if existing:

            # Strict Idempotency Check against DB record
            existing_data = {
                "amount": existing.amount,
                "currency": existing.currency,
                "sender_id": existing.sender_id,
                "receiver_id": existing.receiver_id,
                "sender_country": existing.sender_country,
                "receiver_country": existing.receiver_country,
            }

            if existing_data != request_data:
                logger.warning(
                    "db_idempotency_conflict",
                    idempotency_key=idempotency_key,
                    original_request=existing_data,
                    attempted_request=request_data,
                )
                raise DuplicateTransactionError(idempotency_key)

            logger.info("duplicate_transaction_found", idempotency_key=idempotency_key)
            return TransactionAccepted.model_validate(existing).model_copy(
                update={"already_existed": True}
            )

        now = datetime.now(UTC)

        transaction_data = {
            "idempotency_key": idempotency_key,
            "amount": amount,
            "currency": currency,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "sender_country": sender_country,
            "receiver_country": receiver_country,
            "device_fingerprint": device_fingerprint,
            "ip_address": ip_address,
            "channel": channel,
            "status": TransactionStatus.RECEIVED.value,
            "created_at": now,
        }

        txn = await self.repo.create(transaction_data)
        transaction_id = str(txn.transaction_id)

        logger.info(
            "transaction_persisted",
            transaction_id=transaction_id,
        )

        event_payload = TransactionAccepted.model_validate(txn).model_dump(mode="json")

        try:
            await self.publisher.publish_transaction_queued(event_payload)

            logger.info(
                "transaction_event_published",
                transaction_id=transaction_id,
            )

        except Exception as e:
            logger.error(
                "transaction_event_publish_failed",
                transaction_id=transaction_id,
                error=str(e),
            )

        return TransactionAccepted(
            transaction_id=transaction_id,
            idempotency_key=idempotency_key,
            amount=amount,
            currency=currency,
            sender_id=sender_id,
            receiver_id=receiver_id,
            sender_country=sender_country,
            receiver_country=receiver_country,
            status=TransactionStatus.RECEIVED.value,
            created_at=now,         
            already_existed=False,
        )

    async def get_by_id(self, transaction_id: str) -> TransactionResponse | None:
        import uuid
        try:
            parsed_id = uuid.UUID(transaction_id)
        except ValueError:
            return None

        result = await self.repo.find_by_id(parsed_id)
        if result is None:
            return None
        return TransactionResponse.model_validate(result)

    async def update_status(
        self,
        transaction_id: str,
        new_status: str,
        reason: str = "",
    ) -> TransactionUpdate:
        import uuid
        try:
            parsed_id = uuid.UUID(transaction_id)
        except ValueError:
            raise ValueError(f"Invalid transaction ID format: {transaction_id}")

        return await self.repo.update_status(parsed_id, new_status, reason)