"""Weighted-block cosine KNN against O*NET occupation profiles."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.neighbors import NearestNeighbors

from app.recommendation.catalog import IndexedOccupation, OccupationIndex
from app.recommendation.constants import ALLOWED_K, BLOCK_WEIGHTS, DEFAULT_K, KNN_BLOCKS
from app.recommendation.exceptions import AssessmentError
from app.recommendation.student_features import BlockVector, StudentFeatureVector

MISSING = -1.0


def l2_normalize(values: np.ndarray) -> np.ndarray | None:
    norm = float(np.linalg.norm(values))
    if norm == 0.0:
        return None
    return values / norm


class WeightedBlockCosineDistance:
    """Cosine distance on concat(sqrt(w) * L2(block)), with missing dims dropped."""

    def __init__(self, slices: list[tuple[int, int]], weights: list[float]) -> None:
        self.slices = slices
        self.weights = weights

    def __call__(self, u: np.ndarray, v: np.ndarray) -> float:
        similarity, _ = weighted_block_similarity(u, v, self.slices, self.weights)
        return 1.0 - similarity


def _present(values: np.ndarray) -> np.ndarray:
    return np.isfinite(values) & (values >= 0.0)


def weighted_block_similarity(
    u: np.ndarray,
    v: np.ndarray,
    slices: list[tuple[int, int]],
    weights: list[float],
) -> tuple[float, dict[str, float]]:
    student_parts: list[np.ndarray] = []
    occ_parts: list[np.ndarray] = []
    used_weights: list[float] = []
    block_cosines: dict[str, float] = {}
    for (start, end), weight, name in zip(slices, weights, KNN_BLOCKS, strict=True):
        uu = np.asarray(u[start:end], dtype=float)
        vv = np.asarray(v[start:end], dtype=float)
        mask = _present(uu) & _present(vv)
        if not np.any(mask):
            continue
        student_hat = l2_normalize(uu[mask])
        occ_hat = l2_normalize(vv[mask])
        if student_hat is None or occ_hat is None:
            continue
        block_cosines[name] = float(np.dot(student_hat, occ_hat))
        scale = np.sqrt(weight)
        student_parts.append(scale * student_hat)
        occ_parts.append(scale * occ_hat)
        used_weights.append(weight)
    if not student_parts:
        return 0.0, block_cosines
    weight_sum = float(sum(used_weights))
    if weight_sum <= 0:
        return 0.0, block_cosines
    factor = np.sqrt(1.0 / weight_sum)
    student_concat = np.concatenate(student_parts) * factor
    occ_concat = np.concatenate(occ_parts) * factor
    denom = float(np.linalg.norm(student_concat) * np.linalg.norm(occ_concat))
    if denom == 0.0:
        return 0.0, block_cosines
    similarity = float(np.dot(student_concat, occ_concat) / denom)
    similarity = max(0.0, min(1.0, similarity))
    return similarity, block_cosines


def _block_slices(student: StudentFeatureVector) -> list[tuple[int, int]]:
    slices: list[tuple[int, int]] = []
    cursor = 0
    for name in KNN_BLOCKS:
        length = len(student.blocks[name].element_ids)
        slices.append((cursor, cursor + length))
        cursor += length
    return slices


def pack_student(student: StudentFeatureVector) -> np.ndarray:
    return np.concatenate(
        [np.asarray(student.blocks[name].values, dtype=float) for name in KNN_BLOCKS]
    )


def pack_occupation(occupation: IndexedOccupation, student: StudentFeatureVector) -> np.ndarray:
    parts: list[np.ndarray] = []
    for name in KNN_BLOCKS:
        block: BlockVector = student.blocks[name]
        occ_map = occupation.normalized.get(name, {})
        row = []
        for element_id in block.element_ids:
            if (name, element_id) in occupation.suppressed:
                row.append(MISSING)
            else:
                value = occ_map.get(element_id)
                row.append(MISSING if value is None else float(value))
        parts.append(np.asarray(row, dtype=float))
    return np.concatenate(parts)


@dataclass(frozen=True)
class Neighbor:
    onetsoc_code: str
    distance: float
    raw_similarity: float
    block_cosines: dict[str, float]


def _validate_k(k: int) -> int:
    if k not in ALLOWED_K:
        raise AssessmentError(f"k must be one of {sorted(ALLOWED_K)}", "k")
    return k


def knn_neighbors(
    student: StudentFeatureVector,
    index: OccupationIndex,
    eligible_codes: list[str],
    *,
    k: int = DEFAULT_K,
) -> list[Neighbor]:
    if student.feature_version != index.feature_version:
        raise AssessmentError("Student and occupation feature versions do not match", "feature_version")
    k = _validate_k(k)
    if not eligible_codes:
        return []
    query = pack_student(student)
    if query.size == 0 or not np.any(_present(query)):
        raise AssessmentError("Student KNN vector is empty", "vector")
    matrix = np.vstack([pack_occupation(index.get(code), student) for code in eligible_codes])
    slices = _block_slices(student)
    weights = [BLOCK_WEIGHTS[name] for name in KNN_BLOCKS]
    n_neighbors = min(k, len(eligible_codes))
    metric = WeightedBlockCosineDistance(slices, weights)
    model = NearestNeighbors(
        n_neighbors=n_neighbors,
        metric=metric,
        algorithm="brute",
    )
    model.fit(matrix)
    distances, positions = model.kneighbors(query.reshape(1, -1), return_distance=True)
    neighbors: list[Neighbor] = []
    for distance, position in zip(distances[0], positions[0], strict=True):
        code = eligible_codes[int(position)]
        packed = matrix[int(position)]
        similarity, block_cosines = weighted_block_similarity(query, packed, slices, weights)
        neighbors.append(
            Neighbor(
                onetsoc_code=code,
                distance=float(distance),
                raw_similarity=similarity,
                block_cosines=block_cosines,
            )
        )
    return neighbors
