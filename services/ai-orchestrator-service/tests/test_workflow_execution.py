import uuid
import pytest
from app.models.agent_workflow_executions import AgentWorkflowExecution
from shared.extraction.schemas import StructuredQuotationData, ExtractedLineItem


def test_workflow_pause_at_human_review_and_resume(client, db_session, auth_headers, test_org_id):
    pr_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())

    # 1. Start workflow with unverified, lower-confidence extraction
    raw_quote = StructuredQuotationData(
        supplier_name="Colombo Machine Tools",
        quotation_number="QUO-CMT-992",
        currency="LKR",
        subtotal=450000.0,
        total_cost=486000.0,
        overall_confidence=0.78,  # Below 0.85 threshold
        arithmetic_valid=True,
        flagged_reasons=["Confidence score below threshold (0.78)"],
        line_items=[
            ExtractedLineItem(
                item_name="CNC Lathe Chuck 8 inch",
                quantity=2.0,
                unit_of_measure="UNITS",
                unit_price=225000.0,
                total_price=450000.0,
            )
        ]
    )

    start_res = client.post(
        "/api/v1/ai-orchestrator/workflows/start",
        json={
            "purchase_request_id": pr_id,
            "document_id": doc_id,
            "extracted_data": raw_quote.model_dump(),
            "is_verified": False,
        },
        headers=auth_headers,
    )
    assert start_res.status_code == 201
    wf_data = start_res.json()["data"]
    wf_id = wf_data["workflow_id"]

    # Must be paused for human review!
    assert wf_data["status"] == "WAITING_FOR_HUMAN_REVIEW"
    assert wf_data["requires_human_review"] is True
    assert "not been verified" in wf_data["human_review_reason"]

    # 2. Check workflow status endpoint
    status_res = client.get(
        f"/api/v1/ai-orchestrator/workflows/{wf_id}/status",
        headers=auth_headers,
    )
    assert status_res.status_code == 200
    assert status_res.json()["data"]["status"] == "WAITING_FOR_HUMAN_REVIEW"

    # 3. Simulate human verification and resume workflow
    verified_quote = raw_quote.model_copy(update={"overall_confidence": 1.0, "flagged_reasons": []})
    resume_res = client.post(
        f"/api/v1/ai-orchestrator/workflows/{wf_id}/resume",
        json={
            "updated_extracted_data": verified_quote.model_dump(),
            "confirm_human_verification": True,
        },
        headers=auth_headers,
    )
    assert resume_res.status_code == 200
    resumed_data = resume_res.json()["data"]

    # Must have completed all downstream multi-agent nodes
    assert resumed_data["status"] == "COMPLETED"
    assert resumed_data["current_step"] == "COMPLETED"
    assert resumed_data["requires_human_review"] is False

    # Check that state snapshot preserves risk, optimization, and explainability report
    state = resumed_data["state"]
    assert state["supplier_profile"] is not None
    assert state["risk_assessment"] is not None
    assert "supplier_risk_tier" in state["risk_assessment"]
    assert state["optimization"] is not None
    assert "composite_score" in state["optimization"]
    assert state["policy_validation"] is not None
    assert state["policy_validation"]["policy_compliant"] is True
    assert state["explainability_report"] is not None
    assert "top_supplier_rationale" in state["explainability_report"]
    assert state["recommendation"]["recommended_action"] == "PROCEED_TO_HUMAN_APPROVAL"


def test_workflow_direct_completion_when_preverified(client, db_session, auth_headers):
    pr_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())

    perfect_quote = StructuredQuotationData(
        supplier_name="Verified Industrial Supplier Ltd",
        quotation_number="QUO-VIS-101",
        currency="LKR",
        subtotal=100000.0,
        total_cost=100000.0,
        overall_confidence=0.98,
        arithmetic_valid=True,
        flagged_reasons=[],
        line_items=[
            ExtractedLineItem(
                item_name="Pneumatic Cylinder",
                quantity=1.0,
                unit_of_measure="PCS",
                unit_price=100000.0,
                total_price=100000.0,
            )
        ]
    )

    start_res = client.post(
        "/api/v1/ai-orchestrator/workflows/start",
        json={
            "purchase_request_id": pr_id,
            "document_id": doc_id,
            "extracted_data": perfect_quote.model_dump(),
            "is_verified": True,
        },
        headers=auth_headers,
    )
    assert start_res.status_code == 201
    wf_data = start_res.json()["data"]
    assert wf_data["status"] == "COMPLETED"


def test_stage_4_multi_criteria_and_explainable_recommendation(client, db_session, auth_headers):
    pr_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    sup_id = "sup-lanka-metals"

    quote = StructuredQuotationData(
        supplier_name="Lanka Precision Metals",
        quotation_number="QUO-LPM-882",
        currency="LKR",
        subtotal=650000.0,
        total_cost=650000.0,
        overall_confidence=0.95,
        arithmetic_valid=True,
        flagged_reasons=[],
        line_items=[
            ExtractedLineItem(
                item_name="Alloy Steel Rods 25mm",
                quantity=100.0,
                unit_of_measure="KG",
                unit_price=6500.0,
                total_price=650000.0,
            )
        ]
    )

    # 4 historical delivery orders and 2 quality inspections
    historical_orders = [
        {"order_id": "po-1", "was_delayed": False, "lateness_days": 0, "fulfillment_rate": 1.0},
        {"order_id": "po-2", "was_delayed": False, "lateness_days": 0, "fulfillment_rate": 1.0},
        {"order_id": "po-3", "was_delayed": True, "lateness_days": 2, "fulfillment_rate": 1.0},
        {"order_id": "po-4", "was_delayed": False, "lateness_days": 0, "fulfillment_rate": 0.95},
    ]
    quality_records = [
        {"incident_id": "qa-1", "defect_rate": 0.01, "severity": "LOW"},
        {"incident_id": "qa-2", "defect_rate": 0.02, "severity": "LOW"},
    ]

    # Alternative candidate supplier
    alternatives = [
        {
            "quotation_id": "quo-alt-01",
            "supplier_id": "sup-expensive-alt",
            "supplier_name": "Overseas Heavy Alloys",
            "total_cost": 850000.0,
            "lead_time_days": 28,
            "quality_score": 0.95,
            "risk_score": 0.40,
            "risk_category": "MEDIUM",
            "compliance_passed": True,
        }
    ]

    weights = {"cost": 0.50, "delivery": 0.20, "quality": 0.15, "reliability": 0.15}

    response = client.post(
        "/api/v1/ai-orchestrator/workflows/start",
        json={
            "purchase_request_id": pr_id,
            "document_id": doc_id,
            "supplier_id": sup_id,
            "extracted_data": quote.model_dump(),
            "is_verified": True,
            "supplier_historical_orders": historical_orders,
            "supplier_quality_records": quality_records,
            "alternative_candidates": alternatives,
            "evaluation_weights": weights,
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["status"] == "COMPLETED"

    state = data["state"]
    # 1. Supplier analysis checks
    assert state["supplier_profile"]["total_observations"] == 6
    assert state["supplier_profile"]["has_sufficient_history"] is True

    # 2. Risk assessment
    assert state["risk_assessment"]["data_sufficiency"] == "SUFFICIENT"
    assert state["risk_assessment"]["supplier_risk_tier"] in ["LOW", "MEDIUM"]

    # 3. Optimization rankings
    opt = state["optimization"]
    assert opt["recommended_ranking"] == 1
    assert len(opt["rankings"]) == 2
    assert opt["rankings"][0]["supplier_name"] == "Lanka Precision Metals"

    # 4. Explainable AI report
    exp = state["explainability_report"]
    assert "Lanka Precision Metals" in exp["top_supplier_rationale"]
    assert exp["policy_compliance"]["sri_lanka_vat_checked"] is True

    # 5. Decision preparation
    rec = state["recommendation"]
    assert rec["recommended_action"] == "PROCEED_TO_HUMAN_APPROVAL"
    assert "Human Procurement Manager" in rec["governance_notice"]
