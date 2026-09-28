# AI-Powered Personalized Career Guidance System

Final-year Computer Science project for undergraduate students of **Nasarawa State University, Keffi (NSUK)**.

The system is intended to complement professional career counselling, not replace counsellors.

**Current status:** O*NET ingest, recommendation pipeline, PostgreSQL schema, FastAPI API, secure authentication, the student assessment and recommendation UI, persisted explanations/ratings, and an admin dashboard are in place. The system is being prepared for evaluation. See [docs/EVALUATION.md](docs/EVALUATION.md).

## What is in this repository now

- Official O*NET 30.3 snapshot and download script
- Ingest/preprocessing pipeline (`scripts/ingest_onet.py`)
- Versioned processed occupation tables (`data/processed/onet_30_3_v1/` after ingest)
- Ingest, student features, named rule engine, and KNN pipeline
- PostgreSQL schema and Alembic migrations
- FastAPI application with cookie-based authentication
- React + TypeScript website (`frontend/`)
- Automated tests for ingest, recommendation pipeline, API, and frontend

Read this first:

- [docs/FINAL_SPEC.md](docs/FINAL_SPEC.md) — **canonical specification for approval**
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — stack notes
- [docs/ONET_DATA.md](docs/ONET_DATA.md) — file inspection notes
- [docs/FEATURE_MAPPING.md](docs/FEATURE_MAPPING.md) — questionnaire mapping (superseded in detail by FINAL_SPEC)
- [docs/DATABASE.md](docs/DATABASE.md) — PostgreSQL schema and migrations
- [docs/AUTH.md](docs/AUTH.md) — cookie sessions and authorization
- [docs/EVALUATION.md](docs/EVALUATION.md) — evaluation environment, export, and limitations

## Data

Occupational records come from the official O*NET 30.3 database (CC BY 4.0). They are not typed in by hand.

```bash
python3 scripts/download_onet.py
python3 scripts/ingest_onet.py
```

## Proposed hybrid AI method

1. **Rule-based expert system** — eligibility and constraints (job zone, data quality, course-relatedness, work context)
2. **K-Nearest Neighbour** — similarity ranking of O*NET occupation profiles against the student feature vector

See [docs/FINAL_SPEC.md](docs/FINAL_SPEC.md), [docs/DATABASE.md](docs/DATABASE.md), and [docs/AUTH.md](docs/AUTH.md).

## Attribution

This project uses the O*NET 30.3 Database by the U.S. Department of Labor, Employment and Training Administration, licensed under CC BY 4.0.
