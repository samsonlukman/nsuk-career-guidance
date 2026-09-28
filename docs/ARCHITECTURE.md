# Architecture proposal

Status: specification **approved**. Ingest, student features, rule engine, KNN, and PostgreSQL schema are implemented. API and frontend are not built yet.

Canonical Version 1 specification: [FINAL_SPEC.md](FINAL_SPEC.md).

This document is the shorter stack/pipeline note. It does not claim that the web application or recommendation engine are already built.

## 1. Current project state

The workspace `/Users/apple/finalproject` was empty: no git repository, no framework, no dependencies, no database, no frontend or backend.

Reusable assets now present (data + planning only):

- Official O*NET 30.3 files under `data/raw/`
- Download script `scripts/download_onet.py`
- These architecture notes

## 2. Recommended stack

Keep the stack small enough to explain in a viva.

| Layer | Choice | Why |
|---|---|---|
| Backend | Python **FastAPI** | Natural fit for pandas/scikit-learn, easy to test, clear API boundary |
| Recommendation / ML | **scikit-learn** `NearestNeighbors` | Real KNN, not a hand-waved loop presented as ML |
| Data processing | pandas + numpy | O*NET files are tabular |
| Database | **PostgreSQL** | Proper relational model for users, assessments, occupations, recommendations |
| ORM / migrations | SQLAlchemy + Alembic | Explicit schema |
| Frontend | React + TypeScript (Vite) | Student and admin UI without extra frameworks |
| Auth | JWT + password hashing (bcrypt/argon2) | Students and admins in one API, role-based access |
| Config | `.env` | Secrets stay out of source |

Not proposed: neural networks, microservices, Redis, live O*NET Web Services as the runtime database, or a separate “AI API” product.

Django was a reasonable alternative because of its admin site. FastAPI is preferred so the recommendation package stays a plain Python module with tests, which is easier to defend as the AI component.

## 3. Repository layout (after approval)

```
backend/                 FastAPI app
  app/recommendation/    rules, features, KNN, explanations
  app/api/
  app/models/
frontend/                React student + admin UI
data/raw/                Official O*NET snapshot
data/processed/          Generated matrices/tables
scripts/                 download + preprocess
docs/
tests/                   especially recommendation tests
```

## 4. Recommendation pipeline

```
Student account
    → academic profile
    → career assessment questionnaire
    → raw responses stored
    → student feature vector (normalised)
    → rule-based expert filter / flags
    → remaining occupation vectors
    → KNN similarity (cosine, weighted blocks)
    → ranked occupations
    → top-N recommendations
    → feature-based explanations
    → optional relevance rating (evaluation)
```

Occupations are the **instances**. The student is a **query vector**. This is instance-based person–occupation matching, not classification into a tiny set of faculty labels.

### 4.1 Rule-based expert system

Rules are explicit objects (`code`, `priority`, `condition`, `action`, `explanation`), not scattered `if/else` in the KNN function.

Proposed production rules:

| Code | Condition | Action |
|---|---|---|
| R-DATA | Occupation missing a required domain vector | Exclude from KNN universe |
| R-SUPPRESS | Feature flagged `Recommend Suppress` or `Not Relevant` | Do not use that feature value |
| R-ZONE-LOW | Job Zone 2 and student is an undergraduate targeting graduate-level work | Exclude by default (configurable) |
| R-ZONE-5 | Job Zone 5 and student is not willing to pursue further study | Exclude or flag “typically requires postgraduate/professional training” |
| R-RELATED | Student chose “stay related to my course” and knowledge-prior similarity is below threshold | Penalise, do not silently drop |
| R-CONTEXT | Strong work-setting preference contradicts occupation Work Context | Penalise / optional exclude |
| R-EDU | Modal incumbent education is doctoral/professional and further study = No | Flag |

Exact Zone 5 behaviour (exclude vs flag) should be confirmed before coding. Flagging is safer academically: the system still shows medicine/law-type occupations to a 400-level student who might continue.

### 4.2 Feature representation

See `docs/FEATURE_MAPPING.md`.

Occupation vector blocks, all from O*NET 30.3:

1. RIASEC `OI` (6)
2. Specific Interest Areas `OI` (41; student vector is sparse)
3. Essential Skills `IM` (10)
4. Selected Transferable Skills `IM` (6)
5. Selected Work Styles `WI` mapped to `[0,1]` (6)
6. Knowledge `IM` (33; student vector is sparse from 5 selections + optional faculty prior)

Candidate occupations: **862** with complete ratings in the selected domains. Default rule filter leaves about **544** in Zones 3–5.

### 4.3 KNN

- Fit/store occupation matrix `X` of shape `(n_occupations, n_features)`
- Standardise **within each block** using occupation-set min/max (already bounded scales) rather than leaking student data into scaling
- Distance: `1 - S`, where `S` is a **weighted average of block cosine similarities**
- Implementation: scikit-learn `NearestNeighbors` on the concatenated weighted-normalised vector, metric `cosine`, algorithm `brute` (n ≈ 500–900, exact KNN is cheap)
- `k = 10` recommendations after rules
- Deterministic given the same questionnaire version and O*NET snapshot

Tests should cover: vector shape, normalisation bounds, a synthetic Investigative+IT profile ranking computing occupations above unrelated ones, and rule exclusion of Zone 2 when configured.

### 4.4 Explanations

Do not generate free-form LLM text in v1. Build explanations from ranked contributing features:

- Features where student and occupation are both high
- Official element names from Content Model Reference
- Official Job Zone education sentence
- Rule firing text

Example shape: “Software Developers was recommended because your profile is strongly Investigative, you selected Information Technology, and you rated Programming and Complex Problem Solving highly — those are also important in this occupation. Job Zone 4: considerable preparation, typically a bachelor's degree.”

## 5. Database schema (logical)

```
users
  id, email, password_hash, role(student|admin), is_active, created_at, last_login_at

student_profiles
  user_id, matric_number, first_name, last_name, faculty, department,
  level, further_study, course_relatedness

questions
  id, version, section, prompt, response_type, onet_element_id, onet_scale_id,
  block, weight, sort_order

assessments
  id, student_id, questionnaire_version, status, started_at, completed_at

assessment_responses
  id, assessment_id, question_id, onet_element_id, raw_value, normalized_value

occupations
  onetsoc_code PK, title, description, job_zone, recommendable

occupation_features
  onetsoc_code, domain, element_id, scale_id, data_value,
  not_relevant, recommend_suppress

occupation_vectors
  onetsoc_code, feature_version, vector (float array / json), updated_at

rules
  code PK, name, enabled, priority, params_json

rule_firings
  assessment_id, onetsoc_code, rule_code, action, reason

recommendations
  id, assessment_id, k, metric, feature_version, elapsed_ms, created_at

recommendation_items
  recommendation_id, onetsoc_code, rank, similarity, distance, explanation

recommendation_contributions
  item_id, element_id, student_value, occupation_value, contribution

recommendation_ratings
  item_id, student_id, relevance_1_to_5, comment, created_at

system_config
  key, value, updated_by, updated_at
```

Occupation titles live once in `occupations`. Feature ratings live in `occupation_features`. Vectors are a derived table/file keyed by `feature_version` so a new O*NET snapshot does not silently rewrite history.

## 6. Application features (v1)

Student: register, login, profile, take assessment, view recommendations with explanations, view occupation detail (O*NET description, job zone, top interests/skills/knowledge), view past assessments, rate recommendation relevance.

Admin: login, list users, inspect occupations/features, view recommendation activity, toggle rules, edit faculty→knowledge mapping, view ratings.

No extra modules for the sake of size.

## 7. Evaluation hooks

The architecture records:

- relevance ratings (1–5) per recommended occupation
- recommendation latency (`elapsed_ms`)
- questionnaire version and feature version

Later evaluation can add a System Usability Scale form and a small counsellor-agreement study. **No accuracy number should be claimed until that work is done.**

Synthetic profile tests are part of software testing, not field accuracy.

## 8. Decisions locked in FINAL_SPEC (change only if you reject them)

1. FastAPI + PostgreSQL + React, rather than Django.
2. Default candidate pool = Job Zones 3–5, with Zone 5 flagged rather than hidden.
3. Omit Abilities from KNN in v1.
4. No historical Work Values from older O*NET releases.
5. Faculty→knowledge prior as an explicit, editable admin table.
6. Cosine / weighted-block KNN with k=10.
7. Official NSUK department list still needs confirmation before it is hard-coded.
