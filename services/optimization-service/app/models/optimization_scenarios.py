import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, CHAR, Integer
from app.db.base import Base


class OptimizationScenario(Base):
    __tablename__ = "optimization_scenarios"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    request_id = Column(CHAR(36), nullable=False, index=True)
    algorithm = Column(String(100), default="mcda_weighted_scoring_v1.0", nullable=False)
    total_evaluated = Column(Integer, default=0, nullable=False)
    top_supplier_id = Column(CHAR(36), nullable=True)
    weights_json = Column(Text, nullable=False)
    rankings_json = Column(Text, nullable=False)
    decision_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
