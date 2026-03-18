"""Account profile repository — upsert-based behavioural profile management."""

from datetime import datetime, UTC, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from aegis_shared.enums import RiskDecision
from app.models.account_profile import AccountProfile
from aegis_shared.utils.logging import get_logger

logger = get_logger("account_profile_repo")


class AccountProfileRepository:
    """Database operations for AccountProfile model.

    Two session patterns:
    - get_or_create(): uses injected session — called from orchestrator
      which manages its own session for the full evaluation transaction.
    - upsert_after_transaction(): uses get_session() context manager —
      called from SQS worker which has no existing session.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, account_id: str) -> AccountProfile:
        """Fetch account profile by account_id."""
        result = await self.session.execute(
            select(AccountProfile).where(
                AccountProfile.account_id == account_id
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, account_id: str) -> AccountProfile:
        """Fetch profile or create blank one for first-time accounts.

        Uses injected session — called from orchestrator during
        synchronous risk evaluation.
        """
        profile = await self.get(account_id)
        if profile:
            return profile

        now = datetime.now(UTC)
        profile = AccountProfile(
            account_id=account_id,
            first_seen_at=now,
            last_seen_at=now,
        )
        self.session.add(profile)
        await self.session.flush()        
        await self.session.refresh(profile) 

        logger.info("account_profile_created", account_id=account_id)
        return profile

    async def upsert_after_transaction(
        self,
        account_id: str,
        amount: Decimal,
        receiver_id: str,
        device_fingerprint: Optional[str],
        receiver_country: Optional[str],
        decision: str,
    ) -> None:
        """Update account profile after a transaction is evaluated.

        Called by SQS worker AFTER the sync risk decision is returned.
        Uses SELECT FOR UPDATE to prevent race conditions when multiple
        transactions from the same account arrive simultaneously.

        Args:
            account_id: Sender account ID.
            amount: Transaction amount.
            receiver_id: Receiver account ID.
            device_fingerprint: Device fingerprint hash.
            receiver_country: Receiver ISO country code.
            decision: Risk decision — APPROVE / BLOCK / REVIEW.
        """
        # Lock row to prevent concurrent update race conditions 
        result = await self.session.execute(
            select(AccountProfile)
            .where(AccountProfile.account_id == account_id)
            .with_for_update()
        )
        profile = result.scalar_one_or_none()

        now = datetime.now(UTC)

        if profile is None:
            # First transaction from this account
            profile = AccountProfile(
                account_id=account_id,
                first_seen_at=now,
                last_seen_at=now,
            )
            self.session.add(profile)
            await self.session.flush()

        # Lifetime counters
        profile.total_txn_count += 1
        profile.total_volume_lifetime += amount
        profile.last_txn_amount = amount
        profile.last_seen_at = now

        # Running average (Welford's online algorithm)
        # new_avg = old_avg + (new_val - old_avg) / new_count
        # More numerically stable than sum/count
        old_avg = float(profile.avg_txn_amount or 0)
        profile.avg_txn_amount = Decimal(str(
            old_avg + (float(amount) - old_avg) / profile.total_txn_count
        ))
        if amount > (profile.max_txn_amount or Decimal("0")):
            profile.max_txn_amount = amount

        # 1h rolling window
        if (
            profile.window_reset_at_1h is None
            or now - _ensure_tz(profile.window_reset_at_1h) > timedelta(hours=1)
        ):
            profile.txn_count_1h = 0
            profile.total_volume_1h = Decimal("0.00")
            profile.window_reset_at_1h = now

        profile.txn_count_1h += 1
        profile.total_volume_1h += amount

        # 24h rolling window
        if (
            profile.window_reset_at_24h is None
            or now - _ensure_tz(profile.window_reset_at_24h) > timedelta(hours=24)
        ):
            profile.txn_count_24h = 0
            profile.total_volume_24h = Decimal("0.00")
            profile.window_reset_at_24h = now

        profile.txn_count_24h += 1
        profile.total_volume_24h += amount

        # 30d window
        profile.txn_count_30d += 1
        profile.total_volume_30d += amount

        # Network features
        # use model method — handles deduplication
        profile.update_network_features(
            receiver_id=receiver_id,
            device_fp=device_fingerprint,
            country=receiver_country,
        )

        # Decision counters
        if decision == RiskDecision.BLOCK.value:
            profile.blocked_txn_count += 1
        elif decision == RiskDecision.REVIEW.value:
            profile.review_txn_count += 1

        # Auto-flag high-risk 
        # Flag if >20% of transactions blocked (min 5 transactions)
        if (
            not profile.is_high_risk
            and profile.total_txn_count >= 5
            and profile.blocked_txn_count / profile.total_txn_count > 0.2
        ):
            profile.is_high_risk = True
            logger.warning(
                "account_auto_flagged_high_risk",
                account_id=account_id,
                blocked_rate=round(
                    profile.blocked_txn_count / profile.total_txn_count, 3
                ),
            )

        # Optimistic locking
        profile.version += 1

        logger.info(
            "account_profile_updated",
            account_id=account_id,
            total_txn_count=profile.total_txn_count,
            txn_count_1h=profile.txn_count_1h,
            decision=decision,
            is_high_risk=profile.is_high_risk,
        )

    async def mark_fraud(self, account_id: str) -> None:
        """Increment fraud count when a transaction is confirmed fraud.

        Called externally when a bank confirms fraud — feeds back
        into ML features for future scoring.

        Args:
            account_id: Sender account ID.
        """
        
        await self.session.execute(
            update(AccountProfile)
            .where(AccountProfile.account_id == account_id)
            .values(
                fraud_txn_count=AccountProfile.fraud_txn_count + 1,
                is_high_risk=True,
                version=AccountProfile.version + 1,
            )
        )
        logger.info("account_marked_fraud", account_id=account_id)


def _ensure_tz(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware for comparison with UTC now."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt