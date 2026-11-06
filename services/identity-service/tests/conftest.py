import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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
from app.models.role import Role

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Provides a fresh database session for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()

    # Seed default roles
    for role_name in ["admin", "procurement_manager", "procurement_officer", "supply_chain_analyst", "auditor"]:
        role = Role(name=role_name, description=f"Role {role_name}")
        session.add(role)
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """TestClient that uses the test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
