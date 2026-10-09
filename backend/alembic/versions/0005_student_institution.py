"""Collect student institution alongside matriculation number.

Revision ID: 0005_student_institution
Revises: 0004_experience_evaluations
Create Date: 2026-10-09
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_student_institution"
down_revision: Union[str, Sequence[str], None] = "0004_experience_evaluations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("student_profiles", sa.Column("institution", sa.String(200), nullable=True))
    op.create_index("ix_student_profiles_institution", "student_profiles", ["institution"])
    op.create_index("ix_student_profiles_matric_number", "student_profiles", ["matric_number"])
    op.drop_constraint("uq_student_profiles_matric", "student_profiles", type_="unique")
    op.create_index(
        "uq_student_profiles_institution_matric",
        "student_profiles",
        ["institution", "matric_number"],
        unique=True,
        postgresql_where=sa.text("institution IS NOT NULL AND matric_number IS NOT NULL"),
    )
    op.create_index(
        "uq_student_profiles_matric_no_institution",
        "student_profiles",
        ["matric_number"],
        unique=True,
        postgresql_where=sa.text("matric_number IS NOT NULL AND institution IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_student_profiles_matric_no_institution", table_name="student_profiles")
    op.drop_index("uq_student_profiles_institution_matric", table_name="student_profiles")
    op.create_unique_constraint("uq_student_profiles_matric", "student_profiles", ["matric_number"])
    op.drop_index("ix_student_profiles_matric_number", table_name="student_profiles")
    op.drop_index("ix_student_profiles_institution", table_name="student_profiles")
    op.drop_column("student_profiles", "institution")
