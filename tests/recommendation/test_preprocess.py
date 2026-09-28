from app.recommendation.onet_io import RatingRow
from app.recommendation.preprocess import effective_raw, minmax, occupations_with_all_elements


def test_minmax_uses_official_bounds() -> None:
    assert minmax(1.0, 1.0, 7.0) == 0.0
    assert minmax(7.0, 1.0, 7.0) == 1.0
    assert minmax(4.0, 1.0, 7.0) == 0.5
    assert minmax(-3.0, -3.0, 3.0) == 0.0
    assert minmax(3.0, -3.0, 3.0) == 1.0
    assert minmax(1.0, 1.0, 5.0) == 0.0
    assert minmax(5.0, 1.0, 5.0) == 1.0


def test_not_relevant_floors_to_scale_minimum() -> None:
    row = RatingRow(
        onetsoc_code="11-1011.00",
        element_id="2.C.x00",
        element_name="Test",
        scale_id="IM",
        raw_value=5.0,
        not_relevant=True,
        recommend_suppress=False,
    )
    assert effective_raw(row, 1.0) == 1.0


def test_recommend_suppress_drops_value() -> None:
    row = RatingRow(
        onetsoc_code="11-1011.00",
        element_id="2.A.1.a",
        element_name="Reading Comprehension",
        scale_id="IM",
        raw_value=5.0,
        not_relevant=False,
        recommend_suppress=True,
    )
    assert effective_raw(row, 1.0) is None


def test_suppress_wins_over_not_relevant() -> None:
    row = RatingRow(
        onetsoc_code="11-1011.00",
        element_id="2.C.x00",
        element_name="Test",
        scale_id="IM",
        raw_value=4.0,
        not_relevant=True,
        recommend_suppress=True,
    )
    assert effective_raw(row, 1.0) is None


def test_occupations_with_all_elements_requires_full_coverage() -> None:
    rows = [
        RatingRow("A", "e1", "E1", "IM", 2.0, False, False),
        RatingRow("A", "e2", "E2", "IM", 2.0, False, False),
        RatingRow("B", "e1", "E1", "IM", 2.0, False, False),
    ]
    assert occupations_with_all_elements(rows, ("e1", "e2")) == {"A"}
