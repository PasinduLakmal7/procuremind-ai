import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, CHAR, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(100), default="Colombo", nullable=False)
    country = Column(String(100), default="Sri Lanka", nullable=False)
    category = Column(String(100), default="Raw Materials", nullable=False, index=True)
    tax_id = Column(String(100), nullable=True)
    rating = Column(Float, default=0.0, nullable=False)
    tier = Column(String(50), default="TIER_2", nullable=False)
    compliance_status = Column(String(50), default="VERIFIED", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    contacts = relationship("SupplierContact", back_populates="supplier", cascade="all, delete-orphan")
    delivery_records = relationship("SupplierDeliveryRecord", back_populates="supplier", cascade="all, delete-orphan")
    quality_records = relationship("SupplierQualityRecord", back_populates="supplier", cascade="all, delete-orphan")


class SupplierContact(Base):
    __tablename__ = "supplier_contacts"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    supplier_id = Column(CHAR(36), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    designation = Column(String(100), default="Sales Representative", nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    supplier = relationship("Supplier", back_populates="contacts")


class SupplierCategory(Base):
    __tablename__ = "supplier_categories"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class SupplierDeliveryRecord(Base):
    __tablename__ = "supplier_delivery_records"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    supplier_id = Column(CHAR(36), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    po_reference = Column(String(100), nullable=False)
    promised_delivery_date = Column(DateTime, nullable=False)
    actual_delivery_date = Column(DateTime, nullable=False)
    on_time = Column(Boolean, default=True, nullable=False)
    delay_days = Column(Integer, default=0, nullable=False)
    source_system = Column(String(100), nullable=False, default="MANUAL_AUDIT")  # e.g., ERP_EXPORT, GOODS_RECEIPT_NOTE
    notes = Column(Text, nullable=True)
    recorded_by = Column(CHAR(36), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    supplier = relationship("Supplier", back_populates="delivery_records")


class SupplierQualityRecord(Base):
    __tablename__ = "supplier_quality_records"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    supplier_id = Column(CHAR(36), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_reference = Column(String(100), nullable=False)
    defect_rate = Column(Float, default=0.0, nullable=False)
    incident_severity = Column(String(50), default="NONE", nullable=False)  # NONE, MINOR, MAJOR, CRITICAL
    passed = Column(Boolean, default=True, nullable=False)
    source_system = Column(String(100), nullable=False, default="QA_INSPECTION_LOG")  # QA_LAB_LOG, INCOMING_INSPECTION
    incident_details = Column(Text, nullable=True)
    recorded_by = Column(CHAR(36), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    supplier = relationship("Supplier", back_populates="quality_records")
