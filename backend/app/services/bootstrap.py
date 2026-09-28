"""First-boot helpers for a hosted demo. Does not change recommendation scoring."""

from __future__ import annotations

import os

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User


def ensure_demo_admin(session: Session) -> str | None:
    """Create an admin from DEMO_ADMIN_EMAIL / DEMO_ADMIN_PASSWORD if both are set.

    Credentials stay in the host environment. Nothing is written to source.
    """
    email = (os.environ.get("DEMO_ADMIN_EMAIL") or "").strip().lower()
    password = os.environ.get("DEMO_ADMIN_PASSWORD") or ""
    if not email or len(password) < 8:
        return None
    user = session.scalar(select(User).where(func.lower(User.email) == email))
    if user is None:
        session.add(User(email=email, password_hash=hash_password(password), role="admin", is_active=True))
        session.flush()
        return "created"
    if user.role != "admin":
        return "skipped_existing_non_admin"
    user.password_hash = hash_password(password)
    user.is_active = True
    session.flush()
    return "updated"
