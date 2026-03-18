"""Risk result repository — persist and retrieve risk evaluation results."""

from typing import Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy import select, update

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.db.session import get_session
from app.models.risk_result import RiskResult
from aegis_shared.utils.logging import get_logger

logger = get_logger("risk_result_repo")


class RiskResultRepository:
    """Database operations for RiskResult model."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(
        self,
        assessment,
        transaction_data: dict,
        rule_flags: list[dict],
        ml_anomaly_score: Optional[float],
        ml_model_version: Optional[str],
        ml_fallback_used: bool,
        ml_features_used: Optional[dict],
        correlation_id: Optional[str] = None,
    ) -> None:
        """Atomic upsert for risk results to ensure idempotency."""
        
        stmt = insert(RiskResult).values(
            transaction_id=UUID(assessment.transaction_id),
            amount=Decimal(str(transaction_data.get("amount", 0))),
            currency=transaction_data.get("currency"),
            sender_id=transaction_data.get("sender_id"),
            receiver_id=transaction_data.get("receiver_id"),
            risk_score=assessment.risk_score,
            risk_level=assessment.risk_level.value,
            decision=assessment.decision,
            confidence=assessment.confidence,
            rule_score=float(transaction_data.get("rule_score", 0.0)),
            triggered_rules=[r["rule"] for r in rule_flags if r.get("triggered")],
            rule_flags=rule_flags,
            ml_anomaly_score=ml_anomaly_score,
            ml_model_version=ml_model_version,
            ml_fallback_used=ml_fallback_used,
            ml_features_used=ml_features_used,
            processing_time_ms=assessment.processing_time_ms,
            worker_id=str(transaction_data.get("worker_id", "")),
            correlation_id=correlation_id,
            version=1
        ).on_conflict_do_nothing(index_elements=['transaction_id']) 
            
            
        await self.session.execute(stmt)

    async def update_llm_explanation(
        self,
        transaction_id: str,
        llm_summary: str,
        llm_risk_factors: list[str],
        llm_recommendation: str,
        llm_confidence: float,
        llm_model: str,
        llm_latency_ms: float,
        llm_fallback_used: bool = False,
    ) -> None:
        """Direct Update pattern (Atomic) to avoid SELECT FOR UPDATE overhead."""
        stmt = (
            update(RiskResult)
            .where(RiskResult.transaction_id == UUID(transaction_id))
            .values(
                llm_summary=llm_summary,
                llm_risk_factors=llm_risk_factors,
                llm_recommendation=llm_recommendation,
                llm_confidence=llm_confidence,
                llm_model=llm_model,
                llm_latency_ms=llm_latency_ms,
                llm_fallback_used=llm_fallback_used,
                version=RiskResult.version + 1,
            )
        )
        await self.session.execute(stmt)
            
        logger.info("llm_explanation_updated_atomically", transaction_id=transaction_id)