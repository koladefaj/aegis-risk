"""Risk Engine Servicer Mapper — converts internal models to proto responses."""

from datetime import datetime
from uuid import UUID
from decimal import Decimal

from aegis_shared.generated.risk_engine_pb2 import (
    EvaluateRiskResponse,
    GetRiskResultResponse,
    RiskFactor,
    RuleFlagResult,
)
from aegis_shared.schemas.risk import RiskAssessment, RiskResult


class RiskServicerMapper:
    """Maps RiskAssessment / RiskResult → proto response messages."""

    @staticmethod
    def _fmt(value) -> str:
        """Convert any value to a proto-safe string."""
        if value is None:
            return ""
        if isinstance(value, (UUID, Decimal)):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if hasattr(value, "value"):  # Enum
            return str(value.value)
        return str(value)

    @classmethod
    def to_create_proto(cls, result: RiskAssessment) -> EvaluateRiskResponse:
        """Convert RiskAssessment → EvaluateRiskResponse.

        This is the SYNC response — only decision + score + risk_factors.
        No LLM fields, no rule flags, no ML detail.
        """
        return EvaluateRiskResponse(
            transaction_id=cls._fmt(result.transaction_id),
            decision=result.decision.value if hasattr(result.decision, "value") else str(result.decision),
            risk_score=float(result.risk_score),
            risk_level=result.risk_level.value if hasattr(result.risk_level, "value") else str(result.risk_level),
            confidence=result.confidence or "MEDIUM",
            risk_factors=[
                RiskFactor(
                    factor=rf.factor,
                    severity=rf.severity,
                    detail=rf.detail or "",
                )
                for rf in (result.risk_factors or [])
            ],
            processing_time_ms=float(result.processing_time_ms),
            model_version=result.model_version or "1.0.0",
        )

    @classmethod
    def to_get_proto(cls, result: RiskResult) -> GetRiskResultResponse:
        """Convert RiskResult → GetRiskResultResponse.

        This is the ASYNC response — full detail including LLM explanation,
        rule flags, and ML score. Fetched by bank after webhook notification.
        """
        # ML fields
        ml_score = result.ml_score
        llm = result.llm_explanation

        return GetRiskResultResponse(
            transaction_id=cls._fmt(result.transaction_id),
            decision=result.decision.value if hasattr(result.decision, "value") else str(result.decision),
            risk_score=float(result.risk_score),
            risk_level=result.risk_level.value if hasattr(result.risk_level, "value") else str(result.risk_level),

            # Inline risk factors summary
            risk_factors=[
                RiskFactor(
                    factor=rf.factor,
                    severity=rf.severity,
                    detail=rf.detail or "",
                )
                for rf in (result.risk_factors or [])
            ],

            # Rule engine detail
            rule_flags=[
                RuleFlagResult(
                    rule_name=rf.rule_name.value if hasattr(rf.rule_name, "value") else str(rf.rule_name),
                    triggered=rf.triggered,
                    score=float(rf.score),
                    reason=rf.reason or "",
                )
                for rf in (result.rule_flags or [])
            ],

            # ML detail
            ml_anomaly_score=float(ml_score.ml_anomaly_score) if ml_score else 0.0,
            ml_fallback_used=ml_score.ml_fallback_used if ml_score else True,
            ml_model_version=ml_score.ml_model_version if ml_score else "",

            # LLM explanation — may be empty if async job not complete yet
            llm_summary=llm.llm_summary if llm else "",
            llm_risk_factors=llm.llm_risk_factors if llm else [],
            llm_recommendation=llm.llm_recommendation if llm else "",
            llm_fallback_used=llm.llm_fallback_used if llm else True,

            # Metadata
            processing_time_ms=float(result.processing_time_ms),
            worker_id=cls._fmt(result.worker_id),
            evaluated_at=cls._fmt(result.evaluated_at),
        )