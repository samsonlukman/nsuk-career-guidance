import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user
from app.models import User
from app.schemas.recommendation import RecommendationHistoryOut
from app.services.recommendation_service import list_student_runs

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/{student_id}/recommendations", response_model=RecommendationHistoryOut)
def student_recommendations(
    student_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(db_session),
) -> RecommendationHistoryOut:
    return list_student_runs(session, student_id=student_id, actor=user)
