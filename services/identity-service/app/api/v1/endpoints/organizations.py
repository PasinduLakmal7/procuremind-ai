from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.organization import OrganizationCreate, OrganizationResponse
from app.services.organization_service import OrganizationService
from app.core.config import settings
from shared.auth.jwt_validator import get_current_principal_factory, SecurityPrincipal
from shared.api_contracts.responses import ApiResponse
from shared.core.exceptions import ForbiddenException

router = APIRouter(prefix="/organizations", tags=["Organizations"])

get_current_principal = get_current_principal_factory(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
)


@router.post("", response_model=ApiResponse[OrganizationResponse])
def create_organization(
    body: OrganizationCreate,
    db: Session = Depends(get_db),
):
    """Provisions a new organization / manufacturing plant."""
    service = OrganizationService(db)
    org = service.create_organization(body)
    return ApiResponse(data=org, message="Organization provisioned successfully.")


@router.get("", response_model=ApiResponse[List[OrganizationResponse]])
def list_organizations(
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Lists organizations (restricted to admin users)."""
    if not principal.has_role("admin"):
        raise ForbiddenException("Only administrators can view all organizations.")

    service = OrganizationService(db)
    orgs = service.list_organizations()
    return ApiResponse(data=orgs)


@router.get("/{org_id}", response_model=ApiResponse[OrganizationResponse])
def get_organization(
    org_id: UUID,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Retrieves organization details enforcing tenant boundary."""
    if not principal.has_role("admin") and principal.organization_id != org_id:
        raise ForbiddenException("Cross-organization access forbidden.")

    service = OrganizationService(db)
    org = service.get_organization(org_id)
    return ApiResponse(data=org)

