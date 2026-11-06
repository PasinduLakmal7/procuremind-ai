from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user_id: UUID
    organization_id: UUID
    roles: List[str]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class CurrentUserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    organization_id: UUID
    organization_name: Optional[str] = None
    roles: List[str]
    is_active: bool

