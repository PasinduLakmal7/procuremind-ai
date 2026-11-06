import os
from pathlib import Path

services_config = [
    {
        "name": "procurement-service",
        "port": 8002,
        "db": "procurement_db",
        "table": "purchase_requests",
        "model_name": "PurchaseRequest",
        "model_file": """import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, CHAR
from app.db.base import Base

class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False)
    budget = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
"""
    },
    {
        "name": "supplier-service",
        "port": 8003,
        "db": "supplier_db",
        "table": "suppliers",
        "model_name": "Supplier",
        "model_file": """import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, CHAR
from app.db.base import Base

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    company_name = Column(String(255), nullable=False, index=True)
    tax_id = Column(String(100), nullable=True)
    rating = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
"""
    },
    {
        "name": "document-service",
        "port": 8004,
        "db": "document_db",
        "table": "document_records",
        "model_name": "DocumentRecord",
        "model_file": """import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, CHAR
from app.db.base import Base

class DocumentRecord(Base):
    __tablename__ = "document_records"
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    s3_key = Column(String(500), nullable=False)
    status = Column(String(50), default="UPLOADED", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
"""
    },
    {
        "name": "ai-orchestrator-service",
        "port": 8005,
        "db": "ai_orchestrator_db",
        "table": "agent_workflow_executions",
        "model_name": "AgentWorkflowExecution",
        "model_file": """import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, CHAR
from app.db.base import Base

class AgentWorkflowExecution(Base):
    __tablename__ = "agent_workflow_executions"
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    workflow_name = Column(String(100), nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)
    state_snapshot = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
"""
    },
    {
        "name": "risk-service",
        "port": 8006,
        "db": "risk_db",
        "table": "supplier_risk_profiles",
        "model_name": "SupplierRiskProfile",
        "model_file": """import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, CHAR
from app.db.base import Base

class SupplierRiskProfile(Base):
    __tablename__ = "supplier_risk_profiles"
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    supplier_id = Column(CHAR(36), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    model_version = Column(String(50), default="baseline-rule-v1", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
"""
    },
    {
        "name": "optimization-service",
        "port": 8007,
        "db": "optimization_db",
        "table": "optimization_scenarios",
        "model_name": "OptimizationScenario",
        "model_file": """import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, CHAR
from app.db.base import Base

class OptimizationScenario(Base):
    __tablename__ = "optimization_scenarios"
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(CHAR(36), nullable=False, index=True)
    request_id = Column(CHAR(36), nullable=False, index=True)
    algorithm = Column(String(100), default="weighted_sum_v1", nullable=False)
    rankings_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
"""
    }
]

base_dir = Path("e:/semester 4/Projects\wify/chamodi/project/services")

for svc in services_config:
    svc_name = svc["name"]
    port = svc["port"]
    db_name = svc["db"]
    table_name = svc["table"]
    model_name = svc["model_name"]
    model_code = svc["model_file"]
    svc_path = base_dir / svc_name

    # 1. requirements.txt
    (svc_path / "requirements.txt").write_text("""fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
sqlalchemy>=2.0.30
alembic>=1.13.1
psycopg2-binary>=2.9.9
python-jose[cryptography]>=3.3.0
httpx>=0.27.0
pytest>=8.2.0
pytest-asyncio>=0.23.6
""", encoding="utf-8")

    # 2. Dockerfile
    (svc_path / "Dockerfile").write_text(f"""FROM python:3.12-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    gcc \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

COPY shared/ /workspace/shared/

WORKDIR /workspace/services/{svc_name}
COPY services/{svc_name}/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e /workspace/shared

COPY services/{svc_name}/ .

ENV PYTHONPATH=/workspace:/workspace/services/{svc_name}
EXPOSE {port}

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \\
    CMD curl -f http://localhost:{port}/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "{port}"]
""", encoding="utf-8")

    # 3. alembic.ini
    (svc_path / "alembic.ini").write_text("""[alembic]
script_location = alembic
file_template = %%(rev)s_%%(slug)s
prepend_sys_path = .

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""", encoding="utf-8")

    # 4. alembic/script.py.mako
    (svc_path / "alembic" / "script.py.mako").write_text("""\"\"\"${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

\"\"\"
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}

def upgrade() -> None:
    ${upgrades if upgrades else "pass"}

def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
""", encoding="utf-8")

    # 5. alembic/env.py
    (svc_path / "alembic" / "env.py").write_text("""import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

service_root = Path(__file__).resolve().parents[1]
workspace_root = Path(__file__).resolve().parents[3]
if str(service_root) not in sys.path:
    sys.path.insert(0, str(service_root))
if str(workspace_root) not in sys.path:
    sys.path.insert(0, str(workspace_root))

from app.core.config import settings
from app.db.base import Base
import app.models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    return settings.DATABASE_URL

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
""", encoding="utf-8")

    # 6. alembic/versions/0001_initial_tables.py
    (svc_path / "alembic" / "versions" / "0001_initial_tables.py").write_text(f"""\"\"\"Initial migration for {svc_name}

Revision ID: 0001_initial
Revises: 
Create Date: 2026-11-05 21:00:00.000000
\"\"\"
from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        '{table_name}',
        sa.Column('id', sa.CHAR(36), primary_key=True),
        sa.Column('organization_id', sa.CHAR(36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_{table_name}_org', '{table_name}', ['organization_id'])

def downgrade() -> None:
    op.drop_table('{table_name}')
""", encoding="utf-8")

    # 7. app/__init__.py
    (svc_path / "app" / "__init__.py").write_text(f'"""Application package for {svc_name}."""\n', encoding="utf-8")

    # 8. app/core/config.py
    (svc_path / "app" / "core" / "config.py").write_text(f"""import sys
from pathlib import Path
from pydantic import Field

root_path = str(Path(__file__).resolve().parents[4])
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from shared.core.config import MicroserviceBaseSettings

class ServiceSettings(MicroserviceBaseSettings):
    APP_NAME: str = "{svc_name}"
    PORT: int = {port}
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/{db_name}",
        description="Database URL for {db_name}"
    )

settings = ServiceSettings()
""", encoding="utf-8")

    # 9. app/db/base.py
    (svc_path / "app" / "db" / "base.py").write_text("""from sqlalchemy.orm import declarative_base

Base = declarative_base()
""", encoding="utf-8")

    # 10. app/db/session.py
    (svc_path / "app" / "db" / "session.py").write_text("""from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    connect_args=connect_args,
    pool_pre_ping=True if not settings.DATABASE_URL.startswith("sqlite") else False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""", encoding="utf-8")

    # 11. app/models/
    (svc_path / "app" / "models" / f"{table_name}.py").write_text(model_code, encoding="utf-8")
    (svc_path / "app" / "models" / "__init__.py").write_text(f"""from app.db.base import Base
from app.models.{table_name} import {model_name}

__all__ = ["Base", "{model_name}"]
""", encoding="utf-8")

    # 12. app/api/v1/endpoints/health.py
    (svc_path / "app" / "api" / "v1" / "endpoints" / "health.py").write_text(f"""from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.session import get_db
from shared.api_contracts.responses import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="ok",
        service="{svc_name}",
        version="0.1.0",
        database="n/a",
    )

@router.get("/ready", response_model=HealthResponse)
def readiness_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"disconnected: {{str(exc)}}"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        service="{svc_name}",
        version="0.1.0",
        database=db_status,
    )
""", encoding="utf-8")

    # 13. app/api/v1/endpoints/sample_protected.py
    prefix_clean = svc_name.replace("-service", "")
    (svc_path / "app" / "api" / "v1" / "endpoints" / "sample_protected.py").write_text(f"""from fastapi import APIRouter, Depends
from app.core.config import settings
from shared.auth.jwt_validator import get_current_principal_factory, SecurityPrincipal
from shared.api_contracts.responses import ApiResponse

router = APIRouter(prefix="/status", tags=["Status"])

get_current_principal = get_current_principal_factory(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
)

@router.get("/summary", response_model=ApiResponse[dict])
def get_service_summary(
    principal: SecurityPrincipal = Depends(get_current_principal),
):
    \"\"\"Demonstrates cross-service stateless JWT validation and organization isolation.\"\"\"
    return ApiResponse(
        data={{
            "service": "{svc_name}",
            "organization_id": str(principal.organization_id),
            "caller_email": principal.email,
            "roles": principal.roles,
            "message": "Authorized access verified statelessly without querying Identity DB."
        }}
    )
""", encoding="utf-8")

    # 14. app/api/v1/router.py
    (svc_path / "app" / "api" / "v1" / "router.py").write_text(f"""from fastapi import APIRouter
from app.api.v1.endpoints import health, sample_protected

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(sample_protected.router)
""", encoding="utf-8")

    # 15. app/main.py
    (svc_path / "app" / "main.py").write_text(f"""from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from shared.core.middleware import CorrelationIdMiddleware, register_app_exception_handlers
from shared.observability.logging import setup_logger

logger = setup_logger(
    service_name=settings.APP_NAME,
    log_level=settings.LOG_LEVEL,
    log_format=settings.LOG_FORMAT,
)

def create_app() -> FastAPI:
    app = FastAPI(
        title="{svc_name.replace('-', ' ').title()}",
        description="Microservice for {svc_name}",
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CorrelationIdMiddleware)
    register_app_exception_handlers(app)

    app.include_router(api_router, prefix="/api/v1/{prefix_clean}")

    from app.api.v1.endpoints import health
    app.include_router(health.router)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
""", encoding="utf-8")

    # 16. tests/conftest.py
    (svc_path / "tests" / "conftest.py").write_text(f"""import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-characters-minimum-length-for-testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

service_dir = Path(__file__).resolve().parents[1]
workspace_dir = Path(__file__).resolve().parents[3]
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))
if str(workspace_dir) not in sys.path:
    sys.path.insert(0, str(workspace_dir))

from app.db.base import Base
from app.db.session import get_db
from app.main import app

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={{"check_same_thread": False}},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
""", encoding="utf-8")

    # 17. tests/test_service.py
    (svc_path / "tests" / "test_service.py").write_text(f"""import uuid
import pytest
from jose import jwt

def test_{svc_name.replace('-', '_')}_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["service"] == "{svc_name}"
    assert res.json()["status"] == "ok"

    res_ready = client.get("/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ok"

def test_cross_service_jwt_verification(client):
    secret_key = "test-secret-key-32-characters-minimum-length-for-testing"
    user_id = str(uuid.uuid4())
    org_id = str(uuid.uuid4())
    
    # 1. Valid token
    token = jwt.encode({{
        "sub": user_id,
        "email": "analyst@factory.lk",
        "organization_id": org_id,
        "roles": ["procurement_officer"],
        "token_type": "access",
        "exp": 2000000000
    }}, secret_key, algorithm="HS256")

    res = client.get(
        "/api/v1/{prefix_clean}/status/summary",
        headers={{"Authorization": f"Bearer {{token}}"}}
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["service"] == "{svc_name}"
    assert data["organization_id"] == org_id
    assert data["caller_email"] == "analyst@factory.lk"

    # 2. Tampered token
    tampered_res = client.get(
        "/api/v1/{prefix_clean}/status/summary",
        headers={{"Authorization": "Bearer tampered.token.here"}}
    )
    assert tampered_res.status_code == 401
""", encoding="utf-8")

print("All 6 microservices scaffolded successfully.")

