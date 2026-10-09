"""Registration, login, and current-user helpers. No recommendation scoring."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, UnauthorizedError, UnprocessableError
from app.core.security import create_access_token, hash_password, verify_password
from app.models import StudentProfile, User
from app.schemas.auth import CurrentUserOut, LoginRequest, ProfileOut, RegisterRequest
from app.services.questionnaire_seed import NSUK_FACULTIES


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def _normalize_institution(value: str | None) -> str | None:
    text = _clean(value)
    if text is None:
        return None
    return " ".join(text.split())


def _matric_is_taken(
    session: Session,
    *,
    matric: str,
    institution: str | None,
    exclude_user_id: object | None = None,
) -> bool:
    stmt = select(StudentProfile.user_id).where(StudentProfile.matric_number == matric)
    if institution:
        stmt = stmt.where(func.lower(StudentProfile.institution) == institution.lower())
    else:
        stmt = stmt.where(StudentProfile.institution.is_(None))
    if exclude_user_id is not None:
        stmt = stmt.where(StudentProfile.user_id != exclude_user_id)
    return session.scalar(stmt) is not None


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def user_to_out(user: User) -> CurrentUserOut:
    profile = user.profile
    return CurrentUserOut(
        id=user.id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        profile=ProfileOut(
            first_name=profile.first_name if profile else None,
            last_name=profile.last_name if profile else None,
            institution=profile.institution if profile else None,
            matric_number=profile.matric_number if profile else None,
            faculty=profile.faculty if profile else None,
            department=profile.department if profile else None,
            level=profile.level if profile else None,
            further_study=profile.further_study if profile else None,
            course_relatedness=profile.course_relatedness if profile else None,
        ),
    )


def register_student(session: Session, payload: RegisterRequest) -> tuple[User, str]:
    email = _normalize_email(str(payload.email))
    existing = session.scalar(select(User).where(func.lower(User.email) == email))
    if existing is not None:
        raise ConflictError("An account with this email already exists", code="email_taken")
    institution = _normalize_institution(payload.institution)
    matric = _clean(payload.matric_number)
    if not institution:
        raise UnprocessableError("School name is required", code="missing_student_identity")
    if matric and _matric_is_taken(session, matric=matric, institution=institution):
        raise ConflictError(
            "This matriculation number is already registered at that school",
            code="matric_taken",
        )
    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        role="student",
        is_active=True,
    )
    session.add(user)
    session.flush()
    session.add(
        StudentProfile(
            user_id=user.id,
            first_name=_clean(payload.first_name),
            last_name=_clean(payload.last_name),
            institution=institution,
            matric_number=matric,
        )
    )
    session.flush()
    session.refresh(user)
    return user, create_access_token(user_id=user.id, role=user.role)


def authenticate_user(session: Session, payload: LoginRequest) -> tuple[User, str]:
    email = _normalize_email(str(payload.email))
    user = session.scalar(select(User).where(func.lower(User.email) == email))
    if user is None or not verify_password(user.password_hash, payload.password):
        raise UnauthorizedError("Email or password is incorrect")
    if not user.is_active:
        raise UnauthorizedError("This account is inactive")
    user.last_login_at = datetime.now(timezone.utc)
    session.flush()
    return user, create_access_token(user_id=user.id, role=user.role)


def update_student_profile(session: Session, user: User, fields: dict[str, str | None]) -> User:
    profile = user.profile
    if profile is None:
        profile = StudentProfile(user_id=user.id)
        session.add(profile)
        session.flush()
        user.profile = profile

    if "faculty" in fields:
        faculty = _clean(fields.get("faculty"))
        if faculty and faculty not in NSUK_FACULTIES:
            raise UnprocessableError("Faculty must be one of the official NSUK faculties", code="invalid_faculty")
        profile.faculty = faculty
    if "level" in fields:
        level = _clean(fields.get("level"))
        if level and level not in {"100", "200", "300", "400"}:
            raise UnprocessableError("level must be 100, 200, 300, or 400", code="invalid_response")
        profile.level = level
    if "further_study" in fields:
        further = _clean(fields.get("further_study"))
        if further:
            further = further.lower()
            if further not in {"yes", "maybe", "no"}:
                raise UnprocessableError("further_study must be yes, maybe, or no", code="invalid_response")
        profile.further_study = further
    if "course_relatedness" in fields:
        related = _clean(fields.get("course_relatedness"))
        if related:
            related = related.lower()
            if related not in {"related", "open"}:
                raise UnprocessableError("course_relatedness must be related or open", code="invalid_response")
        profile.course_relatedness = related
    if "institution" in fields:
        profile.institution = _normalize_institution(fields.get("institution"))
    if "matric_number" in fields:
        profile.matric_number = _clean(fields.get("matric_number"))
    if "institution" in fields or "matric_number" in fields:
        matric = profile.matric_number
        institution = profile.institution
        if matric and _matric_is_taken(
            session,
            matric=matric,
            institution=institution,
            exclude_user_id=user.id,
        ):
            raise ConflictError(
                "This matriculation number is already registered at that school",
                code="matric_taken",
            )
    if "first_name" in fields:
        profile.first_name = _clean(fields.get("first_name"))
    if "last_name" in fields:
        profile.last_name = _clean(fields.get("last_name"))
    if "department" in fields:
        profile.department = _clean(fields.get("department"))
    session.flush()
    session.refresh(user)
    return user
