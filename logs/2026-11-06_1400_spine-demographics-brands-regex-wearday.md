# 2026-11-06 14:00. Spine rethink, deeper demographics, brand tests, regex over all reports, wear day 1

## What was asked
- Artemy: the paper's spine felt weak and unclear. Make the three questions concrete.
- Dig deeper into demographics (intersections, location, full suite) and document cohort distributions.
- Run brand-vs-brand tests on the FDA wrong-reading reports, and by demographics.
- See what else the MAUDE reports hold besides numbers; consider reading more than death + injury.
- Read the 3.3 million malfunction reports with patterns only (no model), improving the patterns.
- Wear day 1: bad sensors discarded early, or sensors settling in?
- Stop bringing up the data-cleaning finding in big-picture text.

## Who did it
Manager (spine, briefs, log) + 6 agents. A network outage on 11-06 killed 4 agents at launch; relaunched after a connectivity probe. The field-inventory agent wrote its tables and script but never wrote its memo (`fda-maude/results/FIELD_INVENTORY.md` missing; tables in `fda-maude/results/inventory/`).

## What was produced
| Piece | Files | One-line result |
|---|---|---|
| Deep demographics | `analysis/DEMOGRAPHICS_DEEP.md`, `demographics_deep.py`, figs 29-32 | 680 tests, 226 people: who you are does not predict error. One lead passed correction (sex, low range). |
| Sex-lead follow-up | `analysis/DEMOGRAPHICS_FOLLOWUP.md`, `demographics_followup.py`, fig 35 | Real in this data, sensor not glucose pattern, unexplained, too small to change a dose (about 2.5 mg/dL at 60). |
| Wear day 1 | `analysis/WEAR_DAY.md`, `wear_day.py`, figs 33-34 | Settling, not selection: 92 % of the day-1 excess. Extra error halves every 24 h, gone by day 3. New sensor reads about 10 % low in the low range on day 1. |
| Brand comparison | `fda-maude/results/text/BRAND_COMPARISON.md`, `brand_comparison.py`, tables g_*, figs t7-t10 | Same error size, different failure: Abbott false lows at high true glucose, Dexcom hidden true lows. Most other brand gaps are reporting style. |
| Regex v2 over all 3.38 M reports | `fda-maude/results/text/REGEX_V2_FULL_CORPUS.md`, `extract_regex_v2.py`, `report_regex_v2.py`, tables h_*, figs t11-t13 | Recall vs model 73 -> 89 %. 191,112 malfunction-only pairs: one fault (false low 60-80 % at normal/high glucose). Harm share U-shaped vs error size, partly coding. |
| Field inventory | `fda-maude/results/FIELD_INVENTORY.md`, `field_inventory.py`, `results/inventory/` (27 files) | Finished 2026-11-08. Country per report IS in the clean tables (94.9 % filled; README note was wrong, fixed). Maker-evaluation and device-returned fields unused so far: "no defect found" in 81 % of returned devices. Age/sex fill is a maker habit (Dexcom 93 %, Abbott 7 %). Verdict: do not run the model on the 3.26 M malfunction texts (46 % are 241 identical templates; regex v2 already read the numbers); do two 100-report human reads instead. |

## Decisions
- Spine = one question, three claims: error-to-decision curve; two real-world failure modes and the decision each breaks; a working sensor already misses 1 in 4 lows.
- Data-cleaning finding stays in methods only.
- Sex result goes in as a modest, labelled finding. Day-1 effect is written as settling.
- Phase 2 suggestion from the regex memo: simulate three faults (false low at 70-250; hidden low under 54; floor-pinned sensor over 250) instead of one constant bias. Not yet decided.

## Open
- Folded into `analysis/FINDINGS.md` (findings 9-12, section 10) and `docs/PROJECT_OVERVIEW.md` on 11-08. Inventory memo finished 11-08.
- Not decided: three-fault simulation; inventory memo's ranked suggestions; two 100-report human reads of the extreme error bands.
- Push still waits for Artemy's word. Teammate gold check done 2026-11-08 (no issues). Ollama server, 19 GB bulk_zips: unchanged.
- Lesson: a network outage kills agents at launch with "ENOTFOUND"; probe connectivity, then relaunch. An agent that survives with a dead background job waits forever; tell it the job is dead and to work in the foreground.
