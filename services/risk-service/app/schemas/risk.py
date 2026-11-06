from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DeliveryObservation(BaseModel):
    order_id: Optional[str] = None
    promised_delivery_date: Optional[str] = None
    actual_delivery_date: Optional[str] = None
    was_delayed: bool = False
    lateness_days: int = Field(default=0, ge=0)
    fulfillment_rate: float = Field(default=1.0, ge=0.0, le=1.0)


class QualityObservation(BaseModel):
    incident_id: Optional[str] = None
    incident_type: str = "INSPECTION"
    defect_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    severity: str = Field(default="LOW", description="LOW, MEDIUM, HIGH, CRITICAL")


class RiskEvaluationRequest(BaseModel):
    supplier_id: str
    supplier_name: str
    delivery_records: List[DeliveryObservation] = Field(default_factory=list)
    quality_records: List[QualityObservation] = Field(default_factory=list)
    model_type: Optional[str] = Field(default="rule_baseline", description="rule_baseline or ml_pipeline")


class RiskEvaluationResponse(BaseModel):
    assessment_id: str
    supplier_id: str
    supplier_name: str
    risk_score: Optional[float] = None
    risk_category: str
    confidence: float
    data_sufficiency: str
    observation_count: int
    metrics_breakdown: Dict[str, Any]
    explanation: str
    model_version: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MLModelStatusResponse(BaseModel):
    model_name: str
    version: str
    is_trained: bool
    algorithm: str
    features_used: List[str]
    training_sample_size: int
    metrics: Dict[str, Optional[float]]
    limitations: List[str]
    provenance: str

