from datetime import datetime
from pydantic import BaseModel, Field
from shared.aegis_shared.enums import RiskLevel, TransactionStatus


class AuditLogEntry(BaseModel):
    """Immutable audit log entry for every state transition."""
    transaction_id: str
    previous_status: TransactionStatus | None = None
    new_status: TransactionStatus
    risk_score: float | None = None
    risk_level: RiskLevel | None = None
    rule_flags_triggered: list[str] = Field(default_factory=list)
    ml_score: float | None = None
    llm_output_summary: str | None = None
    processing_time_ms: float | None = None
    failure_reason: str | None = None
    failure_metadata: dict | None = None
    retry_count: int = 0
    worker_id: str | None = None
    correlation_id: str | None = None
    timestamp: datetime
