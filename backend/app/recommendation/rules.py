"""Named rule engine. Rules are not buried inside KNN."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.recommendation.constants import (
    CONTEXT_INDOOR,
    CONTEXT_OUTDOOR,
    CONTEXT_PUBLIC,
    CONTEXT_TEAM,
    PROFESSIONAL_EDUCATION_CATEGORIES,
)
from app.recommendation.catalog import IndexedOccupation, OccupationIndex
from app.recommendation.student_features import StudentFeatureVector

ACTION_EXCLUDE = "exclude"
ACTION_PENALISE = "penalise"
ACTION_FLAG = "flag"
ACTION_DROP = "drop"
ACTION_FLOOR = "floor"

RULE_CODES = (
    "R-DATA",
    "R-SUPPRESS",
    "R-ZONE-LOW",
    "R-ZONE-5",
    "R-RELATED",
    "R-CONTEXT",
    "R-EDU",
)


@dataclass(frozen=True)
class RuleFiring:
    code: str
    onetsoc_code: str
    action: str
    reason: str
    penalty: float | None = None
    element_id: str | None = None
    domain: str | None = None


@dataclass
class RuleConfig:
    """Admin-editable settings. Faculty priors have no built-in NSUK list."""

    enabled: dict[str, bool] = field(
        default_factory=lambda: {code: True for code in RULE_CODES}
    )
    faculty_knowledge_priors: dict[str, tuple[str, ...]] = field(default_factory=dict)
    related_im_threshold: float = 3.0
    related_penalty: float = 0.80
    context_outdoor_penalty: float = 0.85
    context_public_penalty: float = 0.90
    context_team_penalty: float = 0.95
    outdoor_cx_threshold: float = 4.0
    indoor_cx_low: float = 3.0
    public_cx_threshold: float = 4.0
    team_cx_threshold: float = 4.5

    def is_enabled(self, code: str) -> bool:
        return self.enabled.get(code, True)

    def priors_for(self, faculty: str | None) -> tuple[str, ...]:
        if not faculty:
            return ()
        direct = self.faculty_knowledge_priors.get(faculty)
        if direct is not None:
            return tuple(direct)
        lowered = faculty.casefold()
        for key, value in self.faculty_knowledge_priors.items():
            if key.casefold() == lowered:
                return tuple(value)
        return ()


def _zone_education(index: OccupationIndex, zone: int | None) -> str:
    if zone is None:
        return ""
    row = index.job_zone_reference.get(zone) or {}
    return (row.get("Education") or row.get("Name") or "").strip()


def apply_exclude_rules(
    occupation: IndexedOccupation,
    student: StudentFeatureVector,
    config: RuleConfig,
    index: OccupationIndex,
) -> list[RuleFiring]:
    firings: list[RuleFiring] = []
    code = occupation.onetsoc_code
    if config.is_enabled("R-DATA"):
        missing = [
            name
            for name in (
                "riasec",
                "sia",
                "essential_skills",
                "transferable_skills",
                "work_styles",
                "knowledge",
            )
            if not occupation.normalized.get(name)
        ]
        if (not occupation.record.knn_complete) or missing:
            firings.append(
                RuleFiring(
                    code="R-DATA",
                    onetsoc_code=code,
                    action=ACTION_EXCLUDE,
                    reason="Occupation is missing a required KNN domain vector",
                )
            )
    if config.is_enabled("R-ZONE-LOW") and occupation.record.job_zone == 2:
        firings.append(
            RuleFiring(
                code="R-ZONE-LOW",
                onetsoc_code=code,
                action=ACTION_EXCLUDE,
                reason="Job Zone 2 occupations are excluded for this undergraduate system",
            )
        )
    return firings


def apply_suppress_rules(
    occupation: IndexedOccupation,
    student: StudentFeatureVector,
    config: RuleConfig,
) -> list[RuleFiring]:
    if not config.is_enabled("R-SUPPRESS"):
        return []
    firings: list[RuleFiring] = []
    for block in student.knn_blocks().values():
        for element_id in block.element_ids:
            if (block.name, element_id) in occupation.suppressed:
                firings.append(
                    RuleFiring(
                        code="R-SUPPRESS",
                        onetsoc_code=occupation.onetsoc_code,
                        action=ACTION_DROP,
                        reason="Recommend Suppress: element dropped from pairwise comparison",
                        element_id=element_id,
                        domain=block.name,
                    )
                )
            elif (block.name, element_id) in occupation.not_relevant:
                firings.append(
                    RuleFiring(
                        code="R-SUPPRESS",
                        onetsoc_code=occupation.onetsoc_code,
                        action=ACTION_FLOOR,
                        reason="Not Relevant: importance treated as scale minimum 1.0",
                        element_id=element_id,
                        domain=block.name,
                    )
                )
    return firings


def apply_score_rules(
    occupation: IndexedOccupation,
    student: StudentFeatureVector,
    config: RuleConfig,
    index: OccupationIndex,
) -> list[RuleFiring]:
    firings: list[RuleFiring] = []
    code = occupation.onetsoc_code
    zone = occupation.record.job_zone

    if config.is_enabled("R-ZONE-5") and zone == 5 and student.profile.further_study == "no":
        education = _zone_education(index, 5)
        reason = "Job Zone 5 typically requires graduate or professional training"
        if education:
            reason = education
        firings.append(
            RuleFiring(
                code="R-ZONE-5",
                onetsoc_code=code,
                action=ACTION_FLAG,
                reason=reason,
            )
        )

    if (
        config.is_enabled("R-RELATED")
        and student.profile.course_relatedness == "related"
    ):
        prior_ids = config.priors_for(student.profile.faculty)
        if prior_ids:
            values = []
            knowledge_used = occupation.used_values.get("knowledge", {})
            for element_id in prior_ids:
                if ("knowledge", element_id) in occupation.suppressed:
                    continue
                value = knowledge_used.get(element_id)
                if value is not None:
                    values.append(value)
            if values:
                mean_im = sum(values) / len(values)
                if mean_im < config.related_im_threshold:
                    firings.append(
                        RuleFiring(
                            code="R-RELATED",
                            onetsoc_code=code,
                            action=ACTION_PENALISE,
                            penalty=config.related_penalty,
                            reason=(
                                f"Course-related preference: mean knowledge importance "
                                f"{mean_im:.2f} is below {config.related_im_threshold:.1f}"
                            ),
                        )
                    )

    if config.is_enabled("R-CONTEXT"):
        firings.extend(_context_firings(occupation, student, config))

    if (
        config.is_enabled("R-EDU")
        and student.profile.further_study == "no"
        and occupation.education_percents
    ):
        max_pct = max(occupation.education_percents.values())
        modes = {
            category
            for category, pct in occupation.education_percents.items()
            if pct == max_pct
        }
        if modes & PROFESSIONAL_EDUCATION_CATEGORIES:
            firings.append(
                RuleFiring(
                    code="R-EDU",
                    onetsoc_code=code,
                    action=ACTION_FLAG,
                    reason=(
                        "Incumbents most often report a first professional or doctoral degree"
                    ),
                )
            )
    return firings


def _context_firings(
    occupation: IndexedOccupation,
    student: StudentFeatureVector,
    config: RuleConfig,
) -> list[RuleFiring]:
    prefs = student.preferences
    cx = occupation.work_context_cx
    outdoor = cx.get(CONTEXT_OUTDOOR)
    indoor = cx.get(CONTEXT_INDOOR)
    public = cx.get(CONTEXT_PUBLIC)
    team = cx.get(CONTEXT_TEAM)
    firings: list[RuleFiring] = []

    outdoor_uncomfortable = (
        prefs.pref_outdoor is not None
        and prefs.pref_outdoor <= 2
        and outdoor is not None
        and outdoor >= config.outdoor_cx_threshold
    )
    indoor_mismatch = (
        prefs.pref_indoor is not None
        and prefs.pref_indoor >= 4
        and outdoor is not None
        and outdoor >= config.outdoor_cx_threshold
        and indoor is not None
        and indoor < config.indoor_cx_low
    )
    if outdoor_uncomfortable or indoor_mismatch:
        firings.append(
            RuleFiring(
                code="R-CONTEXT",
                onetsoc_code=occupation.onetsoc_code,
                action=ACTION_PENALISE,
                penalty=config.context_outdoor_penalty,
                reason="Work setting mismatch: occupation has high outdoor context",
                element_id=CONTEXT_OUTDOOR,
            )
        )

    if (
        prefs.pref_public is not None
        and prefs.pref_public <= 2
        and public is not None
        and public >= config.public_cx_threshold
    ):
        firings.append(
            RuleFiring(
                code="R-CONTEXT",
                onetsoc_code=occupation.onetsoc_code,
                action=ACTION_PENALISE,
                penalty=config.context_public_penalty,
                reason="Work setting mismatch: occupation has high public/customer contact",
                element_id=CONTEXT_PUBLIC,
            )
        )

    if (
        prefs.pref_team is not None
        and prefs.pref_team <= 2
        and team is not None
        and team >= config.team_cx_threshold
    ):
        firings.append(
            RuleFiring(
                code="R-CONTEXT",
                onetsoc_code=occupation.onetsoc_code,
                action=ACTION_PENALISE,
                penalty=config.context_team_penalty,
                reason="Work setting mismatch: occupation has very high team context",
                element_id=CONTEXT_TEAM,
            )
        )
    return firings


def filter_eligible(
    index: OccupationIndex,
    student: StudentFeatureVector,
    config: RuleConfig | None = None,
) -> tuple[list[str], list[RuleFiring]]:
    config = config or RuleConfig()
    eligible: list[str] = []
    firings: list[RuleFiring] = []
    for code, occupation in index.occupations.items():
        exclude = apply_exclude_rules(occupation, student, config, index)
        firings.extend(exclude)
        if any(item.action == ACTION_EXCLUDE for item in exclude):
            continue
        eligible.append(code)
    return eligible, firings


def combined_penalty(firings: list[RuleFiring]) -> float:
    factor = 1.0
    for item in firings:
        if item.action == ACTION_PENALISE and item.penalty is not None:
            factor *= item.penalty
    return factor
