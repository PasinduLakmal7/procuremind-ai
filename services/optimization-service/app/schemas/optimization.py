from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class CriteriaWeights(BaseModel):
    cost_weight: float = Field(default=0.40, ge=0.0, le=1.0, description="Cost minimization weight (0.0 - 1.0)")
    delivery_weight: float = Field(default=0.25, ge=0.0, le=1.0, description="Lead time minimization weight (0.0 - 1.0)")
    quality_weight: float = Field(default=0.20, ge=0.0, le=1.0, description="Quality maximization weight (0.0 - 1.0)")
    reliability_weight: float = Field(default=0.15, ge=0.0, le=1.0, description="Reliability (1 - risk) weight (0.0 - 1.0)")

    @model_validator(mode="after")
    def validate_weights_sum(self):
        total = self.cost_weight + self.delivery_weight + self.quality_weight + self.reliability_weight
        if abs(total - 1.0) > 0.005:
            raise ValueError(f"Criteria weights must sum to exactly 1.0 (current sum: {total:.4f}).")
        return self


class MandatoryConstraints(BaseModel):
    max_budget: Optional[float] = Field(default=None, description="Hard ceiling budget limit")
    max_lead_time_days: Optional[int] = Field(default=None, description="Maximum allowable delivery lead time in days")
    disallow_critical_risk: bool = Field(default=True, description="Automatically reject suppliers in CRITICAL risk tier")


class QuotationCandidate(BaseModel):
    quotation_id: str
    supplier_id: str
    supplier_name: str
    total_cost: float = Field(ge=0.0)
    currency: str = "LKR"
    lead_time_days: int = Field(ge=1)
    quality_score: float = Field(default=0.85, ge=0.0, le=1.0)
    risk_score: float = Field(default=0.20, ge=0.0, le=1.0)
    risk_category: str = Field(default="LOW")
    compliance_passed: bool = Field(default=True)


class RankedSupplier(BaseModel):
    rank: int
    supplier_id: str
    supplier_name: str
    quotation_id: str
    total_cost: float
    lead_time_days: int
    is_eligible: bool
    rejection_reasons: List[str]
    composite_score: float
    normalized_scores: Dict[str, float]
    explanation: str


class OptimizationRequest(BaseModel):
    request_id: str
    budget_limit: float = Field(ge=0.0)
    currency: str = "LKR"
    candidates: List[QuotationCandidate] = Field(default_factory=list)
    constraints: Optional[MandatoryConstraints] = None
    weights: Optional[CriteriaWeights] = None


class OptimizationResponse(BaseModel):
    scenario_id: str
    request_id: str
    algorithm: str
    total_evaluated: int
    eligible_count: int
    rejected_count: int
    top_recommended_supplier_id: Optional[str] = None
    top_recommended_supplier_name: Optional[str] = None
    rankings: List[RankedSupplier]
    weights_used: Dict[str, float]
    decision_summary: str
    created_at: datetime

    model_config = {"from_attributes": True}

