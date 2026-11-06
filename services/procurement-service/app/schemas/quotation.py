from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class QuotationItemCreate(BaseModel):
    item_name: str = Field(..., min_length=1)
    quantity: float = Field(..., gt=0)
    unit_of_measure: str = Field(default="UNITS", max_length=50)
    unit_price: float = Field(..., ge=0)
    total_price: Optional[float] = None
    lead_time_days: int = Field(default=14, ge=0)


class QuotationItemResponse(QuotationItemCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    quotation_id: str
    total_price: float
    created_at: datetime


class QuotationCreate(BaseModel):
    supplier_id: str = Field(..., description="Target supplier identifier")
    quotation_number: str = Field(..., min_length=1, max_length=100)
    version: int = Field(default=1, ge=1)
    total_cost: float = Field(..., gt=0)
    currency: str = Field(default="LKR", max_length=10)
    submitted_date: Optional[datetime] = None
    validity_date: Optional[datetime] = None
    estimated_delivery_days: int = Field(default=14, gt=0)
    warranty_terms: Optional[str] = None
    payment_terms: Optional[str] = Field(default="Net 30")
    document_id: Optional[str] = Field(default=None, description="Uploaded quotation document reference")
    metadata_notes: Optional[str] = None
    items: Optional[List[QuotationItemCreate]] = None


class QuotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    purchase_request_id: str
    supplier_id: str
    quotation_number: str
    version: int
    total_cost: float
    currency: str
    submitted_date: datetime
    validity_date: Optional[datetime]
    estimated_delivery_days: int
    warranty_terms: Optional[str]
    payment_terms: Optional[str]
    status: str
    document_id: Optional[str]
    metadata_notes: Optional[str]
    items: List[QuotationItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
