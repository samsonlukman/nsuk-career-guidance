"""Write and load the processed occupational feature snapshot."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.recommendation.constants import (
    BLOCK_WEIGHTS,
    ONET_RELEASE_MONTH,
)
from app.recommendation.onet_io import FileInfo
from app.recommendation.preprocess import OccupationRecord, ProcessedRating


@dataclass
class BlockSpec:
    name: str
    weight: float | None
    scale_id: str
    element_ids: tuple[str, ...]
    element_names: dict[str, str]
    include_in_knn: bool


@dataclass
class ProcessedSnapshot:
    feature_version: str
    onet_release: str
    created_at: str
    source_files: list[FileInfo]
    occupations: list[OccupationRecord]
    features: list[ProcessedRating]
    blocks: dict[str, BlockSpec]
    counts: dict[str, int]
    job_zone_reference: list[dict[str, str]]
    education_categories: list[dict[str, str]]
    scales: dict[str, tuple[float, float]]


def _fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}".rstrip("0").rstrip(".")


def write_snapshot(snapshot: ProcessedSnapshot, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_metadata(snapshot, output_dir / "metadata.json")
    _write_occupations(snapshot.occupations, output_dir / "occupations.csv")
    _write_features(snapshot.features, output_dir / "occupation_features.csv")
    _write_job_zone_reference(snapshot.job_zone_reference, output_dir / "job_zone_reference.csv")
    _write_education_categories(
        snapshot.education_categories, output_dir / "education_categories.csv"
    )
    knn_codes = [row.onetsoc_code for row in snapshot.occupations if row.knn_complete]
    skip_wide = {
        name
        for name, spec in snapshot.blocks.items()
        if name == "education" or spec.scale_id == "RL"
    }
    for name, spec in snapshot.blocks.items():
        if name in skip_wide:
            continue
        matrix_path = output_dir / f"matrix_{name}.csv"
        _write_matrix(
            codes=knn_codes,
            element_ids=spec.element_ids,
            features=[row for row in snapshot.features if row.domain == name],
            path=matrix_path,
        )
    return output_dir


def load_metadata(output_dir: Path) -> dict:
    with (output_dir / "metadata.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def _write_metadata(snapshot: ProcessedSnapshot, path: Path) -> None:
    payload = {
        "feature_version": snapshot.feature_version,
        "onet_release": snapshot.onet_release,
        "onet_release_month": ONET_RELEASE_MONTH,
        "created_at": snapshot.created_at,
        "source_files": [asdict(info) for info in snapshot.source_files],
        "counts": snapshot.counts,
        "default_job_zones": [3, 4, 5],
        "block_weights": BLOCK_WEIGHTS,
        "scales": {
            scale_id: {"minimum": lo, "maximum": hi}
            for scale_id, (lo, hi) in snapshot.scales.items()
            if scale_id in {"OI", "IM", "WI", "CX", "RL"}
        },
        "blocks": {
            name: {
                "weight": spec.weight,
                "scale_id": spec.scale_id,
                "include_in_knn": spec.include_in_knn,
                "element_ids": list(spec.element_ids),
                "element_names": spec.element_names,
            }
            for name, spec in snapshot.blocks.items()
        },
        "notes": [
            "Raw O*NET files are never modified by ingest.",
            "Normalisation uses official Scales Reference min/max, not empirical ranges.",
            "Recommend Suppress drops a feature value; Not Relevant floors Importance to 1.0.",
            "Abilities and Work Values are not included in this snapshot.",
            "Work Context is stored for rules, not for KNN.",
        ],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_occupations(rows: list[OccupationRecord], path: Path) -> None:
    fieldnames = [
        "onetsoc_code",
        "title",
        "description",
        "job_zone",
        "knn_complete",
        "recommendable",
        "has_education",
        "has_work_context",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "onetsoc_code": row.onetsoc_code,
                    "title": row.title,
                    "description": row.description,
                    "job_zone": "" if row.job_zone is None else row.job_zone,
                    "knn_complete": str(row.knn_complete).lower(),
                    "recommendable": str(row.recommendable).lower(),
                    "has_education": str(row.has_education).lower(),
                    "has_work_context": str(row.has_work_context).lower(),
                }
            )


def _write_features(rows: list[ProcessedRating], path: Path) -> None:
    fieldnames = [
        "onetsoc_code",
        "domain",
        "element_id",
        "element_name",
        "scale_id",
        "category",
        "raw_value",
        "used_value",
        "normalized_value",
        "not_relevant",
        "recommend_suppress",
        "include_in_knn",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "onetsoc_code": row.onetsoc_code,
                    "domain": row.domain,
                    "element_id": row.element_id,
                    "element_name": row.element_name,
                    "scale_id": row.scale_id,
                    "category": row.category or "",
                    "raw_value": _fmt(row.raw_value),
                    "used_value": _fmt(row.used_value),
                    "normalized_value": _fmt(row.normalized_value),
                    "not_relevant": str(row.not_relevant).lower(),
                    "recommend_suppress": str(row.recommend_suppress).lower(),
                    "include_in_knn": str(row.include_in_knn).lower(),
                }
            )


def _write_matrix(
    codes: list[str],
    element_ids: tuple[str, ...],
    features: list[ProcessedRating],
    path: Path,
) -> None:
    lookup: dict[tuple[str, str], str] = {}
    for row in features:
        lookup[(row.onetsoc_code, row.element_id)] = _fmt(row.normalized_value)
    fieldnames = ["onetsoc_code", *element_ids]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for code in codes:
            record = {"onetsoc_code": code}
            for element_id in element_ids:
                record[element_id] = lookup.get((code, element_id), "")
            writer.writerow(record)


def _write_job_zone_reference(rows: list[dict[str, str]], path: Path) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_education_categories(rows: list[dict[str, str]], path: Path) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def empty_snapshot_timestamp() -> str:
    return utc_now()
