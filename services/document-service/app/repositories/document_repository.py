import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.document_records import (
    DocumentRecord,
    DocumentOutboxEvent,
    QuotationExtraction,
    ExtractionCorrectionAudit,
)
from shared.extraction.schemas import StructuredQuotationData, ExtractionCorrectionRequest


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        organization_id: str,
        file_name: str,
        file_size: int,
        content_type: str,
        storage_path: str,
        checksum: str,
        purchase_request_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        quotation_id: Optional[str] = None,
    ) -> DocumentRecord:
        record = DocumentRecord(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            purchase_request_id=purchase_request_id,
            supplier_id=supplier_id,
            quotation_id=quotation_id,
            file_name=file_name,
            file_size=file_size,
            content_type=content_type,
            storage_path=storage_path,
            status="UPLOADED",
            checksum_sha256=checksum,
        )
        self.db.add(record)

        # Transactional outbox event
        payload = json.dumps({
            "document_id": record.id,
            "organization_id": organization_id,
            "file_name": file_name,
            "file_size": file_size,
            "content_type": content_type,
            "storage_path": storage_path,
            "checksum_sha256": checksum,
            "purchase_request_id": purchase_request_id,
            "supplier_id": supplier_id,
            "quotation_id": quotation_id,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        })
        outbox = DocumentOutboxEvent(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            event_type="quotation.document.uploaded.v1",
            aggregate_id=record.id,
            payload=payload,
            status="PENDING",
        )
        self.db.add(outbox)

        self.db.commit()
        self.db.refresh(record)
        return record

    def get_by_id(self, doc_id: str, organization_id: str) -> Optional[DocumentRecord]:
        return (
            self.db.query(DocumentRecord)
            .filter(DocumentRecord.id == doc_id, DocumentRecord.organization_id == organization_id)
            .first()
        )

    def list_by_organization(
        self,
        organization_id: str,
        purchase_request_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[DocumentRecord]:
        query = self.db.query(DocumentRecord).filter(DocumentRecord.organization_id == organization_id)
        if purchase_request_id:
            query = query.filter(DocumentRecord.purchase_request_id == purchase_request_id)
        if supplier_id:
            query = query.filter(DocumentRecord.supplier_id == supplier_id)
        return query.order_by(DocumentRecord.created_at.desc()).offset(skip).limit(limit).all()

    def update_status(self, doc_id: str, organization_id: str, new_status: str) -> Optional[DocumentRecord]:
        record = self.get_by_id(doc_id, organization_id)
        if record:
            record.status = new_status
            self.db.commit()
            self.db.refresh(record)
        return record

    # --- Extractions ---
    def save_extraction(
        self,
        doc_id: str,
        organization_id: str,
        structured_data: StructuredQuotationData,
    ) -> QuotationExtraction:
        doc = self.get_by_id(doc_id, organization_id)
        existing = (
            self.db.query(QuotationExtraction)
            .filter(QuotationExtraction.document_id == doc_id, QuotationExtraction.organization_id == organization_id)
            .first()
        )

        data_json = structured_data.model_dump_json()
        flagged_json = json.dumps(structured_data.flagged_reasons)

        if existing:
            existing.supplier_name = structured_data.supplier_name
            existing.quotation_number = structured_data.quotation_number
            existing.currency = structured_data.currency
            existing.total_cost = structured_data.total_cost
            existing.confidence_score = structured_data.overall_confidence
            existing.arithmetic_valid = structured_data.arithmetic_valid
            existing.structured_data_json = data_json
            existing.flagged_reasons_json = flagged_json
            self.db.commit()
            self.db.refresh(existing)
            return existing

        extraction = QuotationExtraction(
            id=str(uuid.uuid4()),
            document_id=doc_id,
            organization_id=organization_id,
            purchase_request_id=doc.purchase_request_id if doc else None,
            supplier_id=doc.supplier_id if doc else None,
            supplier_name=structured_data.supplier_name,
            quotation_number=structured_data.quotation_number,
            currency=structured_data.currency,
            total_cost=structured_data.total_cost,
            confidence_score=structured_data.overall_confidence,
            arithmetic_valid=structured_data.arithmetic_valid,
            is_verified=False,
            structured_data_json=data_json,
            flagged_reasons_json=flagged_json,
        )
        self.db.add(extraction)
        if doc:
            doc.status = "EXTRACTED"
        self.db.commit()
        self.db.refresh(extraction)
        return extraction

    def get_extraction(self, doc_id: str, organization_id: str) -> Optional[QuotationExtraction]:
        return (
            self.db.query(QuotationExtraction)
            .filter(QuotationExtraction.document_id == doc_id, QuotationExtraction.organization_id == organization_id)
            .first()
        )

    def apply_corrections(
        self,
        doc_id: str,
        organization_id: str,
        corrections: ExtractionCorrectionRequest,
        corrected_by: str,
    ) -> QuotationExtraction:
        extraction = self.get_extraction(doc_id, organization_id)
        if not extraction:
            raise ValueError(f"No extraction found for document {doc_id}")

        current_data = StructuredQuotationData.model_validate_json(extraction.structured_data_json)
        corr_dict = corrections.model_dump(exclude_unset=True)

        for field, new_val in corr_dict.items():
            old_val = getattr(current_data, field, None)
            if new_val != old_val:
                setattr(current_data, field, new_val)
                # Audit log entry
                audit = ExtractionCorrectionAudit(
                    id=str(uuid.uuid4()),
                    extraction_id=extraction.id,
                    organization_id=organization_id,
                    corrected_by=corrected_by,
                    field_name=field,
                    old_value=str(old_val),
                    new_value=str(new_val),
                )
                self.db.add(audit)

        # Update extraction root fields
        if corrections.supplier_name:
            extraction.supplier_name = corrections.supplier_name
        if corrections.quotation_number:
            extraction.quotation_number = corrections.quotation_number
        if corrections.currency:
            extraction.currency = corrections.currency
        if corrections.total_cost is not None:
            extraction.total_cost = corrections.total_cost

        extraction.structured_data_json = current_data.model_dump_json()
        self.db.commit()
        self.db.refresh(extraction)
        return extraction

    def verify_extraction(self, doc_id: str, organization_id: str, verified_by: str) -> QuotationExtraction:
        extraction = self.get_extraction(doc_id, organization_id)
        if not extraction:
            raise ValueError(f"No extraction found for document {doc_id}")

        extraction.is_verified = True
        extraction.verified_by = verified_by
        extraction.verified_at = datetime.now(timezone.utc)

        doc = self.get_by_id(doc_id, organization_id)
        if doc:
            doc.status = "VERIFIED"

        self.db.commit()
        self.db.refresh(extraction)
        return extraction
