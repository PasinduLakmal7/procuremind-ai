from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate


class OrganizationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, org_id: UUID) -> Optional[Organization]:
        return self.db.query(Organization).filter(Organization.id == org_id).first()

    def get_by_name(self, name: str) -> Optional[Organization]:
        return self.db.query(Organization).filter(Organization.name == name).first()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        return self.db.query(Organization).offset(skip).limit(limit).all()

    def create(self, org_in: OrganizationCreate) -> Organization:
        org = Organization(
            name=org_in.name,
            registration_number=org_in.registration_number,
            industry=org_in.industry,
        )
        self.db.add(org)
        self.db.commit()
        self.db.refresh(org)
        return org

