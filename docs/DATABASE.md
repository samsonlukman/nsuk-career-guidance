# PostgreSQL schema

Occupational rows are loaded from the processed O*NET snapshot. The FastAPI foundation reads this database; it does not parse raw TSV files.

## Connection

Copy `.env.example` to `.env` and set `DATABASE_URL`. Do not put credentials in source code.

Default local URL (Postgres.app / peer auth, no password):

```
postgresql+psycopg://apple@localhost:5432/nsuk_career
```

Development (`nsuk_career`) and automated tests share operational rows. Formal evaluation uses a separate database, `nsuk_career_eval`. See [EVALUATION.md](EVALUATION.md).

## Create the database

```bash
createdb nsuk_career
createdb nsuk_career_test
createdb nsuk_career_eval
```

## Run migrations

From the repository root:

```bash
cd backend
DATABASE_URL=postgresql+psycopg://apple@localhost:5432/nsuk_career alembic upgrade head
```

Rollback:

```bash
DATABASE_URL=postgresql+psycopg://apple@localhost:5432/nsuk_career alembic downgrade -1
```

## Load processed O*NET 30.3

Do not load raw TSV files into PostgreSQL. After ingest (`python3 scripts/ingest_onet.py`) and migrations:

```bash
python3 scripts/load_onet_db.py
```

This upserts `onet_snapshots`, `occupations`, `occupation_features`, `job_zone_definitions`, and `education_categories` for `feature_version=onet_30_3_v1`. It is safe to re-run. Use `--force-features` only to replace feature rows.

## What is stored

Processed occupational rows for runtime use (occupations, long-format features, job-zone and education labels) keyed by `onet_snapshots.feature_version`. Raw O*NET TSV files stay in `data/raw/`. Wide CSV matrices stay in `data/processed/` and are not copied into PostgreSQL.

Faculty → knowledge priors start **empty**. Do not seed NSUK faculties.

Questionnaire questions live in `questions` / `question_options`. They are not hard-coded in Python.

Historical recommendation runs keep foreign keys to the snapshot, questionnaire version, and occupation row that produced them. A later O*NET ingest creates a new snapshot rather than overwriting old occupation rows.
