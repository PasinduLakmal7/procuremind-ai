import pytest


def test_rbac_and_organization_isolation(client):
    # Setup Org 1
    org1_res = client.post("/api/v1/identity/organizations", json={"name": "Kandy Tea Exporters"})
    org1_id = org1_res.json()["data"]["id"]

    # Setup Org 2
    org2_res = client.post("/api/v1/identity/organizations", json={"name": "Galle Cement Factory"})
    org2_id = org2_res.json()["data"]["id"]

    # User 1: Regular Procurement Officer in Org 1
    client.post("/api/v1/identity/users/register", json={
        "email": "officer@kandytea.lk",
        "full_name": "Ruwan Perera",
        "password": "Password123!",
        "organization_id": org1_id,
        "roles": ["procurement_officer"]
    })

    # User 2: Admin in Org 1
    client.post("/api/v1/identity/users/register", json={
        "email": "admin@kandytea.lk",
        "full_name": "Admin User",
        "password": "AdminPassword123!",
        "organization_id": org1_id,
        "roles": ["admin"]
    })

    # Login as Officer
    officer_login = client.post("/api/v1/identity/auth/login", json={
        "email": "officer@kandytea.lk",
        "password": "Password123!"
    })
    officer_token = officer_login.json()["data"]["access_token"]

    # Login as Admin
    admin_login = client.post("/api/v1/identity/auth/login", json={
        "email": "admin@kandytea.lk",
        "password": "AdminPassword123!"
    })
    admin_token = admin_login.json()["data"]["access_token"]

    # Test 1: Officer cannot list all organizations (admin only)
    res_list_orgs = client.get("/api/v1/identity/organizations", headers={"Authorization": f"Bearer {officer_token}"})
    assert res_list_orgs.status_code == 403

    # Test 2: Admin can list organizations
    res_admin_orgs = client.get("/api/v1/identity/organizations", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin_orgs.status_code == 200
    assert len(res_admin_orgs.json()["data"]) >= 2

    # Test 3: Officer cannot access Org 2 directly
    res_cross_org = client.get(f"/api/v1/identity/organizations/{org2_id}", headers={"Authorization": f"Bearer {officer_token}"})
    assert res_cross_org.status_code == 403

    # Test 4: Officer CAN access own Org 1
    res_own_org = client.get(f"/api/v1/identity/organizations/{org1_id}", headers={"Authorization": f"Bearer {officer_token}"})
    assert res_own_org.status_code == 200
    assert res_own_org.json()["data"]["name"] == "Kandy Tea Exporters"


def test_expired_or_invalid_token(client):
    # Invalid token string
    res = client.get("/api/v1/identity/auth/me", headers={"Authorization": "Bearer invalid.token.payload"})
    assert res.status_code == 401

    # Missing authorization header
    res_missing = client.get("/api/v1/identity/auth/me")
    assert res_missing.status_code == 401

