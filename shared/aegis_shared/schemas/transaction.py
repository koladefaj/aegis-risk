""" Transaction related pydantic schemas. """

import re
from datetime import datetime, UTC
from decimal import Decimal
from typing import Literal
from uuid import UUID

from aegis_shared.enums import TransactionStatus
from pydantic import BaseModel, Field, field_validator, ConfigDict, model_validator

IDEMPOTENCY_PATTERN = re.compile(r"^[a-zA-Z0-9-_]{10,64}$")


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""
    idempotency_key: str | None = Field(None, min_length=10, max_length=64, description="Optional unique key (transaction reference prefered). Auto-generated if not provided.")
    amount: Decimal = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code")
    sender_id: str = Field(..., min_length=1, max_length=64, description="Sender account ID")
    receiver_id: str = Field(..., min_length=1, max_length=64, description="Receiver account ID")
    sender_country: str = Field(..., min_length=2, max_length=2, description="Sender ISO country code")
    receiver_country: str = Field(..., min_length=2, max_length=2, description="Receiver ISO country code")
    device_fingerprint: str | None = Field(None, max_length=128, description="Device fingerprint hash")
    channel: Literal["web", "mobile", "api"] = Field(default="web", description="Transaction channel (web, mobile, api)")
    transaction_metadata: dict[str, str] | None = Field(default=None, description="Additional metadata")

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, v: str | None) -> str | None:
        if v is None:
            return v

        if not IDEMPOTENCY_PATTERN.match(v):
            raise ValueError("Invalid idempotency key format")

        return v

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v: str) -> str:
        return v.upper()

    @field_validator("sender_country", "receiver_country")
    @classmethod
    def country_uppercase(cls, v: str) -> str:
        return v.upper()
    
    @model_validator(mode="after")
    def validate_accounts(self):
        if self.sender_id == self.receiver_id:
            raise ValueError("Sender and receiver cannot be the same")
        return self
    
    @field_validator("amount")
    def validate_amount_precision(cls, v: Decimal):
        if v.as_tuple().exponent < -2:
            raise ValueError("Amount cannot exceed 2 decimal places")
        return v.quantize(Decimal("0.01"))

class TransactionAccepted(BaseModel):
    """Response when a transaction is accepted for processing."""
    transaction_id: UUID
    idempotency_key: str
    amount: Decimal
    currency: str
    sender_id: str
    receiver_id: str
    sender_country: str
    receiver_country: str
    status: str = "RECEIVED"
    created_at: datetime
    already_existed: bool = False


    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def parse_amount(cls, values):
        amt = values.get("amount") if isinstance(values, dict) else getattr(values, "amount", None)
        if isinstance(amt, str):
            if isinstance(values, dict):
                values["amount"] = Decimal(amt)
            else:
                setattr(values, "amount", Decimal(amt))
        return values


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
    status: TransactionStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def parse_amount(cls, values):
        amt = values.get("amount") if isinstance(values, dict) else getattr(values, "amount", None)
        if isinstance(amt, str):
            if isinstance(values, dict):
                values["amount"] = Decimal(amt)
            else:
                setattr(values, "amount", Decimal(amt))
        return values

    model_config = ConfigDict(from_attributes=True)


class TransactionEvent(BaseModel):
    """Schema for SQS transaction event."""
    transaction_id: UUID
    idempotency_key: str
    amount: Decimal
    currency: str
    sender_id: str
    receiver_id: str
    sender_country: str
    receiver_country: str
    device_fingerprint: str | None = None
    ip_address: str | None = None
    channel: Literal["web", "mobile", "api"] = Field(default="web")
    transaction_metadata: dict[str, str] | None = Field(default=None, max_length=20)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="before")
    @classmethod
    def parse_amount(cls, values):
        amt = values.get("amount") if isinstance(values, dict) else getattr(values, "amount", None)
        if isinstance(amt, str):
            if isinstance(values, dict):
                values["amount"] = Decimal(amt)
            else:
                setattr(values, "amount", Decimal(amt))
        return values

class TransactionUpdate(BaseModel):
    transaction_id: UUID
    previous_status: str
    new_status: str
    success: bool

class ExplanationStreamChunk(BaseModel):
    """A single chunk of the LLM explanation stream."""
    transaction_id: UUID
    chunk_type: str  # "token", "risk_factors", "recommendation", "done"
    content: str