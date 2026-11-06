# Database Architecture & Schema Specification

**Project:** AI-Powered Procurement Intelligence Platform  
**Target RDBMS:** PostgreSQL 16 (Independent Database-Per-Service)  
**Migration Framework:** Alembic  

---

## 1. Database-Per-Service Mapping

| Microservice | Database Name | Primary Tables |
|---|---|---|
| `identity-service` | `identity_db` | `organizations`, `users`, `roles`, `user_roles`, `refresh_tokens` |
| `supplier-service` | `supplier_db` | `suppliers`, `supplier_contacts`, `supplier_categories`, `supplier_delivery_records`, `supplier_quality_records` |
| `procurement-service` | `procurement_db` | `purchase_requests`, `purchase_request_items`, `candidate_suppliers`, `quotations`, `quotation_items`, `procurement_audit_events`, `outbox_events` |
| `document-service` | `document_db` | `document_records`, `quotation_extractions`, `extraction_correction_audits`, `document_outbox_events` |
| `ai-orchestrator-service` | `ai_orchestrator_db` | `agent_workflow_executions`, `workflow_step_logs` |
| `risk-service` | `risk_db` | `supplier_risk_profiles`, `risk_assessments` |
| `optimization-service` | `optimization_db` | `optimization_scenarios` |

---

## 2. Table Schemas & Key Columns

### 2.1 `identity_db`
- `organizations`: `id (CHAR(36) PK)`, `name`, `tax_id`, `domain`, `is_active`, `created_at`.
- `users`: `id (CHAR(36) PK)`, `organization_id (CHAR(36) FK)`, `email`, `hashed_password`, `full_name`, `is_active`.
- `refresh_tokens`: `id`, `user_id`, `token_hash`, `expires_at`, `revoked`.

### 2.2 `supplier_db`
- `suppliers`: `id (CHAR(36) PK)`, `organization_id`, `company_name`, `contact_email`, `contact_phone`, `city`, `country`, `category`, `tier`, `rating`, `compliance_status`.
- `supplier_delivery_records`: `id`, `supplier_id`, `order_reference`, `promised_delivery_date`, `actual_delivery_date`, `is_delayed`, `lateness_days`, `fulfillment_rate`.
- `supplier_quality_records`: `id`, `supplier_id`, `inspection_reference`, `inspection_date`, `defect_rate`, `severity` (LOW, MEDIUM, HIGH, CRITICAL).

### 2.3 `procurement_db`
- `purchase_requests`: `id (CHAR(36) PK)`, `organization_id`, `created_by_user_id`, `request_number`, `title`, `description`, `category`, `priority`, `budget_limit`, `currency`, `required_delivery_date`, `status` (DRAFT, SUBMITTED, UNDER_EVALUATION, APPROVED, REJECTED, CANCELLED).
- `purchase_request_items`: `id`, `purchase_request_id (FK)`, `item_name`, `quantity`, `unit_of_measure`, `target_unit_price`.
- `quotations`: `id`, `purchase_request_id (FK)`, `supplier_id`, `quotation_number`, `total_cost`, `currency`, `estimated_delivery_days`, `status` (RECEIVED, UNDER_REVIEW, ACCEPTED, REJECTED).
- `procurement_audit_events`: `id`, `purchase_request_id (FK)`, `event_type`, `performed_by`, `old_state`, `new_state`, `details`.
- `outbox_events`: `id`, `organization_id`, `event_type`, `aggregate_type`, `aggregate_id`, `payload`, `status` (PENDING, PUBLISHED, FAILED), `retry_count`.

### 2.4 `document_db`
- `document_records`: `id`, `organization_id`, `file_name`, `file_size`, `content_type`, `storage_path`, `storage_bucket`, `status`.
- `quotation_extractions`: `id`, `document_id (FK)`, `supplier_name`, `quotation_number`, `currency`, `total_cost`, `line_items_json`, `overall_confidence`, `arithmetic_valid`, `is_verified`.
- `extraction_correction_audits`: `id`, `extraction_id (FK)`, `field_name`, `old_value`, `new_value`, `corrected_by`, `created_at`.

### 2.5 `risk_db`
- `risk_assessments`: `id`, `organization_id`, `supplier_id`, `supplier_name`, `risk_score`, `risk_category` (LOW, MEDIUM, HIGH, CRITICAL, INSUFFICIENT_DATA), `confidence`, `data_sufficiency`, `observation_count`, `metrics_breakdown (JSON)`, `model_version`, `explanation`.

### 2.6 `optimization_db`
- `optimization_scenarios`: `id`, `organization_id`, `request_id`, `algorithm`, `total_evaluated`, `top_supplier_id`, `weights_json`, `rankings_json`, `decision_summary`.

### 2.7 `ai_orchestrator_db`
- `agent_workflow_executions`: `id`, `correlation_id`, `organization_id`, `purchase_request_id`, `status`, `current_step`, `requires_human_review`, `human_review_reason`, `state_snapshot (JSON)`.
- `workflow_step_logs`: `id`, `workflow_id (FK)`, `step_name`, `status`, `output_data`.

---

## 3. Migration Commands

To execute schema migrations offline or against local PostgreSQL:
```bash
# Identity Service
cd services/identity-service && alembic upgrade head

# Procurement Service
cd services/procurement-service && alembic upgrade head

# Supplier Service
cd services/supplier-service && alembic upgrade head

# Document Service
cd services/document-service && alembic upgrade head

# AI Orchestrator Service
cd services/ai-orchestrator-service && alembic upgrade head

# Risk Service
cd services/risk-service && alembic upgrade head

# Optimization Service
cd services/optimization-service && alembic upgrade head
```
