import os
import sys
import uuid
import pytest
from pathlib import Path

# Add services and shared directories to sys.path
WORKSPACE_DIR = Path(__file__).resolve().parents[2]
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))
if str(WORKSPACE_DIR / "shared") not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR / "shared"))

def clear_app_modules():
    for mod in list(sys.modules.keys()):
        if mod == "app" or mod.startswith("app."):
            del sys.modules[mod]


# 1. Test Risk Evaluation Engine Directly
def test_risk_evaluation_deterministic_engine():
    clear_app_modules()
    sys.path.insert(0, str(WORKSPACE_DIR / "services" / "risk-service"))
    from app.services.risk_engine import RiskEvaluationEngine
    from app.schemas.risk import RiskEvaluationRequest, DeliveryObservation, QualityObservation
    from app.db.base import Base
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = RiskEvaluationEngine()
    test_db_engine = create_engine("sqlite:///:memory:")
    import app.models
    Base.metadata.create_all(bind=test_db_engine)
    Session = sessionmaker(bind=test_db_engine)
    db = Session()

    # Case A: Insufficient Data (< 3 observations)
    req_sparse = RiskEvaluationRequest(
        supplier_id="sup-sparse",
        supplier_name="New Supplier Co",
        delivery_records=[DeliveryObservation(was_delayed=False, lateness_days=0, fulfillment_rate=1.0)],
        quality_records=[],
    )
    res_sparse = engine.evaluate_supplier(req_sparse, "org-test", db)
    assert res_sparse.risk_category == "INSUFFICIENT_DATA"
    assert res_sparse.data_sufficiency == "INSUFFICIENT_DATA"
    assert res_sparse.risk_score is None

    # Case B: Sufficient Data (4 delivery records, 2 quality inspections)
    req_rich = RiskEvaluationRequest(
        supplier_id="sup-rich",
        supplier_name="Established Vendor Ltd",
        delivery_records=[
            DeliveryObservation(was_delayed=False, lateness_days=0, fulfillment_rate=1.0),
            DeliveryObservation(was_delayed=True, lateness_days=4, fulfillment_rate=1.0),
            DeliveryObservation(was_delayed=False, lateness_days=0, fulfillment_rate=1.0),
            DeliveryObservation(was_delayed=False, lateness_days=0, fulfillment_rate=0.9),
        ],
        quality_records=[
            QualityObservation(defect_rate=0.01, severity="LOW"),
            QualityObservation(defect_rate=0.03, severity="MEDIUM"),
        ],
    )
    res_rich = engine.evaluate_supplier(req_rich, "org-test", db)
    assert res_rich.data_sufficiency == "SUFFICIENT"
    assert res_rich.risk_score is not None
    assert res_rich.risk_category in ["LOW", "MEDIUM"]
    assert res_rich.confidence >= 0.70


# 2. Test Multi-Criteria Decision Analysis Optimization Engine
def test_mcda_optimizer_mathematics():
    clear_app_modules()
    sys.path.insert(0, str(WORKSPACE_DIR / "services" / "optimization-service"))
    from app.services.optimizer_engine import MultiCriteriaOptimizerEngine
    from app.schemas.optimization import (
        OptimizationRequest,
        QuotationCandidate,
        MandatoryConstraints,
        CriteriaWeights,
    )
    from app.db.base import Base
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    optimizer = MultiCriteriaOptimizerEngine()
    test_db_engine = create_engine("sqlite:///:memory:")
    import app.models
    Base.metadata.create_all(bind=test_db_engine)
    Session = sessionmaker(bind=test_db_engine)
    db = Session()

    req = OptimizationRequest(
        request_id="pr-stage-4-e2e",
        budget_limit=1000000.0,
        currency="LKR",
        constraints=MandatoryConstraints(
            max_budget=1000000.0,
            max_lead_time_days=20,
            disallow_critical_risk=True,
        ),
        weights=CriteriaWeights(
            cost_weight=0.40,
            delivery_weight=0.25,
            quality_weight=0.20,
            reliability_weight=0.15,
        ),
        candidates=[
            # Candidate 1: Balanced Winner (medium cost, fast delivery, high quality, low risk)
            QuotationCandidate(
                quotation_id="quo-1",
                supplier_id="sup-1",
                supplier_name="Colombo Precision Tools",
                total_cost=800000.0,
                lead_time_days=7,
                quality_score=0.92,
                risk_score=0.15,
                risk_category="LOW",
                compliance_passed=True,
            ),
            # Candidate 2: Cheap but slow and medium risk
            QuotationCandidate(
                quotation_id="quo-2",
                supplier_id="sup-2",
                supplier_name="Economy Spares Co",
                total_cost=700000.0,
                lead_time_days=18,
                quality_score=0.78,
                risk_score=0.35,
                risk_category="MEDIUM",
                compliance_passed=True,
            ),
            # Candidate 3: Ineligible (Over Budget)
            QuotationCandidate(
                quotation_id="quo-3",
                supplier_id="sup-3",
                supplier_name="Ultra High-End Imports",
                total_cost=1200000.0,  # Exceeds 1M
                lead_time_days=5,
                quality_score=0.99,
                risk_score=0.05,
                risk_category="LOW",
                compliance_passed=True,
            ),
        ],
    )

    res = optimizer.optimize_and_rank(req, "org-test", db)
    assert res.total_evaluated == 3
    assert res.eligible_count == 2
    assert res.rejected_count == 1

    # Verify Rank 1 Winner
    rank_1 = next(r for r in res.rankings if r.rank == 1)
    assert rank_1.is_eligible is True
    assert rank_1.composite_score > 0.0

    # Verify Disqualified Candidate
    disqualified = next(r for r in res.rankings if not r.is_eligible)
    assert disqualified.supplier_id == "sup-3"
    assert any("Exceeds budgetary ceiling" in r for r in disqualified.rejection_reasons)


# 3. Test Machine Learning Pipeline Inference Interface
def test_ml_risk_pipeline_interface():
    clear_app_modules()
    sys.path.insert(0, str(WORKSPACE_DIR / "services" / "risk-service"))
    from app.ml.predictive_pipeline import ml_risk_pipeline

    status = ml_risk_pipeline.get_model_status()
    assert status["is_trained"] is True
    assert "metrics" in status
    assert len(status["limitations"]) > 0

    # Predict risk for high delays
    prob_high, tier_high = ml_risk_pipeline.predict_risk_probability(
        delay_freq=0.8,
        avg_lateness=12.0,
        fulfillment_deficit=0.4,
        defect_rate=0.25,
    )
    assert prob_high > 0.60
    assert tier_high in ["HIGH", "CRITICAL"]

    # Predict risk for clean record
    prob_low, tier_low = ml_risk_pipeline.predict_risk_probability(
        delay_freq=0.0,
        avg_lateness=0.0,
        fulfillment_deficit=0.0,
        defect_rate=0.0,
    )
    assert prob_low < 0.25
    assert tier_low == "LOW"
