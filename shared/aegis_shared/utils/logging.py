import logging
import sys
import structlog


def setup_logger(service_name: str, log_level: str = "INFO") -> structlog.BoundLogger:
    """Configure structured JSON logging for a service.

    Args:
        service_name: Name of the microservice.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).

    Returns:
        Configured structlog bound logger.
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    logger = structlog.get_logger(service=service_name)
    return logger


def get_logger(service_name: str | None = None) -> structlog.BoundLogger:
    """Get a logger instance, optionally binding a service name.

    Args:
        service_name: Optional service name to bind.

    Returns:
        A structlog bound logger.
    """
    logger = structlog.get_logger()
    if service_name:
        logger = logger.bind(service=service_name)
    return logger
