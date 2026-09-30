from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.core.security import hash_password
from app.evaluation.operations import (
    ITEM_EXPORT_FIELDS,
    compare_recommendation_runs,
    participant_id_for,
)
from app.evaluation.safeguards import (
    EvaluationTargetError,
    assert_evaluation_target,
    resolve_evaluation_database_url,
)


def test_evaluation_url_does_not_fall_back_to_development_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://apple@localhost:5432/nsuk_career")
    monkeypatch.delenv("EVALUATION_DATABASE_URL", raising=False)
    url = resolve_evaluation_database_url()
    assert url.endswith("/nsuk_career_eval")
    assert "nsuk_career_eval" in url


def test_safeguards_refuse_development_and_test_databases(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVALUATION_CONFIRM", "I_UNDERSTAND")
    for name in ("nsuk_career", "nsuk_career_test", "postgres"):
        with pytest.raises(EvaluationTargetError, match="protected database"):
            assert_evaluation_target(f"postgresql+psycopg://apple@localhost:5432/{name}", mutating=True)


def test_safeguards_require_eval_suffix(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EVALUATION_CONFIRM", "I_UNDERSTAND")
    with pytest.raises(EvaluationTargetError, match="_eval"):
        assert_evaluation_target(
            "postgresql+psycopg://apple@localhost:5432/nsuk_career_production",
            mutating=True,
        )


def test_mutating_operations_require_explicit_confirm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EVALUATION_CONFIRM", raising=False)
    with pytest.raises(EvaluationTargetError, match="EVALUATION_CONFIRM"):
        assert_evaluation_target(
            "postgresql+psycopg://apple@localhost:5432/nsuk_career_eval",
            mutating=True,
        )
    monkeypatch.setenv("EVALUATION_CONFIRM", "I_UNDERSTAND")
    assert (
        assert_evaluation_target(
            "postgresql+psycopg://apple@localhost:5432/nsuk_career_eval",
            mutating=True,
        )
        == "nsuk_career_eval"
    )


def test_read_only_status_does_not_require_confirm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EVALUATION_CONFIRM", raising=False)
    assert (
        assert_evaluation_target(
            "postgresql+psycopg://apple@localhost:5432/nsuk_career_eval",
            mutating=False,
        )
        == "nsuk_career_eval"
    )


def test_participant_id_is_pseudonymous() -> None:
    user_id = "8b03250e-0f6d-4444-9d28-11813c738e23"
    pid = participant_id_for(user_id)
    assert pid.startswith("P-")
    assert user_id not in pid
    assert "example.com" not in pid
    assert participant_id_for(user_id) == pid


def test_export_fields_exclude_secrets_and_direct_identifiers() -> None:
    forbidden = {
        "password",
        "password_hash",
        "email",
        "first_name",
        "last_name",
        "matric_number",
        "auth_secret",
        "cookie",
        "jwt",
    }
    assert forbidden.isdisjoint(ITEM_EXPORT_FIELDS)
    assert "participant_id" in ITEM_EXPORT_FIELDS
    assert "relevance_rating_1_to_5" in ITEM_EXPORT_FIELDS


def test_compare_recommendation_runs_detects_identical_and_changed_order() -> None:
    item = {
        "onetsoc_code": "15-1252.00",
        "rank": 1,
        "raw_similarity": 0.91,
        "recommendation_score": 0.88,
        "rule_flags": [],
        "penalties": [{"rule_code": "R-ZONE-LOW", "action": "penalise", "penalty": 0.05}],
    }
    same = compare_recommendation_runs({"items": [item]}, {"items": [item]})
    assert same["identical_soc_order"] is True
    assert same["identical_rule_outcomes"] is True
    changed = compare_recommendation_runs(
        {"items": [item]},
        {"items": [{**item, "onetsoc_code": "15-1253.00"}]},
    )
    assert changed["identical_soc_order"] is False


def test_password_hashes_use_argon2id() -> None:
    hashed = hash_password("CorrectHorse9")
    assert hashed.startswith("$argon2id$")


def test_runtime_integrity_has_no_structural_duplicates(db_session) -> None:
    from app.evaluation.operations import collect_integrity_findings

    findings = {row.check: row for row in collect_integrity_findings(db_session)}
    for key in (
        "duplicate_item_ranks",
        "duplicate_item_occupations",
        "duplicate_ratings",
        "duplicate_soc_in_snapshot",
        "orphan_assessments",
        "orphan_runs",
        "orphan_items",
        "orphan_experience_evaluations",
        "duplicate_experience_evaluations",
        "runs_missing_traceability",
        "questionnaire_inconsistency",
        "invalid_faculty_prior_elements",
        "invalid_onet_element_references",
    ):
        assert findings[key].ok, f"{key}: {findings[key].detail} ({findings[key].count})"


def test_evaluation_cli_exists() -> None:
    assert (Path(__file__).resolve().parents[2] / "scripts" / "evaluation.py").is_file()
    assert os.environ.get("EVALUATION_CONFIRM") != "accidental"
