"""Turn official O*NET ratings into Version 1 occupational features."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.recommendation.constants import DEFAULT_JOB_ZONES
from app.recommendation.onet_io import RatingRow


def minmax(value: float, minimum: float, maximum: float) -> float:
    if maximum == minimum:
        raise ValueError("Scale minimum and maximum must differ")
    scaled = (value - minimum) / (maximum - minimum)
    if scaled < 0:
        return 0.0
    if scaled > 1:
        return 1.0
    return scaled


def effective_raw(row: RatingRow, scale_minimum: float) -> float | None:
    """Apply O*NET flags. Suppress drops the value; Not Relevant floors to scale min."""
    if row.recommend_suppress:
        return None
    if row.not_relevant:
        return scale_minimum
    return row.raw_value


@dataclass
class ProcessedRating:
    onetsoc_code: str
    domain: str
    element_id: str
    element_name: str
    scale_id: str
    raw_value: float
    used_value: float | None
    normalized_value: float | None
    not_relevant: bool
    recommend_suppress: bool
    include_in_knn: bool
    category: str | None = None


def process_ratings(
    rows: list[RatingRow],
    *,
    domain: str,
    scale_id: str,
    scales: dict[str, tuple[float, float]],
    include_in_knn: bool,
) -> list[ProcessedRating]:
    minimum, maximum = scales[scale_id]
    processed: list[ProcessedRating] = []
    for row in rows:
        used = effective_raw(row, minimum)
        normalized = None if used is None else minmax(used, minimum, maximum)
        processed.append(
            ProcessedRating(
                onetsoc_code=row.onetsoc_code,
                domain=domain,
                element_id=row.element_id,
                element_name=row.element_name,
                scale_id=scale_id,
                raw_value=row.raw_value,
                used_value=used,
                normalized_value=normalized,
                not_relevant=row.not_relevant,
                recommend_suppress=row.recommend_suppress,
                include_in_knn=include_in_knn and used is not None,
                category=row.category,
            )
        )
    return processed


def occupations_with_all_elements(
    rows: list[RatingRow],
    element_ids: tuple[str, ...],
) -> set[str]:
    required = set(element_ids)
    by_occupation: dict[str, set[str]] = {}
    for row in rows:
        by_occupation.setdefault(row.onetsoc_code, set()).add(row.element_id)
    return {code for code, found in by_occupation.items() if required <= found}


@dataclass
class OccupationRecord:
    onetsoc_code: str
    title: str
    description: str
    job_zone: int | None
    knn_complete: bool
    recommendable: bool
    has_education: bool = False
    has_work_context: bool = False


def build_occupation_records(
    occupation_data: dict[str, dict[str, str]],
    job_zones: dict[str, int],
    knn_complete: set[str],
    education_codes: set[str],
    work_context_codes: set[str],
) -> list[OccupationRecord]:
    records: list[OccupationRecord] = []
    for code in sorted(occupation_data):
        zone = job_zones.get(code)
        complete = code in knn_complete
        recommendable = complete and zone in DEFAULT_JOB_ZONES
        info = occupation_data[code]
        records.append(
            OccupationRecord(
                onetsoc_code=code,
                title=info["title"],
                description=info["description"],
                job_zone=zone,
                knn_complete=complete,
                recommendable=recommendable,
                has_education=code in education_codes,
                has_work_context=code in work_context_codes,
            )
        )
    return records


def pivot_normalized(
    ratings: list[ProcessedRating],
    codes: list[str],
    element_ids: tuple[str, ...],
) -> dict[str, dict[str, float | None]]:
    lookup: dict[tuple[str, str], float | None] = {}
    for row in ratings:
        lookup[(row.onetsoc_code, row.element_id)] = row.normalized_value
    matrix: dict[str, dict[str, float | None]] = {}
    for code in codes:
        matrix[code] = {element_id: lookup.get((code, element_id)) for element_id in element_ids}
    return matrix
