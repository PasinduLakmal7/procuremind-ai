import uuid
import pytest
from jose import jwt


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


def test_supplier_crud_and_tenancy(client):
    org_1 = str(uuid.uuid4())
    org_2 = str(uuid.uuid4())
    token_org1 = create_test_token(org_1)
    token_org2 = create_test_token(org_2)

    # 1. Create Supplier in Org 1
    supplier_payload = {
        "company_name": "Lanka Metals & Alloys PLC",
        "contact_email": "sales@lankametals.lk",
        "contact_phone": "+94 11 2345678",
        "address": "12 Industrial Zone, Ekala",
        "city": "Ja-Ela",
        "country": "Sri Lanka",
        "category": "Raw Materials",
        "tax_id": "VAT-998877",
        "tier": "TIER_1",
        "compliance_status": "VERIFIED",
        "rating": 4.5
    }

    create_res = client.post(
        "/api/v1/supplier/suppliers",
        json=supplier_payload,
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert create_res.status_code == 201
    created_data = create_res.json()["data"]
    supplier_id = created_data["id"]
    assert created_data["company_name"] == "Lanka Metals & Alloys PLC"
    assert created_data["organization_id"] == org_1

    # 2. Reject duplicate supplier name in Org 1
    dup_res = client.post(
        "/api/v1/supplier/suppliers",
        json=supplier_payload,
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert dup_res.status_code == 409

    # 3. Retrieve Supplier in Org 1
    get_res = client.get(
        f"/api/v1/supplier/suppliers/{supplier_id}",
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == supplier_id

    # 4. Enforce Organization Isolation: Org 2 cannot see Org 1 supplier
    cross_org_res = client.get(
        f"/api/v1/supplier/suppliers/{supplier_id}",
        headers={"Authorization": f"Bearer {token_org2}"}
    )
    assert cross_org_res.status_code == 404

    # 5. Update Supplier
    update_res = client.put(
        f"/api/v1/supplier/suppliers/{supplier_id}",
        json={"tier": "TIER_1", "rating": 4.8},
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["rating"] == 4.8

    # 6. List Suppliers with category filter
    list_res = client.get(
        "/api/v1/supplier/suppliers?category=Raw",
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert list_res.status_code == 200
    items = list_res.json()["data"]
    assert len(items) >= 1
    assert items[0]["id"] == supplier_id

    # 7. Soft delete supplier
    del_res = client.delete(
        f"/api/v1/supplier/suppliers/{supplier_id}",
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert del_res.status_code == 200
    assert del_res.json()["data"]["deactivated"] is True

