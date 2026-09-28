"""Database connectivity for the health endpoint."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceUnavailableError
from app.schemas.api import HealthResponse
from app.services.occupation_service import active_feature_version, get_active_snapshot


def get_health(session: Session) -> HealthResponse:
    try:
        session.execute(text("SELECT 1"))
    except Exception as exc:
        raise ServiceUnavailableError("Database is not reachable") from exc
    snapshot = get_active_snapshot(session)
    return HealthResponse(
        status="ok",
        database="connected",
        feature_version=snapshot.feature_version if snapshot else active_feature_version(session),
    )
