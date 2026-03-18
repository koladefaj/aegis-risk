"""Shared enumerations for AegisRisk services."""

from enum import Enum


class TransactionStatus(str, Enum):
    """Transaction lifecycle states."""
    RECEIVED  = "RECEIVED"   
    APPROVED  = "APPROVED"    
    BLOCKED   = "BLOCKED"     # risk engine blocked — bank must decline
    REVIEW    = "REVIEW"      # risk engine uncertain — manual review needed
    PROCESSING = "PROCESSING" # being processed downstream
    COMPLETED  = "COMPLETED"  
    FAILED     = "FAILED"    
    DEAD_LETTERED = "DEAD_LETTERED"

    @classmethod
    def from_risk_decision(cls, decision: str) -> "TransactionStatus":
        """Map a RiskDecision value to a TransactionStatus.
        
        Used by transaction-service after receiving risk-engine response.
        Fails safe to REVIEW — never block due to a scoring error.
        """
        return {
            "APPROVE": cls.APPROVED,
            "BLOCK":   cls.BLOCKED,
            "REVIEW":  cls.REVIEW,
        }.get(decision, cls.REVIEW)  # default REVIEW if unknown decision


class TransactionType(str, Enum):
    TRANSFER   = "TRANSFER"
    PAYMENT    = "PAYMENT"
    WITHDRAWAL = "WITHDRAWAL"
    DEPOSIT    = "DEPOSIT"


class RiskLevel(str, Enum):
    """Risk categorization levels."""
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"  # ✅ added — for score >= 0.95

    @classmethod
    def from_score(cls, score: float) -> "RiskLevel":
        """Map a 0.0–1.0 risk score to a RiskLevel.
        
        Used by risk-engine after ML inference.
        """
        if score >= 0.95:
            return cls.CRITICAL
        if score >= 0.80:
            return cls.HIGH
        if score >= 0.50:
            return cls.MEDIUM
        return cls.LOW


class RiskDecision(str, Enum):
    """Final decision after risk evaluation."""
    APPROVE = "APPROVE"  # ✅ removed trailing commas — they made these tuples
    REVIEW  = "REVIEW"
    BLOCK   = "BLOCK"

    @classmethod
    def from_score(cls, score: float, block_threshold: float = 0.80, review_threshold: float = 0.50) -> "RiskDecision":
        """Map a 0.0–1.0 risk score to a decision.
        
        Used by risk-engine to make final APPROVE/BLOCK/REVIEW call.
        Thresholds are configurable — banks may want different sensitivity.
        """
        if score >= block_threshold:
            return cls.BLOCK
        if score >= review_threshold:
            return cls.REVIEW
        return cls.APPROVE


class RuleFlag(str, Enum):
    """Rule-based detection flags."""
    HIGH_VALUE       = "HIGH_VALUE"
    VELOCITY_SPIKE   = "VELOCITY_SPIKE"
    GEO_MISMATCH     = "GEO_MISMATCH"
    DEVICE_CHANGE    = "DEVICE_CHANGE"
    UNUSUAL_HOUR     = "UNUSUAL_HOUR"
    ACCOUNT_AGE_RISK = "ACCOUNT_AGE_RISK"
    FAILED_BURST     = "FAILED_BURST"
    # ✅ added — needed by risk-engine feature engineering
    HIGH_RISK_CORRIDOR = "HIGH_RISK_CORRIDOR"
    AMOUNT_ANOMALY     = "AMOUNT_ANOMALY"
    NEW_RECEIVER       = "NEW_RECEIVER"
    NEW_DEVICE         = "NEW_DEVICE"
    PRIOR_FRAUD        = "PRIOR_FRAUD"
    ROUND_AMOUNT       = "ROUND_AMOUNT"


class WebhookStatus(str, Enum):
    """Webhook delivery status."""
    PENDING   = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED    = "FAILED"
    RETRYING  = "RETRYING"