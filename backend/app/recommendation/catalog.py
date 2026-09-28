"""Load the processed O*NET snapshot into an in-memory occupation index."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

from app.recommendation.constants import FEATURE_VERSION, KNN_BLOCKS
from app.recommendation.preprocess import OccupationRecord
from app.recommendation.student_features import FeatureCatalog


def _parse_optional_float(value: str) -> float | None:
    text = (value or "").strip()
    if text == "":
        return None
    return float(text)


def _parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


@dataclass
class IndexedOccupation:
    record: OccupationRecord
    normalized: dict[str, dict[str, float | None]]
    used_values: dict[str, dict[str, float | None]]
    suppressed: set[tuple[str, str]]
    not_relevant: set[tuple[str, str]]
    work_context_cx: dict[str, float]
    education_percents: dict[str, float]
    work_activities: list[tuple[str, str, float]]
    element_names: dict[str, str] = field(default_factory=dict)

    @property
    def onetsoc_code(self) -> str:
        return self.record.onetsoc_code


@dataclass
class OccupationIndex:
    feature_version: str
    catalog: FeatureCatalog
    occupations: dict[str, IndexedOccupation]
    job_zone_reference: dict[int, dict[str, str]]
    element_names: dict[str, str]

    def get(self, code: str) -> IndexedOccupation:
        return self.occupations[code]

    def knn_complete_codes(self) -> list[str]:
        return [
            code
            for code, item in self.occupations.items()
            if item.record.knn_complete
        ]


def load_occupation_index(processed_dir: Path) -> OccupationIndex:
    processed_dir = processed_dir.resolve()
    metadata = json.loads((processed_dir / "metadata.json").read_text(encoding="utf-8"))
    if metadata.get("feature_version") != FEATURE_VERSION:
        raise ValueError(
            f"Processed snapshot is {metadata.get('feature_version')}, expected {FEATURE_VERSION}"
        )
    catalog = FeatureCatalog.from_metadata(metadata)
    element_names: dict[str, str] = {}
    for spec in metadata.get("blocks", {}).values():
        element_names.update(spec.get("element_names") or {})

    records: dict[str, OccupationRecord] = {}
    with (processed_dir / "occupations.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            zone = row["job_zone"].strip()
            records[row["onetsoc_code"]] = OccupationRecord(
                onetsoc_code=row["onetsoc_code"],
                title=row["title"],
                description=row["description"],
                job_zone=None if zone == "" else int(zone),
                knn_complete=_parse_bool(row["knn_complete"]),
                recommendable=_parse_bool(row["recommendable"]),
                has_education=_parse_bool(row["has_education"]),
                has_work_context=_parse_bool(row["has_work_context"]),
            )

    occupations: dict[str, IndexedOccupation] = {
        code: IndexedOccupation(
            record=record,
            normalized={name: {} for name in KNN_BLOCKS},
            used_values={name: {} for name in (*KNN_BLOCKS, "work_context", "work_activities", "education")},
            suppressed=set(),
            not_relevant=set(),
            work_context_cx={},
            education_percents={},
            work_activities=[],
            element_names=element_names,
        )
        for code, record in records.items()
    }

    features_path = processed_dir / "occupation_features.csv"
    with features_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            code = row["onetsoc_code"]
            item = occupations.get(code)
            if item is None:
                continue
            domain = row["domain"]
            element_id = row["element_id"]
            name = row["element_name"]
            element_names.setdefault(element_id, name)
            used = _parse_optional_float(row["used_value"])
            normalized = _parse_optional_float(row["normalized_value"])
            if _parse_bool(row["recommend_suppress"]):
                item.suppressed.add((domain, element_id))
            if _parse_bool(row["not_relevant"]):
                item.not_relevant.add((domain, element_id))
            if domain in item.normalized:
                item.normalized[domain][element_id] = normalized
                item.used_values[domain][element_id] = used
            if domain == "work_context" and used is not None:
                item.work_context_cx[element_id] = float(row["raw_value"])
            if domain == "education" and row.get("category"):
                item.education_percents[row["category"]] = float(row["raw_value"])
            if domain == "work_activities" and used is not None:
                item.work_activities.append((element_id, name, used))

    for item in occupations.values():
        item.work_activities.sort(key=lambda row: (-row[2], row[0]))

    zone_ref: dict[int, dict[str, str]] = {}
    zone_path = processed_dir / "job_zone_reference.csv"
    if zone_path.is_file():
        with zone_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                zone_ref[int(row["Job Zone"])] = dict(row)

    return OccupationIndex(
        feature_version=FEATURE_VERSION,
        catalog=catalog,
        occupations=occupations,
        job_zone_reference=zone_ref,
        element_names=element_names,
    )
