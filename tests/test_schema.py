from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.models import (
    Assessment,
    AssessmentResponse,
    FacultyKnowledgePrior,
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

REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://apple@localhost:5432/nsuk_career_test",
)
ADMIN_URL = os.environ.get(
    "POSTGRES_ADMIN_URL",
    "postgresql+psycopg://apple@localhost:5432/postgres",
)


def _alembic_config(url: str) -> Config:
    cfg = Config(str(REPO_ROOT / "backend" / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "backend" / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    os.environ["DATABASE_URL"] = url
    return cfg


def _ensure_database() -> None:
    db_name = TEST_DATABASE_URL.rsplit("/", 1)[-1]
    admin = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT", future=True)
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": db_name}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    admin.dispose()


@pytest.fixture(scope="module")
def engine():
    previous_url = os.environ.get("DATABASE_URL")
    _ensure_database()
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    raw = create_engine(TEST_DATABASE_URL, isolation_level="AUTOCOMMIT", future=True)
    with raw.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    raw.dispose()
    cfg = _alembic_config(TEST_DATABASE_URL)
    command.upgrade(cfg, "head")
    eng = create_engine(TEST_DATABASE_URL, future=True)
    try:
        yield eng
    finally:
        eng.dispose()
        if previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_url


@pytest.fixture
def session(engine):
    SessionLocal = sessionmaker(bind=engine, future=True)
    session = SessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


def test_migrations_apply_on_empty_database(engine) -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    expected = {
        "users",
        "student_profiles",
        "questionnaire_versions",
        "questions",
        "question_options",
        "assessments",
        "assessment_responses",
        "onet_snapshots",
        "occupations",
        "occupation_features",
        "job_zone_definitions",
        "education_categories",
        "recommendation_configs",
        "recommendation_runs",
        "recommendation_items",
        "recommendation_contributions",
        "rule_firings",
        "recommendation_ratings",
        "faculty_knowledge_priors",
        "faculty_knowledge_prior_audits",
        "rules",
        "system_config",
        "alembic_version",
    }
    assert expected <= tables


def test_downgrade_and_upgrade_again(engine) -> None:
    cfg = _alembic_config(TEST_DATABASE_URL)
    command.downgrade(cfg, "base")
    inspector = inspect(engine)
    assert "users" not in inspector.get_table_names()
    command.upgrade(cfg, "head")
    assert "recommendation_runs" in inspect(engine).get_table_names()


def test_unique_email_and_password_is_hash_column(session: Session) -> None:
    user = User(email="student@example.edu", password_hash="argon2id$placeholder-not-plaintext", role="student")
    session.add(user)
    session.commit()
    session.add(User(email="student@example.edu", password_hash="other-hash", role="student"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    columns = {col["name"] for col in inspect(session.get_bind()).get_columns("users")}
    assert "password" not in columns
    assert "password_hash" in columns


def test_foreign_keys_reject_orphan_responses(session: Session) -> None:
    session.add(
        AssessmentResponse(
            id=uuid.uuid4(),
            assessment_id=uuid.uuid4(),
            question_id=uuid.uuid4(),
            raw_value="4",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_required_indexes_exist(engine) -> None:
    inspector = inspect(engine)
    occ_indexes = {idx["name"] for idx in inspector.get_indexes("occupations")}
    assert "ix_occupations_snapshot_recommendable" in occ_indexes
    feature_indexes = {idx["name"] for idx in inspector.get_indexes("occupation_features")}
    assert "ix_occupation_features_snapshot_domain_element" in feature_indexes
    run_indexes = {idx["name"] for idx in inspector.get_indexes("recommendation_runs")}
    assert "ix_recommendation_runs_created_at" in run_indexes


def test_unique_constraints_on_ratings_and_priors(session: Session, engine) -> None:
    uniques = inspect(engine).get_unique_constraints("recommendation_ratings")
    names = {item["name"] for item in uniques}
    assert "uq_recommendation_ratings_item_student" in names
    prior_uniques = {item["name"] for item in inspect(engine).get_unique_constraints("faculty_knowledge_priors")}
    assert "uq_faculty_knowledge_priors" in prior_uniques


def test_faculty_priors_table_starts_empty(session: Session) -> None:
    assert session.query(FacultyKnowledgePrior).count() == 0


def test_seeded_rules_and_config(session: Session) -> None:
    codes = {row.code for row in session.query(RuleDefinition).all()}
    assert codes == {"R-DATA", "R-SUPPRESS", "R-ZONE-LOW", "R-ZONE-5", "R-RELATED", "R-CONTEXT", "R-EDU"}
    config = session.query(RecommendationConfig).filter_by(version="config_v1").one()
    assert config.k == 10
    assert config.block_weights_json["riasec"] == 0.25
    active = session.get(SystemConfig, "active_feature_version")
    assert active is not None
    assert active.value_json["value"] == "onet_30_3_v1"


def test_seeded_questionnaire_v1(session: Session) -> None:
    from app.recommendation.constants import (
        ESSENTIAL_INTERNAL_NAMES,
        RIASEC_INTERNAL_NAMES,
        TRANSFERABLE_INTERNAL_NAMES,
        WORK_STYLE_INTERNAL_NAMES,
    )

    qv = session.query(QuestionnaireVersion).filter_by(version="questionnaire_v1").one()
    assert qv.feature_version == "onet_30_3_v1"
    assert qv.status == "published"
    questions = session.query(Question).filter_by(questionnaire_version_id=qv.id).all()
    by_code = {row.code: row for row in questions}
    for code, element_id in RIASEC_INTERNAL_NAMES.items():
        assert by_code[code].onet_element_id == element_id
        assert by_code[code].is_required is True
    for code, element_id in ESSENTIAL_INTERNAL_NAMES.items():
        assert by_code[code].onet_element_id == element_id
    for code, element_id in TRANSFERABLE_INTERNAL_NAMES.items():
        assert by_code[code].onet_element_id == element_id
    for code, element_id in WORK_STYLE_INTERNAL_NAMES.items():
        assert by_code[code].onet_element_id == element_id
    assert by_code["sia"].response_type == "sparse_select"
    assert by_code["knowledge"].response_type == "sparse_select"
    assert by_code["further_study"].is_required is True
    assert by_code["faculty"].is_required is False
    assert session.query(QuestionOption).filter_by(question_id=by_code["sia"].id).count() == 41
    assert session.query(QuestionOption).filter_by(question_id=by_code["knowledge"].id).count() == 33
    active_q = session.get(SystemConfig, "active_questionnaire_version")
    assert active_q.value_json["value"] == "questionnaire_v1"


def test_historical_recommendation_survives_new_onet_snapshot(session: Session) -> None:
    student = User(email="hist@example.edu", password_hash="argon2id$placeholder", role="student")
    session.add(student)
    session.flush()
    session.add(StudentProfile(user_id=student.id, faculty=None, department=None))

    qv = QuestionnaireVersion(version="q_test_v1", feature_version="onet_30_3_v1", status="published")
    session.add(qv)
    session.flush()
    question = Question(
        questionnaire_version_id=qv.id,
        code="riasec_investigative",
        section="riasec",
        prompt="Investigative work",
        response_type="likert",
        onet_element_id="1.B.1.b",
        onet_scale_id="OI",
        block="riasec",
        min_value=1,
        max_value=7,
    )
    session.add(question)

    snap1 = OnetSnapshot(feature_version="onet_30_3_v1", onet_release="30.3")
    session.add(snap1)
    session.flush()
    occ_v1 = Occupation(
        snapshot_id=snap1.id,
        onetsoc_code="15-1252.00",
        title="Software Developers",
        description="Original snapshot title",
        job_zone=4,
        knn_complete=True,
        recommendable=True,
    )
    session.add(occ_v1)
    session.flush()
    session.add(
        OccupationFeature(
            snapshot_id=snap1.id,
            occupation_id=occ_v1.id,
            domain="riasec",
            element_id="1.B.1.b",
            element_name="Investigative",
            scale_id="OI",
            raw_value=6.5,
            used_value=6.5,
            normalized_value=0.916667,
            include_in_knn=True,
        )
    )

    assessment = Assessment(
        student_user_id=student.id,
        questionnaire_version_id=qv.id,
        onet_snapshot_id=snap1.id,
        feature_version="onet_30_3_v1",
        status="completed",
    )
    session.add(assessment)
    session.flush()
    session.add(
        AssessmentResponse(
            assessment_id=assessment.id,
            question_id=question.id,
            raw_value="7",
            normalized_value=1.0,
            onet_element_id="1.B.1.b",
        )
    )

    config = session.query(RecommendationConfig).filter_by(version="config_v1").one()
    run = RecommendationRun(
        assessment_id=assessment.id,
        student_user_id=student.id,
        questionnaire_version_id=qv.id,
        onet_snapshot_id=snap1.id,
        config_id=config.id,
        feature_version="onet_30_3_v1",
        k=10,
        metric=config.metric,
        eligible_count=1,
        weights_json=config.block_weights_json,
    )
    session.add(run)
    session.flush()
    item = RecommendationItem(
        run_id=run.id,
        occupation_id=occ_v1.id,
        onetsoc_code="15-1252.00",
        rank=1,
        distance=0.1,
        raw_similarity=0.9,
        recommendation_score=0.9,
        explanation_summary="Recommended because Investigative is high. Similarity, not predicted success.",
    )
    session.add(item)
    session.flush()
    session.add(
        RecommendationContribution(
            item_id=item.id,
            block="riasec",
            element_id="1.B.1.b",
            element_name="Investigative",
            student_raw=7,
            student_normalized=1,
            occupation_raw=6.5,
            occupation_normalized=0.916667,
            note="Student and occupation are both high on this interest type",
        )
    )
    session.add(
        RuleFiring(
            run_id=run.id,
            item_id=item.id,
            occupation_id=occ_v1.id,
            onetsoc_code="15-1252.00",
            rule_code="R-ZONE-5",
            action="flag",
            reason="not applicable here",
        )
    )
    session.add(
        RecommendationRating(
            item_id=item.id,
            student_user_id=student.id,
            relevance_1_to_5=4,
            comment="Useful as a discussion prompt",
        )
    )
    session.commit()

    snap2 = OnetSnapshot(feature_version="onet_30_4_v1", onet_release="30.4")
    session.add(snap2)
    session.flush()
    session.add(
        Occupation(
            snapshot_id=snap2.id,
            onetsoc_code="15-1252.00",
            title="Software Developers (revised title)",
            description="Later snapshot must not overwrite history",
            job_zone=4,
            knn_complete=True,
            recommendable=True,
        )
    )
    session.commit()

    stored_item = session.get(RecommendationItem, item.id)
    stored_occ = session.get(Occupation, stored_item.occupation_id)
    assert stored_occ.title == "Software Developers"
    assert stored_item.run.feature_version == "onet_30_3_v1"
    assert stored_item.run.onet_snapshot_id == snap1.id
    assert session.query(Occupation).filter_by(onetsoc_code="15-1252.00").count() == 2
