"""Pytest fixtures for unit and integration testing."""

import os
import json
import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.models.database import Base, get_db
from app.models.orm import Incident, Runbook, PostMortem
from app.main import app
from app.llm.mock_provider import MockLLMProvider
from app.llm.factory import set_llm_provider
from app.memory.base import MemoryStore
from app.memory.factory import set_memory_store

TEST_DATABASE_URL = "sqlite:///./data/test_incidents.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


class DummyTestMemoryStore(MemoryStore):
    """In-memory test memory store for deterministic testing."""

    def __init__(self):
        self.retained_items = []

    @property
    def name(self) -> str:
        return "test_memory"

    async def ping(self) -> bool:
        return True

    async def retain(self, item_id: str, content: str, memory_type: str, metadata=None) -> bool:
        self.retained_items.append({
            "id": item_id,
            "content": content,
            "type": memory_type,
            "metadata": metadata or {},
        })
        return True

    async def recall(self, query: str, limit: int = 5, filter_type=None):
        out = []
        for item in self.retained_items:
            if filter_type and item["type"] != filter_type:
                continue
            out.append({
                "id": item["id"],
                "content": item["content"],
                "metadata": item["metadata"],
                "similarity": 0.88,
                "source": "test_memory",
            })
        return out[:limit]


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create test tables and seed minimal test data."""
    os.makedirs("./data", exist_ok=True)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./data/test_incidents.db"):
        try:
            os.remove("./data/test_incidents.db")
        except Exception:
            pass


@pytest.fixture
def db_session():
    """Provide a transactional database session for each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def setup_test_overrides(db_session):
    """Override get_db dependency and inject mock components."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Set mock LLM and test memory store
    dummy_memory = DummyTestMemoryStore()
    mock_llm = MockLLMProvider()
    set_memory_store(dummy_memory)
    set_llm_provider(mock_llm)

    yield

    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)
