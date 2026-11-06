import uuid
import pytest
from jose import jwt

def test_optimization_service_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["service"] == "optimization-service"
    assert res.json()["status"] == "ok"

    res_ready = client.get("/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ok"

def test_cross_service_jwt_verification(client):
    secret_key = "test-secret-key-32-characters-minimum-length-for-testing"
    user_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    
    # 1. Valid token
    token = jwt.encode({
        "sub": user_id,
        "email": "analyst@factory.lk",
        "organization_id": org_id,
        "roles": ["procurement_officer"],
        "token_type": "access",
        "exp": 2000000000
    }, secret_key, algorithm="HS256")

    res = client.get(
        "/api/v1/optimization/status/summary",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["service"] == "optimization-service"
    assert data["organization_id"] == org_id
    assert data["caller_email"] == "analyst@factory.lk"

    # 2. Tampered token
    tampered_res = client.get(
        "/api/v1/optimization/status/summary",
        headers={"Authorization": "Bearer tampered.token.here"}
    )
    assert tampered_res.status_code == 401
