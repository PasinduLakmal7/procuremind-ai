import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.optimization_scenarios import OptimizationScenario
from app.schemas.optimization import (
    OptimizationRequest,
    OptimizationResponse,
    RankedSupplier,
)
from app.services.optimizer_engine import MultiCriteriaOptimizerEngine
from app.core.config import settings
from shared.auth.jwt_validator import get_current_principal_factory, SecurityPrincipal

router = APIRouter(tags=["Multi-Criteria Optimization"])
engine = MultiCriteriaOptimizerEngine()

get_current_principal = get_current_principal_factory(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
)


@router.post("/rank", response_model=OptimizationResponse, status_code=status.HTTP_201_CREATED)
def rank_procurement_candidates(
    request: OptimizationRequest,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """
    Ranks supplier quotation candidates using Multi-Criteria Decision Analysis (MCDA).
    Filters mandatory constraints (budget, lead time, risk tier) before applying weighted ranking.
    """
    return engine.optimize_and_rank(request, str(principal.organization_id), db)


@router.get("/scenarios/{scenario_id}", response_model=OptimizationResponse)
def get_scenario(
    scenario_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """
    Retrieves an optimization scenario by ID.
    """
    scenario = (
        db.query(OptimizationScenario)
        .filter(
            OptimizationScenario.id == scenario_id,
            OptimizationScenario.organization_id == str(principal.organization_id),
        )
        .first()
    )
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Optimization scenario '{scenario_id}' not found.",
        )

    weights_dict = json.loads(scenario.weights_json)
    rankings_raw = json.loads(scenario.rankings_json)
    rankings = [RankedSupplier(**r) for r in rankings_raw]
    eligible_count = sum(1 for r in rankings if r.is_eligible)
    rejected_count = sum(1 for r in rankings if not r.is_eligible)
    top_name = next((r.supplier_name for r in rankings if r.supplier_id == scenario.top_supplier_id), None)

    return OptimizationResponse(
        scenario_id=scenario.id,
        request_id=scenario.request_id,
        algorithm=scenario.algorithm,
        total_evaluated=scenario.total_evaluated,
        eligible_count=eligible_count,
        rejected_count=rejected_count,
        top_recommended_supplier_id=scenario.top_supplier_id,
        top_recommended_supplier_name=top_name,
        rankings=rankings,
        weights_used=weights_dict,
        decision_summary=scenario.decision_summary or "",
        created_at=scenario.created_at,
    )


@router.get("/requests/{request_id}", response_model=Optional[OptimizationResponse])
def get_latest_scenario_for_request(
    request_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """
    Retrieves the latest optimization scenario executed for a given purchase request.
    """
    scenario = (
        db.query(OptimizationScenario)
        .filter(
            OptimizationScenario.request_id == request_id,
            OptimizationScenario.organization_id == str(principal.organization_id),
        )
        .order_by(OptimizationScenario.created_at.desc())
        .first()
    )
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No optimization scenario found for request '{request_id}'.",
        )

    weights_dict = json.loads(scenario.weights_json)
    rankings_raw = json.loads(scenario.rankings_json)
    rankings = [RankedSupplier(**r) for r in rankings_raw]
    eligible_count = sum(1 for r in rankings if r.is_eligible)
    rejected_count = sum(1 for r in rankings if not r.is_eligible)
    top_name = next((r.supplier_name for r in rankings if r.supplier_id == scenario.top_supplier_id), None)

    return OptimizationResponse(
        scenario_id=scenario.id,
        request_id=scenario.request_id,
        algorithm=scenario.algorithm,
        total_evaluated=scenario.total_evaluated,
        eligible_count=eligible_count,
        rejected_count=rejected_count,
        top_recommended_supplier_id=scenario.top_supplier_id,
        top_recommended_supplier_name=top_name,
        rankings=rankings,
        weights_used=weights_dict,
        decision_summary=scenario.decision_summary or "",
        created_at=scenario.created_at,
    )

