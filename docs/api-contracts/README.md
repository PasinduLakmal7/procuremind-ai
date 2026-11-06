# Microservices REST API Contracts Catalog

All microservices are exposed through the Traefik Gateway under the base path `/api/v1/<service-name>`.

---

## 1. Identity Service (`/api/v1/identity`)

- `POST /auth/register`: Register new user and organization.
- `POST /auth/login`: Issue access and refresh tokens.
- `POST /auth/refresh`: Refresh access token via valid refresh token.
- `POST /auth/logout`: Revoke active refresh token.
- `GET /auth/me`: Retrieve authenticated user identity, organization, and roles.

---

## 2. Supplier Service (`/api/v1/supplier`)

- `POST /suppliers`: Register new supplier vendor.
- `GET /suppliers`: List suppliers with optional category filter.
- `GET /suppliers/{id}`: Retrieve detailed supplier record.
- `POST /suppliers/{id}/delivery-records`: Record historical order delivery outcome.
- `POST /suppliers/{id}/quality-records`: Record quality inspection or defect report.
- `GET /suppliers/{id}/performance-summary`: Retrieve historical delivery and quality averages.

---

## 3. Procurement Service (`/api/v1/procurement`)

- `POST /requests`: Create draft purchase request.
- `GET /requests`: List purchase requests with status filter.
- `GET /requests/{id}/details`: Get purchase request with line items, candidates, and audit events.
- `POST /requests/{id}/items`: Add line item to draft purchase request.
- `DELETE /requests/{id}/items/{item_id}`: Remove item from draft purchase request.
- `PATCH /requests/{id}/status`: Transition status (`DRAFT` → `SUBMITTED`, etc.).
- `POST /requests/{id}/candidate-suppliers`: Associate invited vendor.
- `POST /requests/{id}/quotations`: Register quotation and line items.
- `GET /requests/{id}/quotations`: List submitted quotations for a request.
- `POST /requests/{id}/decision`: Record Human Manager decision (`APPROVE` or `REJECT`) with auditable reason.

---

## 4. Document Service (`/api/v1/document`)

- `POST /documents/upload`: Upload quotation file (PDF, CSV, XLSX, image).
- `GET /documents/{id}`: Retrieve document metadata and file download URL.
- `POST /documents/{id}/extract`: Trigger document intelligence parsing.
- `GET /documents/{id}/extraction`: Retrieve parsed quotation data, evidence, and arithmetic check.
- `PUT /documents/{id}/extraction`: Save officer corrections to extracted fields.
- `POST /documents/{id}/verify`: Confirm and certify quotation extraction as human-verified.

---

## 5. Risk Service (`/api/v1/risk`)

- `POST /risk/evaluate`: Evaluate deterministic supplier risk baseline. Enforces `INSUFFICIENT_DATA` if observations $< 3$.
- `GET /risk/suppliers/{supplier_id}`: Retrieve latest computed risk assessment for vendor.
- `GET /risk/assessments/{assessment_id}`: Retrieve risk assessment by ID.
- `GET /risk/ml/status`: Inspect ML pipeline model version, training sample size, metrics, and limitations.

---

## 6. Optimization Service (`/api/v1/optimization`)

- `POST /optimization/rank`: Perform MCDA ranking across candidate quotations with customizable criteria weights and constraints.
- `GET /optimization/scenarios/{id}`: Retrieve saved optimization scenario.
- `GET /optimization/requests/{request_id}`: Retrieve latest optimization run for a purchase request.

---

## 7. AI Orchestrator Service (`/api/v1/ai-orchestrator`)

- `POST /workflows/start`: Initiate 7-node LangGraph multi-agent procurement evaluation.
- `GET /workflows/{id}/status`: Poll workflow progress, current node, review triggers, and state snapshots.
- `POST /workflows/{id}/resume`: Resume paused workflow after human verification.

