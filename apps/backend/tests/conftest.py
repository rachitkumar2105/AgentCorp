"""tests/conftest.py

Root-level pytest configuration containing global fixtures, mock providers,
and setup/teardown logic for databases and environments.
"""
from __future__ import annotations

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from datetime import datetime
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import ALL models from the root models module so relationships register correctly
from app.models import (
    BaseModel,
    User,
    Role,
    Permission,
    UserRole,
    RolePermission,
    Organization,
    OrganizationMember,
    Team,
    TeamMember,
    Agent,
    AgentVersion,
    Tool,
    AgentTool,
    Conversation,
    Message,
    MultiAgentSession,
    MultiAgentParticipant,
    AgentInterMessage,
    AgentDelegation,
    QuotaUsage,
    SecurityPolicy,
    AuditSecurityEvent
)
from app.db.base import Base
from app.config.settings import settings


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


# ---------------------------------------------------------------------------
# Mock AI Provider
# ---------------------------------------------------------------------------
class MockAIProvider:
    """Deterministic mock provider simulating chat, streaming, tool calling, and usage data."""

    def __init__(self, response_text: str = "Mocked AI Response", tool_calls: list | None = None) -> None:
        self.response_text = response_text
        self.tool_calls = tool_calls or []

    async def chat(self, prompt: str, **kwargs) -> dict:
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": self.response_text,
                    "tool_calls": self.tool_calls
                }
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        words = self.response_text.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.01)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_engine():
    """Session-wide engine for sqlite test database."""
    # Using an in-memory SQLite database for speed and isolation in tests
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(db_engine) -> Generator[Session, None, None]:
    """Function-scoped database session."""
    connection = db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def mock_provider() -> MockAIProvider:
    """Fixture providing a deterministic Mock AI Provider."""
    return MockAIProvider()


# ---------------------------------------------------------------------------
# Core Domain Fixtures / Factories
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def test_org(db: Session) -> Organization:
    org = Organization(name="Test Org", slug="test-org")
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@pytest.fixture(scope="function")
def test_user(db: Session, test_org: Organization) -> User:
    user = User(
        email="testuser@example.com",
        hashed_password="mockhashedpassword",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_agent(db: Session, test_org: Organization) -> Agent:
    agent = Agent(
        name="Test Agent",
        description="A helpful assistant for testing",
        organization_id=test_org.id,
        is_active=True
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@pytest.fixture(scope="function")
def test_conversation(db: Session, test_org: Organization, test_user: User) -> Conversation:
    conv = Conversation(
        title="Test Chat",
        user_id=test_user.id,
        organization_id=test_org.id
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv
