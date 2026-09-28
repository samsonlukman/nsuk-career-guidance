from __future__ import annotations

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import get_engine
from app.models import StudentProfile, User
from tests.conftest import RUNTIME_DATABASE_URL

TEST_PASSWORD = "CorrectHorse9"


@pytest.fixture(scope="session")
def client(loaded_snapshot):
    os.environ["DATABASE_URL"] = RUNTIME_DATABASE_URL
    get_settings.cache_clear()
    get_engine.cache_clear()
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def student(db_session: Session) -> User:
    user = User(
        email=f"student-{uuid.uuid4().hex}@example.com",
        password_hash=hash_password(TEST_PASSWORD),
        role="student",
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(StudentProfile(user_id=user.id, first_name="Test", last_name="Student"))
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def authed_client(client: TestClient, student: User):
    client.cookies.clear()
    response = client.post("/api/v1/auth/login", json={"email": student.email, "password": TEST_PASSWORD})
    assert response.status_code == 200, response.text
    yield client
    client.cookies.clear()


@pytest.fixture
def admin_user(db_session: Session) -> User:
    user = User(
        email=f"admin-{uuid.uuid4().hex}@example.com",
        password_hash=hash_password(TEST_PASSWORD),
        role="admin",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_client(client: TestClient, admin_user: User):
    client.cookies.clear()
    response = client.post("/api/v1/auth/login", json={"email": admin_user.email, "password": TEST_PASSWORD})
    assert response.status_code == 200, response.text
    yield client
    client.cookies.clear()
