import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_student, get_current_user, require_trusted_origin
from app.models import User
from app.schemas.recommendation import (
    ExperienceEvaluationCreateRequest,
    ExperienceEvaluationOut,
    RatingCreateRequest,
    RatingOut,
    RecommendationHistoryOut,
    RecommendationRunOut,
)
from app.services.experience_evaluation_service import get_experience_evaluation, submit_experience_evaluation
from app.services.recommendation_service import list_student_runs, rate_recommendation_item, serialize_run

router = APIRouter(tags=["recommendations"])


@router.get("/me/recommendations", response_model=RecommendationHistoryOut)
def my_recommendations(
    student: User = Depends(get_current_student),
    session: Session = Depends(db_session),
) -> RecommendationHistoryOut:
    return list_student_runs(session, student_id=student.id, actor=student)


@router.get("/recommendations/{run_id}", response_model=RecommendationRunOut)
def get_recommendation_run(
    run_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(db_session),
) -> RecommendationRunOut:
    return serialize_run(session, run_id, actor=user)


@router.post(
    "/recommendations/{item_id}/rating",
    response_model=RatingOut,
    dependencies=[Depends(require_trusted_origin)],
)
def rate_recommendation(
    item_id: uuid.UUID,
    payload: RatingCreateRequest,
    student: User = Depends(get_current_student),
    session: Session = Depends(db_session),
) -> RatingOut:
    return rate_recommendation_item(session, item_id=item_id, actor=student, payload=payload)


@router.get(
    "/recommendations/{run_id}/experience-evaluation",
    response_model=ExperienceEvaluationOut,
)
def read_experience_evaluation(
    run_id: uuid.UUID,
    student: User = Depends(get_current_student),
    session: Session = Depends(db_session),
) -> ExperienceEvaluationOut:
    return get_experience_evaluation(session, run_id=run_id, actor=student)


@router.post(
    "/recommendations/{run_id}/experience-evaluation",
    response_model=ExperienceEvaluationOut,
    dependencies=[Depends(require_trusted_origin)],
)
def create_experience_evaluation(
    run_id: uuid.UUID,
    payload: ExperienceEvaluationCreateRequest,
    student: User = Depends(get_current_student),
    session: Session = Depends(db_session),
) -> ExperienceEvaluationOut:
    return submit_experience_evaluation(session, run_id=run_id, actor=student, payload=payload)
