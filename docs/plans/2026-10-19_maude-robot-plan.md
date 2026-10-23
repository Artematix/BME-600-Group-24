# Plan: FDA MAUDE + recall robot (Phase 1 data collection)

Status: APPROVED 2026-10-19 (tiers 1-4). Access checked live 2026-10-19.
Evidence: `fda-maude/access-check/01..04_*.md`.

## 1. Big picture

- "Robot" = one Python script on a laptop. No person clicking.
- It collects, for CGM (continuous glucose monitor) sensors:
  1. MAUDE reports. MAUDE = FDA database of device problem reports. Each has codes + a free-text story.
  2. Recall records. Official FDA notices that a device was pulled or fixed.
- Main route: openFDA API. API = an FDA web address a script asks for data, gets clean JSON back.
- Web scraping is NOT needed. It adds almost nothing the API lacks.
- LLM labelling is NOT in this plan. Separate plan later.

## 2. Access check results

| Route | Verdict | Key facts |
|---|---|---|
| A. openFDA event API | WORKS | All 9 tests passed. No key needed to test. |
| B. Bulk files (all of MAUDE) | WORKS | 8-19 GB download. Cannot filter before download. Backup only. |
| C. Website scraping | PARTLY | Allowed, but 500-result cap per search. Bot wall on form searches. robots.txt asks 30 s between requests. TPLC site is blocked to robots. |
| D. Recall APIs | WORKS | All 6 known recall numbers found. |

Size of the job (much bigger than we thought):

| Item | Number |
|---|---|
| CGM product codes with reports | 13 |
| CGM reports, total | 3,382,071 |
| Deaths | 623 |
| Injuries | 123,049 |
| Malfunctions | 3,257,596 |
| Dexcom / Libre reports | 2.44 M / 713 k |
| CGM recall events | 32 (7 Class I) |
| Data last updated | 2026-10-07 (newest report 2026-09-30) |

Product codes: QBJ, PQF, MDS, QLG, PZE, SFI, SBA, SAF, QHJ, QCD, QDK, QII, SBH.
Product code = 3-letter FDA device category. Exclude QFG (insulin pump).

## 3. What the robot pulls (tiered)

A full pull of all 3.4 M reports = ~3,400 calls, ~18 GB, ~18 hours. Not needed for most questions.

| Tier | What | Size | Calls | Key needed? |
|---|---|---|---|---|
| 1. Counts | Counts by code, brand, month, outcome, problem type. No records downloaded. Covers "how often" for ALL reports. | tiny | ~200 | No |
| 2. Serious reports | Full records for all deaths + injuries. | ~124 k reports | ~125 | No |
| 3. Malfunction sample | Random sample of malfunction reports, spread over brands and years. | 5-10 k (to decide) | ~10 | No |
| 4. Recalls | All CGM recalls (recall + enforcement APIs, joined on recall number). | 95 records | ~10 | No |
| 5. Full pull (optional) | Everything. Only if tiers 1-3 are not enough. | 3.4 M | ~3,400 | Yes (free) |

- Tiers 1-4 fit inside the no-key limit of 1,000 calls/day.
- Injury/death counts for recalls are NOT in any API. Only on fda.gov news pages. Only 7 Class I events, so copy by hand.

## 4. Steps

1. Config file: product codes, date range, tiers to run.
2. Tier 1 counts -> small CSV tables.
3. Tiers 2-3: split by product code + month. Page with the API's "next page" link (gets past the 25,000-record cap). Resumable per slice.
4. Keep only needed fields: report ID, dates (received AND event), brand, model, lot, code, outcome, problem codes, narrative. Drop the rest.
5. Tier 4 recalls -> one CSV. Drop the huge serial-number field.
6. Clean: one row per report, remove duplicates, tidy brand names.
7. Log every query + pull date. Raw data in `fda-maude/raw/` (gitignored).

## 5. Things the data showed already

- Libre 3 reports by date RECEIVED jump ~3x in Dec 2025 and ~25x from Apr 2026.
- By date the problem HAPPENED: no spike in ALL reports (mostly malfunctions). guess: late reports of older events after the recall.
- BUT death + injury reports DO spike by event date: Dec 2025 (779) and Aug 2024. Both match a recall. See fda-maude/results/report/figures/fig3_libre3_timeline.png.
- So: always keep both dates. Counts by received date show reporting behaviour, not failures.
- Narratives in the API are ALL CAPS. Fine for an LLM.

Demographics (count queries, all 3.38 M CGM reports, 2026-10-19):

| Field | Filled in | Notes |
|---|---|---|
| Age | ~74% | Rest blank or "NA". Most common ages 60-69. |
| Sex | ~46% (F 777 k, M 768 k) | Rest blank, "Unknown" or "Prefer not to disclose". |
| Weight | ~38% | |
| Race | ~0.3% | Too empty to use. |
| Ethnicity | ~0.3% | Too empty to use. |

- Age and sex are usable, with a missing-data warning. Race/ethnicity are not.
- The robot keeps all five fields.

## 6. Tools

- Python + `requests` (or built-in `urllib`). No browser tools (Playwright / Selenium / Scrapy) needed.
- Problem: this laptop has Python 3.8.2 only, no packages installed. CLAUDE.md says Python 3.11. See decisions.

## 7. Decisions (Artemy, 2026-10-19)

| Question | Decision |
|---|---|
| Approach | Tiers 1-4 now. Tier 5 only if needed. |
| Devices | All 13 CGM codes. |
| Malfunction sample | 5,000 reports. |
| Python | Install Python 3.11 on this laptop. |
| Date range | No limit. Tier 2 is only ~124 k reports in total. Sample spread across years. |
| API key | Not needed for tiers 1-4. Get one only if tier 5 happens. |
| Tier 5 full pull | Approved later on 2026-10-19. Free key obtained (stored as a Windows user setting, never in the repo). |
