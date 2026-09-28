import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_admin, require_trusted_origin
from app.models import User
from app.schemas.admin import (
    AdminDashboardOut,
    AdminHealthOut,
    AdminOnetSnapshotOut,
    AdminQuestionnaireOut,
    AdminRatingListOut,
    AdminRecommendationConfigOut,
    AdminRunDetailOut,
    AdminRunListOut,
    AdminStudentDetailOut,
    AdminStudentListOut,
    FacultyKnowledgeCatalogOut,
    FacultyKnowledgePriorAuditListOut,
    FacultyKnowledgePriorListOut,
    FacultyKnowledgePriorOut,
    FacultyKnowledgePriorWrite,
)
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=AdminDashboardOut)
def admin_dashboard(
    admin: User = Depends(get_current_admin),
    session: Session = Depends(db_session),
) -> AdminDashboardOut:
    _ = admin
    return admin_service.get_admin_dashboard(session)


@router.get("/health", response_model=AdminHealthOut)
def admin_health(
    admin: User = Depends(get_current_admin),
    session: Session = Depends(db_session),
) -> AdminHealthOut:
    _ = admin
    return admin_service.get_admin_health(session)


@router.get("/students", response_model=AdminStudentListOut)
def admin_students(
    q: str | None = Query(default=None, max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    session: Session = Depends(db_session),
) -> AdminStudentListOut:
    _ = admin
    return admin_service.list_admin_students(session, query=q, page=page, page_size=page_size)


@router.get("/students/{student_id}", response_model=AdminStudentDetailOut)
def admin_student_detail(
    student_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(db_session),
) -> AdminStudentDetailOut:
    return admin_service.get_admin_student(session, student_id, actor=admin)


@router.get("/recommendation-runs", response_model=AdminRunListOut)
def admin_recommendation_runs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    session: Session = Depends(db_session),
) -> AdminRunListOut:
    _ = admin
    return admin_service.list_admin_runs(session, page=page, page_size=page_size)


@router.get("/recommendation-runs/{run_id}", response_model=AdminRunDetailOut)
def admin_recommendation_run(
    run_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(db_session),
) -> AdminRunDetailOut:
    return admin_service.get_admin_run(session, run_id, actor=admin)


@router.get("/ratings", response_model=AdminRatingListOut)
def admin_ratings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    session: Session = Depends(db_session),
) -> AdminRatingListOut:
    _ = admin
    return admin_service.list_admin_ratings(session, page=page, page_size=page_size)


@router.get("/onet-snapshot", response_model=AdminOnetSnapshotOut)
def admin_onet_snapshot(
    admin: User = Depends(get_current_admin),
    session: Session = Depends(db_session),
) -> AdminOnetSnapshotOut:
    _ = admin
    return admin_service.get_admin_onet_snapshot(session)


@router.get("/questionnaire", response_model=AdminQuestionnaireOut)
def admin_questionnaire(
    admin: User = Depends(get_current_admin),
    session: Session = Depends(db_session),
) -> AdminQuestionnaireOut:
    _ = admin
    return admin_service.get_admin_questionnaire(session)


@router.get("/recommendation-config", response_model=AdminRecommendationConfigOut)
def admin_recommendation_config(
    admin: User = Depends(get_current_admin),
    session: Session = Depends(db_session),
) -> AdminRecommendationConfigOut:
    _ = admin
    return admin_service.get_admin_recommendation_config(session)


@router.get("/faculty-knowledge-priors/catalog", response_model=FacultyKnowledgeCatalogOut)
def admin_faculty_prior_catalog(
    admin: User = Depends(get_current_admin),
    session: Session = Depends(db_session),
) -> FacultyKnowledgeCatalogOut:
    _ = admin
    return admin_service.list_knowledge_catalog(session)


@router.get("/faculty-knowledge-priors", response_model=FacultyKnowledgePriorListOut)
def admin_faculty_priors(
    admin: User = Depends(get_current_admin),
    session: Session = Depends(db_session),
) -> FacultyKnowledgePriorListOut:
    _ = admin
    return admin_service.list_faculty_priors(session)


@router.get("/faculty-knowledge-priors/audits", response_model=FacultyKnowledgePriorAuditListOut)
def admin_faculty_prior_audits(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    session: Session = Depends(db_session),
) -> FacultyKnowledgePriorAuditListOut:
    _ = admin
    return admin_service.list_faculty_prior_audits(session, page=page, page_size=page_size)


@router.post(
    "/faculty-knowledge-priors",
    response_model=FacultyKnowledgePriorOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
def admin_create_faculty_prior(
    payload: FacultyKnowledgePriorWrite,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(db_session),
) -> FacultyKnowledgePriorOut:
    return admin_service.create_faculty_prior(session, payload, actor=admin)


@router.patch(
    "/faculty-knowledge-priors/{prior_id}",
    response_model=FacultyKnowledgePriorOut,
    dependencies=[Depends(require_trusted_origin)],
)
def admin_update_faculty_prior(
    prior_id: int,
    payload: FacultyKnowledgePriorWrite,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(db_session),
) -> FacultyKnowledgePriorOut:
    return admin_service.update_faculty_prior(session, prior_id, payload, actor=admin)


@router.delete(
    "/faculty-knowledge-priors/{prior_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_trusted_origin)],
)
def admin_delete_faculty_prior(
    prior_id: int,
    admin: User = Depends(get_current_admin),
    session: Session = Depends(db_session),
) -> Response:
    admin_service.delete_faculty_prior(session, prior_id, actor=admin)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
