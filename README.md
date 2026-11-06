# AI-Powered Procurement Intelligence Platform

**Domain:** Sri Lankan Manufacturing Industry  
**Architecture:** Microservices + Multi-Agent AI + Event-Driven Processing  
**Current Milestone:** Stage 5 Complete — Fully Integrated Production Platform (Verified)  

---

## 1. Project Overview

The **Procurement Intelligence Platform** is an explainable decision-support system tailored for manufacturing enterprises. It streamlines the evaluation of supplier quotations, historical fulfillment reliability, and supply chain delivery risks through a coordinated multi-agent artificial intelligence framework while maintaining strict **human-in-the-loop accountability**.

Final purchasing authority, contract signing, and payment authorization remain exclusively in the hands of authorized human procurement managers.

---

## 2. Microservices Architecture

The system utilizes an independently deployable microservices architecture governed by the **Database-per-Service** ownership pattern:

```
                            +-----------------------------+
                            |   React + TS Frontend SPA   |
                            |     (Port 5173 / Port 80)   |
                            +--------------+--------------+
                                           |
                                           v
                            +-----------------------------+
                            |     Traefik API Gateway     |
                            |          (Port 80)          |
                            +--------------+--------------+
                                           |
       +-----------------------------------+-----------------------------------+
       |              |              |              |              |           |
       v              v              v              v              v           v
+--------------+ +-----------+ +-----------+ +-----------+ +---------------+ +------+
|   Identity   | |Procurement| | Supplier  | | Document  | |AI Orchestrator| | Risk | ... [Optimization]
|   Service    | |  Service  | |  Service  | |  Service  | |    Service    | |      |
|  (Port 8001) | |(Port 8002)| |(Port 8003)| |(Port 8004)| |  (Port 8005)  |(8006) |
+-------+------+ +-----+-----+ +-----+-----+ +-----+-----+ +-------+-------+ +---+--+
        |              |             |             |               |             |
        v              v             v             v               v             v
  [identity_db] [procurement_db][supplier_db][document_db] [ai_orchestrator_db] [risk_db]
```

### Services Breakdown

| Service | Internal Port | Gateway Route Prefix | Database | Primary Responsibility |
|---|---|---|---|---|
| **Identity Service** | `8001` | `/api/v1/identity` | `identity_db` | Authentication, organization tenancy, user management, and RBAC |
| **Procurement Service** | `8002` | `/api/v1/procurement` | `procurement_db` | Purchase requests, line items, quotations, human manager decisions, and outbox events |
| **Supplier Service** | `8003` | `/api/v1/supplier` | `supplier_db` | Supplier registry, historical delivery logs, quality defect records, and performance summary |
| **Document Service** | `8004` | `/api/v1/document` | `document_db` | Quotation document storage, multi-format OCR extraction, and human review verification |
| **AI Orchestrator Service** | `8005` | `/api/v1/ai-orchestrator` | `ai_orchestrator_db` | 7-node LangGraph multi-agent orchestration, review pause/resume, and explainable recommendations |
| **Risk Service** | `8006` | `/api/v1/risk` | `risk_db` | Deterministic risk scoring baseline, insufficient data rules (< 3 obs), and ML pipeline |
| **Optimization Service** | `8007` | `/api/v1/optimization` | `optimization_db` | Multi-Criteria Decision Analysis (MCDA), constraint filtering, and quotation ranking |

---

## 3. Key Completed Capabilities

1. **Stateless JWT Security & Multi-Tenancy:** Automated role enforcement (`PROCUREMENT_OFFICER`, `MANAGER`) and complete organization isolation.
2. **Multi-Format Quotation Extractor:** Ingestion of digital PDFs, spreadsheets (CSV/XLSX), and scanned receipts with arithmetic consistency checks.
3. **Adversarial Prompt Injection Defense:** Untrusted document payloads are automatically sanitized (`[REDACTED_ADVERSARIAL_INSTRUCTION]`).
4. **Deterministic Supplier Risk Engine:** Transparent scoring evaluating delay frequency, average lateness, fulfillment deficits, defect rates, and critical incidents. Disallows hallucinated probabilities when data is sparse.
5. **Multi-Criteria Optimization (MCDA):** Mathematical normalization scoring across Cost (40%), Delivery (25%), Quality (20%), and Reliability (15%) with constraint filtering.
6. **Statutory Adherence:** Quotations automatically verified against Sri Lankan statutory 8% VAT standards.
7. **Human Decision Gate:** AI cannot commit organizational funds autonomously; all awards require explicit Human Procurement Manager sign-off with audit logging.
8. **React Dashboard SPA:** Complete web interface with live KPI overview, RFQ management, vendor directory, OCR verification modal, Risk Studio, and Audit Explorer.

---

## 4. Documentation Catalog

- **Final Architecture:** [docs/final-architecture.md](docs/final-architecture.md)
- **Database Design & Schemas:** [docs/database-design.md](docs/database-design.md)
- **REST API Contracts Catalog:** [docs/api-contracts/README.md](docs/api-contracts/README.md)
- **RabbitMQ Event Contracts:** [docs/event-contracts/README.md](docs/event-contracts/README.md)
- **Testing & Benchmark Evaluation:** [docs/testing-and-evaluation.md](docs/testing-and-evaluation.md)
- **Deployment & Operations Runbook:** [docs/deployment-guide.md](docs/deployment-guide.md)
- **Known Limitations & Boundaries:** [docs/known-limitations.md](docs/known-limitations.md)
- **Stage 1 Recovery Report:** [docs/agent-handoffs/stage-1-recovery.md](docs/agent-handoffs/stage-1-recovery.md)
- **Stage 2 Report:** [docs/agent-handoffs/stage-2-report.md](docs/agent-handoffs/stage-2-report.md)
- **Stage 3 Report:** [docs/agent-handoffs/stage-3-report.md](docs/agent-handoffs/stage-3-report.md)
- **Stage 4 Report:** [docs/agent-handoffs/stage-4-report.md](docs/agent-handoffs/stage-4-report.md)
- **Stage 5 Report:** [docs/agent-handoffs/stage-5-report.md](docs/agent-handoffs/stage-5-report.md)
| **Procurement Service** | `8002` | `/api/v1/procurement` | `procurement_db` | Purchase requests, budget ceilings, requirements, and orders |
| **Supplier Service** | `8003` | `/api/v1/supplier` | `supplier_db` | Supplier directory, performance history, delivery records |
| **Document Service** | `8004` | `/api/v1/document` | `document_db` | S3/MinIO quotation document storage, validation, metadata |
| **AI Orchestrator** | `8005` | `/api/v1/ai-orchestrator` | `ai_orchestrator_db` | LangGraph state machines, multi-agent evaluation workflows |
| **Risk Service** | `8006` | `/api/v1/risk` | `risk_db` | Historical delivery delay & quality risk model inference |
| **Optimization Service** | `8007` | `/api/v1/optimization` | `optimization_db` | Multi-objective scoring, Pareto ranking, constraint satisfaction |

---

## 3. Technology Stack

- **Frontend:** React 18, TypeScript, Vite, React Router v6, Axios, Lucide Icons
- **Edge Gateway:** Traefik v3 (reverse proxy, path prefix routing, rate limiting, security headers)
- **Backend Microservices:** Python 3.12, FastAPI, Pydantic v2, Pydantic Settings
- **Persistence & Migrations:** PostgreSQL 16 (service-owned databases), SQLAlchemy 2.0, Alembic
- **Caching & Messaging:** Redis 7 (cache/task backend), RabbitMQ 3.13 (event broker)
- **Background Tasks:** Celery workers (`workers/document-worker`)
- **Object Storage:** MinIO (S3-compatible storage for quotations)
- **Containerization:** Docker, Docker Compose

---

## 4. Repository Structure

```
procurement-intelligence/
├── .env.example                       # Environment configuration template
├── .gitignore                         # Git exclusion rules
├── docker-compose.yml                 # Orchestration for all services, middleware & gateway
├── README.md                          # Project documentation and developer guide
├── docs/                              # Architecture, proposals, and stage handoffs
│   ├── project-proposal.md
│   ├── master-plan.md
│   ├── architecture.md
│   ├── database-design.md
│   ├── api-contracts/
│   │   └── auth-verification.md
│   └── agent-handoffs/
│       └── stage-1-recovery.md
├── frontend/                          # React + TypeScript single-page application
│   └── procurement-dashboard/
├── gateway/                           # Traefik configuration
│   └── traefik/
│       ├── traefik.yml
│       └── dynamic.yml
├── infrastructure/                    # Middleware initialization scripts
│   └── postgres/
│       └── init-multiple-databases.sh
├── services/                          # Independent FastAPI microservices
│   ├── identity-service/
│   ├── procurement-service/
│   ├── supplier-service/
│   ├── document-service/
│   ├── ai-orchestrator-service/
│   ├── risk-service/
│   └── optimization-service/
├── shared/                            # Core shared library (auth, logging, contracts)
├── workers/                           # Celery asynchronous task workers
│   └── document-worker/
└── scripts/                           # Utility scripts
```

---

## 5. Environment Setup

### 5.1 Prerequisites
- **Python:** 3.12+
- **Node.js:** 20+ (with npm)
- **Docker & Docker Compose:** Docker Engine 24+ / Docker Desktop

### 5.2 Initial Setup
1. Clone the repository and navigate to the project directory:
   ```bash
   cd project
   ```

2. Copy the environment variables template:
   ```bash
   cp .env.example .env
   ```

3. Setup local Python virtual environment (optional for host testing):
   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   # Linux / macOS
   source .venv/bin/activate

   # Install test dependencies and shared library
   pip install fastapi uvicorn pydantic pydantic-settings email-validator sqlalchemy alembic bcrypt "python-jose[cryptography]" httpx pytest pytest-asyncio
   pip install -e shared
   ```

---

## 6. Docker Startup Instructions

To launch the full infrastructure (Gateway, PostgreSQL, RabbitMQ, Redis, MinIO, and 7 FastAPI microservices):

```bash
# Start all containers in detached mode
docker compose up -d

# Verify container statuses and health
docker compose ps

# View unified logs or service-specific logs
docker compose logs -f gateway
docker compose logs -f identity-service

# Stop all services and network
docker compose down

# Stop all services and remove persistent volumes
docker compose down -v
```

Once running, access endpoints through the Traefik Gateway (`http://localhost`):
- **Frontend Dashboard:** `http://localhost:5173` (or port 80 when routed)
- **Identity API:** `http://localhost/api/v1/identity/health`
- **Procurement API:** `http://localhost/api/v1/procurement/health`
- **Supplier API:** `http://localhost/api/v1/supplier/health`
- **Document API:** `http://localhost/api/v1/document/health`
- **AI Orchestrator API:** `http://localhost/api/v1/ai-orchestrator/health`
- **Risk API:** `http://localhost/api/v1/risk/health`
- **Optimization API:** `http://localhost/api/v1/optimization/health`

---

## 7. Database Migrations

Each stateful service manages its own PostgreSQL schema independently using Alembic.

### Running Migrations via Docker
```bash
docker compose exec identity-service alembic upgrade head
docker compose exec procurement-service alembic upgrade head
docker compose exec supplier-service alembic upgrade head
docker compose exec document-service alembic upgrade head
docker compose exec ai-orchestrator-service alembic upgrade head
docker compose exec risk-service alembic upgrade head
docker compose exec optimization-service alembic upgrade head
```

### Running Migrations Locally (Standalone)
Ensure `DATABASE_URL` is set in your environment:
```bash
cd services/identity-service
alembic upgrade head
```

---

## 8. Testing Commands

### 8.1 Backend Unit & Integration Tests
Execute the pytest suites across services using the local virtual environment:

```bash
# Test Identity Service (Auth, JWT, RBAC, tenant isolation, rate limiting)
pytest services/identity-service/tests

# Test other scaffolded microservices
pytest services/procurement-service/tests
pytest services/supplier-service/tests
pytest services/document-service/tests
pytest services/ai-orchestrator-service/tests
pytest services/risk-service/tests
pytest services/optimization-service/tests

# Run all backend service tests together
pytest services/*/tests
```

### 8.2 Frontend Development & Build Verification
```bash
cd frontend/procurement-dashboard

# Install frontend dependencies
npm install

# Start Vite dev server
npm run dev

# Run TypeScript compilation and production build
npm run build
```

