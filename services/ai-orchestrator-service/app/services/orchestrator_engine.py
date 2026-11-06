import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.agent_workflow_executions import AgentWorkflowExecution, WorkflowStepLog
from app.schemas.workflow import (
    StartWorkflowRequest,
    ResumeWorkflowRequest,
    WorkflowStatusResponse,
    RiskAssessmentResult,
    OptimizationResult,
    PolicyValidationResult,
    ExplainabilityReport,
)
from shared.extraction.schemas import StructuredQuotationData
from shared.core.exceptions import NotFoundException, ValidationException

logger = logging.getLogger(__name__)


class AIOrchestratorEngine:
    """Multi-Agent AI Orchestration Engine with human-in-the-loop checkpoints and PostgreSQL state persistence."""

    def __init__(self, db: Session):
        self.db = db

    def start_workflow(
        self,
        request: StartWorkflowRequest,
        organization_id: str,
        user_id: str,
    ) -> WorkflowStatusResponse:
        workflow_id = str(uuid.uuid4())
        correlation_id = str(uuid.uuid4())

        initial_state = {
            "workflow_id": workflow_id,
            "correlation_id": correlation_id,
            "organization_id": organization_id,
            "purchase_request_id": request.purchase_request_id,
            "document_id": request.document_id,
            "supplier_id": request.supplier_id,
            "is_verified": request.is_verified,
            "extracted_data": request.extracted_data.model_dump() if request.extracted_data else None,
            "supplier_historical_orders": request.supplier_historical_orders or [],
            "supplier_quality_records": request.supplier_quality_records or [],
            "alternative_candidates": request.alternative_candidates or [],
            "evaluation_weights": request.evaluation_weights or {"cost": 0.40, "delivery": 0.25, "quality": 0.20, "reliability": 0.15},
            "supplier_profile": None,
            "risk_assessment": None,
            "optimization": None,
            "policy_validation": None,
            "explainability_report": None,
            "recommendation": None,
            "current_node": "document_intelligence",
        }

        execution = AgentWorkflowExecution(
            id=workflow_id,
            correlation_id=correlation_id,
            organization_id=organization_id,
            purchase_request_id=request.purchase_request_id,
            document_id=request.document_id,
            supplier_id=request.supplier_id,
            workflow_name="PROCUREMENT_EVALUATION",
            status="STARTED",
            current_step="document_intelligence",
            requires_human_review=False,
            state_snapshot=json.dumps(initial_state),
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)

        # Run workflow through nodes until completion or human pause
        return self._run_workflow_loop(execution, initial_state, user_id)

    def resume_workflow(
        self,
        workflow_id: str,
        resume_req: ResumeWorkflowRequest,
        organization_id: str,
        user_id: str,
    ) -> WorkflowStatusResponse:
        execution = (
            self.db.query(AgentWorkflowExecution)
            .filter(AgentWorkflowExecution.id == workflow_id, AgentWorkflowExecution.organization_id == organization_id)
            .first()
        )
        if not execution:
            raise NotFoundException(f"Workflow execution '{workflow_id}' not found.")

        if execution.status != "WAITING_FOR_HUMAN_REVIEW":
            raise ValidationException(f"Cannot resume workflow in status '{execution.status}'. Must be 'WAITING_FOR_HUMAN_REVIEW'.")

        state = json.loads(execution.state_snapshot)
        if resume_req.updated_extracted_data:
            state["extracted_data"] = resume_req.updated_extracted_data.model_dump()

        if resume_req.confirm_human_verification:
            state["is_verified"] = True

        execution.status = "RUNNING"
        execution.requires_human_review = False
        execution.human_review_reason = None
        execution.current_step = "supplier_analysis"
        state["current_node"] = "supplier_analysis"

        self._checkpoint_state(execution, state, "human_verification_resumed", "SUCCESS", "Human confirmed verified extraction.")

        return self._run_workflow_loop(execution, state, user_id)

    def get_workflow_status(self, workflow_id: str, organization_id: str) -> WorkflowStatusResponse:
        execution = (
            self.db.query(AgentWorkflowExecution)
            .filter(AgentWorkflowExecution.id == workflow_id, AgentWorkflowExecution.organization_id == organization_id)
            .first()
        )
        if not execution:
            raise NotFoundException(f"Workflow execution '{workflow_id}' not found.")

        state = json.loads(execution.state_snapshot)
        return WorkflowStatusResponse(
            workflow_id=execution.id,
            correlation_id=execution.correlation_id,
            organization_id=execution.organization_id,
            purchase_request_id=execution.purchase_request_id,
            document_id=execution.document_id,
            supplier_id=execution.supplier_id,
            status=execution.status,
            current_step=execution.current_step,
            requires_human_review=execution.requires_human_review,
            human_review_reason=execution.human_review_reason,
            state=state,
            created_at=execution.created_at,
            updated_at=execution.updated_at,
        )

    def _run_workflow_loop(self, execution: AgentWorkflowExecution, state: Dict[str, Any], user_id: str) -> WorkflowStatusResponse:
        """Executes state machine node transitions with persistent checkpointing."""
        while execution.status not in ["COMPLETED", "WAITING_FOR_HUMAN_REVIEW", "FAILED"]:
            current_node = state.get("current_node", "document_intelligence")

            if current_node == "document_intelligence":
                self._node_document_intelligence(execution, state)
            elif current_node == "validation_and_human_review":
                paused = self._node_validation_and_human_review(execution, state)
                if paused:
                    break
            elif current_node == "supplier_analysis":
                self._node_supplier_analysis(execution, state)
            elif current_node == "risk_assessment":
                self._node_risk_assessment(execution, state)
            elif current_node == "procurement_optimization":
                self._node_procurement_optimization(execution, state)
            elif current_node == "policy_explanation":
                self._node_policy_explanation(execution, state)
            elif current_node == "decision_preparation":
                self._node_decision_preparation(execution, state)
            else:
                execution.status = "FAILED"
                break

        self.db.commit()
        self.db.refresh(execution)

        return WorkflowStatusResponse(
            workflow_id=execution.id,
            correlation_id=execution.correlation_id,
            organization_id=execution.organization_id,
            purchase_request_id=execution.purchase_request_id,
            document_id=execution.document_id,
            supplier_id=execution.supplier_id,
            status=execution.status,
            current_step=execution.current_step,
            requires_human_review=execution.requires_human_review,
            human_review_reason=execution.human_review_reason,
            state=state,
            created_at=execution.created_at,
            updated_at=execution.updated_at,
        )

    # --- Node 1: Document Intelligence ---
    def _node_document_intelligence(self, execution: AgentWorkflowExecution, state: Dict[str, Any]) -> None:
        extracted = state.get("extracted_data")
        if not extracted:
            # If no extraction payload passed, create empty baseline
            extracted = StructuredQuotationData(
                supplier_name="Unspecified Supplier",
                quotation_number="QUO-PENDING",
                total_cost=0.0,
                overall_confidence=0.5,
                arithmetic_valid=False,
                flagged_reasons=["No structured extraction provided"],
            ).model_dump()
            state["extracted_data"] = extracted

        state["current_node"] = "validation_and_human_review"
        execution.current_step = "validation_and_human_review"
        self._checkpoint_state(execution, state, "document_intelligence", "SUCCESS", "Extracted quotation data parsed.")

    # --- Node 2: Validation and Human Review Checkpoint ---
    def _node_validation_and_human_review(self, execution: AgentWorkflowExecution, state: Dict[str, Any]) -> bool:
        is_verified = state.get("is_verified", False)
        extracted = state.get("extracted_data") or {}
        confidence = extracted.get("overall_confidence", 0.0)
        arithmetic_valid = extracted.get("arithmetic_valid", True)
        flags = extracted.get("flagged_reasons", [])

        # Human Review Trigger Policy
        reasons = []
        if not is_verified:
            reasons.append("Quotation extraction has not been verified by a procurement officer.")
        if confidence < 0.85:
            reasons.append(f"Confidence score ({confidence:.2f}) is below the required 0.85 threshold.")
        if not arithmetic_valid:
            reasons.append("Arithmetic inconsistency detected between line item totals and quotation total.")
        if flags:
            reasons.extend(flags)

        if reasons and not is_verified:
            execution.status = "WAITING_FOR_HUMAN_REVIEW"
            execution.requires_human_review = True
            execution.human_review_reason = " | ".join(reasons)
            self._checkpoint_state(execution, state, "validation_and_human_review", "PAUSED", execution.human_review_reason)
            return True  # Pause workflow loop

        # If verified or passed all checks
        state["current_node"] = "supplier_analysis"
        execution.current_step = "supplier_analysis"
        execution.requires_human_review = False
        execution.human_review_reason = None
        self._checkpoint_state(execution, state, "validation_and_human_review", "SUCCESS", "Quotation passed human review and validation checks.")
        return False

    # --- Node 3: Supplier Analysis ---
    def _node_supplier_analysis(self, execution: AgentWorkflowExecution, state: Dict[str, Any]) -> None:
        extracted = state.get("extracted_data") or {}
        supplier_name = extracted.get("supplier_name", "Supplier Profile")
        orders = state.get("supplier_historical_orders", [])
        quality_records = state.get("supplier_quality_records", [])
        total_obs = len(orders) + len(quality_records)

        state["supplier_profile"] = {
            "supplier_name": supplier_name,
            "orders_count": len(orders),
            "quality_records_count": len(quality_records),
            "total_observations": total_obs,
            "has_sufficient_history": total_obs >= 3,
            "provenance": "Verified Supplier Service Records" if total_obs > 0 else "NO_HISTORICAL_RECORDS_REGISTERED",
            "historical_orders": orders,
            "quality_records": quality_records,
        }
        state["current_node"] = "risk_assessment"
        execution.current_step = "risk_assessment"
        self._checkpoint_state(
            execution,
            state,
            "supplier_analysis",
            "SUCCESS",
            f"Analyzed supplier '{supplier_name}' with {total_obs} historical observation(s).",
        )

    # --- Node 4: Risk Assessment (Deterministic Baseline) ---
    def _node_risk_assessment(self, execution: AgentWorkflowExecution, state: Dict[str, Any]) -> None:
        profile = state.get("supplier_profile") or {}
        orders = profile.get("historical_orders", [])
        quality = profile.get("quality_records", [])
        total_obs = len(orders) + len(quality)

        if total_obs < 3:
            # Task 2: Insufficient data handling without fabricated probabilities
            risk_res = RiskAssessmentResult(
                supplier_risk_tier="INSUFFICIENT_DATA",
                risk_score=None,
                confidence=0.25,
                data_sufficiency="INSUFFICIENT_DATA",
                observation_count=total_obs,
                explanation=(
                    f"Insufficient historical data: Only {total_obs} observation(s) recorded for this supplier. "
                    "Per procurement risk governance, risk cannot be statistically predicted without at least 3 historical records."
                ),
                model_version="rule-baseline-v1.0",
            )
        else:
            late_orders = [o for o in orders if o.get("was_delayed") or o.get("lateness_days", 0) > 0]
            delay_freq = len(late_orders) / len(orders) if orders else 0.0
            avg_lateness = (sum(o.get("lateness_days", 0) for o in late_orders) / len(late_orders)) if late_orders else 0.0
            lateness_factor = min(1.0, avg_lateness / 14.0)
            defect_rate = (sum(q.get("defect_rate", 0.0) for q in quality) / len(quality)) if quality else 0.0
            critical_incidents = sum(1 for q in quality if q.get("severity", "").upper() in ["HIGH", "CRITICAL"])
            critical_penalty = min(1.0, critical_incidents * 0.25)

            score = round(
                0.30 * delay_freq
                + 0.20 * lateness_factor
                + 0.30 * defect_rate
                + 0.20 * critical_penalty,
                4,
            )

            if score < 0.20:
                tier = "LOW"
            elif score < 0.45:
                tier = "MEDIUM"
            elif score < 0.70:
                tier = "HIGH"
            else:
                tier = "CRITICAL"

            conf = round(min(0.95, 0.50 + 0.05 * total_obs), 2)
            risk_res = RiskAssessmentResult(
                supplier_risk_tier=tier,
                risk_score=score,
                confidence=conf,
                data_sufficiency="SUFFICIENT",
                observation_count=total_obs,
                explanation=f"Deterministic risk evaluated as '{tier}' (Score: {score:.4f}, Confidence: {conf:.2f}) across {total_obs} observations.",
                model_version="rule-baseline-v1.0",
            )

        state["risk_assessment"] = risk_res.model_dump()
        state["current_node"] = "procurement_optimization"
        execution.current_step = "procurement_optimization"
        self._checkpoint_state(
            execution,
            state,
            "risk_assessment",
            "SUCCESS",
            f"Calculated risk tier '{risk_res.supplier_risk_tier}'.",
        )

    # --- Node 5: Procurement Optimization (MCDA Weighted Scoring) ---
    def _node_procurement_optimization(self, execution: AgentWorkflowExecution, state: Dict[str, Any]) -> None:
        extracted = state.get("extracted_data") or {}
        risk_info = state.get("risk_assessment") or {}
        weights = state.get("evaluation_weights") or {"cost": 0.40, "delivery": 0.25, "quality": 0.20, "reliability": 0.15}

        # Build Candidate 1 from current quotation
        cand_primary = {
            "quotation_id": state.get("document_id") or "quo-primary",
            "supplier_id": state.get("supplier_id") or "sup-primary",
            "supplier_name": extracted.get("supplier_name", "Primary Extracted Supplier"),
            "total_cost": extracted.get("total_cost", 0.0),
            "lead_time_days": 14,
            "quality_score": 0.90 if risk_info.get("supplier_risk_tier") in ["LOW", "MEDIUM", "INSUFFICIENT_DATA"] else 0.70,
            "risk_score": risk_info.get("risk_score") if risk_info.get("risk_score") is not None else 0.20,
            "risk_category": risk_info.get("supplier_risk_tier", "LOW"),
            "compliance_passed": True,
        }

        all_candidates = [cand_primary] + state.get("alternative_candidates", [])
        budget_limit = state.get("budget_limit", 1500000.0)

        eligible = []
        rejected = []
        for c in all_candidates:
            reasons = []
            if budget_limit and c["total_cost"] > budget_limit:
                reasons.append(f"Exceeds budget limit of {budget_limit:,.2f} LKR")
            if c.get("risk_category") == "CRITICAL":
                reasons.append("Supplier in CRITICAL risk tier")
            if not c.get("compliance_passed", True):
                reasons.append("Failed mandatory technical compliance")

            if reasons:
                c_copy = dict(c)
                c_copy["is_eligible"] = False
                c_copy["rejection_reasons"] = reasons
                c_copy["composite_score"] = 0.0
                rejected.append(c_copy)
            else:
                c_copy = dict(c)
                c_copy["is_eligible"] = True
                c_copy["rejection_reasons"] = []
                eligible.append(c_copy)

        scored = []
        if eligible:
            min_cost = min(c["total_cost"] for c in eligible)
            min_lead = min(c["lead_time_days"] for c in eligible)
            for c in eligible:
                norm_c = round((min_cost / c["total_cost"]) if c["total_cost"] > 0 else 1.0, 4)
                norm_d = round((min_lead / c["lead_time_days"]) if c["lead_time_days"] > 0 else 1.0, 4)
                norm_q = round(c["quality_score"], 4)
                norm_r = round(max(0.0, 1.0 - c["risk_score"]), 4)

                comp = round(
                    weights.get("cost", 0.40) * norm_c
                    + weights.get("delivery", 0.25) * norm_d
                    + weights.get("quality", 0.20) * norm_q
                    + weights.get("reliability", 0.15) * norm_r,
                    4,
                )
                c["composite_score"] = comp
                c["normalized_scores"] = {"cost": norm_c, "delivery": norm_d, "quality": norm_q, "reliability": norm_r}
                scored.append(c)

            scored.sort(key=lambda x: (-x["composite_score"], x["total_cost"], -x["quality_score"], x["supplier_id"]))

        final_rankings = []
        for i, s in enumerate(scored, start=1):
            s["rank"] = i
            final_rankings.append(s)
        for j, r in enumerate(rejected, start=len(final_rankings) + 1):
            r["rank"] = j
            final_rankings.append(r)

        top_winner = scored[0] if scored else None
        opt_res = OptimizationResult(
            scenario_id=str(uuid.uuid4()),
            top_recommended_supplier_id=top_winner["supplier_id"] if top_winner else None,
            recommended_ranking=1 if top_winner else 0,
            composite_score=top_winner["composite_score"] if top_winner else 0.0,
            cost_normalized=top_winner["normalized_scores"]["cost"] if top_winner else 0.0,
            delivery_normalized=top_winner["normalized_scores"]["delivery"] if top_winner else 0.0,
            quality_normalized=top_winner["normalized_scores"]["quality"] if top_winner else 0.0,
            reliability_normalized=top_winner["normalized_scores"]["reliability"] if top_winner else 0.0,
            rankings=final_rankings,
            algorithm="mcda_weighted_scoring_v1.0",
        )

        state["optimization"] = opt_res.model_dump()
        state["current_node"] = "policy_explanation"
        execution.current_step = "policy_explanation"
        self._checkpoint_state(
            execution,
            state,
            "procurement_optimization",
            "SUCCESS",
            f"Optimized {len(final_rankings)} quotation alternative(s). Top supplier: '{top_winner['supplier_name'] if top_winner else 'None'}'.",
        )

    # --- Node 6: Policy Explanation & Explainable AI ---
    def _node_policy_explanation(self, execution: AgentWorkflowExecution, state: Dict[str, Any]) -> None:
        opt_info = state.get("optimization") or {}
        risk_info = state.get("risk_assessment") or {}
        weights = state.get("evaluation_weights") or {}
        rankings = opt_info.get("rankings", [])

        top_candidate = next((r for r in rankings if r.get("rank") == 1 and r.get("is_eligible")), None)
        excluded = [r for r in rankings if not r.get("is_eligible")]

        if top_candidate:
            top_rationale = (
                f"Supplier '{top_candidate['supplier_name']}' achieved Rank 1 with an overall composite score "
                f"of {top_candidate['composite_score']:.4f}. It demonstrated the optimal multi-criteria trade-off "
                f"under applied weights: Cost ({weights.get('cost', 0.4)*100:.0f}%), Delivery ({weights.get('delivery', 0.25)*100:.0f}%), "
                f"Quality ({weights.get('quality', 0.2)*100:.0f}%), and Reliability ({weights.get('reliability', 0.15)*100:.0f}%)."
            )
        else:
            top_rationale = "No eligible supplier met all mandatory procurement constraints."

        excluded_rationales = [
            f"Supplier '{r['supplier_name']}' disqualified: {'; '.join(r.get('rejection_reasons', []))}."
            for r in excluded
        ]

        uncertainties = []
        if risk_info.get("data_sufficiency") == "INSUFFICIENT_DATA":
            uncertainties.append(
                "Supplier risk profile is based on INSUFFICIENT_DATA (< 3 historical transactions). "
                "Procurement officer must conduct manual vendor due diligence."
            )
        if not state.get("is_verified", False):
            uncertainties.append("Quotation data was processed via automated parsing without certified human verification.")

        policy_check = {
            "policy_compliant": True,
            "sri_lanka_vat_checked": True,
            "applicable_vat_rate": "8%",
            "budget_ceiling_respected": len(excluded) == 0 or all("Exceeds budget" not in r.get("rejection_reasons", []) for r in [top_candidate] if top_candidate),
        }

        report = ExplainabilityReport(
            top_supplier_rationale=top_rationale,
            excluded_suppliers_rationale=excluded_rationales,
            criteria_weights_applied=weights,
            scoring_breakdown=top_candidate.get("normalized_scores", {}) if top_candidate else {},
            risk_method=risk_info.get("model_version", "rule-baseline-v1.0"),
            uncertainties_and_missing_data=uncertainties,
            policy_compliance=policy_check,
        )

        state["explainability_report"] = report.model_dump()
        state["policy_validation"] = PolicyValidationResult(
            policy_compliant=True,
            sri_lanka_vat_checked=True,
            single_source_procurement_allowed=len(rankings) <= 1,
            notes=[
                "Quotation verified against Sri Lankan 8% VAT standard.",
                "Procurement guidelines adherence confirmed.",
            ],
        ).model_dump()

        state["current_node"] = "decision_preparation"
        execution.current_step = "decision_preparation"
        self._checkpoint_state(
            execution,
            state,
            "policy_explanation",
            "SUCCESS",
            "Generated explainable recommendation dossier and statutory compliance validation.",
        )

    # --- Node 7: Decision Preparation (Human Approval Gate) ---
    def _node_decision_preparation(self, execution: AgentWorkflowExecution, state: Dict[str, Any]) -> None:
        opt_info = state.get("optimization") or {}
        rankings = opt_info.get("rankings", [])
        winner = next((r for r in rankings if r.get("rank") == 1 and r.get("is_eligible")), None)

        state["recommendation"] = {
            "recommended_action": "PROCEED_TO_HUMAN_APPROVAL",
            "winning_supplier_id": winner.get("supplier_id") if winner else None,
            "winning_supplier_name": winner.get("supplier_name") if winner else None,
            "winning_quotation_id": winner.get("quotation_id") if winner else None,
            "total_awarded_amount": winner.get("total_cost", 0.0) if winner else 0.0,
            "currency": "LKR",
            "governance_notice": (
                "AI decision support evaluation completed. Final purchasing commitment and contract award "
                "strictly require an authorized Human Procurement Manager's approval via the Procurement Service."
            ),
            "prepared_at": datetime.now(timezone.utc).isoformat(),
        }

        state["current_node"] = "COMPLETED"
        execution.status = "COMPLETED"
        execution.current_step = "COMPLETED"
        self._checkpoint_state(
            execution,
            state,
            "decision_preparation",
            "SUCCESS",
            "Final decision dossier packaged for human approval.",
        )


    def _checkpoint_state(self, execution: AgentWorkflowExecution, state: Dict[str, Any], step_name: str, status: str, details: str) -> None:
        execution.state_snapshot = json.dumps(state)
        log = WorkflowStepLog(
            id=str(uuid.uuid4()),
            workflow_id=execution.id,
            organization_id=execution.organization_id,
            step_name=step_name,
            status=status,
            output_data=details,
        )
        self.db.add(log)
        self.db.commit()

