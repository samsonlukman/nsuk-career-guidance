from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.recommendation import RecommendationHistoryItemOut, RecommendationRunOut


class PageMeta(BaseModel):
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class AdminSnapshotSummary(BaseModel):
    snapshot_id: uuid.UUID | None = None
    onet_release: str | None = None
    onet_release_month: str | None = None
    feature_version: str | None = None
    occupation_count: int = 0
    recommendable_count: int = 0
    knn_feature_count: int = 0


class AdminQuestionnaireSummary(BaseModel):
    version: str | None = None
    status: str | None = None
    feature_version: str | None = None
    question_count: int = 0
    option_count: int = 0


class AdminConfigSummary(BaseModel):
    version: str | None = None
    k: int | None = None
    metric: str | None = None
    feature_version: str | None = None
    block_weights: dict[str, float] = Field(default_factory=dict)


class AdminSystemStatus(BaseModel):
    api: str
    database: str
    active_onet_snapshot: bool
    active_questionnaire: bool
    active_recommendation_config: bool


class AdminDashboardOut(BaseModel):
    students_total: int
    assessments_completed: int
    recommendation_runs: int
    ratings_total: int
    ratings_average: float | None = None
    active_onet: AdminSnapshotSummary
    active_questionnaire: AdminQuestionnaireSummary
    active_config: AdminConfigSummary
    system: AdminSystemStatus
    notes: list[str] = Field(default_factory=list)


class AdminStudentListItem(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None
    first_name: str | None = None
    last_name: str | None = None
    matric_number: str | None = None
    faculty: str | None = None
    department: str | None = None
    level: str | None = None
    latest_assessment_status: str | None = None
    latest_assessment_completed_at: datetime | None = None
    recommendation_run_count: int = 0


class AdminStudentListOut(PageMeta):
    items: list[AdminStudentListItem]


class AdminStudentProfileOut(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    matric_number: str | None = None
    faculty: str | None = None
    department: str | None = None
    level: str | None = None
    further_study: str | None = None
    course_relatedness: str | None = None


class AdminStudentAssessmentOut(BaseModel):
    id: uuid.UUID
    status: str
    questionnaire_version: str | None = None
    feature_version: str
    started_at: datetime
    completed_at: datetime | None = None


class AdminStudentDetailOut(BaseModel):
    id: uuid.UUID
    email: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None
    profile: AdminStudentProfileOut
    assessments: list[AdminStudentAssessmentOut]
    recommendation_history: list[RecommendationHistoryItemOut]


class AdminRunListItem(BaseModel):
    run_id: uuid.UUID
    student_id: uuid.UUID
    student_email: str
    student_name: str | None = None
    assessment_id: uuid.UUID
    assessment_completed_at: datetime | None = None
    created_at: datetime
    onet_release: str | None = None
    questionnaire_version: str
    config_version: str
    feature_version: str
    item_count: int
    top_occupation_title: str | None = None
    top_onetsoc_code: str | None = None


class AdminRunListOut(PageMeta):
    items: list[AdminRunListItem]


class AdminStudentRef(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str | None = None
    last_name: str | None = None


class AdminRunDetailOut(BaseModel):
    student: AdminStudentRef
    run: RecommendationRunOut


class AdminRatingListItem(BaseModel):
    id: uuid.UUID
    relevance_1_to_5: int
    comment: str | None = None
    created_at: datetime
    occupation_title: str | None = None
    onetsoc_code: str
    run_id: uuid.UUID
    student_id: uuid.UUID
    student_email: str


class AdminRatingSummary(BaseModel):
    ratings_total: int
    average_relevance: float | None = None
    distribution: dict[int, int]
    note: str = "These values are user relevance feedback for later evaluation. They are not a measure of recommendation accuracy."


class AdminRatingListOut(PageMeta):
    items: list[AdminRatingListItem]
    summary: AdminRatingSummary


class AdminJobZoneInfo(BaseModel):
    job_zone: int
    name: str
    education: str | None = None
    occupation_count: int = 0
    recommendable_count: int = 0


class AdminOnetSnapshotOut(BaseModel):
    snapshot_id: uuid.UUID | None = None
    onet_release: str | None = None
    onet_release_month: str | None = None
    feature_version: str | None = None
    occupation_count: int = 0
    recommendable_count: int = 0
    knn_feature_count: int = 0
    job_zones: list[AdminJobZoneInfo] = Field(default_factory=list)
    note: str = "O*NET remains the authoritative occupational source. This view is read-only."


class AdminQuestionInspectOut(BaseModel):
    code: str
    section: str
    prompt: str
    response_type: str
    block: str | None = None
    onet_element_id: str | None = None
    sort_order: int
    is_required: bool
    option_count: int


class AdminQuestionnaireOut(BaseModel):
    version: str | None = None
    status: str | None = None
    feature_version: str | None = None
    question_count: int = 0
    option_count: int = 0
    questions: list[AdminQuestionInspectOut] = Field(default_factory=list)
    note: str = "Questionnaire inspection only. Editing is not available from this view."


class AdminRecommendationConfigOut(BaseModel):
    version: str | None = None
    k: int | None = None
    metric: str | None = None
    feature_version: str | None = None
    block_weights: dict[str, float] = Field(default_factory=dict)
    note: str = "Read-only. Changing k, metric, or weights from this interface is not allowed."


class AdminHealthOut(BaseModel):
    api: str
    database: str
    active_onet_snapshot: bool
    active_questionnaire: bool
    active_recommendation_config: bool
    feature_version: str | None = None
    questionnaire_version: str | None = None
    config_version: str | None = None


class KnowledgeElementOut(BaseModel):
    element_id: str
    element_name: str


class FacultyKnowledgeCatalogOut(BaseModel):
    faculties: list[str]
    knowledge_elements: list[KnowledgeElementOut]
    note: str = (
        "Faculty names are official NSUK faculties. Knowledge element IDs come from the "
        "active O*NET snapshot. Department names are not configured here."
    )


class FacultyKnowledgePriorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    faculty: str
    element_id: str
    element_name: str | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class FacultyKnowledgePriorListOut(BaseModel):
    items: list[FacultyKnowledgePriorOut]


class FacultyKnowledgePriorWrite(BaseModel):
    faculty: str = Field(min_length=1, max_length=200)
    element_id: str = Field(min_length=1, max_length=32)


class FacultyKnowledgePriorAuditOut(BaseModel):
    id: uuid.UUID
    prior_id: int | None = None
    action: str
    faculty: str
    element_id: str
    element_name: str | None = None
    previous_faculty: str | None = None
    previous_element_id: str | None = None
    previous_element_name: str | None = None
    actor_user_id: uuid.UUID | None = None
    actor_email: str | None = None
    created_at: datetime


class FacultyKnowledgePriorAuditListOut(PageMeta):
    items: list[FacultyKnowledgePriorAuditOut]
