from collections.abc import Generator
import uuid

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_session
from app.models import User

__all__ = [
    "get_session",
    "Session",
    "db_session",
    "get_current_user",
    "get_current_student",
    "get_current_admin",
    "require_trusted_origin",
]


def db_session() -> Generator[Session, None, None]:
    yield from get_session()


def get_current_user(
    request: Request,
    session: Session = Depends(db_session),
) -> User:
    settings = get_settings()
    access_cookie = request.cookies.get(settings.auth_cookie_name)
    if not access_cookie:
        raise UnauthorizedError("Authentication required")
    payload = decode_access_token(access_cookie)
    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Session is invalid or has expired") from exc
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Authentication required")
    return user


def get_current_student(user: User = Depends(get_current_user)) -> User:
    if user.role != "student":
        raise ForbiddenError("Student role required")
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise ForbiddenError("Admin role required")
    return user


def public_request_origin(request: Request) -> str | None:
    """Origin of this request as the browser sees it, including reverse-proxy hosts."""
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if not host:
        return None
    proto = (request.headers.get("x-forwarded-proto") or request.url.scheme).split(",")[0].strip()
    return f"{proto}://{host.split(',')[0].strip()}"


def require_trusted_origin(request: Request) -> None:
    """Reject mutating requests whose Origin is not an allowed frontend origin.

    Same-origin clients and the test client may omit Origin; those are allowed.
    A present Origin that matches this request's own public host is also allowed
    so a single-host HTTPS deploy does not need the public URL hard-coded.
    Authorization still comes from the authenticated database principal.
    """
    origin = request.headers.get("origin")
    if not origin:
        return
    if origin in get_settings().cors_origin_list:
        return
    public = public_request_origin(request)
    if public and origin.rstrip("/") == public.rstrip("/"):
        return
    raise ForbiddenError("Cross-origin request rejected")
