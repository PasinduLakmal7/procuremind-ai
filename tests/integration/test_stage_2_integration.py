import os
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import json
import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import Column, String, Integer, DateTime, CHAR, Text, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from shared.event_contracts.envelope import EventEnvelope
from shared.event_contracts.procurement_events import (
    PurchaseRequestSubmittedPayload,
    QuotationDocumentUploadedPayload,
)
from shared.events.outbox_publisher import (
    InMemoryMessageTransport,
    OutboxPublisher,
    IdempotentEventConsumer,
)

Base = declarative_base()


class MockOutboxEvent(Base):
    __tablename__ = "mock_outbox_events"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False)
    event_type = Column(String(100), nullable=False)
    aggregate_type = Column(String(100), nullable=False)
    aggregate_id = Column(CHAR(36), nullable=False)
    payload = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    published_at = Column(DateTime, nullable=True)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_outbox_event_contracts_and_reliable_publishing(db_session):
    transport = InMemoryMessageTransport()
    publisher = OutboxPublisher(transport=transport, max_retries=3)

    org_id = str(uuid.uuid4())
    pr_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # 1. Test purchase_request.submitted.v1 payload contract
    pr_payload = PurchaseRequestSubmittedPayload(
        purchase_request_id=pr_id,
        request_number="PR-2026-0001",
        organization_id=org_id,
        title="Industrial Machinery Bearings",
        budget_limit=750000.0,
        currency="LKR",
        submitted_at=now,
        submitted_by=str(uuid.uuid4()),
    )
    assert pr_payload.currency == "LKR"

    outbox_pr = MockOutboxEvent(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        event_type="purchase_request.submitted.v1",
        aggregate_type="PurchaseRequest",
        aggregate_id=pr_id,
        payload=pr_payload.model_dump_json(),
        status="PENDING",
    )
    db_session.add(outbox_pr)
    db_session.commit()

    # 2. Test quotation.document.uploaded.v1 payload contract
    doc_id = str(uuid.uuid4())
    doc_payload = QuotationDocumentUploadedPayload(
        document_id=doc_id,
        organization_id=org_id,
        file_name="Quotation_Bearings_2026.pdf",
        file_size=102400,
        content_type="application/pdf",
        storage_path=f"data/documents/{org_id}/test.pdf",
        checksum_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        purchase_request_id=pr_id,
        uploaded_at=now,
    )
    outbox_doc = MockOutboxEvent(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        event_type="quotation.document.uploaded.v1",
        aggregate_type="DocumentRecord",
        aggregate_id=doc_id,
        payload=doc_payload.model_dump_json(),
        status="PENDING",
    )
    db_session.add(outbox_doc)
    db_session.commit()

    # 3. Publish both events
    res_pr = publisher.process_outbox_event(outbox_pr, db_session)
    res_doc = publisher.process_outbox_event(outbox_doc, db_session)

    assert res_pr is True
    assert res_doc is True
    assert outbox_pr.status == "PUBLISHED"
    assert outbox_doc.status == "PUBLISHED"
    assert len(transport.published_messages) == 2

    keys = [msg["routing_key"] for msg in transport.published_messages]
    assert "purchase_request.submitted.v1" in keys
    assert "quotation.document.uploaded.v1" in keys


def test_idempotent_event_consumer():
    consumer = IdempotentEventConsumer()
    received_events = []

    def handle_event(envelope: EventEnvelope):
        received_events.append(envelope.payload)

    env = EventEnvelope(
        event_id="evt-112233",
        event_type="purchase_request.submitted.v1",
        producer="PurchaseRequest",
        payload={"request_number": "PR-2026-0001"},
    )

    # First receive
    assert consumer.process(env, handle_event) is True
    assert len(received_events) == 1

    # Redelivered duplicate
    assert consumer.process(env, handle_event) is False
    assert len(received_events) == 1  # Exactly-once guarantee maintained


def test_outbox_dead_letter_and_retry_policy(db_session):
    class FailingTransport(InMemoryMessageTransport):
        def publish(self, exchange: str, routing_key: str, message_body: str) -> bool:
            raise ConnectionError("RabbitMQ broker unavailable")

    publisher = OutboxPublisher(transport=FailingTransport(), max_retries=3)

    event = MockOutboxEvent(
        id=str(uuid.uuid4()),
        organization_id=str(uuid.uuid4()),
        event_type="purchase_request.submitted.v1",
        aggregate_type="PurchaseRequest",
        aggregate_id=str(uuid.uuid4()),
        payload=json.dumps({"test": "data"}),
        status="PENDING",
        retry_count=0,
    )
    db_session.add(event)
    db_session.commit()

    # Attempt 1 -> RETRY
    publisher.process_outbox_event(event, db_session)
    assert event.retry_count == 1
    assert event.status == "RETRY"

    # Attempt 2 -> RETRY
    publisher.process_outbox_event(event, db_session)
    assert event.retry_count == 2
    assert event.status == "RETRY"

    # Attempt 3 -> DEAD_LETTERED
    publisher.process_outbox_event(event, db_session)
    assert event.retry_count == 3
    assert event.status == "DEAD_LETTERED"
    assert "broker unavailable" in event.error_message
