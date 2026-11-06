from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Official company / factory name")
    registration_number: Optional[str] = Field(default=None, max_length=100)
    industry: str = Field(default="Manufacturing", max_length=100)


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationResponse(OrganizationBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

