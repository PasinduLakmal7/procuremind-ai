from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierContactCreate,
    SupplierContactResponse,
    SupplierCategoryCreate,
    SupplierCategoryResponse,
    SupplierDeliveryRecordCreate,
    SupplierDeliveryRecordResponse,
    SupplierQualityRecordCreate,
    SupplierQualityRecordResponse,
    SupplierPerformanceSummary,
)
from shared.core.exceptions import ConflictException, NotFoundException, BadRequestException


class SupplierService:
    def __init__(self, db: Session):
        self.repo = SupplierRepository(db)

    def create_supplier(self, data: SupplierCreate, organization_id: str) -> SupplierResponse:
        existing = self.repo.get_by_name(data.company_name, organization_id)
        if existing:
            raise ConflictException(f"Supplier '{data.company_name}' already exists in this organization.")
        supplier = self.repo.create(data, organization_id)
        return SupplierResponse.model_validate(supplier)

    def get_supplier(self, supplier_id: str, organization_id: str) -> SupplierResponse:
        supplier = self.repo.get_by_id(supplier_id, organization_id)
        if not supplier:
            raise NotFoundException(f"Supplier '{supplier_id}' not found.")
        return SupplierResponse.model_validate(supplier)

    def list_suppliers(
        self,
        organization_id: str,
        category: Optional[str] = None,
        tier: Optional[str] = None,
        compliance_status: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SupplierResponse]:
        suppliers = self.repo.list_all(
            organization_id=organization_id,
            category=category,
            tier=tier,
            compliance_status=compliance_status,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )
        return [SupplierResponse.model_validate(s) for s in suppliers]

    def update_supplier(self, supplier_id: str, update_in: SupplierUpdate, organization_id: str) -> SupplierResponse:
        supplier = self.repo.get_by_id(supplier_id, organization_id)
        if not supplier:
            raise NotFoundException(f"Supplier '{supplier_id}' not found.")
        updated = self.repo.update(supplier, update_in)
        return SupplierResponse.model_validate(updated)

    def delete_supplier(self, supplier_id: str, organization_id: str) -> None:
        supplier = self.repo.get_by_id(supplier_id, organization_id)
        if not supplier:
            raise NotFoundException(f"Supplier '{supplier_id}' not found.")
        self.repo.update(supplier, SupplierUpdate(is_active=False))

    # --- Contacts ---
    def add_contact(self, supplier_id: str, organization_id: str, contact_in: SupplierContactCreate) -> SupplierContactResponse:
        self.get_supplier(supplier_id, organization_id)
        contact = self.repo.add_contact(supplier_id, organization_id, contact_in)
        return SupplierContactResponse.model_validate(contact)

    def list_contacts(self, supplier_id: str, organization_id: str) -> List[SupplierContactResponse]:
        self.get_supplier(supplier_id, organization_id)
        contacts = self.repo.list_contacts(supplier_id, organization_id)
        return [SupplierContactResponse.model_validate(c) for c in contacts]

    # --- Categories ---
    def create_category(self, organization_id: str, category_in: SupplierCategoryCreate) -> SupplierCategoryResponse:
        category = self.repo.create_category(organization_id, category_in)
        return SupplierCategoryResponse.model_validate(category)

    def list_categories(self, organization_id: str) -> List[SupplierCategoryResponse]:
        categories = self.repo.list_categories(organization_id)
        return [SupplierCategoryResponse.model_validate(c) for c in categories]

    # --- Performance & Quality Records ---
    def record_delivery_performance(
        self, supplier_id: str, organization_id: str, recorded_by: str, record_in: SupplierDeliveryRecordCreate
    ) -> SupplierDeliveryRecordResponse:
        self.get_supplier(supplier_id, organization_id)
        if not record_in.source_system or len(record_in.source_system.strip()) < 2:
            raise BadRequestException("Source provenance is required for historical performance auditing.")
        record = self.repo.add_delivery_record(supplier_id, organization_id, recorded_by, record_in)
        return SupplierDeliveryRecordResponse.model_validate(record)

    def record_quality_incident(
        self, supplier_id: str, organization_id: str, recorded_by: str, record_in: SupplierQualityRecordCreate
    ) -> SupplierQualityRecordResponse:
        self.get_supplier(supplier_id, organization_id)
        if not record_in.source_system or len(record_in.source_system.strip()) < 2:
            raise BadRequestException("Source provenance is required for quality audit logging.")
        record = self.repo.add_quality_record(supplier_id, organization_id, recorded_by, record_in)
        return SupplierQualityRecordResponse.model_validate(record)

    def get_performance_summary(self, supplier_id: str, organization_id: str) -> SupplierPerformanceSummary:
        supplier = self.repo.get_by_id(supplier_id, organization_id)
        if not supplier:
            raise NotFoundException(f"Supplier '{supplier_id}' not found.")

        deliveries = self.repo.list_delivery_records(supplier_id, organization_id)
        qualities = self.repo.list_quality_records(supplier_id, organization_id)

        total_deliveries = len(deliveries)
        on_time_count = sum(1 for d in deliveries if d.on_time)
        on_time_rate = round((on_time_count / total_deliveries) * 100.0, 2) if total_deliveries > 0 else 100.0
        avg_delay = round(sum(d.delay_days for d in deliveries) / total_deliveries, 2) if total_deliveries > 0 else 0.0

        total_qualities = len(qualities)
        passed_count = sum(1 for q in qualities if q.passed)
        pass_rate = round((passed_count / total_qualities) * 100.0, 2) if total_qualities > 0 else 100.0
        avg_defect = round(sum(q.defect_rate for q in qualities) / total_qualities, 2) if total_qualities > 0 else 0.0
        critical_count = sum(1 for q in qualities if q.incident_severity == "CRITICAL")

        # Composite score calculation (0 - 5.0)
        # 50% delivery on-time rate, 50% quality pass rate minus penalties for critical incidents
        delivery_score = (on_time_rate / 100.0) * 2.5
        quality_score = (pass_rate / 100.0) * 2.5
        composite = max(0.0, min(5.0, round(delivery_score + quality_score - (critical_count * 0.5), 2)))

        return SupplierPerformanceSummary(
            supplier_id=supplier.id,
            organization_id=organization_id,
            company_name=supplier.company_name,
            total_deliveries=total_deliveries,
            on_time_deliveries=on_time_count,
            on_time_delivery_rate=on_time_rate,
            average_delay_days=avg_delay,
            total_quality_inspections=total_qualities,
            passed_inspections=passed_count,
            quality_pass_rate=pass_rate,
            average_defect_rate=avg_defect,
            critical_incidents_count=critical_count,
            computed_composite_score=composite,
        )
