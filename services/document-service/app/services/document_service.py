import json
from pathlib import Path
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.repositories.document_repository import DocumentRepository
from app.storage.storage_manager import StorageManager
from app.schemas.document import DocumentResponse
from shared.core.exceptions import NotFoundException, ValidationException
from shared.extraction.schemas import (
    StructuredQuotationData,
    ExtractionCorrectionRequest,
    ExtractionResponse,
)
from shared.extraction.extractor import QuotationExtractor


class DocumentService:
    def __init__(self, db: Session, storage_dir: str = "data/documents"):
        self.repo = DocumentRepository(db)
        self.storage = StorageManager(base_directory=storage_dir)

    def upload_document(
        self,
        organization_id: str,
        filename: str,
        content_type: str,
        file_bytes: bytes,
        purchase_request_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        quotation_id: Optional[str] = None,
    ) -> DocumentResponse:
        self.storage.validate_file(filename, content_type, len(file_bytes))
        storage_path, checksum, file_size = self.storage.save_file(organization_id, filename, file_bytes)

        record = self.repo.create(
            organization_id=organization_id,
            file_name=filename,
            file_size=file_size,
            content_type=content_type,
            storage_path=storage_path,
            checksum=checksum,
            purchase_request_id=purchase_request_id,
            supplier_id=supplier_id,
            quotation_id=quotation_id,
        )
        return DocumentResponse.model_validate(record)

    def get_document(self, doc_id: str, organization_id: str) -> DocumentResponse:
        record = self.repo.get_by_id(doc_id, organization_id)
        if not record:
            raise NotFoundException(f"Document '{doc_id}' not found.")
        return DocumentResponse.model_validate(record)

    def list_documents(
        self,
        organization_id: str,
        purchase_request_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[DocumentResponse]:
        records = self.repo.list_by_organization(
            organization_id=organization_id,
            purchase_request_id=purchase_request_id,
            supplier_id=supplier_id,
            skip=skip,
            limit=limit,
        )
        return [DocumentResponse.model_validate(r) for r in records]

    def get_file_for_download(self, doc_id: str, organization_id: str) -> Tuple[Path, str, str]:
        record = self.repo.get_by_id(doc_id, organization_id)
        if not record:
            raise NotFoundException(f"Document '{doc_id}' not found.")
        file_path = self.storage.get_file_path(record.storage_path)
        return file_path, record.file_name, record.content_type

    # --- Document Intelligence & Extraction ---
    def trigger_extraction(self, doc_id: str, organization_id: str) -> ExtractionResponse:
        doc = self.repo.get_by_id(doc_id, organization_id)
        if not doc:
            raise NotFoundException(f"Document '{doc_id}' not found.")

        # Read stored file bytes
        file_path = self.storage.get_file_path(doc.storage_path)
        file_bytes = file_path.read_bytes()

        # Run multi-format parser
        structured_data = QuotationExtractor.process_document(file_bytes, doc.file_name)
        extraction = self.repo.save_extraction(doc_id, organization_id, structured_data)

        return self._to_extraction_response(extraction)

    def get_extraction(self, doc_id: str, organization_id: str) -> ExtractionResponse:
        extraction = self.repo.get_extraction(doc_id, organization_id)
        if not extraction:
            raise NotFoundException(f"No extraction found for document '{doc_id}'. Please trigger extraction first.")
        return self._to_extraction_response(extraction)

    def correct_extraction(
        self,
        doc_id: str,
        organization_id: str,
        corrections: ExtractionCorrectionRequest,
        corrected_by: str,
    ) -> ExtractionResponse:
        extraction = self.repo.apply_corrections(doc_id, organization_id, corrections, corrected_by)
        return self._to_extraction_response(extraction)

    def verify_extraction(self, doc_id: str, organization_id: str, verified_by: str) -> ExtractionResponse:
        extraction = self.repo.verify_extraction(doc_id, organization_id, verified_by)
        return self._to_extraction_response(extraction)

    def _to_extraction_response(self, extraction) -> ExtractionResponse:
        data = StructuredQuotationData.model_validate_json(extraction.structured_data_json)
        flagged = json.loads(extraction.flagged_reasons_json) if extraction.flagged_reasons_json else []
        return ExtractionResponse(
            id=extraction.id,
            document_id=extraction.document_id,
            organization_id=extraction.organization_id,
            purchase_request_id=extraction.purchase_request_id,
            supplier_id=extraction.supplier_id,
            supplier_name=extraction.supplier_name,
            quotation_number=extraction.quotation_number,
            currency=extraction.currency,
            total_cost=extraction.total_cost,
            overall_confidence=extraction.confidence_score,
            arithmetic_valid=extraction.arithmetic_valid,
            is_verified=extraction.is_verified,
            verified_by=extraction.verified_by,
            verified_at=extraction.verified_at,
            flagged_reasons=flagged,
            structured_data=data,
            created_at=extraction.created_at,
            updated_at=extraction.updated_at,
        )
