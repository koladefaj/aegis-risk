"""Transaction business logic service."""

from uuid import UUID
from decimal import Decimal
from datetime import datetime, UTC
import grpc

from app.db.session import get_session
from app.config import settings
from aegis_shared.schemas.transaction import TransactionAccepted, TransactionResponse, TransactionUpdate
from aegis_shared.utils.tracing import get_correlation_id
from app.repo.transaction_repo import TransactionRepository
from app.grpc_clients.risk_engine_client import RiskEngineClient
from aegis_shared.schemas.risk import RiskAssessment
from app.queue.sqs_publisher import SQSPublisher
from aegis_shared.enums import TransactionStatus
from aegis_shared.exceptions import DuplicateTransactionError
from aegis_shared.utils.logging import get_logger

logger = get_logger("transaction_business_service")


class TransactionBusinessService:
    """Core business logic for transaction operations."""

    def __init__(self, publisher: SQSPublisher, risk_engine: RiskEngineClient):
        self.publisher = publisher
        self.risk_engine = risk_engine

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

        now = datetime.now(UTC)

        async with get_session() as session:
            repo = TransactionRepository(session)

            # Check idempotency
            existing = await repo.find_by_idempotency_key(idempotency_key)
            request_data = {
                "amount": amount,
                "currency": currency,
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "sender_country": sender_country,
                "receiver_country": receiver_country,
            }

            if existing:
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

            # Persist with status=RECEIVED
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

            txn = await repo.create(transaction_data)
            transaction_id = str(txn.transaction_id)
            logger.info("transaction_persisted", transaction_id=transaction_id)

        # Risk scoring outside DB session
        risk_decision = await self._score_risk(
            transaction_id=txn.transaction_id,
            amount=amount,
            currency=currency,
            sender_id=sender_id,
            receiver_id=receiver_id,
            sender_country=sender_country,
            receiver_country=receiver_country,
            device_fingerprint=device_fingerprint,
            ip_address=ip_address,
            channel=channel,
        )

        final_status = TransactionStatus.from_risk_decision(risk_decision.decision).value

        # Update status in a new session
        async with get_session() as session:
            repo = TransactionRepository(session)
            await repo.update_status(txn.transaction_id, final_status)

        logger.info(
            "transaction_risk_scored",
            transaction_id=transaction_id,
            decision=risk_decision.decision,
            risk_score=risk_decision.risk_score,
            status=final_status,
        )

        # Build event payload
        event_payload = {
            **TransactionAccepted.model_validate(txn).model_dump(mode="json"),
            "risk_decision": risk_decision.decision.value,
            "risk_score": float(risk_decision.risk_score),
            "risk_level": risk_decision.risk_level.value,
            "confidence": risk_decision.confidence,
            "risk_factors": [rf.dict() for rf in risk_decision.risk_factors],
            "processing_time_ms": risk_decision.processing_time_ms,
            "model_version": risk_decision.model_version,
            "ml_anomaly_score": float(risk_decision.risk_score),
            "ml_model_version": risk_decision.model_version,
            "ml_fallback_used": False,
            "correlation_id": get_correlation_id(),
        }

        try:
            await self.publisher.publish_transaction_queued(event_payload)
            logger.info("transaction_event_published", transaction_id=transaction_id)
        except Exception as e:
            logger.error("transaction_event_publish_failed", transaction_id=transaction_id, error=str(e))

        # Return final TransactionAccepted
        return TransactionAccepted(
            transaction_id=txn.transaction_id,
            idempotency_key=idempotency_key,
            amount=amount,
            currency=currency,
            sender_id=sender_id,
            receiver_id=receiver_id,
            sender_country=sender_country,
            receiver_country=receiver_country,
            status=final_status,
            created_at=now,
            already_existed=False,
            risk_score=risk_decision.risk_score,
            risk_factors=risk_decision.risk_factors,
            decision=risk_decision.decision,
        )

    async def _score_risk(
        self,
        transaction_id: UUID,
        amount: Decimal,
        currency: str,
        sender_id: str,
        receiver_id: str,
        sender_country: str,
        receiver_country: str,
        device_fingerprint: str,
        ip_address: str,
        channel: str,
    ) -> RiskAssessment:
        try:
            return await self.risk_engine.evaluate_risk(
                transaction_id=transaction_id,
                amount=amount,
                currency=currency,
                sender_id=sender_id,
                receiver_id=receiver_id,
                sender_country=sender_country,
                receiver_country=receiver_country,
                device_fingerprint=device_fingerprint,
                ip_address=ip_address,
                channel=channel,
            )
        except Exception as e:
            logger.error("risk_engine_call_failed", transaction_id=transaction_id, error=str(e))
            return RiskAssessment(
                transaction_id=str(transaction_id),
                decision="REVIEW",
                risk_score=0.5,
                risk_factors=[{"factor": "scoring_unavailable", "severity": "MEDIUM", "detail": ""}],
            )

    async def get_by_id(self, transaction_id: str) -> TransactionResponse | None:
        import uuid
        try:
            parsed_id = uuid.UUID(transaction_id)
        except ValueError:
            return None

        async with get_session() as session:
            repo = TransactionRepository(session)
            result = await repo.find_by_id(parsed_id)
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

        async with get_session() as session:
            repo = TransactionRepository(session)
            result = await repo.update_status(parsed_id, new_status, reason)
        return result