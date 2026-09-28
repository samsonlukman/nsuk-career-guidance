"""Admin inspection and faculty-knowledge prior management.

Does not recompute recommendations, edit O*NET rows, or change KNN configuration.
Authorization is enforced by the API layer via get_current_admin.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from math import ceil

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflictError, NotFoundError, UnprocessableError
from app.models import (
    Assessment,
    FacultyKnowledgePrior,
    FacultyKnowledgePriorAudit,
    JobZoneDefinition,
    Occupation,
    OccupationFeature,
    OnetSnapshot,
    Question,
    QuestionOption,
    QuestionnaireVersion,
    RecommendationConfig,
    RecommendationItem,
    RecommendationRating,
    RecommendationRun,
    StudentProfile,
    SystemConfig,
    User,
)
from app.schemas.admin import (
    AdminConfigSummary,
    AdminDashboardOut,
    AdminHealthOut,
    AdminJobZoneInfo,
    AdminOnetSnapshotOut,
    AdminQuestionInspectOut,
    AdminQuestionnaireOut,
    AdminQuestionnaireSummary,
    AdminRatingListItem,
    AdminRatingListOut,
    AdminRatingSummary,
    AdminRecommendationConfigOut,
    AdminRunDetailOut,
    AdminRunListItem,
    AdminRunListOut,
    AdminSnapshotSummary,
    AdminStudentAssessmentOut,
    AdminStudentDetailOut,
    AdminStudentListItem,
    AdminStudentListOut,
    AdminStudentProfileOut,
    AdminStudentRef,
    AdminSystemStatus,
    FacultyKnowledgeCatalogOut,
    FacultyKnowledgePriorAuditListOut,
    FacultyKnowledgePriorAuditOut,
    FacultyKnowledgePriorListOut,
    FacultyKnowledgePriorOut,
    FacultyKnowledgePriorWrite,
    KnowledgeElementOut,
)
from app.services.occupation_service import active_feature_version, get_active_snapshot
from app.services.questionnaire_seed import NSUK_FACULTIES
from app.services.questionnaire_service import active_questionnaire_version_name
from app.services.recommendation_service import list_student_runs, serialize_run

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20
FEEDBACK_NOTE = (
    "These values are user relevance feedback for later evaluation. "
    "They are not a measure of recommendation accuracy."
)
DASHBOARD_NOTES = [
    "Counts are taken from stored records. Nothing here is estimated.",
    "Ratings are user relevance feedback, not a measure of recommendation accuracy.",
]


def _page_bounds(page: int, page_size: int) -> tuple[int, int]:
    safe_page = max(1, page)
    safe_size = min(max(1, page_size), MAX_PAGE_SIZE)
    return safe_page, safe_size


def _total_pages(total: int, page_size: int) -> int:
    return ceil(total / page_size) if total else 0


def _like_pattern(query: str) -> str:
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _config_value(session: Session, key: str, default: str | None) -> str | None:
    row = session.get(SystemConfig, key)
    if row is None:
        return default
    value = (row.value_json or {}).get("value")
    if value is None:
        return default
    return str(value)


def _active_config(session: Session) -> RecommendationConfig | None:
    version = _config_value(session, "active_config_version", "config_v1") or "config_v1"
    return session.scalar(select(RecommendationConfig).where(RecommendationConfig.version == version))


def _knn_feature_count(snapshot: OnetSnapshot | None) -> int:
    if snapshot is None:
        return 0
    total = 0
    for spec in (snapshot.block_spec_json or {}).values():
        if not isinstance(spec, dict) or not spec.get("include_in_knn"):
            continue
        total += len(spec.get("element_ids") or [])
    return total


def _snapshot_summary(session: Session) -> AdminSnapshotSummary:
    snapshot = get_active_snapshot(session)
    if snapshot is None:
        return AdminSnapshotSummary(feature_version=active_feature_version(session))
    occupation_count = int(
        session.scalar(select(func.count()).select_from(Occupation).where(Occupation.snapshot_id == snapshot.id)) or 0
    )
    recommendable_count = int(
        session.scalar(
            select(func.count())
            .select_from(Occupation)
            .where(Occupation.snapshot_id == snapshot.id, Occupation.recommendable.is_(True))
        )
        or 0
    )
    return AdminSnapshotSummary(
        snapshot_id=snapshot.id,
        onet_release=snapshot.onet_release,
        onet_release_month=snapshot.onet_release_month,
        feature_version=snapshot.feature_version,
        occupation_count=occupation_count,
        recommendable_count=recommendable_count,
        knn_feature_count=_knn_feature_count(snapshot),
    )


def _questionnaire_summary(session: Session) -> AdminQuestionnaireSummary:
    version_name = active_questionnaire_version_name(session)
    questionnaire = session.scalar(select(QuestionnaireVersion).where(QuestionnaireVersion.version == version_name))
    if questionnaire is None:
        return AdminQuestionnaireSummary(version=version_name)
    question_count = int(
        session.scalar(
            select(func.count()).select_from(Question).where(Question.questionnaire_version_id == questionnaire.id)
        )
        or 0
    )
    option_count = int(
        session.scalar(
            select(func.count())
            .select_from(QuestionOption)
            .join(Question, QuestionOption.question_id == Question.id)
            .where(Question.questionnaire_version_id == questionnaire.id)
        )
        or 0
    )
    return AdminQuestionnaireSummary(
        version=questionnaire.version,
        status=questionnaire.status,
        feature_version=questionnaire.feature_version,
        question_count=question_count,
        option_count=option_count,
    )


def _config_summary(session: Session) -> AdminConfigSummary:
    config = _active_config(session)
    feature_version = active_feature_version(session)
    if config is None:
        return AdminConfigSummary(feature_version=feature_version)
    return AdminConfigSummary(
        version=config.version,
        k=config.k,
        metric=config.metric,
        feature_version=feature_version,
        block_weights=dict(config.block_weights_json or {}),
    )


def _system_status(session: Session, *, database: str = "connected") -> AdminSystemStatus:
    snapshot = get_active_snapshot(session)
    questionnaire = _questionnaire_summary(session)
    config = _active_config(session)
    return AdminSystemStatus(
        api="ok",
        database=database,
        active_onet_snapshot=snapshot is not None,
        active_questionnaire=questionnaire.version is not None and questionnaire.question_count > 0,
        active_recommendation_config=config is not None,
    )


def get_admin_dashboard(session: Session) -> AdminDashboardOut:
    students_total = int(session.scalar(select(func.count()).select_from(User).where(User.role == "student")) or 0)
    assessments_completed = int(
        session.scalar(select(func.count()).select_from(Assessment).where(Assessment.status == "completed")) or 0
    )
    recommendation_runs = int(session.scalar(select(func.count()).select_from(RecommendationRun)) or 0)
    ratings_total = int(session.scalar(select(func.count()).select_from(RecommendationRating)) or 0)
    ratings_average = session.scalar(select(func.avg(RecommendationRating.relevance_1_to_5)))
    return AdminDashboardOut(
        students_total=students_total,
        assessments_completed=assessments_completed,
        recommendation_runs=recommendation_runs,
        ratings_total=ratings_total,
        ratings_average=round(float(ratings_average), 2) if ratings_average is not None else None,
        active_onet=_snapshot_summary(session),
        active_questionnaire=_questionnaire_summary(session),
        active_config=_config_summary(session),
        system=_system_status(session),
        notes=list(DASHBOARD_NOTES),
    )


def get_admin_health(session: Session) -> AdminHealthOut:
    from sqlalchemy import text

    try:
        session.execute(text("SELECT 1"))
        database = "connected"
    except Exception:
        database = "unavailable"
    snapshot = get_active_snapshot(session)
    questionnaire = _questionnaire_summary(session)
    config = _active_config(session)
    status = _system_status(session, database=database)
    return AdminHealthOut(
        api="ok",
        database=status.database,
        active_onet_snapshot=status.active_onet_snapshot,
        active_questionnaire=status.active_questionnaire,
        active_recommendation_config=status.active_recommendation_config,
        feature_version=snapshot.feature_version if snapshot else active_feature_version(session),
        questionnaire_version=questionnaire.version,
        config_version=config.version if config else None,
    )


def list_admin_students(session: Session, *, query: str | None, page: int, page_size: int) -> AdminStudentListOut:
    page, page_size = _page_bounds(page, page_size)
    filters = [User.role == "student"]
    stmt = select(User).outerjoin(StudentProfile, StudentProfile.user_id == User.id)
    if query and query.strip():
        pattern = _like_pattern(query.strip())
        filters.append(
            or_(
                User.email.ilike(pattern, escape="\\"),
                StudentProfile.first_name.ilike(pattern, escape="\\"),
                StudentProfile.last_name.ilike(pattern, escape="\\"),
                StudentProfile.matric_number.ilike(pattern, escape="\\"),
            )
        )
    total = int(
        session.scalar(select(func.count()).select_from(User).outerjoin(StudentProfile).where(*filters)) or 0
    )
    users = session.scalars(
        stmt.where(*filters)
        .options(selectinload(User.profile))
        .order_by(User.created_at.desc(), User.email)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    ids = [user.id for user in users]
    latest_status: dict[uuid.UUID, tuple[str | None, object | None]] = {}
    run_counts: dict[uuid.UUID, int] = defaultdict(int)
    if ids:
        assessments = session.scalars(
            select(Assessment)
            .where(Assessment.student_user_id.in_(ids))
            .order_by(Assessment.started_at.desc())
        ).all()
        for assessment in assessments:
            if assessment.student_user_id not in latest_status:
                latest_status[assessment.student_user_id] = (assessment.status, assessment.completed_at)
        for student_id, count in session.execute(
            select(RecommendationRun.student_user_id, func.count())
            .where(RecommendationRun.student_user_id.in_(ids))
            .group_by(RecommendationRun.student_user_id)
        ):
            run_counts[student_id] = int(count)
    items = []
    for user in users:
        profile = user.profile
        status, completed_at = latest_status.get(user.id, (None, None))
        items.append(
            AdminStudentListItem(
                id=user.id,
                email=user.email,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login_at=user.last_login_at,
                first_name=profile.first_name if profile else None,
                last_name=profile.last_name if profile else None,
                matric_number=profile.matric_number if profile else None,
                faculty=profile.faculty if profile else None,
                department=profile.department if profile else None,
                level=profile.level if profile else None,
                latest_assessment_status=status,
                latest_assessment_completed_at=completed_at,
                recommendation_run_count=run_counts.get(user.id, 0),
            )
        )
    return AdminStudentListOut(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=_total_pages(total, page_size),
    )


def get_admin_student(session: Session, student_id: uuid.UUID, *, actor: User) -> AdminStudentDetailOut:
    student = session.get(User, student_id)
    if student is None or student.role != "student":
        raise NotFoundError("Student was not found", code="invalid_student")
    profile = student.profile
    assessments = session.scalars(
        select(Assessment)
        .options()
        .where(Assessment.student_user_id == student_id)
        .order_by(Assessment.started_at.desc())
    ).all()
    questionnaire_ids = {row.questionnaire_version_id for row in assessments}
    questionnaires = {}
    if questionnaire_ids:
        questionnaires = {
            row.id: row
            for row in session.scalars(select(QuestionnaireVersion).where(QuestionnaireVersion.id.in_(questionnaire_ids)))
        }
    history = list_student_runs(session, student_id=student_id, actor=actor)
    return AdminStudentDetailOut(
        id=student.id,
        email=student.email,
        is_active=student.is_active,
        created_at=student.created_at,
        last_login_at=student.last_login_at,
        profile=AdminStudentProfileOut(
            first_name=profile.first_name if profile else None,
            last_name=profile.last_name if profile else None,
            matric_number=profile.matric_number if profile else None,
            faculty=profile.faculty if profile else None,
            department=profile.department if profile else None,
            level=profile.level if profile else None,
            further_study=profile.further_study if profile else None,
            course_relatedness=profile.course_relatedness if profile else None,
        ),
        assessments=[
            AdminStudentAssessmentOut(
                id=row.id,
                status=row.status,
                questionnaire_version=(
                    questionnaires[row.questionnaire_version_id].version
                    if row.questionnaire_version_id in questionnaires
                    else None
                ),
                feature_version=row.feature_version,
                started_at=row.started_at,
                completed_at=row.completed_at,
            )
            for row in assessments
        ],
        recommendation_history=history.items,
    )


def list_admin_runs(session: Session, *, page: int, page_size: int) -> AdminRunListOut:
    page, page_size = _page_bounds(page, page_size)
    total = int(session.scalar(select(func.count()).select_from(RecommendationRun)) or 0)
    runs = session.scalars(
        select(RecommendationRun)
        .options(selectinload(RecommendationRun.items))
        .order_by(RecommendationRun.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    student_ids = {run.student_user_id for run in runs}
    assessment_ids = {run.assessment_id for run in runs}
    students = {
        row.id: row
        for row in session.scalars(select(User).options(selectinload(User.profile)).where(User.id.in_(student_ids))).all()
    } if student_ids else {}
    assessments = {
        row.id: row for row in session.scalars(select(Assessment).where(Assessment.id.in_(assessment_ids))).all()
    } if assessment_ids else {}
    snapshots = {
        row.id: row
        for row in session.scalars(
            select(OnetSnapshot).where(OnetSnapshot.id.in_({run.onet_snapshot_id for run in runs}))
        ).all()
    } if runs else {}
    questionnaires = {
        row.id: row
        for row in session.scalars(
            select(QuestionnaireVersion).where(
                QuestionnaireVersion.id.in_({run.questionnaire_version_id for run in runs})
            )
        ).all()
    } if runs else {}
    configs = {
        row.id: row
        for row in session.scalars(
            select(RecommendationConfig).where(RecommendationConfig.id.in_({run.config_id for run in runs}))
        ).all()
    } if runs else {}
    top_ids = []
    for run in runs:
        ranked = sorted(run.items, key=lambda item: item.rank)
        if ranked:
            top_ids.append(ranked[0].occupation_id)
    titles = {
        row.id: row for row in session.scalars(select(Occupation).where(Occupation.id.in_(set(top_ids)))).all()
    } if top_ids else {}
    items = []
    for run in runs:
        student = students.get(run.student_user_id)
        profile = student.profile if student else None
        name_parts = [part for part in ((profile.first_name if profile else None), (profile.last_name if profile else None)) if part]
        ranked = sorted(run.items, key=lambda item: item.rank)
        top = ranked[0] if ranked else None
        items.append(
            AdminRunListItem(
                run_id=run.id,
                student_id=run.student_user_id,
                student_email=student.email if student else "",
                student_name=" ".join(name_parts) or None,
                assessment_id=run.assessment_id,
                assessment_completed_at=assessments[run.assessment_id].completed_at if run.assessment_id in assessments else None,
                created_at=run.created_at,
                onet_release=snapshots[run.onet_snapshot_id].onet_release if run.onet_snapshot_id in snapshots else None,
                questionnaire_version=(
                    questionnaires[run.questionnaire_version_id].version if run.questionnaire_version_id in questionnaires else ""
                ),
                config_version=configs[run.config_id].version if run.config_id in configs else "",
                feature_version=run.feature_version,
                item_count=len(run.items),
                top_occupation_title=titles[top.occupation_id].title if top and top.occupation_id in titles else None,
                top_onetsoc_code=top.onetsoc_code if top else None,
            )
        )
    return AdminRunListOut(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=_total_pages(total, page_size),
    )


def get_admin_run(session: Session, run_id: uuid.UUID, *, actor: User) -> AdminRunDetailOut:
    run = serialize_run(session, run_id, actor=actor)
    stored = session.get(RecommendationRun, run_id)
    if stored is None:
        raise NotFoundError("Recommendation run was not found", code="invalid_recommendation_run")
    student = session.get(User, stored.student_user_id)
    if student is None:
        raise NotFoundError("Student was not found", code="invalid_student")
    profile = student.profile
    return AdminRunDetailOut(
        student=AdminStudentRef(
            id=student.id,
            email=student.email,
            first_name=profile.first_name if profile else None,
            last_name=profile.last_name if profile else None,
        ),
        run=run,
    )


def _rating_summary(session: Session) -> AdminRatingSummary:
    ratings_total = int(session.scalar(select(func.count()).select_from(RecommendationRating)) or 0)
    average = session.scalar(select(func.avg(RecommendationRating.relevance_1_to_5)))
    distribution = {value: 0 for value in range(1, 6)}
    for value, count in session.execute(
        select(RecommendationRating.relevance_1_to_5, func.count()).group_by(RecommendationRating.relevance_1_to_5)
    ):
        distribution[int(value)] = int(count)
    return AdminRatingSummary(
        ratings_total=ratings_total,
        average_relevance=round(float(average), 2) if average is not None else None,
        distribution=distribution,
        note=FEEDBACK_NOTE,
    )


def list_admin_ratings(session: Session, *, page: int, page_size: int) -> AdminRatingListOut:
    page, page_size = _page_bounds(page, page_size)
    total = int(session.scalar(select(func.count()).select_from(RecommendationRating)) or 0)
    ratings = session.scalars(
        select(RecommendationRating)
        .order_by(RecommendationRating.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    item_ids = {row.item_id for row in ratings}
    items = {
        row.id: row
        for row in session.scalars(
            select(RecommendationItem).options(selectinload(RecommendationItem.run)).where(RecommendationItem.id.in_(item_ids))
        ).all()
    } if item_ids else {}
    occupation_ids = {item.occupation_id for item in items.values()}
    occupations = {
        row.id: row for row in session.scalars(select(Occupation).where(Occupation.id.in_(occupation_ids))).all()
    } if occupation_ids else {}
    student_ids = {row.student_user_id for row in ratings}
    students = {
        row.id: row for row in session.scalars(select(User).where(User.id.in_(student_ids))).all()
    } if student_ids else {}
    payload = []
    for rating in ratings:
        item = items.get(rating.item_id)
        occupation = occupations.get(item.occupation_id) if item else None
        student = students.get(rating.student_user_id)
        payload.append(
            AdminRatingListItem(
                id=rating.id,
                relevance_1_to_5=rating.relevance_1_to_5,
                comment=rating.comment,
                created_at=rating.created_at,
                occupation_title=occupation.title if occupation else None,
                onetsoc_code=item.onetsoc_code if item else "",
                run_id=item.run_id if item else uuid.UUID(int=0),
                student_id=rating.student_user_id,
                student_email=student.email if student else "",
            )
        )
    return AdminRatingListOut(
        items=payload,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=_total_pages(total, page_size),
        summary=_rating_summary(session),
    )


def get_admin_onet_snapshot(session: Session) -> AdminOnetSnapshotOut:
    summary = _snapshot_summary(session)
    snapshot = get_active_snapshot(session)
    zones: list[AdminJobZoneInfo] = []
    if snapshot is not None:
        definitions = session.scalars(
            select(JobZoneDefinition)
            .where(JobZoneDefinition.snapshot_id == snapshot.id)
            .order_by(JobZoneDefinition.job_zone)
        ).all()
        counts = {
            zone: (total, recommendable)
            for zone, total, recommendable in session.execute(
                select(
                    Occupation.job_zone,
                    func.count(),
                    func.count().filter(Occupation.recommendable.is_(True)),
                )
                .where(Occupation.snapshot_id == snapshot.id)
                .group_by(Occupation.job_zone)
            )
        }
        for definition in definitions:
            total, recommendable = counts.get(definition.job_zone, (0, 0))
            zones.append(
                AdminJobZoneInfo(
                    job_zone=definition.job_zone,
                    name=definition.name,
                    education=definition.education,
                    occupation_count=int(total or 0),
                    recommendable_count=int(recommendable or 0),
                )
            )
    return AdminOnetSnapshotOut(
        snapshot_id=summary.snapshot_id,
        onet_release=summary.onet_release,
        onet_release_month=summary.onet_release_month,
        feature_version=summary.feature_version,
        occupation_count=summary.occupation_count,
        recommendable_count=summary.recommendable_count,
        knn_feature_count=summary.knn_feature_count,
        job_zones=zones,
    )


def get_admin_questionnaire(session: Session) -> AdminQuestionnaireOut:
    summary = _questionnaire_summary(session)
    version_name = summary.version or active_questionnaire_version_name(session)
    questionnaire = session.scalar(select(QuestionnaireVersion).where(QuestionnaireVersion.version == version_name))
    if questionnaire is None:
        return AdminQuestionnaireOut(version=version_name)
    questions = session.scalars(
        select(Question)
        .options(selectinload(Question.options))
        .where(Question.questionnaire_version_id == questionnaire.id)
        .order_by(Question.sort_order, Question.code)
    ).all()
    return AdminQuestionnaireOut(
        version=questionnaire.version,
        status=questionnaire.status,
        feature_version=questionnaire.feature_version,
        question_count=len(questions),
        option_count=sum(len(question.options) for question in questions),
        questions=[
            AdminQuestionInspectOut(
                code=question.code,
                section=question.section,
                prompt=question.prompt,
                response_type=question.response_type,
                block=question.block,
                onet_element_id=question.onet_element_id,
                sort_order=question.sort_order,
                is_required=question.is_required,
                option_count=len(question.options),
            )
            for question in questions
        ],
    )


def get_admin_recommendation_config(session: Session) -> AdminRecommendationConfigOut:
    summary = _config_summary(session)
    return AdminRecommendationConfigOut(
        version=summary.version,
        k=summary.k,
        metric=summary.metric,
        feature_version=summary.feature_version,
        block_weights=summary.block_weights,
    )


def list_knowledge_catalog(session: Session) -> FacultyKnowledgeCatalogOut:
    snapshot = get_active_snapshot(session)
    elements: list[KnowledgeElementOut] = []
    if snapshot is not None:
        rows = session.execute(
            select(OccupationFeature.element_id, OccupationFeature.element_name)
            .where(OccupationFeature.snapshot_id == snapshot.id, OccupationFeature.domain == "knowledge")
            .distinct()
            .order_by(OccupationFeature.element_id)
        ).all()
        elements = [KnowledgeElementOut(element_id=element_id, element_name=name) for element_id, name in rows]
    return FacultyKnowledgeCatalogOut(faculties=list(NSUK_FACULTIES), knowledge_elements=elements)


def _knowledge_name(session: Session, element_id: str) -> str:
    catalog = {item.element_id: item.element_name for item in list_knowledge_catalog(session).knowledge_elements}
    if element_id not in catalog:
        raise UnprocessableError("Knowledge element is not in the active O*NET snapshot", code="invalid_knowledge_element")
    return catalog[element_id]


def _validated_faculty(faculty: str) -> str:
    if faculty not in NSUK_FACULTIES:
        raise UnprocessableError("Faculty is not an official NSUK faculty", code="invalid_faculty")
    return faculty


def _record_audit(
    session: Session,
    *,
    actor: User,
    action: str,
    prior: FacultyKnowledgePrior | None,
    faculty: str,
    element_id: str,
    element_name: str | None,
    previous: FacultyKnowledgePrior | None = None,
) -> None:
    session.add(
        FacultyKnowledgePriorAudit(
            prior_id=prior.id if prior is not None else None,
            action=action,
            faculty=faculty,
            element_id=element_id,
            element_name=element_name,
            previous_faculty=previous.faculty if previous is not None else None,
            previous_element_id=previous.element_id if previous is not None else None,
            previous_element_name=previous.element_name if previous is not None else None,
            actor_user_id=actor.id,
        )
    )


def list_faculty_priors(session: Session) -> FacultyKnowledgePriorListOut:
    rows = session.scalars(select(FacultyKnowledgePrior).order_by(FacultyKnowledgePrior.faculty, FacultyKnowledgePrior.element_id)).all()
    return FacultyKnowledgePriorListOut(items=[FacultyKnowledgePriorOut.model_validate(row) for row in rows])


def create_faculty_prior(session: Session, payload: FacultyKnowledgePriorWrite, *, actor: User) -> FacultyKnowledgePriorOut:
    faculty = _validated_faculty(payload.faculty.strip())
    element_id = payload.element_id.strip()
    element_name = _knowledge_name(session, element_id)
    existing = session.scalar(
        select(FacultyKnowledgePrior).where(
            FacultyKnowledgePrior.faculty == faculty,
            FacultyKnowledgePrior.element_id == element_id,
        )
    )
    if existing is not None:
        raise ConflictError("That faculty already maps to this knowledge element", code="duplicate_faculty_prior")
    prior = FacultyKnowledgePrior(
        faculty=faculty,
        element_id=element_id,
        element_name=element_name,
        created_by=actor.id,
    )
    session.add(prior)
    try:
        session.flush()
    except IntegrityError as exc:
        raise ConflictError("That faculty already maps to this knowledge element", code="duplicate_faculty_prior") from exc
    _record_audit(
        session,
        actor=actor,
        action="create",
        prior=prior,
        faculty=faculty,
        element_id=element_id,
        element_name=element_name,
    )
    session.flush()
    return FacultyKnowledgePriorOut.model_validate(prior)


def update_faculty_prior(
    session: Session,
    prior_id: int,
    payload: FacultyKnowledgePriorWrite,
    *,
    actor: User,
) -> FacultyKnowledgePriorOut:
    prior = session.get(FacultyKnowledgePrior, prior_id)
    if prior is None:
        raise NotFoundError("Faculty knowledge mapping was not found", code="invalid_faculty_prior")
    previous = FacultyKnowledgePrior(
        faculty=prior.faculty,
        element_id=prior.element_id,
        element_name=prior.element_name,
    )
    faculty = _validated_faculty(payload.faculty.strip())
    element_id = payload.element_id.strip()
    element_name = _knowledge_name(session, element_id)
    prior.faculty = faculty
    prior.element_id = element_id
    prior.element_name = element_name
    try:
        session.flush()
    except IntegrityError as exc:
        raise ConflictError("That faculty already maps to this knowledge element", code="duplicate_faculty_prior") from exc
    _record_audit(
        session,
        actor=actor,
        action="update",
        prior=prior,
        faculty=faculty,
        element_id=element_id,
        element_name=element_name,
        previous=previous,
    )
    session.flush()
    return FacultyKnowledgePriorOut.model_validate(prior)


def delete_faculty_prior(session: Session, prior_id: int, *, actor: User) -> None:
    prior = session.get(FacultyKnowledgePrior, prior_id)
    if prior is None:
        raise NotFoundError("Faculty knowledge mapping was not found", code="invalid_faculty_prior")
    _record_audit(
        session,
        actor=actor,
        action="delete",
        prior=prior,
        faculty=prior.faculty,
        element_id=prior.element_id,
        element_name=prior.element_name,
        previous=prior,
    )
    session.delete(prior)
    session.flush()


def list_faculty_prior_audits(session: Session, *, page: int, page_size: int) -> FacultyKnowledgePriorAuditListOut:
    page, page_size = _page_bounds(page, page_size)
    total = int(session.scalar(select(func.count()).select_from(FacultyKnowledgePriorAudit)) or 0)
    rows = session.scalars(
        select(FacultyKnowledgePriorAudit)
        .order_by(FacultyKnowledgePriorAudit.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    actor_ids = {row.actor_user_id for row in rows if row.actor_user_id}
    actors = {
        row.id: row for row in session.scalars(select(User).where(User.id.in_(actor_ids))).all()
    } if actor_ids else {}
    return FacultyKnowledgePriorAuditListOut(
        items=[
            FacultyKnowledgePriorAuditOut(
                id=row.id,
                prior_id=row.prior_id,
                action=row.action,
                faculty=row.faculty,
                element_id=row.element_id,
                element_name=row.element_name,
                previous_faculty=row.previous_faculty,
                previous_element_id=row.previous_element_id,
                previous_element_name=row.previous_element_name,
                actor_user_id=row.actor_user_id,
                actor_email=actors[row.actor_user_id].email if row.actor_user_id in actors else None,
                created_at=row.created_at,
            )
            for row in rows
        ],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=_total_pages(total, page_size),
    )

