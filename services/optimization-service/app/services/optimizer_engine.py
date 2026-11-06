import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.optimization_scenarios import OptimizationScenario
from app.schemas.optimization import (
    OptimizationRequest,
    OptimizationResponse,
    RankedSupplier,
    QuotationCandidate,
    CriteriaWeights,
)


class MultiCriteriaOptimizerEngine:
    ALGORITHM = "mcda_weighted_scoring_v1.0"

    def optimize_and_rank(
        self,
        request: OptimizationRequest,
        organization_id: str,
        db: Session,
    ) -> OptimizationResponse:
        weights = request.weights or CriteriaWeights()
        constraints = request.constraints

        # Effective constraints
        max_budget = constraints.max_budget if (constraints and constraints.max_budget is not None) else request.budget_limit
        max_lead_time = constraints.max_lead_time_days if constraints else None
        disallow_critical = constraints.disallow_critical_risk if constraints else True

        eligible_candidates: List[QuotationCandidate] = []
        rejected_candidates: List[RankedSupplier] = []

        # Step 1: Mandatory Constraint Filtering
        for cand in request.candidates:
            reasons = []
            if max_budget is not None and max_budget > 0 and cand.total_cost > max_budget:
                reasons.append(
                    f"Exceeds budgetary ceiling of {max_budget:,.2f} {cand.currency} (Quoted: {cand.total_cost:,.2f} {cand.currency})"
                )
            if max_lead_time is not None and cand.lead_time_days > max_lead_time:
                reasons.append(
                    f"Exceeds maximum allowable lead time of {max_lead_time} days (Quoted: {cand.lead_time_days} days)"
                )
            if not cand.compliance_passed:
                reasons.append("Failed statutory compliance or mandatory technical specifications")
            if disallow_critical and cand.risk_category.upper() == "CRITICAL":
                reasons.append(f"Supplier is in CRITICAL risk tier (Risk Score: {cand.risk_score:.2f})")

            if reasons:
                rejected_candidates.append(
                    RankedSupplier(
                        rank=0,  # Will be indexed at bottom
                        supplier_id=cand.supplier_id,
                        supplier_name=cand.supplier_name,
                        quotation_id=cand.quotation_id,
                        total_cost=cand.total_cost,
                        lead_time_days=cand.lead_time_days,
                        is_eligible=False,
                        rejection_reasons=reasons,
                        composite_score=0.0,
                        normalized_scores={"cost": 0.0, "delivery": 0.0, "quality": 0.0, "reliability": 0.0},
                        explanation=f"Disqualified due to mandatory constraints: {'; '.join(reasons)}.",
                    )
                )
            else:
                eligible_candidates.append(cand)

        # Step 2: Multi-Criteria Scoring for Eligible Candidates
        scored_eligible: List[RankedSupplier] = []
        if eligible_candidates:
            min_cost = min(c.total_cost for c in eligible_candidates)
            min_lead_time = min(c.lead_time_days for c in eligible_candidates)

            for cand in eligible_candidates:
                # Normalization formulas:
                # Cost: lower is better -> min_cost / cost
                norm_cost = round((min_cost / cand.total_cost) if cand.total_cost > 0 else 1.0, 4)

                # Delivery lead time: lower is better -> min_lead_time / lead_time
                norm_delivery = round((min_lead_time / cand.lead_time_days) if cand.lead_time_days > 0 else 1.0, 4)

                # Quality: higher is better -> direct scale (0.0 to 1.0)
                norm_quality = round(min(1.0, max(0.0, cand.quality_score)), 4)

                # Reliability: higher is better -> (1.0 - risk_score)
                norm_reliability = round(min(1.0, max(0.0, 1.0 - cand.risk_score)), 4)

                composite = round(
                    weights.cost_weight * norm_cost
                    + weights.delivery_weight * norm_delivery
                    + weights.quality_weight * norm_quality
                    + weights.reliability_weight * norm_reliability,
                    4,
                )

                norm_scores = {
                    "cost": norm_cost,
                    "delivery": norm_delivery,
                    "quality": norm_quality,
                    "reliability": norm_reliability,
                }

                explanation = (
                    f"Composite score: {composite:.4f}. Factors: Cost ({weights.cost_weight * 100:.0f}% wt) normalized to {norm_cost:.2f}; "
                    f"Delivery ({weights.delivery_weight * 100:.0f}% wt) normalized to {norm_delivery:.2f}; "
                    f"Quality ({weights.quality_weight * 100:.0f}% wt) score {norm_quality:.2f}; "
                    f"Reliability ({weights.reliability_weight * 100:.0f}% wt) score {norm_reliability:.2f}."
                )

                scored_eligible.append(
                    RankedSupplier(
                        rank=0,
                        supplier_id=cand.supplier_id,
                        supplier_name=cand.supplier_name,
                        quotation_id=cand.quotation_id,
                        total_cost=cand.total_cost,
                        lead_time_days=cand.lead_time_days,
                        is_eligible=True,
                        rejection_reasons=[],
                        composite_score=composite,
                        normalized_scores=norm_scores,
                        explanation=explanation,
                    )
                )

            # Step 3: Deterministic Sorting & Tie-Breaking
            # 1. Composite score descending
            # 2. Total cost ascending (cheaper is better)
            # 3. Quality score descending
            # 4. Supplier ID alphabetical
            scored_eligible.sort(
                key=lambda s: (
                    -s.composite_score,
                    s.total_cost,
                    -s.normalized_scores["quality"],
                    s.supplier_id,
                )
            )

        # Assign 1-based ranks
        rankings: List[RankedSupplier] = []
        for i, s in enumerate(scored_eligible, start=1):
            s.rank = i
            rankings.append(s)

        # Append ineligible candidates at bottom
        for j, r in enumerate(rejected_candidates, start=len(rankings) + 1):
            r.rank = j
            rankings.append(r)

        top_winner = scored_eligible[0] if scored_eligible else None
        top_supplier_id = top_winner.supplier_id if top_winner else None
        top_supplier_name = top_winner.supplier_name if top_winner else None

        if top_winner:
            decision_summary = (
                f"Recommended Supplier: '{top_winner.supplier_name}' (Quotation: {top_winner.quotation_id}) "
                f"achieved Rank 1 with composite score of {top_winner.composite_score:.4f} across cost, delivery, quality, and reliability. "
                f"Total candidates evaluated: {len(request.candidates)} ({len(scored_eligible)} eligible, {len(rejected_candidates)} disqualified)."
            )
        else:
            decision_summary = (
                f"No eligible suppliers found. All {len(request.candidates)} candidate(s) failed mandatory "
                "budgetary, delivery lead time, or risk constraints."
            )

        scenario_id = str(uuid.uuid4())
        weights_dict = weights.model_dump()
        rankings_dump = [r.model_dump() for r in rankings]

        scenario = OptimizationScenario(
            id=scenario_id,
            organization_id=organization_id,
            request_id=request.request_id,
            algorithm=self.ALGORITHM,
            total_evaluated=len(request.candidates),
            top_supplier_id=top_supplier_id,
            weights_json=json.dumps(weights_dict),
            rankings_json=json.dumps(rankings_dump),
            decision_summary=decision_summary,
        )
        db.add(scenario)
        db.commit()
        db.refresh(scenario)

        return OptimizationResponse(
            scenario_id=scenario.id,
            request_id=scenario.request_id,
            algorithm=scenario.algorithm,
            total_evaluated=len(request.candidates),
            eligible_count=len(scored_eligible),
            rejected_count=len(rejected_candidates),
            top_recommended_supplier_id=top_supplier_id,
            top_recommended_supplier_name=top_supplier_name,
            rankings=rankings,
            weights_used=weights_dict,
            decision_summary=decision_summary,
            created_at=scenario.created_at,
        )

