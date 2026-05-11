"""shared pytest fixtures.

Spins up the FastAPI app against an in-memory SQLite database so tests stay
hermetic. The app and its DB session dependency are wired together via
`app.dependency_overrides`, matching the canonical FastAPI testing pattern.
"""
from __future__ import annotations

import os
import sys
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# server/ is the import root used by the running app; the test runner is
# invoked from there too, but make it explicit so editors and direct calls work.
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


@pytest.fixture()
def test_db() -> Generator[Session, None, None]:
    """Fresh in-memory SQLite + bound session per test."""
    from db import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # ensure models are imported before metadata.create_all
    from models import Event, SessionSummary  # noqa: F401

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with the DB dependency overridden."""
    from db import get_db
    from main import app

    def _override_get_db() -> Generator[Session, None, None]:
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_header() -> dict[str, str]:
    """Default dev token; matches `utils/helpers.SHARED_TOKEN`."""
    return {"Authorization": "dev-secret-token"}
