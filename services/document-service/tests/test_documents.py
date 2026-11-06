import io
import uuid
import pytest
from jose import jwt
from app.models.document_records import DocumentOutboxEvent


def create_test_token(org_id: str, email: str = "officer@factory.lk", role: str = "procurement_officer") -> str:
    secret_key = "test-secret-key-32-characters-minimum-length-for-testing"
    return jwt.encode({
        "sub": str(uuid.uuid4()),
        "email": email,
        "organization_id": org_id,
        "roles": [role],
        "token_type": "access",
        "exp": 2000000000
    }, secret_key, algorithm="HS256")


def test_document_upload_and_download_flow(client, db_session):
    org_1 = str(uuid.uuid4())
    org_2 = str(uuid.uuid4())
    token_org1 = create_test_token(org_1)
    token_org2 = create_test_token(org_2)

    fake_pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n>>\n%%EOF"
    file_payload = ("quotation_supplier_a.pdf", io.BytesIO(fake_pdf_content), "application/pdf")

    # 1. Upload Document in Org 1
    upload_res = client.post(
        "/api/v1/document/documents/upload",
        files={"file": file_payload},
        data={"purchase_request_id": str(uuid.uuid4()), "supplier_id": str(uuid.uuid4())},
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()["data"]
    doc_id = doc_data["id"]
    assert doc_data["file_name"] == "quotation_supplier_a.pdf"
    assert doc_data["organization_id"] == org_1
    assert doc_data["status"] == "UPLOADED"
    assert doc_data["checksum_sha256"] is not None

    # Check Outbox Event creation
    outbox = db_session.query(DocumentOutboxEvent).filter(
        DocumentOutboxEvent.aggregate_id == doc_id,
        DocumentOutboxEvent.event_type == "quotation.document.uploaded.v1",
    ).first()
    assert outbox is not None
    assert outbox.status == "PENDING"

    # 2. Retrieve Metadata
    meta_res = client.get(
        f"/api/v1/document/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert meta_res.status_code == 200
    assert meta_res.json()["data"]["id"] == doc_id

    # 3. Organization Isolation: Org 2 cannot retrieve Org 1 document metadata
    cross_org_res = client.get(
        f"/api/v1/document/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token_org2}"}
    )
    assert cross_org_res.status_code == 404

    # 4. Download file
    dl_res = client.get(
        f"/api/v1/document/documents/{doc_id}/download",
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert dl_res.status_code == 200
    assert dl_res.content == fake_pdf_content

    # 5. Reject Invalid File Extension
    bad_file = ("script.exe", io.BytesIO(b"malicious code"), "application/octet-stream")
    bad_res = client.post(
        "/api/v1/document/documents/upload",
        files={"file": bad_file},
        headers={"Authorization": f"Bearer {token_org1}"}
    )
    assert bad_res.status_code == 422


def test_additional_document_formats_upload(client):
    org_id = str(uuid.uuid4())
    token = create_test_token(org_id)

    # Spreadsheet CSV
    csv_content = b"item,quantity,price\nSteel,100,2500"
    res_csv = client.post(
        "/api/v1/document/documents/upload",
        files={"file": ("quotes.csv", io.BytesIO(csv_content), "text/csv")},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_csv.status_code == 201

    # Image PNG
    png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    res_png = client.post(
        "/api/v1/document/documents/upload",
        files={"file": ("scan.png", io.BytesIO(png_content), "image/png")},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_png.status_code == 201
