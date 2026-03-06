"""Correlation ID utilities for distributed tracing."""

import uuid
import structlog
from contextvars import ContextVar

# Context variable to hold the current correlation ID
correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def generate_correlation_id() -> str:
    """Generate a new unique correlation ID."""
    return str(uuid.uuid4())


def get_correlation_id() -> str | None:
    """Get the current correlation ID from context."""
    return correlation_id_ctx.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID in the current context and bind to structlog.

    Args:
        correlation_id: The correlation ID to set.
    """
    correlation_id_ctx.set(correlation_id)
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def clear_correlation_id() -> None:
    """Clear the correlation ID from the current context."""
    correlation_id_ctx.set(None)
    structlog.contextvars.unbind_contextvars("correlation_id")
