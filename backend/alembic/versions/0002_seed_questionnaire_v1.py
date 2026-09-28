"""Seed questionnaire_v1.

Revision ID: 0002_seed_questionnaire_v1
Revises: 0001_initial_schema
Create Date: 2026-08-21
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy.orm import Session

revision: str = "0002_seed_questionnaire_v1"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from app.services.questionnaire_seed import seed_questionnaire_v1

    session = Session(bind=op.get_bind())
    seed_questionnaire_v1(session)
    session.flush()


def downgrade() -> None:
    from app.services.questionnaire_seed import QUESTIONNAIRE_VERSION

    op.execute(
        f"""
        DELETE FROM question_options
        WHERE question_id IN (
            SELECT q.id FROM questions q
            JOIN questionnaire_versions v ON v.id = q.questionnaire_version_id
            WHERE v.version = '{QUESTIONNAIRE_VERSION}'
        )
        """
    )
    op.execute(
        f"""
        DELETE FROM questions
        WHERE questionnaire_version_id IN (
            SELECT id FROM questionnaire_versions WHERE version = '{QUESTIONNAIRE_VERSION}'
        )
        """
    )
    op.execute(f"DELETE FROM questionnaire_versions WHERE version = '{QUESTIONNAIRE_VERSION}'")
    op.execute(
        "UPDATE system_config SET value_json = '{\"value\": null}'::jsonb "
        "WHERE key = 'active_questionnaire_version'"
    )
