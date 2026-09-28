# Processed occupational features

This directory holds **generated** tables. Do not edit them by hand.

```bash
python3 scripts/ingest_onet.py
```

writes `data/processed/onet_30_3_v1/` from the official files in `data/raw/db_30_3_text/`.

Ingest never writes to `data/raw/`.

## Output (`onet_30_3_v1/`)

| File | Contents |
|---|---|
| `metadata.json` | Feature version, source SHA-256 hashes, counts, block element IDs, official scale bounds |
| `occupations.csv` | All Occupation Data rows plus job zone, `knn_complete`, `recommendable` (Zones 3–5 and complete) |
| `occupation_features.csv` | Long-format ratings for KNN-complete occupations |
| `matrix_*.csv` | Wide matrices (one row per complete occupation; empty cell = Recommend Suppress) |
| `job_zone_reference.csv` | Official zone definitions |
| `education_categories.csv` | Official education category labels |

KNN matrices: `riasec`, `sia`, `knowledge`, `essential_skills`, `transferable_skills`, `work_styles`.

Rule/explanation matrices: `work_context`, `work_activities`.

Education stays in long-form `occupation_features.csv` only (one row per occupation × category). A wide matrix would collapse the 12 education categories.

Abilities and Work Values are not written.
