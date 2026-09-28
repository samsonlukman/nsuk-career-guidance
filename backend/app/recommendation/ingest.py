"""Build the O*NET 30.3 occupational feature snapshot.

Reads official files from data/raw/ (never writes there) and writes versioned
tables under data/processed/onet_30_3_v1/.
"""

from __future__ import annotations

from pathlib import Path

from app.recommendation.constants import (
    BLOCK_WEIGHTS,
    EDUCATION_ELEMENT_ID,
    EXPECTED_KNOWLEDGE_COUNT,
    EXPECTED_SIA_COUNT,
    EXPECTED_WORK_ACTIVITY_COUNT,
    FEATURE_VERSION,
    KNN_DOMAIN_FILES,
    ONET_RELEASE,
    WORK_CONTEXT_IDS,
)
from app.recommendation.onet_io import (
    discover_element_ids,
    element_names,
    load_job_zones,
    load_occupation_data,
    load_ratings,
    load_scales,
    load_tsv,
    verify_raw_dir,
)
from app.recommendation.preprocess import (
    build_occupation_records,
    occupations_with_all_elements,
    process_ratings,
)
from app.recommendation.snapshot import (
    BlockSpec,
    ProcessedSnapshot,
    empty_snapshot_timestamp,
    write_snapshot,
)


def run_ingest(raw_dir: Path, output_dir: Path) -> ProcessedSnapshot:
    raw_dir = raw_dir.resolve()
    output_dir = output_dir.resolve()
    if output_dir.is_relative_to(raw_dir) or raw_dir.is_relative_to(output_dir):
        raise ValueError("Processed output must not be inside the raw O*NET directory")

    source_files = verify_raw_dir(raw_dir)
    scales = load_scales(raw_dir)
    occupation_data = load_occupation_data(raw_dir)
    job_zones = load_job_zones(raw_dir)

    knn_rows: dict[str, list] = {}
    knn_elements: dict[str, tuple[str, ...]] = {}
    knn_names: dict[str, dict[str, str]] = {}
    complete_sets: dict[str, set[str]] = {}

    for domain, (filename, scale_id, fixed_ids) in KNN_DOMAIN_FILES.items():
        rows = load_ratings(raw_dir / filename, scale_id=scale_id, element_ids=fixed_ids)
        discovered = discover_element_ids(rows) if fixed_ids is None else tuple(fixed_ids)
        if domain == "sia" and len(discovered) != EXPECTED_SIA_COUNT:
            raise ValueError(
                f"Specific Interest Areas: expected {EXPECTED_SIA_COUNT} elements, found {len(discovered)}"
            )
        if domain == "knowledge" and len(discovered) != EXPECTED_KNOWLEDGE_COUNT:
            raise ValueError(
                f"Knowledge: expected {EXPECTED_KNOWLEDGE_COUNT} elements, found {len(discovered)}"
            )
        knn_rows[domain] = rows
        knn_elements[domain] = discovered
        knn_names[domain] = element_names(rows)
        complete_sets[domain] = occupations_with_all_elements(rows, discovered)

    knn_complete = set.intersection(*complete_sets.values()) if complete_sets else set()

    work_activities = load_ratings(
        raw_dir / "Work Activities.txt",
        scale_id="IM",
    )
    activity_ids = discover_element_ids(work_activities)
    if len(activity_ids) != EXPECTED_WORK_ACTIVITY_COUNT:
        raise ValueError(
            f"Work Activities: expected {EXPECTED_WORK_ACTIVITY_COUNT} elements, found {len(activity_ids)}"
        )

    work_context = load_ratings(
        raw_dir / "Work Context.txt",
        scale_id="CX",
        element_ids=WORK_CONTEXT_IDS,
    )
    education = load_ratings(
        raw_dir / "Education.txt",
        scale_id="RL",
        element_ids=(EDUCATION_ELEMENT_ID,),
        require_category=True,
    )

    occupations = build_occupation_records(
        occupation_data=occupation_data,
        job_zones=job_zones,
        knn_complete=knn_complete,
        education_codes={row.onetsoc_code for row in education},
        work_context_codes=occupations_with_all_elements(work_context, WORK_CONTEXT_IDS),
    )

    features = []
    blocks: dict[str, BlockSpec] = {}
    for domain, (filename, scale_id, _fixed) in KNN_DOMAIN_FILES.items():
        processed = process_ratings(
            knn_rows[domain],
            domain=domain,
            scale_id=scale_id,
            scales=scales,
            include_in_knn=True,
        )
        # Keep KNN-complete occupations only in the feature table for vector domains.
        keep = knn_complete
        features.extend(row for row in processed if row.onetsoc_code in keep)
        blocks[domain] = BlockSpec(
            name=domain,
            weight=BLOCK_WEIGHTS[domain],
            scale_id=scale_id,
            element_ids=knn_elements[domain],
            element_names=knn_names[domain],
            include_in_knn=True,
        )

    features.extend(
        row
        for row in process_ratings(
            work_context,
            domain="work_context",
            scale_id="CX",
            scales=scales,
            include_in_knn=False,
        )
        if row.onetsoc_code in knn_complete
    )
    blocks["work_context"] = BlockSpec(
        name="work_context",
        weight=None,
        scale_id="CX",
        element_ids=WORK_CONTEXT_IDS,
        element_names=element_names(work_context),
        include_in_knn=False,
    )

    features.extend(
        row
        for row in process_ratings(
            work_activities,
            domain="work_activities",
            scale_id="IM",
            scales=scales,
            include_in_knn=False,
        )
        if row.onetsoc_code in knn_complete
    )
    blocks["work_activities"] = BlockSpec(
        name="work_activities",
        weight=None,
        scale_id="IM",
        element_ids=activity_ids,
        element_names=element_names(work_activities),
        include_in_knn=False,
    )

    education_processed = process_ratings(
        education,
        domain="education",
        scale_id="RL",
        scales=scales,
        include_in_knn=False,
    )
    features.extend(row for row in education_processed if row.onetsoc_code in knn_complete)
    blocks["education"] = BlockSpec(
        name="education",
        weight=None,
        scale_id="RL",
        element_ids=(EDUCATION_ELEMENT_ID,),
        element_names=element_names(education) or {EDUCATION_ELEMENT_ID: "Required Level of Education"},
        include_in_knn=False,
    )

    knn_complete_rows = [row for row in occupations if row.knn_complete]
    zone_counts = {2: 0, 3: 0, 4: 0, 5: 0}
    for row in knn_complete_rows:
        if row.job_zone in zone_counts:
            zone_counts[row.job_zone] += 1

    snapshot = ProcessedSnapshot(
        feature_version=FEATURE_VERSION,
        onet_release=ONET_RELEASE,
        created_at=empty_snapshot_timestamp(),
        source_files=source_files,
        occupations=occupations,
        features=features,
        blocks=blocks,
        counts={
            "occupation_data": len(occupation_data),
            "knn_complete": len(knn_complete),
            "recommendable_zones_3_5": sum(1 for row in occupations if row.recommendable),
            "knn_complete_zone_2": zone_counts[2],
            "knn_complete_zone_3": zone_counts[3],
            "knn_complete_zone_4": zone_counts[4],
            "knn_complete_zone_5": zone_counts[5],
            "knn_complete_with_education": sum(1 for row in knn_complete_rows if row.has_education),
            "knn_complete_with_work_context": sum(
                1 for row in knn_complete_rows if row.has_work_context
            ),
            "occupation_feature_rows": len(features),
        },
        job_zone_reference=load_tsv(raw_dir / "Job Zone Reference.txt"),
        education_categories=load_tsv(raw_dir / "Education Categories.txt"),
        scales=scales,
    )
    write_snapshot(snapshot, output_dir)
    return snapshot


def default_raw_dir(repo_root: Path) -> Path:
    return repo_root / "data" / "raw" / "db_30_3_text"


def default_output_dir(repo_root: Path) -> Path:
    return repo_root / "data" / "processed" / FEATURE_VERSION
