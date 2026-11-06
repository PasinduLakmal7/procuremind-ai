from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.risk_assessments import RiskAssessmentRecord
from app.schemas.risk import (
    RiskEvaluationRequest,
    RiskEvaluationResponse,
    MLModelStatusResponse,
)
from app.services.risk_engine import RiskEvaluationEngine
from app.ml.predictive_pipeline import ml_risk_pipeline
from app.core.config import settings
from shared.auth.jwt_validator import get_current_principal_factory, SecurityPrincipal

router = APIRouter(tags=["Risk Assessment"])
engine = RiskEvaluationEngine()

get_current_principal = get_current_principal_factory(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
)


@router.post("/evaluate", response_model=RiskEvaluationResponse, status_code=status.HTTP_201_CREATED)
def evaluate_supplier_risk(
    request: RiskEvaluationRequest,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """
    Evaluates supplier risk using the transparent, deterministic baseline.
    Enforces 'INSUFFICIENT_DATA' if observations are below threshold (< 3).
    """
    return engine.evaluate_supplier(request, str(principal.organization_id), db)


@router.get("/suppliers/{supplier_id}", response_model=Optional[RiskEvaluationResponse])
def get_supplier_latest_risk(
    supplier_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """
    Retrieves the latest persisted risk assessment for a given supplier in the organization.
    """
    import json
    record = (
        db.query(RiskAssessmentRecord)
        .filter(
            RiskAssessmentRecord.supplier_id == supplier_id,
            RiskAssessmentRecord.organization_id == str(principal.organization_id),
        )
        .order_by(RiskAssessmentRecord.created_at.desc())
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No risk assessment found for supplier '{supplier_id}'.",
        )

    breakdown = json.loads(record.metrics_breakdown) if record.metrics_breakdown else {}
    return RiskEvaluationResponse(
        assessment_id=record.id,
        supplier_id=record.supplier_id,
        supplier_name=record.supplier_name,
        risk_score=record.risk_score,
        risk_category=record.risk_category,
        confidence=record.confidence,
        data_sufficiency=record.data_sufficiency,
        observation_count=record.observation_count,
        metrics_breakdown=breakdown,
        explanation=record.explanation or "",
        model_version=record.model_version,
        created_at=record.created_at,
    )


@router.get("/assessments/{assessment_id}", response_model=RiskEvaluationResponse)
def get_risk_assessment_by_id(
    assessment_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """
    Retrieves a specific risk assessment by ID.
    """
    import json
    record = (
        db.query(RiskAssessmentRecord)
        .filter(
            RiskAssessmentRecord.id == assessment_id,
            RiskAssessmentRecord.organization_id == str(principal.organization_id),
        )
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk assessment '{assessment_id}' not found.",
        )

    breakdown = json.loads(record.metrics_breakdown) if record.metrics_breakdown else {}
    return RiskEvaluationResponse(
        assessment_id=record.id,
        supplier_id=record.supplier_id,
        supplier_name=record.supplier_name,
        risk_score=record.risk_score,
        risk_category=record.risk_category,
        confidence=record.confidence,
        data_sufficiency=record.data_sufficiency,
        observation_count=record.observation_count,
        metrics_breakdown=breakdown,
        explanation=record.explanation or "",
        model_version=record.model_version,
        created_at=record.created_at,
    )


@router.get("/ml/status", response_model=MLModelStatusResponse)
def get_ml_status(principal: SecurityPrincipal = Depends(get_current_principal)):
    """
    Returns the training status, provenances, and limitations of the ML pipeline.
    """
    return MLModelStatusResponse(**ml_risk_pipeline.get_model_status())
