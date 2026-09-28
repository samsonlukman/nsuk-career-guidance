"""Deterministic, non-LLM explanations for a recommended occupation."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.recommendation.catalog import IndexedOccupation, OccupationIndex
from app.recommendation.rules import RuleFiring
from app.recommendation.student_features import StudentFeatureVector


@dataclass(frozen=True)
class FeatureContribution:
    block: str
    element_id: str
    element_name: str
    student_raw: float | None
    student_normalized: float | None
    occupation_raw: float | None
    occupation_normalized: float | None
    note: str


@dataclass(frozen=True)
class RecommendationExplanation:
    summary: str
    contributions: list[FeatureContribution] = field(default_factory=list)
    work_activities: list[str] = field(default_factory=list)
    job_zone_note: str | None = None
    rule_notes: list[str] = field(default_factory=list)


def _name(index: OccupationIndex, occupation: IndexedOccupation, element_id: str) -> str:
    return occupation.element_names.get(element_id) or index.element_names.get(element_id) or element_id


def explain_recommendation(
    student: StudentFeatureVector,
    occupation: IndexedOccupation,
    index: OccupationIndex,
    firings: list[RuleFiring],
    block_cosines: dict[str, float],
) -> RecommendationExplanation:
    contributions: list[FeatureContribution] = []
    riasec = student.blocks["riasec"]
    occ_riasec_raw = occupation.used_values.get("riasec", {})
    occ_riasec_norm = occupation.normalized.get("riasec", {})
    for element_id, raw, norm in zip(riasec.element_ids, riasec.raw_values, riasec.values, strict=True):
        occ_raw = occ_riasec_raw.get(element_id)
        if raw >= 5 and occ_raw is not None and occ_raw >= 5:
            contributions.append(
                FeatureContribution(
                    block="riasec",
                    element_id=element_id,
                    element_name=_name(index, occupation, element_id),
                    student_raw=raw,
                    student_normalized=norm,
                    occupation_raw=occ_raw,
                    occupation_normalized=occ_riasec_norm.get(element_id),
                    note="Student and occupation are both high on this interest type",
                )
            )

    for block_name, raw_threshold, norm_threshold in (
        ("sia", 5.0, 0.6),
        ("knowledge", 4.0, 0.6),
    ):
        block = student.blocks[block_name]
        occ_raw_map = occupation.used_values.get(block_name, {})
        occ_norm_map = occupation.normalized.get(block_name, {})
        for element_id, raw, norm in zip(block.element_ids, block.raw_values, block.values, strict=True):
            occ_raw = occ_raw_map.get(element_id)
            occ_norm = occ_norm_map.get(element_id)
            if occ_raw is None:
                continue
            if occ_raw >= raw_threshold or (occ_norm is not None and occ_norm >= norm_threshold):
                contributions.append(
                    FeatureContribution(
                        block=block_name,
                        element_id=element_id,
                        element_name=_name(index, occupation, element_id),
                        student_raw=raw,
                        student_normalized=norm,
                        occupation_raw=occ_raw,
                        occupation_normalized=occ_norm,
                        note="Selected area is also important in this occupation",
                    )
                )

    for block_name in ("essential_skills", "transferable_skills"):
        block = student.blocks[block_name]
        occ_norm_map = occupation.normalized.get(block_name, {})
        occ_raw_map = occupation.used_values.get(block_name, {})
        for element_id, raw, norm in zip(block.element_ids, block.raw_values, block.values, strict=True):
            occ_norm = occ_norm_map.get(element_id)
            if occ_norm is not None and norm >= 0.6 and occ_norm >= 0.6:
                contributions.append(
                    FeatureContribution(
                        block=block_name,
                        element_id=element_id,
                        element_name=_name(index, occupation, element_id),
                        student_raw=raw,
                        student_normalized=norm,
                        occupation_raw=occ_raw_map.get(element_id),
                        occupation_normalized=occ_norm,
                        note="Student rating and occupational importance are both high",
                    )
                )

    activities = [
        name for _element_id, name, _im in occupation.work_activities[:5]
    ]
    zone = occupation.record.job_zone
    zone_row = index.job_zone_reference.get(zone or -1) or {}
    job_zone_note = zone_row.get("Education") or zone_row.get("Name")
    rule_notes = [
        f"{item.code} ({item.action}): {item.reason}"
        for item in firings
        if item.onetsoc_code == occupation.onetsoc_code
        and item.action in {"penalise", "flag", "drop", "floor"}
    ]
    lead = occupation.record.title
    if contributions:
        top = contributions[0].element_name
        summary = (
            f"{lead} was recommended because your profile aligns on {top} "
            f"and related O*NET features. Match scores are similarity, not predicted success."
        )
    else:
        summary = (
            f"{lead} was among the nearest O*NET occupation profiles to your assessment. "
            "Match scores are similarity, not predicted success."
        )
    if block_cosines.get("riasec") is not None:
        summary += f" RIASEC block cosine={block_cosines['riasec']:.3f}."
    return RecommendationExplanation(
        summary=summary,
        contributions=contributions,
        work_activities=activities,
        job_zone_note=job_zone_note,
        rule_notes=rule_notes,
    )
