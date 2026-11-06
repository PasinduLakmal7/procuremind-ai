import os
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


def test_mcda_optimization_ranking_and_math(client):
    headers = get_auth_headers()
    payload = {
        "request_id": "pr-req-001",
        "budget_limit": 500000.0,
        "currency": "LKR",
        "constraints": {
            "max_budget": 500000.0,
            "max_lead_time_days": 21,
            "disallow_critical_risk": True,
        },
        "weights": {
            "cost_weight": 0.40,
            "delivery_weight": 0.25,
            "quality_weight": 0.20,
            "reliability_weight": 0.15,
        },
        "candidates": [
            {
                "quotation_id": "quo-opt-01",
                "supplier_id": "sup-fast-01",
                "supplier_name": "Swift Industrial Supplies",
                "total_cost": 420000.0,
                "lead_time_days": 7,
                "quality_score": 0.90,
                "risk_score": 0.15,
                "risk_category": "LOW",
                "compliance_passed": True,
            },
            {
                "quotation_id": "quo-opt-02",
                "supplier_id": "sup-cheap-02",
                "supplier_name": "Budget Parts Co",
                "total_cost": 350000.0,  # Lowest cost
                "lead_time_days": 18,
                "quality_score": 0.80,
                "risk_score": 0.35,
                "risk_category": "MEDIUM",
                "compliance_passed": True,
            },
            {
                "quotation_id": "quo-opt-03",
                "supplier_id": "sup-overbudget-03",
                "supplier_name": "Premium Exotics Ltd",
                "total_cost": 550000.0,  # Exceeds 500,000 budget
                "lead_time_days": 5,
                "quality_score": 0.98,
                "risk_score": 0.10,
                "risk_category": "LOW",
                "compliance_passed": True,
            },
            {
                "quotation_id": "quo-opt-04",
                "supplier_id": "sup-critical-04",
                "supplier_name": "Risky Operations",
                "total_cost": 300000.0,
                "lead_time_days": 10,
                "quality_score": 0.70,
                "risk_score": 0.85,
                "risk_category": "CRITICAL",  # Fails critical risk constraint
                "compliance_passed": True,
            },
        ],
    }

    response = client.post("/api/v1/optimization/rank", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()

    assert data["total_evaluated"] == 4
    assert data["eligible_count"] == 2
    assert data["rejected_count"] == 2
    assert len(data["rankings"]) == 4

    # Verify disqualified candidates are flagged with explicit reasons
    disqualified = [r for r in data["rankings"] if not r["is_eligible"]]
    assert len(disqualified) == 2
    overbudget = next(r for r in disqualified if r["supplier_id"] == "sup-overbudget-03")
    assert any("Exceeds budgetary ceiling" in reason for reason in overbudget["rejection_reasons"])

    critical_risk = next(r for r in disqualified if r["supplier_id"] == "sup-critical-04")
    assert any("CRITICAL risk tier" in reason for reason in critical_risk["rejection_reasons"])

    # Verify Rank 1 Winner exists and has positive composite score
    rank_1 = next(r for r in data["rankings"] if r["rank"] == 1)
    assert rank_1["is_eligible"] is True
    assert rank_1["composite_score"] > 0.0
    assert "cost" in rank_1["normalized_scores"]
    assert "delivery" in rank_1["normalized_scores"]

    # Verify scenario persistence and retrieval
    scenario_id = data["scenario_id"]
    get_res = client.get(f"/api/v1/optimization/scenarios/{scenario_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["scenario_id"] == scenario_id

    # Retrieve by PR request_id
    pr_res = client.get("/api/v1/optimization/requests/pr-req-001", headers=headers)
    assert pr_res.status_code == 200
    assert pr_res.json()["request_id"] == "pr-req-001"


def test_invalid_weights_sum_rejected(client):
    headers = get_auth_headers()
    payload = {
        "request_id": "pr-req-002",
        "budget_limit": 100000.0,
        "weights": {
            "cost_weight": 0.60,
            "delivery_weight": 0.30,
            "quality_weight": 0.20,
            "reliability_weight": 0.10,  # Sum = 1.20 != 1.0
        },
        "candidates": [],
    }
    response = client.post("/api/v1/optimization/rank", json=payload, headers=headers)
    assert response.status_code == 422  # Pydantic validation error


def test_tie_breaking_deterministic(client):
    headers = get_auth_headers()
    payload = {
        "request_id": "pr-req-003",
        "budget_limit": 200000.0,
        "candidates": [
            {
                "quotation_id": "quo-a",
                "supplier_id": "sup-b-beta",
                "supplier_name": "Supplier Beta",
                "total_cost": 100000.0,
                "lead_time_days": 10,
                "quality_score": 0.90,
                "risk_score": 0.20,
            },
            {
                "quotation_id": "quo-b",
                "supplier_id": "sup-a-alpha",
                "supplier_name": "Supplier Alpha",
                "total_cost": 100000.0,
                "lead_time_days": 10,
                "quality_score": 0.90,
                "risk_score": 0.20,
            },
        ],
    }
    response = client.post("/api/v1/optimization/rank", json=payload, headers=headers)
    assert response.status_code == 201
    rankings = response.json()["rankings"]
    # Tied on composite, cost, and quality -> Alpha before Beta alphabetically
    assert rankings[0]["supplier_name"] == "Supplier Alpha"
    assert rankings[1]["supplier_name"] == "Supplier Beta"

