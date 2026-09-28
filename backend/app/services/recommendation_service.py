"""Boundary between HTTP and the recommendation engine.

KNN, feature formulas, rules, and O*NET parsing stay in app.recommendation.
This module loads runtime configuration, calls pipeline.recommend, and
persists/reads recommendation runs. It does not recompute on GET.
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ForbiddenError, NotFoundError, ServiceUnavailableError
from app.models import (
    Assessment,
    FacultyKnowledgePrior,
    Occupation,
    OccupationFeature,
    OnetSnapshot,
    QuestionnaireVersion,
    RecommendationConfig,
    RecommendationContribution,
    RecommendationItem,
    RecommendationRating,
    RecommendationRun,
    RuleDefinition,
    RuleFiring,
    SystemConfig,
    User,
)
from app.recommendation.constants import ALLOWED_K, BLOCK_WEIGHTS, DEFAULT_JOB_ZONES, FEATURE_VERSION
from app.recommendation.pipeline import RecommendationResult, recommend
from app.recommendation.rules import RuleConfig
from app.recommendation.runtime import get_occupation_index
from app.recommendation.student_features import StudentAssessment
from app.schemas.api import RecommendationConfigPublic, RecommendationMetadataResponse
from app.schemas.recommendation import (
    FeatureContributionOut,
    RatingCreateRequest,
    RatingOut,
    RecommendationHistoryItemOut,
    RecommendationHistoryOut,
    RecommendationItemOut,
    RecommendationRunOut,
    RuleFiringOut,
)


def _config_value(session: Session, key: str, default: str | None) -> str | None:
    row = session.get(SystemConfig, key)
    if row is None:
        return default
    value = (row.value_json or {}).get("value")
    if value is None:
        return default
    return str(value)


def get_recommendation_metadata(session: Session) -> RecommendationMetadataResponse:
    feature_version = _config_value(session, "active_feature_version", FEATURE_VERSION) or FEATURE_VERSION
    config_version = _config_value(session, "active_config_version", "config_v1") or "config_v1"
    config = session.scalar(select(RecommendationConfig).where(RecommendationConfig.version == config_version))
    if config is None:
        raise NotFoundError(f"Recommendation config {config_version} was not found")

    snapshot = session.scalar(select(OnetSnapshot).where(OnetSnapshot.feature_version == feature_version))
    weights = dict(config.block_weights_json or BLOCK_WEIGHTS)
    public = RecommendationConfigPublic(
        version=config.version,
        k=config.k,
        metric=config.metric,
        block_weights=weights,
    )
    return RecommendationMetadataResponse(
        feature_version=feature_version,
        onet_release=snapshot.onet_release if snapshot else None,
        onet_release_month=snapshot.onet_release_month if snapshot else None,
        snapshot_id=str(snapshot.id) if snapshot else None,
        config=public,
        k=config.k,
        metric=config.metric,
        block_weights=weights,
        allowed_k=sorted(ALLOWED_K),
        default_job_zones=list(DEFAULT_JOB_ZONES),
    )


def rule_config_from_db(session: Session) -> RuleConfig:
    enabled = {row.code: row.enabled for row in session.scalars(select(RuleDefinition)).all()}
    priors: dict[str, list[str]] = defaultdict(list)
    for row in session.scalars(select(FacultyKnowledgePrior)).all():
        priors[row.faculty].append(row.element_id)
    config = RuleConfig(
        faculty_knowledge_priors={faculty: tuple(ids) for faculty, ids in priors.items()},
    )
    if enabled:
        config.enabled.update(enabled)
    return config


def persist_recommendation_run(
    session: Session,
    *,
    student: User,
    assessment: Assessment,
    questionnaire: QuestionnaireVersion,
    snapshot: OnetSnapshot,
    config: RecommendationConfig,
    student_assessment: StudentAssessment,
) -> RecommendationRunOut:
    try:
        index = get_occupation_index()
    except FileNotFoundError as exc:
        raise ServiceUnavailableError("Processed O*NET snapshot is not available") from exc
    started = time.perf_counter()
    result = recommend(
        student_assessment,
        index,
        k=config.k,
        rule_config=rule_config_from_db(session),
    )
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return _save_result(
        session,
        student=student,
        assessment=assessment,
        questionnaire=questionnaire,
        snapshot=snapshot,
        config=config,
        result=result,
        elapsed_ms=elapsed_ms,
    )


def _save_result(
    session: Session,
    *,
    student: User,
    assessment: Assessment,
    questionnaire: QuestionnaireVersion,
    snapshot: OnetSnapshot,
    config: RecommendationConfig,
    result: RecommendationResult,
    elapsed_ms: int,
) -> RecommendationRunOut:
    run = RecommendationRun(
        assessment_id=assessment.id,
        student_user_id=student.id,
        questionnaire_version_id=questionnaire.id,
        onet_snapshot_id=snapshot.id,
        config_id=config.id,
        feature_version=result.feature_version,
        k=result.k,
        metric=result.metric,
        eligible_count=result.eligible_count,
        elapsed_ms=elapsed_ms,
        weights_json=dict(config.block_weights_json or BLOCK_WEIGHTS),
    )
    session.add(run)
    session.flush()

    codes = [item.onetsoc_code for item in result.items]
    occupations = {
        row.onetsoc_code: row
        for row in session.scalars(
            select(Occupation).where(
                Occupation.snapshot_id == snapshot.id,
                Occupation.onetsoc_code.in_(codes),
            )
        ).all()
    }
    for ranked in result.items:
        occupation = occupations.get(ranked.onetsoc_code)
        if occupation is None:
            raise ServiceUnavailableError(
                f"Occupation {ranked.onetsoc_code} is missing from the active snapshot"
            )
        item = RecommendationItem(
            run_id=run.id,
            occupation_id=occupation.id,
            onetsoc_code=ranked.onetsoc_code,
            rank=ranked.rank,
            distance=ranked.distance,
            raw_similarity=ranked.raw_similarity,
            recommendation_score=ranked.recommendation_score,
            explanation_summary=ranked.explanation.summary,
            job_zone_note=ranked.explanation.job_zone_note,
        )
        session.add(item)
        session.flush()
        for contribution in ranked.explanation.contributions:
            session.add(
                RecommendationContribution(
                    item_id=item.id,
                    block=contribution.block,
                    element_id=contribution.element_id,
                    element_name=contribution.element_name,
                    student_raw=contribution.student_raw,
                    student_normalized=contribution.student_normalized,
                    occupation_raw=contribution.occupation_raw,
                    occupation_normalized=contribution.occupation_normalized,
                    note=contribution.note,
                )
            )
        for firing in ranked.firings:
            session.add(
                RuleFiring(
                    run_id=run.id,
                    item_id=item.id,
                    occupation_id=occupation.id,
                    onetsoc_code=firing.onetsoc_code,
                    rule_code=firing.code,
                    action=firing.action,
                    penalty=firing.penalty,
                    reason=firing.reason,
                    element_id=firing.element_id,
                    domain=firing.domain,
                )
            )
    session.flush()
    return serialize_run(session, run.id, actor=student)


def _can_access_student(actor: User, student_id: uuid.UUID) -> bool:
    return actor.role == "admin" or actor.id == student_id


def serialize_run(session: Session, run_id: uuid.UUID, *, actor: User) -> RecommendationRunOut:
    run = session.scalar(
        select(RecommendationRun)
        .options(
            selectinload(RecommendationRun.items).selectinload(RecommendationItem.contributions),
            selectinload(RecommendationRun.items).selectinload(RecommendationItem.firings),
        )
        .where(RecommendationRun.id == run_id)
    )
    if run is None:
        raise NotFoundError("Recommendation run was not found", code="invalid_recommendation_run")
    if not _can_access_student(actor, run.student_user_id):
        raise ForbiddenError("Not allowed to access this recommendation run")
    return _run_out(session, run)


def list_student_runs(session: Session, *, student_id: uuid.UUID, actor: User) -> RecommendationHistoryOut:
    if not _can_access_student(actor, student_id):
        raise ForbiddenError("Not allowed to access this student's recommendation history")
    student = session.get(User, student_id)
    if student is None or student.role != "student":
        raise NotFoundError("Student was not found", code="invalid_student")
    runs = session.scalars(
        select(RecommendationRun)
        .options(selectinload(RecommendationRun.items))
        .where(RecommendationRun.student_user_id == student_id)
        .order_by(RecommendationRun.created_at.desc())
    ).all()
    snapshots = _rows_by_id(session, OnetSnapshot, {run.onet_snapshot_id for run in runs})
    questionnaires = _rows_by_id(session, QuestionnaireVersion, {run.questionnaire_version_id for run in runs})
    configs = _rows_by_id(session, RecommendationConfig, {run.config_id for run in runs})
    top_ids = []
    for run in runs:
        ranked = sorted(run.items, key=lambda item: item.rank)
        if ranked:
            top_ids.append(ranked[0].occupation_id)
    titles = _rows_by_id(session, Occupation, set(top_ids))
    items: list[RecommendationHistoryItemOut] = []
    for run in runs:
        ranked = sorted(run.items, key=lambda item: item.rank)
        top = ranked[0] if ranked else None
        items.append(
            RecommendationHistoryItemOut(
                run_id=run.id,
                created_at=run.created_at,
                k=run.k,
                feature_version=run.feature_version,
                questionnaire_version=(questionnaires[run.questionnaire_version_id].version if run.questionnaire_version_id in questionnaires else ""),
                config_version=configs[run.config_id].version if run.config_id in configs else "",
                onet_release=snapshots[run.onet_snapshot_id].onet_release if run.onet_snapshot_id in snapshots else None,
                eligible_count=run.eligible_count,
                item_count=len(run.items),
                top_occupation_title=titles[top.occupation_id].title if top and top.occupation_id in titles else None,
                top_onetsoc_code=top.onetsoc_code if top else None,
            )
        )
    return RecommendationHistoryOut(student_id=student_id, items=items)


def _rows_by_id(session: Session, model, ids: set):
    if not ids:
        return {}
    return {row.id: row for row in session.scalars(select(model).where(model.id.in_(ids))).all()}


def rate_recommendation_item(
    session: Session,
    *,
    item_id: uuid.UUID,
    actor: User,
    payload: RatingCreateRequest,
) -> RatingOut:
    item = session.scalar(
        select(RecommendationItem)
        .options(selectinload(RecommendationItem.run))
        .where(RecommendationItem.id == item_id)
    )
    if item is None:
        raise NotFoundError("Recommendation item was not found", code="invalid_recommendation_item")
    if item.run.student_user_id != actor.id:
        raise ForbiddenError("Not allowed to rate this recommendation")
    existing = session.scalar(
        select(RecommendationRating).where(
            RecommendationRating.item_id == item_id,
            RecommendationRating.student_user_id == actor.id,
        )
    )
    if existing is None:
        existing = RecommendationRating(
            item_id=item_id,
            student_user_id=actor.id,
            relevance_1_to_5=payload.relevance_1_to_5,
            comment=payload.comment,
        )
        session.add(existing)
    else:
        existing.relevance_1_to_5 = payload.relevance_1_to_5
        existing.comment = payload.comment
    session.flush()
    return RatingOut(
        id=existing.id,
        item_id=existing.item_id,
        relevance_1_to_5=existing.relevance_1_to_5,
        comment=existing.comment,
        created_at=existing.created_at,
    )


def _run_out(session: Session, run: RecommendationRun) -> RecommendationRunOut:
    snapshot = session.get(OnetSnapshot, run.onet_snapshot_id)
    questionnaire = session.get(QuestionnaireVersion, run.questionnaire_version_id)
    config = session.get(RecommendationConfig, run.config_id)
    items = sorted(run.items, key=lambda item: item.rank)
    occupation_ids = [item.occupation_id for item in items]
    occupations = _rows_by_id(session, Occupation, set(occupation_ids))
    activities = _work_activity_names(session, occupation_ids)
    return RecommendationRunOut(
        id=run.id,
        assessment_id=run.assessment_id,
        created_at=run.created_at,
        k=run.k,
        metric=run.metric,
        eligible_count=run.eligible_count,
        elapsed_ms=run.elapsed_ms,
        feature_version=run.feature_version,
        onet_release=snapshot.onet_release if snapshot else None,
        onet_snapshot_id=run.onet_snapshot_id,
        questionnaire_version=questionnaire.version if questionnaire else "",
        config_version=config.version if config else "",
        block_weights=dict(run.weights_json or {}),
        notes=["Scores are O*NET profile similarity, not predicted job success or accuracy."],
        items=[
            _item_out(item, occupations.get(item.occupation_id), activities.get(item.occupation_id, []))
            for item in items
        ],
    )


def _item_out(
    item: RecommendationItem,
    occupation: Occupation | None,
    work_activities: list[str],
) -> RecommendationItemOut:
    firings = [
        RuleFiringOut(
            rule_code=row.rule_code,
            action=row.action,
            reason=row.reason,
            penalty=float(row.penalty) if row.penalty is not None else None,
            element_id=row.element_id,
            domain=row.domain,
        )
        for row in item.firings
    ]
    return RecommendationItemOut(
        id=item.id,
        rank=item.rank,
        onetsoc_code=item.onetsoc_code,
        title=occupation.title if occupation else item.onetsoc_code,
        job_zone=occupation.job_zone if occupation else None,
        distance=float(item.distance),
        raw_similarity=float(item.raw_similarity),
        recommendation_score=float(item.recommendation_score),
        explanation=item.explanation_summary,
        job_zone_note=item.job_zone_note,
        work_activities=work_activities,
        contributing_features=[
            FeatureContributionOut(
                block=row.block,
                element_id=row.element_id,
                element_name=row.element_name,
                student_raw=float(row.student_raw) if row.student_raw is not None else None,
                student_normalized=float(row.student_normalized) if row.student_normalized is not None else None,
                occupation_raw=float(row.occupation_raw) if row.occupation_raw is not None else None,
                occupation_normalized=float(row.occupation_normalized) if row.occupation_normalized is not None else None,
                note=row.note,
            )
            for row in item.contributions
        ],
        rule_flags=[row for row in firings if row.action == "flag"],
        penalties=[row for row in firings if row.action == "penalise"],
    )


def _work_activity_names(session: Session, occupation_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[str]]:
    if not occupation_ids:
        return {}
    rows = session.scalars(
        select(OccupationFeature).where(
            OccupationFeature.occupation_id.in_(occupation_ids),
            OccupationFeature.domain == "work_activities",
        )
    ).all()
    grouped: dict[uuid.UUID, list[OccupationFeature]] = defaultdict(list)
    for row in rows:
        grouped[row.occupation_id].append(row)
    names: dict[uuid.UUID, list[str]] = {}
    for occupation_id, features in grouped.items():
        ranked = sorted(
            features,
            key=lambda row: (-float(row.used_value if row.used_value is not None else row.raw_value), row.element_id),
        )
        names[occupation_id] = [row.element_name for row in ranked[:5]]
    return names
