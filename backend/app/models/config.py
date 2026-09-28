"""Admin-editable priors, named rule definitions, and system configuration."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FacultyKnowledgePrior(Base):
    """Editable faculty → O*NET knowledge element mapping. Starts empty."""

    __tablename__ = "faculty_knowledge_priors"
    __table_args__ = (UniqueConstraint("faculty", "element_id", name="uq_faculty_knowledge_priors"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    faculty: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    element_id: Mapped[str] = mapped_column(String(32), nullable=False)
    element_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class FacultyKnowledgePriorAudit(Base):
    """Who changed a faculty→knowledge mapping, what changed, and when."""

    __tablename__ = "faculty_knowledge_prior_audits"
    __table_args__ = (
        CheckConstraint("action IN ('create', 'update', 'delete')", name="ck_faculty_knowledge_prior_audits_action"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prior_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("faculty_knowledge_priors.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    faculty: Mapped[str] = mapped_column(Text, nullable=False)
    element_id: Mapped[str] = mapped_column(String(32), nullable=False)
    element_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_faculty: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_element_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    previous_element_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class RuleDefinition(Base):
    __tablename__ = "rules"

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    params_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    explanation_template: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SystemConfig(Base):
    __tablename__ = "system_config"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
