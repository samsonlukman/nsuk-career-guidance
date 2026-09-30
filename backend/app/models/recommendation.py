"""Recommendation configuration, runs, items, explanations, firings, and ratings."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RecommendationConfig(Base):
    __tablename__ = "recommendation_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    k: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    metric: Mapped[str] = mapped_column(String(120), nullable=False)
    block_weights_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    rule_params_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (CheckConstraint("k IN (5, 10, 15)", name="ck_recommendation_configs_k"),)


class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    student_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    questionnaire_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questionnaire_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    onet_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("onet_snapshots.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendation_configs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    feature_version: Mapped[str] = mapped_column(String(64), nullable=False)
    k: Mapped[int] = mapped_column(Integer, nullable=False)
    metric: Mapped[str] = mapped_column(String(120), nullable=False)
    eligible_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    elapsed_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weights_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    items: Mapped[list[RecommendationItem]] = relationship(back_populates="run")
    firings: Mapped[list[RuleFiring]] = relationship(back_populates="run")
    experience_evaluations: Mapped[list[ExperienceEvaluation]] = relationship(back_populates="run")


class RecommendationItem(Base):
    __tablename__ = "recommendation_items"
    __table_args__ = (
        UniqueConstraint("run_id", "rank", name="uq_recommendation_items_rank"),
        UniqueConstraint("run_id", "occupation_id", name="uq_recommendation_items_occupation"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    occupation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("occupations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    onetsoc_code: Mapped[str] = mapped_column(String(16), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    distance: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False)
    raw_similarity: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False)
    recommendation_score: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False)
    explanation_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    job_zone_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    run: Mapped[RecommendationRun] = relationship(back_populates="items")
    contributions: Mapped[list[RecommendationContribution]] = relationship(back_populates="item")
    firings: Mapped[list[RuleFiring]] = relationship(back_populates="item")
    ratings: Mapped[list[RecommendationRating]] = relationship(back_populates="item")


class RecommendationContribution(Base):
    __tablename__ = "recommendation_contributions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    block: Mapped[str] = mapped_column(String(40), nullable=False)
    element_id: Mapped[str] = mapped_column(String(32), nullable=False)
    element_name: Mapped[str] = mapped_column(Text, nullable=False)
    student_raw: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)
    student_normalized: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)
    occupation_raw: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)
    occupation_normalized: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")

    item: Mapped[RecommendationItem] = relationship(back_populates="contributions")


class RuleFiring(Base):
    __tablename__ = "rule_firings"
    __table_args__ = (
        CheckConstraint(
            "action IN ('exclude', 'penalise', 'flag', 'drop', 'floor')",
            name="ck_rule_firings_action",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_items.id", ondelete="CASCADE"), nullable=True, index=True
    )
    occupation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("occupations.id", ondelete="SET NULL"), nullable=True
    )
    onetsoc_code: Mapped[str] = mapped_column(String(16), nullable=False)
    rule_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    penalty: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    element_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(40), nullable=True)

    run: Mapped[RecommendationRun] = relationship(back_populates="firings")
    item: Mapped[RecommendationItem | None] = relationship(back_populates="firings")


class RecommendationRating(Base):
    __tablename__ = "recommendation_ratings"
    __table_args__ = (
        UniqueConstraint("item_id", "student_user_id", name="uq_recommendation_ratings_item_student"),
        CheckConstraint("relevance_1_to_5 BETWEEN 1 AND 5", name="ck_recommendation_ratings_scale"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    relevance_1_to_5: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    item: Mapped[RecommendationItem] = relationship(back_populates="ratings")


EXPERIENCE_EVALUATION_SCALE_FIELDS = (
    "questions_easy_to_understand",
    "assessment_easy_to_complete",
    "system_easy_to_navigate",
    "recommendations_easy_to_understand",
    "explanations_helped",
    "reflected_interests",
    "reflected_skills",
    "helped_explore_options",
    "would_use_again",
    "would_discuss_with_counsellor",
)


class ExperienceEvaluation(Base):
    """Student experience, usability, usefulness, and perceived relevance.

    This is not an accuracy measure.
    """

    __tablename__ = "experience_evaluations"
    __table_args__ = (
        UniqueConstraint("run_id", "student_user_id", name="uq_experience_evaluations_run_student"),
        CheckConstraint(
            "questions_easy_to_understand BETWEEN 1 AND 5",
            name="ck_experience_eval_questions_easy",
        ),
        CheckConstraint(
            "assessment_easy_to_complete BETWEEN 1 AND 5",
            name="ck_experience_eval_assessment_easy",
        ),
        CheckConstraint("system_easy_to_navigate BETWEEN 1 AND 5", name="ck_experience_eval_navigate"),
        CheckConstraint(
            "recommendations_easy_to_understand BETWEEN 1 AND 5",
            name="ck_experience_eval_recs_easy",
        ),
        CheckConstraint("explanations_helped BETWEEN 1 AND 5", name="ck_experience_eval_explanations"),
        CheckConstraint("reflected_interests BETWEEN 1 AND 5", name="ck_experience_eval_interests"),
        CheckConstraint("reflected_skills BETWEEN 1 AND 5", name="ck_experience_eval_skills"),
        CheckConstraint("helped_explore_options BETWEEN 1 AND 5", name="ck_experience_eval_explore"),
        CheckConstraint("would_use_again BETWEEN 1 AND 5", name="ck_experience_eval_use_again"),
        CheckConstraint(
            "would_discuss_with_counsellor BETWEEN 1 AND 5",
            name="ck_experience_eval_counsellor",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    questions_easy_to_understand: Mapped[int] = mapped_column(Integer, nullable=False)
    assessment_easy_to_complete: Mapped[int] = mapped_column(Integer, nullable=False)
    system_easy_to_navigate: Mapped[int] = mapped_column(Integer, nullable=False)
    recommendations_easy_to_understand: Mapped[int] = mapped_column(Integer, nullable=False)
    explanations_helped: Mapped[int] = mapped_column(Integer, nullable=False)
    reflected_interests: Mapped[int] = mapped_column(Integer, nullable=False)
    reflected_skills: Mapped[int] = mapped_column(Integer, nullable=False)
    helped_explore_options: Mapped[int] = mapped_column(Integer, nullable=False)
    would_use_again: Mapped[int] = mapped_column(Integer, nullable=False)
    would_discuss_with_counsellor: Mapped[int] = mapped_column(Integer, nullable=False)
    liked_most_and_improvement: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    run: Mapped[RecommendationRun] = relationship(back_populates="experience_evaluations")
