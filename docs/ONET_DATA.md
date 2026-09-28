# O*NET 30.3 inspection notes

Inspection date: 20 August 2026 (full-file verification after download complete)  
Official source: [O*NET Resource Center Database page](https://www.onetcenter.org/database.html)  
Release: **O*NET 30.3** (May 2026)  
Format downloaded: official tab-delimited text files  
Dictionary: https://www.onetcenter.org/dictionary/30.3/text/  
License: [CC BY 4.0](https://www.onetcenter.org/license_db.html)

These notes record what was actually present in the downloaded files. They are not a substitute for the official data dictionary.

## Files inspected

| File | Rows (data) | Occupations | Role in this project |
|---|---:|---:|---|
| Occupation Data.txt | 1,016 | 1,016 | Titles and descriptions |
| Career Interest Types.txt | 8,307 | 923 | RIASEC interest profiles (KNN) |
| Specific Interest Areas.txt | 73,062 | 891 | 41 finer interest areas (KNN + explanation) |
| Knowledge.txt | 59,004 | 894 | 33 knowledge areas (KNN/rules) |
| Essential Skills.txt | 17,880 | 894 | 10 essential skills (KNN) |
| Transferable Skills.txt | 44,700 | 894 | 25 transferable skills (subset in KNN) |
| Work Styles.txt | 37,422 | 891 | 21 work styles (subset in KNN) |
| Job Zones.txt | 923 | 923 | Education/training filter (rules) |
| Job Zone Reference.txt | 4 | n/a | Zone definitions |
| Education.txt | 11,100 | 878 | Required education frequencies (rules/display) |
| Education Categories.txt | 12 | n/a | Education category labels |
| Content Model Reference.txt | 3,006 | n/a | Official element names/descriptions |
| Scales Reference.txt | 32 | n/a | Scale IDs and ranges |
| Training and Experience.txt | 26,025 | 878 | Experience/training (display, not KNN) |
| Occupation Level Metadata.txt | 32,202 | 878 | Collection metadata only |
| Work Context Categories.txt | 281 | n/a | Labels for work-preference rules |
| Work Context.txt | 297,676 | 894 | 57 context elements; selected items for preference rules |
| Work Activities.txt | 73,308 | 894 | 41 General Work Activities (explanations) |
| Abilities.txt | 92,976 | 894 | 52 abilities; display only in v1 |
| Read Me.txt | n/a | n/a | Confirms version 30.3, May 2026 |

All files required for the proposed architecture are present and parse cleanly. Re-run `python3 scripts/download_onet.py` to refresh the snapshot.

## Occupation coverage

The O*NET-SOC taxonomy in Occupation Data contains **1,016** occupations. Not every occupation has ratings in every domain.

Verified overlap for the proposed KNN domains:

- Career Interest Types ∩ Knowledge ∩ Essential Skills ∩ Transferable Skills ∩ Work Styles ∩ Specific Interest Areas = **862 occupations**

Job Zone split of that 862-occupation set:

- Zone 2 (very little to some preparation): 318
- Zone 3 (medium preparation): 196
- Zone 4 (considerable / typically bachelor's): 202
- Zone 5 (extensive / typically graduate or professional): 146

Default undergraduate candidate pool is proposed as Zones **3–5** (544 occupations), with Zone 5 flagged when further study is typically required.

## Important fields by domain

### Occupation Data

- `O*NET-SOC Code`, `Title`, `Description`

### Career Interest Types (formerly “Interests” before 30.3)

- Elements: Realistic, Investigative, Artistic, Social, Enterprising, Conventional, plus three high-point codes
- Scales: `OI` Occupational Interests (1–7); `IH` high-point (0–6)
- Use `OI` for the six RIASEC dimensions. Do not put high-point codes in the KNN vector; they are derived ranks.
- Domain source in this release is predominantly `Machine Learning/Expert` or `Machine Learning`. This must be disclosed in the dissertation.

### Specific Interest Areas (new in 30.3)

- 41 areas such as Information Technology, Teaching/Education, Law, Agriculture, Medical Science
- Scale `OI` (1–7) is the rating to use
- Scale `DS` is a display rank, not a KNN feature

### Knowledge, Essential Skills, Transferable Skills

- Shared rating columns: `Scale ID`, `Data Value`, `Recommend Suppress`, `Not Relevant`
- Scales: `IM` Importance (1–5) and `LV` Level (0–7, observed maxima vary)
- **Use Importance (`IM`) for KNN**, not Level. Importance is more compatible with a short student self-rating. Level is better as an explanation/detail field.
- `Not Relevant = Y` and `Recommend Suppress = Y` must be handled in preprocessing. Knowledge in particular has thousands of such flags.

### Work Styles (redesigned in 30.x)

- 21 styles (Innovation, Dependability, Stress Tolerance, etc.)
- Scale `WI` Work Styles Impact (−3 to +3): how beneficial or detrimental the style is for the occupation
- Scale `DR` Distinctiveness Rank (0–10): display/ranking metadata, not a KNN value
- Conceptual note: WI is occupational *need/benefit*, not a typical-incumbent personality score. Matching a student’s self-description to WI is still a reasonable person–job fit interpretation, but it is not identical to older O*NET work-style “level” ratings.

### Work Activities (General Work Activities)

- 41 elements, Importance (`IM` 1–5) and Level (`LV`)
- Use **Importance** plus official element names for explanations (“this occupation involves analysing data, teaching others, working with computers”)
- Do not put all 41 into the student questionnaire

### Job Zones (30.2/30.3)

The reference file has **four rows**, but occupation ratings use zones **2, 3, 4, 5**. Zone 1 was merged into “Job Zone 1-2”.

- Zone 2: high school / little preparation
- Zone 3: vocational, related experience, or associate-level
- Zone 4: considerable preparation; most require a four-year bachelor's degree
- Zone 5: extensive preparation; most require graduate or professional school

### Education

- Element `2.D.1` Required Level of Education
- Scale `RL` is percent of incumbents in each of 12 education categories
- Category 6 = Bachelor's Degree
- Useful for explanation and eligibility rules, not as a KNN dimension

## Datasets selected for the engine

**Selected**

1. Occupation Data — identity and explanation text
2. Career Interest Types — core interest vector
3. Specific Interest Areas — finer interest matching and explanations
4. Knowledge — academic/field fit
5. Essential Skills — short, questionnaire-friendly skill vector
6. Transferable Skills — graduate-relevant skills such as problem solving and programming
7. Work Styles — personal characteristics
8. Job Zones + Education — rule-based eligibility
9. Work Context (selected items only) — work-preference rules
10. Work Activities (General Work Activities) — explanation of “what the job involves”, not the full questionnaire

**Inspected but not used as KNN features**

- Occupation Level Metadata — survey administration, not student-relevant
- Training and Experience — useful on occupation pages, not a student vector
- Software Skills — too sparse/US-technology-specific for a first version
- Task Statements — occupation detail pages later
- Abilities — 52 items; many are psychomotor/physical and poor as unvalidated self-ratings. Cognitive abilities overlap Essential Skills. Proposed as display-only unless we later add a very small optional subset.

## Work Values

`Work Values` is **not present** in the O*NET 30.3 data dictionary (the 30.3 URL returns 404). Content Model 30.3 also has no `1.C Work Values` branch.

The scale list still contains `VH` (Work Value High-Point), which appears to be leftover from earlier releases.

**Decision:** do not mix historical Work Values from O*NET 29.x into a 30.3 system. Career preferences will be captured through Specific Interest Areas, Work Styles, and Work Context instead.

## US labour-market limitation

O*NET describes occupations in the United States. Titles, interest profiles, skill importance, and education patterns are still usable as a structured occupational taxonomy for NSUK students, but:

- Nigerian labour-market demand, salary, and credential rules are **not** in these files
- Some US job titles will be unfamiliar locally
- The UI and dissertation must state this limitation clearly

No Nigerian occupational ratings will be invented to “localise” O*NET.
