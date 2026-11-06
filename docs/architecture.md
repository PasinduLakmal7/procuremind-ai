# System Architecture Specification

## 1. Architectural Style
The platform employs a distributed, asynchronous microservices architecture combined with stateful multi-agent orchestration via LangGraph.

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
       +-----------------------------+-----------------------------+
       |              |              |              |              |
       v              v              v              v              v
+--------------+ +-----------+ +-----------+ +-----------+ +---------------+
|   Identity   | |Procurement| | Supplier  | | Document  | |AI Orchestrator| ... [Risk & Optimization]
|   Service    | |  Service  | |  Service  | |  Service  | |    Service    |
|  (Port 8001) | |(Port 8002)| |(Port 8003)| |(Port 8004)| |  (Port 8005)  |
+-------+------+ +-----+-----+ +-----+-----+ +-----+-----+ +-------+-------+
        |              |             |             |               |
        v              v             v             v               v
  [identity_db] [procurement_db][supplier_db][document_db] [ai_orchestrator_db]
```

## 2. Service Responsibilities & Ports

| Service Name | Port | Database | Primary Responsibility |
|---|---|---|---|
| **Traefik Gateway** | `80` (proxy) | N/A | Reverse proxy, path routing (`/api/v1/*`), TLS termination, rate limiting |
| **Frontend** | `5173` | N/A | React + TypeScript + Vite procurement UI |
| **Identity Service** | `8001` | `identity_db` | Auth, organization isolation, user profiles, RBAC, session/refresh tokens |
| **Procurement Service** | `8002` | `procurement_db` | Purchase requests, line items, requirement constraints, approvals |
| **Supplier Service** | `8003` | `supplier_db` | Supplier profiles, tier classifications, historical order & delivery logs |
| **Document Service** | `8004` | `document_db` | Uploads, MinIO object metadata, document validation, extraction jobs |
| **AI Orchestrator Service** | `8005` | `ai_orchestrator_db` | LangGraph agent state machine, multi-agent evaluation execution |
| **Risk Service** | `8006` | `risk_db` | Supplier risk baselines, delivery delay & quality risk model inference |
| **Optimization Service** | `8007` | `optimization_db` | Multi-criteria supplier ranking, Pareto trade-offs, constraint checks |

## 3. Communication Patterns
- **Synchronous (REST):** Client-to-service via Traefik; internal service-to-service calls using signed JWT propagation.
- **Asynchronous (RabbitMQ Events):** Domain event broadcasts (e.g., `DocumentUploaded.v1`, `SupplierEvaluated.v1`, `QuotationExtracted.v1`).
- **Heavy Async Processing (Celery):** Document OCR parsing, heavy feature extraction.
- **Object Storage (MinIO):** Raw documents (PDF, XLSX, PNG) with presigned URL access.

