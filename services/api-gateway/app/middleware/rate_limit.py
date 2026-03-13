"""Redis-backed rate limiting middleware with slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings
from aegis_shared.utils.logging import get_logger
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

logger = get_logger("rate-limiter")

storage_uri = settings.REDIS_URL if settings.ENVIRONMENT != "testing" else "memory://"
IS_TESTING = settings.ENVIRONMENT == "testing"

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"{storage_uri}",
    strategy="sliding-window",
    enabled=not IS_TESTING,
)


def init_limiter_error_handlers(app):

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
        ip = request.client.host if request.client else "unknown"
        logger.warning(
            "rate_limit_exceeded",
            ip=ip,                   
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please slow down."},
        )