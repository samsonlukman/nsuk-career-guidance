"""Student assessment → versioned KNN feature vector (FINAL_SPEC sections 4–5).

Academic profile and work-setting preferences are stored on the vector for the
rule engine. They are not KNN dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.recommendation.constants import (
    BLOCK_WEIGHTS,
    COURSE_RELATEDNESS_VALUES,
    ESSENTIAL_INTERNAL_NAMES,
    ESSENTIAL_SKILL_IDS,
    FEATURE_VERSION,
    FURTHER_STUDY_VALUES,
    KNN_BLOCKS,
    LEVEL_VALUES,
    MAX_SPARSE_SELECTIONS,
    MIN_SPARSE_SELECTIONS,
    OFFICIAL_SCALES,
    RIASEC_ELEMENT_IDS,
    RIASEC_INTERNAL_NAMES,
    STUDENT_PREFERENCE_SCALE,
    STUDENT_STYLE_SCALE,
    TRANSFERABLE_INTERNAL_NAMES,
    TRANSFERABLE_SKILL_IDS,
    WORK_STYLE_IDS,
    WORK_STYLE_INTERNAL_NAMES,
    CONTEXT_INDOOR,
    CONTEXT_OUTDOOR,
    CONTEXT_PUBLIC,
    CONTEXT_TEAM,
)
from app.recommendation.exceptions import AssessmentError
from app.recommendation.preprocess import minmax


def _as_number(value: object, field: str) -> float:
    if isinstance(value, bool) or value is None:
        raise AssessmentError(f"{field} is required", field)
    if isinstance(value, int):
        return float(value)
    if isinstance(value, float):
        if value != int(value):
            raise AssessmentError(f"{field} must be a whole number on the O*NET scale", field)
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return float(int(value.strip()))
    raise AssessmentError(f"{field} must be a number", field)


def _in_scale(value: float, minimum: float, maximum: float, field: str) -> float:
    if value < minimum or value > maximum:
        raise AssessmentError(
            f"{field} must be between {int(minimum)} and {int(maximum)}",
            field,
        )
    return value


def _resolve_id(key: str, mapping: dict[str, str], allowed: tuple[str, ...], field: str) -> str:
    if key in allowed:
        return key
    if key in mapping:
        return mapping[key]
    raise AssessmentError(f"Unknown {field} element: {key}", field)


def _require_fixed_block(
    raw: dict[str, object] | None,
    *,
    element_ids: tuple[str, ...],
    mapping: dict[str, str],
    minimum: float,
    maximum: float,
    field: str,
) -> dict[str, float]:
    if not raw:
        raise AssessmentError(f"{field} ratings are required", field)
    resolved: dict[str, float] = {}
    for key, value in raw.items():
        element_id = _resolve_id(str(key), mapping, element_ids, field)
        if element_id in resolved:
            raise AssessmentError(f"Duplicate {field} rating for {element_id}", field)
        number = _in_scale(_as_number(value, field), minimum, maximum, field)
        resolved[element_id] = number
    missing = [element_id for element_id in element_ids if element_id not in resolved]
    extra = [element_id for element_id in resolved if element_id not in element_ids]
    if extra:
        raise AssessmentError(f"{field} contains unsupported elements: {extra}", field)
    if missing:
        raise AssessmentError(f"{field} is missing required elements: {missing}", field)
    return {element_id: resolved[element_id] for element_id in element_ids}


def _require_sparse_block(
    raw: dict[str, object] | None,
    *,
    allowed: tuple[str, ...],
    minimum: float,
    maximum: float,
    field: str,
) -> dict[str, float]:
    if not raw:
        raise AssessmentError(
            f"Select at least {MIN_SPARSE_SELECTIONS} {field} element(s)",
            field,
        )
    resolved: dict[str, float] = {}
    for key, value in raw.items():
        element_id = str(key)
        if element_id not in allowed:
            raise AssessmentError(f"Unknown {field} element: {element_id}", field)
        if element_id in resolved:
            raise AssessmentError(f"Duplicate {field} selection {element_id}", field)
        resolved[element_id] = _in_scale(_as_number(value, field), minimum, maximum, field)
    if len(resolved) < MIN_SPARSE_SELECTIONS:
        raise AssessmentError(
            f"Select at least {MIN_SPARSE_SELECTIONS} {field} element(s)",
            field,
        )
    if len(resolved) > MAX_SPARSE_SELECTIONS:
        raise AssessmentError(
            f"Select at most {MAX_SPARSE_SELECTIONS} {field} elements",
            field,
        )
    # Preserve student selection order (not zero-filled unused IDs).
    return resolved


@dataclass(frozen=True)
class FeatureCatalog:
    """Allowed SIA/knowledge IDs from the processed O*NET snapshot."""

    sia_ids: tuple[str, ...]
    knowledge_ids: tuple[str, ...]
    sia_names: dict[str, str] = field(default_factory=dict)
    knowledge_names: dict[str, str] = field(default_factory=dict)
    feature_version: str = FEATURE_VERSION
    scales: dict[str, tuple[float, float]] = field(default_factory=lambda: dict(OFFICIAL_SCALES))

    @classmethod
    def from_metadata(cls, metadata: dict) -> FeatureCatalog:
        sia = metadata["blocks"]["sia"]
        knowledge = metadata["blocks"]["knowledge"]
        scales = {
            scale_id: (float(bounds["minimum"]), float(bounds["maximum"]))
            for scale_id, bounds in metadata.get("scales", {}).items()
        }
        return cls(
            sia_ids=tuple(sia["element_ids"]),
            knowledge_ids=tuple(knowledge["element_ids"]),
            sia_names=dict(sia.get("element_names") or {}),
            knowledge_names=dict(knowledge.get("element_names") or {}),
            feature_version=str(metadata.get("feature_version") or FEATURE_VERSION),
            scales=scales or dict(OFFICIAL_SCALES),
        )

    @classmethod
    def from_processed_dir(cls, processed_dir: Path) -> FeatureCatalog:
        import json

        path = processed_dir / "metadata.json"
        with path.open(encoding="utf-8") as handle:
            return cls.from_metadata(json.load(handle))


@dataclass(frozen=True)
class AcademicProfile:
    faculty: str | None = None
    department: str | None = None
    level: str | None = None
    further_study: str = "maybe"
    course_relatedness: str = "open"


@dataclass(frozen=True)
class WorkPreferences:
    pref_indoor: int | None = None
    pref_outdoor: int | None = None
    pref_team: int | None = None
    pref_public: int | None = None

    def as_cx_map(self) -> dict[str, int]:
        mapping = {
            CONTEXT_INDOOR: self.pref_indoor,
            CONTEXT_OUTDOOR: self.pref_outdoor,
            CONTEXT_TEAM: self.pref_team,
            CONTEXT_PUBLIC: self.pref_public,
        }
        return {key: value for key, value in mapping.items() if value is not None}


@dataclass(frozen=True)
class BlockVector:
    name: str
    element_ids: tuple[str, ...]
    raw_values: tuple[float, ...]
    values: tuple[float, ...]  # min–max to [0, 1]
    weight: float
    scale_id: str

    def as_dict(self) -> dict[str, float]:
        return dict(zip(self.element_ids, self.values, strict=True))

    def raw_dict(self) -> dict[str, float]:
        return dict(zip(self.element_ids, self.raw_values, strict=True))


@dataclass(frozen=True)
class StudentFeatureVector:
    feature_version: str
    blocks: dict[str, BlockVector]
    profile: AcademicProfile
    preferences: WorkPreferences

    def knn_blocks(self) -> dict[str, BlockVector]:
        return {name: self.blocks[name] for name in KNN_BLOCKS}


@dataclass(frozen=True)
class StudentAssessment:
    riasec: dict[str, object]
    sia: dict[str, object]
    essential_skills: dict[str, object]
    transferable_skills: dict[str, object]
    work_styles: dict[str, object]
    knowledge: dict[str, object]
    profile: AcademicProfile = field(default_factory=AcademicProfile)
    preferences: WorkPreferences = field(default_factory=WorkPreferences)


def _normalize_profile(profile: AcademicProfile) -> AcademicProfile:
    faculty = profile.faculty.strip() if profile.faculty else None
    department = profile.department.strip() if profile.department else None
    level = profile.level.strip() if profile.level else None
    if level is not None:
        if level not in LEVEL_VALUES:
            raise AssessmentError("level must be 100, 200, 300, or 400", "level")
    further = (profile.further_study or "").strip().lower()
    if further not in FURTHER_STUDY_VALUES:
        raise AssessmentError("further_study must be yes, maybe, or no", "further_study")
    relatedness = (profile.course_relatedness or "").strip().lower()
    if relatedness not in COURSE_RELATEDNESS_VALUES:
        raise AssessmentError("course_relatedness must be related or open", "course_relatedness")
    return AcademicProfile(
        faculty=faculty or None,
        department=department or None,
        level=level,
        further_study=further,
        course_relatedness=relatedness,
    )


def _normalize_preferences(prefs: WorkPreferences) -> WorkPreferences:
    lo, hi = STUDENT_PREFERENCE_SCALE

    def one(value: int | None, field: str) -> int | None:
        if value is None:
            return None
        number = _in_scale(_as_number(value, field), lo, hi, field)
        return int(number)

    return WorkPreferences(
        pref_indoor=one(prefs.pref_indoor, "pref_indoor"),
        pref_outdoor=one(prefs.pref_outdoor, "pref_outdoor"),
        pref_team=one(prefs.pref_team, "pref_team"),
        pref_public=one(prefs.pref_public, "pref_public"),
    )


def _block(
    name: str,
    raw: dict[str, float],
    *,
    scale_id: str,
    scales: dict[str, tuple[float, float]],
    student_bounds: tuple[float, float] | None = None,
) -> BlockVector:
    minimum, maximum = student_bounds if student_bounds is not None else scales[scale_id]
    values = tuple(minmax(value, minimum, maximum) for value in raw.values())
    return BlockVector(
        name=name,
        element_ids=tuple(raw.keys()),
        raw_values=tuple(raw.values()),
        values=values,
        weight=BLOCK_WEIGHTS[name],
        scale_id=scale_id,
    )


def build_student_vector(
    assessment: StudentAssessment,
    catalog: FeatureCatalog,
) -> StudentFeatureVector:
    """Transform a validated assessment into feature_version onet_30_3_v1."""
    if catalog.feature_version != FEATURE_VERSION:
        raise AssessmentError(
            f"Catalog feature_version {catalog.feature_version} does not match {FEATURE_VERSION}",
            "feature_version",
        )
    scales = catalog.scales or dict(OFFICIAL_SCALES)
    oi_min, oi_max = scales["OI"]
    im_min, im_max = scales["IM"]

    riasec = _require_fixed_block(
        assessment.riasec,
        element_ids=RIASEC_ELEMENT_IDS,
        mapping=RIASEC_INTERNAL_NAMES,
        minimum=oi_min,
        maximum=oi_max,
        field="riasec",
    )
    essential = _require_fixed_block(
        assessment.essential_skills,
        element_ids=ESSENTIAL_SKILL_IDS,
        mapping=ESSENTIAL_INTERNAL_NAMES,
        minimum=im_min,
        maximum=im_max,
        field="essential_skills",
    )
    transferable = _require_fixed_block(
        assessment.transferable_skills,
        element_ids=TRANSFERABLE_SKILL_IDS,
        mapping=TRANSFERABLE_INTERNAL_NAMES,
        minimum=im_min,
        maximum=im_max,
        field="transferable_skills",
    )
    styles = _require_fixed_block(
        assessment.work_styles,
        element_ids=WORK_STYLE_IDS,
        mapping=WORK_STYLE_INTERNAL_NAMES,
        minimum=STUDENT_STYLE_SCALE[0],
        maximum=STUDENT_STYLE_SCALE[1],
        field="work_styles",
    )
    sia = _require_sparse_block(
        assessment.sia,
        allowed=catalog.sia_ids,
        minimum=oi_min,
        maximum=oi_max,
        field="sia",
    )
    knowledge = _require_sparse_block(
        assessment.knowledge,
        allowed=catalog.knowledge_ids,
        minimum=im_min,
        maximum=im_max,
        field="knowledge",
    )

    blocks = {
        "riasec": _block("riasec", riasec, scale_id="OI", scales=scales),
        "sia": _block("sia", sia, scale_id="OI", scales=scales),
        "essential_skills": _block("essential_skills", essential, scale_id="IM", scales=scales),
        "transferable_skills": _block(
            "transferable_skills", transferable, scale_id="IM", scales=scales
        ),
        "work_styles": _block(
            "work_styles",
            styles,
            scale_id="WI",
            scales=scales,
            student_bounds=STUDENT_STYLE_SCALE,
        ),
        "knowledge": _block("knowledge", knowledge, scale_id="IM", scales=scales),
    }
    return StudentFeatureVector(
        feature_version=FEATURE_VERSION,
        blocks=blocks,
        profile=_normalize_profile(assessment.profile),
        preferences=_normalize_preferences(assessment.preferences),
    )
