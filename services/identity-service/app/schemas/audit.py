from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[UUID]
    organization_id: Optional[UUID]
    action: str
    status: str
    ip_address: Optional[str]
    details: Optional[str]
    created_at: datetime

