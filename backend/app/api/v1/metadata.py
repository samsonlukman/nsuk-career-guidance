from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.recommendation.constants import COURSE_RELATEDNESS_VALUES, FURTHER_STUDY_VALUES, LEVEL_VALUES
from app.schemas.api import RecommendationMetadataResponse
from app.schemas.auth import ProfileOptionsOut
from app.services.questionnaire_seed import NSUK_FACULTIES
from app.services.recommendation_service import get_recommendation_metadata

router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.get("/recommendation", response_model=RecommendationMetadataResponse)
def recommendation_metadata(session: Session = Depends(db_session)) -> RecommendationMetadataResponse:
    return get_recommendation_metadata(session)


@router.get("/profile-options", response_model=ProfileOptionsOut)
def profile_options() -> ProfileOptionsOut:
    return ProfileOptionsOut(
        faculties=list(NSUK_FACULTIES),
        levels=sorted(LEVEL_VALUES),
        further_study=sorted(FURTHER_STUDY_VALUES),
        course_relatedness=sorted(COURSE_RELATEDNESS_VALUES),
    )
