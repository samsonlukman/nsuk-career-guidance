from __future__ import annotations

from pathlib import Path

import pytest

from app.recommendation.catalog import load_occupation_index
from app.recommendation.constants import (
    ESSENTIAL_SKILL_IDS,
    FEATURE_VERSION,
    RIASEC_ELEMENT_IDS,
    TRANSFERABLE_SKILL_IDS,
    WORK_STYLE_IDS,
)
from app.recommendation.pipeline import recommend
from app.recommendation.rules import RuleConfig
from app.recommendation.student_features import AcademicProfile, StudentAssessment, WorkPreferences
from tests.recommendation.fakes import make_index, make_occupation
from tests.recommendation.test_student_features import valid_assessment

PROCESSED = Path("/Users/apple/finalproject/data/processed/onet_30_3_v1")


def fixture_index():
    investigative = {eid: 0.1 for eid in RIASEC_ELEMENT_IDS}
    investigative["1.B.1.b"] = 1.0
    realistic = {eid: 0.1 for eid in RIASEC_ELEMENT_IDS}
    realistic["1.B.1.a"] = 1.0
    return make_index(
        [
            make_occupation(
                "15-1252.00",
                "Software Developers",
                zone=4,
                riasec=investigative,
                sia={"1.B.3.q": 1.0, "1.B.3.j": 0.8},
                knowledge={"2.C.3.a": 1.0, "2.C.4.a": 0.8},
                transferable=0.9,
                activities=[
                    ("4.A.3.b.1", "Working with Computers", 4.8),
                    ("4.A.2.a.4", "Analyzing Data or Information", 4.6),
                ],
            ),
            make_occupation(
                "47-2031.00",
                "Carpenters",
                zone=2,
                riasec=realistic,
                sia={"1.B.3.q": 0.1},
            ),
            make_occupation(
                "29-1229.00",
                "Physicians, All Other",
                zone=5,
                riasec=investigative,
                sia={"1.B.3.q": 0.2, "1.B.3.j": 0.3},
                knowledge={"2.C.3.a": 0.2, "2.C.4.a": 0.2},
                education={"11": 80.0, "6": 10.0},
            ),
            make_occupation(
                "19-1029.00",
                "Biological Scientists",
                zone=4,
                riasec=investigative,
                sia={"1.B.3.q": 0.3, "1.B.3.j": 0.4},
                knowledge={"2.C.3.a": 0.2, "2.C.4.a": 0.3},
                knowledge_used={
                    eid: 1.2
                    for eid in ("2.C.3.a", "2.C.4.a", "2.C.6", "2.C.1.a", "2.C.4.b", "2.C.8.b")
                },
            ),
            make_occupation("99-9999.00", "Incomplete Job", zone=4, knn_complete=False),
        ]
    )


def investigative_it_assessment(**profile_overrides) -> StudentAssessment:
    profile = dict(
        faculty="Natural and Applied Sciences",
        further_study="no",
        course_relatedness="related",
    )
    profile.update(profile_overrides)
    return valid_assessment(
        riasec={eid: 2 for eid in RIASEC_ELEMENT_IDS} | {"1.B.1.b": 7},
        sia={"1.B.3.q": 7, "1.B.3.j": 6},
        transferable_skills={eid: 3 for eid in TRANSFERABLE_SKILL_IDS} | {"2.B.3.e": 5},
        knowledge={"2.C.3.a": 5, "2.C.4.a": 4},
        profile=AcademicProfile(**profile),
        preferences=WorkPreferences(pref_indoor=5, pref_outdoor=1, pref_team=3, pref_public=3),
    )


def test_pipeline_excludes_zone_2_and_incomplete_and_flags_zone_5() -> None:
    result = recommend(investigative_it_assessment(), fixture_index(), k=5)
    codes = [item.onetsoc_code for item in result.items]
    assert "47-2031.00" not in codes
    assert "99-9999.00" not in codes
    assert result.eligible_count == 3
    physicians = next(item for item in result.items if item.onetsoc_code == "29-1229.00")
    assert physicians.job_zone == 5
    assert any(firing.code == "R-ZONE-5" and firing.action == "flag" for firing in physicians.firings)
    assert any(firing.code == "R-EDU" for firing in physicians.firings)


def test_pipeline_ranks_software_above_unrelated_and_explains() -> None:
    config = RuleConfig(
        faculty_knowledge_priors={"Natural and Applied Sciences": ("2.C.3.a", "2.C.4.a")}
    )
    result = recommend(investigative_it_assessment(), fixture_index(), k=5, rule_config=config)
    assert result.items[0].onetsoc_code == "15-1252.00"
    top = result.items[0]
    assert top.explanation.contributions
    assert any(item.element_id == "1.B.1.b" for item in top.explanation.contributions)
    assert "Working with Computers" in top.explanation.work_activities
    assert top.explanation.job_zone_note
    assert "similarity" in top.explanation.summary.lower()
    biologists = next(item for item in result.items if item.onetsoc_code == "19-1029.00")
    assert any(firing.code == "R-RELATED" for firing in biologists.firings)
    assert biologists.recommendation_score < biologists.raw_similarity


def test_pipeline_ranking_is_deterministic() -> None:
    index = fixture_index()
    assessment = investigative_it_assessment()
    first = [item.onetsoc_code for item in recommend(assessment, index, k=5).items]
    second = [item.onetsoc_code for item in recommend(assessment, index, k=5).items]
    assert first == second
    scores = [item.recommendation_score for item in recommend(assessment, index, k=5).items]
    assert scores == sorted(scores, reverse=True)


def test_pipeline_soc_code_tie_break() -> None:
    student_like = {eid: 0.5 for eid in RIASEC_ELEMENT_IDS}
    a = make_occupation("19-0002.00", "Second", zone=4, riasec=student_like)
    b = make_occupation("19-0001.00", "First", zone=4, riasec=student_like)
    index = make_index([a, b])
    result = recommend(valid_assessment(), index, k=5)
    assert [item.onetsoc_code for item in result.items] == ["19-0001.00", "19-0002.00"]


@pytest.mark.skipif(not (PROCESSED / "metadata.json").is_file(), reason="processed O*NET snapshot missing")
def test_real_snapshot_k10_excludes_zone_2_and_is_deterministic() -> None:
    index = load_occupation_index(PROCESSED)
    catalog = index.catalog
    sia_id = "1.B.3.q" if "1.B.3.q" in catalog.sia_ids else catalog.sia_ids[0]
    knowledge_id = "2.C.3.a" if "2.C.3.a" in catalog.knowledge_ids else catalog.knowledge_ids[0]
    assessment = StudentAssessment(
        riasec={eid: 3 for eid in RIASEC_ELEMENT_IDS} | {"1.B.1.b": 7},
        sia={sia_id: 7},
        essential_skills={eid: 4 for eid in ESSENTIAL_SKILL_IDS},
        transferable_skills={eid: 3 for eid in TRANSFERABLE_SKILL_IDS} | {"2.B.3.e": 5},
        work_styles={eid: 4 for eid in WORK_STYLE_IDS},
        knowledge={knowledge_id: 5},
        profile=AcademicProfile(further_study="maybe", course_relatedness="open"),
        preferences=WorkPreferences(pref_indoor=4, pref_outdoor=3, pref_team=4, pref_public=3),
    )
    first = recommend(assessment, index, k=10)
    second = recommend(assessment, index, k=10)
    assert first.feature_version == FEATURE_VERSION
    assert len(first.items) == 10
    assert all(item.job_zone in {3, 4, 5} for item in first.items)
    assert [item.onetsoc_code for item in first.items] == [item.onetsoc_code for item in second.items]
    assert all(item.explanation.summary for item in first.items)
    assert "not predicted" in first.notes[0].lower()
