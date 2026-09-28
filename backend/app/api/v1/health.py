from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.api import HealthResponse
from app.services.health_service import get_health

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(session: Session = Depends(db_session)) -> HealthResponse:
    return get_health(session)
