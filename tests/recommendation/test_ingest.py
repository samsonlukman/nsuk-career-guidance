from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from app.recommendation.constants import ESSENTIAL_SKILL_IDS, FEATURE_VERSION
from app.recommendation.ingest import run_ingest
from app.recommendation.onet_io import sha256_file
from tests.recommendation.helpers import COMPLETE_ZONE2, COMPLETE_ZONE4, INCOMPLETE, write_mini_onet

REAL_RAW = Path("/Users/apple/finalproject/data/raw/db_30_3_text")


def test_ingest_mini_snapshot(tmp_path: Path) -> None:
    raw = write_mini_onet(tmp_path / "raw")
    out = tmp_path / "processed"
    snapshot = run_ingest(raw, out)

    assert snapshot.feature_version == FEATURE_VERSION
    assert snapshot.counts["knn_complete"] == 2
    assert snapshot.counts["recommendable_zones_3_5"] == 1
    assert snapshot.counts["knn_complete_zone_2"] == 1
    assert snapshot.counts["knn_complete_zone_4"] == 1

    occupations = {row.onetsoc_code: row for row in snapshot.occupations}
    assert occupations[COMPLETE_ZONE4].recommendable is True
    assert occupations[COMPLETE_ZONE2].recommendable is False
    assert occupations[INCOMPLETE].knn_complete is False

    knowledge_nr = next(
        row
        for row in snapshot.features
        if row.onetsoc_code == COMPLETE_ZONE4
        and row.domain == "knowledge"
        and row.not_relevant
    )
    assert knowledge_nr.used_value == 1.0
    assert knowledge_nr.normalized_value == 0.0

    suppressed = next(
        row
        for row in snapshot.features
        if row.onetsoc_code == COMPLETE_ZONE4
        and row.domain == "essential_skills"
        and row.recommend_suppress
    )
    assert suppressed.used_value is None
    assert suppressed.normalized_value is None
    assert suppressed.include_in_knn is False

    metadata = json.loads((out / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["counts"]["knn_complete"] == 2
    assert metadata["blocks"]["riasec"]["include_in_knn"] is True
    assert metadata["blocks"]["work_context"]["include_in_knn"] is False

    with (out / "matrix_essential_skills.csv").open(newline="", encoding="utf-8") as handle:
        matrix = list(csv.DictReader(handle))
    zone4 = next(row for row in matrix if row["onetsoc_code"] == COMPLETE_ZONE4)
    assert zone4[ESSENTIAL_SKILL_IDS[0]] == ""
    assert zone4[ESSENTIAL_SKILL_IDS[1]] != ""

    assert (out / "matrix_work_context.csv").is_file()
    assert not (out / "matrix_education.csv").exists()

    education_rows = [
        row
        for row in snapshot.features
        if row.onetsoc_code == COMPLETE_ZONE4 and row.domain == "education"
    ]
    assert education_rows
    assert education_rows[0].category == "6"

    with (out / "occupations.csv").open(newline="", encoding="utf-8") as handle:
        written = {row["onetsoc_code"]: row for row in csv.DictReader(handle)}
    assert written[COMPLETE_ZONE4]["recommendable"] == "true"
    assert written[INCOMPLETE]["knn_complete"] == "false"


def test_ingest_does_not_write_raw_files(tmp_path: Path) -> None:
    raw = write_mini_onet(tmp_path / "raw")
    before = {path.name: (path.stat().st_mtime_ns, sha256_file(path)) for path in raw.iterdir()}
    run_ingest(raw, tmp_path / "processed")
    after = {path.name: (path.stat().st_mtime_ns, sha256_file(path)) for path in raw.iterdir()}
    assert before == after
    assert set(before) == set(after)


def test_ingest_refuses_output_inside_raw(tmp_path: Path) -> None:
    raw = write_mini_onet(tmp_path / "raw")
    with pytest.raises(ValueError, match="must not be inside"):
        run_ingest(raw, raw / "processed")


def test_ingest_rejects_work_values_file(tmp_path: Path) -> None:
    raw = write_mini_onet(tmp_path / "raw")
    (raw / "Work Values.txt").write_text("should not be mixed into 30.3\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Work Values"):
        run_ingest(raw, tmp_path / "processed")


@pytest.mark.skipif(not (REAL_RAW / "Occupation Data.txt").is_file(), reason="O*NET 30.3 raw files are not present")
def test_ingest_real_onet_30_3(tmp_path: Path) -> None:
    before = sha256_file(REAL_RAW / "Occupation Data.txt")
    snapshot = run_ingest(REAL_RAW, tmp_path / "processed")
    after = sha256_file(REAL_RAW / "Occupation Data.txt")
    assert before == after
    assert snapshot.onet_release == "30.3"
    assert snapshot.counts["occupation_data"] == 1016
    assert snapshot.counts["knn_complete"] == 862
    assert snapshot.counts["recommendable_zones_3_5"] == 544
    assert snapshot.counts["knn_complete_zone_2"] == 318
    assert snapshot.counts["knn_complete_zone_3"] == 196
    assert snapshot.counts["knn_complete_zone_4"] == 202
    assert snapshot.counts["knn_complete_zone_5"] == 146
    assert snapshot.counts["knn_complete_with_education"] == 846
    assert "abilities" not in snapshot.blocks
    assert "work_values" not in snapshot.blocks
    assert (tmp_path / "processed" / "matrix_riasec.csv").is_file()
    assert (tmp_path / "processed" / "matrix_work_context.csv").is_file()
    assert not (tmp_path / "processed" / "matrix_education.csv").exists()
