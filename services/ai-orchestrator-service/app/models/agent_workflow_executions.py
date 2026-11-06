import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, CHAR, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class AgentWorkflowExecution(Base):
    __tablename__ = "agent_workflow_executions"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    correlation_id = Column(CHAR(36), nullable=False, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    purchase_request_id = Column(CHAR(36), nullable=False, index=True)
    document_id = Column(CHAR(36), nullable=True, index=True)
    supplier_id = Column(CHAR(36), nullable=True, index=True)
    workflow_name = Column(String(100), default="PROCUREMENT_EVALUATION", nullable=False)
    status = Column(String(50), default="STARTED", nullable=False)  # STARTED, WAITING_FOR_HUMAN_REVIEW, RUNNING, COMPLETED, FAILED
    current_step = Column(String(100), default="document_intelligence", nullable=False)
    requires_human_review = Column(Boolean, default=False, nullable=False)
    human_review_reason = Column(Text, nullable=True)
    state_snapshot = Column(Text, nullable=False)  # JSON checkpoint of workflow state
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    step_logs = relationship("WorkflowStepLog", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowStepLog(Base):
    __tablename__ = "workflow_step_logs"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(CHAR(36), ForeignKey("agent_workflow_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(CHAR(36), nullable=False)
    step_name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)  # SUCCESS, FAILED, PAUSED
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    workflow = relationship("AgentWorkflowExecution", back_populates="step_logs")
