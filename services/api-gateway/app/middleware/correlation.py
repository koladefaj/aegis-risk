"""Correlation ID middleware — injects or propagates a unique ID per request."""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars
from app.config import settings
from aegis_shared.utils.tracing import set_correlation_id, clear_correlation_id


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware that ensures every request has a correlation ID.

    If the incoming request contains a correlation ID header, it is used.
    else, a new UUID is generated. The ID is injected into the
    response headers and bound to structlog context for the request lifetime.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        
        # Extract or generate correlation ID
        correlation_id = request.headers.get(
            settings.CORRELATION_ID_HEADER,
            str(uuid.uuid4()),
        )

        # Bind to structlog context
        set_correlation_id(correlation_id)

        # Store in request state for downstream use
        request.state.correlation_id = correlation_id

        # logging context bind
        bind_contextvars(
            request_path=request.url.path,
            method=request.method,
        )

        try:
            response = await call_next(request)
            response.headers[settings.CORRELATION_ID_HEADER] = correlation_id
            
            return response
        finally:
            clear_correlation_id()
            clear_contextvars()
