"""Persist student experience evaluations for a recommendation run.

Does not change KNN, rules, O*NET data, or recommendation scores.
Responses are experience, usability, usefulness, and perceived relevance —
not accuracy.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models import ExperienceEvaluation, RecommendationRun, User
from app.schemas.recommendation import ExperienceEvaluationCreateRequest, ExperienceEvaluationOut


def _normalize_comment(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _to_out(row: ExperienceEvaluation) -> ExperienceEvaluationOut:
    return ExperienceEvaluationOut(
        id=row.id,
        run_id=row.run_id,
        student_user_id=row.student_user_id,
        questions_easy_to_understand=row.questions_easy_to_understand,
        assessment_easy_to_complete=row.assessment_easy_to_complete,
        system_easy_to_navigate=row.system_easy_to_navigate,
        recommendations_easy_to_understand=row.recommendations_easy_to_understand,
        explanations_helped=row.explanations_helped,
        reflected_interests=row.reflected_interests,
        reflected_skills=row.reflected_skills,
        helped_explore_options=row.helped_explore_options,
        would_use_again=row.would_use_again,
        would_discuss_with_counsellor=row.would_discuss_with_counsellor,
        liked_most_and_improvement=row.liked_most_and_improvement,
        created_at=row.created_at,
    )


def _owned_run(session: Session, run_id: uuid.UUID, actor: User) -> RecommendationRun:
    run = session.scalar(
        select(RecommendationRun)
        .options(selectinload(RecommendationRun.experience_evaluations))
        .where(RecommendationRun.id == run_id)
    )
    if run is None:
        raise NotFoundError("Recommendation run was not found", code="invalid_recommendation_run")
    if run.student_user_id != actor.id:
        raise ForbiddenError("Not allowed to evaluate this recommendation run")
    return run


def get_experience_evaluation(session: Session, *, run_id: uuid.UUID, actor: User) -> ExperienceEvaluationOut:
    run = _owned_run(session, run_id, actor)
    row = session.scalar(
        select(ExperienceEvaluation).where(
            ExperienceEvaluation.run_id == run.id,
            ExperienceEvaluation.student_user_id == actor.id,
        )
    )
    if row is None:
        raise NotFoundError("Experience evaluation was not found", code="experience_evaluation_not_found")
    return _to_out(row)


def submit_experience_evaluation(
    session: Session,
    *,
    run_id: uuid.UUID,
    actor: User,
    payload: ExperienceEvaluationCreateRequest,
) -> ExperienceEvaluationOut:
    run = _owned_run(session, run_id, actor)
    existing = session.scalar(
        select(ExperienceEvaluation).where(
            ExperienceEvaluation.run_id == run.id,
            ExperienceEvaluation.student_user_id == actor.id,
        )
    )
    if existing is not None:
        raise ConflictError(
            "You have already submitted an experience evaluation for this recommendation run",
            code="experience_evaluation_exists",
        )
    row = ExperienceEvaluation(
        run_id=run.id,
        student_user_id=actor.id,
        questions_easy_to_understand=payload.questions_easy_to_understand,
        assessment_easy_to_complete=payload.assessment_easy_to_complete,
        system_easy_to_navigate=payload.system_easy_to_navigate,
        recommendations_easy_to_understand=payload.recommendations_easy_to_understand,
        explanations_helped=payload.explanations_helped,
        reflected_interests=payload.reflected_interests,
        reflected_skills=payload.reflected_skills,
        helped_explore_options=payload.helped_explore_options,
        would_use_again=payload.would_use_again,
        would_discuss_with_counsellor=payload.would_discuss_with_counsellor,
        liked_most_and_improvement=_normalize_comment(payload.liked_most_and_improvement),
    )
    session.add(row)
    session.flush()
    return _to_out(row)
