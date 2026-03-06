from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ConfigDict


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""
    amount: Decimal = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code")
    sender_id: str = Field(..., min_length=1, max_length=64, description="Sender account ID")
    receiver_id: str = Field(..., min_length=1, max_length=64, description="Receiver account ID")
    sender_country: str = Field(..., min_length=2, max_length=2, description="Sender ISO country code")
    receiver_country: str = Field(..., min_length=2, max_length=2, description="Receiver ISO country code")
    device_fingerprint: str | None = Field(None, max_length=256, description="Device fingerprint hash")
    ip_address: str | None = Field(None, max_length=45, description="Client IP address")
    channel: str = Field(default="web", description="Transaction channel (web, mobile, api)")
    metadata: dict | None = Field(default=None, description="Additional metadata")

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v: str) -> str:
        return v.upper()

    @field_validator("sender_country", "receiver_country")
    @classmethod
    def country_uppercase(cls, v: str) -> str:
        return v.upper()


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    transaction_id: UUID
    idempotency_key: str
    amount: Decimal
    currency: str
    sender_id: str
    receiver_id: str
    sender_country: str
    receiver_country: str
    status: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TransactionEvent(BaseModel):
    """Schema for SQS transaction event."""
    transaction_id: str
    idempotency_key: str
    amount: float
    currency: str
    sender_id: str
    receiver_id: str
    sender_country: str
    receiver_country: str
    device_fingerprint: str | None = None
    ip_address: str | None = None
    channel: str = "web"
    metadata: dict | None = None
    created_at: str
