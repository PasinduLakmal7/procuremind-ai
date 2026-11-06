import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, CHAR, Text, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    created_by_user_id = Column(CHAR(36), nullable=False)
    request_number = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), default="Raw Materials", nullable=False, index=True)
    priority = Column(String(50), default="MEDIUM", nullable=False)
    budget_limit = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), default="LKR", nullable=False)
    required_delivery_date = Column(DateTime, nullable=True)
    evaluation_criteria = Column(Text, nullable=True)
    status = Column(String(50), default="DRAFT", nullable=False, index=True)  # DRAFT, SUBMITTED, UNDER_EVALUATION, APPROVED, REJECTED, CANCELLED
    items_json = Column(Text, nullable=True)  # Backward compatibility
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    items = relationship("PurchaseRequestItem", back_populates="purchase_request", cascade="all, delete-orphan")
    candidate_suppliers = relationship("CandidateSupplier", back_populates="purchase_request", cascade="all, delete-orphan")
    quotations = relationship("Quotation", back_populates="purchase_request", cascade="all, delete-orphan")
    audit_events = relationship("ProcurementAuditEvent", back_populates="purchase_request", cascade="all, delete-orphan")


class PurchaseRequestItem(Base):
    __tablename__ = "purchase_request_items"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    purchase_request_id = Column(CHAR(36), ForeignKey("purchase_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    item_name = Column(String(255), nullable=False)
    specification = Column(Text, nullable=True)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_of_measure = Column(String(50), default="UNITS", nullable=False)
    target_unit_price = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    purchase_request = relationship("PurchaseRequest", back_populates="items")


class CandidateSupplier(Base):
    __tablename__ = "candidate_suppliers"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    purchase_request_id = Column(CHAR(36), ForeignKey("purchase_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(CHAR(36), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    supplier_email = Column(String(255), nullable=True)
    invitation_status = Column(String(50), default="INVITED", nullable=False)  # INVITED, ACCEPTED, DECLINED, QUOTED
    invited_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    purchase_request = relationship("PurchaseRequest", back_populates="candidate_suppliers")


class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    purchase_request_id = Column(CHAR(36), ForeignKey("purchase_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(CHAR(36), nullable=False, index=True)
    quotation_number = Column(String(100), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    total_cost = Column(Float, nullable=False)
    currency = Column(String(10), default="LKR", nullable=False)
    submitted_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    validity_date = Column(DateTime, nullable=True)
    estimated_delivery_days = Column(Integer, default=14, nullable=False)
    warranty_terms = Column(String(255), nullable=True)
    payment_terms = Column(String(100), default="Net 30", nullable=True)
    document_id = Column(CHAR(36), nullable=True, index=True)
    metadata_notes = Column(Text, nullable=True)
    status = Column(String(50), default="RECEIVED", nullable=False)  # RECEIVED, UNDER_REVIEW, ACCEPTED, REJECTED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    purchase_request = relationship("PurchaseRequest", back_populates="quotations")
    items = relationship("QuotationItem", back_populates="quotation", cascade="all, delete-orphan")


class QuotationItem(Base):
    __tablename__ = "quotation_items"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    quotation_id = Column(CHAR(36), ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True)
    item_name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_of_measure = Column(String(50), default="UNITS", nullable=False)
    unit_price = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)
    lead_time_days = Column(Integer, default=14, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    quotation = relationship("Quotation", back_populates="items")


class ProcurementAuditEvent(Base):
    __tablename__ = "procurement_audit_events"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    purchase_request_id = Column(CHAR(36), ForeignKey("purchase_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    performed_by = Column(CHAR(36), nullable=False)
    old_state = Column(Text, nullable=True)
    new_state = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    purchase_request = relationship("PurchaseRequest", back_populates="audit_events")


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)  # e.g., purchase_request.submitted.v1
    aggregate_type = Column(String(100), nullable=False)         # PurchaseRequest, Quotation
    aggregate_id = Column(CHAR(36), nullable=False, index=True)
    payload = Column(Text, nullable=False)                       # JSON string
    status = Column(String(50), default="PENDING", nullable=False, index=True)  # PENDING, PUBLISHED, FAILED
    retry_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    published_at = Column(DateTime, nullable=True)
