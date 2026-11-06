import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, CHAR, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class DocumentRecord(Base):
    __tablename__ = "document_records"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    purchase_request_id = Column(CHAR(36), nullable=True, index=True)
    supplier_id = Column(CHAR(36), nullable=True, index=True)
    quotation_id = Column(CHAR(36), nullable=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    storage_path = Column(String(500), nullable=False)
    status = Column(String(50), default="UPLOADED", nullable=False)  # UPLOADED, PROCESSING, EXTRACTED, FAILED, VERIFIED
    checksum_sha256 = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    extraction = relationship("QuotationExtraction", back_populates="document", uselist=False, cascade="all, delete-orphan")


class QuotationExtraction(Base):
    __tablename__ = "quotation_extractions"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(CHAR(36), ForeignKey("document_records.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(CHAR(36), nullable=False, index=True)
    purchase_request_id = Column(CHAR(36), nullable=True, index=True)
    supplier_id = Column(CHAR(36), nullable=True, index=True)
    supplier_name = Column(String(255), nullable=True)
    quotation_number = Column(String(100), nullable=True)
    currency = Column(String(10), default="LKR", nullable=False)
    total_cost = Column(Float, nullable=True)
    confidence_score = Column(Float, default=1.0, nullable=False)
    arithmetic_valid = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_by = Column(CHAR(36), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    structured_data_json = Column(Text, nullable=False)
    flagged_reasons_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("DocumentRecord", back_populates="extraction")
    corrections = relationship("ExtractionCorrectionAudit", back_populates="extraction", cascade="all, delete-orphan")


class ExtractionCorrectionAudit(Base):
    __tablename__ = "extraction_correction_audits"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    extraction_id = Column(CHAR(36), ForeignKey("quotation_extractions.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(CHAR(36), nullable=False, index=True)
    corrected_by = Column(CHAR(36), nullable=False)
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    extraction = relationship("QuotationExtraction", back_populates="corrections")


class DocumentOutboxEvent(Base):
    __tablename__ = "document_outbox_events"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)  # quotation.document.uploaded.v1
    aggregate_type = Column(String(100), default="DocumentRecord", nullable=False)
    aggregate_id = Column(CHAR(36), nullable=False, index=True)
    payload = Column(Text, nullable=False)  # JSON string
    status = Column(String(50), default="PENDING", nullable=False, index=True)
    retry_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    published_at = Column(DateTime, nullable=True)
