"""Initial PostgreSQL schema for versioned assessments and recommendations.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-08-20
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="student"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("role IN ('student', 'admin')", name="ck_users_role"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "student_profiles",
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("matric_number", sa.String(64), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("faculty", sa.Text(), nullable=True),
        sa.Column("department", sa.Text(), nullable=True),
        sa.Column("level", sa.String(10), nullable=True),
        sa.Column("further_study", sa.String(16), nullable=True),
        sa.Column("course_relatedness", sa.String(16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("matric_number", name="uq_student_profiles_matric"),
    )

    op.create_table(
        "questionnaire_versions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("feature_version", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('draft', 'published', 'retired')", name="ck_questionnaire_status"),
        sa.UniqueConstraint("version", name="uq_questionnaire_versions_version"),
    )

    op.create_table(
        "questions",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column(
            "questionnaire_version_id",
            UUID,
            sa.ForeignKey("questionnaire_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("section", sa.String(80), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("response_type", sa.String(32), nullable=False),
        sa.Column("onet_element_id", sa.String(32), nullable=True),
        sa.Column("onet_scale_id", sa.String(16), nullable=True),
        sa.Column("block", sa.String(40), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("min_value", sa.Numeric(8, 3), nullable=True),
        sa.Column("max_value", sa.Numeric(8, 3), nullable=True),
        sa.CheckConstraint(
            "response_type IN ('likert', 'sparse_select', 'choice', 'text', 'boolean', 'preference')",
            name="ck_questions_response_type",
        ),
        sa.UniqueConstraint("questionnaire_version_id", "code", name="uq_questions_version_code"),
    )
    op.create_index("ix_questions_questionnaire_version_id", "questions", ["questionnaire_version_id"])

    op.create_table(
        "question_options",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("question_id", UUID, sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", sa.String(128), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("onet_element_id", sa.String(32), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("question_id", "value", name="uq_question_options_value"),
    )
    op.create_index("ix_question_options_question_id", "question_options", ["question_id"])
    op.create_index("ix_question_options_onet_element_id", "question_options", ["onet_element_id"])

    op.create_table(
        "onet_snapshots",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("feature_version", sa.String(64), nullable=False),
        sa.Column("onet_release", sa.String(16), nullable=False),
        sa.Column("onet_release_month", sa.String(32), nullable=True),
        sa.Column("scales_json", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("block_spec_json", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("source_files_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("feature_version", name="uq_onet_snapshots_feature_version"),
    )

    op.create_table(
        "occupations",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("snapshot_id", UUID, sa.ForeignKey("onet_snapshots.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("onetsoc_code", sa.String(16), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("job_zone", sa.Integer(), nullable=True),
        sa.Column("knn_complete", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("recommendable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_education", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_work_context", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("snapshot_id", "onetsoc_code", name="uq_occupations_snapshot_soc"),
    )
    op.create_index("ix_occupations_snapshot_id", "occupations", ["snapshot_id"])
    op.create_index("ix_occupations_onetsoc_code", "occupations", ["onetsoc_code"])
    op.create_index("ix_occupations_recommendable", "occupations", ["recommendable"])
    op.create_index("ix_occupations_snapshot_recommendable", "occupations", ["snapshot_id", "recommendable"])

    op.create_table(
        "occupation_features",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("snapshot_id", UUID, sa.ForeignKey("onet_snapshots.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("occupation_id", UUID, sa.ForeignKey("occupations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain", sa.String(40), nullable=False),
        sa.Column("element_id", sa.String(32), nullable=False),
        sa.Column("element_name", sa.Text(), nullable=False),
        sa.Column("scale_id", sa.String(16), nullable=False),
        sa.Column("category", sa.String(16), nullable=False, server_default=""),
        sa.Column("raw_value", sa.Numeric(12, 6), nullable=False),
        sa.Column("used_value", sa.Numeric(12, 6), nullable=True),
        sa.Column("normalized_value", sa.Numeric(12, 6), nullable=True),
        sa.Column("not_relevant", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("recommend_suppress", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("include_in_knn", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint(
            "occupation_id", "domain", "element_id", "category", name="uq_occupation_features_element"
        ),
    )
    op.create_index("ix_occupation_features_snapshot_id", "occupation_features", ["snapshot_id"])
    op.create_index("ix_occupation_features_occupation_id", "occupation_features", ["occupation_id"])
    op.create_index("ix_occupation_features_domain", "occupation_features", ["domain"])
    op.create_index(
        "ix_occupation_features_snapshot_domain_element",
        "occupation_features",
        ["snapshot_id", "domain", "element_id"],
    )

    op.create_table(
        "job_zone_definitions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("snapshot_id", UUID, sa.ForeignKey("onet_snapshots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_zone", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("education", sa.Text(), nullable=True),
        sa.Column("experience", sa.Text(), nullable=True),
        sa.Column("job_training", sa.Text(), nullable=True),
        sa.Column("examples", sa.Text(), nullable=True),
        sa.Column("svp_range", sa.String(64), nullable=True),
        sa.UniqueConstraint("snapshot_id", "job_zone", name="uq_job_zone_definitions"),
    )
    op.create_index("ix_job_zone_definitions_snapshot_id", "job_zone_definitions", ["snapshot_id"])

    op.create_table(
        "education_categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("snapshot_id", UUID, sa.ForeignKey("onet_snapshots.id", ondelete="CASCADE"), nullable=False),
        sa.Column("element_id", sa.String(32), nullable=False),
        sa.Column("scale_id", sa.String(16), nullable=False, server_default="RL"),
        sa.Column("category", sa.String(16), nullable=False),
        sa.Column("category_description", sa.Text(), nullable=False),
        sa.UniqueConstraint("snapshot_id", "element_id", "category", name="uq_education_categories"),
    )
    op.create_index("ix_education_categories_snapshot_id", "education_categories", ["snapshot_id"])

    op.create_table(
        "recommendation_configs",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("k", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("metric", sa.String(120), nullable=False),
        sa.Column("block_weights_json", JSONB, nullable=False),
        sa.Column("rule_params_json", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("k IN (5, 10, 15)", name="ck_recommendation_configs_k"),
        sa.UniqueConstraint("version", name="uq_recommendation_configs_version"),
    )

    op.create_table(
        "rules",
        sa.Column("code", sa.String(32), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("params_json", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("explanation_template", sa.Text(), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "faculty_knowledge_priors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("faculty", sa.Text(), nullable=False),
        sa.Column("element_id", sa.String(32), nullable=False),
        sa.Column("element_name", sa.Text(), nullable=True),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("faculty", "element_id", name="uq_faculty_knowledge_priors"),
    )
    op.create_index("ix_faculty_knowledge_priors_faculty", "faculty_knowledge_priors", ["faculty"])

    op.create_table(
        "system_config",
        sa.Column("key", sa.String(80), primary_key=True),
        sa.Column("value_json", JSONB, nullable=False),
        sa.Column("updated_by", UUID, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "assessments",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("student_user_id", UUID, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column(
            "questionnaire_version_id",
            UUID,
            sa.ForeignKey("questionnaire_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("onet_snapshot_id", UUID, sa.ForeignKey("onet_snapshots.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("feature_version", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="in_progress"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('in_progress', 'completed', 'abandoned')", name="ck_assessments_status"),
    )
    op.create_index("ix_assessments_student_user_id", "assessments", ["student_user_id"])
    op.create_index("ix_assessments_questionnaire_version_id", "assessments", ["questionnaire_version_id"])
    op.create_index("ix_assessments_onet_snapshot_id", "assessments", ["onet_snapshot_id"])
    op.create_index("ix_assessments_student_status", "assessments", ["student_user_id", "status"])

    op.create_table(
        "assessment_responses",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("assessment_id", UUID, sa.ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", UUID, sa.ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column(
            "question_option_id", UUID, sa.ForeignKey("question_options.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("raw_value", sa.Text(), nullable=False),
        sa.Column("normalized_value", sa.Numeric(12, 6), nullable=True),
        sa.Column("onet_element_id", sa.String(32), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "assessment_id", "question_id", "onet_element_id", name="uq_assessment_responses_sparse"
        ),
    )
    op.create_index("ix_assessment_responses_assessment_id", "assessment_responses", ["assessment_id"])
    op.create_index("ix_assessment_responses_question_id", "assessment_responses", ["question_id"])

    op.create_table(
        "recommendation_runs",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("assessment_id", UUID, sa.ForeignKey("assessments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("student_user_id", UUID, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column(
            "questionnaire_version_id",
            UUID,
            sa.ForeignKey("questionnaire_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("onet_snapshot_id", UUID, sa.ForeignKey("onet_snapshots.id", ondelete="RESTRICT"), nullable=False),
        sa.Column(
            "config_id", UUID, sa.ForeignKey("recommendation_configs.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("feature_version", sa.String(64), nullable=False),
        sa.Column("k", sa.Integer(), nullable=False),
        sa.Column("metric", sa.String(120), nullable=False),
        sa.Column("eligible_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("elapsed_ms", sa.Integer(), nullable=True),
        sa.Column("weights_json", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_recommendation_runs_assessment_id", "recommendation_runs", ["assessment_id"])
    op.create_index("ix_recommendation_runs_student_user_id", "recommendation_runs", ["student_user_id"])
    op.create_index("ix_recommendation_runs_onet_snapshot_id", "recommendation_runs", ["onet_snapshot_id"])
    op.create_index("ix_recommendation_runs_config_id", "recommendation_runs", ["config_id"])
    op.create_index("ix_recommendation_runs_created_at", "recommendation_runs", ["created_at"])

    op.create_table(
        "recommendation_items",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("run_id", UUID, sa.ForeignKey("recommendation_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("occupation_id", UUID, sa.ForeignKey("occupations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("onetsoc_code", sa.String(16), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("distance", sa.Numeric(12, 8), nullable=False),
        sa.Column("raw_similarity", sa.Numeric(12, 8), nullable=False),
        sa.Column("recommendation_score", sa.Numeric(12, 8), nullable=False),
        sa.Column("explanation_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("job_zone_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("run_id", "rank", name="uq_recommendation_items_rank"),
        sa.UniqueConstraint("run_id", "occupation_id", name="uq_recommendation_items_occupation"),
    )
    op.create_index("ix_recommendation_items_run_id", "recommendation_items", ["run_id"])
    op.create_index("ix_recommendation_items_occupation_id", "recommendation_items", ["occupation_id"])

    op.create_table(
        "recommendation_contributions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("item_id", UUID, sa.ForeignKey("recommendation_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("block", sa.String(40), nullable=False),
        sa.Column("element_id", sa.String(32), nullable=False),
        sa.Column("element_name", sa.Text(), nullable=False),
        sa.Column("student_raw", sa.Numeric(12, 6), nullable=True),
        sa.Column("student_normalized", sa.Numeric(12, 6), nullable=True),
        sa.Column("occupation_raw", sa.Numeric(12, 6), nullable=True),
        sa.Column("occupation_normalized", sa.Numeric(12, 6), nullable=True),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_recommendation_contributions_item_id", "recommendation_contributions", ["item_id"])

    op.create_table(
        "rule_firings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", UUID, sa.ForeignKey("recommendation_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", UUID, sa.ForeignKey("recommendation_items.id", ondelete="CASCADE"), nullable=True),
        sa.Column("occupation_id", UUID, sa.ForeignKey("occupations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("onetsoc_code", sa.String(16), nullable=False),
        sa.Column("rule_code", sa.String(32), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("penalty", sa.Numeric(8, 4), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("element_id", sa.String(32), nullable=True),
        sa.Column("domain", sa.String(40), nullable=True),
        sa.CheckConstraint(
            "action IN ('exclude', 'penalise', 'flag', 'drop', 'floor')",
            name="ck_rule_firings_action",
        ),
    )
    op.create_index("ix_rule_firings_run_id", "rule_firings", ["run_id"])
    op.create_index("ix_rule_firings_item_id", "rule_firings", ["item_id"])
    op.create_index("ix_rule_firings_rule_code", "rule_firings", ["rule_code"])

    op.create_table(
        "recommendation_ratings",
        sa.Column("id", UUID, primary_key=True, nullable=False),
        sa.Column("item_id", UUID, sa.ForeignKey("recommendation_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_user_id", UUID, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("relevance_1_to_5", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("relevance_1_to_5 BETWEEN 1 AND 5", name="ck_recommendation_ratings_scale"),
        sa.UniqueConstraint("item_id", "student_user_id", name="uq_recommendation_ratings_item_student"),
    )
    op.create_index("ix_recommendation_ratings_item_id", "recommendation_ratings", ["item_id"])
    op.create_index("ix_recommendation_ratings_student_user_id", "recommendation_ratings", ["student_user_id"])

    rules = sa.table(
        "rules",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("enabled", sa.Boolean),
        sa.column("priority", sa.Integer),
        sa.column("params_json", JSONB),
        sa.column("explanation_template", sa.Text),
    )
    op.bulk_insert(
        rules,
        [
            {
                "code": "R-DATA",
                "name": "Required domain coverage",
                "enabled": True,
                "priority": 10,
                "params_json": {},
                "explanation_template": "Occupation is missing a required KNN domain vector",
            },
            {
                "code": "R-SUPPRESS",
                "name": "O*NET suppress and not-relevant flags",
                "enabled": True,
                "priority": 20,
                "params_json": {},
                "explanation_template": "Recommend Suppress drops a feature; Not Relevant floors importance",
            },
            {
                "code": "R-ZONE-LOW",
                "name": "Exclude Job Zone 2",
                "enabled": True,
                "priority": 30,
                "params_json": {"excluded_zones": [2]},
                "explanation_template": "Job Zone 2 occupations are excluded for this undergraduate system",
            },
            {
                "code": "R-ZONE-5",
                "name": "Flag Job Zone 5",
                "enabled": True,
                "priority": 40,
                "params_json": {"flag_when_further_study": "no"},
                "explanation_template": "Job Zone 5 typically requires graduate or professional training",
            },
            {
                "code": "R-RELATED",
                "name": "Course-related knowledge prior",
                "enabled": True,
                "priority": 50,
                "params_json": {"threshold": 3.0, "penalty": 0.8},
                "explanation_template": "Course-related preference: mean knowledge importance is below threshold",
            },
            {
                "code": "R-CONTEXT",
                "name": "Work context preference penalties",
                "enabled": True,
                "priority": 60,
                "params_json": {
                    "outdoor_penalty": 0.85,
                    "public_penalty": 0.9,
                    "team_penalty": 0.95,
                },
                "explanation_template": "Work setting mismatch against O*NET Work Context CX",
            },
            {
                "code": "R-EDU",
                "name": "Professional or doctoral education flag",
                "enabled": True,
                "priority": 70,
                "params_json": {"categories": ["10", "11"]},
                "explanation_template": "Incumbents most often report a first professional or doctoral degree",
            },
        ],
    )

    configs = sa.table(
        "recommendation_configs",
        sa.column("id", UUID),
        sa.column("version", sa.String),
        sa.column("k", sa.Integer),
        sa.column("metric", sa.String),
        sa.column("block_weights_json", JSONB),
        sa.column("rule_params_json", JSONB),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO recommendation_configs (id, version, k, metric, block_weights_json, rule_params_json)
            VALUES (
                '11111111-1111-1111-1111-111111111111',
                'config_v1',
                10,
                'weighted-block cosine (sklearn NearestNeighbors, algorithm=brute)',
                '{"riasec": 0.25, "sia": 0.20, "essential_skills": 0.20, "transferable_skills": 0.15, "work_styles": 0.10, "knowledge": 0.10}'::jsonb,
                '{}'::jsonb
            )
            """
        )
    )

    op.execute(
        sa.text(
            """
            INSERT INTO system_config (key, value_json) VALUES
            ('active_feature_version', '{"value": "onet_30_3_v1"}'::jsonb),
            ('active_config_version', '{"value": "config_v1"}'::jsonb),
            ('active_questionnaire_version', '{"value": null}'::jsonb)
            """
        )
    )


def downgrade() -> None:
    for table in [
        "recommendation_ratings",
        "rule_firings",
        "recommendation_contributions",
        "recommendation_items",
        "recommendation_runs",
        "assessment_responses",
        "assessments",
        "system_config",
        "faculty_knowledge_priors",
        "rules",
        "recommendation_configs",
        "education_categories",
        "job_zone_definitions",
        "occupation_features",
        "occupations",
        "onet_snapshots",
        "question_options",
        "questions",
        "questionnaire_versions",
        "student_profiles",
        "users",
    ]:
        op.drop_table(table)
