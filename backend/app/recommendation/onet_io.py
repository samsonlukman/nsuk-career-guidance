"""Read-only loaders for official O*NET tab-delimited files.

This module never opens files under data/raw/ for writing.
"""

from __future__ import annotations

import csv
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

from app.recommendation.constants import (
    EXPECTED_HEADERS,
    ONET_RELEASE,
    RATING_CORE_HEADERS,
    REQUIRED_RAW_FILES,
)

csv.field_size_limit(sys.maxsize)


@dataclass(frozen=True)
class FileInfo:
    name: str
    path: str
    bytes: int
    sha256: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def describe_file(path: Path) -> FileInfo:
    return FileInfo(
        name=path.name,
        path=str(path),
        bytes=path.stat().st_size,
        sha256=sha256_file(path),
    )


def verify_raw_dir(raw_dir: Path) -> list[FileInfo]:
    if not raw_dir.is_dir():
        raise FileNotFoundError(f"O*NET raw directory not found: {raw_dir}")
    infos: list[FileInfo] = []
    missing = [name for name in REQUIRED_RAW_FILES if not (raw_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing required O*NET files: {missing}")
    readme = (raw_dir / "Read Me.txt").read_text(encoding="utf-8")
    if ONET_RELEASE not in readme:
        raise ValueError(
            f"Read Me.txt does not identify O*NET {ONET_RELEASE}. "
            "Refusing to ingest an unexpected database version."
        )
    if (raw_dir / "Work Values.txt").exists():
        raise ValueError(
            "Work Values.txt is present but is not part of the approved O*NET 30.3 "
            "feature set. Remove it or use the official 30.3 snapshot only."
        )
    for name in REQUIRED_RAW_FILES:
        path = raw_dir / name
        expected = EXPECTED_HEADERS.get(name)
        if expected:
            with path.open(newline="", encoding="utf-8") as handle:
                header = next(csv.reader(handle, delimiter="\t"))
            if header[: len(expected)] != expected:
                raise ValueError(f"Unexpected header in {name}: {header}")
        infos.append(describe_file(path))
    return infos


def load_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def iter_tsv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def require_headers(path: Path, required: list[str]) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        header = next(csv.reader(handle, delimiter="\t"))
    missing = [col for col in required if col not in header]
    if missing:
        raise ValueError(f"{path.name} is missing columns {missing}")


def load_scales(raw_dir: Path) -> dict[str, tuple[float, float]]:
    path = raw_dir / "Scales Reference.txt"
    scales: dict[str, tuple[float, float]] = {}
    for row in load_tsv(path):
        scales[row["Scale ID"]] = (float(row["Minimum"]), float(row["Maximum"]))
    for scale_id in ("OI", "IM", "WI", "CX", "RL"):
        if scale_id not in scales:
            raise ValueError(f"Scales Reference.txt has no {scale_id} scale")
    return scales


def load_occupation_data(raw_dir: Path) -> dict[str, dict[str, str]]:
    path = raw_dir / "Occupation Data.txt"
    occupations: dict[str, dict[str, str]] = {}
    for row in load_tsv(path):
        code = row["O*NET-SOC Code"].strip()
        occupations[code] = {
            "onetsoc_code": code,
            "title": row["Title"],
            "description": row["Description"],
        }
    return occupations


def load_job_zones(raw_dir: Path) -> dict[str, int]:
    zones: dict[str, int] = {}
    for row in load_tsv(raw_dir / "Job Zones.txt"):
        zones[row["O*NET-SOC Code"].strip()] = int(row["Job Zone"])
    return zones


def flag_yes(value: str | None) -> bool:
    return (value or "").strip().upper() == "Y"


@dataclass(frozen=True)
class RatingRow:
    onetsoc_code: str
    element_id: str
    element_name: str
    scale_id: str
    raw_value: float
    not_relevant: bool
    recommend_suppress: bool
    category: str | None = None


def load_ratings(
    path: Path,
    *,
    scale_id: str,
    element_ids: tuple[str, ...] | None = None,
    require_category: bool = False,
) -> list[RatingRow]:
    require_headers(path, RATING_CORE_HEADERS)
    allowed = set(element_ids) if element_ids is not None else None
    rows: list[RatingRow] = []
    for raw in iter_tsv(path):
        if raw.get("Scale ID") != scale_id:
            continue
        element_id = raw["Element ID"].strip()
        if allowed is not None and element_id not in allowed:
            continue
        category = raw.get("Category")
        if require_category:
            if not category or category.strip() in {"", "n/a"}:
                continue
        else:
            if category and category.strip() not in {"", "n/a"}:
                continue
        value = raw.get("Data Value", "").strip()
        if value == "":
            continue
        rows.append(
            RatingRow(
                onetsoc_code=raw["O*NET-SOC Code"].strip(),
                element_id=element_id,
                element_name=raw["Element Name"],
                scale_id=scale_id,
                raw_value=float(value),
                not_relevant=flag_yes(raw.get("Not Relevant")),
                recommend_suppress=flag_yes(raw.get("Recommend Suppress")),
                category=None if not category or category.strip() in {"", "n/a"} else category.strip(),
            )
        )
    return rows


def discover_element_ids(rows: list[RatingRow]) -> tuple[str, ...]:
    seen: dict[str, None] = {}
    for row in rows:
        seen.setdefault(row.element_id, None)
    return tuple(sorted(seen))


def element_names(rows: list[RatingRow]) -> dict[str, str]:
    names: dict[str, str] = {}
    for row in rows:
        names.setdefault(row.element_id, row.element_name)
    return names
