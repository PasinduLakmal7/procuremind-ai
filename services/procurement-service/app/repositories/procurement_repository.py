import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.purchase_requests import (
    PurchaseRequest,
    PurchaseRequestItem,
    CandidateSupplier,
    Quotation,
    QuotationItem,
    ProcurementAuditEvent,
    OutboxEvent,
)
from app.schemas.purchase_request import (
    PurchaseRequestCreate,
    PurchaseRequestUpdate,
    PurchaseRequestItemCreate,
    CandidateSupplierCreate,
)
from app.schemas.quotation import QuotationCreate, QuotationItemCreate


class ProcurementRepository:
    def __init__(self, db: Session):
        self.db = db

    def generate_request_number(self, organization_id: str) -> str:
        count = self.db.query(PurchaseRequest).filter(PurchaseRequest.organization_id == organization_id).count()
        year = 2026
        return f"PR-{year}-{count + 1:04d}"

    def create_request(self, data: PurchaseRequestCreate, organization_id: str, user_id: str) -> PurchaseRequest:
        req_num = self.generate_request_number(organization_id)
        pr = PurchaseRequest(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            created_by_user_id=user_id,
            request_number=req_num,
            title=data.title,
            description=data.description,
            category=data.category,
            priority=data.priority,
            budget_limit=data.budget_limit,
            currency=data.currency,
            required_delivery_date=data.required_delivery_date,
            evaluation_criteria=data.evaluation_criteria,
            status="DRAFT",
        )
        self.db.add(pr)

        if data.items:
            for item in data.items:
                pr_item = PurchaseRequestItem(
                    id=str(uuid.uuid4()),
                    organization_id=organization_id,
                    purchase_request_id=pr.id,
                    item_name=item.item_name,
                    specification=item.specification,
                    quantity=item.quantity,
                    unit_of_measure=item.unit_of_measure,
                    target_unit_price=item.target_unit_price,
                )
                self.db.add(pr_item)

        # Audit event
        audit = ProcurementAuditEvent(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            purchase_request_id=pr.id,
            event_type="DRAFT_CREATED",
            performed_by=user_id,
            new_state="DRAFT",
            details=f"Draft purchase request {req_num} created.",
        )
        self.db.add(audit)

        self.db.commit()
        self.db.refresh(pr)
        return pr

    def get_request_by_id(self, pr_id: str, organization_id: str) -> Optional[PurchaseRequest]:
        return (
            self.db.query(PurchaseRequest)
            .filter(PurchaseRequest.id == pr_id, PurchaseRequest.organization_id == organization_id)
            .first()
        )

    def list_requests(
        self,
        organization_id: str,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[PurchaseRequest]:
        query = self.db.query(PurchaseRequest).filter(PurchaseRequest.organization_id == organization_id)
        if status:
            query = query.filter(PurchaseRequest.status == status)
        if category:
            query = query.filter(PurchaseRequest.category == category)
        if priority:
            query = query.filter(PurchaseRequest.priority == priority)
        return query.order_by(PurchaseRequest.created_at.desc()).offset(skip).limit(limit).all()

    def update_request(self, pr: PurchaseRequest, update_in: PurchaseRequestUpdate, user_id: str) -> PurchaseRequest:
        update_data = update_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(pr, field, value)
        
        audit = ProcurementAuditEvent(
            id=str(uuid.uuid4()),
            organization_id=pr.organization_id,
            purchase_request_id=pr.id,
            event_type="DRAFT_EDITED",
            performed_by=user_id,
            details=f"Fields updated: {', '.join(update_data.keys())}",
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(pr)
        return pr

    # Items
    def add_item(self, pr_id: str, organization_id: str, item_in: PurchaseRequestItemCreate, user_id: str) -> PurchaseRequestItem:
        item = PurchaseRequestItem(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            purchase_request_id=pr_id,
            item_name=item_in.item_name,
            specification=item_in.specification,
            quantity=item_in.quantity,
            unit_of_measure=item_in.unit_of_measure,
            target_unit_price=item_in.target_unit_price,
        )
        self.db.add(item)
        audit = ProcurementAuditEvent(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            purchase_request_id=pr_id,
            event_type="ITEM_ADDED",
            performed_by=user_id,
            details=f"Added item {item_in.item_name} (Qty: {item_in.quantity})",
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(item)
        return item

    def remove_item(self, pr_id: str, item_id: str, organization_id: str, user_id: str) -> None:
        item = (
            self.db.query(PurchaseRequestItem)
            .filter(
                PurchaseRequestItem.id == item_id,
                PurchaseRequestItem.purchase_request_id == pr_id,
                PurchaseRequestItem.organization_id == organization_id,
            )
            .first()
        )
        if item:
            item_name = item.item_name
            self.db.delete(item)
            audit = ProcurementAuditEvent(
                id=str(uuid.uuid4()),
                organization_id=organization_id,
                purchase_request_id=pr_id,
                event_type="ITEM_REMOVED",
                performed_by=user_id,
                details=f"Removed item {item_name}",
            )
            self.db.add(audit)
            self.db.commit()

    # Candidate Suppliers
    def add_candidate_supplier(
        self, pr_id: str, organization_id: str, candidate_in: CandidateSupplierCreate, user_id: str
    ) -> CandidateSupplier:
        candidate = CandidateSupplier(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            purchase_request_id=pr_id,
            supplier_id=candidate_in.supplier_id,
            supplier_name=candidate_in.supplier_name,
            supplier_email=candidate_in.supplier_email,
            invitation_status="INVITED",
        )
        self.db.add(candidate)
        audit = ProcurementAuditEvent(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            purchase_request_id=pr_id,
            event_type="SUPPLIER_ASSOCIATED",
            performed_by=user_id,
            details=f"Associated supplier {candidate_in.supplier_name} ({candidate_in.supplier_id})",
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def list_candidate_suppliers(self, pr_id: str, organization_id: str) -> List[CandidateSupplier]:
        return (
            self.db.query(CandidateSupplier)
            .filter(CandidateSupplier.purchase_request_id == pr_id, CandidateSupplier.organization_id == organization_id)
            .all()
        )

    # State Transition & Outbox Event
    def transition_status(
        self, pr: PurchaseRequest, new_status: str, user_id: str
    ) -> PurchaseRequest:
        old_status = pr.status
        pr.status = new_status

        audit = ProcurementAuditEvent(
            id=str(uuid.uuid4()),
            organization_id=pr.organization_id,
            purchase_request_id=pr.id,
            event_type="STATUS_CHANGED",
            performed_by=user_id,
            old_state=old_status,
            new_state=new_status,
            details=f"Status changed from {old_status} to {new_status}",
        )
        self.db.add(audit)

        # Transactional outbox event if submitted
        if new_status == "SUBMITTED":
            payload = json.dumps({
                "purchase_request_id": pr.id,
                "request_number": pr.request_number,
                "organization_id": pr.organization_id,
                "title": pr.title,
                "budget_limit": pr.budget_limit,
                "currency": pr.currency,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "submitted_by": user_id,
            })
            outbox = OutboxEvent(
                id=str(uuid.uuid4()),
                organization_id=pr.organization_id,
                event_type="purchase_request.submitted.v1",
                aggregate_type="PurchaseRequest",
                aggregate_id=pr.id,
                payload=payload,
                status="PENDING",
            )
            self.db.add(outbox)

        self.db.commit()
        self.db.refresh(pr)
        return pr

    # Quotations
    def create_quotation(self, pr_id: str, data: QuotationCreate, organization_id: str, user_id: str) -> Quotation:
        quote = Quotation(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            purchase_request_id=pr_id,
            supplier_id=data.supplier_id,
            quotation_number=data.quotation_number,
            version=data.version,
            total_cost=data.total_cost,
            currency=data.currency,
            submitted_date=data.submitted_date or datetime.now(timezone.utc),
            validity_date=data.validity_date,
            estimated_delivery_days=data.estimated_delivery_days,
            warranty_terms=data.warranty_terms,
            payment_terms=data.payment_terms,
            document_id=data.document_id,
            metadata_notes=data.metadata_notes,
            status="RECEIVED",
        )
        self.db.add(quote)

        if data.items:
            for it in data.items:
                tot = it.total_price if it.total_price is not None else (it.quantity * it.unit_price)
                q_item = QuotationItem(
                    id=str(uuid.uuid4()),
                    organization_id=organization_id,
                    quotation_id=quote.id,
                    item_name=it.item_name,
                    quantity=it.quantity,
                    unit_of_measure=it.unit_of_measure,
                    unit_price=it.unit_price,
                    total_price=tot,
                    lead_time_days=it.lead_time_days,
                )
                self.db.add(q_item)

        audit = ProcurementAuditEvent(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            purchase_request_id=pr_id,
            event_type="QUOTATION_REGISTERED",
            performed_by=user_id,
            details=f"Registered quotation {data.quotation_number} from supplier {data.supplier_id}",
        )
        self.db.add(audit)

        self.db.commit()
        self.db.refresh(quote)
        return quote

    def list_quotations_for_request(self, pr_id: str, organization_id: str) -> List[Quotation]:
        return (
            self.db.query(Quotation)
            .filter(Quotation.purchase_request_id == pr_id, Quotation.organization_id == organization_id)
            .order_by(Quotation.total_cost.asc())
            .all()
        )

    def get_quotation_by_id(self, quote_id: str, organization_id: str) -> Optional[Quotation]:
        return (
            self.db.query(Quotation)
            .filter(Quotation.id == quote_id, Quotation.organization_id == organization_id)
            .first()
        )

    def list_outbox_events(self, organization_id: str, status: str = "PENDING") -> List[OutboxEvent]:
        return (
            self.db.query(OutboxEvent)
            .filter(OutboxEvent.organization_id == organization_id, OutboxEvent.status == status)
            .all()
        )

    def record_human_decision(
        self,
        pr: PurchaseRequest,
        action: str,
        reason: str,
        selected_supplier_id: Optional[str],
        selected_quotation_id: Optional[str],
        user_id: str,
    ) -> PurchaseRequest:
        old_status = pr.status
        new_status = "APPROVED" if action.upper() == "APPROVE" else "REJECTED"
        pr.status = new_status
        pr.updated_at = datetime.now(timezone.utc)

        if action.upper() == "APPROVE" and selected_quotation_id:
            for q in pr.quotations:
                if q.id == selected_quotation_id:
                    q.status = "ACCEPTED"
                else:
                    q.status = "REJECTED"

        audit = ProcurementAuditEvent(
            id=str(uuid.uuid4()),
            organization_id=pr.organization_id,
            purchase_request_id=pr.id,
            event_type=f"DECISION_{new_status}",
            performed_by=user_id,
            old_state=old_status,
            new_state=new_status,
            details=json.dumps({
                "action": action,
                "reason": reason,
                "selected_supplier_id": selected_supplier_id,
                "selected_quotation_id": selected_quotation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }),
        )
        self.db.add(audit)

        outbox = OutboxEvent(
            id=str(uuid.uuid4()),
            organization_id=pr.organization_id,
            event_type="purchase_request.decision_recorded.v1",
            aggregate_type="PurchaseRequest",
            aggregate_id=pr.id,
            payload=json.dumps({
                "purchase_request_id": pr.id,
                "organization_id": pr.organization_id,
                "status": new_status,
                "action": action,
                "reason": reason,
                "selected_supplier_id": selected_supplier_id,
                "selected_quotation_id": selected_quotation_id,
                "decided_by": user_id,
            }),
            status="PENDING",
        )
        self.db.add(outbox)

        self.db.commit()
        self.db.refresh(pr)
        return pr
