"""Versioned processed O*NET occupational data. Raw TSV files are not stored here."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
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


class OnetSnapshot(Base):
    __tablename__ = "onet_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_version: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    onet_release: Mapped[str] = mapped_column(String(16), nullable=False)
    onet_release_month: Mapped[str | None] = mapped_column(String(32), nullable=True)
    scales_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    block_spec_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    source_files_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    occupations: Mapped[list[Occupation]] = relationship(back_populates="snapshot")


class Occupation(Base):
    __tablename__ = "occupations"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "onetsoc_code", name="uq_occupations_snapshot_soc"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("onet_snapshots.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    onetsoc_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    job_zone: Mapped[int | None] = mapped_column(Integer, nullable=True)
    knn_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recommendable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    has_education: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_work_context: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    snapshot: Mapped[OnetSnapshot] = relationship(back_populates="occupations")
    features: Mapped[list[OccupationFeature]] = relationship(back_populates="occupation")


class OccupationFeature(Base):
    __tablename__ = "occupation_features"
    __table_args__ = (
        UniqueConstraint(
            "occupation_id",
            "domain",
            "element_id",
            "category",
            name="uq_occupation_features_element",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("onet_snapshots.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    occupation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("occupations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    domain: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    element_id: Mapped[str] = mapped_column(String(32), nullable=False)
    element_name: Mapped[str] = mapped_column(Text, nullable=False)
    scale_id: Mapped[str] = mapped_column(String(16), nullable=False)
    category: Mapped[str] = mapped_column(String(16), nullable=False, default="")
    raw_value: Mapped[float] = mapped_column(Numeric(12, 6), nullable=False)
    used_value: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)
    normalized_value: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)
    not_relevant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recommend_suppress: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    include_in_knn: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    occupation: Mapped[Occupation] = relationship(back_populates="features")


class JobZoneDefinition(Base):
    __tablename__ = "job_zone_definitions"
    __table_args__ = (UniqueConstraint("snapshot_id", "job_zone", name="uq_job_zone_definitions"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("onet_snapshots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_zone: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    education: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_training: Mapped[str | None] = mapped_column(Text, nullable=True)
    examples: Mapped[str | None] = mapped_column(Text, nullable=True)
    svp_range: Mapped[str | None] = mapped_column(String(64), nullable=True)


class EducationCategory(Base):
    __tablename__ = "education_categories"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "element_id", "category", name="uq_education_categories"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("onet_snapshots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    element_id: Mapped[str] = mapped_column(String(32), nullable=False)
    scale_id: Mapped[str] = mapped_column(String(16), nullable=False, default="RL")
    category: Mapped[str] = mapped_column(String(16), nullable=False)
    category_description: Mapped[str] = mapped_column(Text, nullable=False)
