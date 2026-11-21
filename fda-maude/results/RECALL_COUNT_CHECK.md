# Recall count check (2026-11-20)
**Numbers for the paper:** 32 events and 95 records (7 Class I, 23 Class II, 2 old events with no class). Why: the one event the refresh added is an insulin dose software fault, not a glucose sensor fault.
- Before citing: add event 99765 to the drop list in `fda-maude/scripts/config.json` and rebuild the CSV. Today the CSV still holds 96 records and 33 events.
- Checked from files on disk and git history. No new FDA download.
- CGM = continuous glucose monitor. Recall event = one FDA action. Recall record = one product model inside an event. Recall class = FDA risk level (Class I = most serious).

## 1. What the 2026-10-26 refresh added: one record, one event
| Item | Value |
|---|---|
| Record / event id | Z-0203-2027 / 99765 |
| Company, product | Medtronic MiniMed, Inc. CareLink Clinic software, REF MMT-7350 |
| Recall class | Blank in our file. FDA status is "Open, Classified", so FDA has set a class. Our class look-up on 2026-10-26 found nothing. The class is in no file we hold. It is on the FDA recall web page for this record (FDA page id 222434) |
| Date started | 2026-09-11 |
| Date classified | Blank in our file. FDA posted the record on 2026-10-21. guess: classified that day or one day before (true for all 41 records that have both dates) |
- FDA posted it 2 days after the first pull (2026-10-19). Proof: the first-pull CSV in git (commit 2b1f092) has 95 rows and 32 events. Z-0203-2027 is the only row not in it. No row was removed.

## 2. Is it a CGM recall? No. This is our judgement from the FDA reason text, not an FDA label
- The fault: a "Settings Calculator" in the software gives wrong insulin dose settings. No glucose reading is wrong.
- It is not a pump or a meter. It is insulin dose software. The drop list already removes this kind: event 86895 (CareLink software, wrong pump insulin data).
- Why it was kept: its FDA code (PHV = software that reviews stored CGM data) is on our search list. The drop list is 9 event ids typed by hand on 2026-10-19. Nobody has reviewed event 99765.
- Event 97873 is the same product and is rightly kept. Its fault is a wrong sensor glucose graph.

## 3. Counts (class columns count events)
| | Records | Events | Class I | Class II | Class III | No class |
|---|---|---|---|---|---|---|
| CSV as it stands | 96 | 33 | 7 | 23 | 0 | 3 |
| CSV without event 99765 | 95 | 32 | 7 | 23 | 0 | 2 |
- The third no-class event is 99765. It is from 2026, not old. A re-run of `report_results.py` would label it "No class (old)" with product "?" (line 687).

## 4. Places that state the old count: 22 places in 13 files. None fixed
| Where | File and line numbers |
|---|---|
| repo root | `README.md` 78, 154 |
| `docs/` | `PROJECT_OVERVIEW.md` 35, 68. `plans/2026-10-19_maude-robot-plan.md` 35, 50 |
| `docs/paper/` | `FACT_SHEET.md` 67, 380, 410. `OUTLINE.md` 326 (row "G3"; this file was edited tonight, so the line may move). All but 410 already flag the mismatch |
| `fda-maude/` | `README.md` 22, 58. `access-check/04_recalls.md` 49, 50. `results/PULL_SUMMARY.md` 16, 34 |
| `fda-maude/results/report/` | `report_results.md` 154. `tables/a_scope.csv` 7. `tables/g_recalls_by_class.csv` 2-4. `tables/g_recall_events.csv` (whole file, 32 event rows) |
| `fda-maude/scripts/` | `report_results.py` 732, 747. Both have "32" typed in by hand. Line 732 is the title of figure `fig5_recalls_timeline.png` |
- `fda-maude/DATA_NOTES.md` 50 and 149 state the new count (96 / 33). `analysis/` states no recall count. Lines that say only "7 Class I" are true either way.
