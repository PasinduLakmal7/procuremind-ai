import uuid
import pytest
from jose import jwt
from app.models.purchase_requests import OutboxEvent


def create_test_token(org_id: str, email: str = "officer@factory.lk", role: str = "procurement_officer") -> str:
    secret_key = "test-secret-key-32-characters-minimum-length-for-testing"
    return jwt.encode({
        "sub": str(uuid.uuid4()),
        "email": email,
        "organization_id": org_id,
        "roles": [role],
        "token_type": "access",
        "exp": 2000000000
    }, secret_key, algorithm="HS256")


def test_purchase_request_and_quotations_lifecycle(client, db_session):
    org_1 = str(uuid.uuid4())
    org_2 = str(uuid.uuid4())
    token_org1 = create_test_token(org_1)
    token_org2 = create_test_token(org_2)

    # 1. Create Purchase Request in Org 1 (starts in DRAFT)
    pr_payload = {
        "title": "Industrial Steel Rods 20mm",
        "description": "Required for Q1 structural assembly",
        "category": "Steel & Metals",
        "priority": "HIGH",
        "budget_limit": 1500000.0,
        "currency": "LKR",
        "items": [
            {"item_name": "Steel Rod 20mm x 6m", "quantity": 500, "unit_of_measure": "units", "target_unit_price": 3000.0}
        ]
    }

    create_res = client.post(
        "/api/v1/procurement/requests",
        json=pr_payload,
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert create_res.status_code == 201
    pr_data = create_res.json()["data"]
    pr_id = pr_data["id"]
    assert pr_data["title"] == "Industrial Steel Rods 20mm"
    assert pr_data["status"] == "DRAFT"
    assert pr_data["request_number"].startswith("PR-2026-")
    assert len(pr_data["items"]) == 1

    # 2. Retrieve Single PR
    get_res = client.get(
        f"/api/v1/procurement/requests/{pr_id}",
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == pr_id

    # 3. Tenant Isolation Check: Org 2 cannot retrieve Org 1 PR
    cross_org_res = client.get(
        f"/api/v1/procurement/requests/{pr_id}",
        headers={"Authorization": f"Bearer {token_org2}"}
    )
    assert cross_org_res.status_code == 404

    # 4. Associate Candidate Supplier
    supplier_1 = str(uuid.uuid4())
    cand_res = client.post(
        f"/api/v1/procurement/requests/{pr_id}/candidate-suppliers",
        json={"supplier_id": supplier_1, "supplier_name": "Lanka Metals Ltd", "supplier_email": "sales@lankametals.lk"},
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert cand_res.status_code == 201
    assert cand_res.json()["data"]["supplier_name"] == "Lanka Metals Ltd"

    # 5. Invalid State Transition Rejected (DRAFT cannot jump directly to APPROVED)
    invalid_res = client.patch(
        f"/api/v1/procurement/requests/{pr_id}/status",
        json={"status": "APPROVED"},
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert invalid_res.status_code == 422

    # 6. Submit Purchase Request (DRAFT -> SUBMITTED)
    submit_res = client.patch(
        f"/api/v1/procurement/requests/{pr_id}/status",
        json={"status": "SUBMITTED"},
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["data"]["status"] == "SUBMITTED"

    # Verify Outbox event was created in the database transactionally
    outbox_event = db_session.query(OutboxEvent).filter(
        OutboxEvent.aggregate_id == pr_id,
        OutboxEvent.event_type == "purchase_request.submitted.v1"
    ).first()
    assert outbox_event is not None
    assert outbox_event.status == "PENDING"

    # 7. Submit Quotation 1 for PR
    quote_payload_1 = {
        "supplier_id": supplier_1,
        "quotation_number": "QUO-LM-2026-001",
        "total_cost": 1420000.0,
        "currency": "LKR",
        "estimated_delivery_days": 10,
        "warranty_terms": "12 Months Structural Warranty",
        "payment_terms": "Net 30"
    }
    quote_res_1 = client.post(
        f"/api/v1/procurement/requests/{pr_id}/quotations",
        json=quote_payload_1,
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert quote_res_1.status_code == 201
    assert quote_res_1.json()["data"]["total_cost"] == 1420000.0

    # 8. Submit Quotation 2 for PR
    supplier_2 = str(uuid.uuid4())
    quote_payload_2 = {
        "supplier_id": supplier_2,
        "quotation_number": "QUO-CS-2026-089",
        "total_cost": 1390000.0,
        "currency": "LKR",
        "estimated_delivery_days": 7,
        "warranty_terms": "6 Months Warranty",
        "payment_terms": "Advance 20%, Balance 80%"
    }
    quote_res_2 = client.post(
        f"/api/v1/procurement/requests/{pr_id}/quotations",
        json=quote_payload_2,
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert quote_res_2.status_code == 201

    # 9. List Quotations for PR
    list_quotes_res = client.get(
        f"/api/v1/procurement/requests/{pr_id}/quotations",
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert list_quotes_res.status_code == 200
    quotes = list_quotes_res.json()["data"]
    assert len(quotes) == 2
    assert quotes[0]["total_cost"] <= quotes[1]["total_cost"]

    # 10. Update PR Status to UNDER_EVALUATION
    status_res = client.patch(
        f"/api/v1/procurement/requests/{pr_id}/status",
        json={"status": "UNDER_EVALUATION"},
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert status_res.status_code == 200
    assert status_res.json()["data"]["status"] == "UNDER_EVALUATION"

    # 11. View PR Full Details
    detail_res = client.get(
        f"/api/v1/procurement/requests/{pr_id}/details",
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert detail_res.status_code == 200
    detail = detail_res.json()["data"]
    assert len(detail["items"]) == 1
    assert len(detail["candidate_suppliers"]) == 1
    assert len(detail["audit_events"]) >= 4
