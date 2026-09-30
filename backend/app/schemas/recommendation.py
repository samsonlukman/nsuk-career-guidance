from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuestionOptionOut(BaseModel):
    value: str
    label: str
    onet_element_id: str | None = None
    sort_order: int = 0


class QuestionOut(BaseModel):
    code: str
    section: str
    prompt: str
    response_type: str
    block: str | None = None
    onet_element_id: str | None = None
    onet_scale_id: str | None = None
    sort_order: int
    is_required: bool
    min_value: float | None = None
    max_value: float | None = None
    min_selections: int | None = None
    max_selections: int | None = None
    options: list[QuestionOptionOut] = Field(default_factory=list)


class QuestionnaireOut(BaseModel):
    version: str
    feature_version: str
    status: str
    questions: list[QuestionOut]


class SparseSelectionIn(BaseModel):
    element_id: str
    value: int | str


class AssessmentResponseIn(BaseModel):
    code: str
    value: int | str | None = None
    selections: list[SparseSelectionIn] | None = None


class AssessmentCreateRequest(BaseModel):
    questionnaire_version: str
    responses: list[AssessmentResponseIn]


class FeatureContributionOut(BaseModel):
    block: str
    element_id: str
    element_name: str
    student_raw: float | None = None
    student_normalized: float | None = None
    occupation_raw: float | None = None
    occupation_normalized: float | None = None
    note: str = ""


class RuleFiringOut(BaseModel):
    rule_code: str
    action: str
    reason: str
    penalty: float | None = None
    element_id: str | None = None
    domain: str | None = None


class RecommendationItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rank: int
    onetsoc_code: str
    title: str
    job_zone: int | None = None
    distance: float
    raw_similarity: float
    recommendation_score: float
    explanation: str
    job_zone_note: str | None = None
    work_activities: list[str] = Field(default_factory=list)
    contributing_features: list[FeatureContributionOut] = Field(default_factory=list)
    rule_flags: list[RuleFiringOut] = Field(default_factory=list)
    penalties: list[RuleFiringOut] = Field(default_factory=list)


class RecommendationRunOut(BaseModel):
    id: uuid.UUID
    assessment_id: uuid.UUID
    created_at: datetime
    k: int
    metric: str
    eligible_count: int
    elapsed_ms: int | None = None
    feature_version: str
    onet_release: str | None = None
    onet_snapshot_id: uuid.UUID
    questionnaire_version: str
    config_version: str
    block_weights: dict[str, float]
    notes: list[str] = Field(default_factory=list)
    items: list[RecommendationItemOut]


class RecommendationHistoryItemOut(BaseModel):
    run_id: uuid.UUID
    created_at: datetime
    k: int
    feature_version: str
    questionnaire_version: str
    config_version: str
    onet_release: str | None = None
    eligible_count: int
    item_count: int
    top_occupation_title: str | None = None
    top_onetsoc_code: str | None = None


class RecommendationHistoryOut(BaseModel):
    student_id: uuid.UUID
    items: list[RecommendationHistoryItemOut]


class RatingCreateRequest(BaseModel):
    relevance_1_to_5: int = Field(..., ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class RatingOut(BaseModel):
    id: uuid.UUID
    item_id: uuid.UUID
    relevance_1_to_5: int
    comment: str | None = None
    created_at: datetime
    note: str = "This is user relevance feedback, not a measure of recommendation accuracy."


class ExperienceEvaluationCreateRequest(BaseModel):
    questions_easy_to_understand: int = Field(..., ge=1, le=5)
    assessment_easy_to_complete: int = Field(..., ge=1, le=5)
    system_easy_to_navigate: int = Field(..., ge=1, le=5)
    recommendations_easy_to_understand: int = Field(..., ge=1, le=5)
    explanations_helped: int = Field(..., ge=1, le=5)
    reflected_interests: int = Field(..., ge=1, le=5)
    reflected_skills: int = Field(..., ge=1, le=5)
    helped_explore_options: int = Field(..., ge=1, le=5)
    would_use_again: int = Field(..., ge=1, le=5)
    would_discuss_with_counsellor: int = Field(..., ge=1, le=5)
    liked_most_and_improvement: str | None = Field(default=None, max_length=2000)


class ExperienceEvaluationOut(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    student_user_id: uuid.UUID
    questions_easy_to_understand: int
    assessment_easy_to_complete: int
    system_easy_to_navigate: int
    recommendations_easy_to_understand: int
    explanations_helped: int
    reflected_interests: int
    reflected_skills: int
    helped_explore_options: int
    would_use_again: int
    would_discuss_with_counsellor: int
    liked_most_and_improvement: str | None = None
    created_at: datetime
    note: str = (
        "This form records your experience, usability, usefulness, and perceived relevance. "
        "It is not an accuracy test."
    )
