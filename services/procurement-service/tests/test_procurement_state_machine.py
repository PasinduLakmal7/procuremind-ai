import uuid
import pytest
from app.schemas.purchase_request import (
    PurchaseRequestCreate,
    PurchaseRequestUpdate,
    PurchaseRequestItemCreate,
    PurchaseRequestStatusUpdate,
)
from app.services.procurement_service import ProcurementService
from shared.core.exceptions import ValidationException


def test_procurement_state_machine_and_item_modifications(db_session, test_org_id, test_user_id):
    service = ProcurementService(db_session)

    # 1. Create Draft PR with no initial items
    pr = service.create_request(
        PurchaseRequestCreate(
            title="Packaging Tape 48mm",
            budget_limit=50000.0,
            currency="LKR",
        ),
        organization_id=test_org_id,
        user_id=test_user_id,
    )
    assert pr.status == "DRAFT"

    # 2. Cannot submit with 0 items
    with pytest.raises(ValidationException) as exc:
        service.update_status(
            pr.id,
            PurchaseRequestStatusUpdate(status="SUBMITTED"),
            organization_id=test_org_id,
            user_id=test_user_id,
        )
    assert "0 items" in str(exc.value)

    # 3. Add an item in DRAFT
    item = service.add_item(
        pr.id,
        PurchaseRequestItemCreate(
            item_name="Brown Tape Roll",
            quantity=100.0,
            unit_of_measure="ROLLS",
            target_unit_price=500.0,
        ),
        organization_id=test_org_id,
        user_id=test_user_id,
    )
    assert item.item_name == "Brown Tape Roll"

    # 4. Edit draft
    updated = service.update_draft(
        pr.id,
        PurchaseRequestUpdate(title="Heavy-Duty Packaging Tape 48mm"),
        organization_id=test_org_id,
        user_id=test_user_id,
    )
    assert updated.title == "Heavy-Duty Packaging Tape 48mm"

    # 5. Now submission succeeds
    submitted = service.update_status(
        pr.id,
        PurchaseRequestStatusUpdate(status="SUBMITTED"),
        organization_id=test_org_id,
        user_id=test_user_id,
    )
    assert submitted.status == "SUBMITTED"

    # 6. Cannot edit after submission
    with pytest.raises(ValidationException):
        service.update_draft(
            pr.id,
            PurchaseRequestUpdate(title="Should fail"),
            organization_id=test_org_id,
            user_id=test_user_id,
        )

    # 7. Cannot add items after submission
    with pytest.raises(ValidationException):
        service.add_item(
            pr.id,
            PurchaseRequestItemCreate(
                item_name="Another item",
                quantity=10.0,
            ),
            organization_id=test_org_id,
            user_id=test_user_id,
        )

