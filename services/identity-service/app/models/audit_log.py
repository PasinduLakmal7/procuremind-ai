import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text
from app.db.base import Base
from app.models.organization import GUID


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), nullable=True, index=True)
    organization_id = Column(GUID(), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default="SUCCESS", nullable=False)
    ip_address = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

