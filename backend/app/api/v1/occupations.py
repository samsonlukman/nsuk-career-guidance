from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.api import OccupationDetail, OccupationListResponse
from app.services.occupation_service import get_occupation, list_occupations

router = APIRouter(prefix="/occupations", tags=["occupations"])


@router.get("", response_model=OccupationListResponse)
def list_occupation_rows(
    session: Session = Depends(db_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    recommendable: bool | None = Query(None),
) -> OccupationListResponse:
    return list_occupations(session, page=page, page_size=page_size, recommendable=recommendable)


@router.get("/{soc_code}", response_model=OccupationDetail)
def get_occupation_row(soc_code: str, session: Session = Depends(db_session)) -> OccupationDetail:
    return get_occupation(session, soc_code)
