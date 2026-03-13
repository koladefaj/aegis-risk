"""AegisRisk API Gateway — FastAPI application entrypoint."""

import grpc
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.middleware.correlation import CorrelationIdMiddleware

from app.grpc_clients.transaction_client import TransactionGRPCClient
from aegis_shared.utils.logging import setup_logger
from aegis_shared.utils.redis import init_redis


from app.routers.auth import router as auth_router
from app.routers.transactions import router as transaction_router
from app.dependencies import get_current_user, require_role, AuthUser

logger = setup_logger("api-gateway", settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Initialize Redis
    init_redis(settings.REDIS_URL)
    
    # Initialize the client
    client = TransactionGRPCClient()
    
    # Store it in app state so dependencies can find it
    app.state.transaction_client = client
    
    logger.info("api_gateway_starting", port=settings.API_GATEWAY_PORT)
    yield
    
    # Clean up 
    await client.close()
    logger.info("api_gateway_shutting_down")


app = FastAPI(
    title="AegisRisk API Gateway",
    description="Real-Time Distributed Fraud Detection Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization","Content-Type","Idempotency-Key"],
)


@app.exception_handler(grpc.RpcError)
async def grpc_exception_handler(request: Request, exc: grpc.RpcError):
    """
    Globally map gRPC codes to HTTP codes.
    """
    # Map of gRPC codes -> (HTTP status, Generic Message)
    mapping = {
        grpc.StatusCode.NOT_FOUND: (status.HTTP_404_NOT_FOUND, "Resource not found"),
        grpc.StatusCode.ALREADY_EXISTS: (status.HTTP_409_CONFLICT, "Resource already exists"),
        grpc.StatusCode.INVALID_ARGUMENT: (status.HTTP_400_BAD_REQUEST, "Invalid arguments"),
        grpc.StatusCode.PERMISSION_DENIED: (status.HTTP_403_FORBIDDEN, "Permission denied"),
        grpc.StatusCode.UNAUTHENTICATED: (status.HTTP_401_UNAUTHORIZED, "Unauthenticated"),
    }

    code = exc.code()
    http_status, default_msg = mapping.get(code, (status.HTTP_502_BAD_GATEWAY, "Upstream service error"))
    
    # Use the gRPC 'details' if available, otherwise fallback to default_msg
    detail = exc.details() or default_msg

    return JSONResponse(
        status_code=http_status,
        content={"detail": detail},
    )

app.include_router(auth_router)
app.include_router(transaction_router)


# ── Protected route examples ──────────────────────────────

@app.get("/me")
def get_me(user: AuthUser = Depends(get_current_user)):
    """Any authenticated user."""
    return {"sub": user.sub, "email": user.email, "name": user.name}


@app.get("/admin/dashboard")
def admin_only(user: AuthUser = Depends(require_role("admin"))):
    """Only users in the Cognito 'admin' group."""
    return {"message": f"Welcome admin {user.email}"}


@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.API_GATEWAY_PORT,
        reload=True,
    )
