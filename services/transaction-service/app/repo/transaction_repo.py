""" Transaction repositoy, database operations. """

from sqlalchemy import select
from datetime import datetime, UTC
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from aegis_shared.schemas.transaction import TransactionUpdate
from app.db.session import get_session
from app.models.transaction import Transaction
from aegis_shared.enums import TransactionStatus
from aegis_shared.utils.logging import get_logger

logger = get_logger("transaction_repo")

# Valid state transitions
VALID_TRANSITIONS = {
    TransactionStatus.RECEIVED: [
        TransactionStatus.PROCESSING, 
        TransactionStatus.DEAD_LETTERED, 
        TransactionStatus.APPROVED,
        TransactionStatus.REVIEW, 
        TransactionStatus.BLOCKED,
    ],
    TransactionStatus.REVIEW: [
        TransactionStatus.APPROVED, 
        TransactionStatus.BLOCKED
    ],
    TransactionStatus.PROCESSING: [TransactionStatus.COMPLETED, TransactionStatus.FAILED],
    TransactionStatus.FAILED: [TransactionStatus.RECEIVED],
    TransactionStatus.COMPLETED: [],
    TransactionStatus.DEAD_LETTERED: [],
    TransactionStatus.APPROVED: [TransactionStatus.PROCESSING],
}

class TransactionRepository:
    """Database operations for Transaction model.
    All operations use atomic transactions with proper error handling.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> Transaction:
        """Insert a new transaction.

        Args:
            data: Transaction data dict.

        Returns:
            Created Transaction ORM instance.
        """
            
        txn = Transaction(**data)
        self.session.add(txn)
        await self.session.flush()
        await self.session.refresh(txn)

        logger.info("transaction_created", transaction_id=str(txn.transaction_id))
        return txn

    async def find_by_id(self, transaction_id: UUID) -> Transaction | None:
        """Find a transaction by ID.

        Args:
            transaction_id: Transaction UUID.

        Returns:
            Transaction ORM instance or None.
        """
        
        stmt = select(Transaction).where(Transaction.transaction_id == transaction_id)
        result = await self.session.execute(stmt)
        txn = result.scalar_one_or_none()
        return txn

    async def find_by_idempotency_key(self, idempotency_key: str) -> Transaction | None:
        """Find a transaction by idempotency key.

        Args:
            idempotency_key: Client-provided unique key.

        Returns:
            Transaction ORM instance or None.
        """
        
        stmt = select(Transaction).where(Transaction.idempotency_key == idempotency_key)
        result = await self.session.execute(stmt)
        txn = result.scalar_one_or_none()
        return txn

    async def update_status(
        self,
        transaction_id: UUID,
        new_status: str,
        reason: str | None = None,
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
        
        stmt = (
            select(Transaction)
            .where(Transaction.transaction_id == transaction_id)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
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

        await self.session.flush()
        await self.session.refresh(txn)


        logger.info(
            "transaction_status_updated",
            transaction_id=transaction_id,
            previous_status=previous_status,
            new_status=target_status.value,
        )

        return TransactionUpdate(
            transaction_id= transaction_id,
            previous_status= previous_status,
            new_status=target_status.value,
            success= True,
        )