from __future__ import annotations

import pytest

from app.recommendation.constants import (
    BLOCK_WEIGHTS,
    ESSENTIAL_SKILL_IDS,
    FEATURE_VERSION,
    RIASEC_ELEMENT_IDS,
    TRANSFERABLE_SKILL_IDS,
    WORK_STYLE_IDS,
)
from app.recommendation.exceptions import AssessmentError
from app.recommendation.student_features import (
    AcademicProfile,
    FeatureCatalog,
    StudentAssessment,
    WorkPreferences,
    build_student_vector,
)

MINI_SIA = ("1.B.3.q", "1.B.3.j", "1.B.3.y", "1.B.3.n", "1.B.3.r", "1.B.3.a")
MINI_KNOWLEDGE = ("2.C.3.a", "2.C.4.a", "2.C.6", "2.C.1.a", "2.C.4.b", "2.C.8.b")


def mini_catalog() -> FeatureCatalog:
    return FeatureCatalog(
        sia_ids=MINI_SIA,
        knowledge_ids=MINI_KNOWLEDGE,
        sia_names={"1.B.3.q": "Information Technology"},
        knowledge_names={"2.C.3.a": "Computers and Electronics"},
    )


def valid_assessment(**overrides) -> StudentAssessment:
    data = dict(
        riasec={element_id: 4 for element_id in RIASEC_ELEMENT_IDS},
        sia={"1.B.3.q": 7, "1.B.3.j": 6},
        essential_skills={element_id: 3 for element_id in ESSENTIAL_SKILL_IDS},
        transferable_skills={element_id: 3 for element_id in TRANSFERABLE_SKILL_IDS},
        work_styles={element_id: 3 for element_id in WORK_STYLE_IDS},
        knowledge={"2.C.3.a": 5, "2.C.4.a": 4},
        profile=AcademicProfile(further_study="maybe", course_relatedness="open"),
        preferences=WorkPreferences(pref_indoor=4, pref_outdoor=2, pref_team=4, pref_public=3),
    )
    data.update(overrides)
    return StudentAssessment(**data)


def test_normal_vector_uses_official_transforms_and_excludes_unselected() -> None:
    vector = build_student_vector(valid_assessment(), mini_catalog())
    assert vector.feature_version == FEATURE_VERSION
    assert tuple(vector.blocks) == (
        "riasec",
        "sia",
        "essential_skills",
        "transferable_skills",
        "work_styles",
        "knowledge",
    )
    assert vector.blocks["riasec"].values[0] == pytest.approx((4 - 1) / 6)
    assert vector.blocks["essential_skills"].values[0] == pytest.approx((3 - 1) / 4)
    assert vector.blocks["work_styles"].values[0] == pytest.approx((3 - 1) / 4)
    assert vector.blocks["sia"].element_ids == ("1.B.3.q", "1.B.3.j")
    assert "1.B.3.y" not in vector.blocks["sia"].element_ids
    assert vector.blocks["sia"].values[0] == pytest.approx(1.0)
    assert vector.blocks["knowledge"].element_ids == ("2.C.3.a", "2.C.4.a")
    assert vector.blocks["riasec"].weight == BLOCK_WEIGHTS["riasec"]
    assert vector.profile.further_study == "maybe"
    assert "faculty" not in vector.knn_blocks()


def test_internal_names_are_resolved_to_element_ids() -> None:
    assessment = valid_assessment(
        riasec={
            "interest_realistic": 1,
            "interest_investigative": 7,
            "interest_artistic": 1,
            "interest_social": 1,
            "interest_enterprising": 1,
            "interest_conventional": 1,
        }
    )
    vector = build_student_vector(assessment, mini_catalog())
    assert vector.blocks["riasec"].element_ids[1] == "1.B.1.b"
    assert vector.blocks["riasec"].values[1] == pytest.approx(1.0)
    assert vector.blocks["riasec"].values[0] == pytest.approx(0.0)


def test_boundary_values() -> None:
    assessment = valid_assessment(
        riasec={element_id: 1 for element_id in RIASEC_ELEMENT_IDS} | {"1.B.1.b": 7},
        essential_skills={element_id: 1 for element_id in ESSENTIAL_SKILL_IDS} | {"2.A.1.a": 5},
        work_styles={element_id: 1 for element_id in WORK_STYLE_IDS} | {"1.D.1.a": 5},
        sia={"1.B.3.q": 1},
        knowledge={"2.C.3.a": 5},
    )
    vector = build_student_vector(assessment, mini_catalog())
    assert vector.blocks["riasec"].values[0] == 0.0
    assert vector.blocks["riasec"].values[1] == 1.0
    assert vector.blocks["essential_skills"].values[0] == 1.0
    assert vector.blocks["work_styles"].values[0] == 1.0
    assert vector.blocks["sia"].values[0] == 0.0
    assert vector.blocks["knowledge"].values[0] == 1.0


@pytest.mark.parametrize("bad", [0, 8, 4.5, None])
def test_invalid_riasec_values(bad) -> None:
    with pytest.raises(AssessmentError):
        build_student_vector(
            valid_assessment(riasec={element_id: 4 for element_id in RIASEC_ELEMENT_IDS} | {"1.B.1.a": bad}),
            mini_catalog(),
        )


def test_missing_essential_skill() -> None:
    skills = {element_id: 3 for element_id in ESSENTIAL_SKILL_IDS}
    del skills["2.A.1.a"]
    with pytest.raises(AssessmentError, match="missing required"):
        build_student_vector(valid_assessment(essential_skills=skills), mini_catalog())


def test_empty_sia_is_invalid() -> None:
    with pytest.raises(AssessmentError, match="at least 1"):
        build_student_vector(valid_assessment(sia={}), mini_catalog())


def test_too_many_knowledge_selections() -> None:
    knowledge = {element_id: 4 for element_id in MINI_KNOWLEDGE}
    with pytest.raises(AssessmentError, match="at most 5"):
        build_student_vector(valid_assessment(knowledge=knowledge), mini_catalog())


def test_unknown_sia_id() -> None:
    with pytest.raises(AssessmentError, match="Unknown sia"):
        build_student_vector(valid_assessment(sia={"9.Z.9": 4}), mini_catalog())


def test_partial_sia_does_not_zero_fill() -> None:
    vector = build_student_vector(valid_assessment(sia={"1.B.3.q": 5}), mini_catalog())
    assert vector.blocks["sia"].element_ids == ("1.B.3.q",)
    assert len(vector.blocks["sia"].values) == 1
    assert set(MINI_SIA) - set(vector.blocks["sia"].element_ids)


def test_invalid_profile_and_preferences() -> None:
    with pytest.raises(AssessmentError, match="further_study"):
        build_student_vector(
            valid_assessment(profile=AcademicProfile(further_study="later")),
            mini_catalog(),
        )
    with pytest.raises(AssessmentError, match="pref_outdoor"):
        build_student_vector(
            valid_assessment(preferences=WorkPreferences(pref_outdoor=9, pref_indoor=3, pref_team=3, pref_public=3)),
            mini_catalog(),
        )


def test_catalog_from_metadata_roundtrip() -> None:
    catalog = FeatureCatalog.from_metadata(
        {
            "feature_version": FEATURE_VERSION,
            "blocks": {
                "sia": {"element_ids": list(MINI_SIA), "element_names": {}},
                "knowledge": {"element_ids": list(MINI_KNOWLEDGE), "element_names": {}},
            },
            "scales": {"OI": {"minimum": 1, "maximum": 7}, "IM": {"minimum": 1, "maximum": 5}},
        }
    )
    vector = build_student_vector(valid_assessment(), catalog)
    assert vector.feature_version == FEATURE_VERSION
