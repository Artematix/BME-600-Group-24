# MAUDE + recall pull: summary

Status: ALL 5 TIERS DONE. Pulled 2026-10-19 by `scripts/maude_robot.py`. Full pull cleaned 2026-10-20.
FDA data last updated 2026-10-07 (newest report received 2026-09-30).
CGM = continuous glucose monitor. MAUDE = FDA database of device problem reports. 13 CGM product codes (FDA device-type labels).
API calls used by the robot on 2026-10-19: 5,011 in total.
- 700 without a key (tiers 1, 2, 4 and part of 3)
- the rest with a free FDA API key (rest of tier 3, tier 5 tests and the full pull)

## What was pulled
| Tier | What | Result | Status |
|---|---|---|---|
| 1. Counts | Count tables for all CGM reports (no reports downloaded) | 169 count queries -> `results/counts/` | Done |
| 2. Serious | Every death + injury report | 123,672 downloaded = 123,607 unique reports | Done |
| 3. Sample | Random malfunction reports | 5,193 reports in 76 of 76 groups | Done (finished with the key) |
| 4. Recalls | CGM recall records + recall class | 95 records, 32 recall events | Done |
| 5. Full | Every CGM report, all event types | 997 of 997 slices, 3,382,162 downloads = 3,382,071 unique reports | Done. Ran 2026-10-19 16:05 to 17:55. Cleaned 2026-10-20 |

- Tier 3 ends 193 over the 5,000 target. Groups are filled with clusters of up to 10 reports, so a group can end a few over.
- Tier 3 clean: 0 duplicate keys, 0 shared report numbers.
- Tier 5: 3,382,162 downloads = 3,382,071 reports + 91 reports that list two CGM codes. `clean` keeps each report once.
- Tier 5 check: all 997 slices got exactly the planned number of reports (3,382,162 of 3,382,162).
- Tier 5 used 4,093 calls and took about 1 hour 50 minutes (4 workers).
- A few calls failed on network errors and were retried. All slices finished.
- Tier 5 file sizes:

| File | Size |
|---|---|
| `raw/full/` (997 gzipped files) | 314 MB |
| `clean/full.csv.gz` (one row per report) | 193 MB |

- Checks: tier 1 total matches the access check (3,382,071). Tier 2 matches tier 1 (623 deaths + 123,049 injuries).
- 65 tier 2 reports list two CGM codes, so they came twice. Removed in `clean/`. 6 rows share a report number (flagged).
- Recalls: 7 Class I (most serious), 23 Class II, 2 old events with no class.

## Reports by product code (all reports, tier 1)
| Code | Main devices | Reports | Deaths | Injuries | Malfunctions |
|---|---|---|---|---|---|
| QBJ | Dexcom G6/G7, Libre 2 Plus/3/3 Plus | 2,352,192 | 245 | 43,892 | 2,307,699 |
| PQF | Dexcom G5, Medtronic Guardian 4 / Simplera | 327,332 | 10 | 2,328 | 324,994 |
| MDS | Older Dexcom G4/G5, Medtronic | 282,266 | 321 | 13,645 | 267,813 |
| QLG | Libre 2, Libre 3 | 260,781 | 31 | 42,306 | 218,422 |
| PZE | Libre 14 day | 143,132 | 13 | 17,511 | 125,600 |
| 8 small codes | Eversense, Stelo, Lingo, Simplera Sync, G6 Pro | 16,459 | 3 | 3,367 | 13,068 |
| **All 13** | | **3,382,071** | **623** | **123,049** | **3,257,596** |

- About 900 reports have event type "Other" or blank.
- The "All 13" row counts each report once. 91 reports list two CGM codes, so the code rows add up to 91 more.

## Reports by year received (all codes)
| Year | Reports | Deaths | Injuries |
|---|---|---|---|
| before 2014 | 14,075 | 98 | 7,402 |
| 2014-2017 | 287,464 | 212 | 5,628 |
| 2018-2021 | 868,931 | 36 | 20,891 |
| 2022 | 286,649 | 11 | 13,726 |
| 2023 | 344,344 | 22 | 20,598 |
| 2024 | 415,499 | 32 | 20,231 |
| 2025 | 447,015 | 94 | 16,410 |
| 2026 (to Sep) | 718,185 | 118 | 18,163 |

## Top 10 problem types (all reports; one report can have several)
| Problem (FDA code text) | Reports |
|---|---|
| Wireless Communication Problem | 1,057,609 |
| Incorrect, Inadequate or Imprecise Result or Readings | 602,892 |
| No Device Output | 325,299 |
| Low Readings | 174,493 |
| Imprecision | 171,362 |
| Detachment of Device or Device Component | 156,989 |
| Device Displays Incorrect Message | 129,766 |
| Premature End-of-Life Indicator | 113,104 |
| Device Operates Differently Than Expected | 83,231 |
| Unintended Application Program Shut Down | 73,138 |

## Demographics: how often the field is filled in (missing = blank, "NA", "Unknown")
| Field | All reports (tier 1) | Serious reports (tier 2) |
|---|---|---|
| Age | 73.9% | 44.7% |
| Sex (incl. "Prefer not to disclose") | 46.6% | 29.4% |
| Race | 0.3% | 3.0% |
| Ethnicity | 0.3% | 2.0% |
| Patient outcome | 4.4% | 94.0% |

## Not done yet
- `recall_harm_manual.csv` has only the Nov 2025 Libre 3 row. Other Class I recalls need injuries/deaths typed in by hand.
- The clean tables have no country per report. The pull ran before the robot kept the field `reporter_country_code`. Country counts come from `scripts/country_spread.py` instead.

## Caveats
- MAUDE is voluntary reporting. Counts are reports, not failure rates. We do not know how many sensors were used.
- Date received is not the date the problem happened. The 2026 Libre 3 jump shows only by date received. guess: late reports after the recall.
- A report can list several product problems. Problem counts add up to more than the report count.
- Brand names are messy (same product spelled many ways). Not cleaned yet.
- Tier 1 brand table: MDS hit the 999-row limit, so its rarest brand spellings are cut.
- Sample: use `weight` or `weight_norm` when scaling sample counts up to all malfunction reports.
