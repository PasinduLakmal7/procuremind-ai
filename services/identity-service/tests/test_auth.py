import uuid
import pytest


def test_health_endpoints(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["service"] == "identity-service"

    res_ready = client.get("/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ok"


def test_organization_and_user_registration(client):
    # 1. Create Organization
    org_payload = {
        "name": "Colombo Steel Works PLC",
        "registration_number": "PV-12345",
        "industry": "Steel Manufacturing"
    }
    org_res = client.post("/api/v1/identity/organizations", json=org_payload)
    assert org_res.status_code == 200
    org_data = org_res.json()["data"]
    org_id = org_data["id"]
    assert org_data["name"] == "Colombo Steel Works PLC"

    # 2. Register User
    user_payload = {
        "email": "procurement@colombosteel.lk",
        "full_name": "Kasun Perera",
        "password": "StrongPassword123!",
        "organization_id": org_id,
        "roles": ["procurement_officer"]
    }
    user_res = client.post("/api/v1/identity/users/register", json=user_payload)
    assert user_res.status_code == 200
    user_data = user_res.json()["data"]
    assert user_data["email"] == "procurement@colombosteel.lk"
    assert "procurement_officer" in user_data["roles"]


def test_user_login_and_token_refresh(client):
    # Setup Org & User
    org_res = client.post("/api/v1/identity/organizations", json={"name": "Lanka Fabrics Ltd"})
    org_id = org_res.json()["data"]["id"]

    client.post("/api/v1/identity/users/register", json={
        "email": "manager@lankafabrics.lk",
        "full_name": "Anoma Silva",
        "password": "ManagerPass123!",
        "organization_id": org_id,
        "roles": ["procurement_manager"]
    })

    # 1. Valid Login
    login_res = client.post("/api/v1/identity/auth/login", json={
        "email": "manager@lankafabrics.lk",
        "password": "ManagerPass123!"
    })
    assert login_res.status_code == 200
    tokens = login_res.json()["data"]
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    assert access_token is not None
    assert refresh_token is not None
    assert "procurement_manager" in tokens["roles"]

    # 2. Access Protected /me endpoint
    me_res = client.get("/api/v1/identity/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_res.status_code == 200
    profile = me_res.json()["data"]
    assert profile["email"] == "manager@lankafabrics.lk"
    assert profile["full_name"] == "Anoma Silva"

    # 3. Refresh Token
    refresh_res = client.post("/api/v1/identity/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    new_tokens = refresh_res.json()["data"]
    new_access_token = new_tokens["access_token"]
    new_refresh_token = new_tokens["refresh_token"]
    assert new_access_token != access_token

    # 4. Old refresh token should be revoked (token rotation)
    reused_res = client.post("/api/v1/identity/auth/refresh", json={"refresh_token": refresh_token})
    assert reused_res.status_code == 401

    # 5. Logout
    logout_res = client.post("/api/v1/identity/auth/logout", json={"refresh_token": new_refresh_token})
    assert logout_res.status_code == 200


def test_invalid_login_rejection(client):
    res = client.post("/api/v1/identity/auth/login", json={
        "email": "nonexistent@manufacturing.lk",
        "password": "wrongpassword"
    })
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHORIZED"

