"""Custom exceptions for AegisRisk services."""


class AegisBaseException(Exception):
    """Base exception for all AegisRisk errors."""

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class TransactionNotFoundError(AegisBaseException):
    """Raised when a transaction is not found."""

    def __init__(self, transaction_id: str):
        super().__init__(
            message=f"Transaction {transaction_id} not found",
            code="TRANSACTION_NOT_FOUND",
        )


class DuplicateTransactionError(AegisBaseException):
    """Raised when a duplicate idempotency key is detected."""

    def __init__(self, idempotency_key: str):
        super().__init__(
            message=f"Duplicate transaction with idempotency key: {idempotency_key}",
            code="DUPLICATE_TRANSACTION",
        )


class InvalidTransactionStateError(AegisBaseException):
    """Raised when a transaction state transition is invalid."""

    def __init__(self, current_state: str, target_state: str):
        super().__init__(
            message=f"Invalid state transition from {current_state} to {target_state}",
            code="INVALID_STATE_TRANSITION",
        )


class RiskEvaluationError(AegisBaseException):
    """Raised when risk evaluation fails."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Risk evaluation failed: {reason}",
            code="RISK_EVALUATION_ERROR",
        )


class MLServiceError(AegisBaseException):
    """Raised when ML service encounters an error."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"ML service error: {reason}",
            code="ML_SERVICE_ERROR",
        )


class LLMServiceError(AegisBaseException):
    """Raised when LLM service encounters an error."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"LLM service error: {reason}",
            code="LLM_SERVICE_ERROR",
        )


class WebhookDeliveryError(AegisBaseException):
    """Raised when webhook delivery fails."""

    def __init__(self, url: str, reason: str):
        super().__init__(
            message=f"Webhook delivery to {url} failed: {reason}",
            code="WEBHOOK_DELIVERY_ERROR",
        )


class AuthenticationError(AegisBaseException):
    """Raised when authentication fails."""

    def __init__(self, reason: str = "Invalid or expired token"):
        super().__init__(
            message=f"Authentication failed: {reason}",
            code="AUTHENTICATION_ERROR",
        )


class RateLimitExceededError(AegisBaseException):
    """Raised when rate limit is exceeded."""

    def __init__(self, client_id: str):
        super().__init__(
            message=f"Rate limit exceeded for client: {client_id}",
            code="RATE_LIMIT_EXCEEDED",
        )
