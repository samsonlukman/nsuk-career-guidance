"""Assessment → features → rules → KNN → penalties/flags → ranked recommendations."""

from __future__ import annotations

from dataclasses import dataclass

from app.recommendation.catalog import OccupationIndex
from app.recommendation.constants import DEFAULT_K, FEATURE_VERSION
from app.recommendation.explain import RecommendationExplanation, explain_recommendation
from app.recommendation.knn import Neighbor, knn_neighbors
from app.recommendation.rules import (
    RuleConfig,
    RuleFiring,
    apply_score_rules,
    apply_suppress_rules,
    combined_penalty,
    filter_eligible,
)
from app.recommendation.student_features import StudentAssessment, StudentFeatureVector, build_student_vector


@dataclass(frozen=True)
class RankedRecommendation:
    rank: int
    onetsoc_code: str
    title: str
    description: str
    job_zone: int | None
    distance: float
    raw_similarity: float
    recommendation_score: float
    block_cosines: dict[str, float]
    firings: list[RuleFiring]
    explanation: RecommendationExplanation


@dataclass(frozen=True)
class RecommendationResult:
    feature_version: str
    k: int
    metric: str
    student: StudentFeatureVector
    eligible_count: int
    exclude_firings: list[RuleFiring]
    items: list[RankedRecommendation]
    notes: tuple[str, ...] = (
        "Scores are O*NET profile similarity, not predicted job success or accuracy.",
    )


def recommend(
    assessment: StudentAssessment,
    index: OccupationIndex,
    *,
    k: int = DEFAULT_K,
    rule_config: RuleConfig | None = None,
) -> RecommendationResult:
    config = rule_config or RuleConfig()
    student = build_student_vector(assessment, index.catalog)
    eligible, exclude_firings = filter_eligible(index, student, config)
    neighbors = knn_neighbors(student, index, eligible, k=k)
    pending: list[tuple[float, float, str, Neighbor, list[RuleFiring]]] = []
    for neighbor in neighbors:
        occupation = index.get(neighbor.onetsoc_code)
        firings = [
            *apply_suppress_rules(occupation, student, config),
            *apply_score_rules(occupation, student, config, index),
        ]
        penalty = combined_penalty(firings)
        score = neighbor.raw_similarity * penalty
        riasec = neighbor.block_cosines.get("riasec", 0.0)
        pending.append((score, riasec, neighbor.onetsoc_code, neighbor, firings))

    pending.sort(key=lambda row: (-row[0], -row[1], row[2]))
    items: list[RankedRecommendation] = []
    for rank, (score, _riasec, code, neighbor, firings) in enumerate(pending, start=1):
        occupation = index.get(code)
        items.append(
            RankedRecommendation(
                rank=rank,
                onetsoc_code=code,
                title=occupation.record.title,
                description=occupation.record.description,
                job_zone=occupation.record.job_zone,
                distance=neighbor.distance,
                raw_similarity=neighbor.raw_similarity,
                recommendation_score=score,
                block_cosines=neighbor.block_cosines,
                firings=firings,
                explanation=explain_recommendation(
                    student, occupation, index, firings, neighbor.block_cosines
                ),
            )
        )
    return RecommendationResult(
        feature_version=FEATURE_VERSION,
        k=k,
        metric="weighted-block cosine (sklearn NearestNeighbors, algorithm=brute)",
        student=student,
        eligible_count=len(eligible),
        exclude_firings=exclude_firings,
        items=items,
    )
