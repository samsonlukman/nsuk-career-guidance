"""Minimal audit log for faculty knowledge prior changes.

Revision ID: 0003_prior_audits
Revises: 0002_seed_questionnaire_v1
Create Date: 2026-08-24
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_prior_audits"
down_revision: Union[str, Sequence[str], None] = "0002_seed_questionnaire_v1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "faculty_knowledge_prior_audits",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column(
            "prior_id",
            sa.Integer(),
            sa.ForeignKey("faculty_knowledge_priors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("faculty", sa.Text(), nullable=False),
        sa.Column("element_id", sa.String(32), nullable=False),
        sa.Column("element_name", sa.Text(), nullable=True),
        sa.Column("previous_faculty", sa.Text(), nullable=True),
        sa.Column("previous_element_id", sa.String(32), nullable=True),
        sa.Column("previous_element_name", sa.Text(), nullable=True),
        sa.Column(
            "actor_user_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("action IN ('create', 'update', 'delete')", name="ck_faculty_knowledge_prior_audits_action"),
    )
    op.create_index("ix_faculty_knowledge_prior_audits_prior_id", "faculty_knowledge_prior_audits", ["prior_id"])
    op.create_index(
        "ix_faculty_knowledge_prior_audits_actor_user_id",
        "faculty_knowledge_prior_audits",
        ["actor_user_id"],
    )
    op.create_index("ix_faculty_knowledge_prior_audits_created_at", "faculty_knowledge_prior_audits", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_faculty_knowledge_prior_audits_created_at", table_name="faculty_knowledge_prior_audits")
    op.drop_index("ix_faculty_knowledge_prior_audits_actor_user_id", table_name="faculty_knowledge_prior_audits")
    op.drop_index("ix_faculty_knowledge_prior_audits_prior_id", table_name="faculty_knowledge_prior_audits")
    op.drop_table("faculty_knowledge_prior_audits")
