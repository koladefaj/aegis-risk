""" Auth api routes """

import httpx
from app.config import settings
from fastapi import APIRouter, HTTPException, status
from aegis_shared.schemas.auth import TokenResponse
from fastapi.responses import RedirectResponse


router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/login")
def login():
    """Redirect user to Cognito Hosted UI"""
    
    return RedirectResponse(settings.LOGIN_URL)

@router.get("/callback", response_model=TokenResponse)
async def callback(code: str):

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.COGNITO_DOMAIN}/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "client_id": settings.COGNITO_APP_CLIENT_ID,
                "client_secret": settings.COGNITO_APP_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.COGNITO_REDIRECT_URI
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bad Request"
            )
        
        tokens = response.json()

        return TokenResponse(
            access_token=tokens["access_token"],
            id_token=tokens["id_token"],
            refresh_token=tokens.get("refresh_token"),
            token_type="Bearer",
        )
    
@router.get("/logout")
def logout():
    """Redirect to Cognito logout endpoint."""

    url = (
        f"{settings.COGNITO_DOMAIN}/logout"
        f"?client_id={settings.COGNITO_APP_CLIENT_ID}"
        f"&logout_uri=http://localhost:8000/"
    )
    
    return RedirectResponse(url)


