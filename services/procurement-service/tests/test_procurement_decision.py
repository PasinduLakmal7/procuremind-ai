import os
import uuid
import pytest
from shared.auth.jwt_validator import create_access_token


def get_auth_headers(
    org_id="11111111-1111-1111-1111-111111111111",
    user_id="22222222-2222-2222-2222-222222222222",
):
    secret = os.environ.get("JWT_SECRET_KEY", "test-secret-key-32-characters-minimum-length-for-testing")
    token = create_access_token(
        data={"sub": user_id, "organization_id": org_id, "roles": ["PROCUREMENT_OFFICER", "MANAGER"]},
        secret_key=secret,
    )
    return {"Authorization": f"Bearer {token}"}


def test_procurement_human_approval_decision(client):
    headers = get_auth_headers()

    # 1. Create PR
    pr_res = client.post(
        "/api/v1/procurement/requests",
        json={"title": "CNC Milling Cutters", "category": "Machinery", "budget_limit": 800000.0},
        headers=headers,
    )
    assert pr_res.status_code == 201
    pr_id = pr_res.json()["data"]["id"]

    # 2. Add Item
    item_res = client.post(
        f"/api/v1/procurement/requests/{pr_id}/items",
        json={"item_name": "Carbide End Mills 10mm", "quantity": 50, "unit_of_measure": "PCS"},
        headers=headers,
    )
    assert item_res.status_code == 201

    # 3. Submit PR
    sub_res = client.patch(
        f"/api/v1/procurement/requests/{pr_id}/status",
        json={"status": "SUBMITTED"},
        headers=headers,
    )
    assert sub_res.status_code == 200
    assert sub_res.json()["data"]["status"] == "SUBMITTED"

    # 4. Add 2 Quotations
    q1_res = client.post(
        f"/api/v1/procurement/requests/{pr_id}/quotations",
        json={
            "supplier_id": "sup-alpha",
            "quotation_number": "QUO-A-1",
            "total_cost": 720000.0,
            "items": [{"item_name": "Carbide End Mills", "quantity": 50, "unit_price": 14400.0}],
        },
        headers=headers,
    )
    assert q1_res.status_code == 201
    q1_id = q1_res.json()["data"]["id"]

    q2_res = client.post(
        f"/api/v1/procurement/requests/{pr_id}/quotations",
        json={
            "supplier_id": "sup-beta",
            "quotation_number": "QUO-B-1",
            "total_cost": 790000.0,
            "items": [{"item_name": "Carbide End Mills", "quantity": 50, "unit_price": 15800.0}],
        },
        headers=headers,
    )
    assert q2_res.status_code == 201
    q2_id = q2_res.json()["data"]["id"]

    # 5. Record Human APPROVAL Decision
    dec_res = client.post(
        f"/api/v1/procurement/requests/{pr_id}/decision",
        json={
            "action": "APPROVE",
            "decision_reason": "Approved winning quotation QUO-A-1 from Supplier Alpha based on superior cost and ISO compliance.",
            "selected_supplier_id": "sup-alpha",
            "selected_quotation_id": q1_id,
        },
        headers=headers,
    )
    assert dec_res.status_code == 200
    dec_data = dec_res.json()["data"]
    assert dec_data["status"] == "APPROVED"
    assert len(dec_data["audit_events"]) > 0
    decision_audits = [a for a in dec_data["audit_events"] if a["event_type"] == "DECISION_APPROVED"]
    assert len(decision_audits) == 1

    # Check quotation status updates
    quotes = client.get(f"/api/v1/procurement/requests/{pr_id}/quotations", headers=headers).json()["data"]
    q1 = next(q for q in quotes if q["id"] == q1_id)
    q2 = next(q for q in quotes if q["id"] == q2_id)
    assert q1["status"] == "ACCEPTED"
    assert q2["status"] == "REJECTED"


def test_procurement_human_rejection_decision(client):
    headers = get_auth_headers()
    pr_res = client.post(
        "/api/v1/procurement/requests",
        json={"title": "Hydraulic Seals", "category": "Spare Parts", "budget_limit": 100000.0},
        headers=headers,
    )
    pr_id = pr_res.json()["data"]["id"]
    client.post(
        f"/api/v1/procurement/requests/{pr_id}/items",
        json={"item_name": "O-Rings", "quantity": 100},
        headers=headers,
    )
    client.patch(f"/api/v1/procurement/requests/{pr_id}/status", json={"status": "SUBMITTED"}, headers=headers)

    dec_res = client.post(
        f"/api/v1/procurement/requests/{pr_id}/decision",
        json={"action": "REJECT", "decision_reason": "Budget cuts cancelled this quarter's maintenance purchase."},
        headers=headers,
    )
    assert dec_res.status_code == 200
    assert dec_res.json()["data"]["status"] == "REJECTED"
