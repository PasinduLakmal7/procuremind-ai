import json
import uuid
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.risk_assessments import RiskAssessmentRecord
from app.schemas.risk import RiskEvaluationRequest, RiskEvaluationResponse


class RiskEvaluationEngine:
    MIN_OBSERVATIONS_THRESHOLD = 3
    VERSION = "rule-baseline-v1.0"

    def evaluate_supplier(
        self,
        request: RiskEvaluationRequest,
        organization_id: str,
        db: Session,
    ) -> RiskEvaluationResponse:
        total_deliveries = len(request.delivery_records)
        total_quality = len(request.quality_records)
        total_observations = total_deliveries + total_quality

        # Task 2 Requirement: If insufficient historical data exists, return INSUFFICIENT_DATA.
        # Do not generate unsupported numerical risk probabilities.
        if total_observations < self.MIN_OBSERVATIONS_THRESHOLD:
            assessment_id = str(uuid.uuid4())
            breakdown = {
                "total_deliveries": total_deliveries,
                "total_quality_inspections": total_quality,
                "total_observations": total_observations,
                "minimum_required": self.MIN_OBSERVATIONS_THRESHOLD,
                "delay_frequency": None,
                "average_lateness_days": None,
                "fulfillment_rate": None,
                "average_defect_rate": None,
                "critical_incident_count": 0,
            }
            explanation = (
                f"Insufficient historical data: Only {total_observations} record(s) found for supplier "
                f"'{request.supplier_name}', below the minimum required threshold of {self.MIN_OBSERVATIONS_THRESHOLD}. "
                "Deterministic baseline policy dictates 'INSUFFICIENT_DATA' rather than generating unverified probabilistic scores."
            )

            record = RiskAssessmentRecord(
                id=assessment_id,
                organization_id=organization_id,
                supplier_id=request.supplier_id,
                supplier_name=request.supplier_name,
                risk_score=None,
                risk_category="INSUFFICIENT_DATA",
                confidence=0.25,
                data_sufficiency="INSUFFICIENT_DATA",
                observation_count=total_observations,
                metrics_breakdown=json.dumps(breakdown),
                observations=json.dumps({
                    "deliveries": [d.model_dump() for d in request.delivery_records],
                    "quality": [q.model_dump() for q in request.quality_records],
                }),
                model_version=self.VERSION,
                explanation=explanation,
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            return RiskEvaluationResponse(
                assessment_id=record.id,
                supplier_id=record.supplier_id,
                supplier_name=record.supplier_name,
                risk_score=None,
                risk_category=record.risk_category,
                confidence=record.confidence,
                data_sufficiency=record.data_sufficiency,
                observation_count=record.observation_count,
                metrics_breakdown=breakdown,
                explanation=record.explanation,
                model_version=record.model_version,
                created_at=record.created_at,
            )

        # Sufficient data exists -> Compute deterministic metric scores
        late_deliveries = [d for d in request.delivery_records if d.was_delayed or d.lateness_days > 0]
        late_count = len(late_deliveries)
        delay_frequency = late_count / total_deliveries if total_deliveries > 0 else 0.0

        total_lateness_days = sum(d.lateness_days for d in late_deliveries)
        avg_lateness_days = (total_lateness_days / late_count) if late_count > 0 else 0.0
        lateness_factor = min(1.0, avg_lateness_days / 14.0)

        mean_fulfillment = (
            sum(d.fulfillment_rate for d in request.delivery_records) / total_deliveries
            if total_deliveries > 0 else 1.0
        )
        fulfillment_failure = max(0.0, 1.0 - mean_fulfillment)

        mean_defect_rate = (
            sum(q.defect_rate for q in request.quality_records) / total_quality
            if total_quality > 0 else 0.0
        )

        critical_incidents = sum(
            1 for q in request.quality_records if q.severity.upper() in ["HIGH", "CRITICAL"]
        )
        critical_penalty = min(1.0, critical_incidents * 0.25)

        # Baseline Formula:
        # 30% Delay Frequency + 20% Lateness Factor + 20% Fulfillment Failure + 20% Defect Rate + 10% Critical Incidents
        raw_score = (
            0.30 * delay_frequency
            + 0.20 * lateness_factor
            + 0.20 * fulfillment_failure
            + 0.20 * mean_defect_rate
            + 0.10 * critical_penalty
        )
        risk_score = round(min(1.0, max(0.0, raw_score)), 4)

        if risk_score < 0.20:
            category = "LOW"
        elif risk_score < 0.45:
            category = "MEDIUM"
        elif risk_score < 0.70:
            category = "HIGH"
        else:
            category = "CRITICAL"

        confidence = round(min(0.95, 0.50 + 0.05 * total_observations), 2)

        breakdown = {
            "total_deliveries": total_deliveries,
            "late_deliveries_count": late_count,
            "delay_frequency": round(delay_frequency, 4),
            "average_lateness_days": round(avg_lateness_days, 1),
            "lateness_factor": round(lateness_factor, 4),
            "mean_fulfillment_rate": round(mean_fulfillment, 4),
            "fulfillment_failure_rate": round(fulfillment_failure, 4),
            "total_quality_inspections": total_quality,
            "mean_defect_rate": round(mean_defect_rate, 4),
            "critical_incident_count": critical_incidents,
            "critical_incident_penalty": round(critical_penalty, 4),
            "composite_score": risk_score,
        }

        explanation = (
            f"Risk Tier '{category}' (Score: {risk_score:.4f}, Confidence: {confidence:.2f}) evaluated across "
            f"{total_observations} observations ({total_deliveries} orders, {total_quality} inspections). "
            f"Delay frequency: {delay_frequency * 100:.1f}%, average lateness: {avg_lateness_days:.1f} days, "
            f"fulfillment rate: {mean_fulfillment * 100:.1f}%, mean defect rate: {mean_defect_rate * 100:.1f}%, "
            f"critical incidents: {critical_incidents}."
        )

        assessment_id = str(uuid.uuid4())
        record = RiskAssessmentRecord(
            id=assessment_id,
            organization_id=organization_id,
            supplier_id=request.supplier_id,
            supplier_name=request.supplier_name,
            risk_score=risk_score,
            risk_category=category,
            confidence=confidence,
            data_sufficiency="SUFFICIENT",
            observation_count=total_observations,
            metrics_breakdown=json.dumps(breakdown),
            observations=json.dumps({
                "deliveries": [d.model_dump() for d in request.delivery_records],
                "quality": [q.model_dump() for q in request.quality_records],
            }),
            model_version=self.VERSION,
            explanation=explanation,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return RiskEvaluationResponse(
            assessment_id=record.id,
            supplier_id=record.supplier_id,
            supplier_name=record.supplier_name,
            risk_score=record.risk_score,
            risk_category=record.risk_category,
            confidence=record.confidence,
            data_sufficiency=record.data_sufficiency,
            observation_count=record.observation_count,
            metrics_breakdown=breakdown,
            explanation=record.explanation,
            model_version=record.model_version,
            created_at=record.created_at,
        )

