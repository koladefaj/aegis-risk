"""JWT Auth with AWS Conginto """

import httpx
import jwt
from jwt.exceptions import PyJWTError, ExpiredSignatureError
from jwt.algorithms import RSAAlgorithm
from fastapi import HTTPException, status
from cachetools import cached, TTLCache
from app.config import settings
from aegis_shared.utils.logging import get_logger
import json

logger = get_logger("auth")


@cached(cache=TTLCache(maxsize=1, ttl=3600))
def get_jwks() -> dict:

    response = httpx.get(settings.JWKS_URL, timeout=10)
    response.raise_for_status()

    return response.json()


def get_public_key(kid: str):
    """Find the JWK matching `kid` and convert it to an RSA public key object."""

    jwks = get_jwks()

    jwk = next(
        (k for k in jwks["keys"] if k["kid"] == kid),
        None
    )

    if not jwk:
        # kid not found possible keys may have rotated, bust cache and retry once
        get_jwks.cache_clear()
        
        jwks = get_jwks()
        jwk = next((k for k in jwks["keys"] if k["kid"] == kid), None)

    if not jwk:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Public key not found — unknown token kid"
        )

    # PyJWT needs RSA key object
    return RSAAlgorithm.from_jwk(json.dumps(jwk))


def verify_token(token: str) -> dict:
    """
    Verify a Cognito JWT (RS256) and return its claims.
    Raises HTTP 401 on any failure.
    """
    try:
        header = jwt.get_unverified_header(token)
        public_key = get_public_key(header["kid"])

        claims = jwt.decode(
            token,
            public_key,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.COGNITO_APP_CLIENT_ID,
            issuer=settings.ISSUER,                 
            options={"verify_exp": True},
        )

        return claims

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
