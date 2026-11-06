import os
import sys
from pathlib import Path
from celery import Celery

workspace_root = Path(__file__).resolve().parents[2]
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from shared.extraction.extractor import QuotationExtractor

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672//")

celery_app = Celery(
    "document_tasks",
    broker=RABBITMQ_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)


@celery_app.task(name="tasks.ping")
def ping():
    return "pong"


@celery_app.task(name="tasks.process_document_extraction", bind=True, max_retries=3, default_retry_delay=10)
def process_document_extraction(self, document_id: str, file_path_str: str, filename: str):
    """Asynchronous background worker task extracting structured quotation data."""
    try:
        path = Path(file_path_str)
        if not path.exists():
            raise FileNotFoundError(f"Document file {file_path_str} not found on worker storage.")

        file_bytes = path.read_bytes()
        extracted = QuotationExtractor.process_document(file_bytes, filename)
        return {
            "status": "SUCCESS",
            "document_id": document_id,
            "data": extracted.model_dump(),
        }
    except Exception as exc:
        raise self.retry(exc=exc)
