# Evaluation readiness

This document prepares the system for a later formal evaluation. It does **not** contain evaluation results, accuracy claims, or approved NSUK faculty mappings.

The recommendation method is unchanged: O*NET 30.3, `questionnaire_v1`, `config_v1`, approved feature engineering, named rules, and KNN. Scores remain occupational **profile similarity**, not predicted job success.

Do not collect real evaluation participants until this document has been reviewed.

## 1. Test data vs evaluation data

| Database | Purpose |
|---|---|
| `nsuk_career` | Local development and FastAPI automated tests. Contains leftover test users, assessments, runs, ratings, and unverified faculty-prior rows. **Do not treat this database as evaluation data.** |
| `nsuk_career_test` | Isolated schema/Alembic tests. Wiped by schema tests. |
| `nsuk_career_eval` | Clean evaluation environment. Starts with schema, O*NET 30.3, `questionnaire_v1`, `config_v1`, and system configuration. Student operational tables start empty. |

Automated API tests write to `nsuk_career` through `RUNTIME_DATABASE_URL`. That is why a separate evaluation database is required. Do not delete development rows to “clean” evaluation. Point the API at `nsuk_career_eval` instead.

Default URLs (Postgres.app / peer auth):

```
DATABASE_URL=postgresql+psycopg://apple@localhost:5432/nsuk_career
TEST_DATABASE_URL=postgresql+psycopg://apple@localhost:5432/nsuk_career_test
EVALUATION_DATABASE_URL=postgresql+psycopg://apple@localhost:5432/nsuk_career_eval
```

## 2. Evaluation environment setup

Prerequisites: PostgreSQL running, processed snapshot at `data/processed/onet_30_3_v1/`, Python virtualenv.

```bash
export EVALUATION_CONFIRM=I_UNDERSTAND
export EVALUATION_DATABASE_URL=postgresql+psycopg://apple@localhost:5432/nsuk_career_eval

python3 scripts/evaluation.py init
python3 scripts/evaluation.py status
```

`init` will:

1. Refuse any database whose name is `nsuk_career`, `nsuk_career_test`, or does not end in `_eval`
2. Create `nsuk_career_eval` if it does not exist
3. Apply Alembic migrations (schema, `questionnaire_v1`, recommendation configuration, system configuration)
4. Load the processed O*NET 30.3 snapshot
5. Leave `faculty_knowledge_priors` empty
6. Leave student / assessment / recommendation / rating tables empty

Start the API against the evaluation database (do not rely on the development `.env` `DATABASE_URL`):

```bash
cd backend
DATABASE_URL=postgresql+psycopg://apple@localhost:5432/nsuk_career_eval \
  ../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The Vite app on `http://localhost:5173` proxies `/api` to that process.

### Administrator account

Public registration always creates a **student**. Create an admin only through the approved CLI, which hashes the password with Argon2id:

```bash
export EVALUATION_CONFIRM=I_UNDERSTAND
export EVALUATION_DATABASE_URL=postgresql+psycopg://apple@localhost:5432/nsuk_career_eval
export EVAL_ADMIN_EMAIL='your-admin@example.edu'
export EVAL_ADMIN_PASSWORD='a-long-password-typed-in-the-shell'
python3 scripts/evaluation.py create-admin
```

Do not put the password in source, `.env.example`, or this file. Do not pass it on the command line (`ps` can see argv).

## 3. Faculty knowledge priors

The table is **configuration**, not test data, but it starts empty by design.

No officially approved NSUK faculty → O*NET knowledge mapping has been supplied. The evaluation database therefore has **zero** faculty-prior rows. Do not invent NSUK mappings.

The development database `nsuk_career` may still contain leftover browser/test rows (for example Natural and Applied Sciences → `2.C.3.a` from Step 14 verification). Those rows are **not** approved academic configuration and were **not** copied into `nsuk_career_eval`.

## 4. Reset / rebuild

There is **no** public HTTP reset endpoint.

Return evaluation student activity to zero while keeping schema, O*NET, questionnaire, recommendation configuration, system configuration, and admin accounts:

```bash
export EVALUATION_CONFIRM=I_UNDERSTAND
export EVALUATION_DATABASE_URL=postgresql+psycopg://apple@localhost:5432/nsuk_career_eval
python3 scripts/evaluation.py reset-students --yes
```

Safeguards:

- Database name must end with `_eval`
- `nsuk_career` and `nsuk_career_test` are always refused
- Mutating commands also require `EVALUATION_CONFIRM=I_UNDERSTAND`
- `--yes` is required for `reset-students`

To rebuild from scratch, drop only the evaluation database after a conscious check of the name, then run `init` again. Do not drop `nsuk_career`.

## 5. Immutability and traceability

A completed `recommendation_runs` row stores:

- `student_user_id`
- `assessment_id`
- `questionnaire_version_id`
- `onet_snapshot_id`
- `config_id`
- `feature_version`
- `created_at`
- `k`, `metric`, `weights_json`, `elapsed_ms`

Child rows store ranked items (SOC, similarity, final score, explanation), contributions, and rule firings (flags / penalties). Retrieval reads those stored foreign keys and stored scores. A later O*NET ingest is designed to add a new snapshot rather than overwrite historical occupation rows. Do not rewrite completed runs.

## 6. Determinism (not accuracy)

With the same questionnaire answers and unchanged O*NET snapshot, questionnaire version, recommendation configuration, feature version, and rule configuration, two submissions produced the same ranking.

Checked on `nsuk_career_eval` with a fixed complete `questionnaire_v1` payload:

| Check | Result |
|---|---|
| Ranked SOC codes | identical |
| Ranks | identical |
| Raw similarity scores | identical |
| Final recommendation scores | identical |
| Rule flags / penalties | identical |

SOC order from that verification payload (not an evaluation sample):

`15-1221.00`, `19-1029.04`, `15-2041.01`, `19-2012.00`, `15-1254.00`, `19-2011.00`, `19-1042.00`, `17-2031.00`, `15-1241.00`, `15-1252.00`

Re-run:

```bash
export EVALUATION_CONFIRM=I_UNDERSTAND
export EVALUATION_DATABASE_URL=postgresql+psycopg://apple@localhost:5432/nsuk_career_eval
python3 scripts/evaluation.py determinism
python3 scripts/evaluation.py reset-students --yes
```

Determinism means the pipeline is stable. It is **not** statistical accuracy, career-prediction quality, or evidence that the occupations are “correct” for a student.

## 7. Evaluation export

```bash
export EVALUATION_DATABASE_URL=postgresql+psycopg://apple@localhost:5432/nsuk_career_eval
python3 scripts/evaluation.py export
```

Writes gitignored files under `data/evaluation/exports/evaluation_export_<UTC>/`:

- `recommendation_items.csv`
- `recommendation_items.json`
- `manifest.json`

One row per recommendation item.

| Field | Meaning |
|---|---|
| `participant_id` | Pseudonymous `P-` + SHA-256 prefix of the internal user id. Not an email. |
| `assessment_id` | Assessment UUID |
| `recommendation_run_id` | Run UUID |
| `recommendation_item_id` | Item UUID |
| `rank` | 1..k |
| `onetsoc_code` | O*NET-SOC |
| `occupation_title` | Occupation title from the stored snapshot row |
| `raw_similarity` | KNN similarity |
| `recommendation_score` | Final score after rules |
| `relevance_rating_1_to_5` | Student relevance rating, or empty |
| `feedback_comment` | Optional comment |
| `run_created_at` | Run timestamp |
| `questionnaire_version` | e.g. `questionnaire_v1` |
| `onet_release` | e.g. `30.3` |
| `feature_version` | e.g. `onet_30_3_v1` |
| `config_version` | e.g. `config_v1` |
| `elapsed_ms` | Stored generation time |
| `faculty`, `department`, `level` | Optional academic context from the student profile, not personal names |

Never exported: passwords, password hashes, session cookies, JWTs, `AUTH_SECRET`, email addresses, first/last names, matriculation numbers.

The 1–5 rating is **relevance feedback**, not prediction accuracy.

## 8. Planned evaluation metrics

Do not invent an accuracy metric. The system is prepared to support later analysis of:

**A. Recommendation relevance** using the existing 1–5 item rating:

1. Not relevant  
2. Slightly relevant  
3. Moderately relevant  
4. Relevant  
5. Highly relevant  

**B. System usability** (to be collected later, not implemented as a product feature and not fabricated here):

- ease of completing the assessment
- clarity of recommendations
- ease of navigation
- usefulness
- overall satisfaction

**C. Technical performance** — `recommendation_runs.elapsed_ms` stores generation time. Client-side timings can be recorded during evaluation sessions. Local numbers below are a development baseline only.

## 9. Privacy

Collected because it is required for operation or evaluation:

| Data | Why |
|---|---|
| Email + Argon2id password hash | Authentication |
| Optional name / matriculation number | Account/profile operation; **not** exported |
| Faculty, department, level, further-study, course-relatedness | Assessment / recommendation inputs |
| Questionnaire responses | Generate and persist the recommendation |
| Recommendation run, items, explanations, scores | Show results and analyse ranking |
| 1–5 relevance rating + optional comment | Later relevance analysis |
| Session cookie (httpOnly JWT) | Keep the student signed in |

The analysis export uses a pseudonymous participant id. Administrators can see emails in the operational admin UI so they can support participants; that is not the research export.

Do not add unnecessary personal-data fields.

## 10. Security checklist

| Check | Status |
|---|---|
| Assessment submission requires authentication | Yes (401 without session) |
| Student cannot read another student's run | Yes (403) |
| Student cannot call admin APIs | Yes (403, database role) |
| Admin APIs check `users.role == admin` | Yes; JWT `role` claim is not the authorization source |
| Passwords stored as Argon2id | Yes (`$argon2id$`) |
| Session cookie httpOnly | Yes (`nsuk_session`) |
| Session cookie SameSite=Lax | Yes |
| Production Secure cookie | Set `AUTH_COOKIE_SECURE=true` when serving HTTPS. Local HTTP leaves it false. |
| `AUTH_SECRET` from environment | Yes; `.env` is gitignored |
| Raw database errors hidden | Yes; generic `internal_error` |
| Admin APIs omit password hashes | Yes |
| Client-supplied `role` on register ignored | Yes; always `student` |
| IDOR on recommendation runs | Owner or admin only |

### CSRF

Authentication uses a cookie, so CSRF matters.

- `SameSite=Lax` prevents a typical cross-site form POST from sending `nsuk_session`.
- Cookie-authenticated mutations also reject a present `Origin` that is not in `CORS_ORIGINS`. The test client and some same-origin clients may omit `Origin`; those are allowed.

That combination is **defense in depth**, not comprehensive CSRF protection. Residual risks include same-site attackers, XSS, and a later change to `SameSite=None`. A dedicated CSRF token was not added (that would be a larger product change).

## 11. Database integrity

`python3 scripts/evaluation.py integrity` checks orphans, duplicate ranks/occupations/ratings, duplicate SOC codes within a snapshot, questionnaire consistency, run traceability, faculty-prior element ids, and questionnaire O*NET element references.

On the clean evaluation database after `init`, all checks passed (count 0).

Historical development rows in `nsuk_career` were not rewritten.

## 12. Development performance baseline

Collected with FastAPI `TestClient` against `nsuk_career_eval` on a local machine. **DEVELOPMENT BASELINE only.** Not production performance, not an SLA, not evidence of scale.

| Operation | n | min ms | median ms | max ms |
|---|---|---|---|---|
| Questionnaire retrieval | 3 | 23.4 | 27.9 | 59.3 |
| Assessment submit + recommendation generation (HTTP) | 3 | 324.9 | 401.7 | 1280.5 |
| Stored `elapsed_ms` (generation only) | 3 | 177 | 261 | 374 |
| Recommendation retrieval | 3 | 45.1 | 45.8 | 55.9 |

Re-run: `python3 scripts/evaluation.py baseline` (requires `EVALUATION_CONFIRM` and then `reset-students`).

## 13. Browser verification (not evaluation)

A clean-environment walkthrough used **new** accounts on `nsuk_career_eval`, not the earlier Amina / Chioma / `admin@example.com` development users.

Verified:

1. Student registration
2. Login
3. Complete `questionnaire_v1` (39 questions)
4. Submit
5. Real recommendation run (10 occupations, versions `questionnaire_v1` / `onet_30_3_v1` / `config_v1`)
6. Open recommendations
7. Open career details (explanations, contributions, job zone)
8. Submit a 1–5 relevance rating (UI states it is not accuracy)
9. Logout
10. Login again
11. Recommendation history still present
12. A second student received 403 for the first student's run
13. Admin dashboard showed stored activity counts
14. A student opening `/admin` was kept on the student dashboard; admin APIs returned 403

Those verification accounts were removed with `reset-students` so formal evaluation can start from zero student records. They are not evaluation results.

## 14. Limitations

- No formal participants have been recruited.
- No relevance, usability, or performance **evaluation** results exist yet.
- Determinism is not accuracy.
- Local timings are not production performance.
- Faculty-prior table is empty until a validated mapping is supplied.
- CSRF protections are not a complete anti-forgery design.
- Development/test data in `nsuk_career` must never be mixed into evaluation analysis.

## 15. Commands reference

```bash
export EVALUATION_CONFIRM=I_UNDERSTAND
export EVALUATION_DATABASE_URL=postgresql+psycopg://apple@localhost:5432/nsuk_career_eval

python3 scripts/evaluation.py status
python3 scripts/evaluation.py init
python3 scripts/evaluation.py create-admin
python3 scripts/evaluation.py reset-students --yes
python3 scripts/evaluation.py export
python3 scripts/evaluation.py integrity
python3 scripts/evaluation.py determinism
python3 scripts/evaluation.py baseline
```
