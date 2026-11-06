"""
Shared fixtures for the API tests.

The database URL is pointed at a throw-away SQLite file *before* the app is
imported, so tests never touch a real database configured in `.env`.
"""

import os
import tempfile
from pathlib import Path

import pytest

_DB_DIR = tempfile.mkdtemp(prefix="shiftmaster-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_DB_DIR) / 'test.db'}"
os.environ["ENVIRONMENT"] = "development"  # seeds the demo accounts, disables rate limiting
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:  # runs the lifespan (tables + seed data)
        yield test_client


def _login(client, email: str, password: str) -> dict:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(scope="session")
def admin_headers(client):
    return _login(client, "admin@example.com", "admin123")


@pytest.fixture(scope="session")
def employee_headers(client):
    return _login(client, "employee@example.com", "employee123")


@pytest.fixture(scope="session")
def login(client):
    return lambda email, password: _login(client, email, password)
