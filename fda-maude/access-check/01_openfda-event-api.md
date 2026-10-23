# Access check 01: openFDA device adverse event API
**Verdict: WORKS.** All 9 checks passed live on 2026-10-19. One catch: the data is huge (3.4 million CGM reports). So a free API key is needed for a full pull.

Terms: **MAUDE** = FDA database of device problem reports. **openFDA API** = FDA web address that returns MAUDE reports as JSON (structured text a script reads). **Product code** = 3-letter FDA label for a device type. **API key** = free personal password that raises the daily call limit.
Base URL: `https://api.fda.gov/device/event.json`. About 145 calls used. No API key used.

## What was tested
| # | Thing tested | Query used | Result | Evidence |
|---|---|---|---|---|
| 1 | Reachable, no key | `?limit=1` | yes | HTTP 200, JSON |
| 2 | Find CGM product codes | `classification.json?search=device_name:"continuous glucose"` (+ "glucose", "interstitial") | yes | 13 CGM codes with reports (table below) |
| 3 | Sizing by code, year, event type, brand | `count=date_received`, `count=event_type.exact`, `count=device.brand_name.exact` | yes | Count sums match totals exactly |
| 4 | Libre 3 by month | `device.brand_name:"libre 3"` + `count=date_received` | yes | See "Recall signal" below |
| 5 | Fields in single records | `limit=3` (Libre 3, Nov 2025) and `limit=100` (QBJ, 2026) | yes | All asked-for fields present |
| 6a | Max `limit` per call | limit 999 / 1000 / 1001 | partial | 999 = OK. 1000 = HTTP 403 "API_KEY_MISSING". 1001 = HTTP 400 |
| 6b | Max `skip` | skip 25000 / 25001 / 26000 | yes | 25000 = OK. Above that = HTTP 400 |
| 6c | `search_after` past skip cap | followed `Link` header, 999 per page | yes | 28 pages. 27,972 records. All unique. No errors |
| 7 | Rate limit headers | read all response headers | no | No rate-limit headers are sent |
| 8 | Freshness | `meta.last_updated` | yes | 2026-10-07. Newest report received 2026-09-30 |
| 9 | Date range filter | `date_received:[20250101 TO 20251231]` | yes | HTTP 200. 447,015 CGM reports in 2025 |

## Sizing: CGM product codes (field `device.device_report_product_code`)
| Code | Device name (FDA) | Reports | Death | Injury | Malfunction |
|---|---|---|---|---|---|
| QBJ | Integrated CGM, factory calibrated (Dexcom G6/G7, Libre 2 Plus/3/3 Plus) | 2,352,192 | 245 | 43,892 | 2,307,699 |
| PQF | Invasive glucose sensor, non-adjunctive (Dexcom G5, Medtronic Guardian 4 / Simplera / Instinct) | 327,332 | 10 | 2,328 | 324,994 |
| MDS | Invasive glucose sensor (older Dexcom G4/G5, Medtronic) | 282,266 | 321 | 13,645 | 267,813 |
| QLG | Integrated CGM, not for insulin pumps (Libre 2, Libre 3) | 260,781 | 31 | 42,306 | 218,422 |
| PZE | Factory calibrated, user-initiated (Libre 14 day) | 143,132 | 13 | 17,511 | 125,600 |
| SFI | Sensor, part of auto insulin system (Simplera Sync, Instinct) | 5,019 | 0 | 112 | 4,907 |
| SBA | Integrated CGM with dexamethasone sensor (Eversense 365) | 3,775 | 1 | 820 | 2,942 |
| SAF | Over-the-counter CGM (Stelo, Lingo) | 2,807 | 0 | 228 | 2,571 |
| QHJ | Implanted sensor, non-adjunctive (Eversense) | 2,485 | 0 | 1,238 | 1,246 |
| QCD | Implanted CGM, adjunctive (Eversense) | 1,514 | 0 | 948 | 566 |
| QDK | CGM for non-intensive use (Dexcom G6 program) | 620 | 1 | 18 | 601 |
| QII | Professional CGM (Dexcom G6 Pro) | 237 | 1 | 2 | 234 |
| SBH | Over-the-counter CGM (Stelo) | 2 | 0 | 1 | 1 |
| **All 13** | | **3,382,071** | **623** | **123,049** | **3,257,596** |

- QDL, SJD, SFU exist in FDA's list but have 0 reports. Not counted: OZP (901,619) and OZO (439,586). These are insulin pump + sensor systems. Most Medtronic Guardian sensor/transmitter reports sit there.

All 13 CGM codes, reports by year received:

| Before 2014 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (to Sep) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 14,075 | 36,209 | 39,944 | 97,218 | 114,093 | 164,535 | 130,938 | 221,157 | 352,301 | 286,649 | 344,344 | 415,499 | 447,015 | 718,185 |

Brands inside the 13 CGM codes (word search on brand name). All four expected brands appear. Names are messy ("FREESTYLE LIBRE 3" and "FreeStyle Libre 3" count separately); the robot must clean them.

| Brand word | Reports |
|---|---|
| Dexcom | 2,444,824 |
| Libre | 713,394 |
| Eversense | 7,753 |
| Guardian (Medtronic) | 5,599 (+ about 20,000 more under pump code OZP) |
| Simplera (Medtronic) | 4,635 |
| Stelo (Dexcom) | 2,716 |

## Recall signal (Libre 3, includes Libre 3 Plus)
| Month received | 2025 Jan-Nov (each month) | 2025 Dec | 2026 Jan | 2026 Feb | 2026 Mar | 2026 Apr | 2026 May | 2026 Jun | 2026 Jul | 2026 Aug | 2026 Sep |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Reports | 1,299 to 1,929 | 4,570 | 4,408 | 2,349 | 4,303 | 31,719 | 36,900 | 39,990 | 15,269 | 48,271 | 44,038 |

- Yes, a spike. Dec 2025 is about 3x normal, right after the Nov 2025 recall. A much bigger jump starts Apr 2026 (about 25x).
- By event date (when the problem happened), counts are flat. About 9,000-11,500 per month in 2025. No spike.
- guess: Abbott sent in many late reports for older events in 2026. The robot should track both date fields.

## Content of one record
| Field | Present? | Notes |
|---|---|---|
| `mdr_text` (narrative text) | yes | Usually 2 parts: event description + manufacturer notes. Median 1,298 characters total (range 193-4,729, n=100) |
| `product_problems` | yes | 100 of 100. Examples: "Low Readings", "High Readings" |
| Patient outcome (`patient.sequence_number_outcome`, `patient_problems`) | yes | e.g. "Required Intervention", "Hypoglycemia" |
| `report_number`, `mdr_report_key` | yes | Unique report IDs |
| Dates | yes | `date_received`, `date_of_event`, `date_report`, `date_manufacturer_received`, more |
| Device model / lot | partly | `model_number` filled. `lot_number` filled in 79 of 100. `udi_di` sometimes empty |
| Size | yes | Median about 5.9 KB per record (JSON) |

## Limits found
- Page size: max 999 without a key (1,000 needs a key). `skip`: max 25,000; past that use `search_after` (works).
- Speed: about 19 seconds per 999-record page (measured: 28 pages in 521 s). About 5.2 MB per page.
- Rate limits (FDA docs, open.fda.gov/apis/authentication). Not shown in headers.

| | Per minute | Per day |
|---|---|---|
| No key (per IP address) | 240 | 1,000 |
| Free key | 240 | 120,000 |

- Full pull of all 3,382,071 CGM reports = about 3,390 calls. Without key: at least 4 days. With key: about 17-18 hours one call at a time, at measured speed. About 18 GB raw JSON.
- Freshness: updated 2026-10-07 (12 days before today). Newest report received 2026-09-30 (19 days old). guess: updates about monthly.

## What this means for the robot
- This route works. Use it as the main way to get MAUDE reports.
- Get a free API key before the full pull. Without one, 1,000 calls/day is too few.
- Split the pull by product code and by month of `date_received`. Then follow `search_after` inside each slice. This also lets the robot resume after a crash.
- Do not store the whole raw JSON. Keep only needed fields (IDs, dates, brand, code, event type, problems, outcome, narrative). guess: this cuts 18 GB to a few GB.
- Do not send all 3.4 million narratives to an LLM. Sample first, or filter (for example, deaths + injuries = about 124,000 reports).
- Clean brand names and keep both received date and event date. The 2026 Libre surge looks like late reporting, not new events.
- Not tested: speed with an API key, running calls in parallel, the bulk download files (see 02_bulk-files.md).
