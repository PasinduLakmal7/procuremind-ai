"""Reliable Outbox Publisher and Idempotent Consumer framework."""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set
from shared.event_contracts.envelope import EventEnvelope

logger = logging.getLogger(__name__)


class MessageTransport:
    """Abstract interface for messaging transport."""
    def publish(self, exchange: str, routing_key: str, message_body: str) -> bool:
        raise NotImplementedError


class InMemoryMessageTransport(MessageTransport):
    """In-memory messaging transport for fast and reliable testing and verification."""
    def __init__(self):
        self.published_messages: List[Dict[str, Any]] = []
        self.dead_letter_queue: List[Dict[str, Any]] = []

    def publish(self, exchange: str, routing_key: str, message_body: str) -> bool:
        self.published_messages.append({
            "exchange": exchange,
            "routing_key": routing_key,
            "body": message_body,
            "published_at": datetime.now(timezone.utc).isoformat(),
        })
        return True


class OutboxPublisher:
    """Processes pending outbox events from a repository, publishes them to transport, and updates status."""
    def __init__(self, transport: MessageTransport, max_retries: int = 3):
        self.transport = transport
        self.max_retries = max_retries

    def process_outbox_event(self, event, db_session) -> bool:
        """Processes a single outbox record with retry policy and dead-letter handling."""
        try:
            payload_data = json.loads(event.payload) if isinstance(event.payload, str) else event.payload
            envelope = EventEnvelope(
                event_type=event.event_type,
                producer=event.aggregate_type,
                payload=payload_data,
                metadata={"aggregate_id": event.aggregate_id, "organization_id": event.organization_id},
            )
            body_json = envelope.model_dump_json()

            routing_key = event.event_type
            exchange = "procurement.events.topic"

            success = self.transport.publish(exchange=exchange, routing_key=routing_key, message_body=body_json)
            if success:
                event.status = "PUBLISHED"
                event.published_at = datetime.now(timezone.utc)
                event.error_message = None
                db_session.commit()
                return True
            else:
                raise RuntimeError("Transport failed to acknowledge receipt")

        except Exception as exc:
            event.retry_count += 1
            event.error_message = str(exc)
            if event.retry_count >= self.max_retries:
                event.status = "DEAD_LETTERED"
                logger.error(f"Outbox event {event.id} dead-lettered after {event.retry_count} retries: {exc}")
            else:
                event.status = "RETRY"
            db_session.commit()
            return False


class IdempotentEventConsumer:
    """Ensures each event is processed exactly once even when redelivered."""
    def __init__(self):
        self._processed_event_ids: Set[str] = set()

    def process(self, envelope: EventEnvelope, handler: Callable[[EventEnvelope], None]) -> bool:
        if envelope.event_id in self._processed_event_ids:
            logger.info(f"Duplicate event {envelope.event_id} ignored (idempotent guard).")
            return False

        handler(envelope)
        self._processed_event_ids.add(envelope.event_id)
        return True

    def is_processed(self, event_id: str) -> bool:
        return event_id in self._processed_event_ids

