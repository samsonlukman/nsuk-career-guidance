from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.recommendation import QuestionnaireOut
from app.services.questionnaire_service import get_active_questionnaire, get_questionnaire

router = APIRouter(prefix="/questionnaires", tags=["questionnaires"])


@router.get("/active", response_model=QuestionnaireOut)
def active_questionnaire(session: Session = Depends(db_session)) -> QuestionnaireOut:
    return get_active_questionnaire(session)


@router.get("/{version}", response_model=QuestionnaireOut)
def questionnaire_version(version: str, session: Session = Depends(db_session)) -> QuestionnaireOut:
    return get_questionnaire(session, version)
