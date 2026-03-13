"""Dependency injection for API Gateway — JWT auth and rate limiting."""

from fastapi import HTTPException, status, Depends, Request
from aegis_shared.schemas.auth import AuthUser
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.grpc_clients.transaction_client import TransactionGRPCClient
from app.middleware.auth.cognito import verify_token

oauth2_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme)
) -> AuthUser:
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    
    claims = verify_token(token.credentials)

    groups = claims.get("cognito:groups", [])

    return AuthUser(
        sub=claims["sub"],
        email=claims.get("email") or claims.get("email", ""),
        name=claims.get("name") or claims.get("email", ""),
        roles=groups,
    )


def require_role(role: str):
    """Factory for role-based route guards."""
    
    def _check_role(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if role not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Denied"
            )
        return user
    return _check_role

def get_transaction_client(request: Request) -> TransactionGRPCClient:
    """
    Retrieve the gRPC client from the application state.
    """
    client = getattr(request.app.state, "transaction_client", None)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transaction service client not initialized"
        )
    return client