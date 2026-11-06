from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierContactCreate,
    SupplierContactResponse,
    SupplierCategoryCreate,
    SupplierCategoryResponse,
    SupplierDeliveryRecordCreate,
    SupplierDeliveryRecordResponse,
    SupplierQualityRecordCreate,
    SupplierQualityRecordResponse,
    SupplierPerformanceSummary,
)
from app.services.supplier_service import SupplierService
from app.core.config import settings
from shared.auth.jwt_validator import get_current_principal_factory, SecurityPrincipal
from shared.api_contracts.responses import ApiResponse

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])

get_current_principal = get_current_principal_factory(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
)


# --- Category Endpoints ---
@router.post("/categories", response_model=ApiResponse[SupplierCategoryResponse], status_code=status.HTTP_201_CREATED)
def create_category(
    body: SupplierCategoryCreate,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Creates a supplier category for the organization."""
    service = SupplierService(db)
    category = service.create_category(str(principal.organization_id), body)
    return ApiResponse(data=category, message="Category created successfully.")


@router.get("/categories", response_model=ApiResponse[List[SupplierCategoryResponse]])
def list_categories(
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Lists supplier categories for the organization."""
    service = SupplierService(db)
    categories = service.list_categories(str(principal.organization_id))
    return ApiResponse(data=categories)


# --- Supplier CRUD Endpoints ---
@router.post("", response_model=ApiResponse[SupplierResponse], status_code=status.HTTP_201_CREATED)
def create_supplier(
    body: SupplierCreate,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Registers a new vendor/supplier within the caller's organization."""
    service = SupplierService(db)
    supplier = service.create_supplier(body, organization_id=str(principal.organization_id))
    return ApiResponse(data=supplier, message="Supplier registered successfully.")


@router.get("", response_model=ApiResponse[List[SupplierResponse]])
def list_suppliers(
    category: Optional[str] = Query(None, description="Filter by category"),
    tier: Optional[str] = Query(None, description="Filter by tier: TIER_1, TIER_2, TIER_3"),
    compliance_status: Optional[str] = Query(None, description="Filter by compliance: VERIFIED, PENDING, REJECTED"),
    is_active: Optional[bool] = Query(None, description="Filter active/inactive suppliers"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Lists suppliers belonging to the caller's organization."""
    service = SupplierService(db)
    suppliers = service.list_suppliers(
        organization_id=str(principal.organization_id),
        category=category,
        tier=tier,
        compliance_status=compliance_status,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(data=suppliers)


@router.get("/{supplier_id}", response_model=ApiResponse[SupplierResponse])
def get_supplier(
    supplier_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Retrieves single supplier profile enforcing organization tenancy."""
    service = SupplierService(db)
    supplier = service.get_supplier(supplier_id, organization_id=str(principal.organization_id))
    return ApiResponse(data=supplier)


@router.put("/{supplier_id}", response_model=ApiResponse[SupplierResponse])
def update_supplier(
    supplier_id: str,
    body: SupplierUpdate,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Updates supplier information."""
    service = SupplierService(db)
    updated = service.update_supplier(supplier_id, body, organization_id=str(principal.organization_id))
    return ApiResponse(data=updated, message="Supplier updated successfully.")


@router.delete("/{supplier_id}", response_model=ApiResponse[dict])
def deactivate_supplier(
    supplier_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Soft-deactivates a supplier."""
    service = SupplierService(db)
    service.delete_supplier(supplier_id, organization_id=str(principal.organization_id))
    return ApiResponse(data={"deactivated": True}, message="Supplier deactivated successfully.")


# --- Contact Endpoints ---
@router.post("/{supplier_id}/contacts", response_model=ApiResponse[SupplierContactResponse], status_code=status.HTTP_201_CREATED)
def add_supplier_contact(
    supplier_id: str,
    body: SupplierContactCreate,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Adds a primary or secondary contact for the supplier."""
    service = SupplierService(db)
    contact = service.add_contact(supplier_id, str(principal.organization_id), body)
    return ApiResponse(data=contact, message="Contact added successfully.")


@router.get("/{supplier_id}/contacts", response_model=ApiResponse[List[SupplierContactResponse]])
def list_supplier_contacts(
    supplier_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Lists contacts for the supplier."""
    service = SupplierService(db)
    contacts = service.list_contacts(supplier_id, str(principal.organization_id))
    return ApiResponse(data=contacts)


# --- Performance & Quality Records ---
@router.post("/{supplier_id}/delivery-records", response_model=ApiResponse[SupplierDeliveryRecordResponse], status_code=status.HTTP_201_CREATED)
def record_delivery_performance(
    supplier_id: str,
    body: SupplierDeliveryRecordCreate,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Audits and records actual delivery performance with verified source provenance."""
    service = SupplierService(db)
    record = service.record_delivery_performance(
        supplier_id=supplier_id,
        organization_id=str(principal.organization_id),
        recorded_by=str(principal.user_id),
        record_in=body,
    )
    return ApiResponse(data=record, message="Historical delivery record saved.")


@router.post("/{supplier_id}/quality-records", response_model=ApiResponse[SupplierQualityRecordResponse], status_code=status.HTTP_201_CREATED)
def record_quality_incident(
    supplier_id: str,
    body: SupplierQualityRecordCreate,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Audits and records quality inspection or incident log with verified source provenance."""
    service = SupplierService(db)
    record = service.record_quality_incident(
        supplier_id=supplier_id,
        organization_id=str(principal.organization_id),
        recorded_by=str(principal.user_id),
        record_in=body,
    )
    return ApiResponse(data=record, message="Quality record logged.")


@router.get("/{supplier_id}/performance-summary", response_model=ApiResponse[SupplierPerformanceSummary])
def get_supplier_performance_summary(
    supplier_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Calculates authorized supplier performance metrics derived from real delivery and quality audits."""
    service = SupplierService(db)
    summary = service.get_performance_summary(supplier_id, str(principal.organization_id))
    return ApiResponse(data=summary)
