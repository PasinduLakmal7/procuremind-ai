# Deployment Guide & Operations Runbook

**Project:** AI-Powered Procurement Intelligence Platform  
**Environment:** Local Development, Docker Demonstration, & Production  

---

## 1. Prerequisites

- **Docker & Docker Compose:** Docker Engine 24.0+ / Docker Desktop.
- **Node.js & npm:** Node 18+ / npm 9+ (for frontend dashboard).
- **Python:** Python 3.12+ (for local test runner and scripting).

---

## 2. Quick-Start (Docker Compose Demonstration)

### Step 1: Clone & Configure Environment Variables
```bash
cp .env.example .env
```
Ensure secrets (`JWT_SECRET_KEY`, `POSTGRES_PASSWORD`, `MINIO_ROOT_PASSWORD`) are configured.

### Step 2: Build & Start All Containers
```bash
docker compose up -d --build
```
This spins up:
- Edge Gateway: `traefik:v3.0` (Port 80)
- Middleware: PostgreSQL 16 (multi-database), RabbitMQ 3.13, Redis 7, MinIO S3
- 7 Microservices: `identity`, `procurement`, `supplier`, `document`, `ai-orchestrator`, `risk`, `optimization`
- Workers: `document-worker` (Celery)
- Frontend: `frontend` (React 18 SPA)

### Step 3: Run Database Migrations
```bash
# Run migrations across all 7 service databases
for svc in identity-service procurement-service supplier-service document-service ai-orchestrator-service risk-service optimization-service; do
  docker compose exec $svc alembic upgrade head
done
```

### Step 4: Seed Demo Data
```bash
python scripts/seed_demo_data.py
```

### Step 5: Access Web Applications
- **Procurement Dashboard:** `http://localhost`
- **Traefik API Gateway:** `http://localhost/api/v1/...`
- **MinIO S3 Console:** `http://localhost:9001` (Credentials: `minioadmin` / `minioadmin`)

---

## 3. Local Development (Without Docker)

### Backend Virtual Environment
```bash
# Setup virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r shared/requirements.txt
```

### Frontend Development Server
```bash
cd frontend/procurement-dashboard
npm install
npm run dev
# Dashboard accessible at http://localhost:5173
```

### Running Backend Tests
```bash
# Run all integration & unit test suites
.\.venv\Scripts\pytest.exe tests/integration/ -v
```

---

## 4. Backup & Restore Guidance

### PostgreSQL Multi-Database Backup
```bash
docker compose exec postgres pg_dumpall -U postgres > backup_all_databases_$(date +%Y%m%d).sql
```

### PostgreSQL Restore
```bash
cat backup_all_databases_20261106.sql | docker compose exec -T postgres psql -U postgres
```

### MinIO Document Object Storage Backup
```bash
docker compose exec minio-init mc mirror local/procurement-quotations /backup/minio/
```

