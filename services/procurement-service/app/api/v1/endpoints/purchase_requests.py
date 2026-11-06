from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.purchase_request import (
    PurchaseRequestCreate,
    PurchaseRequestUpdate,
    PurchaseRequestResponse,
    PurchaseRequestDetailResponse,
    PurchaseRequestStatusUpdate,
    PurchaseRequestItemCreate,
    PurchaseRequestItemResponse,
    CandidateSupplierCreate,
    CandidateSupplierResponse,
    PurchaseRequestDecision,
)
from app.schemas.quotation import QuotationCreate, QuotationResponse
from app.services.procurement_service import ProcurementService
from app.core.config import settings
from shared.auth.jwt_validator import get_current_principal_factory, SecurityPrincipal
from shared.api_contracts.responses import ApiResponse

router = APIRouter(tags=["Purchase Requests & Quotations"])

get_current_principal = get_current_principal_factory(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
)


@router.post("/requests", response_model=ApiResponse[PurchaseRequestResponse], status_code=status.HTTP_201_CREATED)
def create_purchase_request(
    body: PurchaseRequestCreate,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Creates a new purchasing requirement in DRAFT status."""
    service = ProcurementService(db)
    pr = service.create_request(
        data=body,
        organization_id=str(principal.organization_id),
        user_id=str(principal.user_id),
    )
    return ApiResponse(data=pr, message="Purchase request created as draft.")


@router.get("/requests", response_model=ApiResponse[List[PurchaseRequestResponse]])
def list_purchase_requests(
    status: Optional[str] = Query(None, description="Filter by status: DRAFT, SUBMITTED, UNDER_EVALUATION, etc."),
    category: Optional[str] = Query(None, description="Filter by product category"),
    priority: Optional[str] = Query(None, description="Filter by priority: LOW, MEDIUM, HIGH, URGENT"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Lists purchase requests belonging to caller's organization."""
    service = ProcurementService(db)
    prs = service.list_requests(
        organization_id=str(principal.organization_id),
        status=status,
        category=category,
        priority=priority,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(data=prs)


@router.get("/requests/{request_id}", response_model=ApiResponse[PurchaseRequestResponse])
def get_purchase_request(
    request_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Retrieves single purchase request."""
    service = ProcurementService(db)
    pr = service.get_request(request_id, organization_id=str(principal.organization_id))
    return ApiResponse(data=pr)


@router.get("/requests/{request_id}/details", response_model=ApiResponse[PurchaseRequestDetailResponse])
def get_purchase_request_details(
    request_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Retrieves full purchase request with items, candidates, and audit trail."""
    service = ProcurementService(db)
    detail = service.get_request_detail(request_id, organization_id=str(principal.organization_id))
    return ApiResponse(data=detail)


@router.put("/requests/{request_id}", response_model=ApiResponse[PurchaseRequestResponse])
def update_purchase_request_draft(
    request_id: str,
    body: PurchaseRequestUpdate,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Edits a draft purchase request. Only permitted in DRAFT status."""
    service = ProcurementService(db)
    updated = service.update_draft(
        pr_id=request_id,
        update_in=body,
        organization_id=str(principal.organization_id),
        user_id=str(principal.user_id),
    )
    return ApiResponse(data=updated, message="Draft purchase request updated.")


@router.post("/requests/{request_id}/items", response_model=ApiResponse[PurchaseRequestItemResponse], status_code=status.HTTP_201_CREATED)
def add_request_item(
    request_id: str,
    body: PurchaseRequestItemCreate,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Adds a line item to a draft purchase request."""
    service = ProcurementService(db)
    item = service.add_item(
        pr_id=request_id,
        item_in=body,
        organization_id=str(principal.organization_id),
        user_id=str(principal.user_id),
    )
    return ApiResponse(data=item, message="Item added to purchase request.")


@router.delete("/requests/{request_id}/items/{item_id}", response_model=ApiResponse[dict])
def remove_request_item(
    request_id: str,
    item_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Removes a line item from a draft purchase request."""
    service = ProcurementService(db)
    service.remove_item(
        pr_id=request_id,
        item_id=item_id,
        organization_id=str(principal.organization_id),
        user_id=str(principal.user_id),
    )
    return ApiResponse(data={"removed": True}, message="Item removed from purchase request.")


@router.post("/requests/{request_id}/candidate-suppliers", response_model=ApiResponse[CandidateSupplierResponse], status_code=status.HTTP_201_CREATED)
def add_candidate_supplier(
    request_id: str,
    body: CandidateSupplierCreate,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Associates an invited candidate supplier with the purchase request."""
    service = ProcurementService(db)
    cand = service.add_candidate_supplier(
        pr_id=request_id,
        candidate_in=body,
        organization_id=str(principal.organization_id),
        user_id=str(principal.user_id),
    )
    return ApiResponse(data=cand, message="Candidate supplier associated.")


@router.get("/requests/{request_id}/candidate-suppliers", response_model=ApiResponse[List[CandidateSupplierResponse]])
def list_candidate_suppliers(
    request_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Lists candidate suppliers associated with a purchase request."""
    service = ProcurementService(db)
    cands = service.list_candidate_suppliers(request_id, organization_id=str(principal.organization_id))
    return ApiResponse(data=cands)


@router.patch("/requests/{request_id}/status", response_model=ApiResponse[PurchaseRequestResponse])
def update_purchase_request_status(
    request_id: str,
    body: PurchaseRequestStatusUpdate,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Validates state machine transitions (e.g. SUBMITTED generates outbox event)."""
    service = ProcurementService(db)
    updated = service.update_status(
        pr_id=request_id,
        status_in=body,
        organization_id=str(principal.organization_id),
        user_id=str(principal.user_id),
    )
    return ApiResponse(data=updated, message=f"Status transitioned to {body.status}.")


# ---------------- Quotations for a Purchase Request ----------------

@router.post("/requests/{request_id}/quotations", response_model=ApiResponse[QuotationResponse], status_code=status.HTTP_201_CREATED)
def submit_quotation_for_request(
    request_id: str,
    body: QuotationCreate,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Associates a supplier quotation with a purchasing request."""
    service = ProcurementService(db)
    quote = service.submit_quotation(
        pr_id=request_id,
        data=body,
        organization_id=str(principal.organization_id),
        user_id=str(principal.user_id),
    )
    return ApiResponse(data=quote, message="Quotation registered successfully.")


@router.get("/requests/{request_id}/quotations", response_model=ApiResponse[List[QuotationResponse]])
def list_quotations_for_request(
    request_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Lists all quotations submitted for a purchase request."""
    service = ProcurementService(db)
    quotes = service.list_quotations(request_id, organization_id=str(principal.organization_id))
    return ApiResponse(data=quotes)


@router.get("/quotations/{quotation_id}", response_model=ApiResponse[QuotationResponse])
def get_quotation_by_id(
    quotation_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Retrieves a single quotation by ID."""
    service = ProcurementService(db)
    quote = service.get_quotation(quotation_id, organization_id=str(principal.organization_id))
    return ApiResponse(data=quote)


@router.post("/requests/{request_id}/decision", response_model=ApiResponse[PurchaseRequestDetailResponse])
def record_procurement_decision(
    request_id: str,
    body: PurchaseRequestDecision,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """
    Records an authorized human procurement decision (APPROVE or REJECT).
    Enforces human governance before contract award or fund expenditure.
    """
    service = ProcurementService(db)
    updated = service.record_decision(
        pr_id=request_id,
        decision=body,
        organization_id=str(principal.organization_id),
        user_id=str(principal.user_id),
    )
    return ApiResponse(
        data=updated,
        message=f"Purchase request {body.action.upper()} decision recorded successfully with audit trail.",
    )

