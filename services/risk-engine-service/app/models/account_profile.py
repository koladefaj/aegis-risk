"""Account profile model — tracks per-account behavioural statistics for fraud detection."""

from datetime import datetime, UTC
from typing import Optional, Any
from decimal import Decimal

from sqlalchemy import (
    String, Integer, Numeric, Boolean, DateTime, Index, text, BigInteger
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from app.db.base import Base
from app.config import settings


class AccountProfile(Base):
    """
    Running behavioural summary for a sender account.

    One row per account — updated (upserted) on every transaction processed
    by the risk engine. Used to derive velocity and behavioural features
    for ML fraud scoring.

    Update strategy: ON CONFLICT (account_id) DO UPDATE
    Never INSERT a second row for the same account_id.
    """

    __tablename__ = "account_profiles"

    # ── Identity 
    account_id: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        nullable=False,
        comment="Sender account ID — matches sender_id in transactions table",
    )

    # ── Lifetime counters ─────────────────────────────────────────────────────
    total_txn_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Total transactions ever submitted by this account",
    )

    total_volume_lifetime: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
        comment="Total amount transacted over account lifetime",
    )

    # ── 30-day rolling window ─────────────────────────────────────────────────
    total_volume_30d: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
        comment="Total amount transacted in the last 30 days",
    )

    txn_count_30d: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Number of transactions in the last 30 days",
    )

    # ── 24-hour rolling window ────────────────────────────────────────────────
    total_volume_24h: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
        comment="Total amount transacted in the last 24 hours",
    )

    txn_count_24h: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Number of transactions in the last 24 hours",
    )

    # ── 1-hour rolling window ─────────────────────────────────────────────────
    txn_count_1h: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Number of transactions in the last 1 hour — strongest velocity signal",
    )

    total_volume_1h: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
        comment="Total amount transacted in the last 1 hour",
    )

    # ── Amount statistics ─────────────────────────────────────────────────────
    avg_txn_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
        comment="Running average transaction amount",
    )

    max_txn_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
        comment="Largest single transaction ever submitted",
    )

    last_txn_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Amount of the most recent transaction",
    )

    # ── Behavioural flags ─────────────────────────────────────────────────────
    is_high_risk: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        comment="Manually or automatically flagged as high-risk account",
    )

    fraud_txn_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Number of transactions confirmed as fraud",
    )

    blocked_txn_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Number of transactions blocked by risk engine",
    )

    review_txn_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Number of transactions sent to manual review",
    )

    # ── Network features ──────────────────────────────────────────────────────
    unique_receiver_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Number of distinct receiver accounts ever transacted with",
    )

    known_receiver_ids: Mapped[list[str]] = mapped_column(
        ARRAY(String(64)),
        nullable=False,
        default=list,
        server_default=text("ARRAY[]::varchar[]"),
        comment="Array of known receiver account IDs",
    )

    unique_device_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Number of distinct device fingerprints seen",
    )

    known_device_fingerprints: Mapped[list[str]] = mapped_column(
        ARRAY(String(128)),
        nullable=False,
        default=list,
        server_default=text("ARRAY[]::varchar[]"),
        comment="Array of known device fingerprints",
    )

    unique_country_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Number of distinct destination countries transacted to",
    )

    known_receiver_countries: Mapped[list[str]] = mapped_column(
        ARRAY(String(2)),
        nullable=False,
        default=list,
        server_default=text("ARRAY[]::varchar[]"),
        comment="Array of known receiver countries (ISO 3166-1 alpha-2)",
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        comment="When this account first submitted a transaction",
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        comment="Timestamp of most recent transaction",
    )

    window_reset_at_24h: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the 24h rolling window was last reset",
    )

    window_reset_at_1h: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the 1h rolling window was last reset",
    )

    # ── Extra metadata ────────────────────────────────────────────────────────
    profile_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Arbitrary metadata — notes, manual review flags, etc.",
    )

    # ── Version for optimistic locking ────────────────────────────────────────
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default=text("1"),
        comment="Optimistic locking version",
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_account_profiles_last_seen_at", "last_seen_at"),
        Index("ix_account_profiles_is_high_risk", "is_high_risk"),
        Index("ix_account_profiles_fraud_txn_count", "fraud_txn_count"),
        Index("ix_account_profiles_txn_count_1h", "txn_count_1h"),
        Index("ix_account_profiles_total_txn_count", "total_txn_count"),
        Index("ix_account_profiles_created_at", "first_seen_at"),
        Index("ix_account_profiles_risk_velocity", "is_high_risk", "txn_count_1h"),
    )

    def __repr__(self) -> str:
        return (
            f"<AccountProfile account_id={self.account_id} "
            f"txn_count={self.total_txn_count} "
            f"avg_amount={self.avg_txn_amount} "
            f"fraud_count={self.fraud_txn_count}>"
        )

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def account_age_hours(self) -> float:
        """Hours since first transaction — key ML feature."""
        now = datetime.now(UTC)
        first_seen = (
            self.first_seen_at.replace(tzinfo=UTC)
            if self.first_seen_at.tzinfo is None
            else self.first_seen_at
        )
        return (now - first_seen).total_seconds() / 3600

    @property
    def account_age_days(self) -> float:
        """Days since first transaction."""
        return self.account_age_hours / 24

    @property
    def is_new_account(self) -> bool:
        """Account less than 24 hours old."""
        return self.account_age_hours < 24

    @property
    def is_dormant(self) -> bool:
        """No activity in last 30 days."""
        now = datetime.now(UTC)
        last_seen = (
            self.last_seen_at.replace(tzinfo=UTC)
            if self.last_seen_at.tzinfo is None
            else self.last_seen_at
        )
        return (now - last_seen).days > 30

    @property
    def fraud_rate(self) -> float:
        """Percentage of transactions that were fraudulent."""
        if self.total_txn_count == 0:
            return 0.0
        return (self.fraud_txn_count / self.total_txn_count) * 100

    @property
    def velocity_score(self) -> float:
        """Normalized velocity score based on 1h transaction count."""
        max_expected = getattr(settings, "MAX_TXN_PER_HOUR", 10)
        if max_expected == 0:
            return 0.0
        return min(self.txn_count_1h / max_expected, 1.0)

    # ── Helper methods ────────────────────────────────────────────────────────

    def is_new_receiver(self, receiver_id: str) -> bool:
        """True if this account has never sent to this receiver before."""
        if not receiver_id or not self.known_receiver_ids:
            return True
        return receiver_id not in self.known_receiver_ids

    def is_new_device(self, device_fingerprint: Optional[str]) -> bool:
        """True if this device fingerprint has never been seen for this account."""
        if not device_fingerprint or not self.known_device_fingerprints:
            return True
        return device_fingerprint not in self.known_device_fingerprints

    def update_network_features(
        self,
        receiver_id: str,
        device_fp: Optional[str],
        country: Optional[str],
    ) -> None:
        """Update network-related features — call from service layer with proper locking."""
        # ✅ fixed — was inverted (added only if NOT new)
        if receiver_id and self.is_new_receiver(receiver_id):
            self.unique_receiver_count += 1
            self.known_receiver_ids = [*self.known_receiver_ids, receiver_id]

        if device_fp and self.is_new_device(device_fp):
            self.unique_device_count += 1
            self.known_device_fingerprints = [*self.known_device_fingerprints, device_fp]

        if country and country not in (self.known_receiver_countries or []):
            self.unique_country_count += 1
            self.known_receiver_countries = [*self.known_receiver_countries, country]

    def to_feature_dict(
        self,
        current_amount: Decimal,
        receiver_id: str,
        device_fingerprint: Optional[str],
    ) -> dict[str, float]:
        """Build the ML feature vector for this account + current transaction."""
        avg = float(self.avg_txn_amount) if self.avg_txn_amount else 0.0
        amount = float(current_amount)
        amount_ratio = min(amount / avg, 50.0) if avg > 0 else 1.0

        return {
            "sender_txn_count": float(self.total_txn_count),
            "sender_total_volume": float(self.total_volume_lifetime),
            "sender_avg_amount": avg,
            "sender_max_amount": float(self.max_txn_amount),
            "amount_vs_avg_ratio": amount_ratio,
            "account_age_hours": self.account_age_hours,
            "is_new_account": float(self.is_new_account),
            "is_new_receiver": float(self.is_new_receiver(receiver_id)),
            "is_new_device": float(self.is_new_device(device_fingerprint)),
            "unique_receiver_count": float(self.unique_receiver_count),
            "unique_device_count": float(self.unique_device_count),
            "fraud_txn_count": float(self.fraud_txn_count),
            "blocked_txn_count": float(self.blocked_txn_count),
            "txn_count_1h": float(self.txn_count_1h),
            "txn_count_24h": float(self.txn_count_24h),
            "total_volume_24h": float(self.total_volume_24h),
            "total_volume_1h": float(self.total_volume_1h),
            "velocity_score": self.velocity_score,
            "fraud_rate": self.fraud_rate,
            "is_dormant": float(self.is_dormant),
        }