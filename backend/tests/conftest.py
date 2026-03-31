"""Pytest: отдельная БД test_starthub.db, сброс схемы на каждый тест."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("STARTHUB_TESTING", "1")

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def reset_tables() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def event_base_payload() -> dict:
    return {
        "name": "Test Event",
        "date_start": "2026-07-01",
        "location": "Moscow",
        "sport_type": "running",
        "created_by": "pytest",
    }
