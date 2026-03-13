""" Transaction repositoy, database operations. """

from sqlalchemy import select
from datetime import datetime, UTC
from uuid import UUID


from app.db.session import get_session
from app.models.transaction import Transaction
from aegis_shared.enums import TransactionStatus
from aegis_shared.utils.logging import get_logger

logger = get_logger("transaction_repo")

# Valid state transitions
VALID_TRANSITIONS = {
    TransactionStatus.RECEIVED: [TransactionStatus.PROCESSING, TransactionStatus.DEAD_LETTERED],
    TransactionStatus.PROCESSING: [TransactionStatus.COMPLETED, TransactionStatus.FAILED],
    TransactionStatus.FAILED: [TransactionStatus.RECEIVED],  # Retry
    TransactionStatus.COMPLETED: [],  # Terminal state
    TransactionStatus.DEAD_LETTERED: [],  # Terminal state
}


class TransactionRepository:
    """Database operations for Transaction model.
    All operations use atomic transactions with proper error handling.
    """

    async def create(self, data: dict) -> Transaction:
        """Insert a new transaction.

        Args:
            data: Transaction data dict.

        Returns:
            Created Transaction ORM instance.
        """
        async with get_session() as session:
            txn = Transaction(**data)
            try:
                session.add(txn)
                await session.commit()
                await session.refresh(txn)
            except Exception:
                await session.rollback()
                raise

            logger.info("transaction_created", transaction_id=str(txn.transaction_id))
            return txn

    async def find_by_id(self, transaction_id: UUID) -> Transaction | None:
        """Find a transaction by ID.

        Args:
            transaction_id: Transaction UUID.

        Returns:
            Transaction ORM instance or None.
        """
        async with get_session() as session:
            stmt = select(Transaction).where(Transaction.transaction_id == transaction_id)
            result = await session.execute(stmt)
            txn = result.scalar_one_or_none()
            return txn

    async def find_by_idempotency_key(self, idempotency_key: str) -> Transaction | None:
        """Find a transaction by idempotency key.

        Args:
            idempotency_key: Client-provided unique key.

        Returns:
            Transaction ORM instance or None.
        """
        async with get_session() as session:
            stmt = select(Transaction).where(Transaction.idempotency_key == idempotency_key)
            result = await session.execute(stmt)
            txn = result.scalar_one_or_none()
            return txn

    async def update_status(
        self,
        transaction_id: UUID,
        new_status: str,
        reason: str = "",
    ) -> dict:
        """Atomically update transaction status with validation.

        Uses SELECT FOR UPDATE to prevent concurrent modifications.

        Args:
            transaction_id: Transaction UUID.
            new_status: Target status string.
            reason: Reason for transition.

        Returns:
            Dict with previous and new status.

        Raises:
            ValueError: If transition is invalid.
        """
        async with get_session() as session:
            stmt = (
                select(Transaction)
                .where(Transaction.transaction_id == transaction_id)
                .with_for_update()
            )
            result = await session.execute(stmt)
            txn = result.scalar_one_or_none()

            if txn is None:
                raise ValueError(f"Transaction {transaction_id} not found")

            current_status = TransactionStatus(txn.status)
            target_status = TransactionStatus(new_status)

            # Validate transition
            if target_status not in VALID_TRANSITIONS.get(current_status, []):
                raise ValueError(
                    f"Invalid transition from {current_status.value} to {target_status.value}"
                )

            previous_status = txn.status
            txn.status = target_status.value
            txn.updated_at = datetime.now(UTC)

            await session.commit()

            logger.info(
                "transaction_status_updated",
                transaction_id=transaction_id,
                previous_status=previous_status,
                new_status=target_status.value,
            )

            return {
                "transaction_id": transaction_id,
                "previous_status": previous_status,
                "new_status": target_status.value,
                "success": True,
            }