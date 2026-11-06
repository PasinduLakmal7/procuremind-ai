# Asynchronous Event Contracts & Messaging Topology

**Broker:** RabbitMQ 3.13 (AMQP 0-9-1)  
**Exchange Type:** Topic Exchange (`procurement.events`)  
**Dead-Letter Exchange:** `procurement.dlx`  
**Pattern:** Transactional Outbox Pattern  

---

## 1. Message Structure Standard

All domain events published over RabbitMQ follow a uniform JSON schema:

```json
{
  "event_id": "c8a4173e-3cb8-4bc2-8f92-5ebaa0fdf441",
  "event_type": "purchase_request.submitted.v1",
  "aggregate_type": "PurchaseRequest",
  "aggregate_id": "0f90c102-1811-477c-8d59-3a3c988be08a",
  "organization_id": "11111111-1111-1111-1111-111111111111",
  "correlation_id": "corr-88319-994",
  "timestamp": "2026-11-06T14:30:00Z",
  "payload": {
    "purchase_request_id": "0f90c102-1811-477c-8d59-3a3c988be08a",
    "request_number": "PR-2026-0001",
    "title": "CNC Milling Tooling",
    "budget_limit": 1200000.0,
    "currency": "LKR",
    "submitted_by": "22222222-2222-2222-2222-222222222222"
  }
}
```

---

## 2. Event Catalog & Routing Keys

| Routing Key | Producing Service | Consuming Workers / Services | Description |
|---|---|---|---|
| `purchase_request.submitted.v1` | `procurement-service` | `ai-orchestrator-service` | Triggered when a PR transitions from `DRAFT` to `SUBMITTED`. |
| `document.uploaded.v1` | `document-service` | `document-worker` | Triggers Celery background task for asynchronous OCR extraction. |
| `document.verified.v1` | `document-service` | `ai-orchestrator-service` | Resumes paused multi-agent workflow after officer verification. |
| `purchase_request.decision_recorded.v1` | `procurement-service` | Notification service, audit bus | Broadcasts manager's final `APPROVED` or `REJECTED` action. |

---

## 3. Reliability & Dead-Letter Handling

1. **Transactional Outbox:**
   - Database events are written into `outbox_events` in the same database transaction as the business entity.
   - A background publisher polls pending outbox records and delivers them to RabbitMQ.
2. **Idempotency Guarantee:**
   - Consumers store `processed_event_ids` to discard duplicate transmissions.
3. **Dead-Letter Queue (DLQ):**
   - Unhandled exceptions trigger message rejection with `requeue=False`, routing failing payloads to `procurement.dlx` and queue `procurement.dead_letter` for manual inspection.

