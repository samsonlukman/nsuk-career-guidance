"""Evaluation database init, reset, export, integrity, and verification helpers.

These operations never change O*NET data, feature engineering, KNN, rule
formulas, or recommendation weights. They manage environment isolation only.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import statistics
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete, func, inspect, select, text, update
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import REPO_ROOT
from app.core.security import hash_password
from app.evaluation.safeguards import (
    assert_evaluation_target,
    resolve_evaluation_database_url,
    sqlalchemy_url_database_name,
)
from app.models import (
    Assessment,
    AssessmentResponse,
    FacultyKnowledgePrior,
    FacultyKnowledgePriorAudit,
    Occupation,
    OccupationFeature,
    OnetSnapshot,
    Question,
    QuestionOption,
    QuestionnaireVersion,
    RecommendationConfig,
    RecommendationContribution,
    RecommendationItem,
    RecommendationRating,
    RecommendationRun,
    RuleDefinition,
    RuleFiring,
    StudentProfile,
    SystemConfig,
    User,
)
from app.recommendation.constants import FEATURE_VERSION, ONET_RELEASE
from app.services.onet_loader import default_processed_dir, load_processed_snapshot
from app.services.questionnaire_seed import QUESTIONNAIRE_VERSION

EXPORT_FORBIDDEN_SUBSTRINGS = (
    "password",
    "password_hash",
    "auth_secret",
    "cookie",
    "jwt",
    "session",
    "token",
    "email",
    "first_name",
    "last_name",
    "matric",
)

ITEM_EXPORT_FIELDS = (
    "participant_id",
    "assessment_id",
    "recommendation_run_id",
    "recommendation_item_id",
    "rank",
    "onetsoc_code",
    "occupation_title",
    "raw_similarity",
    "recommendation_score",
    "relevance_rating_1_to_5",
    "feedback_comment",
    "run_created_at",
    "questionnaire_version",
    "onet_release",
    "feature_version",
    "config_version",
    "elapsed_ms",
    "faculty",
    "department",
    "level",
)


@dataclass
class EvaluationStatus:
    database_name: str
    database_url_host: str
    schema_ready: bool
    onet_release: str | None
    feature_version: str | None
    occupation_count: int
    questionnaire_version: str | None
    config_version: str | None
    rule_count: int
    student_count: int
    assessment_count: int
    recommendation_run_count: int
    rating_count: int
    faculty_prior_count: int
    admin_count: int
    notes: list[str] = field(default_factory=list)


@dataclass
class IntegrityFinding:
    check: str
    ok: bool
    count: int
    detail: str


@dataclass
class IntegrityReport:
    database_name: str
    passed: bool
    findings: list[IntegrityFinding]


def _alembic_config(url: str) -> Config:
    cfg = Config(str(REPO_ROOT / "backend" / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "backend" / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def _session_factory(url: str) -> tuple[Engine, sessionmaker[Session]]:
    engine = create_engine(url, future=True)
    return engine, sessionmaker(bind=engine, autoflush=False, class_=Session)


def participant_id_for(user_id: Any) -> str:
    digest = hashlib.sha256(f"nsuk-eval-participant:{user_id}".encode("utf-8")).hexdigest()
    return f"P-{digest[:16]}"


def ensure_evaluation_database(url: str, *, admin_url: str | None = None) -> str:
    name = assert_evaluation_target(url, mutating=True)
    postgres_url = admin_url or os.environ.get(
        "POSTGRES_ADMIN_URL", "postgresql+psycopg://apple@localhost:5432/postgres"
    )
    admin = create_engine(postgres_url, isolation_level="AUTOCOMMIT", future=True)
    try:
        with admin.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": name}
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{name}"'))
    finally:
        admin.dispose()
    return name


def migrate_evaluation_database(url: str) -> None:
    assert_evaluation_target(url, mutating=True)
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    try:
        command.upgrade(_alembic_config(url), "head")
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous


def load_evaluation_onet(url: str, *, processed_dir: Path | None = None) -> dict[str, Any]:
    assert_evaluation_target(url, mutating=True)
    engine, factory = _session_factory(url)
    session = factory()
    try:
        result = load_processed_snapshot(session, processed_dir or default_processed_dir(REPO_ROOT))
        session.commit()
        return asdict(result)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


def evaluation_status(url: str) -> EvaluationStatus:
    name = assert_evaluation_target(url, mutating=False)
    engine, factory = _session_factory(url)
    session = factory()
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        schema_ready = {"users", "onet_snapshots", "questionnaire_versions", "recommendation_configs"}.issubset(
            tables
        )
        snapshot = session.scalar(select(OnetSnapshot).where(OnetSnapshot.feature_version == FEATURE_VERSION))
        questionnaire = session.scalar(
            select(QuestionnaireVersion).where(QuestionnaireVersion.version == QUESTIONNAIRE_VERSION)
        )
        config = session.scalar(select(RecommendationConfig).where(RecommendationConfig.version == "config_v1"))
        notes: list[str] = []
        prior_count = session.scalar(select(func.count()).select_from(FacultyKnowledgePrior)) or 0
        if prior_count == 0:
            notes.append(
                "faculty_knowledge_priors is intentionally empty: no officially approved NSUK mapping has been supplied."
            )
        else:
            notes.append(
                "faculty_knowledge_priors is not empty. Do not treat unverified rows as approved research configuration."
            )
        host = url.split("@")[-1] if "@" in url else url
        return EvaluationStatus(
            database_name=name,
            database_url_host=host,
            schema_ready=schema_ready,
            onet_release=snapshot.onet_release if snapshot else None,
            feature_version=snapshot.feature_version if snapshot else None,
            occupation_count=session.scalar(select(func.count()).select_from(Occupation)) or 0,
            questionnaire_version=questionnaire.version if questionnaire else None,
            config_version=config.version if config else None,
            rule_count=session.scalar(select(func.count()).select_from(RuleDefinition)) or 0,
            student_count=session.scalar(select(func.count()).select_from(User).where(User.role == "student")) or 0,
            assessment_count=session.scalar(select(func.count()).select_from(Assessment)) or 0,
            recommendation_run_count=session.scalar(select(func.count()).select_from(RecommendationRun)) or 0,
            rating_count=session.scalar(select(func.count()).select_from(RecommendationRating)) or 0,
            faculty_prior_count=prior_count,
            admin_count=session.scalar(select(func.count()).select_from(User).where(User.role == "admin")) or 0,
            notes=notes,
        )
    finally:
        session.close()
        engine.dispose()


def initialize_evaluation_environment(url: str, *, processed_dir: Path | None = None) -> EvaluationStatus:
    ensure_evaluation_database(url)
    migrate_evaluation_database(url)
    load_evaluation_onet(url, processed_dir=processed_dir)
    return evaluation_status(url)


def reset_evaluation_students(url: str) -> dict[str, int]:
    """Delete evaluation student operational rows. Keep schema, O*NET, questionnaire, config."""
    assert_evaluation_target(url, mutating=True)
    engine, factory = _session_factory(url)
    session = factory()
    try:
        student_ids = list(session.scalars(select(User.id).where(User.role == "student")))
        counts = {
            "ratings": session.scalar(select(func.count()).select_from(RecommendationRating)) or 0,
            "runs": session.scalar(select(func.count()).select_from(RecommendationRun)) or 0,
            "assessments": session.scalar(select(func.count()).select_from(Assessment)) or 0,
            "students": len(student_ids),
        }
        session.execute(delete(RecommendationRating))
        session.execute(delete(RecommendationContribution))
        session.execute(delete(RuleFiring))
        session.execute(delete(RecommendationItem))
        session.execute(delete(RecommendationRun))
        session.execute(delete(AssessmentResponse))
        session.execute(delete(Assessment))
        if student_ids:
            session.execute(
                update(FacultyKnowledgePrior)
                .where(FacultyKnowledgePrior.created_by.in_(student_ids))
                .values(created_by=None)
            )
            session.execute(
                update(FacultyKnowledgePriorAudit)
                .where(FacultyKnowledgePriorAudit.actor_user_id.in_(student_ids))
                .values(actor_user_id=None)
            )
            session.execute(
                update(SystemConfig).where(SystemConfig.updated_by.in_(student_ids)).values(updated_by=None)
            )
            session.execute(delete(StudentProfile).where(StudentProfile.user_id.in_(student_ids)))
            session.execute(delete(User).where(User.role == "student"))
        session.commit()
        return counts
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


def create_evaluation_admin(url: str) -> dict[str, str]:
    """Create or rotate an admin using EVAL_ADMIN_EMAIL / EVAL_ADMIN_PASSWORD.

    Credentials are read from the environment only. They are never written to
    source or to the export files.
    """
    assert_evaluation_target(url, mutating=True)
    email = (os.environ.get("EVAL_ADMIN_EMAIL") or "").strip().lower()
    password = os.environ.get("EVAL_ADMIN_PASSWORD") or ""
    if not email or not password:
        raise RuntimeError(
            "Set EVAL_ADMIN_EMAIL and EVAL_ADMIN_PASSWORD in the environment. "
            "Do not pass the password on the command line."
        )
    if len(password) < 8:
        raise RuntimeError("EVAL_ADMIN_PASSWORD must be at least 8 characters.")
    engine, factory = _session_factory(url)
    session = factory()
    try:
        user = session.scalar(select(User).where(func.lower(User.email) == email))
        if user is None:
            user = User(email=email, password_hash=hash_password(password), role="admin", is_active=True)
            session.add(user)
            action = "created"
        elif user.role != "admin":
            raise RuntimeError("An account with that email exists and is not an admin.")
        else:
            user.password_hash = hash_password(password)
            user.is_active = True
            action = "updated"
        session.commit()
        return {"email": email, "action": action, "role": "admin"}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


def _config_value(session: Session, key: str) -> str | None:
    row = session.get(SystemConfig, key)
    if row is None:
        return None
    value = row.value_json.get("value") if isinstance(row.value_json, dict) else None
    return str(value) if value is not None else None


def collect_integrity_findings(session: Session) -> list[IntegrityFinding]:
    findings: list[IntegrityFinding] = []

    def add(check: str, count: int, detail: str) -> None:
        findings.append(IntegrityFinding(check=check, ok=count == 0, count=count, detail=detail))

    add(
        "orphan_assessments",
        session.scalar(
            select(func.count())
            .select_from(Assessment)
            .outerjoin(User, Assessment.student_user_id == User.id)
            .where(User.id.is_(None))
        )
        or 0,
        "assessments whose student no longer exists",
    )
    add(
        "orphan_runs",
        session.scalar(
            select(func.count())
            .select_from(RecommendationRun)
            .outerjoin(Assessment, RecommendationRun.assessment_id == Assessment.id)
            .where(Assessment.id.is_(None))
        )
        or 0,
        "recommendation runs whose assessment no longer exists",
    )
    add(
        "orphan_items",
        session.scalar(
            select(func.count())
            .select_from(RecommendationItem)
            .outerjoin(RecommendationRun, RecommendationItem.run_id == RecommendationRun.id)
            .where(RecommendationRun.id.is_(None))
        )
        or 0,
        "recommendation items whose run no longer exists",
    )
    add(
        "duplicate_item_ranks",
        session.scalar(
            select(func.count()).select_from(
                select(RecommendationItem.run_id, RecommendationItem.rank)
                .group_by(RecommendationItem.run_id, RecommendationItem.rank)
                .having(func.count() > 1)
                .subquery()
            )
        )
        or 0,
        "duplicate ranks inside a recommendation run",
    )
    add(
        "duplicate_item_occupations",
        session.scalar(
            select(func.count()).select_from(
                select(RecommendationItem.run_id, RecommendationItem.occupation_id)
                .group_by(RecommendationItem.run_id, RecommendationItem.occupation_id)
                .having(func.count() > 1)
                .subquery()
            )
        )
        or 0,
        "duplicate occupations inside a recommendation run",
    )
    add(
        "duplicate_ratings",
        session.scalar(
            select(func.count()).select_from(
                select(RecommendationRating.item_id, RecommendationRating.student_user_id)
                .group_by(RecommendationRating.item_id, RecommendationRating.student_user_id)
                .having(func.count() > 1)
                .subquery()
            )
        )
        or 0,
        "duplicate ratings for the same student and item",
    )
    add(
        "duplicate_soc_in_snapshot",
        session.scalar(
            select(func.count()).select_from(
                select(Occupation.snapshot_id, Occupation.onetsoc_code)
                .group_by(Occupation.snapshot_id, Occupation.onetsoc_code)
                .having(func.count() > 1)
                .subquery()
            )
        )
        or 0,
        "duplicate SOC codes within an O*NET snapshot",
    )
    add(
        "runs_missing_traceability",
        session.scalar(
            select(func.count())
            .select_from(RecommendationRun)
            .outerjoin(OnetSnapshot, RecommendationRun.onet_snapshot_id == OnetSnapshot.id)
            .outerjoin(
                QuestionnaireVersion,
                RecommendationRun.questionnaire_version_id == QuestionnaireVersion.id,
            )
            .outerjoin(RecommendationConfig, RecommendationRun.config_id == RecommendationConfig.id)
            .where(
                (OnetSnapshot.id.is_(None))
                | (QuestionnaireVersion.id.is_(None))
                | (RecommendationConfig.id.is_(None))
                | (RecommendationRun.feature_version.is_(None))
            )
        )
        or 0,
        "runs missing snapshot, questionnaire, config, or feature version",
    )
    snapshot = session.scalar(select(OnetSnapshot).where(OnetSnapshot.feature_version == FEATURE_VERSION))
    knowledge_ids: set[str] = set()
    if snapshot is not None:
        knowledge_ids = set(
            session.scalars(
                select(OccupationFeature.element_id)
                .where(OccupationFeature.snapshot_id == snapshot.id, OccupationFeature.domain == "knowledge")
                .distinct()
            )
        )
    invalid_priors = 0
    for prior in session.scalars(select(FacultyKnowledgePrior)):
        if knowledge_ids and prior.element_id not in knowledge_ids:
            invalid_priors += 1
    add("invalid_faculty_prior_elements", invalid_priors, "faculty priors whose element_id is not a knowledge feature")

    questionnaire = session.scalar(
        select(QuestionnaireVersion).where(QuestionnaireVersion.version == QUESTIONNAIRE_VERSION)
    )
    question_issues = 0
    if questionnaire is None:
        question_issues = 1
    else:
        questions = list(session.scalars(select(Question).where(Question.questionnaire_version_id == questionnaire.id)))
        if not questions:
            question_issues += 1
        if questionnaire.feature_version != FEATURE_VERSION:
            question_issues += 1
        if questionnaire.status != "published":
            question_issues += 1
    add("questionnaire_inconsistency", question_issues, "questionnaire_v1 missing, unpublished, or wrong feature version")

    invalid_question_elements = 0
    if snapshot is not None and questionnaire is not None:
        catalog_ids = set(
            session.scalars(
                select(OccupationFeature.element_id).where(OccupationFeature.snapshot_id == snapshot.id).distinct()
            )
        )
        for question in session.scalars(select(Question).where(Question.questionnaire_version_id == questionnaire.id)):
            if question.onet_element_id and question.onet_element_id not in catalog_ids:
                if question.block not in {"profile", "work_context"}:
                    invalid_question_elements += 1
        for option in session.scalars(
            select(QuestionOption).join(Question).where(Question.questionnaire_version_id == questionnaire.id)
        ):
            if option.onet_element_id and option.onet_element_id not in catalog_ids:
                invalid_question_elements += 1
    add(
        "invalid_onet_element_references",
        invalid_question_elements,
        "questionnaire element IDs absent from the active O*NET snapshot",
    )
    return findings


def run_integrity_checks(url: str) -> IntegrityReport:
    name = assert_evaluation_target(url, mutating=False)
    engine, factory = _session_factory(url)
    session = factory()
    try:
        findings = collect_integrity_findings(session)
        return IntegrityReport(database_name=name, passed=all(item.ok for item in findings), findings=findings)
    finally:
        session.close()
        engine.dispose()


_EXPORT_FORBIDDEN_KEYS = {
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


def _assert_export_row(row: dict[str, Any]) -> None:
    keys = {key.lower() for key in row}
    leaked = keys & _EXPORT_FORBIDDEN_KEYS
    if leaked:
        raise RuntimeError(f"Refusing to export forbidden field(s): {sorted(leaked)}")
    blob = json.dumps(row).lower()
    for token in ("password_hash", "auth_secret", "$argon2"):
        if token in blob:
            raise RuntimeError(f"Export payload contains forbidden secret material ({token})")


def export_evaluation_results(url: str, output_dir: Path) -> Path:
    assert_evaluation_target(url, mutating=False)
    engine, factory = _session_factory(url)
    session = factory()
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = output_dir / f"evaluation_export_{stamp}"
    target.mkdir(parents=True, exist_ok=True)
    try:
        rows: list[dict[str, Any]] = []
        runs = session.scalars(select(RecommendationRun).order_by(RecommendationRun.created_at)).all()
        snapshots = {row.id: row for row in session.scalars(select(OnetSnapshot))}
        questionnaires = {row.id: row for row in session.scalars(select(QuestionnaireVersion))}
        configs = {row.id: row for row in session.scalars(select(RecommendationConfig))}
        profiles = {row.user_id: row for row in session.scalars(select(StudentProfile))}
        for run in runs:
            snapshot = snapshots.get(run.onet_snapshot_id)
            questionnaire = questionnaires.get(run.questionnaire_version_id)
            config = configs.get(run.config_id)
            profile = profiles.get(run.student_user_id)
            items = session.scalars(
                select(RecommendationItem)
                .where(RecommendationItem.run_id == run.id)
                .order_by(RecommendationItem.rank)
            ).all()
            for item in items:
                rating = session.scalar(
                    select(RecommendationRating).where(
                        RecommendationRating.item_id == item.id,
                        RecommendationRating.student_user_id == run.student_user_id,
                    )
                )
                occupation = session.get(Occupation, item.occupation_id)
                row = {
                    "participant_id": participant_id_for(run.student_user_id),
                    "assessment_id": str(run.assessment_id),
                    "recommendation_run_id": str(run.id),
                    "recommendation_item_id": str(item.id),
                    "rank": item.rank,
                    "onetsoc_code": item.onetsoc_code,
                    "occupation_title": occupation.title if occupation else None,
                    "raw_similarity": float(item.raw_similarity),
                    "recommendation_score": float(item.recommendation_score),
                    "relevance_rating_1_to_5": rating.relevance_1_to_5 if rating else None,
                    "feedback_comment": rating.comment if rating else None,
                    "run_created_at": run.created_at.isoformat() if run.created_at else None,
                    "questionnaire_version": questionnaire.version if questionnaire else None,
                    "onet_release": snapshot.onet_release if snapshot else None,
                    "feature_version": run.feature_version,
                    "config_version": config.version if config else None,
                    "elapsed_ms": run.elapsed_ms,
                    "faculty": profile.faculty if profile else None,
                    "department": profile.department if profile else None,
                    "level": profile.level if profile else None,
                }
                _assert_export_row(row)
                rows.append(row)
        csv_path = target / "recommendation_items.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(ITEM_EXPORT_FIELDS))
            writer.writeheader()
            writer.writerows(rows)
        (target / "recommendation_items.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
        manifest = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "database_name": sqlalchemy_url_database_name(url),
            "row_count": len(rows),
            "format": "One row per recommendation item. Ratings are relevance (1-5), not accuracy.",
            "participant_id": "Pseudonymous SHA-256 prefix of the internal user id. Not an email or name.",
            "excluded": [
                "passwords",
                "password hashes",
                "session cookies",
                "JWTs",
                "AUTH_SECRET",
                "email addresses",
                "first and last names",
                "matriculation numbers",
            ],
            "fields": list(ITEM_EXPORT_FIELDS),
            "active_feature_version": FEATURE_VERSION,
            "active_onet_release": ONET_RELEASE,
            "notes": [
                "This export is for later analysis. It is not an accuracy result.",
                "faculty/department/level are optional academic context collected for the assessment, not personal names.",
            ],
        }
        (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return target
    finally:
        session.close()
        engine.dispose()


def deterministic_assessment_payload(questionnaire: dict[str, Any]) -> dict[str, Any]:
    """Fixed complete questionnaire_v1 answers used only for determinism checks."""
    responses: list[dict[str, Any]] = []
    for question in questionnaire["questions"]:
        code = question["code"]
        if question["response_type"] == "sparse_select":
            chosen = "1.B.3.q" if code == "sia" else "2.C.3.a"
            match = next((opt for opt in question["options"] if opt["value"] == chosen), question["options"][0])
            rating = 7 if code == "sia" else 5
            responses.append({"code": code, "selections": [{"element_id": match["value"], "value": rating}]})
        elif question["response_type"] == "choice":
            value = {
                "level": "300",
                "further_study": "maybe",
                "course_relatedness": "open",
                "faculty": "Natural and Applied Sciences",
            }.get(code, question["options"][0]["value"])
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
                value = 4 if question.get("max_value") == 7 else 3
            responses.append({"code": code, "value": value})
    return {"questionnaire_version": questionnaire["version"], "responses": responses}


def _item_signature(item: dict[str, Any]) -> dict[str, Any]:
    firings = [
        {
            "rule_code": row.get("rule_code"),
            "action": row.get("action"),
            "penalty": row.get("penalty"),
        }
        for row in [*(item.get("rule_flags") or []), *(item.get("penalties") or [])]
    ]
    return {
        "onetsoc_code": item["onetsoc_code"],
        "rank": item["rank"],
        "raw_similarity": item["raw_similarity"],
        "recommendation_score": item["recommendation_score"],
        "rule_outcomes": firings,
    }


def compare_recommendation_runs(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    left = [_item_signature(item) for item in first["items"]]
    right = [_item_signature(item) for item in second["items"]]
    return {
        "identical_soc_order": [item["onetsoc_code"] for item in left] == [item["onetsoc_code"] for item in right],
        "identical_ranks": [item["rank"] for item in left] == [item["rank"] for item in right],
        "identical_similarities": [item["raw_similarity"] for item in left]
        == [item["raw_similarity"] for item in right],
        "identical_final_scores": [item["recommendation_score"] for item in left]
        == [item["recommendation_score"] for item in right],
        "identical_rule_outcomes": [item["rule_outcomes"] for item in left]
        == [item["rule_outcomes"] for item in right],
        "first_soc_codes": [item["onetsoc_code"] for item in left],
        "second_soc_codes": [item["onetsoc_code"] for item in right],
    }


def _bind_app_to_url(url: str):
    os.environ["DATABASE_URL"] = url
    from app.core.config import get_settings
    from app.db.session import get_engine

    get_settings.cache_clear()
    get_engine.cache_clear()
    from app.main import app

    return app


def run_determinism_check(url: str) -> dict[str, Any]:
    """Submit the same assessment twice against the evaluation database."""
    assert_evaluation_target(url, mutating=True)
    from fastapi.testclient import TestClient

    from tests.api.conftest import TEST_PASSWORD

    app = _bind_app_to_url(url)
    with TestClient(app) as client:
        email = f"determinism-{int(time.time())}@example.com"
        register = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": TEST_PASSWORD, "first_name": "Eval", "last_name": "Check"},
        )
        if register.status_code != 200:
            raise RuntimeError(f"Could not register determinism user: {register.text}")
        questionnaire = client.get("/api/v1/questionnaires/active").json()
        payload = deterministic_assessment_payload(questionnaire)
        first = client.post("/api/v1/assessments", json=payload)
        second = client.post("/api/v1/assessments", json=payload)
        if first.status_code != 200 or second.status_code != 200:
            raise RuntimeError(f"Assessment failed: {first.text} {second.text}")
        comparison = compare_recommendation_runs(first.json(), second.json())
        comparison["questionnaire_version"] = first.json()["questionnaire_version"]
        comparison["feature_version"] = first.json()["feature_version"]
        comparison["config_version"] = first.json()["config_version"]
        comparison["onet_release"] = first.json()["onet_release"]
        comparison["deterministic"] = all(
            comparison[key]
            for key in (
                "identical_soc_order",
                "identical_ranks",
                "identical_similarities",
                "identical_final_scores",
                "identical_rule_outcomes",
            )
        )
        comparison["note"] = (
            "Determinism means the same inputs produced the same ranking. "
            "It is not a measure of statistical accuracy or career-prediction quality."
        )
        return comparison


def run_performance_baseline(url: str, *, repeats: int = 3) -> dict[str, Any]:
    """Local development timings only. Not a production performance claim."""
    assert_evaluation_target(url, mutating=True)
    from fastapi.testclient import TestClient

    from tests.api.conftest import TEST_PASSWORD

    app = _bind_app_to_url(url)
    questionnaire_ms: list[float] = []
    submit_ms: list[float] = []
    retrieve_ms: list[float] = []
    generation_ms: list[int] = []
    with TestClient(app) as client:
        email = f"baseline-{int(time.time())}@example.com"
        created = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": TEST_PASSWORD},
        )
        if created.status_code != 200:
            raise RuntimeError(f"Could not register baseline user: {created.text}")
        questionnaire = client.get("/api/v1/questionnaires/active").json()
        payload = deterministic_assessment_payload(questionnaire)
        for _ in range(repeats):
            started = time.perf_counter()
            q = client.get("/api/v1/questionnaires/active")
            questionnaire_ms.append((time.perf_counter() - started) * 1000)
            if q.status_code != 200:
                raise RuntimeError(q.text)
            started = time.perf_counter()
            submitted = client.post("/api/v1/assessments", json=payload)
            submit_ms.append((time.perf_counter() - started) * 1000)
            if submitted.status_code != 200:
                raise RuntimeError(submitted.text)
            body = submitted.json()
            if body.get("elapsed_ms") is not None:
                generation_ms.append(int(body["elapsed_ms"]))
            started = time.perf_counter()
            fetched = client.get(f"/api/v1/recommendations/{body['id']}")
            retrieve_ms.append((time.perf_counter() - started) * 1000)
            if fetched.status_code != 200:
                raise RuntimeError(fetched.text)

    def summarize(samples: list[float]) -> dict[str, float]:
        return {
            "n": len(samples),
            "min_ms": round(min(samples), 2),
            "median_ms": round(statistics.median(samples), 2),
            "max_ms": round(max(samples), 2),
        }

    return {
        "label": "DEVELOPMENT BASELINE",
        "disclaimer": (
            "These timings were collected on a local development machine with TestClient. "
            "They are not production performance, not a scalability result, and not an SLA."
        ),
        "questionnaire_retrieval": summarize(questionnaire_ms),
        "assessment_submission_and_recommendation_generation": summarize(submit_ms),
        "stored_recommendation_generation_elapsed_ms": summarize([float(v) for v in generation_ms])
        if generation_ms
        else None,
        "recommendation_retrieval": summarize(retrieve_ms),
        "repeats": repeats,
    }


def default_export_dir() -> Path:
    return REPO_ROOT / "data" / "evaluation" / "exports"


def configured_evaluation_url(explicit: str | None = None) -> str:
    return resolve_evaluation_database_url(explicit)
