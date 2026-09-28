from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Assessment, RecommendationItem, RecommendationRun, User
from app.recommendation.constants import (
    ESSENTIAL_INTERNAL_NAMES,
    FEATURE_VERSION,
    RIASEC_INTERNAL_NAMES,
    TRANSFERABLE_INTERNAL_NAMES,
    WORK_STYLE_INTERNAL_NAMES,
)
from app.recommendation.pipeline import recommend
from app.recommendation.runtime import get_occupation_index
from app.recommendation.student_features import AcademicProfile, StudentAssessment, WorkPreferences
from app.services.questionnaire_seed import QUESTIONNAIRE_VERSION
from tests.api.conftest import TEST_PASSWORD

SAMPLE_SOC = "11-1011.00"


def _complete_responses(questionnaire: dict, *, overrides: dict | None = None) -> list[dict]:
    overrides = overrides or {}
    responses: list[dict] = []
    for question in questionnaire["questions"]:
        code = question["code"]
        if code in overrides:
            responses.append(overrides[code])
            continue
        if question["response_type"] == "sparse_select":
            chosen = "1.B.3.q" if code == "sia" else "2.C.3.a"
            match = next((opt for opt in question["options"] if opt["value"] == chosen), question["options"][0])
            rating = 7 if code == "sia" else 5
            responses.append({"code": code, "selections": [{"element_id": match["value"], "value": rating}]})
        elif question["response_type"] == "choice":
            if code == "level":
                value = "300"
            elif code == "further_study":
                value = "maybe"
            elif code == "course_relatedness":
                value = "open"
            elif code == "faculty":
                value = "Natural and Applied Sciences"
            else:
                value = question["options"][0]["value"]
            responses.append({"code": code, "value": value})
        elif question["response_type"] in {"likert", "preference"}:
            if code == "interest_investigative":
                value = 7
            elif code.startswith("interest_"):
                value = 3
            elif code == "skill_programming":
                value = 5
            elif code == "pref_indoor":
                value = 4
            elif code == "pref_outdoor":
                value = 3
            else:
                value = 4 if question["max_value"] == 7 else 3
            responses.append({"code": code, "value": value})
        elif question["response_type"] == "text":
            continue
    return responses


def _payload(client: TestClient, *, overrides: dict | None = None) -> dict:
    questionnaire = client.get("/api/v1/questionnaires/active").json()
    return {
        "questionnaire_version": questionnaire["version"],
        "responses": _complete_responses(questionnaire, overrides=overrides),
    }


def test_active_questionnaire_retrieval(client: TestClient) -> None:
    response = client.get("/api/v1/questionnaires/active")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == QUESTIONNAIRE_VERSION
    assert payload["feature_version"] == FEATURE_VERSION
    codes = [question["code"] for question in payload["questions"]]
    assert codes == [question["code"] for question in sorted(payload["questions"], key=lambda item: item["sort_order"])]
    assert "interest_investigative" in codes
    assert "sia" in codes
    assert "knowledge" in codes
    sia = next(question for question in payload["questions"] if question["code"] == "sia")
    assert sia["min_selections"] == 1
    assert sia["max_selections"] == 5
    assert len(sia["options"]) == 41
    knowledge = next(question for question in payload["questions"] if question["code"] == "knowledge")
    assert len(knowledge["options"]) == 33
    for code, element_id in RIASEC_INTERNAL_NAMES.items():
        question = next(item for item in payload["questions"] if item["code"] == code)
        assert question["onet_element_id"] == element_id
    for mapping in (ESSENTIAL_INTERNAL_NAMES, TRANSFERABLE_INTERNAL_NAMES, WORK_STYLE_INTERNAL_NAMES):
        for code, element_id in mapping.items():
            question = next(item for item in payload["questions"] if item["code"] == code)
            assert question["onet_element_id"] == element_id


def test_questionnaire_version_retrieval(client: TestClient) -> None:
    response = client.get(f"/api/v1/questionnaires/{QUESTIONNAIRE_VERSION}")
    assert response.status_code == 200
    assert response.json()["version"] == QUESTIONNAIRE_VERSION


def test_invalid_questionnaire_version(client: TestClient) -> None:
    response = client.get("/api/v1/questionnaires/not_a_version")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "invalid_questionnaire_version"


def test_valid_assessment_and_end_to_end_persistence(authed_client: TestClient, db_session: Session) -> None:
    payload = _payload(authed_client)
    response = authed_client.post("/api/v1/assessments", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["feature_version"] == FEATURE_VERSION
    assert body["questionnaire_version"] == QUESTIONNAIRE_VERSION
    assert body["config_version"] == "config_v1"
    assert body["onet_release"] == "30.3"
    assert body["k"] == 10
    assert len(body["items"]) == 10
    assert all(item["job_zone"] in {3, 4, 5} for item in body["items"])
    assert all("similarity" in item["explanation"].lower() for item in body["items"])
    assert "not predicted" in body["notes"][0].lower()

    expected = recommend(_student_assessment_from_payload(payload), get_occupation_index(), k=10)
    assert [item["onetsoc_code"] for item in body["items"]] == [item.onetsoc_code for item in expected.items]
    assert [item["rank"] for item in body["items"]] == list(range(1, 11))
    top = body["items"][0]
    assert top["contributing_features"] or top["explanation"]
    assert top["raw_similarity"] == pytest.approx(expected.items[0].raw_similarity, rel=1e-6)
    assert top["recommendation_score"] == pytest.approx(expected.items[0].recommendation_score, rel=1e-6)

    db_session.expire_all()
    assert db_session.get(Assessment, uuid.UUID(body["assessment_id"])) is not None
    run = db_session.get(RecommendationRun, uuid.UUID(body["id"]))
    assert run is not None
    assert run.feature_version == FEATURE_VERSION
    assert run.questionnaire_version_id is not None
    assert run.onet_snapshot_id is not None
    assert run.config_id is not None
    assert db_session.query(RecommendationItem).filter_by(run_id=run.id).count() == 10


def test_invalid_response(authed_client: TestClient) -> None:
    payload = _payload(
        authed_client,
        overrides={"interest_realistic": {"code": "interest_realistic", "value": 99}},
    )
    response = authed_client.post("/api/v1/assessments", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] in {"invalid_response", "validation_error"}


def test_missing_required_response(authed_client: TestClient) -> None:
    payload = _payload(authed_client)
    payload["responses"] = [item for item in payload["responses"] if item["code"] != "interest_realistic"]
    response = authed_client.post("/api/v1/assessments", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "missing_required_response"


def test_invalid_assessment_questionnaire_version(authed_client: TestClient) -> None:
    payload = _payload(authed_client)
    payload["questionnaire_version"] = "questionnaire_v9"
    response = authed_client.post("/api/v1/assessments", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_questionnaire_version"


def test_recommendation_retrieval_and_explanation(authed_client: TestClient) -> None:
    created = authed_client.post("/api/v1/assessments", json=_payload(authed_client)).json()
    response = authed_client.get(f"/api/v1/recommendations/{created['id']}")
    assert response.status_code == 200
    fetched = response.json()
    assert fetched["id"] == created["id"]
    assert [item["onetsoc_code"] for item in fetched["items"]] == [item["onetsoc_code"] for item in created["items"]]
    top = fetched["items"][0]
    assert top["explanation"]
    assert "predicted success" in top["explanation"].lower() or "similarity" in top["explanation"].lower()
    assert isinstance(top["contributing_features"], list)
    assert isinstance(top["work_activities"], list)
    assert fetched["questionnaire_version"] == QUESTIONNAIRE_VERSION
    assert fetched["feature_version"] == FEATURE_VERSION
    assert fetched["config_version"] == "config_v1"


def test_recommendation_history_and_ownership(
    authed_client: TestClient,
    student: User,
    db_session: Session,
) -> None:
    first = authed_client.post("/api/v1/assessments", json=_payload(authed_client)).json()
    second = authed_client.post("/api/v1/assessments", json=_payload(authed_client)).json()
    mine = authed_client.get("/api/v1/me/recommendations")
    assert mine.status_code == 200
    run_ids = {item["run_id"] for item in mine.json()["items"]}
    assert first["id"] in run_ids
    assert second["id"] in run_ids
    scoped = authed_client.get(f"/api/v1/students/{student.id}/recommendations")
    assert scoped.status_code == 200
    assert scoped.json()["student_id"] == str(student.id)

    other = User(
        email=f"other-{uuid.uuid4().hex}@example.com",
        password_hash=hash_password(TEST_PASSWORD),
        role="student",
    )
    db_session.add(other)
    db_session.commit()
    authed_client.cookies.clear()
    login = authed_client.post("/api/v1/auth/login", json={"email": other.email, "password": TEST_PASSWORD})
    assert login.status_code == 200
    forbidden = authed_client.get(f"/api/v1/students/{student.id}/recommendations")
    assert forbidden.status_code == 403
    authed_client.cookies.clear()
    missing_actor = authed_client.get(f"/api/v1/students/{student.id}/recommendations")
    assert missing_actor.status_code == 401


def test_unauthenticated_assessment_rejected(client: TestClient) -> None:
    client.cookies.clear()
    payload = _payload(client)
    response = client.post("/api/v1/assessments", json=payload)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_invalid_recommendation_run(authed_client: TestClient) -> None:
    response = authed_client.get(f"/api/v1/recommendations/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "invalid_recommendation_run"


def test_rating_creation_and_invalid_rating(authed_client: TestClient) -> None:
    created = authed_client.post("/api/v1/assessments", json=_payload(authed_client)).json()
    item_id = created["items"][0]["id"]
    ok = authed_client.post(
        f"/api/v1/recommendations/{item_id}/rating",
        json={"relevance_1_to_5": 4, "comment": "Useful as a discussion prompt"},
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["relevance_1_to_5"] == 4
    assert "accuracy" not in body["note"].lower() or "not" in body["note"].lower()
    assert "user relevance feedback" in body["note"].lower()

    invalid = authed_client.post(
        f"/api/v1/recommendations/{item_id}/rating",
        json={"relevance_1_to_5": 9},
    )
    assert invalid.status_code == 422

    missing_item = authed_client.post(
        f"/api/v1/recommendations/{uuid.uuid4()}/rating",
        json={"relevance_1_to_5": 3},
    )
    assert missing_item.status_code == 404
    assert missing_item.json()["error"]["code"] == "invalid_recommendation_item"


def test_occupation_details_for_recommendation_link(client: TestClient) -> None:
    response = client.get(f"/api/v1/occupations/{SAMPLE_SOC}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["onetsoc_code"] == SAMPLE_SOC
    assert payload["title"] == "Chief Executives"
    assert payload["job_zone"] == 5
    assert payload["job_zone_education"]
    assert payload["work_activities"]
    assert payload["interests"]
    assert "id" not in payload


def test_identical_assessment_is_deterministic(authed_client: TestClient) -> None:
    payload = _payload(authed_client)
    first = authed_client.post("/api/v1/assessments", json=payload)
    second = authed_client.post("/api/v1/assessments", json=payload)
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    left = first.json()
    right = second.json()
    assert [item["onetsoc_code"] for item in left["items"]] == [item["onetsoc_code"] for item in right["items"]]
    assert [item["rank"] for item in left["items"]] == [item["rank"] for item in right["items"]]
    assert [item["raw_similarity"] for item in left["items"]] == [item["raw_similarity"] for item in right["items"]]
    assert [item["recommendation_score"] for item in left["items"]] == [
        item["recommendation_score"] for item in right["items"]
    ]
    assert [[flag["rule_code"] for flag in item["rule_flags"]] for item in left["items"]] == [
        [flag["rule_code"] for flag in item["rule_flags"]] for item in right["items"]
    ]
    assert [[row["rule_code"] for row in item["penalties"]] for item in left["items"]] == [
        [row["rule_code"] for row in item["penalties"]] for item in right["items"]
    ]


def test_untrusted_origin_cannot_submit_assessment(authed_client: TestClient) -> None:
    payload = _payload(authed_client)
    response = authed_client.post(
        "/api/v1/assessments",
        json=payload,
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_historical_version_traceability(authed_client: TestClient, db_session: Session) -> None:
    created = authed_client.post("/api/v1/assessments", json=_payload(authed_client)).json()
    run = db_session.get(RecommendationRun, uuid.UUID(created["id"]))
    assert run is not None
    fetched = authed_client.get(f"/api/v1/recommendations/{created['id']}").json()
    assert fetched["feature_version"] == run.feature_version
    assert fetched["questionnaire_version"] == QUESTIONNAIRE_VERSION
    assert fetched["config_version"] == "config_v1"
    assert fetched["onet_snapshot_id"] == str(run.onet_snapshot_id)
    assert fetched["onet_release"] == "30.3"


def _student_assessment_from_payload(payload: dict) -> StudentAssessment:
    by_code = {item["code"]: item for item in payload["responses"]}

    def likert_block(names: dict[str, str]) -> dict[str, object]:
        return {code: int(by_code[code]["value"]) for code in names}

    def sparse(code: str) -> dict[str, object]:
        return {row["element_id"]: int(row["value"]) for row in by_code[code]["selections"]}

    return StudentAssessment(
        riasec=likert_block(RIASEC_INTERNAL_NAMES),
        sia=sparse("sia"),
        essential_skills=likert_block(ESSENTIAL_INTERNAL_NAMES),
        transferable_skills=likert_block(TRANSFERABLE_INTERNAL_NAMES),
        work_styles=likert_block(WORK_STYLE_INTERNAL_NAMES),
        knowledge=sparse("knowledge"),
        profile=AcademicProfile(
            faculty=by_code["faculty"]["value"] if "faculty" in by_code else None,
            department=None,
            level=str(by_code["level"]["value"]),
            further_study=str(by_code["further_study"]["value"]),
            course_relatedness=str(by_code["course_relatedness"]["value"]),
        ),
        preferences=WorkPreferences(
            pref_indoor=int(by_code["pref_indoor"]["value"]),
            pref_outdoor=int(by_code["pref_outdoor"]["value"]),
            pref_team=int(by_code["pref_team"]["value"]),
            pref_public=int(by_code["pref_public"]["value"]),
        ),
    )
