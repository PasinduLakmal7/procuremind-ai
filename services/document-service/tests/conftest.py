import os
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

from sqlalchemy.pool import StaticPool

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
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
