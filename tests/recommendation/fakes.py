"""In-memory occupations for unit and integration tests. Not real student data."""

from __future__ import annotations

from app.recommendation.catalog import IndexedOccupation, OccupationIndex
from app.recommendation.constants import (
    CONTEXT_INDOOR,
    CONTEXT_OUTDOOR,
    CONTEXT_PUBLIC,
    CONTEXT_TEAM,
    ESSENTIAL_SKILL_IDS,
    FEATURE_VERSION,
    RIASEC_ELEMENT_IDS,
    TRANSFERABLE_SKILL_IDS,
    WORK_STYLE_IDS,
)
from app.recommendation.preprocess import OccupationRecord
from app.recommendation.student_features import FeatureCatalog
from tests.recommendation.test_student_features import MINI_KNOWLEDGE, MINI_SIA, mini_catalog


def _filled(ids: tuple[str, ...], value: float) -> dict[str, float]:
    return {element_id: value for element_id in ids}


def make_occupation(
    code: str,
    title: str,
    *,
    zone: int | None,
    knn_complete: bool = True,
    riasec: dict[str, float] | None = None,
    sia: dict[str, float] | None = None,
    essential: float = 0.5,
    transferable: float = 0.5,
    styles: float = 0.5,
    knowledge: dict[str, float] | None = None,
    knowledge_used: dict[str, float] | None = None,
    suppressed: set[tuple[str, str]] | None = None,
    not_relevant: set[tuple[str, str]] | None = None,
    indoor: float = 4.5,
    outdoor: float = 1.5,
    team: float = 3.5,
    public: float = 2.0,
    education: dict[str, float] | None = None,
    activities: list[tuple[str, str, float]] | None = None,
    description: str = "Test occupation",
) -> IndexedOccupation:
    recommendable = knn_complete and zone in {3, 4, 5}
    record = OccupationRecord(
        onetsoc_code=code,
        title=title,
        description=description,
        job_zone=zone,
        knn_complete=knn_complete,
        recommendable=recommendable,
        has_education=bool(education),
        has_work_context=True,
    )
    riasec_norm = riasec or _filled(RIASEC_ELEMENT_IDS, 0.5)
    sia_norm = sia or _filled(MINI_SIA, 0.2)
    knowledge_norm = knowledge or _filled(MINI_KNOWLEDGE, 0.2)
    essential_norm = _filled(ESSENTIAL_SKILL_IDS, essential)
    transferable_norm = _filled(TRANSFERABLE_SKILL_IDS, transferable)
    style_norm = _filled(WORK_STYLE_IDS, styles)
    used = {
        "riasec": {key: 1 + 6 * value for key, value in riasec_norm.items()},
        "sia": {key: 1 + 6 * value for key, value in sia_norm.items()},
        "essential_skills": {key: 1 + 4 * value for key, value in essential_norm.items()},
        "transferable_skills": {key: 1 + 4 * value for key, value in transferable_norm.items()},
        "work_styles": {key: -3 + 6 * value for key, value in style_norm.items()},
        "knowledge": knowledge_used
        or {key: 1 + 4 * value for key, value in knowledge_norm.items()},
    }
    return IndexedOccupation(
        record=record,
        normalized={
            "riasec": riasec_norm,
            "sia": sia_norm,
            "essential_skills": essential_norm,
            "transferable_skills": transferable_norm,
            "work_styles": style_norm,
            "knowledge": knowledge_norm,
        },
        used_values=used,
        suppressed=suppressed or set(),
        not_relevant=not_relevant or set(),
        work_context_cx={
            CONTEXT_INDOOR: indoor,
            CONTEXT_OUTDOOR: outdoor,
            CONTEXT_TEAM: team,
            CONTEXT_PUBLIC: public,
        },
        education_percents=education or {},
        work_activities=activities
        or [("4.A.2.a.4", "Analyzing Data or Information", 4.5)],
    )


def make_index(occupations: list[IndexedOccupation], catalog: FeatureCatalog | None = None) -> OccupationIndex:
    catalog = catalog or mini_catalog()
    return OccupationIndex(
        feature_version=FEATURE_VERSION,
        catalog=catalog,
        occupations={item.onetsoc_code: item for item in occupations},
        job_zone_reference={
            2: {"Job Zone": "2", "Name": "Job Zone 1-2", "Education": "Usually requires a high school diploma or GED."},
            4: {"Job Zone": "4", "Name": "Job Zone Four", "Education": "Most of these occupations require a four-year bachelor's degree."},
            5: {
                "Job Zone": "5",
                "Name": "Job Zone Five",
                "Education": "Most of these occupations require graduate school.",
            },
        },
        element_names={
            "1.B.1.b": "Investigative",
            "1.B.3.q": "Information Technology",
            "2.C.3.a": "Computers and Electronics",
            "2.A.1.a": "Reading Comprehension",
            "2.B.3.e": "Programming",
        },
    )
