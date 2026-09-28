from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_student, require_trusted_origin
from app.models import User
from app.schemas.recommendation import AssessmentCreateRequest, RecommendationRunOut
from app.services.assessment_service import submit_assessment

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("", response_model=RecommendationRunOut, dependencies=[Depends(require_trusted_origin)])
def create_assessment(
    payload: AssessmentCreateRequest,
    student: User = Depends(get_current_student),
    session: Session = Depends(db_session),
) -> RecommendationRunOut:
    return submit_assessment(session, student, payload)
