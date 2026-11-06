import json
from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.procurement_repository import ProcurementRepository
from app.models.purchase_requests import PurchaseRequest
from app.schemas.purchase_request import (
    PurchaseRequestCreate,
    PurchaseRequestUpdate,
    PurchaseRequestResponse,
    PurchaseRequestDetailResponse,
    PurchaseRequestStatusUpdate,
    PurchaseRequestItemCreate,
    PurchaseRequestItemResponse,
    CandidateSupplierCreate,
    CandidateSupplierResponse,
    ProcurementAuditEventResponse,
    PurchaseRequestDecision,
)
from app.schemas.quotation import (
    QuotationCreate,
    QuotationResponse,
    QuotationItemResponse,
)
from shared.core.exceptions import NotFoundException, ValidationException, BadRequestException


VALID_TRANSITIONS = {
    "DRAFT": {"SUBMITTED", "CANCELLED"},
    "SUBMITTED": {"UNDER_EVALUATION", "CANCELLED"},
    "UNDER_EVALUATION": {"APPROVED", "REJECTED", "CANCELLED"},
    "APPROVED": set(),
    "REJECTED": set(),
    "CANCELLED": set(),
}


class ProcurementService:
    def __init__(self, db: Session):
        self.repo = ProcurementRepository(db)

    def _to_pr_response(self, pr: PurchaseRequest) -> PurchaseRequestResponse:
        items = [PurchaseRequestItemResponse.model_validate(it) for it in pr.items]
        return PurchaseRequestResponse(
            id=pr.id,
            organization_id=pr.organization_id,
            created_by_user_id=pr.created_by_user_id,
            request_number=pr.request_number,
            title=pr.title,
            description=pr.description,
            category=pr.category,
            priority=pr.priority,
            budget_limit=pr.budget_limit,
            currency=pr.currency,
            required_delivery_date=pr.required_delivery_date,
            evaluation_criteria=pr.evaluation_criteria,
            status=pr.status,
            items=items,
            created_at=pr.created_at,
            updated_at=pr.updated_at,
        )

    def _to_pr_detail_response(self, pr: PurchaseRequest) -> PurchaseRequestDetailResponse:
        items = [PurchaseRequestItemResponse.model_validate(it) for it in pr.items]
        candidates = [CandidateSupplierResponse.model_validate(c) for c in pr.candidate_suppliers]
        audits = [ProcurementAuditEventResponse.model_validate(a) for a in pr.audit_events]
        return PurchaseRequestDetailResponse(
            id=pr.id,
            organization_id=pr.organization_id,
            created_by_user_id=pr.created_by_user_id,
            request_number=pr.request_number,
            title=pr.title,
            description=pr.description,
            category=pr.category,
            priority=pr.priority,
            budget_limit=pr.budget_limit,
            currency=pr.currency,
            required_delivery_date=pr.required_delivery_date,
            evaluation_criteria=pr.evaluation_criteria,
            status=pr.status,
            items=items,
            candidate_suppliers=candidates,
            audit_events=audits,
            created_at=pr.created_at,
            updated_at=pr.updated_at,
        )

    def create_request(self, data: PurchaseRequestCreate, organization_id: str, user_id: str) -> PurchaseRequestResponse:
        pr = self.repo.create_request(data, organization_id=organization_id, user_id=user_id)
        return self._to_pr_response(pr)

    def get_request(self, pr_id: str, organization_id: str) -> PurchaseRequestResponse:
        pr = self.repo.get_request_by_id(pr_id, organization_id)
        if not pr:
            raise NotFoundException(f"Purchase request '{pr_id}' not found.")
        return self._to_pr_response(pr)

    def get_request_detail(self, pr_id: str, organization_id: str) -> PurchaseRequestDetailResponse:
        pr = self.repo.get_request_by_id(pr_id, organization_id)
        if not pr:
            raise NotFoundException(f"Purchase request '{pr_id}' not found.")
        return self._to_pr_detail_response(pr)

    def list_requests(
        self,
        organization_id: str,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[PurchaseRequestResponse]:
        prs = self.repo.list_requests(
            organization_id=organization_id,
            status=status,
            category=category,
            priority=priority,
            skip=skip,
            limit=limit,
        )
        return [self._to_pr_response(pr) for pr in prs]

    def update_draft(
        self, pr_id: str, update_in: PurchaseRequestUpdate, organization_id: str, user_id: str
    ) -> PurchaseRequestResponse:
        pr = self.repo.get_request_by_id(pr_id, organization_id)
        if not pr:
            raise NotFoundException(f"Purchase request '{pr_id}' not found.")
        if pr.status != "DRAFT":
            raise ValidationException(f"Cannot edit purchase request in '{pr.status}' status. Only 'DRAFT' can be edited.")
        updated = self.repo.update_request(pr, update_in, user_id)
        return self._to_pr_response(updated)

    def add_item(
        self, pr_id: str, item_in: PurchaseRequestItemCreate, organization_id: str, user_id: str
    ) -> PurchaseRequestItemResponse:
        pr = self.repo.get_request_by_id(pr_id, organization_id)
        if not pr:
            raise NotFoundException(f"Purchase request '{pr_id}' not found.")
        if pr.status != "DRAFT":
            raise ValidationException(f"Cannot add items to purchase request in '{pr.status}' status. Only 'DRAFT' can be modified.")
        item = self.repo.add_item(pr_id, organization_id, item_in, user_id)
        return PurchaseRequestItemResponse.model_validate(item)

    def remove_item(self, pr_id: str, item_id: str, organization_id: str, user_id: str) -> None:
        pr = self.repo.get_request_by_id(pr_id, organization_id)
        if not pr:
            raise NotFoundException(f"Purchase request '{pr_id}' not found.")
        if pr.status != "DRAFT":
            raise ValidationException(f"Cannot remove items from purchase request in '{pr.status}' status.")
        self.repo.remove_item(pr_id, item_id, organization_id, user_id)

    def add_candidate_supplier(
        self, pr_id: str, candidate_in: CandidateSupplierCreate, organization_id: str, user_id: str
    ) -> CandidateSupplierResponse:
        pr = self.repo.get_request_by_id(pr_id, organization_id)
        if not pr:
            raise NotFoundException(f"Purchase request '{pr_id}' not found.")
        cand = self.repo.add_candidate_supplier(pr_id, organization_id, candidate_in, user_id)
        return CandidateSupplierResponse.model_validate(cand)

    def list_candidate_suppliers(self, pr_id: str, organization_id: str) -> List[CandidateSupplierResponse]:
        self.get_request(pr_id, organization_id)
        candidates = self.repo.list_candidate_suppliers(pr_id, organization_id)
        return [CandidateSupplierResponse.model_validate(c) for c in candidates]

    # State Machine Transition
    def update_status(
        self, pr_id: str, status_in: PurchaseRequestStatusUpdate, organization_id: str, user_id: str
    ) -> PurchaseRequestResponse:
        pr = self.repo.get_request_by_id(pr_id, organization_id)
        if not pr:
            raise NotFoundException(f"Purchase request '{pr_id}' not found.")

        target = status_in.status.upper()
        allowed = VALID_TRANSITIONS.get(pr.status, set())
        if target not in allowed:
            raise ValidationException(
                f"Invalid state transition from '{pr.status}' to '{target}'. Allowed next states: {', '.join(allowed) or 'None'}"
            )

        if target == "SUBMITTED" and len(pr.items) == 0:
            raise ValidationException("Cannot submit a purchase request with 0 items. Please add at least one line item.")

        updated = self.repo.transition_status(pr, target, user_id)
        return self._to_pr_response(updated)

    # Quotations
    def submit_quotation(
        self, pr_id: str, data: QuotationCreate, organization_id: str, user_id: str
    ) -> QuotationResponse:
        pr = self.repo.get_request_by_id(pr_id, organization_id)
        if not pr:
            raise NotFoundException(f"Purchase request '{pr_id}' not found.")
        if pr.status in {"CANCELLED", "REJECTED"}:
            raise ValidationException(f"Cannot register quotations for purchase request in '{pr.status}' status.")

        quote = self.repo.create_quotation(pr_id, data, organization_id, user_id)
        items = [QuotationItemResponse.model_validate(it) for it in quote.items]
        return QuotationResponse(
            id=quote.id,
            organization_id=quote.organization_id,
            purchase_request_id=quote.purchase_request_id,
            supplier_id=quote.supplier_id,
            quotation_number=quote.quotation_number,
            version=quote.version,
            total_cost=quote.total_cost,
            currency=quote.currency,
            submitted_date=quote.submitted_date,
            validity_date=quote.validity_date,
            estimated_delivery_days=quote.estimated_delivery_days,
            warranty_terms=quote.warranty_terms,
            payment_terms=quote.payment_terms,
            status=quote.status,
            document_id=quote.document_id,
            metadata_notes=quote.metadata_notes,
            items=items,
            created_at=quote.created_at,
            updated_at=quote.updated_at,
        )

    def list_quotations(self, pr_id: str, organization_id: str) -> List[QuotationResponse]:
        pr = self.repo.get_request_by_id(pr_id, organization_id)
        if not pr:
            raise NotFoundException(f"Purchase request '{pr_id}' not found.")
        quotes = self.repo.list_quotations_for_request(pr_id, organization_id)
        res = []
        for q in quotes:
            items = [QuotationItemResponse.model_validate(it) for it in q.items]
            res.append(
                QuotationResponse(
                    id=q.id,
                    organization_id=q.organization_id,
                    purchase_request_id=q.purchase_request_id,
                    supplier_id=q.supplier_id,
                    quotation_number=q.quotation_number,
                    version=q.version,
                    total_cost=q.total_cost,
                    currency=q.currency,
                    submitted_date=q.submitted_date,
                    validity_date=q.validity_date,
                    estimated_delivery_days=q.estimated_delivery_days,
                    warranty_terms=q.warranty_terms,
                    payment_terms=q.payment_terms,
                    status=q.status,
                    document_id=q.document_id,
                    metadata_notes=q.metadata_notes,
                    items=items,
                    created_at=q.created_at,
                    updated_at=q.updated_at,
                )
            )
        return res

    def get_quotation(self, quote_id: str, organization_id: str) -> QuotationResponse:
        quote = self.repo.get_quotation_by_id(quote_id, organization_id)
        if not quote:
            raise NotFoundException(f"Quotation '{quote_id}' not found.")
        items = [QuotationItemResponse.model_validate(it) for it in quote.items]
        return QuotationResponse(
            id=quote.id,
            organization_id=quote.organization_id,
            purchase_request_id=quote.purchase_request_id,
            supplier_id=quote.supplier_id,
            quotation_number=quote.quotation_number,
            version=quote.version,
            total_cost=quote.total_cost,
            currency=quote.currency,
            submitted_date=quote.submitted_date,
            validity_date=quote.validity_date,
            estimated_delivery_days=quote.estimated_delivery_days,
            warranty_terms=quote.warranty_terms,
            payment_terms=quote.payment_terms,
            status=quote.status,
            document_id=quote.document_id,
            metadata_notes=quote.metadata_notes,
            items=items,
            created_at=quote.created_at,
            updated_at=quote.updated_at,
        )

    def record_decision(
        self, pr_id: str, decision: PurchaseRequestDecision, organization_id: str, user_id: str
    ) -> PurchaseRequestDetailResponse:
        pr = self.repo.get_request_by_id(pr_id, organization_id)
        if not pr:
            raise NotFoundException(f"Purchase request '{pr_id}' not found.")
        if pr.status not in {"SUBMITTED", "UNDER_EVALUATION"}:
            raise ValidationException(
                f"Cannot record decision for purchase request in '{pr.status}' status. Must be SUBMITTED or UNDER_EVALUATION."
            )
        action = decision.action.upper()
        if action not in {"APPROVE", "REJECT"}:
            raise ValidationException(f"Invalid decision action '{action}'. Must be 'APPROVE' or 'REJECT'.")

        updated = self.repo.record_human_decision(
            pr=pr,
            action=action,
            reason=decision.decision_reason,
            selected_supplier_id=decision.selected_supplier_id,
            selected_quotation_id=decision.selected_quotation_id,
            user_id=user_id,
        )
        return self._to_pr_detail_response(updated)

