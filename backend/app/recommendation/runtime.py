"""Process-level cache for the processed O*NET occupation index.

Recommendation requests must not re-read raw O*NET TSV files. The approved
catalog loader reads the processed snapshot once per process.
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import REPO_ROOT
from app.recommendation.catalog import OccupationIndex, load_occupation_index
from app.recommendation.constants import PROCESSED_DIRNAME

_INDEX: OccupationIndex | None = None


def processed_snapshot_dir() -> Path:
    return REPO_ROOT / "data" / "processed" / PROCESSED_DIRNAME


def get_occupation_index() -> OccupationIndex:
    global _INDEX
    if _INDEX is None:
        directory = processed_snapshot_dir()
        if not (directory / "metadata.json").is_file():
            raise FileNotFoundError(f"Processed O*NET snapshot not found: {directory}")
        _INDEX = load_occupation_index(directory)
    return _INDEX


def warm_occupation_index() -> OccupationIndex:
    return get_occupation_index()
