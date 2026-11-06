from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.document import DocumentResponse
from app.services.document_service import DocumentService
from app.core.config import settings
from shared.auth.jwt_validator import get_current_principal_factory, SecurityPrincipal
from shared.api_contracts.responses import ApiResponse
from shared.extraction.schemas import (
    ExtractionResponse,
    ExtractionCorrectionRequest,
)

router = APIRouter(prefix="/documents", tags=["Quotation Documents & Intelligence"])

get_current_principal = get_current_principal_factory(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
)


@router.post("/upload", response_model=ApiResponse[DocumentResponse], status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    purchase_request_id: Optional[str] = Form(None),
    supplier_id: Optional[str] = Form(None),
    quotation_id: Optional[str] = Form(None),
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Uploads quotation document (PDF, Excel, CSV, images) into organization-scoped storage."""
    file_bytes = await file.read()
    service = DocumentService(db)
    record = service.upload_document(
        organization_id=str(principal.organization_id),
        filename=file.filename or "quotation.pdf",
        content_type=file.content_type or "application/octet-stream",
        file_bytes=file_bytes,
        purchase_request_id=purchase_request_id,
        supplier_id=supplier_id,
        quotation_id=quotation_id,
    )
    return ApiResponse(data=record, message="Document uploaded successfully.")


@router.get("", response_model=ApiResponse[List[DocumentResponse]])
def list_documents(
    purchase_request_id: Optional[str] = None,
    supplier_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Lists uploaded document metadata belonging to the caller's organization."""
    service = DocumentService(db)
    docs = service.list_documents(
        organization_id=str(principal.organization_id),
        purchase_request_id=purchase_request_id,
        supplier_id=supplier_id,
        skip=skip,
        limit=limit,
    )
    return ApiResponse(data=docs)


@router.get("/{document_id}", response_model=ApiResponse[DocumentResponse])
def get_document_metadata(
    document_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Retrieves metadata of a document."""
    service = DocumentService(db)
    doc = service.get_document(document_id, organization_id=str(principal.organization_id))
    return ApiResponse(data=doc)


@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Downloads binary document file enforcing tenant isolation."""
    service = DocumentService(db)
    file_path, filename, content_type = service.get_file_for_download(
        document_id, organization_id=str(principal.organization_id)
    )
    return FileResponse(path=file_path, filename=filename, media_type=content_type)


# ----------------- Document Intelligence Endpoints -----------------

@router.post("/{document_id}/extract", response_model=ApiResponse[ExtractionResponse])
def trigger_document_extraction(
    document_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Extracts structured line items, pricing, arithmetic verification, and flags."""
    service = DocumentService(db)
    extraction = service.trigger_extraction(document_id, organization_id=str(principal.organization_id))
    return ApiResponse(data=extraction, message="Quotation extraction completed.")


@router.get("/{document_id}/extraction", response_model=ApiResponse[ExtractionResponse])
def get_document_extraction(
    document_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Retrieves structured quotation extraction result with confidence scores and evidence."""
    service = DocumentService(db)
    extraction = service.get_extraction(document_id, organization_id=str(principal.organization_id))
    return ApiResponse(data=extraction)


@router.put("/{document_id}/extraction", response_model=ApiResponse[ExtractionResponse])
def correct_extraction_fields(
    document_id: str,
    body: ExtractionCorrectionRequest,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Allows authorized human-in-the-loop reviewer to correct extraction fields with audit tracking."""
    service = DocumentService(db)
    updated = service.correct_extraction(
        doc_id=document_id,
        organization_id=str(principal.organization_id),
        corrections=body,
        corrected_by=str(principal.user_id),
    )
    return ApiResponse(data=updated, message="Extraction updated and correction audited.")


@router.post("/{document_id}/verify", response_model=ApiResponse[ExtractionResponse])
def verify_document_extraction(
    document_id: str,
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Confirms and verifies extracted quotation data for downstream AI orchestration."""
    service = DocumentService(db)
    verified = service.verify_extraction(
        doc_id=document_id,
        organization_id=str(principal.organization_id),
        verified_by=str(principal.user_id),
    )
    return ApiResponse(data=verified, message="Quotation extraction marked as verified.")
