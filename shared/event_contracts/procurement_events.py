"""Specific event payload contracts for procurement and documents."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PurchaseRequestSubmittedPayload(BaseModel):
    purchase_request_id: str
    request_number: str
    organization_id: str
    title: str
    budget_limit: float
    currency: str = "LKR"
    submitted_at: datetime
    submitted_by: str


class QuotationDocumentUploadedPayload(BaseModel):
    document_id: str
    organization_id: str
    file_name: str
    file_size: int
    content_type: str
    storage_path: str
    checksum_sha256: str
    purchase_request_id: Optional[str] = None
    supplier_id: Optional[str] = None
    quotation_id: Optional[str] = None
    uploaded_at: datetime

