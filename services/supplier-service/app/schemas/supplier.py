from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class SupplierBase(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=255, description="Supplier business name")
    contact_email: EmailStr
    contact_phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=500)
    city: str = Field(default="Colombo", max_length=100)
    country: str = Field(default="Sri Lanka", max_length=100)
    category: str = Field(default="Raw Materials", max_length=100)
    tax_id: Optional[str] = Field(default=None, max_length=100, description="VAT or SVAT number")
    tier: str = Field(default="TIER_2", description="TIER_1, TIER_2, or TIER_3")
    compliance_status: str = Field(default="VERIFIED", description="VERIFIED, PENDING, or REJECTED")


class SupplierCreate(SupplierBase):
    rating: Optional[float] = Field(default=3.5, ge=0.0, le=5.0)


class SupplierUpdate(BaseModel):
    company_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None
    tax_id: Optional[str] = None
    rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    tier: Optional[str] = None
    compliance_status: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    rating: float
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Contacts ---
class SupplierContactCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=50)
    designation: Optional[str] = Field(default="Sales Representative", max_length=100)
    is_primary: bool = False


class SupplierContactResponse(SupplierContactCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    supplier_id: str
    created_at: datetime


# --- Categories ---
class SupplierCategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)


class SupplierCategoryResponse(SupplierCategoryCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    created_at: datetime


# --- Delivery Records ---
class SupplierDeliveryRecordCreate(BaseModel):
    po_reference: str = Field(..., min_length=1, max_length=100)
    promised_delivery_date: datetime
    actual_delivery_date: datetime
    on_time: bool
    delay_days: int = Field(default=0, ge=0)
    source_system: str = Field(..., min_length=2, max_length=100, description="Audit source system e.g. ERP_EXPORT, GRN_LOG")
    notes: Optional[str] = None


class SupplierDeliveryRecordResponse(SupplierDeliveryRecordCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    supplier_id: str
    recorded_by: str
    created_at: datetime


# --- Quality Records ---
class SupplierQualityRecordCreate(BaseModel):
    batch_reference: str = Field(..., min_length=1, max_length=100)
    defect_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    incident_severity: str = Field(default="NONE", description="NONE, MINOR, MAJOR, CRITICAL")
    passed: bool = True
    source_system: str = Field(..., min_length=2, max_length=100, description="Audit source system e.g. QA_INSPECTION_LOG")
    incident_details: Optional[str] = None


class SupplierQualityRecordResponse(SupplierQualityRecordCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    supplier_id: str
    recorded_by: str
    created_at: datetime


# --- Performance Summary ---
class SupplierPerformanceSummary(BaseModel):
    supplier_id: str
    organization_id: str
    company_name: str
    total_deliveries: int
    on_time_deliveries: int
    on_time_delivery_rate: float  # Percentage 0-100
    average_delay_days: float
    total_quality_inspections: int
    passed_inspections: int
    quality_pass_rate: float  # Percentage 0-100
    average_defect_rate: float
    critical_incidents_count: int
    computed_composite_score: float  # Scale 0-5
