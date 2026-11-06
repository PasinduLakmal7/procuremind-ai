# Stage 3 Implementation Report: Document Intelligence, AI Orchestration and Human Verification

**Project:** AI-Powered Procurement Intelligence Platform (Sri Lankan Manufacturing Domain)  
**Stage:** Stage 3 — Document Intelligence, AI Orchestration and Human Verification  
**Date:** 2026-11-06  
**Status:** Stage 3 Complete — Verified Across All Microservices & Ready for Stage 4  

---

## 1. Executive Summary

Stage 3 has established the AI extraction and multi-agent workflow orchestration layer. The platform now ingests supplier quotations across diverse formats, extracts structured line items with evidence references, validates arithmetic integrity, flags uncertainties and adversarial prompt injections, provides a human-in-the-loop verification UI, and coordinates a LangGraph-style 7-node state machine with PostgreSQL checkpoint persistence.

---

## 2. Implemented Capabilities & Architecture

### 2.1 Multi-Format Document Processing Pipeline (`shared/extraction`)
- **Supported Formats:**
  - Digital text PDFs (`.pdf`): native stream decompression and text operator extraction.
  - Scanned PDFs & Images (`.png`, `.jpg`, `.jpeg`): pattern extraction and simulated OCR heuristic.
  - Spreadsheets (`.csv`, `.xlsx`, `.xls`): native CSV parsing and zip XML worksheet parsing.
- **Adversarial Prompt Injection Defense:**
  - Scans untrusted document content for jailbreaks/system prompt override phrases (`IGNORE ALL PREVIOUS INSTRUCTIONS`, `SYSTEM: OVERRIDE`, `GRANT ADMIN`).
  - Redacts matched payloads and logs high-priority security warnings in `flagged_reasons`.
- **Arithmetic Verification Engine:**
  - Recomputes item total price (`quantity * unit_price`).
  - Compares sum of line items against stated subtotal and quotation total.
  - Discrepancies > 5.0 absolute or > 5% trigger `arithmetic_valid = False` with explicit warning messages.
- **Confidence Scoring Model:**
  - Base confidence (0.95), with transparent deductions:
    - Missing supplier name: -0.20
    - Missing quotation reference: -0.15
    - Arithmetic inconsistency: -0.25
    - Scanned/OCR formats: -0.10

### 2.2 Quotation Extraction & Human Review Lifecycle (`services/document-service`)
- **Independently Owned Database Entities:**
  - `quotation_extractions`: Stores extracted supplier name, quotation number, currency, total cost, line items JSON, evidence references, confidence scores, and verification status (`is_verified`).
  - `extraction_correction_audits`: Durable audit trail recording human modifications (`field_name`, `old_value`, `new_value`, `corrected_by`, timestamp).
- **Human Verification Workflow:**
  1. `POST /api/v1/document/documents/{id}/extract` parses document and returns structured extraction.
  2. `GET /api/v1/document/documents/{id}/extraction` retrieves extraction, evidence, and warnings.
  3. `PUT /api/v1/document/documents/{id}/extraction` allows authorized officer to correct field values with audit logging.
  4. `POST /api/v1/document/documents/{id}/verify` confirms data as verified (`is_verified = True`), updating document status to `VERIFIED`.
- **Alembic Migration:** `0004_doc_extractions.py` verified for PostgreSQL DDL.

### 2.3 LangGraph Multi-Agent Orchestrator (`services/ai-orchestrator-service`)
- **Workflow State Machine Nodes:**
  1. `document_intelligence`: Validates presence of structured extraction.
  2. `validation_and_human_review`: Checks `is_verified`, `overall_confidence >= 0.85`, and `arithmetic_valid`. If unverified or confidence is low, pauses workflow at `WAITING_FOR_HUMAN_REVIEW` with descriptive reason.
  3. `supplier_analysis`: Analyzes vendor tier and performance history.
  4. `risk_assessment`: Evaluates delivery and quality risk (Stage 4 typed interface contract).
  5. `procurement_optimization`: Benchmarks quotation cost against PR budget limit (Stage 4 typed interface contract).
  6. `policy_explanation`: Validates organizational procurement policies (e.g. Sri Lankan 8% VAT verification).
  7. `decision_preparation`: Prepares final recommendation dossier and transitions to `COMPLETED`.
- **Checkpointer & Persistence:**
  - State snapshot saved to `agent_workflow_executions.state_snapshot` after every node transition.
  - Individual step transitions logged to `workflow_step_logs`.
  - State persists safely across service and database restarts.
- **Resume Capability:**
  - `POST /api/v1/ai-orchestrator/workflows/{id}/resume` resumes a paused workflow once human verification has confirmed the extraction.
- **Alembic Migration:** `0002_orchestrator_checkpoints.py` verified for PostgreSQL DDL.

### 2.4 Asynchronous Worker Tasks (`workers/document-worker`)
- Celery worker configured for asynchronous background extraction (`tasks.process_document_extraction`).
- RabbitMQ broker and Redis result backend integration with retry policy (3 retries).

### 2.5 React Review Interface (`frontend/procurement-dashboard`)
- [`QuotationsPage.tsx`](file:///e:/semester%204/Projects/wify/chamodi/project/frontend/procurement-dashboard/src/pages/QuotationsPage.tsx):
  - Document intake and listing with real-time status badges (`UPLOADED`, `EXTRACTED`, `VERIFIED`).
  - "Review & Verify AI" modal:
    - Overall confidence score percentage.
    - Arithmetic consistency badge (green check or red warning).
    - Flagged review reasons and security alerts.
    - Editable fields for supplier name, quotation number, and total cost with audit logging.
    - One-click "Confirm & Verify" button.
    - "Run AI Workflow" and "Resume AI Workflow" controls displaying state machine progression and recommendation dossiers.
- Production build verified: `npm run build` succeeds (1571 modules transformed in 2.54s, 0 errors).

---

## 3. Measured Fixture Extraction Results

Evaluated against test fixtures in `tests/fixtures/documents/`:

| Fixture File | Type | Expected Result | Actual Measured Result | Status |
|---|---|---|---|---|
| `valid_quotation.csv` | CSV | 2 line items, valid math, confidence >= 0.90 | Extracted 2 items (Steel Angle, Channel), math valid, confidence 95% | **PASSED** |
| `inconsistent_totals.csv` | CSV | Mismatch: items sum 270k vs stated 999k | `arithmetic_valid = False`, flagged mismatch warning, confidence 70% | **PASSED** |
| `missing_fields.csv` | CSV | Missing supplier & quote number | Flagged missing supplier and quotation number, confidence 60% | **PASSED** |
| `malicious_prompt_injection.csv` | CSV | Injected prompt override command | Injected text redacted, security alert flagged in review warnings | **PASSED** |
| `digital_quotation.pdf` | Digital PDF | Extracted supplier, quote ref, total | "Ceylon Structural Engineering", "QUO-CSE-2026-105", 1.25M LKR | **PASSED** |

---

## 4. Test Verification Summary

- **`identity-service`:** 7/7 tests passed
- **`supplier-service`:** 6/6 tests passed
- **`procurement-service`:** 4/4 tests passed
- **`document-service`:** 6/6 tests passed (upload, download, extraction, human edits, prompt injection defense)
- **`ai-orchestrator-service`:** 4/4 tests passed (workflow start, human review pause, state snapshot, workflow resume)
- **`tests/integration`:** 8/8 tests passed (outbox event publishing, idempotent consumer, document intelligence fixtures)
- **Total Passing Tests:** **35/35 tests passed**

---

## 5. Stage 4 Integration Contracts

Stage 3 provides the verified inputs and typed interface contracts for Stage 4:
1. `RiskAssessmentResult`:
   - `supplier_risk_tier`: TIER_1 / TIER_2 / TIER_3
   - `on_time_delivery_probability`: float (0.0 to 1.0)
   - `defect_risk_score`: float (0.0 to 1.0)
   - `financial_stability_index`: float (0.0 to 1.0)
2. `OptimizationResult`:
   - `recommended_ranking`: int
   - `cost_variance_vs_budget`: float
   - `within_budget`: bool
   - `suggested_allocation_percentage`: float
3. `PolicyValidationResult`:
   - `policy_compliant`: bool
   - `sri_lanka_vat_checked`: bool
   - `notes`: List[str]

Stage 4 will implement real risk models (`risk-service`) and linear/heuristic multi-criteria optimization (`optimization-service`) to replace these preview contracts without changing the API signatures.

