from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        action: str,
        user_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        status: str = "SUCCESS",
        ip_address: Optional[str] = None,
        details: Optional[str] = None,
    ) -> AuditLog:
        audit_entry = AuditLog(
            action=action,
            user_id=user_id,
            organization_id=organization_id,
            status=status,
            ip_address=ip_address,
            details=details,
        )
        self.db.add(audit_entry)
        self.db.commit()
        self.db.refresh(audit_entry)
        return audit_entry

    def list_by_organization(self, organization_id: UUID, limit: int = 50) -> List[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.organization_id == organization_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )

