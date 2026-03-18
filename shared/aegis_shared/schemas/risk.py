"""Risk related pydantic schemas."""

from uuid import UUID
from datetime import datetime, UTC
from pydantic import BaseModel, Field, ConfigDict

from aegis_shared.enums import RiskLevel, RiskDecision, RuleFlag


class RiskFactor(BaseModel):
    """Single risk factor — returned to bank in sync response."""
    factor: str      # matches RuleFlag values e.g. "HIGH_VELOCITY"
    severity: str    # "HIGH", "MEDIUM", "LOW"
    detail: str = "" # "8 transactions in 1 hour"


class RuleFlagResult(BaseModel):
    """Result from a single rule evaluation inside risk-engine."""
    rule_name: RuleFlag
    triggered: bool
    score: float = Field(..., ge=0.0, le=1.0)
    reason: str


class MLScore(BaseModel):
    """ML model inference result."""
    ml_anomaly_score: float = Field(..., ge=0.0, le=1.0)
    ml_model_version: str
    ml_fallback_used: bool = False


class LLMExplanation(BaseModel):
    """LLM-generated explanation — populated async after decision."""
    llm_summary: str
    llm_risk_factors: list[str]
    llm_recommendation: str
    llm_confidence: float = Field(..., ge=0.0, le=1.0)
    llm_fallback_used: bool = False


class RiskAssessment(BaseModel):
    """
    Sync response from risk-engine to transaction-service.
    Named RiskAssessment to avoid conflict with RiskDecision enum.
    Returned inline — LLM explanation empty (comes async via webhook).
    """
    transaction_id: str
    decision: RiskDecision              # enum: APPROVE / BLOCK / REVIEW
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel = RiskLevel.LOW
    confidence: str = "MEDIUM"          # "HIGH", "MEDIUM", "LOW"
    risk_factors: list[RiskFactor] = []
    processing_time_ms: float = 0.0
    model_version: str = "1.0.0"

    @property
    def is_blocked(self) -> bool:
        return self.decision == RiskDecision.BLOCK

    @property
    def is_approved(self) -> bool:
        return self.decision == RiskDecision.APPROVE


class RiskResult(BaseModel):
    """
    Full risk evaluation result — stored in risk-engine DB.
    Includes LLM explanation once async job completes.
    """
    transaction_id: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    decision: RiskDecision
    rule_flags: list[RuleFlagResult]
    ml_score: MLScore | None = None
    llm_explanation: LLMExplanation | None = None
    rule_score: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: float
    worker_id: UUID
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(from_attributes=True)


class RiskResultResponse(BaseModel):
    """Public risk result — returned to bank via GET /risk/{transaction_id}."""
    transaction_id: str
    risk_score: float
    risk_level: RiskLevel
    decision: RiskDecision
    triggered_rules: list[str]
    risk_factors: list[RiskFactor] = []
    llm_explanation: LLMExplanation | None = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))