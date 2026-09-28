"""Versioned O*NET 30.3 feature identifiers from the approved specification.

Element IDs are official O*NET Content Model IDs. Names are loaded from the
downloaded files at ingest time, not invented here.
"""

from __future__ import annotations

FEATURE_VERSION = "onet_30_3_v1"
ONET_RELEASE = "30.3"
ONET_RELEASE_MONTH = "May 2026"

RAW_DIRNAME = "db_30_3_text"
PROCESSED_DIRNAME = FEATURE_VERSION

DEFAULT_JOB_ZONES = (3, 4, 5)

BLOCK_WEIGHTS = {
    "riasec": 0.25,
    "sia": 0.20,
    "essential_skills": 0.20,
    "transferable_skills": 0.15,
    "work_styles": 0.10,
    "knowledge": 0.10,
}

KNN_BLOCKS = (
    "riasec",
    "sia",
    "essential_skills",
    "transferable_skills",
    "work_styles",
    "knowledge",
)

ALLOWED_K = frozenset({5, 10, 15})
DEFAULT_K = 10

OFFICIAL_SCALES = {
    "OI": (1.0, 7.0),
    "IM": (1.0, 5.0),
    "WI": (-3.0, 3.0),
    "CX": (1.0, 5.0),
    "RL": (0.0, 100.0),
}

# Student work-style items use a 1–5 self-description scale, not occupational WI.
STUDENT_STYLE_SCALE = (1.0, 5.0)
STUDENT_PREFERENCE_SCALE = (1.0, 5.0)

MAX_SPARSE_SELECTIONS = 5
MIN_SPARSE_SELECTIONS = 1

FURTHER_STUDY_VALUES = frozenset({"yes", "maybe", "no"})
COURSE_RELATEDNESS_VALUES = frozenset({"related", "open"})
LEVEL_VALUES = frozenset({"100", "200", "300", "400"})

CONTEXT_INDOOR = "4.C.2.a.1.a"
CONTEXT_OUTDOOR = "4.C.2.a.1.c"
CONTEXT_TEAM = "4.C.1.b.1.e"
CONTEXT_PUBLIC = "4.C.1.b.1.f"

PROFESSIONAL_EDUCATION_CATEGORIES = frozenset({"10", "11"})

RIASEC_INTERNAL_NAMES = {
    "interest_realistic": "1.B.1.a",
    "interest_investigative": "1.B.1.b",
    "interest_artistic": "1.B.1.c",
    "interest_social": "1.B.1.d",
    "interest_enterprising": "1.B.1.e",
    "interest_conventional": "1.B.1.f",
}

ESSENTIAL_INTERNAL_NAMES = {
    "skill_reading": "2.A.1.a",
    "skill_listening": "2.A.1.b",
    "skill_writing": "2.A.1.c",
    "skill_speaking": "2.A.1.d",
    "skill_math": "2.A.1.e",
    "skill_science": "2.A.1.f",
    "skill_critical_thinking": "2.A.2.a",
    "skill_active_learning": "2.A.2.b",
    "skill_learning_strategies": "2.A.2.c",
    "skill_monitoring": "2.A.2.d",
}

TRANSFERABLE_INTERNAL_NAMES = {
    "skill_problem_solving": "2.B.2.i",
    "skill_programming": "2.B.3.e",
    "skill_instructing": "2.B.1.e",
    "skill_persuasion": "2.B.1.c",
    "skill_negotiation": "2.B.1.d",
    "skill_time_management": "2.B.5.a",
}

WORK_STYLE_INTERNAL_NAMES = {
    "style_innovation": "1.D.1.a",
    "style_achievement": "1.D.1.b",
    "style_leadership": "1.D.1.i",
    "style_cooperation": "1.D.2.d",
    "style_detail": "1.D.3.b",
    "style_stress": "1.D.4.a",
}

RIASEC_ELEMENT_IDS = (
    "1.B.1.a",  # Realistic
    "1.B.1.b",  # Investigative
    "1.B.1.c",  # Artistic
    "1.B.1.d",  # Social
    "1.B.1.e",  # Enterprising
    "1.B.1.f",  # Conventional
)

ESSENTIAL_SKILL_IDS = (
    "2.A.1.a",  # Reading Comprehension
    "2.A.1.b",  # Active Listening
    "2.A.1.c",  # Writing
    "2.A.1.d",  # Speaking
    "2.A.1.e",  # Mathematics
    "2.A.1.f",  # Science
    "2.A.2.a",  # Critical Thinking
    "2.A.2.b",  # Active Learning
    "2.A.2.c",  # Learning Strategies
    "2.A.2.d",  # Monitoring
)

TRANSFERABLE_SKILL_IDS = (
    "2.B.2.i",  # Complex Problem Solving
    "2.B.3.e",  # Programming
    "2.B.1.e",  # Instructing
    "2.B.1.c",  # Persuasion
    "2.B.1.d",  # Negotiation
    "2.B.5.a",  # Time Management
)

WORK_STYLE_IDS = (
    "1.D.1.a",  # Innovation
    "1.D.1.b",  # Achievement Orientation
    "1.D.1.i",  # Leadership Orientation
    "1.D.2.d",  # Cooperation
    "1.D.3.b",  # Attention to Detail
    "1.D.4.a",  # Stress Tolerance
)

WORK_CONTEXT_IDS = (
    "4.C.2.a.1.a",  # Indoors, Environmentally Controlled
    "4.C.2.a.1.c",  # Outdoors, Exposed to All Weather Conditions
    "4.C.1.b.1.e",  # Work With or Contribute to a Work Group or Team
    "4.C.1.b.1.f",  # Deal With External Customers or the Public in General
)

EDUCATION_ELEMENT_ID = "2.D.1"

EXPECTED_SIA_COUNT = 41
EXPECTED_KNOWLEDGE_COUNT = 33
EXPECTED_WORK_ACTIVITY_COUNT = 41

KNN_DOMAIN_FILES = {
    "riasec": ("Career Interest Types.txt", "OI", RIASEC_ELEMENT_IDS),
    "sia": ("Specific Interest Areas.txt", "OI", None),  # discovered; must be 41
    "knowledge": ("Knowledge.txt", "IM", None),  # discovered; must be 33
    "essential_skills": ("Essential Skills.txt", "IM", ESSENTIAL_SKILL_IDS),
    "transferable_skills": ("Transferable Skills.txt", "IM", TRANSFERABLE_SKILL_IDS),
    "work_styles": ("Work Styles.txt", "WI", WORK_STYLE_IDS),
}

REQUIRED_RAW_FILES = (
    "Read Me.txt",
    "Occupation Data.txt",
    "Scales Reference.txt",
    "Career Interest Types.txt",
    "Specific Interest Areas.txt",
    "Knowledge.txt",
    "Essential Skills.txt",
    "Transferable Skills.txt",
    "Work Styles.txt",
    "Work Activities.txt",
    "Job Zones.txt",
    "Job Zone Reference.txt",
    "Education.txt",
    "Education Categories.txt",
    "Work Context.txt",
)

EXPECTED_HEADERS = {
    "Occupation Data.txt": ["O*NET-SOC Code", "Title", "Description"],
    "Scales Reference.txt": ["Scale ID", "Scale Name", "Minimum", "Maximum"],
    "Career Interest Types.txt": [
        "O*NET-SOC Code",
        "Element ID",
        "Element Name",
        "Scale ID",
        "Data Value",
        "Date",
        "Domain Source",
    ],
    "Job Zones.txt": ["O*NET-SOC Code", "Job Zone", "Date", "Domain Source"],
    "Job Zone Reference.txt": [
        "Job Zone",
        "Name",
        "Experience",
        "Education",
        "Job Training",
        "Examples",
        "SVP Range",
    ],
}

RATING_CORE_HEADERS = [
    "O*NET-SOC Code",
    "Element ID",
    "Element Name",
    "Scale ID",
    "Data Value",
]
