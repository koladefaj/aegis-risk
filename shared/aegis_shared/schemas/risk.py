""" Risk related pydantic schemas. """

from datetime import datetime, UTC
from pydantic import BaseModel, Field, ConfigDict
from aegis_shared.enums import RiskLevel, RuleFlag


class RuleFlagResult(BaseModel):
    """Result from a single rule evaluation."""
    rule: RuleFlag
    triggered: bool
    score: float = Field(..., ge=0.0, le=1.0)
    reason: str


class MLScore(BaseModel):
    """ML anomaly detection result."""
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    model_version: str
    fallback_used: bool = False


class LLMExplanation(BaseModel):
    """LLM-generated explanation."""
    summary: str
    risk_factors: list[str]
    recommendation: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    fallback_used: bool = False


class RiskResult(BaseModel):
    """Complete risk evaluation result."""
    transaction_id: str
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: RiskLevel
    rule_flags: list[RuleFlagResult]
    ml_score: MLScore | None = None
    llm_explanation: LLMExplanation | None = None
    rule_score: float = Field(..., ge=0.0, le=100.0)
    processing_time_ms: float
    worker_id: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(from_attributes=True)


class RiskResultResponse(BaseModel):
    """Public risk result response."""
    transaction_id: str
    risk_score: float
    risk_level: RiskLevel
    triggered_rules: list[str]
    explanation: LLMExplanation | None = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
