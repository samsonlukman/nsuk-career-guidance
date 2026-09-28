from __future__ import annotations

import json
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import FacultyKnowledgePrior, FacultyKnowledgePriorAudit, User
from tests.api.conftest import TEST_PASSWORD
from tests.api.test_recommendation_api import _payload

ADMIN_GET_PATHS = (
    "/api/v1/admin/dashboard",
    "/api/v1/admin/health",
    "/api/v1/admin/students",
    "/api/v1/admin/recommendation-runs",
    "/api/v1/admin/ratings",
    "/api/v1/admin/onet-snapshot",
    "/api/v1/admin/questionnaire",
    "/api/v1/admin/recommendation-config",
    "/api/v1/admin/faculty-knowledge-priors",
    "/api/v1/admin/faculty-knowledge-priors/catalog",
    "/api/v1/admin/faculty-knowledge-priors/audits",
)


def _login(client: TestClient, email: str) -> None:
    client.cookies.clear()
    response = client.post("/api/v1/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert response.status_code == 200, response.text


def _assert_no_secrets(payload: object) -> None:
    dumped = json.dumps(payload)
    assert "password_hash" not in dumped
    assert "auth_secret" not in dumped
    assert "database_url" not in dumped.lower()


def test_unauthenticated_admin_endpoints_are_rejected(client: TestClient) -> None:
    client.cookies.clear()
    for path in ADMIN_GET_PATHS:
        response = client.get(path)
        assert response.status_code == 401, path
        assert response.json()["error"]["code"] == "unauthenticated"


def test_student_is_denied_admin_endpoints(authed_client: TestClient) -> None:
    for path in ADMIN_GET_PATHS:
        response = authed_client.get(path)
        assert response.status_code == 403, path
        assert response.json()["error"]["code"] == "forbidden"
        assert "password_hash" not in response.text


def test_admin_dashboard_uses_stored_counts(admin_client: TestClient, student: User) -> None:
    _ = student
    response = admin_client.get("/api/v1/admin/dashboard")
    assert response.status_code == 200
    body = response.json()
    _assert_no_secrets(body)
    assert body["students_total"] >= 1
    assert body["assessments_completed"] >= 0
    assert body["recommendation_runs"] >= 0
    assert body["ratings_total"] >= 0
    assert body["active_onet"]["onet_release"] == "30.3"
    assert body["active_onet"]["occupation_count"] > 0
    assert body["active_onet"]["recommendable_count"] > 0
    assert body["active_questionnaire"]["version"] == "questionnaire_v1"
    assert body["active_questionnaire"]["question_count"] > 0
    assert body["active_config"]["version"] == "config_v1"
    assert body["active_config"]["k"] == 10
    assert body["active_config"]["block_weights"]
    assert body["system"]["api"] == "ok"
    assert body["system"]["database"] == "connected"
    assert "accuracy" not in " ".join(body["notes"]).lower() or "not a measure" in " ".join(body["notes"]).lower()


def test_admin_health_omits_secrets(admin_client: TestClient) -> None:
    response = admin_client.get("/api/v1/admin/health")
    assert response.status_code == 200
    body = response.json()
    _assert_no_secrets(body)
    assert body["api"] == "ok"
    assert body["database"] == "connected"
    assert body["active_onet_snapshot"] is True
    assert body["active_questionnaire"] is True
    assert body["active_recommendation_config"] is True
    assert "traceback" not in response.text.lower()


def test_admin_student_management_search_and_pagination(
    admin_client: TestClient,
    student: User,
) -> None:
    listed = admin_client.get("/api/v1/admin/students", params={"page": 1, "page_size": 5})
    assert listed.status_code == 200
    body = listed.json()
    _assert_no_secrets(body)
    assert body["page"] == 1
    assert body["page_size"] == 5
    assert body["total"] >= 1
    emails = {item["email"] for item in body["items"]}
    assert student.email in emails or body["total"] > len(body["items"])
    detail = admin_client.get(f"/api/v1/admin/students/{student.id}")
    assert detail.status_code == 200
    profile = detail.json()
    assert profile["email"] == student.email
    assert profile["profile"]["first_name"] == "Test"
    assert "password_hash" not in profile
    assert "assessments" in profile
    assert "recommendation_history" in profile

    search = admin_client.get("/api/v1/admin/students", params={"q": student.email.split("@")[0]})
    assert search.status_code == 200
    assert any(item["id"] == str(student.id) for item in search.json()["items"])

    missing = admin_client.get(f"/api/v1/admin/students/{uuid.uuid4()}")
    assert missing.status_code == 404


def test_admin_cannot_see_password_hash_on_student_list(admin_client: TestClient) -> None:
    response = admin_client.get("/api/v1/admin/students")
    assert response.status_code == 200
    _assert_no_secrets(response.json())
    for item in response.json()["items"]:
        assert set(item) >= {"id", "email", "is_active"}
        assert "password_hash" not in item
        assert "password" not in item


def test_admin_recommendation_activity_and_persisted_run(
    client: TestClient,
    student: User,
    admin_user: User,
) -> None:
    _login(client, student.email)
    created = client.post("/api/v1/assessments", json=_payload(client))
    assert created.status_code == 200, created.text
    run = created.json()
    _login(client, admin_user.email)
    listed = client.get("/api/v1/admin/recommendation-runs")
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] >= 1
    match = next(item for item in body["items"] if item["run_id"] == run["id"])
    assert match["student_id"] == str(student.id)
    assert match["student_email"] == student.email
    assert match["questionnaire_version"] == "questionnaire_v1"
    assert match["config_version"] == "config_v1"
    assert match["onet_release"] == "30.3"
    assert match["item_count"] == 10
    assert match["top_occupation_title"]

    detail = client.get(f"/api/v1/admin/recommendation-runs/{run['id']}")
    assert detail.status_code == 200
    inspected = detail.json()
    assert inspected["student"]["email"] == student.email
    assert inspected["run"]["id"] == run["id"]
    assert [item["onetsoc_code"] for item in inspected["run"]["items"]] == [item["onetsoc_code"] for item in run["items"]]
    top = inspected["run"]["items"][0]
    assert top["explanation"]
    assert top["recommendation_score"] == run["items"][0]["recommendation_score"]
    assert isinstance(top["contributing_features"], list)
    assert "rule_flags" in top
    missing = client.get(f"/api/v1/admin/recommendation-runs/{uuid.uuid4()}")
    assert missing.status_code == 404


def test_admin_feedback_view_and_aggregates(
    client: TestClient,
    student: User,
    admin_user: User,
) -> None:
    _login(client, student.email)
    created = client.post("/api/v1/assessments", json=_payload(client)).json()
    item_id = created["items"][0]["id"]
    rated = client.post(
        f"/api/v1/recommendations/{item_id}/rating",
        json={"relevance_1_to_5": 4, "comment": "Useful as a discussion prompt"},
    )
    assert rated.status_code == 200
    _login(client, admin_user.email)
    response = client.get("/api/v1/admin/ratings")
    assert response.status_code == 200
    body = response.json()
    _assert_no_secrets(body)
    assert body["summary"]["ratings_total"] >= 1
    assert body["summary"]["average_relevance"] is not None
    assert set(map(int, body["summary"]["distribution"])) == {1, 2, 3, 4, 5}
    assert "not a measure of recommendation accuracy" in body["summary"]["note"].lower()
    assert "ai accuracy" not in response.text.lower()
    match = next(item for item in body["items"] if item["id"] == rated.json()["id"])
    assert match["relevance_1_to_5"] == 4
    assert match["comment"] == "Useful as a discussion prompt"
    assert match["run_id"] == created["id"]
    assert match["student_email"] == student.email
    assert match["occupation_title"]


def test_admin_onet_questionnaire_and_config_are_read_only(admin_client: TestClient) -> None:
    snapshot = admin_client.get("/api/v1/admin/onet-snapshot")
    assert snapshot.status_code == 200
    onet = snapshot.json()
    assert onet["onet_release"] == "30.3"
    assert onet["feature_version"]
    assert onet["snapshot_id"]
    assert onet["occupation_count"] > 0
    assert onet["recommendable_count"] > 0
    assert onet["knn_feature_count"] > 0
    assert onet["job_zones"]
    assert any(zone["job_zone"] == 5 for zone in onet["job_zones"])
    assert "read-only" in onet["note"].lower()

    questionnaire = admin_client.get("/api/v1/admin/questionnaire")
    assert questionnaire.status_code == 200
    qbody = questionnaire.json()
    assert qbody["version"] == "questionnaire_v1"
    assert qbody["status"] == "published"
    assert qbody["question_count"] == len(qbody["questions"])
    assert qbody["option_count"] > 0
    assert any(item["code"] == "knowledge" for item in qbody["questions"])

    config = admin_client.get("/api/v1/admin/recommendation-config")
    assert config.status_code == 200
    cbody = config.json()
    assert cbody["version"] == "config_v1"
    assert cbody["k"] == 10
    assert cbody["metric"]
    assert cbody["block_weights"]["riasec"]
    assert "not allowed" in cbody["note"].lower()
    assert admin_client.post("/api/v1/admin/recommendation-config", json={"k": 5}).status_code in {404, 405}
    assert admin_client.patch("/api/v1/admin/recommendation-config", json={"k": 5}).status_code in {404, 405}


def test_faculty_knowledge_crud_audit_and_invalid_input(
    admin_client: TestClient,
    admin_user: User,
    db_session: Session,
) -> None:
    catalog = admin_client.get("/api/v1/admin/faculty-knowledge-priors/catalog")
    assert catalog.status_code == 200
    knowledge = catalog.json()["knowledge_elements"]
    faculties = catalog.json()["faculties"]
    assert knowledge
    assert any(item["element_id"] == "2.C.3.a" for item in knowledge)
    assert "Natural and Applied Sciences" in faculties

    existing = {
        (item["faculty"], item["element_id"])
        for item in admin_client.get("/api/v1/admin/faculty-knowledge-priors").json()["items"]
    }
    create_faculty = next(name for name in faculties if (name, "2.C.3.a") not in existing)
    update_faculty = next(
        name for name in faculties if name != create_faculty and (name, "2.C.4.a") not in existing
    )

    created = admin_client.post(
        "/api/v1/admin/faculty-knowledge-priors",
        json={"faculty": create_faculty, "element_id": "2.C.3.a"},
    )
    assert created.status_code == 201, created.text
    prior = created.json()
    assert prior["faculty"] == create_faculty
    assert prior["element_id"] == "2.C.3.a"
    assert prior["element_name"]
    prior_id = prior["id"]

    duplicate = admin_client.post(
        "/api/v1/admin/faculty-knowledge-priors",
        json={"faculty": create_faculty, "element_id": "2.C.3.a"},
    )
    assert duplicate.status_code == 409

    invalid_faculty = admin_client.post(
        "/api/v1/admin/faculty-knowledge-priors",
        json={"faculty": "Invented Faculty of Magic", "element_id": "2.C.3.a"},
    )
    assert invalid_faculty.status_code == 422
    assert invalid_faculty.json()["error"]["code"] == "invalid_faculty"

    invalid_knowledge = admin_client.post(
        "/api/v1/admin/faculty-knowledge-priors",
        json={"faculty": "Law", "element_id": "9.Z.9.z"},
    )
    assert invalid_knowledge.status_code == 422
    assert invalid_knowledge.json()["error"]["code"] == "invalid_knowledge_element"

    updated = admin_client.patch(
        f"/api/v1/admin/faculty-knowledge-priors/{prior_id}",
        json={"faculty": update_faculty, "element_id": "2.C.4.a"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["faculty"] == update_faculty
    assert updated.json()["element_id"] == "2.C.4.a"

    listed = admin_client.get("/api/v1/admin/faculty-knowledge-priors")
    assert listed.status_code == 200
    assert any(item["id"] == prior_id and item["faculty"] == update_faculty for item in listed.json()["items"])

    deleted = admin_client.delete(f"/api/v1/admin/faculty-knowledge-priors/{prior_id}")
    assert deleted.status_code == 204
    remaining = admin_client.get("/api/v1/admin/faculty-knowledge-priors").json()["items"]
    assert all(item["id"] != prior_id for item in remaining)
    missing = admin_client.delete(f"/api/v1/admin/faculty-knowledge-priors/{prior_id}")
    assert missing.status_code == 404

    audits = admin_client.get("/api/v1/admin/faculty-knowledge-priors/audits")
    assert audits.status_code == 200
    ours = [item for item in audits.json()["items"] if item["actor_user_id"] == str(admin_user.id)]
    assert {item["action"] for item in ours} >= {"create", "update", "delete"}
    delete_row = next(item for item in ours if item["action"] == "delete")
    assert delete_row["faculty"] == update_faculty
    assert delete_row["element_id"] == "2.C.4.a"
    assert delete_row["previous_faculty"] == update_faculty
    db_session.expire_all()
    assert db_session.get(FacultyKnowledgePrior, prior_id) is None
    assert db_session.query(FacultyKnowledgePriorAudit).count() >= 3


def test_faculty_prior_rejects_untrusted_origin(admin_client: TestClient) -> None:
    response = admin_client.post(
        "/api/v1/admin/faculty-knowledge-priors",
        json={"faculty": "Law", "element_id": "2.C.3.a"},
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 403
