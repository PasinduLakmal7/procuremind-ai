from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from shared.extraction.schemas import StructuredQuotationData


# --- Typed contracts for downstream services (Stage 4) ---
class RiskAssessmentResult(BaseModel):
    assessment_id: Optional[str] = None
    supplier_risk_tier: str = "LOW"
    risk_score: Optional[float] = 0.18
    confidence: float = 0.85
    data_sufficiency: str = "SUFFICIENT"
    observation_count: int = 5
    explanation: str = "Baseline deterministic risk profile calculated."
    model_version: str = "rule-baseline-v1.0"


class OptimizationResult(BaseModel):
    scenario_id: Optional[str] = None
    top_recommended_supplier_id: Optional[str] = None
    recommended_ranking: int = 1
    composite_score: float = 0.892
    cost_normalized: float = 0.92
    delivery_normalized: float = 0.85
    quality_normalized: float = 0.88
    reliability_normalized: float = 0.82
    rankings: List[Dict[str, Any]] = Field(default_factory=list)
    algorithm: str = "mcda_weighted_scoring_v1.0"


class ExplainabilityReport(BaseModel):
    top_supplier_rationale: str
    excluded_suppliers_rationale: List[str] = Field(default_factory=list)
    criteria_weights_applied: Dict[str, float] = Field(default_factory=dict)
    scoring_breakdown: Dict[str, Any] = Field(default_factory=dict)
    risk_method: str = "Deterministic Rule-Based Baseline (v1.0)"
    uncertainties_and_missing_data: List[str] = Field(default_factory=list)
    policy_compliance: Dict[str, Any] = Field(default_factory=dict)


class PolicyValidationResult(BaseModel):
    policy_compliant: bool = True
    sri_lanka_vat_checked: bool = True
    single_source_procurement_allowed: bool = True
    notes: List[str] = Field(default_factory=list)


# --- Workflow Schemas ---
class StartWorkflowRequest(BaseModel):
    purchase_request_id: str = Field(..., min_length=1)
    document_id: Optional[str] = None
    supplier_id: Optional[str] = None
    extracted_data: Optional[StructuredQuotationData] = None
    is_verified: bool = False
    supplier_historical_orders: Optional[List[Dict[str, Any]]] = None
    supplier_quality_records: Optional[List[Dict[str, Any]]] = None
    alternative_candidates: Optional[List[Dict[str, Any]]] = None
    evaluation_weights: Optional[Dict[str, float]] = None


class ResumeWorkflowRequest(BaseModel):
    updated_extracted_data: Optional[StructuredQuotationData] = None
    confirm_human_verification: bool = True


class WorkflowStepLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    step_name: str
    status: str
    output_data: Optional[str] = None
    timestamp: datetime


class WorkflowStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    workflow_id: str
    correlation_id: str
    organization_id: str
    purchase_request_id: str
    document_id: Optional[str] = None
    supplier_id: Optional[str] = None
    status: str  # STARTED, WAITING_FOR_HUMAN_REVIEW, RUNNING, COMPLETED, FAILED
    current_step: str
    requires_human_review: bool
    human_review_reason: Optional[str] = None
    state: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
