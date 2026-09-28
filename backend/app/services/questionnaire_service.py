"""Read published questionnaires. No scoring."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError
from app.models import Question, QuestionnaireVersion, SystemConfig
from app.recommendation.constants import MAX_SPARSE_SELECTIONS, MIN_SPARSE_SELECTIONS
from app.schemas.recommendation import QuestionOptionOut, QuestionOut, QuestionnaireOut
from app.services.questionnaire_seed import QUESTIONNAIRE_VERSION


def active_questionnaire_version_name(session: Session) -> str:
    row = session.get(SystemConfig, "active_questionnaire_version")
    value = (row.value_json or {}).get("value") if row else None
    return str(value or QUESTIONNAIRE_VERSION)


def get_questionnaire(session: Session, version: str) -> QuestionnaireOut:
    questionnaire = session.scalar(
        select(QuestionnaireVersion).where(QuestionnaireVersion.version == version)
    )
    if questionnaire is None:
        raise NotFoundError(f"Questionnaire version {version} was not found", code="invalid_questionnaire_version")
    questions = session.scalars(
        select(Question)
        .where(Question.questionnaire_version_id == questionnaire.id)
        .options(selectinload(Question.options))
        .order_by(Question.sort_order, Question.code)
    ).all()
    return QuestionnaireOut(
        version=questionnaire.version,
        feature_version=questionnaire.feature_version,
        status=questionnaire.status,
        questions=[_question_out(question) for question in questions],
    )


def get_active_questionnaire(session: Session) -> QuestionnaireOut:
    return get_questionnaire(session, active_questionnaire_version_name(session))


def _question_out(question: Question) -> QuestionOut:
    options = sorted(question.options, key=lambda item: (item.sort_order, item.value))
    min_selections = MIN_SPARSE_SELECTIONS if question.response_type == "sparse_select" else None
    max_selections = MAX_SPARSE_SELECTIONS if question.response_type == "sparse_select" else None
    return QuestionOut(
        code=question.code,
        section=question.section,
        prompt=question.prompt,
        response_type=question.response_type,
        block=question.block,
        onet_element_id=question.onet_element_id,
        onet_scale_id=question.onet_scale_id,
        sort_order=question.sort_order,
        is_required=question.is_required,
        min_value=float(question.min_value) if question.min_value is not None else None,
        max_value=float(question.max_value) if question.max_value is not None else None,
        min_selections=min_selections,
        max_selections=max_selections,
        options=[
            QuestionOptionOut(
                value=option.value,
                label=option.label,
                onet_element_id=option.onet_element_id,
                sort_order=option.sort_order,
            )
            for option in options
        ],
    )
