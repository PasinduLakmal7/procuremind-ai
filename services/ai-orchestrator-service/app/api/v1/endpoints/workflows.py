from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.workflow import (
    StartWorkflowRequest,
    ResumeWorkflowRequest,
    WorkflowStatusResponse,
)
from app.services.orchestrator_engine import AIOrchestratorEngine
from app.core.config import settings
from shared.auth.jwt_validator import get_current_principal_factory, SecurityPrincipal
from shared.api_contracts.responses import ApiResponse

router = APIRouter(prefix="/workflows", tags=["Multi-Agent AI Orchestration"])

get_current_principal = get_current_principal_factory(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
)


@router.post("/start", response_model=ApiResponse[WorkflowStatusResponse], status_code=status.HTTP_201_CREATED)
def start_procurement_workflow(
    body: StartWorkflowRequest,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Starts the LangGraph-style procurement evaluation workflow."""
    engine = AIOrchestratorEngine(db)
    result = engine.start_workflow(
        request=body,
        organization_id=str(principal.organization_id),
        user_id=str(principal.user_id),
    )
    return ApiResponse(data=result, message="AI workflow initiated.")


@router.get("/{workflow_id}/status", response_model=ApiResponse[WorkflowStatusResponse])
def get_workflow_status(
    workflow_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Retrieves current workflow step, durable state snapshot, and human-review flags."""
    engine = AIOrchestratorEngine(db)
    status_resp = engine.get_workflow_status(workflow_id, organization_id=str(principal.organization_id))
    return ApiResponse(data=status_resp)


@router.post("/{workflow_id}/resume", response_model=ApiResponse[WorkflowStatusResponse])
def resume_workflow_after_human_verification(
    workflow_id: str,
    body: ResumeWorkflowRequest,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Resumes paused workflow after human-in-the-loop review and verification."""
    engine = AIOrchestratorEngine(db)
    resumed = engine.resume_workflow(
        workflow_id=workflow_id,
        resume_req=body,
        organization_id=str(principal.organization_id),
        user_id=str(principal.user_id),
    )
    return ApiResponse(data=resumed, message="AI workflow resumed with verified extraction.")

