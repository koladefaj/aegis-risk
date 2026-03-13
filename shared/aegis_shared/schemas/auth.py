""" Authentication Pydantic Schemas."""

from pydantic import BaseModel, field_validator

class AuthUser(BaseModel):
    sub: str
    email: str
    name: str = ""
    roles: list[str] = []

    @field_validator("email")
    @classmethod
    def email_must_not_be_empty(cls, v):
        if not v:
            raise ValueError("Email claim missing from token")
        return v

    @property
    def is_admin(self) -> bool:
        return "admin" in self.roles

    @property
    def is_client(self) -> bool:
        return "client" in self.roles
    
class TokenResponse(BaseModel):
    access_token: str
    id_token: str
    refresh_token: str | None = None
    token_type: str