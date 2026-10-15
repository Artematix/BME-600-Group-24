# 2026-10-14 18:30  Midterm research plan: final draft

## What was asked
- Review the team's Oct 12 report draft against the rubric.
- Fix Sections I to III. Write the empty sections (IV, V, VI, data and code, AI use, contributions).
- Make a version with comments explaining each change, for the team.

## Who did it
- Artemy, with Claude for drafting, prose tightening and reference checks.
- Four parallel agents for the review: Sections I-II, Section III, reference check, drafts of empty sections.

## What was produced
- `docs/plans/2026-10-14_midterm-research-plan.pdf` and `.docx`: full plan. Title page, 6 body pages, references.
- `docs/plans/2026-10-14_midterm-research-plan_change-notes.docx`: same plan with 26 comments explaining each change.
- `docs/plans/2026-10-14_midterm-research-plan.md`: source text.
- README and PROJECT_OVERVIEW: corrected pair count, sensor name, Shanghai cohort wording.

## Decisions
- Headline accuracy set: REPLACE-BG meter pairs (475,502). Calibration pairs (120,202) reported alongside.
- Primary REPLACE-BG sample for the next phase: CGM+BGM arm (routine testing). CGM-only arm as a check.
- Bias in the low range is grouped by the average of CGM and fingerstick (regression to the mean fix).
- Corrections to the old draft:

| Old | New | Why |
|---|---|---|
| About 600,000 pairs | 475,502 pairs | Count from our code |
| Precision Xtra meter | Contour Next meter (Precision Xtra for 203 people) | Trial paper and our data |
| Jaeb terms forbid re-identification | Terms require attribution, bind downstream users | Jaeb download page |
| 112 hospital patients | 112 adults recruited through two hospitals | Zhao et al. 2023 |
| Recall tally by year | 2026 records are one event, started Nov 24, 2025 | FDA recall database |

## Open questions
- Team to confirm Table 3 leads, meeting day, final due date, other AI tools used.
- 38 million US diabetes figure in Section I needs a CDC citation or should be cut.
- Jaeb attribution text from the dataset ReadMe still to be added.
- Next analysis step: lag correction and calibration-pair exclusion.
