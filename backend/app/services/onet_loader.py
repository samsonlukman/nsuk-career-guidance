"""Load processed O*NET snapshot files into PostgreSQL. Does not read raw TSVs."""

from __future__ import annotations

import csv
import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import EducationCategory, JobZoneDefinition, Occupation, OccupationFeature, OnetSnapshot
from app.recommendation.constants import FEATURE_VERSION


@dataclass
class LoadResult:
    feature_version: str
    snapshot_id: str
    occupations: int
    recommendable: int
    knn_complete: int
    features: int
    job_zone_definitions: int
    education_categories: int
    features_skipped: bool


def _parse_bool(value: str) -> bool:
    return (value or "").strip().lower() == "true"


def _parse_optional_int(value: str) -> int | None:
    text = (value or "").strip()
    if text == "":
        return None
    return int(text)


def _parse_optional_float(value: str) -> float | None:
    text = (value or "").strip()
    if text == "":
        return None
    return float(text)


def default_processed_dir(repo_root: Path) -> Path:
    return repo_root / "data" / "processed" / FEATURE_VERSION


def load_processed_snapshot(
    session: Session,
    processed_dir: Path,
    *,
    force_features: bool = False,
) -> LoadResult:
    """Upsert the processed snapshot. Safe to run more than once.

    Occupations are keyed by (snapshot_id, onetsoc_code). Feature rows are
    replaced only when missing, incomplete, or force_features=True.
    """
    processed_dir = processed_dir.resolve()
    metadata_path = processed_dir / "metadata.json"
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Processed snapshot metadata not found: {metadata_path}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    feature_version = metadata["feature_version"]
    if feature_version != FEATURE_VERSION:
        raise ValueError(f"Refusing to load {feature_version}; expected {FEATURE_VERSION}")

    expected_features = int(metadata["counts"]["occupation_feature_rows"])
    snapshot_id = _upsert_snapshot(session, metadata)
    _upsert_occupations(session, snapshot_id, processed_dir / "occupations.csv")
    session.flush()

    code_to_id = dict(
        session.execute(
            select(Occupation.onetsoc_code, Occupation.id).where(Occupation.snapshot_id == snapshot_id)
        ).all()
    )
    _upsert_job_zones(session, snapshot_id, processed_dir / "job_zone_reference.csv")
    _upsert_education_categories(session, snapshot_id, processed_dir / "education_categories.csv")

    existing_features = int(
        session.scalar(
            select(func.count())
            .select_from(OccupationFeature)
            .where(OccupationFeature.snapshot_id == snapshot_id)
        )
        or 0
    )
    features_skipped = False
    if existing_features == expected_features and not force_features:
        features_skipped = True
    else:
        if existing_features:
            session.execute(delete(OccupationFeature).where(OccupationFeature.snapshot_id == snapshot_id))
            session.flush()
        _insert_features(session, snapshot_id, code_to_id, processed_dir / "occupation_features.csv")

    session.flush()
    counts = _count_snapshot(session, snapshot_id)
    return LoadResult(
        feature_version=feature_version,
        snapshot_id=str(snapshot_id),
        features_skipped=features_skipped,
        **counts,
    )


def _upsert_snapshot(session: Session, metadata: dict) -> uuid.UUID:
    payload = {
        "feature_version": metadata["feature_version"],
        "onet_release": metadata["onet_release"],
        "onet_release_month": metadata.get("onet_release_month"),
        "scales_json": metadata.get("scales") or {},
        "block_spec_json": metadata.get("blocks") or {},
        "source_files_json": {"files": metadata.get("source_files") or []},
    }
    snapshot = session.scalar(
        select(OnetSnapshot).where(OnetSnapshot.feature_version == payload["feature_version"])
    )
    if snapshot is None:
        snapshot = OnetSnapshot(id=uuid.uuid4(), **payload)
        session.add(snapshot)
        session.flush()
        return snapshot.id
    snapshot.onet_release = payload["onet_release"]
    snapshot.onet_release_month = payload["onet_release_month"]
    snapshot.scales_json = payload["scales_json"]
    snapshot.block_spec_json = payload["block_spec_json"]
    snapshot.source_files_json = payload["source_files_json"]
    session.flush()
    return snapshot.id


def _upsert_occupations(session: Session, snapshot_id: uuid.UUID, path: Path) -> None:
    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "id": uuid.uuid4(),
                    "snapshot_id": snapshot_id,
                    "onetsoc_code": row["onetsoc_code"],
                    "title": row["title"],
                    "description": row["description"],
                    "job_zone": _parse_optional_int(row["job_zone"]),
                    "knn_complete": _parse_bool(row["knn_complete"]),
                    "recommendable": _parse_bool(row["recommendable"]),
                    "has_education": _parse_bool(row["has_education"]),
                    "has_work_context": _parse_bool(row["has_work_context"]),
                }
            )
    if not rows:
        raise ValueError(f"No occupations found in {path}")
    stmt = insert(Occupation).values(rows)
    session.execute(
        stmt.on_conflict_do_update(
            constraint="uq_occupations_snapshot_soc",
            set_={
                "title": stmt.excluded.title,
                "description": stmt.excluded.description,
                "job_zone": stmt.excluded.job_zone,
                "knn_complete": stmt.excluded.knn_complete,
                "recommendable": stmt.excluded.recommendable,
                "has_education": stmt.excluded.has_education,
                "has_work_context": stmt.excluded.has_work_context,
            },
        )
    )


def _upsert_job_zones(session: Session, snapshot_id: uuid.UUID, path: Path) -> None:
    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "snapshot_id": snapshot_id,
                    "job_zone": int(row["Job Zone"]),
                    "name": row["Name"],
                    "education": row.get("Education"),
                    "experience": row.get("Experience"),
                    "job_training": row.get("Job Training"),
                    "examples": row.get("Examples"),
                    "svp_range": row.get("SVP Range"),
                }
            )
    if not rows:
        return
    stmt = insert(JobZoneDefinition).values(rows)
    session.execute(
        stmt.on_conflict_do_update(
            constraint="uq_job_zone_definitions",
            set_={
                "name": stmt.excluded.name,
                "education": stmt.excluded.education,
                "experience": stmt.excluded.experience,
                "job_training": stmt.excluded.job_training,
                "examples": stmt.excluded.examples,
                "svp_range": stmt.excluded.svp_range,
            },
        )
    )


def _upsert_education_categories(session: Session, snapshot_id: uuid.UUID, path: Path) -> None:
    rows = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "snapshot_id": snapshot_id,
                    "element_id": row["Element ID"],
                    "scale_id": row["Scale ID"],
                    "category": row["Category"],
                    "category_description": row["Category Description"],
                }
            )
    if not rows:
        return
    stmt = insert(EducationCategory).values(rows)
    session.execute(
        stmt.on_conflict_do_update(
            constraint="uq_education_categories",
            set_={
                "scale_id": stmt.excluded.scale_id,
                "category_description": stmt.excluded.category_description,
            },
        )
    )


def _insert_features(
    session: Session,
    snapshot_id: uuid.UUID,
    code_to_id: dict[str, uuid.UUID],
    path: Path,
) -> None:
    connection = session.connection()
    dbapi = connection.connection
    driver = getattr(dbapi, "driver_connection", None) or dbapi
    copy_sql = (
        "COPY occupation_features ("
        "snapshot_id, occupation_id, domain, element_id, element_name, "
        "scale_id, category, raw_value, used_value, normalized_value, "
        "not_relevant, recommend_suppress, include_in_knn"
        ") FROM STDIN"
    )
    with driver.cursor() as cursor:
        with cursor.copy(copy_sql) as copy:
            with path.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    occupation_id = code_to_id.get(row["onetsoc_code"])
                    if occupation_id is None:
                        raise ValueError(f"Feature row has unknown occupation {row['onetsoc_code']}")
                    copy.write_row(
                        (
                            snapshot_id,
                            occupation_id,
                            row["domain"],
                            row["element_id"],
                            row["element_name"],
                            row["scale_id"],
                            row.get("category") or "",
                            float(row["raw_value"]),
                            _parse_optional_float(row["used_value"]),
                            _parse_optional_float(row["normalized_value"]),
                            _parse_bool(row["not_relevant"]),
                            _parse_bool(row["recommend_suppress"]),
                            _parse_bool(row["include_in_knn"]),
                        )
                    )


def _count_snapshot(session: Session, snapshot_id: uuid.UUID) -> dict[str, int]:
    occupations = session.scalar(
        select(func.count()).select_from(Occupation).where(Occupation.snapshot_id == snapshot_id)
    )
    recommendable = session.scalar(
        select(func.count())
        .select_from(Occupation)
        .where(Occupation.snapshot_id == snapshot_id, Occupation.recommendable.is_(True))
    )
    knn_complete = session.scalar(
        select(func.count())
        .select_from(Occupation)
        .where(Occupation.snapshot_id == snapshot_id, Occupation.knn_complete.is_(True))
    )
    features = session.scalar(
        select(func.count())
        .select_from(OccupationFeature)
        .where(OccupationFeature.snapshot_id == snapshot_id)
    )
    zones = session.scalar(
        select(func.count())
        .select_from(JobZoneDefinition)
        .where(JobZoneDefinition.snapshot_id == snapshot_id)
    )
    education = session.scalar(
        select(func.count())
        .select_from(EducationCategory)
        .where(EducationCategory.snapshot_id == snapshot_id)
    )
    return {
        "occupations": int(occupations or 0),
        "recommendable": int(recommendable or 0),
        "knn_complete": int(knn_complete or 0),
        "features": int(features or 0),
        "job_zone_definitions": int(zones or 0),
        "education_categories": int(education or 0),
    }
