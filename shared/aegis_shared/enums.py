"""Shared enumerations for AegisRisk services."""

from enum import Enum


class TransactionStatus(str, Enum):
    """Transaction lifecycle states."""
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DEAD_LETTERED = "DEAD_LETTERED"

class TransactionType(str, Enum):
    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    WITHDRAWAL = "WITHDRAWAL"
    DEPOSIT = "DEPOSIT"


class RiskLevel(str, Enum):
    """Risk categorization levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RuleFlag(str, Enum):
    """Rule-based detection flags."""
    HIGH_VALUE = "HIGH_VALUE"
    VELOCITY_SPIKE = "VELOCITY_SPIKE"
    GEO_MISMATCH = "GEO_MISMATCH"
    DEVICE_CHANGE = "DEVICE_CHANGE"
    UNUSUAL_HOUR = "UNUSUAL_HOUR"
    ACCOUNT_AGE_RISK = "ACCOUNT_AGE_RISK"
    FAILED_BURST = "FAILED_BURST"


class WebhookStatus(str, Enum):
    """Webhook delivery status."""
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
