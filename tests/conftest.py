# conftest for all tests
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend')))
from app.main import app
from app.core.database import Base  # assuming Base is defined here
from app.security.secret_manager import SecretManager

# Use in-memory SQLite for fast tests
SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

class MockSecretManager(SecretManager):
    def get_secret(self, name: str) -> str:
        return f"mock-{name}"

@pytest.fixture(autouse=True)
def override_secret_manager(monkeypatch):
    monkeypatch.setattr("app.dependencies.security.get_secret_manager", lambda: MockSecretManager())

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c
