"""Validate and store assessments, then hand off to the recommendation service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ServiceUnavailableError, UnprocessableError
from app.models import (
    Assessment,
    AssessmentResponse,
    Question,
    QuestionnaireVersion,
    QuestionOption,
    RecommendationConfig,
    StudentProfile,
    SystemConfig,
    User,
)
from app.recommendation.constants import (
    COURSE_RELATEDNESS_VALUES,
    FURTHER_STUDY_VALUES,
    LEVEL_VALUES,
    MAX_SPARSE_SELECTIONS,
    MIN_SPARSE_SELECTIONS,
)
from app.recommendation.exceptions import AssessmentError
from app.recommendation.preprocess import minmax
from app.recommendation.student_features import AcademicProfile, StudentAssessment, WorkPreferences
from app.schemas.recommendation import AssessmentCreateRequest, AssessmentResponseIn, RecommendationRunOut
from app.services.occupation_service import get_active_snapshot
from app.services.recommendation_service import persist_recommendation_run


def submit_assessment(session: Session, student: User, payload: AssessmentCreateRequest) -> RecommendationRunOut:
    questionnaire = session.scalar(
        select(QuestionnaireVersion).where(QuestionnaireVersion.version == payload.questionnaire_version)
    )
    if questionnaire is None or questionnaire.status != "published":
        raise UnprocessableError(
            f"Questionnaire version {payload.questionnaire_version} is not available",
            code="invalid_questionnaire_version",
        )
    snapshot = get_active_snapshot(session)
    if snapshot is None:
        raise ServiceUnavailableError("Active O*NET snapshot is not loaded", code="missing_snapshot")
    config = _active_config(session)

    questions = session.scalars(
        select(Question)
        .where(Question.questionnaire_version_id == questionnaire.id)
        .options(selectinload(Question.options))
    ).all()
    by_code = {question.code: question for question in questions}
    grouped = _group_responses(payload.responses, by_code)
    _require_complete(grouped, questions)

    assessment = Assessment(
        student_user_id=student.id,
        questionnaire_version_id=questionnaire.id,
        onet_snapshot_id=snapshot.id,
        feature_version=snapshot.feature_version,
        status="completed",
        completed_at=datetime.now(timezone.utc),
    )
    session.add(assessment)
    session.flush()
    stored = _store_responses(session, assessment.id, grouped, by_code)
    student_assessment = _to_student_assessment(stored, by_code)
    _update_profile(session, student, student_assessment.profile)
    try:
        return persist_recommendation_run(
            session,
            student=student,
            assessment=assessment,
            questionnaire=questionnaire,
            snapshot=snapshot,
            config=config,
            student_assessment=student_assessment,
        )
    except AssessmentError as exc:
        raise UnprocessableError(str(exc), code="invalid_response") from exc


def _active_config(session: Session) -> RecommendationConfig:
    row = session.get(SystemConfig, "active_config_version")
    version = ((row.value_json or {}).get("value") if row else None) or "config_v1"
    config = session.scalar(select(RecommendationConfig).where(RecommendationConfig.version == version))
    if config is None:
        raise ServiceUnavailableError(
            "Active recommendation configuration is not loaded",
            code="missing_recommendation_configuration",
        )
    return config


def _group_responses(
    responses: list[AssessmentResponseIn],
    by_code: dict[str, Question],
) -> dict[str, list[AssessmentResponseIn]]:
    grouped: dict[str, list[AssessmentResponseIn]] = {}
    for item in responses:
        if item.code not in by_code:
            raise UnprocessableError(f"Unknown question code: {item.code}", code="invalid_response")
        grouped.setdefault(item.code, []).append(item)
    return grouped


def _require_complete(grouped: dict[str, list[AssessmentResponseIn]], questions: list[Question]) -> None:
    missing = [
        question.code
        for question in questions
        if question.is_required and question.code not in grouped
    ]
    if missing:
        raise UnprocessableError(
            f"Missing required response(s): {', '.join(missing)}",
            code="missing_required_response",
        )


def _store_responses(
    session: Session,
    assessment_id,
    grouped: dict[str, list[AssessmentResponseIn]],
    by_code: dict[str, Question],
) -> dict[str, list[AssessmentResponse]]:
    stored: dict[str, list[AssessmentResponse]] = {}
    rows: list[AssessmentResponse] = []
    for code, items in grouped.items():
        question = by_code[code]
        parsed = _parse_question_responses(question, items)
        stored[code] = parsed
        rows.extend(parsed)
        for row in parsed:
            row.assessment_id = assessment_id
            row.question_id = question.id
    session.add_all(rows)
    session.flush()
    return stored


def _option_map(question: Question) -> dict[str, QuestionOption]:
    return {option.value: option for option in question.options}


def _parse_question_responses(question: Question, items: list[AssessmentResponseIn]) -> list[AssessmentResponse]:
    if question.response_type == "sparse_select":
        return _parse_sparse(question, items)
    if len(items) != 1:
        raise UnprocessableError(f"Question {question.code} must have a single response", code="invalid_response")
    item = items[0]
    if item.selections:
        raise UnprocessableError(f"Question {question.code} does not accept selections", code="invalid_response")
    raw = "" if item.value is None else str(item.value).strip()
    if question.is_required and raw == "":
        raise UnprocessableError(
            f"Missing required response(s): {question.code}",
            code="missing_required_response",
        )
    if not question.is_required and raw == "":
        return []
    options = _option_map(question)
    option = options.get(raw)
    if question.response_type in {"choice", "likert", "preference"} and option is None:
        raise UnprocessableError(f"Invalid value for {question.code}", code="invalid_response")
    if question.response_type in {"likert", "preference"}:
        number = _numeric(raw, question.code)
        minimum = float(question.min_value) if question.min_value is not None else None
        maximum = float(question.max_value) if question.max_value is not None else None
        if minimum is not None and maximum is not None and (number < minimum or number > maximum):
            raise UnprocessableError(f"Invalid value for {question.code}", code="invalid_response")
        normalized = minmax(number, minimum, maximum) if minimum is not None and maximum is not None else None
        return [
            AssessmentResponse(
                raw_value=str(int(number)),
                normalized_value=normalized,
                onet_element_id=question.onet_element_id or "",
                question_option_id=option.id if option else None,
            )
        ]
    if question.code == "level" and raw not in LEVEL_VALUES:
        raise UnprocessableError("level must be 100, 200, 300, or 400", code="invalid_response")
    if question.code == "further_study" and raw not in FURTHER_STUDY_VALUES:
        raise UnprocessableError("further_study must be yes, maybe, or no", code="invalid_response")
    if question.code == "course_relatedness" and raw not in COURSE_RELATEDNESS_VALUES:
        raise UnprocessableError("course_relatedness must be related or open", code="invalid_response")
    return [
        AssessmentResponse(
            raw_value=raw,
            normalized_value=None,
            onet_element_id="",
            question_option_id=option.id if option else None,
        )
    ]


def _parse_sparse(question: Question, items: list[AssessmentResponseIn]) -> list[AssessmentResponse]:
    selections: list[tuple[str, str]] = []
    for item in items:
        if item.selections:
            if item.value is not None:
                raise UnprocessableError(
                    f"Question {question.code} selections must not also include value",
                    code="invalid_response",
                )
            for selection in item.selections:
                selections.append((selection.element_id, str(selection.value)))
        elif item.value is not None:
            raise UnprocessableError(
                f"Question {question.code} requires selections of element_id and value",
                code="invalid_response",
            )
    allowed = {option.value: option for option in question.options}
    parsed: list[AssessmentResponse] = []
    seen: set[str] = set()
    minimum = float(question.min_value) if question.min_value is not None else 1.0
    maximum = float(question.max_value) if question.max_value is not None else 7.0
    for element_id, raw in selections:
        if element_id not in allowed:
            raise UnprocessableError(f"Unknown {question.code} element: {element_id}", code="invalid_response")
        if element_id in seen:
            raise UnprocessableError(f"Duplicate {question.code} selection {element_id}", code="invalid_response")
        seen.add(element_id)
        number = _numeric(raw, question.code)
        if number < minimum or number > maximum:
            raise UnprocessableError(f"Invalid value for {question.code}", code="invalid_response")
        option = allowed[element_id]
        parsed.append(
            AssessmentResponse(
                raw_value=str(int(number)),
                normalized_value=minmax(number, minimum, maximum),
                onet_element_id=option.onet_element_id or element_id,
                question_option_id=option.id,
            )
        )
    if len(parsed) < MIN_SPARSE_SELECTIONS:
        raise UnprocessableError(
            f"Select at least {MIN_SPARSE_SELECTIONS} {question.code} element(s)",
            code="incomplete_assessment",
        )
    if len(parsed) > MAX_SPARSE_SELECTIONS:
        raise UnprocessableError(
            f"Select at most {MAX_SPARSE_SELECTIONS} {question.code} elements",
            code="invalid_response",
        )
    return parsed


def _numeric(raw: str, code: str) -> float:
    try:
        number = float(raw)
    except ValueError as exc:
        raise UnprocessableError(f"Invalid value for {code}", code="invalid_response") from exc
    if number != int(number):
        raise UnprocessableError(f"Invalid value for {code}", code="invalid_response")
    return number


def _first_value(stored: dict[str, list[AssessmentResponse]], code: str) -> str | None:
    rows = stored.get(code) or []
    if not rows:
        return None
    return rows[0].raw_value


def _to_student_assessment(
    stored: dict[str, list[AssessmentResponse]],
    by_code: dict[str, Question],
) -> StudentAssessment:
    def block_from_codes(codes: dict[str, str]) -> dict[str, object]:
        values: dict[str, object] = {}
        for code in codes:
            rows = stored.get(code) or []
            if not rows:
                continue
            values[code] = int(float(rows[0].raw_value))
        return values

    def sparse(code: str) -> dict[str, object]:
        return {row.onet_element_id: int(float(row.raw_value)) for row in stored.get(code) or []}

    riasec = block_from_codes({k: k for k in by_code if by_code[k].block == "riasec"})
    essential = block_from_codes({k: k for k in by_code if by_code[k].block == "essential_skills"})
    transferable = block_from_codes({k: k for k in by_code if by_code[k].block == "transferable_skills"})
    styles = block_from_codes({k: k for k in by_code if by_code[k].block == "work_styles"})
    return StudentAssessment(
        riasec=riasec,
        sia=sparse("sia"),
        essential_skills=essential,
        transferable_skills=transferable,
        work_styles=styles,
        knowledge=sparse("knowledge"),
        profile=AcademicProfile(
            faculty=_first_value(stored, "faculty"),
            department=_first_value(stored, "department"),
            level=_first_value(stored, "level"),
            further_study=_first_value(stored, "further_study") or "maybe",
            course_relatedness=_first_value(stored, "course_relatedness") or "open",
        ),
        preferences=WorkPreferences(
            pref_indoor=_optional_int(_first_value(stored, "pref_indoor")),
            pref_outdoor=_optional_int(_first_value(stored, "pref_outdoor")),
            pref_team=_optional_int(_first_value(stored, "pref_team")),
            pref_public=_optional_int(_first_value(stored, "pref_public")),
        ),
    )


def _optional_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(float(value))


def _update_profile(session: Session, student: User, profile: AcademicProfile) -> None:
    row = session.get(StudentProfile, student.id)
    if row is None:
        row = StudentProfile(user_id=student.id)
        session.add(row)
    row.faculty = profile.faculty
    row.department = profile.department
    row.level = profile.level
    row.further_study = profile.further_study
    row.course_relatedness = profile.course_relatedness
