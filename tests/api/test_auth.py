from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User
from app.services.questionnaire_seed import NSUK_FACULTIES
from tests.api.conftest import TEST_PASSWORD


def test_register_login_me_and_logout(client: TestClient) -> None:
    client.cookies.clear()
    email = f"reg-{uuid.uuid4().hex}@example.com"
    created = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": TEST_PASSWORD,
            "first_name": "Amina",
            "last_name": "Bello",
            "matric_number": f"NSU/{uuid.uuid4().hex[:6].upper()}",
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["email"] == email
    assert body["role"] == "student"
    assert body["profile"]["first_name"] == "Amina"
    assert "password" not in body
    assert "nsuk_session" in created.cookies

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["id"] == body["id"]

    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401

    login = client.post("/api/v1/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert login.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 200
    client.cookies.clear()


def test_register_duplicate_email(client: TestClient) -> None:
    client.cookies.clear()
    email = f"dup-{uuid.uuid4().hex}@example.com"
    first = client.post("/api/v1/auth/register", json={"email": email, "password": TEST_PASSWORD})
    assert first.status_code == 200
    client.cookies.clear()
    second = client.post("/api/v1/auth/register", json={"email": email, "password": TEST_PASSWORD})
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "email_taken"


def test_login_rejects_wrong_password(client: TestClient, student: User) -> None:
    client.cookies.clear()
    response = client.post("/api/v1/auth/login", json={"email": student.email, "password": "wrong-pass"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_protected_route_requires_session(client: TestClient) -> None:
    client.cookies.clear()
    response = client.get("/api/v1/me/dashboard")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_profile_update_and_dashboard_empty_state(authed_client: TestClient) -> None:
    updated = authed_client.put(
        "/api/v1/me/profile",
        json={
            "first_name": "Chinedu",
            "last_name": "Okeke",
            "faculty": NSUK_FACULTIES[8],
            "department": "Computer Science",
            "level": "400",
            "further_study": "maybe",
            "course_relatedness": "open",
        },
    )
    assert updated.status_code == 200, updated.text
    profile = updated.json()["profile"]
    assert profile["faculty"] == "Natural and Applied Sciences"
    assert profile["department"] == "Computer Science"
    assert profile["level"] == "400"

    dashboard = authed_client.get("/api/v1/me/dashboard")
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["user"]["profile"]["first_name"] == "Chinedu"
    assert body["has_completed_assessment"] is False
    assert body["latest_assessment"] is None
    assert body["latest_recommendation"] is None
    assert body["recommendation_history"] == []


def test_profile_rejects_unknown_faculty(authed_client: TestClient) -> None:
    response = authed_client.put("/api/v1/me/profile", json={"faculty": "Invented Faculty of Magic"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_faculty"


def test_profile_options_are_official(client: TestClient) -> None:
    response = client.get("/api/v1/metadata/profile-options")
    assert response.status_code == 200
    payload = response.json()
    assert payload["faculties"] == list(NSUK_FACULTIES)
    assert "100" in payload["levels"]
    assert "Computer Science" not in str(payload)


def test_register_ignores_client_supplied_role(client: TestClient) -> None:
    client.cookies.clear()
    email = f"role-{uuid.uuid4().hex}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": TEST_PASSWORD, "role": "admin"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["role"] == "student"
    client.cookies.clear()


def test_same_origin_forwarded_host_is_allowed_on_login(client: TestClient, student: User) -> None:
    client.cookies.clear()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": student.email, "password": TEST_PASSWORD},
        headers={
            "Origin": "https://demo.example",
            "Host": "demo.example",
            "X-Forwarded-Proto": "https",
            "X-Forwarded-Host": "demo.example",
        },
    )
    assert response.status_code == 200, response.text
    client.cookies.clear()


def test_untrusted_origin_is_rejected_on_login(client: TestClient, student: User) -> None:
    client.cookies.clear()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": student.email, "password": TEST_PASSWORD},
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
    client.cookies.clear()


def test_admin_cannot_use_student_dashboard(client: TestClient, db_session: Session) -> None:
    from app.core.security import hash_password

    admin = User(
        email=f"admin-{uuid.uuid4().hex}@example.com",
        password_hash=hash_password(TEST_PASSWORD),
        role="admin",
    )
    db_session.add(admin)
    db_session.commit()
    client.cookies.clear()
    login = client.post("/api/v1/auth/login", json={"email": admin.email, "password": TEST_PASSWORD})
    assert login.status_code == 200
    forbidden = client.get("/api/v1/me/dashboard")
    assert forbidden.status_code == 403
    client.cookies.clear()
