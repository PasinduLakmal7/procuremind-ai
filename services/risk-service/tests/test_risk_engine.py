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
        data={"sub": user_id, "organization_id": org_id, "roles": ["PROCUREMENT_OFFICER"]},
        secret_key=secret,
    )
    return {"Authorization": f"Bearer {token}"}


def test_insufficient_data_returns_insufficient_data_tier(client):
    headers = get_auth_headers()
    # Supplier with only 1 observation (< 3 threshold)
    payload = {
        "supplier_id": "sup-new-001",
        "supplier_name": "Lanka Fresh Components",
        "delivery_records": [
            {
                "order_id": "ord-1",
                "was_delayed": False,
                "lateness_days": 0,
                "fulfillment_rate": 1.0,
            }
        ],
        "quality_records": [],
    }

    response = client.post("/api/v1/risk/evaluate", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["risk_category"] == "INSUFFICIENT_DATA"
    assert data["data_sufficiency"] == "INSUFFICIENT_DATA"
    assert data["risk_score"] is None
    assert data["observation_count"] == 1
    assert "Insufficient historical data" in data["explanation"]


def test_sufficient_data_calculates_deterministic_score(client):
    headers = get_auth_headers()
    # Supplier with 4 delivery records and 2 quality inspections
    payload = {
        "supplier_id": "sup-seasoned-002",
        "supplier_name": "Colombo Precision Engineering",
        "delivery_records": [
            {"order_id": "ord-1", "was_delayed": False, "lateness_days": 0, "fulfillment_rate": 1.0},
            {"order_id": "ord-2", "was_delayed": True, "lateness_days": 3, "fulfillment_rate": 1.0},
            {"order_id": "ord-3", "was_delayed": False, "lateness_days": 0, "fulfillment_rate": 1.0},
            {"order_id": "ord-4", "was_delayed": False, "lateness_days": 0, "fulfillment_rate": 0.9},
        ],
        "quality_records": [
            {"incident_id": "insp-1", "defect_rate": 0.02, "severity": "LOW"},
            {"incident_id": "insp-2", "defect_rate": 0.04, "severity": "MEDIUM"},
        ],
    }

    response = client.post("/api/v1/risk/evaluate", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["data_sufficiency"] == "SUFFICIENT"
    assert data["risk_score"] is not None
    assert data["risk_score"] > 0.0
    assert data["risk_category"] in ["LOW", "MEDIUM"]
    assert data["observation_count"] == 6
    assert data["metrics_breakdown"]["late_deliveries_count"] == 1
    assert data["metrics_breakdown"]["total_quality_inspections"] == 2

    # Query latest assessment
    get_res = client.get(f"/api/v1/risk/suppliers/{data['supplier_id']}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["assessment_id"] == data["assessment_id"]


def test_high_risk_and_critical_incidents(client):
    headers = get_auth_headers()
    payload = {
        "supplier_id": "sup-failing-003",
        "supplier_name": "Faulty Fabrications Ltd",
        "delivery_records": [
            {"order_id": "ord-1", "was_delayed": True, "lateness_days": 14, "fulfillment_rate": 0.6},
            {"order_id": "ord-2", "was_delayed": True, "lateness_days": 10, "fulfillment_rate": 0.5},
            {"order_id": "ord-3", "was_delayed": True, "lateness_days": 8, "fulfillment_rate": 0.7},
        ],
        "quality_records": [
            {"incident_id": "insp-1", "defect_rate": 0.25, "severity": "CRITICAL"},
            {"incident_id": "insp-2", "defect_rate": 0.30, "severity": "HIGH"},
        ],
    }

    response = client.post("/api/v1/risk/evaluate", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["risk_category"] in ["HIGH", "CRITICAL"]
    assert data["risk_score"] > 0.50
    assert data["metrics_breakdown"]["critical_incident_count"] == 2


def test_ml_status_endpoint_returns_limitations_and_provenance(client):
    headers = get_auth_headers()
    response = client.get("/api/v1/risk/ml/status", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_trained"] is True
    assert "metrics" in data
    assert len(data["limitations"]) > 0
    assert "provenance" in data
