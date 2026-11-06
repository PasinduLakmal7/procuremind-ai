import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, CHAR
from app.db.base import Base

class SupplierRiskProfile(Base):
    __tablename__ = "supplier_risk_profiles"
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    supplier_id = Column(CHAR(36), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    model_version = Column(String(50), default="baseline-rule-v1", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
