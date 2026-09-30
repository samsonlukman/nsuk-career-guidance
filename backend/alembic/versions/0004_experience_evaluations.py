"""Student post-recommendation experience evaluation.

Revision ID: 0004_experience_evaluations
Revises: 0003_prior_audits
Create Date: 2026-09-30
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_experience_evaluations"
down_revision: Union[str, Sequence[str], None] = "0003_prior_audits"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "experience_evaluations",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column(
            "run_id",
            UUID,
            sa.ForeignKey("recommendation_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_user_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("questions_easy_to_understand", sa.Integer(), nullable=False),
        sa.Column("assessment_easy_to_complete", sa.Integer(), nullable=False),
        sa.Column("system_easy_to_navigate", sa.Integer(), nullable=False),
        sa.Column("recommendations_easy_to_understand", sa.Integer(), nullable=False),
        sa.Column("explanations_helped", sa.Integer(), nullable=False),
        sa.Column("reflected_interests", sa.Integer(), nullable=False),
        sa.Column("reflected_skills", sa.Integer(), nullable=False),
        sa.Column("helped_explore_options", sa.Integer(), nullable=False),
        sa.Column("would_use_again", sa.Integer(), nullable=False),
        sa.Column("would_discuss_with_counsellor", sa.Integer(), nullable=False),
        sa.Column("liked_most_and_improvement", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("run_id", "student_user_id", name="uq_experience_evaluations_run_student"),
        sa.CheckConstraint(
            "questions_easy_to_understand BETWEEN 1 AND 5",
            name="ck_experience_eval_questions_easy",
        ),
        sa.CheckConstraint(
            "assessment_easy_to_complete BETWEEN 1 AND 5",
            name="ck_experience_eval_assessment_easy",
        ),
        sa.CheckConstraint("system_easy_to_navigate BETWEEN 1 AND 5", name="ck_experience_eval_navigate"),
        sa.CheckConstraint(
            "recommendations_easy_to_understand BETWEEN 1 AND 5",
            name="ck_experience_eval_recs_easy",
        ),
        sa.CheckConstraint("explanations_helped BETWEEN 1 AND 5", name="ck_experience_eval_explanations"),
        sa.CheckConstraint("reflected_interests BETWEEN 1 AND 5", name="ck_experience_eval_interests"),
        sa.CheckConstraint("reflected_skills BETWEEN 1 AND 5", name="ck_experience_eval_skills"),
        sa.CheckConstraint("helped_explore_options BETWEEN 1 AND 5", name="ck_experience_eval_explore"),
        sa.CheckConstraint("would_use_again BETWEEN 1 AND 5", name="ck_experience_eval_use_again"),
        sa.CheckConstraint(
            "would_discuss_with_counsellor BETWEEN 1 AND 5",
            name="ck_experience_eval_counsellor",
        ),
    )
    op.create_index("ix_experience_evaluations_run_id", "experience_evaluations", ["run_id"])
    op.create_index("ix_experience_evaluations_student_user_id", "experience_evaluations", ["student_user_id"])


def downgrade() -> None:
    op.drop_index("ix_experience_evaluations_student_user_id", table_name="experience_evaluations")
    op.drop_index("ix_experience_evaluations_run_id", table_name="experience_evaluations")
    op.drop_table("experience_evaluations")
