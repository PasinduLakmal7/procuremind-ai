from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.organization import OrganizationCreate, OrganizationResponse
from shared.core.exceptions import ConflictException, NotFoundException


class OrganizationService:
    def __init__(self, db: Session):
        self.repo = OrganizationRepository(db)

    def create_organization(self, data: OrganizationCreate) -> OrganizationResponse:
        existing = self.repo.get_by_name(data.name)
        if existing:
            raise ConflictException(f"Organization with name '{data.name}' already exists.")
        org = self.repo.create(data)
        return OrganizationResponse.model_validate(org)

    def get_organization(self, org_id: UUID) -> OrganizationResponse:
        org = self.repo.get_by_id(org_id)
        if not org:
            raise NotFoundException(f"Organization '{org_id}' not found.")
        return OrganizationResponse.model_validate(org)

    def list_organizations(self, skip: int = 0, limit: int = 100) -> List[OrganizationResponse]:
        orgs = self.repo.list_all(skip=skip, limit=limit)
        return [OrganizationResponse.model_validate(o) for o in orgs]

