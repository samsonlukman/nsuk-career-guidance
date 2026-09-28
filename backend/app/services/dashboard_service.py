"""Student dashboard summary from persisted assessments and recommendation runs."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Assessment, QuestionnaireVersion, User
from app.schemas.auth import AssessmentSummaryOut, DashboardOut
from app.services.auth_service import user_to_out
from app.services.recommendation_service import list_student_runs


def get_student_dashboard(session: Session, user: User) -> DashboardOut:
    history = list_student_runs(session, student_id=user.id, actor=user)
    latest_assessment = session.scalar(
        select(Assessment)
        .where(Assessment.student_user_id == user.id)
        .order_by(Assessment.created_at.desc())
    )
    questionnaire_version = None
    if latest_assessment is not None:
        qv = session.get(QuestionnaireVersion, latest_assessment.questionnaire_version_id)
        questionnaire_version = qv.version if qv else None
    completed = bool(latest_assessment and latest_assessment.status == "completed")
    latest_run = history.items[0] if history.items else None
    return DashboardOut(
        user=user_to_out(user),
        has_completed_assessment=completed,
        latest_assessment=(
            AssessmentSummaryOut(
                id=latest_assessment.id,
                status=latest_assessment.status,
                questionnaire_version=questionnaire_version,
                feature_version=latest_assessment.feature_version,
                started_at=latest_assessment.started_at,
                completed_at=latest_assessment.completed_at,
            )
            if latest_assessment
            else None
        ),
        latest_recommendation=latest_run,
        recommendation_history=history.items,
    )
