import hashlib
import os
import uuid
from pathlib import Path
from typing import Tuple
from shared.core.exceptions import ValidationException

ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv", ".png", ".jpg", ".jpeg"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/csv",
    "image/png",
    "image/jpeg",
}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


class StorageManager:
    def __init__(self, base_directory: str = "data/documents"):
        self.base_dir = Path(base_directory)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, filename: str, content_type: str, file_size: int) -> None:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationException(
                f"Unsupported file extension '{ext}'. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
            raise ValidationException(f"Unsupported content type '{content_type}'.")

        if file_size > MAX_FILE_SIZE_BYTES:
            raise ValidationException(f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB.")

    def save_file(self, organization_id: str, filename: str, file_bytes: bytes) -> Tuple[str, str, int]:
        """Saves file bytes into organization-scoped folder and returns (relative_path, checksum_sha256, size)."""
        sha256 = hashlib.sha256(file_bytes).hexdigest()
        ext = Path(filename).suffix.lower()
        unique_name = f"{uuid.uuid4()}{ext}"

        org_folder = self.base_dir / organization_id
        org_folder.mkdir(parents=True, exist_ok=True)

        target_path = org_folder / unique_name
        target_path.write_bytes(file_bytes)

        relative_path = str(target_path.relative_to(self.base_dir.parent))
        return relative_path, sha256, len(file_bytes)

    def get_file_path(self, storage_path: str) -> Path:
        resolved = self.base_dir.parent / storage_path
        if not resolved.exists():
            raise ValidationException("Stored document file could not be located on disk.")
        return resolved

