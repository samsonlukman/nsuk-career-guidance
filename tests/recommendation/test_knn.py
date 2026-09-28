from __future__ import annotations

import pytest

from app.recommendation.constants import ESSENTIAL_SKILL_IDS, KNN_BLOCKS, RIASEC_ELEMENT_IDS
from app.recommendation.exceptions import AssessmentError
from app.recommendation.knn import knn_neighbors, pack_occupation, pack_student, weighted_block_similarity
from app.recommendation.rules import filter_eligible
from app.recommendation.student_features import build_student_vector
from tests.recommendation.fakes import make_index, make_occupation
from tests.recommendation.test_student_features import valid_assessment


def _student(**overrides):
    return build_student_vector(valid_assessment(**overrides), make_index([]).catalog)


def test_vector_dimensions_match_selected_blocks() -> None:
    student = _student(sia={"1.B.3.q": 7}, knowledge={"2.C.3.a": 5})
    packed = pack_student(student)
    expected = 6 + 1 + 10 + 6 + 6 + 1
    assert packed.shape == (expected,)
    occ = make_occupation("15-0000.00", "Match", zone=4)
    assert pack_occupation(occ, student).shape == packed.shape
    assert packed.shape[0] == sum(len(student.blocks[name].element_ids) for name in KNN_BLOCKS)


def test_identical_profiles_have_similarity_one() -> None:
    student = _student()
    occ = make_occupation(
        "15-0001.00",
        "Clone",
        zone=4,
        riasec=student.blocks["riasec"].as_dict(),
        sia=student.blocks["sia"].as_dict(),
        knowledge=student.blocks["knowledge"].as_dict(),
        essential=student.blocks["essential_skills"].values[0],
        transferable=student.blocks["transferable_skills"].values[0],
        styles=student.blocks["work_styles"].values[0],
    )
    index = make_index([occ])
    neighbors = knn_neighbors(student, index, ["15-0001.00"], k=5)
    assert len(neighbors) == 1
    assert neighbors[0].raw_similarity == pytest.approx(1.0, abs=1e-6)
    assert neighbors[0].distance == pytest.approx(0.0, abs=1e-6)


def test_ranking_prefers_matching_interest_profile() -> None:
    student = _student(
        riasec={element_id: 1 for element_id in RIASEC_ELEMENT_IDS} | {"1.B.1.b": 7}
    )
    investigative = make_occupation(
        "15-0002.00",
        "Scientist",
        zone=4,
        riasec={element_id: 0.0 for element_id in RIASEC_ELEMENT_IDS} | {"1.B.1.b": 1.0},
        sia=student.blocks["sia"].as_dict(),
        knowledge=student.blocks["knowledge"].as_dict(),
    )
    realistic = make_occupation(
        "15-0003.00",
        "Builder",
        zone=4,
        riasec={element_id: 0.0 for element_id in RIASEC_ELEMENT_IDS} | {"1.B.1.a": 1.0},
        sia=student.blocks["sia"].as_dict(),
        knowledge=student.blocks["knowledge"].as_dict(),
    )
    index = make_index([realistic, investigative])
    neighbors = knn_neighbors(student, index, ["15-0003.00", "15-0002.00"], k=5)
    assert neighbors[0].onetsoc_code == "15-0002.00"
    assert neighbors[0].raw_similarity > neighbors[1].raw_similarity


def test_k_is_capped_and_validated() -> None:
    occupations = [make_occupation(f"15-000{i}.00", f"Job {i}", zone=4) for i in range(3)]
    index = make_index(occupations)
    student = _student()
    codes = [item.onetsoc_code for item in occupations]
    assert len(knn_neighbors(student, index, codes, k=5)) == 3
    with pytest.raises(AssessmentError, match="k must be"):
        knn_neighbors(student, index, codes, k=7)


def test_empty_eligible_returns_no_neighbors() -> None:
    index = make_index([make_occupation("15-0099.00", "X", zone=4)])
    assert knn_neighbors(_student(), index, [], k=10) == []


def test_invalid_all_missing_occupation_block_is_skipped() -> None:
    student = _student()
    query = pack_student(student)
    occ = pack_occupation(make_occupation("15-0088.00", "X", zone=4), student)
    slices = []
    cursor = 0
    weights = []
    from app.recommendation.constants import BLOCK_WEIGHTS, KNN_BLOCKS

    for name in KNN_BLOCKS:
        length = len(student.blocks[name].element_ids)
        slices.append((cursor, cursor + length))
        weights.append(BLOCK_WEIGHTS[name])
        cursor += length
    similarity, blocks = weighted_block_similarity(query, occ, slices, weights)
    assert 0.0 <= similarity <= 1.0
    assert "riasec" in blocks


def test_results_are_deterministic() -> None:
    occupations = [
        make_occupation("15-0010.00", "A", zone=4, riasec={eid: 0.7 for eid in RIASEC_ELEMENT_IDS}),
        make_occupation("15-0011.00", "B", zone=4, riasec={eid: 0.2 for eid in RIASEC_ELEMENT_IDS}),
        make_occupation("15-0012.00", "C", zone=4, riasec={eid: 0.5 for eid in RIASEC_ELEMENT_IDS}),
    ]
    index = make_index(occupations)
    student = _student()
    codes = [item.onetsoc_code for item in occupations]
    first = [item.onetsoc_code for item in knn_neighbors(student, index, codes, k=5)]
    second = [item.onetsoc_code for item in knn_neighbors(student, index, codes, k=5)]
    assert first == second


def test_excluded_zone_2_not_passed_to_knn() -> None:
    zone2 = make_occupation("35-0000.00", "Helper", zone=2)
    zone4 = make_occupation("15-0020.00", "Analyst", zone=4)
    index = make_index([zone2, zone4])
    student = _student()
    eligible, _ = filter_eligible(index, student)
    assert "35-0000.00" not in eligible
    neighbors = knn_neighbors(student, index, eligible, k=5)
    assert [item.onetsoc_code for item in neighbors] == ["15-0020.00"]


def test_partial_sia_changes_packed_width() -> None:
    one = pack_student(_student(sia={"1.B.3.q": 6}))
    two = pack_student(_student(sia={"1.B.3.q": 6, "1.B.3.j": 5}))
    assert two.shape[0] - one.shape[0] == 1


def test_suppressed_element_is_dropped_from_pairwise_block() -> None:
    student = _student()
    occ = make_occupation(
        "15-0030.00",
        "Suppressed",
        zone=4,
        suppressed={("essential_skills", ESSENTIAL_SKILL_IDS[0])},
    )
    packed = pack_occupation(occ, student)
    essential_start = 6 + len(student.blocks["sia"].element_ids)
    assert packed[essential_start] == pytest.approx(-1.0)
