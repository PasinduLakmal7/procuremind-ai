# An Explainable Multi-Agent AI Framework for Procurement Process Optimization and Supplier Risk Prediction

**Project:** AI-Powered Procurement Intelligence Platform  
**Domain:** Sri Lankan Manufacturing Industry  
**Architecture:** Microservices + Multi-Agent AI + Event-Driven Processing  
**Document Version:** 1.0 — Implementation-Oriented Specification  
**Project Status:** Proposed System / Stage 1 Implementation  

---

## 1. Executive Summary
This project delivers an explainable multi-agent artificial intelligence decision-support platform designed for manufacturing procurement. It combines intelligent quotation processing, supplier performance analysis, machine learning risk estimation, multi-objective supplier optimization, and explainable recommendations while maintaining strict human-in-the-loop decision-making.

## 2. Key Problem Domains
1. **Time-Consuming Quotation Processing:** Manual extraction of unstructured pricing, discounts, and terms from PDF, image, and spreadsheet quotes.
2. **Supplier Reliability Uncertainty:** Price-only choices leading to delivery delays, quality disputes, and incomplete fulfillment.
3. **Fragmented Procurement Data:** Disconnected data silos hindering comparison, tracking, and compliance audits.
4. **Limited Decision Transparency:** Lack of verifiable, evidence-backed scoring and explanation for supplier awards.

## 3. High-Level System Architecture
- **Frontend:** React + TypeScript + Vite
- **API Gateway:** Traefik reverse proxy and router
- **Backend Services (FastAPI):**
  - Identity Service
  - Procurement Service
  - Supplier Service
  - Document Service
  - AI Orchestrator Service (LangGraph)
  - Risk Service
  - Optimization Service
- **Event-Driven Messaging & Tasks:** RabbitMQ + Celery
- **Database & Storage:** PostgreSQL (database-per-service ownership pattern), MinIO (S3-compatible object storage), Redis (caching)
- **Deployment & Orchestration:** Docker Compose

