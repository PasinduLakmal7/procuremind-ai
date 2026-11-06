"""Strict Pydantic schemas for structured quotation extraction, evidence, and validation."""
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class ExtractedLineItem(BaseModel):
    item_name: str = Field(..., min_length=1)
    specification: Optional[str] = None
    quantity: float = Field(..., gt=0)
    unit_of_measure: str = Field(default="UNITS")
    unit_price: float = Field(..., ge=0)
    total_price: float = Field(..., ge=0)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)


class FieldEvidence(BaseModel):
    field_name: str
    source_text: str
    page_number: Optional[int] = 1
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    extraction_method: str = Field(default="DIRECT_TEXT_PARSE")  # REGEX, SPREADSHEET_PARSE, OCR, LLM


class StructuredQuotationData(BaseModel):
    supplier_name: Optional[str] = None
    quotation_number: Optional[str] = None
    document_date: Optional[str] = None
    currency: str = Field(default="LKR")
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = 0.0
    discount_amount: Optional[float] = 0.0
    total_cost: Optional[float] = None
    delivery_lead_time_days: Optional[int] = 14
    payment_terms: Optional[str] = "Net 30"
    warranty_terms: Optional[str] = None
    line_items: List[ExtractedLineItem] = Field(default_factory=list)

    # Verification and Validation Metadata
    overall_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    arithmetic_valid: bool = True
    flagged_reasons: List[str] = Field(default_factory=list)
    evidence: Dict[str, FieldEvidence] = Field(default_factory=dict)
    extraction_method: str = "STRUCTURED_PARSER"


class ExtractionCorrectionRequest(BaseModel):
    supplier_name: Optional[str] = None
    quotation_number: Optional[str] = None
    currency: Optional[str] = None
    total_cost: Optional[float] = None
    delivery_lead_time_days: Optional[int] = None
    payment_terms: Optional[str] = None
    warranty_terms: Optional[str] = None
    line_items: Optional[List[ExtractedLineItem]] = None


class ExtractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    organization_id: str
    purchase_request_id: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    quotation_number: Optional[str] = None
    currency: str
    total_cost: Optional[float] = None
    overall_confidence: float
    arithmetic_valid: bool
    is_verified: bool
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    flagged_reasons: List[str] = Field(default_factory=list)
    structured_data: StructuredQuotationData
    created_at: datetime
    updated_at: datetime

