from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list | dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    status: str
    database: str
    feature_version: str | None = None


class OccupationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    onetsoc_code: str
    title: str
    job_zone: int | None = None
    knn_complete: bool
    recommendable: bool
    has_education: bool
    has_work_context: bool


class OccupationEducationItem(BaseModel):
    category: str
    description: str
    percent: float


class OccupationActivityItem(BaseModel):
    element_id: str
    name: str
    importance: float | None = None


class OccupationFeatureItem(BaseModel):
    element_id: str
    element_name: str
    value: float | None = None


class OccupationDetail(OccupationSummary):
    description: str
    feature_version: str
    onet_release: str
    job_zone_name: str | None = None
    job_zone_education: str | None = None
    job_zone_experience: str | None = None
    feature_count: int
    education: list[OccupationEducationItem] = Field(default_factory=list)
    work_activities: list[OccupationActivityItem] = Field(default_factory=list)
    interests: list[OccupationFeatureItem] = Field(default_factory=list)


class OccupationListResponse(BaseModel):
    items: list[OccupationSummary]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class RecommendationConfigPublic(BaseModel):
    version: str
    k: int
    metric: str
    block_weights: dict[str, float]


class RecommendationMetadataResponse(BaseModel):
    feature_version: str
    onet_release: str | None = None
    onet_release_month: str | None = None
    snapshot_id: str | None = None
    config: RecommendationConfigPublic
    k: int
    metric: str
    block_weights: dict[str, float]
    allowed_k: list[int]
    default_job_zones: list[int]
