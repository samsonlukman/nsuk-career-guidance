from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_student, require_trusted_origin
from app.models import User
from app.schemas.auth import CurrentUserOut, DashboardOut, ProfileUpdateRequest
from app.services.auth_service import update_student_profile, user_to_out
from app.services.dashboard_service import get_student_dashboard

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(student: User = Depends(get_current_student), session: Session = Depends(db_session)) -> DashboardOut:
    return get_student_dashboard(session, student)


@router.put("/profile", response_model=CurrentUserOut, dependencies=[Depends(require_trusted_origin)])
def update_profile(
    payload: ProfileUpdateRequest,
    student: User = Depends(get_current_student),
    session: Session = Depends(db_session),
) -> CurrentUserOut:
    user = update_student_profile(session, student, payload.model_dump(exclude_unset=True))
    return user_to_out(user)
