"""Pytest fixtures for ShopAgent AI."""

import pytest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database import Base, get_db
from backend.models import Product, Order, Payment, AgentSession, AuditLog
from backend.catalog import seed_catalog
from backend.razorpay_client import RazorpayClient

# Shared in-memory SQLite engine with StaticPool so all threads share the same database
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(scope="function")
def db_session():
    """In-memory SQLite database session fixture."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    session = TestingSessionLocal()
    seed_catalog(session)
    yield session
    session.close()
    Base.metadata.drop_all(bind=TEST_ENGINE)


@pytest.fixture(scope="function")
def rzp_client():
    """Razorpay test client fixture."""
    return RazorpayClient(key_id="rzp_test_fixture", key_secret="secret_fixture_123")


@pytest.fixture(scope="function")
def client():
    """FastAPI TestClient with overridden database and engine dependencies."""
    Base.metadata.drop_all(bind=TEST_ENGINE)
    Base.metadata.create_all(bind=TEST_ENGINE)

    session = TestingSessionLocal()
    seed_catalog(session)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    from backend.main import app
    from backend import api_routes, database

    app.dependency_overrides[get_db] = override_get_db

    with patch.object(api_routes, "engine", TEST_ENGINE), \
         patch.object(api_routes, "Base", Base), \
         patch.object(database, "engine", TEST_ENGINE):
        with TestClient(app, raise_server_exceptions=True) as test_client:
            yield test_client

    app.dependency_overrides.clear()
    session.close()
    Base.metadata.drop_all(bind=TEST_ENGINE)
