from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    organization_id: UUID
    roles: List[str] = Field(default=["procurement_officer"], description="List of role names")


class UserInvite(UserBase):
    organization_id: UUID
    roles: List[str] = Field(default=["procurement_officer"])


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    is_active: bool
    is_verified: bool
    roles: List[str] = []
    created_at: datetime
    updated_at: datetime

