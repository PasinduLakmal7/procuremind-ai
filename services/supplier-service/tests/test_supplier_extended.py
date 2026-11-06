from datetime import datetime, timezone, timedelta
import pytest
from app.schemas.supplier import (
    SupplierCreate,
    SupplierContactCreate,
    SupplierCategoryCreate,
    SupplierDeliveryRecordCreate,
    SupplierQualityRecordCreate,
)
from app.services.supplier_service import SupplierService
from shared.core.exceptions import BadRequestException


def test_supplier_contacts_and_categories(db_session, test_org_id, test_user_id):
    service = SupplierService(db_session)
    
    # 1. Category
    cat = service.create_category(test_org_id, SupplierCategoryCreate(name="Packaging", description="Cartons and plastic"))
    assert cat.name == "Packaging"
    cats = service.list_categories(test_org_id)
    assert len(cats) >= 1

    # 2. Supplier
    supp = service.create_supplier(
        SupplierCreate(
            company_name="Ceylon Packaging Ltd",
            contact_email="sales@ceylonpack.lk",
            category="Packaging",
        ),
        test_org_id,
    )

    # 3. Contact
    contact = service.add_contact(
        supp.id,
        test_org_id,
        SupplierContactCreate(
            full_name="Kasun Perera",
            email="kasun@ceylonpack.lk",
            phone="+94771234567",
            designation="Key Account Manager",
            is_primary=True,
        ),
    )
    assert contact.full_name == "Kasun Perera"
    contacts = service.list_contacts(supp.id, test_org_id)
    assert len(contacts) == 1
    assert contacts[0].email == "kasun@ceylonpack.lk"


def test_supplier_performance_records_and_summary(db_session, test_org_id, test_user_id):
    service = SupplierService(db_session)
    supp = service.create_supplier(
        SupplierCreate(
            company_name="Lanka Industrial Chemicals",
            contact_email="sales@lankachem.lk",
        ),
        test_org_id,
    )

    now = datetime.now(timezone.utc)
    # Add 1 on-time delivery
    service.record_delivery_performance(
        supplier_id=supp.id,
        organization_id=test_org_id,
        recorded_by=test_user_id,
        record_in=SupplierDeliveryRecordCreate(
            po_reference="PO-2026-001",
            promised_delivery_date=now - timedelta(days=5),
            actual_delivery_date=now - timedelta(days=5),
            on_time=True,
            delay_days=0,
            source_system="ERP_EXPORT_GRN",
        ),
    )

    # Add 1 delayed delivery
    service.record_delivery_performance(
        supplier_id=supp.id,
        organization_id=test_org_id,
        recorded_by=test_user_id,
        record_in=SupplierDeliveryRecordCreate(
            po_reference="PO-2026-002",
            promised_delivery_date=now - timedelta(days=3),
            actual_delivery_date=now - timedelta(days=1),
            on_time=False,
            delay_days=2,
            source_system="ERP_EXPORT_GRN",
        ),
    )

    # Add quality record
    service.record_quality_incident(
        supplier_id=supp.id,
        organization_id=test_org_id,
        recorded_by=test_user_id,
        record_in=SupplierQualityRecordCreate(
            batch_reference="BATCH-991",
            defect_rate=1.2,
            incident_severity="MINOR",
            passed=True,
            source_system="QA_LAB_LOG",
        ),
    )

    summary = service.get_performance_summary(supp.id, test_org_id)
    assert summary.total_deliveries == 2
    assert summary.on_time_deliveries == 1
    assert summary.on_time_delivery_rate == 50.0
    assert summary.average_delay_days == 1.0
    assert summary.total_quality_inspections == 1
    assert summary.quality_pass_rate == 100.0
    assert summary.average_defect_rate == 1.2
    assert summary.computed_composite_score > 0


def test_provenance_validation_rejects_empty(db_session, test_org_id, test_user_id):
    service = SupplierService(db_session)
    supp = service.create_supplier(
        SupplierCreate(
            company_name="Quick Steel Corp",
            contact_email="steel@corp.lk",
        ),
        test_org_id,
    )

    with pytest.raises(BadRequestException):
        service.record_delivery_performance(
            supplier_id=supp.id,
            organization_id=test_org_id,
            recorded_by=test_user_id,
            record_in=SupplierDeliveryRecordCreate(
                po_reference="PO-2026-003",
                promised_delivery_date=datetime.now(timezone.utc),
                actual_delivery_date=datetime.now(timezone.utc),
                on_time=True,
                delay_days=0,
                source_system="   ",
            ),
        )

