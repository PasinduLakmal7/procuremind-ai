# Master Implementation Plan

## 1. Development Stages Overview

| Stage | Name | Key Deliverables | Status |
|---|---|---|---|
| **Stage 1** | **Foundation & Infrastructure** | Monorepo layout, Docker Compose, PostgreSQL multi-databases, Traefik gateway, Shared packages, Identity Service with RBAC & JWT, Scaffolding for all 7 FastAPI services, React+TS frontend skeleton, CI/test setup. | **In Progress** |
| **Stage 2** | **Core Business Services** | Supplier management, purchase requests, quotation uploads, document persistence, and basic procurement dashboard. | Pending |
| **Stage 3** | **Document AI & Agent Orchestration** | OCR extraction pipelines, human-in-the-loop verification, LangGraph workflows, and Celery background workers. | Pending |
| **Stage 4** | **Risk Prediction & Optimization** | Statistical/ML risk models, multi-criteria optimization, explanation generation, and managerial approval workflows. | Pending |
| **Stage 5** | **Frontend Completion & Deployment** | End-to-end UI integration, telemetry/observability, performance benchmarks, evaluation reports, and production packaging. | Pending |

## 2. Master Engineering Rules
1. **Microservices Boundary Integrity:** Strict database-per-service ownership; no direct SQL queries across services.
2. **Stateless Service Auth:** Services validate JWTs locally using signature verification and claims (`sub`, `org_id`, `roles`) without querying Identity DB.
3. **Event-Driven Asynchrony:** REST for low-latency queries/commands; RabbitMQ for cross-boundary domain events and Celery for intensive background tasks.
4. **Explainability & Human-in-the-Loop:** AI agents generate proposals with traceable citations; final purchase decisions require human approval.
5. **No Hallucinated Predictions or Metrics:** Real datasets or documented synthetic baselines; clear indicators when historical supplier data is insufficient.

