from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    purchase_request_id: Optional[str] = None
    supplier_id: Optional[str] = None
    quotation_id: Optional[str] = None
    file_name: str
    file_size: int
    content_type: str
    storage_path: str
    status: str
    checksum_sha256: Optional[str] = None
    created_at: datetime
    updated_at: datetime

