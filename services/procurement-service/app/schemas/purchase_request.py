from datetime import datetime
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict


class LineItem(BaseModel):
    item_name: str = Field(..., min_length=1)
    specification: Optional[str] = None
    quantity: float = Field(..., gt=0)
    unit_of_measure: str = Field(default="UNITS", max_length=50)
    target_unit_price: float = Field(default=0.0, ge=0)


class PurchaseRequestItemCreate(LineItem):
    pass


class PurchaseRequestItemResponse(LineItem):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    purchase_request_id: str
    created_at: datetime


class CandidateSupplierCreate(BaseModel):
    supplier_id: str = Field(..., min_length=1)
    supplier_name: str = Field(..., min_length=1, max_length=255)
    supplier_email: Optional[str] = None


class CandidateSupplierResponse(CandidateSupplierCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    purchase_request_id: str
    invitation_status: str
    invited_at: datetime


class PurchaseRequestBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    category: str = Field(default="Raw Materials", max_length=100)
    priority: str = Field(default="MEDIUM", description="LOW, MEDIUM, HIGH, URGENT")
    budget_limit: float = Field(..., ge=0)
    currency: str = Field(default="LKR", max_length=10)
    required_delivery_date: Optional[datetime] = None
    evaluation_criteria: Optional[str] = None


class PurchaseRequestCreate(PurchaseRequestBase):
    items: Optional[List[PurchaseRequestItemCreate]] = None


class PurchaseRequestUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    budget_limit: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = None
    required_delivery_date: Optional[datetime] = None
    evaluation_criteria: Optional[str] = None


class PurchaseRequestStatusUpdate(BaseModel):
    status: str = Field(..., description="DRAFT, SUBMITTED, UNDER_EVALUATION, APPROVED, REJECTED, CANCELLED")


class ProcurementAuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    purchase_request_id: str
    event_type: str
    performed_by: str
    old_state: Optional[str] = None
    new_state: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime


class PurchaseRequestResponse(PurchaseRequestBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    created_by_user_id: str
    request_number: str
    status: str
    items: List[PurchaseRequestItemResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PurchaseRequestDecision(BaseModel):
    action: str = Field(..., description="APPROVE or REJECT")
    decision_reason: str = Field(..., min_length=5, description="Auditable justification for the human procurement decision")
    selected_supplier_id: Optional[str] = Field(default=None, description="Supplier approved for contract award")
    selected_quotation_id: Optional[str] = Field(default=None, description="Winning quotation ID")


class PurchaseRequestDetailResponse(PurchaseRequestResponse):
    candidate_suppliers: List[CandidateSupplierResponse] = Field(default_factory=list)
    audit_events: List[ProcurementAuditEventResponse] = Field(default_factory=list)

