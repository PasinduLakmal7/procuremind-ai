# Stage 2 Implementation Report: Core Procurement, Supplier and Document Management

**Project:** AI-Powered Procurement Intelligence Platform (Sri Lankan Manufacturing Domain)  
**Stage:** Stage 2 — Core Procurement, Supplier, and Document Management  
**Date:** 2026-11-06  
**Status:** Stage 2 Complete — Verified Across All Microservices & Ready for Stage 3  

---

## 1. Executive Summary

Stage 2 has been implemented in accordance with the architectural boundaries, multi-tenancy requirements, and data governance policies. The system delivers complete functional business capabilities for:
1. **Supplier Management:** Supplier directory, contact directory, categorization, historical delivery audits, quality incident tracking with provenance, and calculated performance metrics.
2. **Purchase Request Lifecycle:** Creation of drafts, item specifications with units and quantities, candidate supplier association, state-machine validation, and audit trail logging.
3. **Quotation Registration:** Supplier quotation records with item breakdown, pricing, lead time, and cross-service validation without direct cross-database queries.
4. **Quotation Document Service & Object Storage:** File uploads with format validation (`.pdf`, `.xlsx`, `.csv`, `.png`, `.jpg`), SHA-256 integrity checks, tenant directory scoping, and streaming file downloads.
5. **Transactional Outbox & Event-Driven Architecture:** Reliable business event publishing (`purchase_request.submitted.v1`, `quotation.document.uploaded.v1`), retry policy, dead-letter queue handling, and idempotent event consumer deduplication.
6. **Frontend Dashboard:** Interactive views in React 18 + Vite for suppliers, requests (with full detail modal and candidate assignment), and quotations.

---

## 2. Implemented Capabilities & Service Architecture

### 2.1 Supplier Service (`services/supplier-service`)
- **Independently Owned Database Entities:**
  - `suppliers`: Business profile, contact info, category, tax ID (VAT/SVAT), tier (`TIER_1` to `TIER_3`), compliance status, and soft-delete flag.
  - `supplier_contacts`: Primary and secondary corporate contact directory.
  - `supplier_categories`: Category taxonomies scoped by organization.
  - `supplier_delivery_records`: Audit entries of past PO deliveries (`po_reference`, `promised_delivery_date`, `actual_delivery_date`, `on_time`, `delay_days`, `source_system`, `recorded_by`). Provenance is strictly required.
  - `supplier_quality_records`: Incoming inspection batches (`batch_reference`, `defect_rate`, `incident_severity`, `passed`, `source_system`). Provenance is strictly required.
- **Performance Computation Engine:**
  - `GET /api/v1/supplier/suppliers/{id}/performance-summary`: Computes on-time delivery rate (%), average delay, quality pass rate, average defect rate, critical incidents count, and composite reliability score (0–5.0) exclusively from verified audit records.
- **Migrations:**
  - `0001_initial_tables.py`
  - `0002_supplier_profile_fields.py`
  - `0003_supplier_contacts_records_categories.py`

### 2.2 Procurement Service (`services/procurement-service`)
- **Independently Owned Database Entities:**
  - `purchase_requests`: Requirement numbers (`PR-2026-XXXX`), title, budget ceiling (LKR), category, priority, evaluation criteria, status.
  - `purchase_request_items`: Line items with item name, specification, quantity, unit of measure, and target unit price.
  - `candidate_suppliers`: Suppliers invited to quote on a purchase request (`supplier_id`, `supplier_name`, `invitation_status`).
  - `quotations`: Supplier quotes with reference numbers, versions, total cost, validity dates, payment terms, and linked document references.
  - `quotation_items`: Detailed line-item quotes with quantity, unit price, total, and lead time.
  - `procurement_audit_events`: Durable audit trail recording state transitions, draft modifications, item additions/removals, and user IDs.
  - `outbox_events`: Transactional outbox table storing integration events in the same DB transaction as business mutations.
- **State Machine Rules:**
  - Allowed statuses: `DRAFT`, `SUBMITTED`, `UNDER_EVALUATION`, `APPROVED`, `REJECTED`, `CANCELLED`.
  - Only `DRAFT` requests can have items added/removed or draft details edited.
  - Requests cannot be submitted without at least one line item.
  - Direct jumps (e.g. `DRAFT` -> `APPROVED`) are rejected with 422 Unprocessable Entity.
  - Submitting a request transactionally creates an outbox record for `purchase_request.submitted.v1`.
- **Migrations:**
  - `0001_initial_tables.py`
  - `0002_procurement_and_quotations.py`
  - `0003_procurement_items_candidates_outbox.py`

### 2.3 Quotation Document Service (`services/document-service`)
- **Independently Owned Database Entities:**
  - `document_records`: Metadata, file size, content type, SHA-256 checksum, relative storage path, status (`UPLOADED`, `PROCESSING`, `FAILED`, `ARCHIVED`), and optional references to `purchase_request_id` and `supplier_id`.
  - `document_outbox_events`: Transactional outbox table storing `quotation.document.uploaded.v1` events.
- **Storage Subsystem:**
  - Files stored in organization-scoped directories (`data/documents/{org_id}/{uuid}.{ext}`).
  - Validated file formats: `.pdf`, `.xlsx`, `.xls`, `.csv`, `.png`, `.jpg`, `.jpeg`.
  - Maximum file size: 25 MB.
  - Disallowed executables (`.exe`, `.bat`, etc.) rejected with 422.
- **Migrations:**
  - `0001_initial_tables.py`
  - `0002_document_metadata_fields.py`
  - `0003_document_outbox_events.py`

### 2.4 Event-Driven Outbox & Messaging Infrastructure (`shared/events`)
- **Event Contracts:**
  - `purchase_request.submitted.v1`: Contains PR ID, request number, organization, title, budget limit, submission timestamp, and submitter.
  - `quotation.document.uploaded.v1`: Contains document ID, organization, filename, size, checksum, and associations.
- **Reliable Outbox Publisher:**
  - Reads pending outbox records, formats into standard `EventEnvelope`, publishes to exchange `procurement.events.topic`, and transitions status to `PUBLISHED`.
  - Exponential backoff / retry policy (up to 3 retries) with transition to `DEAD_LETTERED` on permanent transport failures.
- **Idempotent Consumer:**
  - Deduplication guard ensuring redelivered messages are safely processed exactly once.

---

## 3. API Endpoints Reference

| Service | Method | Path | Description |
|---|---|---|---|
| **Supplier** | `POST` | `/api/v1/supplier/suppliers` | Register new industrial vendor |
| **Supplier** | `GET` | `/api/v1/supplier/suppliers` | List suppliers (filters: category, tier, compliance) |
| **Supplier** | `GET` | `/api/v1/supplier/suppliers/{id}` | Get supplier profile |
| **Supplier** | `PUT` | `/api/v1/supplier/suppliers/{id}` | Update supplier profile |
| **Supplier** | `DELETE` | `/api/v1/supplier/suppliers/{id}` | Soft-deactivate supplier |
| **Supplier** | `POST` | `/api/v1/supplier/suppliers/{id}/contacts` | Add supplier contact |
| **Supplier** | `GET` | `/api/v1/supplier/suppliers/{id}/contacts` | List supplier contacts |
| **Supplier** | `POST` | `/api/v1/supplier/suppliers/{id}/delivery-records` | Log historical delivery audit |
| **Supplier** | `POST` | `/api/v1/supplier/suppliers/{id}/quality-records` | Log quality inspection / incident |
| **Supplier** | `GET` | `/api/v1/supplier/suppliers/{id}/performance-summary` | Get computed performance metrics |
| **Procurement** | `POST` | `/api/v1/procurement/requests` | Create draft purchase request |
| **Procurement** | `GET` | `/api/v1/procurement/requests` | List purchase requests |
| **Procurement** | `GET` | `/api/v1/procurement/requests/{id}` | Get request summary |
| **Procurement** | `GET` | `/api/v1/procurement/requests/{id}/details` | Full details (items, candidates, audits) |
| **Procurement** | `PUT` | `/api/v1/procurement/requests/{id}` | Edit draft request |
| **Procurement** | `POST` | `/api/v1/procurement/requests/{id}/items` | Add line item to draft |
| **Procurement** | `DELETE` | `/api/v1/procurement/requests/{id}/items/{item_id}` | Remove line item |
| **Procurement** | `POST` | `/api/v1/procurement/requests/{id}/candidate-suppliers` | Associate candidate supplier |
| **Procurement** | `PATCH` | `/api/v1/procurement/requests/{id}/status` | Transition status (SUBMITTED queues outbox) |
| **Procurement** | `POST` | `/api/v1/procurement/requests/{id}/quotations` | Register supplier quotation |
| **Procurement** | `GET` | `/api/v1/procurement/requests/{id}/quotations` | List quotations for request |
| **Document** | `POST` | `/api/v1/document/documents/upload` | Upload quotation file (multipart) |
| **Document** | `GET` | `/api/v1/document/documents` | List organization documents |
| **Document** | `GET` | `/api/v1/document/documents/{id}` | Get document metadata |
| **Document** | `GET` | `/api/v1/document/documents/{id}/download` | Stream binary document file |

---

## 4. Test Verification Summary

All 24 test suites pass with zero regressions:

1. **`identity-service` (7/7 tests passed):**
   - User registration, login, token rotation, RBAC enforcement, and rate limiting.
2. **`supplier-service` (6/6 tests passed):**
   - Full CRUD, duplicate name rejection within organization, tenant isolation.
   - Contact association and category listing.
   - Historical delivery and quality records with mandatory provenance checking.
   - Authorized performance summary calculation.
3. **`procurement-service` (4/4 tests passed):**
   - Request creation in `DRAFT` status, `PR-2026-XXXX` sequencing, LKR budget ceilings.
   - Rejection of submission with 0 items; rejection of illegal state jumps.
   - Candidate supplier association and quotation registration.
   - Transactional `purchase_request.submitted.v1` outbox event persistence.
4. **`document-service` (4/4 tests passed):**
   - Multipart file upload and streaming download.
   - SHA-256 checksum verification.
   - Multiple format acceptance (`.pdf`, `.csv`, `.png`).
   - Rejection of invalid file extensions (`.exe`).
   - Cross-organization tenant isolation (404 rejection).
   - Transactional `quotation.document.uploaded.v1` outbox event persistence.
5. **Integration & Outbox (`tests/integration`, 3/3 tests passed):**
   - Reliable outbox processing and status transition from `PENDING` to `PUBLISHED`.
   - Exactly-once delivery guarantee using `IdempotentEventConsumer`.
   - Retry policy and dead-lettering to `DEAD_LETTERED` after exceeding max retries.
6. **Frontend SPA:**
   - Production bundle compiled with `tsc && vite build` (1571 modules transformed in 4.04s, 0 errors).

---

## 5. Known Limitations & Stage 3 Integration Requirements

1. **AI / OCR Extraction:** Quotation extraction is currently manual/placeholder; Stage 3 will introduce Document AI agents (OCR, line item parsing, confidence scoring).
2. **Multi-Agent Orchestrator:** LangGraph state machine will coordinate Document Intelligence and Supplier Evaluation agents in Stage 3.
3. **Broker Transport:** In local development without a running RabbitMQ container, `InMemoryMessageTransport` handles event routing; Docker deployment uses the RabbitMQ broker on port 5672.
