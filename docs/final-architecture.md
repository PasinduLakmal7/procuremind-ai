# Final Architecture Specification: Procurement Intelligence Platform

**Project:** AI-Powered Procurement Intelligence Platform  
**Target Domain:** Sri Lankan Manufacturing Industry  
**Architectural Style:** Microservices + Multi-Agent AI + Event-Driven Processing  
**Document Status:** Production Architecture (Final Release)  

---

## 1. System Architecture Overview

The platform is designed around strict bounded contexts with independent database-per-service ownership, stateless JWT authentication, asynchronous event-driven messaging, and stateful multi-agent AI orchestration:

```
+-----------------------------------------------------------------------------------------+
|                               React 18 + TypeScript SPA                                 |
|          Procurement Dashboard • Quotation OCR • Risk Studio • Approval Gate            |
+-----------------------------------------------------------------------------------------+
                                             | HTTP (Port 80)
                                             v
+-----------------------------------------------------------------------------------------+
|                              Traefik v3.0 API Gateway                                   |
|                Path Routing • TLS Termination • Correlation ID Injection                |
+-----------------------------------------------------------------------------------------+
      |               |              |              |              |              |
      | /identity     | /procurement | /supplier    | /document    | /risk        | /optimization
      v               v              v              v              v              v
+------------+ +------------+ +------------+ +------------+ +------------+ +------------+
|  Identity  | |Procurement | |  Supplier  | |  Document  | |    Risk    | |Optimization|
|  Service   | |  Service   | |  Service   | |  Service   | |  Service   | |  Service   |
| (Port 8001)| | (Port 8002)| | (Port 8003)| | (Port 8004)| | (Port 8006)| | (Port 8007)|
+------------+ +------------+ +------------+ +------------+ +------------+ +------------+
      |               |              |              |              |              |
      |               |              |              +-------+      |              |
      |               |              |                      |      |              |
      v               v              v                      v      v              v
  [Postgres]      [Postgres]     [Postgres]             [Postgres][Postgres]  [Postgres]
 (identity_db)  (procurement_db)(supplier_db)          (doc_db)  (risk_db)   (opt_db)
                                                            |
                                                            v
                                                        [MinIO S3]
                                                  (quotation-documents)

                                       +-----------------------+
                                       |  AI Orchestrator Svc  |
                                       | (LangGraph Engine)    |
                                       |      (Port 8005)      |
                                       +-----------------------+
                                                   |
                                                   v
                                               [Postgres]
                                         (ai_orchestrator_db)
                                                   |
                   +-------------------------------+-------------------------------+
                   |                                                               |
                   v                                                               v
         [RabbitMQ Event Bus]                                             [Celery Workers]
 (Events: submitted, verified, decided)                             (document-worker: OCR & parsing)
```

---

## 2. Microservice Boundaries & Responsibilities

### 2.1 Identity Service (`services/identity-service`)
- **Port:** 8001 | **Database:** `identity_db`
- **Responsibilities:** User authentication, password hashing (Argon2 / bcrypt), JWT issuance and validation, refresh token rotation, and multi-tenant organization directory.
- **Roles:** `PROCUREMENT_OFFICER`, `MANAGER`, `ADMIN`.

### 2.2 Procurement Service (`services/procurement-service`)
- **Port:** 8002 | **Database:** `procurement_db`
- **Responsibilities:** Purchase request (PR) lifecycle management (`DRAFT`, `SUBMITTED`, `UNDER_EVALUATION`, `APPROVED`, `REJECTED`), line item specifications, candidate supplier invitations, quotation registration, and human approval decision gates.
- **Pattern:** Transactional Outbox pattern guaranteeing atomic database persistence and RabbitMQ event publication.

### 2.3 Supplier Service (`services/supplier-service`)
- **Port:** 8003 | **Database:** `supplier_db`
- **Responsibilities:** Supplier registry, categories, contact management, historical delivery logs (promised vs actual dates), quality inspection records, and defect incident tracking.
- **Governance:** Strict provenance tracking; missing supplier performance data is never fabricated.

### 2.4 Document Service (`services/document-service`)
- **Port:** 8004 | **Database:** `document_db` | **Object Storage:** MinIO S3
- **Responsibilities:** Quotation document storage, multi-format parsing (PDF, CSV, XLSX, scanned images), structured line-item extraction with evidence references, arithmetic verification, and human verification audit logs (`extraction_correction_audits`).

### 2.5 Risk Service (`services/risk-service`)
- **Port:** 8006 | **Database:** `risk_db`
- **Responsibilities:** Transparent, deterministic supplier risk evaluation baseline. Assesses historical delay frequency, lateness severity, order fulfillment deficits, quality defect rates, and critical incidents.
- **Governance:** Enforces `INSUFFICIENT_DATA` rule if observation count $< 3$. Includes an L2-regularized Logistic Regression predictive pipeline (`ml-logistic-v1.0`).

### 2.6 Optimization Service (`services/optimization-service`)
- **Port:** 8007 | **Database:** `optimization_db`
- **Responsibilities:** Multi-Criteria Decision Analysis (MCDA) quotation ranking. Filters mandatory constraints (budget ceilings, maximum lead times, disqualified vendors) before applying weighted ranking across Cost (40%), Delivery (25%), Quality (20%), and Reliability (15%).

### 2.7 AI Orchestrator Service (`services/ai-orchestrator-service`)
- **Port:** 8005 | **Database:** `ai_orchestrator_db`
- **Responsibilities:** Coordinates stateful multi-agent workflows using a 7-node LangGraph-style state machine:
  1. `document_intelligence`: Ingests and verifies parsed data.
  2. `validation_and_human_review`: Checkpoint that interrupts and pauses execution at `WAITING_FOR_HUMAN_REVIEW` if confidence $< 0.85$ or if unverified.
  3. `supplier_analysis`: Analyzes vendor performance history.
  4. `risk_assessment`: Deterministic risk baseline evaluation.
  5. `procurement_optimization`: Multi-criteria quotation ranking.
  6. `policy_explanation`: Generates Explainable AI rationale and verifies Sri Lankan 8% VAT statutory compliance.
  7. `decision_preparation`: Packages recommendation dossier for human approval.

---

## 3. Communication Protocols & Security Model

1. **Stateless JWT Authorization:** Every internal cross-service and external gateway request carries signed JWT claims (`sub`, `organization_id`, `roles`).
2. **Multi-Tenancy Isolation:** All SQL queries are scoped strictly by `organization_id`.
3. **Adversarial Input Defense:** Input documents undergo regex sanitization (`[REDACTED_ADVERSARIAL_INSTRUCTION]`) to neutralize prompt injection attacks.
4. **Human-in-the-Loop Governance:** AI agents generate inspectable recommendations; only an authorized Human Procurement Manager can approve expenditure and commit funds.

