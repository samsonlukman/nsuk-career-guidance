from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.schemas.recommendation import RecommendationHistoryItemOut


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    matric_number: str | None = Field(default=None, max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ProfileOut(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    matric_number: str | None = None
    faculty: str | None = None
    department: str | None = None
    level: str | None = None
    further_study: str | None = None
    course_relatedness: str | None = None


class ProfileUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    matric_number: str | None = Field(default=None, max_length=64)
    faculty: str | None = None
    department: str | None = Field(default=None, max_length=200)
    level: str | None = None
    further_study: str | None = None
    course_relatedness: str | None = None


class CurrentUserOut(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    is_active: bool
    profile: ProfileOut


class AssessmentSummaryOut(BaseModel):
    id: uuid.UUID
    status: str
    questionnaire_version: str | None = None
    feature_version: str
    started_at: datetime
    completed_at: datetime | None = None


class DashboardOut(BaseModel):
    user: CurrentUserOut
    has_completed_assessment: bool
    latest_assessment: AssessmentSummaryOut | None = None
    latest_recommendation: RecommendationHistoryItemOut | None = None
    recommendation_history: list[RecommendationHistoryItemOut]


class ProfileOptionsOut(BaseModel):
    faculties: list[str]
    levels: list[str]
    further_study: list[str]
    course_relatedness: list[str]
