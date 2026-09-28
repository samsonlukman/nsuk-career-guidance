from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_user, require_trusted_origin
from app.core.cookies import clear_session_cookie, set_session_cookie
from app.models import User
from app.schemas.auth import CurrentUserOut, LoginRequest, RegisterRequest
from app.services.auth_service import authenticate_user, register_student, user_to_out

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=CurrentUserOut, dependencies=[Depends(require_trusted_origin)])
def register(payload: RegisterRequest, response: Response, session: Session = Depends(db_session)) -> CurrentUserOut:
    user, token = register_student(session, payload)
    set_session_cookie(response, token)
    return user_to_out(user)


@router.post("/login", response_model=CurrentUserOut, dependencies=[Depends(require_trusted_origin)])
def login(payload: LoginRequest, response: Response, session: Session = Depends(db_session)) -> CurrentUserOut:
    user, token = authenticate_user(session, payload)
    set_session_cookie(response, token)
    return user_to_out(user)


@router.post("/logout", dependencies=[Depends(require_trusted_origin)])
def logout(response: Response) -> dict[str, str]:
    clear_session_cookie(response)
    return {"status": "ok"}


@router.get("/me", response_model=CurrentUserOut)
def me(user: User = Depends(get_current_user)) -> CurrentUserOut:
    return user_to_out(user)
