import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, CHAR, Text, Integer
from app.db.base import Base


class RiskAssessmentRecord(Base):
    __tablename__ = "risk_assessments"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    supplier_id = Column(CHAR(36), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    risk_score = Column(Float, nullable=True)  # Null if INSUFFICIENT_DATA
    risk_category = Column(String(50), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL, INSUFFICIENT_DATA
    confidence = Column(Float, nullable=False, default=0.5)
    data_sufficiency = Column(String(50), nullable=False, default="INSUFFICIENT_DATA")
    observation_count = Column(Integer, nullable=False, default=0)
    metrics_breakdown = Column(Text, nullable=True)  # JSON text
    observations = Column(Text, nullable=True)       # JSON text
    model_version = Column(String(50), default="rule-baseline-v1.0", nullable=False)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

