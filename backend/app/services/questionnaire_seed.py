"""Seed the Version 1 questionnaire from FINAL_SPEC + student_features IDs.

Question codes match app.recommendation.constants internal names. O*NET element
IDs are official Content Model IDs from the processed 30.3 snapshot. Faculty
option labels are the NSUK faculties listed in FINAL_SPEC.md. Department names
are not hard-coded.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import REPO_ROOT
from app.models import Question, QuestionnaireVersion, QuestionOption, SystemConfig
from app.recommendation.constants import (
    CONTEXT_INDOOR,
    CONTEXT_OUTDOOR,
    CONTEXT_PUBLIC,
    CONTEXT_TEAM,
    ESSENTIAL_INTERNAL_NAMES,
    FEATURE_VERSION,
    PROCESSED_DIRNAME,
    RIASEC_INTERNAL_NAMES,
    TRANSFERABLE_INTERNAL_NAMES,
    WORK_STYLE_INTERNAL_NAMES,
)

QUESTIONNAIRE_VERSION = "questionnaire_v1"
QUESTIONNAIRE_VERSION_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")

# Official NSUK faculties listed in FINAL_SPEC.md (academics page). Not invented.
NSUK_FACULTIES = (
    "Administration",
    "Agriculture",
    "Arts",
    "Communication and Media Studies",
    "Education",
    "Engineering",
    "Environmental Sciences",
    "Law",
    "Natural and Applied Sciences",
    "Social Sciences",
    "College of Medicine and Health Allied Sciences",
)

RIASEC_PROMPTS = {
    "interest_realistic": (
        "How much would you enjoy realistic work (building, repairing, outdoor or physical work, using tools or machines)?"
    ),
    "interest_investigative": "How much would you enjoy investigative work (research, analysis, science)?",
    "interest_artistic": "How much would you enjoy artistic work (design, writing, performance, original work)?",
    "interest_social": "How much would you enjoy social work (helping, teaching, counselling)?",
    "interest_enterprising": "How much would you enjoy enterprising work (leading, selling, persuading, business)?",
    "interest_conventional": "How much would you enjoy conventional work (records, procedures, structured data work)?",
}

ESSENTIAL_PROMPTS = {
    "skill_reading": "Reading comprehension — how strong is your current skill?",
    "skill_listening": "Active listening — how strong is your current skill?",
    "skill_writing": "Writing — how strong is your current skill?",
    "skill_speaking": "Speaking — how strong is your current skill?",
    "skill_math": "Mathematics — how strong is your current skill?",
    "skill_science": "Science — how strong is your current skill?",
    "skill_critical_thinking": "Critical thinking — how strong is your current skill?",
    "skill_active_learning": "Active learning — how strong is your current skill?",
    "skill_learning_strategies": "Learning strategies — how strong is your current skill?",
    "skill_monitoring": "Monitoring (checking progress or quality) — how strong is your current skill?",
}

TRANSFERABLE_PROMPTS = {
    "skill_problem_solving": "Complex problem solving — how strong is your current skill?",
    "skill_programming": "Programming — how strong is your current skill?",
    "skill_instructing": "Instructing / teaching others — how strong is your current skill?",
    "skill_persuasion": "Persuasion — how strong is your current skill?",
    "skill_negotiation": "Negotiation — how strong is your current skill?",
    "skill_time_management": "Time management — how strong is your current skill?",
}

STYLE_PROMPTS = {
    "style_innovation": "I am inventive and like new ways of doing work.",
    "style_achievement": "I set demanding goals and work hard to reach them.",
    "style_leadership": "I am comfortable taking charge and leading.",
    "style_cooperation": "I enjoy cooperating and helping colleagues.",
    "style_detail": "I am thorough and pay attention to detail.",
    "style_stress": "I stay effective under stress.",
}

PREFERENCE_PROMPTS = {
    "pref_indoor": ("I prefer mostly indoor, office-type settings.", CONTEXT_INDOOR, "Indoors, Environmentally Controlled"),
    "pref_outdoor": (
        "I am comfortable working outdoors / in the field.",
        CONTEXT_OUTDOOR,
        "Outdoors, Exposed to All Weather Conditions",
    ),
    "pref_team": (
        "I prefer working as part of a team.",
        CONTEXT_TEAM,
        "Work With or Contribute to a Work Group or Team",
    ),
    "pref_public": (
        "I am comfortable dealing with the public / customers.",
        CONTEXT_PUBLIC,
        "Deal With External Customers or the Public in General",
    ),
}


def _metadata_path() -> Path:
    return REPO_ROOT / "data" / "processed" / PROCESSED_DIRNAME / "metadata.json"


def _load_block_names(block: str) -> list[tuple[str, str]]:
    path = _metadata_path()
    if not path.is_file():
        raise FileNotFoundError(f"Processed snapshot metadata is required to seed questionnaire options: {path}")
    metadata = json.loads(path.read_text(encoding="utf-8"))
    spec = metadata["blocks"][block]
    names = spec.get("element_names") or {}
    return [(element_id, names.get(element_id, element_id)) for element_id in spec["element_ids"]]


def _likert_options(question_id: uuid.UUID, minimum: int, maximum: int, low_label: str, high_label: str) -> list[QuestionOption]:
    options = []
    for value in range(minimum, maximum + 1):
        if value == minimum:
            label = f"{value} — {low_label}"
        elif value == maximum:
            label = f"{value} — {high_label}"
        else:
            label = str(value)
        options.append(
            QuestionOption(
                id=uuid.uuid4(),
                question_id=question_id,
                value=str(value),
                label=label,
                sort_order=value,
            )
        )
    return options


def _choice_options(question_id: uuid.UUID, pairs: list[tuple[str, str]]) -> list[QuestionOption]:
    return [
        QuestionOption(
            id=uuid.uuid4(),
            question_id=question_id,
            value=value,
            label=label,
            sort_order=index,
        )
        for index, (value, label) in enumerate(pairs)
    ]


def _set_active_questionnaire(session: Session) -> None:
    row = session.get(SystemConfig, "active_questionnaire_version")
    payload = {"value": QUESTIONNAIRE_VERSION}
    if row is None:
        session.add(SystemConfig(key="active_questionnaire_version", value_json=payload))
    else:
        row.value_json = payload


def seed_questionnaire_v1(session: Session) -> QuestionnaireVersion:
    existing = session.scalar(
        select(QuestionnaireVersion).where(QuestionnaireVersion.version == QUESTIONNAIRE_VERSION)
    )
    if existing is not None:
        _set_active_questionnaire(session)
        return existing

    sia_options = _load_block_names("sia")
    knowledge_options = _load_block_names("knowledge")
    version = QuestionnaireVersion(
        id=QUESTIONNAIRE_VERSION_ID,
        version=QUESTIONNAIRE_VERSION,
        feature_version=FEATURE_VERSION,
        status="published",
    )
    session.add(version)
    session.flush()

    order = 0
    questions: list[Question] = []
    options: list[QuestionOption] = []

    def add_question(**kwargs) -> Question:
        nonlocal order
        order += 10
        question = Question(id=uuid.uuid4(), questionnaire_version_id=version.id, sort_order=order, **kwargs)
        questions.append(question)
        return question

    faculty_q = add_question(
        code="faculty",
        section="profile",
        prompt="Which NSUK faculty are you enrolled in?",
        response_type="choice",
        block="profile",
        is_required=False,
    )
    options.extend(_choice_options(faculty_q.id, [(name, name) for name in NSUK_FACULTIES]))

    add_question(
        code="department",
        section="profile",
        prompt="Department / programme (optional). Leave blank if not confirmed.",
        response_type="text",
        block="profile",
        is_required=False,
    )

    level_q = add_question(
        code="level",
        section="profile",
        prompt="What is your current undergraduate level?",
        response_type="choice",
        block="profile",
        is_required=True,
    )
    options.extend(_choice_options(level_q.id, [(level, f"{level} level") for level in ("100", "200", "300", "400")]))

    further_q = add_question(
        code="further_study",
        section="profile",
        prompt="Are you willing to pursue postgraduate or professional training after your current programme?",
        response_type="choice",
        block="profile",
        is_required=True,
    )
    options.extend(
        _choice_options(
            further_q.id,
            [("yes", "Yes"), ("maybe", "Maybe"), ("no", "No")],
        )
    )

    related_q = add_question(
        code="course_relatedness",
        section="profile",
        prompt="Do you prefer careers related to your course, or are you open to other fields?",
        response_type="choice",
        block="profile",
        is_required=True,
    )
    options.extend(
        _choice_options(
            related_q.id,
            [("related", "Related to my course"), ("open", "Open to other fields")],
        )
    )

    for code, element_id in RIASEC_INTERNAL_NAMES.items():
        question = add_question(
            code=code,
            section="riasec",
            prompt=RIASEC_PROMPTS[code],
            response_type="likert",
            onet_element_id=element_id,
            onet_scale_id="OI",
            block="riasec",
            is_required=True,
            min_value=1,
            max_value=7,
        )
        options.extend(
            _likert_options(
                question.id,
                1,
                7,
                "Strongly dislike this type of work",
                "Strongly like this type of work",
            )
        )

    sia_q = add_question(
        code="sia",
        section="sia",
        prompt="Select 1 to 5 specific interest areas, then rate how much you would enjoy each (1–7).",
        response_type="sparse_select",
        onet_scale_id="OI",
        block="sia",
        is_required=True,
        min_value=1,
        max_value=7,
    )
    for index, (element_id, name) in enumerate(sia_options):
        options.append(
            QuestionOption(
                id=uuid.uuid4(),
                question_id=sia_q.id,
                value=element_id,
                label=name,
                onet_element_id=element_id,
                sort_order=index,
            )
        )

    for code, element_id in ESSENTIAL_INTERNAL_NAMES.items():
        question = add_question(
            code=code,
            section="essential_skills",
            prompt=ESSENTIAL_PROMPTS[code],
            response_type="likert",
            onet_element_id=element_id,
            onet_scale_id="IM",
            block="essential_skills",
            is_required=True,
            min_value=1,
            max_value=5,
        )
        options.extend(
            _likert_options(question.id, 1, 5, "Very limited current skill", "Very strong current skill")
        )

    for code, element_id in TRANSFERABLE_INTERNAL_NAMES.items():
        question = add_question(
            code=code,
            section="transferable_skills",
            prompt=TRANSFERABLE_PROMPTS[code],
            response_type="likert",
            onet_element_id=element_id,
            onet_scale_id="IM",
            block="transferable_skills",
            is_required=True,
            min_value=1,
            max_value=5,
        )
        options.extend(
            _likert_options(question.id, 1, 5, "Very limited current skill", "Very strong current skill")
        )

    for code, element_id in WORK_STYLE_INTERNAL_NAMES.items():
        question = add_question(
            code=code,
            section="work_styles",
            prompt=STYLE_PROMPTS[code],
            response_type="likert",
            onet_element_id=element_id,
            onet_scale_id="WI",
            block="work_styles",
            is_required=True,
            min_value=1,
            max_value=5,
        )
        options.extend(
            _likert_options(question.id, 1, 5, "Does not describe me", "Describes me very well")
        )

    knowledge_q = add_question(
        code="knowledge",
        section="knowledge",
        prompt="Select 1 to 5 knowledge areas you are strongest in or enjoy studying, then rate each (1–5).",
        response_type="sparse_select",
        onet_scale_id="IM",
        block="knowledge",
        is_required=True,
        min_value=1,
        max_value=5,
    )
    for index, (element_id, name) in enumerate(knowledge_options):
        options.append(
            QuestionOption(
                id=uuid.uuid4(),
                question_id=knowledge_q.id,
                value=element_id,
                label=name,
                onet_element_id=element_id,
                sort_order=index,
            )
        )

    for code, (prompt, element_id, _name) in PREFERENCE_PROMPTS.items():
        question = add_question(
            code=code,
            section="work_preferences",
            prompt=prompt,
            response_type="preference",
            onet_element_id=element_id,
            onet_scale_id="CX",
            block="work_context",
            is_required=True,
            min_value=1,
            max_value=5,
        )
        options.extend(_likert_options(question.id, 1, 5, "Strongly disagree", "Strongly agree"))

    session.add_all(questions)
    session.flush()
    session.add_all(options)
    _set_active_questionnaire(session)
    session.flush()
    return version
