"""Risk result SQLAlchemy model."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Any

from sqlalchemy import (
    DateTime, Float, Index, String, Text, JSON,
    func, text, Boolean, Integer, Numeric
)
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SAEnum

from app.db.base import Base
from aegis_shared.enums import RiskDecision


class RiskResult(Base):
    """Stores completed risk evaluation results.

    One row per evaluated transaction with full scoring details.
    Created AFTER successful processing — represents the outcome.
    """

    __tablename__ = "risk_results"

    # ── Primary Key ───────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # ── Transaction Reference ─────────────────────────────────────────────────
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        unique=True,  # one result per transaction
    )

    # ── Denormalized transaction data (for analytics without cross-service joins)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    sender_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    receiver_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # ── Core risk scores ──────────────────────────────────────────────────────
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)

    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    decision: Mapped[RiskDecision] = mapped_column(  # ✅ fixed typo descision → decision
        SAEnum(RiskDecision, name="riskdecision", create_type=False),
        nullable=False,
        index=True,
    )

    confidence: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="MEDIUM",
        server_default=text("'MEDIUM'"),
    )

    # ── Rule engine results ───────────────────────────────────────────────────
    rule_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    triggered_rules: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    rule_flags: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # ── ML scoring ────────────────────────────────────────────────────────────
    ml_anomaly_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ml_model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ml_fallback_used: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    ml_features_used: Mapped[Optional[dict[str, float]]] = mapped_column(JSON, nullable=True)
    ml_latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── LLM analysis ──────────────────────────────────────────────────────────
    # All nullable — populated async after sync response is returned
    llm_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    llm_risk_factors: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    llm_recommendation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    llm_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    llm_fallback_used: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    llm_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    llm_latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Performance metrics ───────────────────────────────────────────────────
    processing_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    worker_id: Mapped[Optional[str]] = mapped_column(  # ✅ fixed — was missing mapped_column
        String(64),
        nullable=True,
    )

    # ── Tracing ───────────────────────────────────────────────────────────────
    correlation_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ── Optimistic locking ────────────────────────────────────────────────────
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_risk_results_transaction_id", "transaction_id", unique=True),
        Index("ix_risk_results_sender_id", "sender_id"),
        Index("ix_risk_results_correlation_id", "correlation_id"),
        Index("ix_risk_results_risk_level", "risk_level"),
        Index("ix_risk_results_risk_score", "risk_score"),
        Index("ix_risk_results_decision", "decision"),          # ✅ fixed — was final_decision
        Index("ix_risk_results_evaluated_at", "evaluated_at"),
        Index("ix_risk_results_ml_model_version", "ml_model_version"),
        Index("ix_risk_results_level_evaluated", "risk_level", "evaluated_at"),
        Index("ix_risk_results_decision_evaluated", "decision", "evaluated_at"),  # ✅ fixed
        Index(
            "ix_risk_results_high_risk_only",
            "id",
            postgresql_where=text("risk_level IN ('HIGH', 'CRITICAL')"),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<RiskResult id={self.id} "
            f"txn={self.transaction_id} "
            f"score={self.risk_score} "
            f"level={self.risk_level} "
            f"decision={self.decision.value}>"
        )

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def is_high_risk(self) -> bool:
        return self.risk_level.upper() in ("HIGH", "CRITICAL")

    @property
    def is_ml_based(self) -> bool:
        return self.ml_anomaly_score is not None and not self.ml_fallback_used

    @property
    def is_llm_based(self) -> bool:
        return self.llm_summary is not None and not self.llm_fallback_used

    def to_analytics(self) -> dict:
        """Convert to analytics-friendly format."""
        return {
            "result_id": str(self.id),
            "transaction_id": str(self.transaction_id),
            "amount": float(self.amount),               # ✅ fixed field name
            "currency": self.currency,                  # ✅ fixed field name
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "decision": self.decision.value if self.decision else None,  # ✅ fixed field name
            "ml_score": self.ml_anomaly_score,
            "ml_version": self.ml_model_version,
            "ml_fallback": self.ml_fallback_used,
            "llm_fallback": self.llm_fallback_used,
            "processing_time_ms": self.processing_time_ms,  # ✅ fixed field name
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
        }