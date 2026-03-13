""" Webhook related pydantic schemas. """

from datetime import datetime, timezone
from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from aegis_shared.enums import WebhookStatus


class WebhookRegistration(BaseModel):
    """Schema for registering a webhook endpoint."""
    url: HttpUrl
    client_id: str = Field(..., min_length=1, max_length=64)
    events: list[str] = Field(default_factory=lambda: ["risk.completed"])
    secret: str | None = Field(None, description="Client-provided webhook secret override")


class WebhookRegistrationResponse(BaseModel):
    """Schema for webhook registration response."""
    webhook_id: str
    url: str
    client_id: str
    events: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookPayload(BaseModel):
    """Schema for webhook delivery payload."""
    event: str
    transaction_id: str
    risk_score: float
    risk_level: str
    triggered_rules: list[str]
    explanation_summary: str | None = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WebhookDeliveryRecord(BaseModel):
    """Schema for tracking webhook delivery attempts."""
    webhook_id: str
    transaction_id: str
    attempt_count: int = 0
    last_status_code: int | None = None
    status: WebhookStatus = WebhookStatus.PENDING
    delivered_at: datetime | None = None
    last_error: str | None = None
