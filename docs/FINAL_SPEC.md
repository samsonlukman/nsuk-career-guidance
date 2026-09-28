# Final technical specification

**Status:** Version 1 specification **approved** (20 August 2026). Implementation is in progress, starting with O*NET ingest and occupational feature representation.

**Inspection date:** 20 August 2026  
**O*NET release:** 30.3 (May 2026)  
**Source files:** `data/raw/db_30_3_text/`  
**License:** CC BY 4.0 (U.S. Department of Labor / O*NET Resource Center)

This specification is based only on files that were downloaded and parsed. No O*NET fields, occupations, or mappings are invented. Work Values are absent from 30.3 and are not used.

---

## 1. File verification

`Read Me.txt` states: O*NET 30.3 Database, May 2026 Release.

All required files are present, UTF-8, tab-delimited, and parse as valid CSV with the official headers. Record counts below are data rows (excluding the header).

| File | Bytes | Readable | Occupations | Notes |
|---|---:|---|---:|---|
| Occupation Data.txt | 265,794 | yes | 1,016 | Titles and descriptions |
| Career Interest Types.txt | 629,058 | yes | 923 | RIASEC + high-points |
| Specific Interest Areas.txt | 4,563,781 | yes | 891 | 41 interest areas (new in 30.3) |
| Knowledge.txt | 5,605,166 | yes | 894 | 33 knowledge areas |
| Essential Skills.txt | 1,539,626 | yes | 894 | 10 skills (new in 30.3) |
| Transferable Skills.txt | 4,105,406 | yes | 894 | 25 skills (new in 30.3) |
| Work Styles.txt | 2,279,557 | yes | 891 | 21 styles; WI −3..+3 |
| Work Activities.txt | 8,749,064 | yes | 894 | 41 General Work Activities |
| Abilities.txt | 8,557,526 | yes | 894 | 52 abilities; IM/LV |
| Work Context.txt | 36,782,933 | yes | 894 | 57 context elements; CX/CXP |
| Work Context Categories.txt | 23,269 | yes | n/a | Category labels |
| Job Zones.txt | 28,028 | yes | 923 | Zones 2, 3, 4, 5 |
| Job Zone Reference.txt | 3,660 | yes | n/a | 4 zone definitions |
| Education.txt | 1,108,076 | yes | 878 | Required education % |
| Education Categories.txt | 1,823 | yes | n/a | 12 education categories |
| Content Model Reference.txt | 234,750 | yes | n/a | Official element IDs/names |
| Scales Reference.txt | 950 | yes | n/a | Scale min/max |
| Training and Experience.txt | 2,525,556 | yes | 878 | Display on occupation pages |
| Occupation Level Metadata.txt | 2,621,846 | yes | 878 | Survey administration only |
| Work Values.txt | — | **absent** | — | Not in 30.3; do not import 29.x |

Primary identifier on every occupation-level file: **`O*NET-SOC Code`**. Join to `Occupation Data.txt` for title and description.

---

## 2. Data inventory

Join key everywhere: `O*NET-SOC Code`.

### 2.1 Occupation Data.txt — 1,016 records

- Fields: `O*NET-SOC Code`, `Title`, `Description`
- Role: occupation identity, recommendation labels, explanation text
- Relationship: parent table for all other occupation files

### 2.2 Career Interest Types.txt — 8,307 records / 923 occupations

- Fields: `O*NET-SOC Code`, `Element ID`, `Element Name`, `Scale ID`, `Data Value`, `Date`, `Domain Source`
- Elements: Realistic `1.B.1.a` … Conventional `1.B.1.f`; high-points `1.B.1.g/h/i`
- Scales: `OI` Occupational Interests **1–7**; `IH` high-point **0–6**
- Observed `OI` range in file: 1.0–7.0
- Domain source in this release: mostly `Machine Learning/Expert` (7,839 rows) and `Machine Learning` (468). That is official metadata, not this project’s model.
- Relationship: Holland RIASEC profile per occupation

### 2.3 Specific Interest Areas.txt — 73,062 records / 891 occupations

- 41 elements under `1.B.3.*` (Mechanics/Electronics … Social Service)
- Scales: `OI` 1–7 (ratings); `DS` Summary Display Rank 0–100 (display only)
- Relationship: finer interest taxonomy under Career Interest Types

### 2.4 Knowledge.txt — 59,004 records / 894 occupations

- 33 elements `2.C.*`
- Scales: `IM` Importance **1–5**; `LV` Level **0–7**
- Flags: `Recommend Suppress` Y = 4,880; `Not Relevant` Y = 6,037
- Relationship: worker requirements; academic/field fit

### 2.5 Essential Skills.txt — 17,880 records / 894 occupations

- 10 elements `2.A.1.a`–`2.A.2.d` (Reading Comprehension … Monitoring)
- Scales: `IM` 1–5, `LV` 0–7
- Flags: suppress Y = 16; not relevant Y = 285
- Relationship: basic skills required across occupations

### 2.6 Transferable Skills.txt — 44,700 records / 894 occupations

- 25 elements `2.B.*`
- Scales: `IM` 1–5, `LV` 0–7
- Flags: suppress Y = 131; not relevant Y = 3,098
- Relationship: cross-occupation skills (social, technical, resource management)

### 2.7 Work Styles.txt — 37,422 records / 891 occupations

- 21 elements `1.D.*`
- Scales: `WI` Work Styles Impact **−3 to +3** (observed −1.42 to 3.0); `DR` Distinctiveness Rank 0–10 (display)
- Conceptual meaning: how beneficial/detrimental the style is for the occupation, not a typical-incumbent personality score
- Relationship: worker characteristics

### 2.8 Work Activities.txt — 73,308 records / 894 occupations

- 41 General Work Activities `4.A.*`
- Scales: `IM` 1–5, `LV` 0–7
- Relationship: what the job involves; explanations, not the full questionnaire

### 2.9 Abilities.txt — 92,976 records / 894 occupations

- 52 elements `1.A.*` (cognitive, psychomotor, physical, sensory)
- Scales: `IM` 1–5, `LV` 0–7
- Flags: suppress Y = 68; not relevant Y = 7,410
- Relationship: worker requirements; many items are not valid as short student self-report

### 2.10 Work Context.txt — 297,676 records / 894 occupations

- 57 elements `4.C.*`
- Scales: `CX` Context **1–5** (occupation-level mean); `CXP` category percents 0–100; some items use `CT`/`CTP`
- Selected CX ranges: indoor 1.03–5.0; outdoor 1.0–5.0; team 1.86–5.0; public 1.09–4.99
- Relationship: work setting; preference rules, not the KNN vector

### 2.11 Job Zones.txt — 923 records

- Fields: `O*NET-SOC Code`, `Job Zone`, `Date`, `Domain Source`
- Values present: **2, 3, 4, 5** only. Zone 1 was merged into “Job Zone 1-2”.
- Full-file counts: Zone 2 = 331, Zone 3 = 212, Zone 4 = 226, Zone 5 = 154
- Relationship: preparation/education eligibility

### 2.12 Job Zone Reference.txt — 4 records

- Official education/experience wording used in explanations and rules

### 2.13 Education.txt — 11,100 records / 878 occupations

- Element `2.D.1` Required Level of Education; scale `RL` = percent of incumbents in 12 categories
- Category 6 = Bachelor's Degree (from Education Categories.txt)
- Also `2.D.4.a` Job-Related Professional Certification (`IM`)
- Relationship: display and optional education flags; 16 of the 862 KNN-complete occupations have no Education row

### 2.14 Reference / metadata (not occupation profiles)

- Content Model Reference: 3,006 elements — official names/descriptions for questions and explanations
- Scales Reference: 32 scales — official min/max for normalisation
- Occupation Level Metadata: survey administration
- Training and Experience: related experience / OJT distributions for occupation pages

### 2.15 Coverage used by Version 1 KNN

Intersection of Career Interest Types ∩ Specific Interest Areas ∩ Knowledge ∩ Essential Skills ∩ Transferable Skills ∩ Work Styles = **862 occupations**.

That set also has Work Activities, Abilities, Work Context, and Job Zones (862). Education is present for 846 of them.

Job Zone split of the 862:

| Zone | Official name | Count |
|---|---|---:|
| 2 | Very Little to Some Preparation | 318 |
| 3 | Medium Preparation | 196 |
| 4 | Considerable Preparation (most require bachelor's) | 202 |
| 5 | Extensive Preparation (most require graduate/professional school) | 146 |

Default undergraduate pool after R-ZONE-LOW: Zones 3–5 = **544**.

---

## 3. Which datasets belong in this system

Criterion: a student at NSUK must be able to answer the item honestly in a short questionnaire, and the answer must correspond to an actual O*NET 30.3 field that occupations also have.

| Domain | Use in Version 1 | Reason |
|---|---|---|
| Career Interest Types (RIASEC) | **KNN** | Classic person–occupation interest match; 6 items; same `OI` 1–7 scale |
| Specific Interest Areas | **KNN (sparse)** | Finer than RIASEC; 41 official areas; student picks ≤5 |
| Essential Skills | **KNN** | 10 questionnaire-friendly skills; `IM` 1–5 |
| Transferable Skills (6 of 25) | **KNN** | Discriminating, self-ratable skills; omit equipment/repair items |
| Work Styles (6 of 21) | **KNN** | Self-describable characteristics; map student Likert to `WI` |
| Knowledge (sparse 33) | **KNN + optional rule prior** | Maps to academic strengths; student picks ≤5 |
| Job Zones + Education | **Rules + explanation** | Eligibility, not similarity dimensions |
| Work Context (4 of 57) | **Rules** | Setting preferences; CX is occupational context, not a student trait |
| Occupation Data | **Identity / copy** | Title and description |
| Work Activities | **Explanation only** | 41 items is too long for the assessment |
| Abilities | **Occupation page only** | 52 items; many physical/sensory; poor unvalidated self-report |
| Work Values | **Do not use** | File and Content Model `1.C` absent in 30.3 |
| Training and Experience | **Occupation page only** | Incumbent experience, not a student vector |
| Occupation Level Metadata | **Unused** | Survey administration |
| Software Skills / Tasks | **Not in this download set / later pages** | Not required for v1 matching |
| CGPA | **Not an O*NET field** | Optional profile storage only; never a KNN dimension |

---

## 4. Version 1 KNN features (exact)

All numeric transforms use **official scale bounds** from `Scales Reference.txt`, not empirical min/max.

Block weights are configuration (sum to 1.00), not trained parameters.

| Block | Weight | Dims | File | Field | Type | Numeric form | Student source |
|---|---:|---:|---|---|---|---|---|
| RIASEC | 0.25 | 6 | Career Interest Types | `OI` on `1.B.1.a`–`1.B.1.f` | float | `(x-1)/6` → [0,1] | 6 Likert items, same 1–7 wording |
| Specific Interest Areas | 0.20 | ≤5 used | Specific Interest Areas | `OI` on selected `1.B.3.*` | float | `(x-1)/6`; cosine **only on selected IDs** | Pick ≤5 of 41, then rate 1–7 |
| Essential Skills | 0.20 | 10 | Essential Skills | `IM` on `2.A.1.a`–`2.A.2.d` | float | `(x-1)/4` → [0,1] | 10 skill ratings 1–5 |
| Transferable Skills | 0.15 | 6 | Transferable Skills | `IM` on IDs below | float | `(x-1)/4` | 6 skill ratings 1–5 |
| Work Styles | 0.10 | 6 | Work Styles | `WI` on IDs below | float | occupation `(wi+3)/6`; student `(x-1)/4` | 6 “this describes me” 1–5 |
| Knowledge | 0.10 | ≤5 used | Knowledge | `IM` on selected `2.C.*` | float | `(x-1)/4`; cosine **only on selected IDs** | Pick ≤5 of 33, then rate 1–5 |

### Transferable Skills included (and why the other 19 are not)

Included:

- `2.B.2.i` Complex Problem Solving
- `2.B.3.e` Programming
- `2.B.1.e` Instructing
- `2.B.1.c` Persuasion
- `2.B.1.d` Negotiation
- `2.B.5.a` Time Management

Omitted from the questionnaire: equipment selection/installation/maintenance/repair/operation, operations monitoring, quality control, technology design, operations/systems analysis, and resource-management skills. Those exist in the file but are poor undergraduate self-ratings or overlap the selected items.

### Work Styles included

- `1.D.1.a` Innovation
- `1.D.1.b` Achievement Orientation
- `1.D.1.i` Leadership Orientation
- `1.D.2.d` Cooperation
- `1.D.3.b` Attention to Detail
- `1.D.4.a` Stress Tolerance

### Missing-value handling (from actual flags)

For Knowledge, Essential Skills, and Transferable Skills:

- `Not Relevant = Y` → treat occupation `IM` as **1.0** (minimum importance) for that element
- `Recommend Suppress = Y` → **drop that element from the pairwise comparison** for that occupation (do not use a fabricated rating)

High-points (`IH`), display ranks (`DS`, `DR`), and Level (`LV`) are **not** KNN inputs. `LV` is shown on occupation pages if needed.

---

## 5. Student assessment mapping

Every scored item maps to an element that exists in the downloaded files. Academic profile items are **not** O*NET fields and are not KNN dimensions.

Student Likert labels should use Content Model names. Exact prompt text can be edited at implementation time; element IDs cannot.

### 5.1 Academic profile (rules only)

| Student question | Response | Internal feature | O*NET feature | Transform | KNN |
|---|---|---|---|---|---|
| Faculty | one of 11 official NSUK faculties | `faculty` | none | categorical | no |
| Department / programme | text or confirmed lookup | `department` | none | categorical | no |
| Current level | 100 / 200 / 300 / 400 | `level` | none | stored | no |
| Willing to pursue postgraduate or professional training? | Yes / Maybe / No | `further_study` | Job Zone 5 education text | rule R-ZONE-5 | no |
| Prefer careers related to my course, or open to other fields? | related / open | `course_relatedness` | Knowledge `IM` via admin prior table | rule R-RELATED | no |

NSUK faculties (official academics page): Administration; Agriculture; Arts; Communication and Media Studies; Education; Engineering; Environmental Sciences; Law; Natural and Applied Sciences; Social Sciences; College of Medicine and Health Allied Sciences.

Department names are **not** hard-coded until confirmed from NSUK. Faculty → knowledge prior is an **editable admin table**, not an O*NET file.

### 5.2 RIASEC (KNN)

Scale: 1 = Strongly dislike this type of work … 7 = Strongly like this type of work (same bounds as `OI`).

| Question (intent) | Scale | Internal | O*NET | Transform | KNN |
|---|---|---|---|---|---|
| Enjoy realistic work (tools, machines, outdoor/physical, building/repairing) | 1–7 | `interest_realistic` | Career Interest Types `1.B.1.a` `OI` | `(x-1)/6` | RIASEC block |
| Enjoy investigative work (research, analysis, science) | 1–7 | `interest_investigative` | `1.B.1.b` `OI` | `(x-1)/6` | RIASEC |
| Enjoy artistic work (design, writing, performance, original work) | 1–7 | `interest_artistic` | `1.B.1.c` `OI` | `(x-1)/6` | RIASEC |
| Enjoy social work (helping, teaching, counselling) | 1–7 | `interest_social` | `1.B.1.d` `OI` | `(x-1)/6` | RIASEC |
| Enjoy enterprising work (leading, selling, persuading, business) | 1–7 | `interest_enterprising` | `1.B.1.e` `OI` | `(x-1)/6` | RIASEC |
| Enjoy conventional work (records, procedures, structured data work) | 1–7 | `interest_conventional` | `1.B.1.f` `OI` | `(x-1)/6` | RIASEC |

### 5.3 Specific Interest Areas (KNN, sparse)

UI: show the **41 official `Element Name` values** from Specific Interest Areas.txt. Student selects up to 5, then rates each 1–7.

| Question | Scale | Internal | O*NET | Transform | KNN |
|---|---|---|---|---|---|
| Select up to 5 specific interest areas, then rate enjoyment | 1–7 on selected | `sia_<element_id>` | Specific Interest Areas `1.B.3.*` `OI` | selected `(x-1)/6`; **unselected excluded from this block** | SIA subset cosine |

If the student selects fewer than 5, use only those dimensions. Selecting 0 is invalid (require ≥1).

### 5.4 Essential Skills (KNN)

Scale: 1 = Very limited current skill … 5 = Very strong current skill (same bounds as `IM`).

| Question | Internal | O*NET Element ID | Transform |
|---|---|---|---|
| Reading comprehension | `skill_reading` | `2.A.1.a` | `(x-1)/4` |
| Active listening | `skill_listening` | `2.A.1.b` | `(x-1)/4` |
| Writing | `skill_writing` | `2.A.1.c` | `(x-1)/4` |
| Speaking | `skill_speaking` | `2.A.1.d` | `(x-1)/4` |
| Mathematics | `skill_math` | `2.A.1.e` | `(x-1)/4` |
| Science | `skill_science` | `2.A.1.f` | `(x-1)/4` |
| Critical thinking | `skill_critical_thinking` | `2.A.2.a` | `(x-1)/4` |
| Active learning | `skill_active_learning` | `2.A.2.b` | `(x-1)/4` |
| Learning strategies | `skill_learning_strategies` | `2.A.2.c` | `(x-1)/4` |
| Monitoring (checking progress/quality) | `skill_monitoring` | `2.A.2.d` | `(x-1)/4` |

### 5.5 Transferable Skills (KNN)

Same 1–5 skill scale → `(x-1)/4`.

| Question | Internal | Element ID |
|---|---|---|
| Complex problem solving | `skill_problem_solving` | `2.B.2.i` |
| Programming | `skill_programming` | `2.B.3.e` |
| Instructing / teaching others | `skill_instructing` | `2.B.1.e` |
| Persuasion | `skill_persuasion` | `2.B.1.c` |
| Negotiation | `skill_negotiation` | `2.B.1.d` |
| Time management | `skill_time_management` | `2.B.5.a` |

### 5.6 Work Styles (KNN)

Student: 1 = Does not describe me … 5 = Describes me very well.  
Occupation: `WI` −3..+3 → `(wi+3)/6`.

| Question | Internal | Element ID |
|---|---|---|
| I am inventive and like new ways of doing work | `style_innovation` | `1.D.1.a` |
| I set demanding goals and work hard to reach them | `style_achievement` | `1.D.1.b` |
| I am comfortable taking charge and leading | `style_leadership` | `1.D.1.i` |
| I enjoy cooperating and helping colleagues | `style_cooperation` | `1.D.2.d` |
| I am thorough and pay attention to detail | `style_detail` | `1.D.3.b` |
| I stay effective under stress | `style_stress` | `1.D.4.a` |

### 5.7 Knowledge (KNN, sparse)

UI: 33 official knowledge `Element Name` values from Knowledge.txt. Pick ≤5, rate 1–5 (same bounds as `IM`).

| Question | Internal | O*NET | Transform | KNN |
|---|---|---|---|---|
| Select up to 5 knowledge areas you are strongest in / enjoy studying | `knowledge_<element_id>` | Knowledge `2.C.*` `IM` | selected `(x-1)/4`; unselected excluded from this block | Knowledge subset cosine |

Require ≥1 selection.

### 5.8 Work setting preferences (rules only)

Student 1–5 preference. Occupation comparison uses Work Context **`CX` (1–5)**, Category `n/a` (the occupation mean, not CXP percents).

| Question | Internal | Element ID | Element name | Rule use |
|---|---|---|---|---|
| I prefer mostly indoor, office-type settings | `pref_indoor` | `4.C.2.a.1.a` | Indoors, Environmentally Controlled | R-CONTEXT |
| I am comfortable working outdoors / in the field | `pref_outdoor` | `4.C.2.a.1.c` | Outdoors, Exposed to All Weather Conditions | R-CONTEXT |
| I prefer working as part of a team | `pref_team` | `4.C.1.b.1.e` | Work With or Contribute to a Work Group or Team | R-CONTEXT (mild; CX min already 1.86) |
| I am comfortable dealing with the public / customers | `pref_public` | `4.C.1.b.1.f` | Deal With External Customers or the Public in General | R-CONTEXT |

CXP category labels exist (Never…Every day for indoor/outdoor; Not important…Extremely important for team/public). They are for occupation-page display, not student questions.

**Item count:** 5 profile + 6 RIASEC + up to 5 SIA + 10 essential + 6 transferable + 6 styles + up to 5 knowledge + 4 context = **about 47 prompts**, of which **33 are always shown** and 10 are “pick then rate”.

Intentionally not asked: 52 abilities, 41 GWAs as Likert, Work Values, CGPA as a matcher.

---

## 6. Rule-based component

Rules are named objects (`code`, `enabled`, `priority`, `params`, `action`, `explanation`). They run **before** KNN, except penalties that adjust the similarity score after distance is computed.

They exist to enforce eligibility and data integrity. They are not a second “smart” ranker.

| Code | Filters / flags | Information used | Interaction with occupations |
|---|---|---|---|
| R-DATA | Exclude | Presence of all six KNN domain vectors | Occupation missing any required domain is not a neighbour |
| R-SUPPRESS | Feature-level | `Recommend Suppress`, `Not Relevant` | Drop or floor that element; occupation may still remain |
| R-ZONE-LOW | Exclude by default | `Job Zones.txt` zone = 2; student is an NSUK undergraduate | Removes 318 of 862 (high-school / little-preparation jobs) |
| R-ZONE-5 | **Flag, do not hide** (default) | Job Zone = 5; `further_study` | If No: keep occupation, attach official Zone 5 education sentence. If Yes/Maybe: no flag |
| R-RELATED | Penalise, do not drop | `course_relatedness` = related; faculty→knowledge prior table; occupation Knowledge `IM` | If mean IM on prior knowledge IDs (not relevant→1.0) < 3.0, multiply score by 0.80 |
| R-CONTEXT | Penalise, do not drop | Student prefs vs occupation `CX` | See formulas below |
| R-EDU | Flag only | Education.txt `2.D.1` RL category 10 or 11 modal if available; `further_study` = No | Flag professional/doctoral-typical occupations; skip if Education row missing (16 occupations) |

### R-CONTEXT formulas (using CX 1–5)

- If `pref_outdoor ≤ 2` and outdoor `CX ≥ 4.0` → penalty 0.85
- If `pref_indoor ≥ 4` and outdoor `CX ≥ 4.0` and indoor `CX < 3.0` → penalty 0.85 (do not double-apply with the previous; take the stronger single outdoor penalty)
- If `pref_public ≤ 2` and public `CX ≥ 4.0` → penalty 0.90
- Team: apply only if `pref_team ≤ 2` and team `CX ≥ 4.5` → penalty 0.95 (weak, because almost every occupation has substantial team context)

Penalties multiply: `score' = score * Π p_i`. Multiple distinct rules can fire; the same outdoor mismatch fires once.

Admin can disable any rule. Default R-ZONE-LOW is on.

No rules for CGPA, gender, religion, or invented Nigerian salary/demand.

---

## 7. KNN component

**Problem type:** instance-based person–occupation matching. Occupations are instances. The student is a query. This is not classification into faculty labels.

### 7.1 Student feature vector

Ordered blocks, after transforms to [0,1]:

1. RIASEC — 6 floats, always present
2. SIA — 1–5 floats, only selected element IDs, stored with those IDs
3. Essential Skills — 10 floats, fixed ID order
4. Transferable Skills — 6 floats, fixed ID order
5. Work Styles — 6 floats, fixed ID order
6. Knowledge — 1–5 floats, only selected element IDs

`feature_version = onet_30_3_v1`

### 7.2 Occupational feature vector

Same blocks and IDs. For SIA and Knowledge blocks, **slice to the student’s selected IDs** before cosine (subset match). Occupation values come from the 30.3 files after R-SUPPRESS handling.

### 7.3 Preprocessing

1. Load official TSVs from `data/raw/db_30_3_text/`
2. Keep occupations in the 862-complete set
3. Pivot each domain to occupation × element
4. Apply Not Relevant / Suppress
5. Min–max with official scale bounds
6. Persist `occupation_features` and derived `occupation_vectors` keyed by `feature_version`

Do not refit scaling on the student. Do not call live O*NET Web Services at recommendation time.

### 7.4 Scaling / normalisation

- Per-element min–max using official min/max
- Then **L2-normalise each block** (skip a block if the student vector is all zeros — should not happen if validation works)
- Concatenate `sqrt(w_b) * block_hat` so cosine of the concatenation equals the weighted sum of block cosines

If a block is skipped (e.g. suppress removed all comparable skills for one occupation), renormalise remaining block weights to sum to 1 for that pairwise comparison.

### 7.5 Distance metric

Cosine distance on the concatenated weighted blocks:

- `similarity = 1 - cosine_distance`
- Implementation: scikit-learn `NearestNeighbors(metric="cosine", algorithm="brute")` on the eligible occupation matrix after the same concatenation

Brute force is appropriate: n ≈ 544 after R-ZONE-LOW.

Why cosine: Holland-style matching is about profile **shape**. Limitation: a student who rates all skills low can still match high-importance occupations if relative peaks align. Document this; do not silently switch to Euclidean in v1.

### 7.6 K

- Default **k = 10**
- Configurable range **{5, 10, 15}**
- If eligible occupations < k, return all eligible

### 7.7 Selection

1. Apply exclude-rules → eligible set E
2. Compute cosine neighbours among E
3. Take the k smallest cosine distances

### 7.8 Ranking

1. `raw_similarity = 1 - distance`
2. `recommendation_score = raw_similarity * Π(rule penalties)`
3. Sort by `recommendation_score` descending
4. Ties: higher RIASEC block cosine, then `O*NET-SOC Code` ascending (deterministic)

### 7.9 Displayed scores

- Store `distance`, `raw_similarity`, `recommendation_score`
- UI: `round(recommendation_score * 100)` as “match score”, with a caption that this is similarity, not predicted job success

---

## 8. Complete pipeline

```
Student account
  → academic profile (faculty, programme, level, further_study, course_relatedness)
  → assessment (raw answers stored)
  → validated responses → student feature vector (onet_30_3_v1)
  → load occupation feature table (same version)
  → rule-based filtering (R-DATA, R-ZONE-LOW) → eligible occupations
  → KNN cosine on weighted blocks
  → apply score penalties (R-RELATED, R-CONTEXT) and flags (R-ZONE-5, R-EDU)
  → rank by recommendation_score
  → join Occupation Data (title, description)
  → explanations from contributing elements + Job Zone text + fired rules
  → top-k ranked careers
  → optional relevance rating (1–5) for later evaluation
```

Explanation construction (no LLM in v1):

- RIASEC types where student OI-equivalent ≥ 5 and occupation OI ≥ 5
- Selected SIA/knowledge IDs where occupation OI/IM is in the occupation’s top values
- Skills where both student and occupation [0,1] values are ≥ 0.6
- Top 5 Work Activities by occupation `IM` (from Work Activities.txt) as “this job involves…”
- Official Job Zone education sentence
- Text of any fired rule

---

## 9. Database schema

PostgreSQL. O*NET titles stored once. Vectors derived and versioned.

```
users
  id, email, password_hash, role (student|admin), is_active, created_at, last_login_at

student_profiles
  user_id FK, matric_number UNIQUE, first_name, last_name,
  faculty, department, level, further_study, course_relatedness

questions
  id, version, section, prompt, response_type,
  onet_element_id NULL, onet_scale_id NULL, block, sort_order, is_required

assessments
  id, student_id FK, questionnaire_version, feature_version,
  status (in_progress|completed), started_at, completed_at

assessment_responses
  id, assessment_id FK, question_id FK, onet_element_id,
  raw_value, normalized_value

occupations
  onetsoc_code PK, title, description, job_zone, recommendable

occupation_features
  onetsoc_code FK, domain, element_id, element_name, scale_id,
  data_value, not_relevant, recommend_suppress, source_date, domain_source

occupation_vectors
  onetsoc_code FK, feature_version, vector (json/float[]), updated_at

faculty_knowledge_priors
  faculty, element_id, element_name, created_at
  -- admin-editable; not from O*NET

rules
  code PK, name, enabled, priority, params_json, explanation_template

rule_firings
  assessment_id, onetsoc_code, rule_code, action (exclude|penalise|flag),
  penalty, reason

recommendations
  id, assessment_id FK, k, metric, feature_version, elapsed_ms, created_at

recommendation_items
  id, recommendation_id FK, onetsoc_code, rank,
  distance, raw_similarity, recommendation_score, explanation

recommendation_contributions
  item_id FK, block, element_id, student_value, occupation_value, contribution

recommendation_ratings
  item_id FK, student_id FK, relevance_1_to_5, comment, created_at

system_config
  key PK, value_json, updated_by, updated_at
  -- k, block weights, zone policy
```

---

## 10. Application architecture (to implement after approval)

**Stack**

| Layer | Choice |
|---|---|
| Backend | Python FastAPI |
| KNN | scikit-learn `NearestNeighbors` |
| Processing | pandas, numpy |
| Database | PostgreSQL + SQLAlchemy + Alembic |
| Frontend | React + TypeScript (Vite) |
| Auth | JWT, password hashing (argon2/bcrypt), role-based access |
| Config | environment variables; no secrets in source |

Not in v1: neural nets, microservices, Redis, live O*NET APIs, LLM explanations.

**Repository modules (future)**

```
backend/app/core/             config, security
backend/app/models/           SQLAlchemy
backend/app/api/              auth, profile, assessment, recommend, occupations, admin
backend/app/recommendation/   ingest, features, rules, knn, explain
backend/app/schemas/
frontend/                     student + admin UI
scripts/                      download_onet.py, ingest_onet.py
data/raw/                     official snapshot
data/processed/               derived matrices
tests/recommendation/         vector shape, rules, synthetic profiles
docs/                         this spec
```

**Student features (later):** register/login, profile, take assessment, view ranked careers with explanations, occupation detail (O*NET description, zone, top interests/skills/knowledge/activities), history, rate relevance.

**Admin features (later):** login, users, inspect occupations/features, toggle rules, edit faculty–knowledge priors, view ratings and latency. No extra modules for size.

**Runtime data flow:** ingest O*NET → PostgreSQL `occupations` / `occupation_features` → build versioned vectors → API builds student vector → rules → KNN → persist recommendations.

---

## 11. Weaknesses, assumptions, limitations

1. **US taxonomy.** O*NET describes US occupations. Nigerian demand, salary, and licensing are not in the files and will not be invented.
2. **Self-report.** Skill and style items are not validated tests. Students may over- or under-rate.
3. **Work Styles conceptual mismatch.** `WI` is occupational impact, not incumbent personality. Matching is still person–job fit, but it is not the older work-style level construct.
4. **Interest ratings origin.** Career Interest Types in 30.3 are labelled Machine Learning/Expert. Disclose this in the dissertation.
5. **Work Values absent.** Cannot use Holland/O*NET work values without mixing database versions.
6. **Abilities omitted.** Physical/sensory self-ratings are indefensible; cognitive abilities overlap skills.
7. **Cosine ignores magnitude.** Profile shape can match even when absolute skill ratings are low.
8. **Sparse SIA/knowledge.** Unselected areas are excluded from those blocks; an occupation strong in unselected areas is not penalised there (RIASEC still constrains broadly).
9. **Job Zone 2 exclusion.** Some legitimate technical/vocational paths are hidden. Configurable, but the default is undergraduate-oriented.
10. **Zone 5 flag vs hide.** Default is flag. Hiding would drop 146 occupations including many professional careers NSUK students pursue.
11. **Education coverage gap.** 16 KNN-complete occupations lack Education.txt rows; R-EDU skips them.
12. **Faculty→knowledge prior is ours.** O*NET does not know NSUK programmes. The table must stay editable and labelled as project configuration.
13. **No accuracy claim.** Ratings and counsellor agreement come after implementation. Synthetic profile tests are software tests, not field accuracy.
14. **k and weights are untrained.** Starting values for a viva-defensible system; they belong in `system_config`.
15. **Snapshot freeze.** Recommendations are only as current as O*NET 30.3 (May 2026). Updating requires a new `feature_version` and re-ingest.

---

## Approval checkpoint

Implementation of frontend, questionnaire UI, and the live recommendation engine waits on approval of this specification.

Locked recommendations unless you change them:

1. FastAPI + PostgreSQL + React
2. Candidate pool = Job Zones 3–5; Zone 5 flagged, not hidden
3. Abilities not in KNN
4. No O*NET 29.x Work Values
5. Faculty→knowledge prior as an admin table
6. Weighted-block cosine, k = 10
7. NSUK department list confirmed before it is hard-coded
