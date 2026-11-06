import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.suppliers import (
    Supplier,
    SupplierContact,
    SupplierCategory,
    SupplierDeliveryRecord,
    SupplierQualityRecord,
)
from app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierContactCreate,
    SupplierCategoryCreate,
    SupplierDeliveryRecordCreate,
    SupplierQualityRecordCreate,
)


class SupplierRepository:
    def __init__(self, db: Session):
        self.db = db

    # --- Supplier Core ---
    def get_by_id(self, supplier_id: str, organization_id: str) -> Optional[Supplier]:
        return (
            self.db.query(Supplier)
            .filter(Supplier.id == supplier_id, Supplier.organization_id == organization_id)
            .first()
        )

    def get_by_name(self, company_name: str, organization_id: str) -> Optional[Supplier]:
        return (
            self.db.query(Supplier)
            .filter(Supplier.company_name == company_name, Supplier.organization_id == organization_id)
            .first()
        )

    def list_all(
        self,
        organization_id: str,
        category: Optional[str] = None,
        tier: Optional[str] = None,
        compliance_status: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Supplier]:
        query = self.db.query(Supplier).filter(Supplier.organization_id == organization_id)
        if category:
            query = query.filter(Supplier.category.ilike(f"%{category}%"))
        if tier:
            query = query.filter(Supplier.tier == tier)
        if compliance_status:
            query = query.filter(Supplier.compliance_status == compliance_status)
        if is_active is not None:
            query = query.filter(Supplier.is_active == is_active)
        return query.order_by(Supplier.created_at.desc()).offset(skip).limit(limit).all()

    def create(self, supplier_in: SupplierCreate, organization_id: str) -> Supplier:
        supplier = Supplier(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            company_name=supplier_in.company_name,
            contact_email=supplier_in.contact_email,
            contact_phone=supplier_in.contact_phone,
            address=supplier_in.address,
            city=supplier_in.city,
            country=supplier_in.country,
            category=supplier_in.category,
            tax_id=supplier_in.tax_id,
            rating=supplier_in.rating or 3.5,
            tier=supplier_in.tier,
            compliance_status=supplier_in.compliance_status,
            is_active=True,
        )
        self.db.add(supplier)
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    def update(self, supplier: Supplier, update_in: SupplierUpdate) -> Supplier:
        update_data = update_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(supplier, field, value)
        self.db.commit()
        self.db.refresh(supplier)
        return supplier

    # --- Contacts ---
    def add_contact(self, supplier_id: str, organization_id: str, contact_in: SupplierContactCreate) -> SupplierContact:
        contact = SupplierContact(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            supplier_id=supplier_id,
            full_name=contact_in.full_name,
            email=contact_in.email,
            phone=contact_in.phone,
            designation=contact_in.designation,
            is_primary=contact_in.is_primary,
        )
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def list_contacts(self, supplier_id: str, organization_id: str) -> List[SupplierContact]:
        return (
            self.db.query(SupplierContact)
            .filter(SupplierContact.supplier_id == supplier_id, SupplierContact.organization_id == organization_id)
            .all()
        )

    # --- Categories ---
    def create_category(self, organization_id: str, category_in: SupplierCategoryCreate) -> SupplierCategory:
        category = SupplierCategory(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            name=category_in.name,
            description=category_in.description,
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def list_categories(self, organization_id: str) -> List[SupplierCategory]:
        return self.db.query(SupplierCategory).filter(SupplierCategory.organization_id == organization_id).all()

    # --- Historical Delivery Records ---
    def add_delivery_record(
        self, supplier_id: str, organization_id: str, recorded_by: str, record_in: SupplierDeliveryRecordCreate
    ) -> SupplierDeliveryRecord:
        record = SupplierDeliveryRecord(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            supplier_id=supplier_id,
            po_reference=record_in.po_reference,
            promised_delivery_date=record_in.promised_delivery_date,
            actual_delivery_date=record_in.actual_delivery_date,
            on_time=record_in.on_time,
            delay_days=record_in.delay_days,
            source_system=record_in.source_system,
            notes=record_in.notes,
            recorded_by=recorded_by,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_delivery_records(self, supplier_id: str, organization_id: str) -> List[SupplierDeliveryRecord]:
        return (
            self.db.query(SupplierDeliveryRecord)
            .filter(SupplierDeliveryRecord.supplier_id == supplier_id, SupplierDeliveryRecord.organization_id == organization_id)
            .order_by(SupplierDeliveryRecord.actual_delivery_date.desc())
            .all()
        )

    # --- Quality Records ---
    def add_quality_record(
        self, supplier_id: str, organization_id: str, recorded_by: str, record_in: SupplierQualityRecordCreate
    ) -> SupplierQualityRecord:
        record = SupplierQualityRecord(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            supplier_id=supplier_id,
            batch_reference=record_in.batch_reference,
            defect_rate=record_in.defect_rate,
            incident_severity=record_in.incident_severity,
            passed=record_in.passed,
            source_system=record_in.source_system,
            incident_details=record_in.incident_details,
            recorded_by=recorded_by,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_quality_records(self, supplier_id: str, organization_id: str) -> List[SupplierQualityRecord]:
        return (
            self.db.query(SupplierQualityRecord)
            .filter(SupplierQualityRecord.supplier_id == supplier_id, SupplierQualityRecord.organization_id == organization_id)
            .order_by(SupplierQualityRecord.created_at.desc())
            .all()
        )
