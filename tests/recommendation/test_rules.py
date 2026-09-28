from __future__ import annotations

from app.recommendation.constants import CONTEXT_OUTDOOR, CONTEXT_PUBLIC, RIASEC_ELEMENT_IDS
from app.recommendation.rules import (
    RuleConfig,
    apply_exclude_rules,
    apply_score_rules,
    apply_suppress_rules,
    filter_eligible,
)
from app.recommendation.student_features import AcademicProfile, WorkPreferences, build_student_vector
from tests.recommendation.fakes import make_index, make_occupation
from tests.recommendation.test_student_features import MINI_KNOWLEDGE, valid_assessment


def _student(**overrides):
    catalog = make_index([]).catalog
    return build_student_vector(valid_assessment(**overrides), catalog)


def test_r_data_excludes_incomplete_occupation() -> None:
    incomplete = make_occupation("99-0001.00", "Incomplete", zone=4, knn_complete=False)
    incomplete.normalized["knowledge"] = {}
    index = make_index([incomplete])
    student = _student()
    firings = apply_exclude_rules(incomplete, student, RuleConfig(), index)
    assert any(item.code == "R-DATA" and item.action == "exclude" for item in firings)


def test_r_data_negative_complete_occupation() -> None:
    complete = make_occupation("99-0002.00", "Complete", zone=4, knn_complete=True)
    index = make_index([complete])
    firings = apply_exclude_rules(complete, _student(), RuleConfig(), index)
    assert all(item.code != "R-DATA" for item in firings)


def test_r_zone_low_excludes_zone_2_but_not_zone_4() -> None:
    low = make_occupation("99-0003.00", "Helper", zone=2)
    high = make_occupation("99-0004.00", "Analyst", zone=4)
    index = make_index([low, high])
    student = _student()
    assert any(item.code == "R-ZONE-LOW" for item in apply_exclude_rules(low, student, RuleConfig(), index))
    assert all(item.code != "R-ZONE-LOW" for item in apply_exclude_rules(high, student, RuleConfig(), index))
    eligible, firings = filter_eligible(index, student, RuleConfig())
    assert eligible == ["99-0004.00"]
    assert any(item.code == "R-ZONE-LOW" for item in firings)


def test_r_zone_low_can_be_disabled() -> None:
    low = make_occupation("99-0003.00", "Helper", zone=2)
    index = make_index([low])
    config = RuleConfig(enabled={**{code: True for code in ["R-DATA", "R-ZONE-LOW"]}, "R-ZONE-LOW": False})
    eligible, _ = filter_eligible(index, _student(), config)
    assert "99-0003.00" in eligible


def test_r_suppress_drop_and_floor() -> None:
    occ = make_occupation(
        "99-0005.00",
        "Suppressed",
        zone=4,
        suppressed={("essential_skills", "2.A.1.a")},
        not_relevant={("knowledge", "2.C.3.a")},
    )
    student = _student()
    firings = apply_suppress_rules(occ, student, RuleConfig())
    actions = {(item.action, item.element_id) for item in firings}
    assert ("drop", "2.A.1.a") in actions
    assert ("floor", "2.C.3.a") in actions
    negative = make_occupation("99-0006.00", "Clean", zone=4)
    assert apply_suppress_rules(negative, student, RuleConfig()) == []


def test_r_zone_5_flags_when_further_study_is_no() -> None:
    occ = make_occupation("99-0007.00", "Surgeon", zone=5)
    index = make_index([occ])
    flagged = apply_score_rules(
        occ,
        _student(profile=AcademicProfile(further_study="no")),
        RuleConfig(),
        index,
    )
    assert any(item.code == "R-ZONE-5" and item.action == "flag" for item in flagged)
    not_flagged = apply_score_rules(
        occ,
        _student(profile=AcademicProfile(further_study="yes")),
        RuleConfig(),
        index,
    )
    assert all(item.code != "R-ZONE-5" for item in not_flagged)
    eligible, _ = filter_eligible(index, _student(profile=AcademicProfile(further_study="no")))
    assert "99-0007.00" in eligible


def test_r_related_penalises_only_with_configured_priors() -> None:
    occ = make_occupation(
        "99-0008.00",
        "Unrelated",
        zone=4,
        knowledge_used={element_id: 1.5 for element_id in MINI_KNOWLEDGE},
    )
    index = make_index([occ])
    student = _student(
        profile=AcademicProfile(
            faculty="Natural and Applied Sciences",
            course_relatedness="related",
            further_study="maybe",
        )
    )
    empty = apply_score_rules(occ, student, RuleConfig(), index)
    assert all(item.code != "R-RELATED" for item in empty)

    config = RuleConfig(faculty_knowledge_priors={"Natural and Applied Sciences": ("2.C.3.a", "2.C.4.a")})
    penalised = apply_score_rules(occ, student, config, index)
    assert any(item.code == "R-RELATED" and item.penalty == 0.80 for item in penalised)

    open_student = _student(
        profile=AcademicProfile(
            faculty="Natural and Applied Sciences",
            course_relatedness="open",
            further_study="maybe",
        )
    )
    assert all(item.code != "R-RELATED" for item in apply_score_rules(occ, open_student, config, index))


def test_r_context_outdoor_public_team_and_no_double_outdoor() -> None:
    outdoor = make_occupation("99-0009.00", "Field", zone=4, indoor=2.0, outdoor=4.5, public=4.2, team=4.7)
    indoor = make_occupation("99-0010.00", "Office", zone=4, indoor=4.8, outdoor=1.2, public=1.5, team=3.0)
    index = make_index([outdoor, indoor])
    student = _student(
        preferences=WorkPreferences(pref_indoor=5, pref_outdoor=1, pref_team=1, pref_public=1)
    )
    outdoor_firings = apply_score_rules(outdoor, student, RuleConfig(), index)
    context = [item for item in outdoor_firings if item.code == "R-CONTEXT"]
    outdoor_penalties = [item for item in context if item.element_id == CONTEXT_OUTDOOR]
    assert len(outdoor_penalties) == 1
    assert any(item.element_id == CONTEXT_PUBLIC and item.penalty == 0.90 for item in context)
    indoor_firings = apply_score_rules(indoor, student, RuleConfig(), index)
    assert all(item.code != "R-CONTEXT" for item in indoor_firings)


def test_r_edu_flags_modal_doctoral_and_skips_missing_education() -> None:
    doctoral = make_occupation(
        "99-0011.00",
        "Scientist",
        zone=4,
        education={"6": 10.0, "11": 70.0, "8": 20.0},
    )
    missing = make_occupation("99-0012.00", "No Edu", zone=4, education={})
    index = make_index([doctoral, missing])
    student = _student(profile=AcademicProfile(further_study="no"))
    assert any(item.code == "R-EDU" and item.action == "flag" for item in apply_score_rules(doctoral, student, RuleConfig(), index))
    assert all(item.code != "R-EDU" for item in apply_score_rules(missing, student, RuleConfig(), index))
    yes = _student(profile=AcademicProfile(further_study="yes"))
    assert all(item.code != "R-EDU" for item in apply_score_rules(doctoral, yes, RuleConfig(), index))
