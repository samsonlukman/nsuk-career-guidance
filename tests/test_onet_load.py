from __future__ import annotations

import csv
import json
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.models import EducationCategory, JobZoneDefinition, Occupation, OccupationFeature, OnetSnapshot
from app.recommendation.constants import FEATURE_VERSION
from app.services.onet_loader import load_processed_snapshot

EXPECTED_OCCUPATIONS = 1016
EXPECTED_RECOMMENDABLE = 544
EXPECTED_KNN_COMPLETE = 862
EXPECTED_FEATURES = 136866
EXPECTED_ZONE_5_COMPLETE = 146
SAMPLE_SOC = "11-1011.00"


def test_expected_snapshot_exists(db_session: Session, loaded_snapshot) -> None:
    snapshot = db_session.scalar(select(OnetSnapshot).where(OnetSnapshot.feature_version == FEATURE_VERSION))
    assert snapshot is not None
    assert snapshot.onet_release == "30.3"
    assert str(snapshot.id) == loaded_snapshot.snapshot_id
    assert db_session.scalar(select(func.count()).select_from(OnetSnapshot)) == 1


def test_expected_occupation_counts(db_session: Session, loaded_snapshot) -> None:
    snapshot_id = loaded_snapshot.snapshot_id
    occupations = db_session.scalar(
        select(func.count()).select_from(Occupation).where(Occupation.snapshot_id == snapshot_id)
    )
    recommendable = db_session.scalar(
        select(func.count())
        .select_from(Occupation)
        .where(Occupation.snapshot_id == snapshot_id, Occupation.recommendable.is_(True))
    )
    knn_complete = db_session.scalar(
        select(func.count())
        .select_from(Occupation)
        .where(Occupation.snapshot_id == snapshot_id, Occupation.knn_complete.is_(True))
    )
    assert occupations == EXPECTED_OCCUPATIONS
    assert recommendable == EXPECTED_RECOMMENDABLE
    assert knn_complete == EXPECTED_KNN_COMPLETE
    assert loaded_snapshot.occupations == EXPECTED_OCCUPATIONS
    assert loaded_snapshot.recommendable == EXPECTED_RECOMMENDABLE


def test_expected_feature_records(db_session: Session, loaded_snapshot) -> None:
    features = db_session.scalar(
        select(func.count())
        .select_from(OccupationFeature)
        .where(OccupationFeature.snapshot_id == loaded_snapshot.snapshot_id)
    )
    assert features == EXPECTED_FEATURES
    assert loaded_snapshot.features == EXPECTED_FEATURES
    assert loaded_snapshot.job_zone_definitions == 4
    assert loaded_snapshot.education_categories == 12
    assert db_session.scalar(select(func.count()).select_from(JobZoneDefinition)) == 4
    assert db_session.scalar(select(func.count()).select_from(EducationCategory)) == 12


def test_zone_2_excluded_from_recommendable(db_session: Session, loaded_snapshot) -> None:
    snapshot_id = loaded_snapshot.snapshot_id
    zone2 = db_session.scalar(
        select(func.count()).select_from(Occupation).where(
            Occupation.snapshot_id == snapshot_id,
            Occupation.job_zone == 2,
        )
    )
    zone2_recommendable = db_session.scalar(
        select(func.count()).select_from(Occupation).where(
            Occupation.snapshot_id == snapshot_id,
            Occupation.job_zone == 2,
            Occupation.recommendable.is_(True),
        )
    )
    assert zone2 > 0
    assert zone2_recommendable == 0


def test_zone_5_present_and_recommendable_when_complete(db_session: Session, loaded_snapshot) -> None:
    snapshot_id = loaded_snapshot.snapshot_id
    zone5 = db_session.scalars(
        select(Occupation).where(Occupation.snapshot_id == snapshot_id, Occupation.job_zone == 5)
    ).all()
    assert zone5
    complete_zone5 = [row for row in zone5 if row.knn_complete]
    assert len(complete_zone5) == EXPECTED_ZONE_5_COMPLETE
    assert all(row.recommendable for row in complete_zone5)
    sample = db_session.scalar(
        select(Occupation).where(
            Occupation.snapshot_id == snapshot_id,
            Occupation.onetsoc_code == SAMPLE_SOC,
        )
    )
    assert sample is not None
    assert sample.job_zone == 5
    assert sample.recommendable is True
    assert sample.title == "Chief Executives"


def test_duplicate_import_does_not_create_duplicates(
    db_session: Session,
    runtime_engine,
    processed_dir: Path,
    loaded_snapshot,
) -> None:
    SessionLocal = sessionmaker(bind=runtime_engine, autoflush=False, class_=Session)
    session = SessionLocal()
    try:
        second = load_processed_snapshot(session, processed_dir)
        session.commit()
    finally:
        session.close()

    assert second.occupations == EXPECTED_OCCUPATIONS
    assert second.recommendable == EXPECTED_RECOMMENDABLE
    assert second.features == EXPECTED_FEATURES
    assert second.snapshot_id == loaded_snapshot.snapshot_id
    assert db_session.scalar(select(func.count()).select_from(OnetSnapshot)) == 1
    assert db_session.scalar(select(func.count()).select_from(Occupation)) == EXPECTED_OCCUPATIONS
    assert db_session.scalar(select(func.count()).select_from(OccupationFeature)) == EXPECTED_FEATURES


def test_soc_codes_unique_within_snapshot(db_session: Session, loaded_snapshot) -> None:
    snapshot_id = loaded_snapshot.snapshot_id
    total = db_session.scalar(
        select(func.count()).select_from(Occupation).where(Occupation.snapshot_id == snapshot_id)
    )
    distinct = db_session.scalar(
        select(func.count(func.distinct(Occupation.onetsoc_code))).where(Occupation.snapshot_id == snapshot_id)
    )
    assert total == distinct == EXPECTED_OCCUPATIONS


def test_feature_elements_associated_with_occupations(
    db_session: Session,
    loaded_snapshot,
    processed_dir: Path,
) -> None:
    snapshot_id = loaded_snapshot.snapshot_id
    occupation = db_session.scalar(
        select(Occupation).where(
            Occupation.snapshot_id == snapshot_id,
            Occupation.onetsoc_code == SAMPLE_SOC,
        )
    )
    assert occupation is not None
    realistic = db_session.scalar(
        select(OccupationFeature).where(
            OccupationFeature.occupation_id == occupation.id,
            OccupationFeature.element_id == "1.B.1.a",
            OccupationFeature.domain == "riasec",
        )
    )
    assert realistic is not None
    assert realistic.element_name == "Realistic"
    assert realistic.scale_id == "OI"
    assert realistic.include_in_knn is True
    assert float(realistic.raw_value) == 1.26
    assert float(realistic.used_value) == 1.26
    assert float(realistic.normalized_value) == 0.043333

    csv_count = 0
    with (processed_dir / "occupation_features.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["onetsoc_code"] == SAMPLE_SOC:
                csv_count += 1
    db_count = db_session.scalar(
        select(func.count()).select_from(OccupationFeature).where(
            OccupationFeature.occupation_id == occupation.id
        )
    )
    assert db_count == csv_count
    assert csv_count > 0

    orphan_features = db_session.scalar(
        select(func.count())
        .select_from(OccupationFeature)
        .where(OccupationFeature.occupation_id.not_in(select(Occupation.id)))
    )
    assert orphan_features == 0


def test_loaded_counts_match_processed_metadata(loaded_snapshot, processed_dir: Path) -> None:
    metadata = json.loads((processed_dir / "metadata.json").read_text(encoding="utf-8"))
    counts = metadata["counts"]
    assert loaded_snapshot.occupations == counts["occupation_data"]
    assert loaded_snapshot.recommendable == counts["recommendable_zones_3_5"]
    assert loaded_snapshot.knn_complete == counts["knn_complete"]
    assert loaded_snapshot.features == counts["occupation_feature_rows"]
