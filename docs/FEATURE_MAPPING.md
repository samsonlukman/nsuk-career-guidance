# Questionnaire → feature → O*NET mapping

Canonical Version 1 mapping, including sparse SIA/knowledge cosine and rule formulas: [FINAL_SPEC.md](FINAL_SPEC.md) sections 4–5.

Every scored questionnaire item must map to an official O*NET 30.3 element. Academic profile items are used by the rule layer, not by KNN.

Student responses use the **same numeric range as the chosen O*NET scale** wherever possible, then min–max normalisation to `[0, 1]` before similarity is computed.

Proposed questionnaire length: about **40 items**, plus 5 academic-profile fields.

Weights below are starting values for a weighted-block cosine similarity. They are configuration, not trained parameters, and must remain editable.

| Student question | Feature | O*NET file / element | Scale | Transformation | Block weight |
|---|---|---|---|---|---|
| How much would you enjoy realistic work (building, repairing, outdoor/physical, using tools or machines)? | `interest_realistic` | Career Interest Types / `1.B.1.a` Realistic | OI 1–7 | `(x-1)/6` | 0.25 (RIASEC block) |
| How much would you enjoy investigative work (research, analysis, science, studying problems in depth)? | `interest_investigative` | `1.B.1.b` Investigative | OI 1–7 | `(x-1)/6` | RIASEC block |
| How much would you enjoy artistic work (design, writing, performance, original creative work)? | `interest_artistic` | `1.B.1.c` Artistic | OI 1–7 | `(x-1)/6` | RIASEC block |
| How much would you enjoy social work (helping, teaching, counselling, serving people)? | `interest_social` | `1.B.1.d` Social | OI 1–7 | `(x-1)/6` | RIASEC block |
| How much would you enjoy enterprising work (leading, selling, persuading, business, politics)? | `interest_enterprising` | `1.B.1.e` Enterprising | OI 1–7 | `(x-1)/6` | RIASEC block |
| How much would you enjoy conventional work (organising records, following procedures, working with data in a structured setting)? | `interest_conventional` | `1.B.1.f` Conventional | OI 1–7 | `(x-1)/6` | RIASEC block |
| Select up to 5 specific work activities you would most enjoy, then rate each. Options are the 41 Specific Interest Areas. Unselected areas = 1. | `sia_<element_id>` | Specific Interest Areas / `1.B.3.*` (41 elements) | OI 1–7 | selected: `(x-1)/6`; unselected: `0` | 0.20 |
| Rate your current skill: Reading comprehension | `skill_reading` | Essential Skills / `2.A.1.a` | IM 1–5 | `(x-1)/4` | 0.20 (essential-skills block) |
| Active listening | `skill_listening` | `2.A.1.b` | IM 1–5 | `(x-1)/4` | essential-skills |
| Writing | `skill_writing` | `2.A.1.c` | IM 1–5 | `(x-1)/4` | essential-skills |
| Speaking | `skill_speaking` | `2.A.1.d` | IM 1–5 | `(x-1)/4` | essential-skills |
| Mathematics | `skill_math` | `2.A.1.e` | IM 1–5 | `(x-1)/4` | essential-skills |
| Science | `skill_science` | `2.A.1.f` | IM 1–5 | `(x-1)/4` | essential-skills |
| Critical thinking | `skill_critical_thinking` | `2.A.2.a` | IM 1–5 | `(x-1)/4` | essential-skills |
| Active learning | `skill_active_learning` | `2.A.2.b` | IM 1–5 | `(x-1)/4` | essential-skills |
| Learning strategies | `skill_learning_strategies` | `2.A.2.c` | IM 1–5 | `(x-1)/4` | essential-skills |
| Monitoring (checking progress/quality) | `skill_monitoring` | `2.A.2.d` | IM 1–5 | `(x-1)/4` | essential-skills |
| Complex problem solving | `skill_problem_solving` | Transferable Skills / `2.B.2.i` | IM 1–5 | `(x-1)/4` | 0.15 |
| Programming | `skill_programming` | `2.B.3.e` | IM 1–5 | `(x-1)/4` | transferable block |
| Instructing / teaching others | `skill_instructing` | `2.B.1.e` | IM 1–5 | `(x-1)/4` | transferable block |
| Persuasion | `skill_persuasion` | `2.B.1.c` | IM 1–5 | `(x-1)/4` | transferable block |
| Negotiation | `skill_negotiation` | `2.B.1.d` | IM 1–5 | `(x-1)/4` | transferable block |
| Time management | `skill_time_management` | `2.B.5.a` | IM 1–5 | `(x-1)/4` | transferable block |
| I am inventive and like new ways of doing work | `style_innovation` | Work Styles / `1.D.1.a` Innovation | Student 1–5 vs WI −3..+3 | student `(x-1)/4`; occupation `(wi+3)/6` | 0.10 |
| I set demanding goals and work hard to reach them | `style_achievement` | `1.D.1.b` | 1–5 vs WI | as above | work-styles block |
| I am comfortable taking charge and leading | `style_leadership` | `1.D.1.i` | 1–5 vs WI | as above | work-styles block |
| I enjoy cooperating and helping colleagues | `style_cooperation` | `1.D.2.d` | 1–5 vs WI | as above | work-styles block |
| I am thorough and pay attention to detail | `style_detail` | `1.D.3.b` | 1–5 vs WI | as above | work-styles block |
| I stay effective under stress | `style_stress` | `1.D.4.a` | 1–5 vs WI | as above | work-styles block |
| Faculty | `faculty` | not an O*NET field | categorical | rule input + knowledge prior | n/a |
| Department / programme | `department` | not an O*NET field | categorical | rule input + knowledge prior | n/a |
| Current level (100–400) | `level` | not an O*NET field | categorical | stored on profile only | n/a |
| Willing to pursue postgraduate or professional training? | `further_study` | Job Zones / Education | Yes/Maybe/No | rule filter for Zone 5 | n/a |
| Prefer careers related to my course, or open to other fields? | `course_relatedness` | Knowledge IM vector | related / open | if “related”, penalise low knowledge-prior similarity | n/a |
| Select up to 5 knowledge areas you are strongest in / enjoy studying | `knowledge_<element_id>` | Knowledge / `2.C.*` (33 elements) | IM 1–5 | selected `(x-1)/4`; unselected `0` | 0.10 |
| I prefer mostly indoor, office-type settings | `pref_indoor` | Work Context `4.C.2.a.1.a` Indoors, Environmentally Controlled | CX/context | rule: down-rank high outdoor occupations if strongly indoor | n/a |
| I am comfortable working outdoors / in the field | `pref_outdoor` | `4.C.2.a.1.c` Outdoors, Exposed to All Weather Conditions | CX | rule | n/a |
| I prefer working as part of a team | `pref_team` | `4.C.1.b.1.e` Work With or Contribute to a Work Group or Team | CX | rule | n/a |
| I am comfortable dealing with the public / customers | `pref_public` | `4.C.1.b.1.f` Deal With External Customers or the Public | CX | rule | n/a |

## Knowledge prior from NSUK faculty (rules, not invented O*NET scores)

O*NET does not know NSUK programmes. A **documented, editable mapping** will raise prior scores on relevant knowledge elements when the student chooses “prefer careers related to my course”. This mapping is ours, not O*NET, and must be shown in admin configuration.

Faculty list is taken from the official NSUK Academics page. Department lists will be confirmed from NSUK before they are hard-coded.

| NSUK faculty (official site) | Knowledge elements to boost if “stay related” is selected |
|---|---|
| Administration | Administration and Management; Economics and Accounting; Personnel and Human Resources; Sales and Marketing; Customer and Personal Service |
| Agriculture | Food Production; Biology; Chemistry |
| Arts | English Language; Foreign Language; Fine Arts; History and Archeology; Philosophy and Theology |
| Communication and Media Studies | Communications and Media; Telecommunications; English Language; Sales and Marketing |
| Education | Education and Training; Psychology; English Language |
| Engineering | Engineering and Technology; Design; Physics; Mathematics; Building and Construction; Mechanical; Computers and Electronics |
| Environmental Sciences | Building and Construction; Design; Geography; Engineering and Technology |
| Law | Law and Government; English Language |
| Natural and Applied Sciences | Mathematics; Physics; Chemistry; Biology; Computers and Electronics |
| Social Sciences | Psychology; Sociology and Anthropology; Economics and Accounting; Geography; Law and Government |
| College of Medicine and Health Allied Sciences | Medicine and Dentistry; Therapy and Counseling; Biology; Chemistry; Psychology |

This table is a proposal. It should be reviewed before implementation because several faculties map to overlapping knowledge areas, and NSUK department names still need official confirmation.

## Items intentionally not asked

- All 52 abilities. Many are physical/psychomotor and unsafe to infer from a short self-report.
- All 41 General Work Activities as Likert items. They will be used to explain recommended occupations (“this job involves analysing data, writing, teaching…”) from O*NET ratings.
- Work Values. The domain is absent from O*NET 30.3.
- CGPA. O*NET has no CGPA field. Storing CGPA on the student profile is optional; using it inside KNN would be fabricating a mapping.

## Explanation features

For each recommended occupation, explanations will be generated only from features that actually contributed, typically:

- Top RIASEC matches (student high and occupation `OI` high)
- Selected Specific Interest Areas that are also high for the occupation
- Essential/transferable skills where both student and occupation importance/self-rating are high
- Knowledge areas that matched
- Job Zone / education caveat from official Job Zone text
- Fired eligibility rules (“included because you are willing to pursue further study”)
