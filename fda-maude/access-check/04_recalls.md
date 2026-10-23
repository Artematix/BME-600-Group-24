# Access check 04: FDA recall sources for CGM sensors

**Verdict: WORKS.** The openFDA recall API gives every CGM recall we looked for, for free, with no key. Recall class and injury/death counts need a second source.

- Tested live: 2026-10-19. About 80 requests in total, max 1 per second. CGM = continuous glucose monitor. API = a web address a script can ask for data and get clean, machine-readable data back.
- Recall class: FDA's risk level. Class I = most serious (may cause serious injury or death). Class II = may cause temporary harm.
- Probe scripts and outputs were kept locally, not in the repo.

## 1. Sources tested

| Source | URL | Works? | Evidence |
|---|---|---|---|
| openFDA recall API | api.fda.gov/device/recall.json | yes | 105 records (102 by CGM product code, 3 under pump code OZP that mention "sensor"). All 6 known recall numbers present (Z-1020..1023-2026, Z-2692-2024, Z-0734-2024). |
| openFDA enforcement API | api.fda.gov/device/enforcement.json | yes | Has recall class. Matched 84 of 105 CGM records. The 21 missing ones are all 2008-2010 (Navigator). |
| CDRH recall database page | accessdata.fda.gov/.../cfres/res.cfm?id=217499 | yes | robots.txt allows `res.cfm`. Plain Python got HTTP 200. Page is 5.3 MB (mostly serial numbers). |
| FDA "Recalls and Early Alerts" pages | fda.gov/medical-devices/medical-device-safety/medical-device-recalls-and-early-alerts | partial | Default Python user-agent gets "404 Not found". Browser-like user-agent gets 200. Libre 3 page states the injury and death counts. |
| Health Canada recalls (quick check) | recalls-rappels.canada.ca/sites/default/files/opendata-donneesouvertes/HCRSAMOpenData.json | yes, thin | One open-data JSON file, 15.8 MB, 34,263 items, 8,686 medical devices (2006 to 2026-10-16). 10+ CGM items seen (e.g. Libre 3 Plus, 2025-12-03, Type II). Only short fields: product, issue type, class, date, link. No search API tested. |
| Freshness | meta.last_updated | yes | recall.json: 2026-10-15 (59,494 records). enforcement.json: 2026-10-07 (40,249 records). |

## 2. What fields each source has

| Field | recall.json | enforcement.json | CDRH page | FDA news page |
|---|---|---|---|---|
| Reason for recall (firm's words) | yes | yes | yes | yes (FDA's plain-language version) |
| Root cause (FDA category, e.g. "Process control") | yes | no | yes | no |
| Recall class (I / II / III) | **no** | yes | yes (page title) | yes ("most serious type") |
| Product code, 510(k) number | yes | no | yes | no |
| Quantity in commerce | yes | yes | yes | no |
| Dates (initiated, posted, terminated) | yes | initiated, classified, report date | yes | no |
| Distribution (US states, countries) | yes | yes | yes | no |
| Voluntary or FDA-ordered, how firm notified | no | yes | no | no |
| Injury and death counts | no | no | no | **yes** (only here) |

- Query tips: recall.json `search=product_code:MDS+product_code:QBJ+...` works. `product_code:(MDS+QBJ)` returned 404.
  - enforcement.json has no product code field. Join it to recall.json by recall number.
  - Look-up by number: `recall_number.exact:"Z-1020-2026"`, one number per request (OR-ing several gave only 1 hit).
- Text search is noisy. "Guardian" matched hip implants, walkers and mattresses. Product codes are the better filter.
- Some recall numbers have a huge `code_info` field. Z-1020-2026 has 5.3 million characters (serial numbers).

## 3. CGM product codes (from classification API)

- Sensors and CGM systems: MDS, PQF, PZE, QHJ, QCD, SFI, QBJ, QLG, QDK, QII, QDL, SAF, SBH, SBA, SJD, PYV. CGM software and displays: PJT, PHV, QRX.
- Some sensors are filed under insulin-pump codes. Example: Guardian 4 sensor Z-1005-2024 is under OZP. guess: a robot that only uses CGM codes will miss a few such records.
- Records per code: MDS 57, QBJ 23, QLG 10, PQF 4, PZE 3, OZP 3, QRX 2, PHV 2, QHJ 1.

## 4. CGM recalls found

- Raw hits: 105 records, 41 events (one event = one problem; it can cover many products).
- Removed 9 events that are really insulin pumps, pump apps or a meter. Left: **32 CGM events, 95 records.**
- Class by event: Class I = 7, Class II = 23, no class in API = 2.

| Recall number(s) | Date started | Class | Firm | Short reason |
|---|---|---|---|---|
| Z-2574-2026 | 2026-05-27 | II | Dexcom | Stolen scrap G7 sensors resold to pharmacies |
| Z-2163..2165-2026 | 2026-04-14 | II | Dexcom | G7 app bug delays glucose alerts |
| Z-1020..1023-2026 | 2025-11-24 | I | Abbott | Libre 3 / 3 Plus sensors read falsely low |
| Z-0770-2026 | 2025-11-03 | II | Get Tested Intl. | CGM sold without FDA clearance |
| Z-0594-2026 | 2025-10-21 | II | Medtronic | CareLink Clinic shows wrong sensor glucose graph |
| Z-0318-2026 | 2025-08-28 | I | Dexcom | G6 Android app crashes; no readings or alarms |
| Z-2446..2450-2025 | 2025-07-24 | I | Dexcom | G7/ONE+ app: no "sensor failed" alert |
| Z-1943..1946-2025 | 2025-05-12 | I | Dexcom | G6 receiver speaker fails; alarms missed |
| Z-0033-2026 | 2025-05-07 | II | Medtronic | Simplera sensor cap label; sterility risk |
| Z-1906-2025 | 2025-05-05 | II | Dexcom | G7 iOS app freezes on old reading |
| Z-1202..1204-2025 | 2025-01-27 | II | Dexcom | G6 receiver may miss high/low alarms |
| Z-2692-2024 | 2024-07-24 | I | Abbott | Libre 3 sensors read falsely high |
| Z-1005-2024 | 2023-11-15 | II | Medtronic | Guardian 4 enzyme layer off-spec; wrong readings |
| Z-2414-2023 | 2023-07-12 | II | Abbott | Libre 2 reader rejects new sensor |
| Z-1273..1275-2023 | 2023-02-13 | I | Abbott | Libre reader battery swells; fire risk |
| Z-0734-2024 | 2023-02-09 | II | Abbott | Libre 3 app on Android 13 loses signal |
| Z-0776-2023 | 2022-11-21 | II | Medtronic | Guardian app logs out; data stops uploading |
| Z-1930, 1931, 1934-2021 | 2021-03-16 | II | Cardinal Health | Shipped too cold; readings may be wrong |
| Z-1599..1618-2021 | 2021-02-26 | II | Medtronic | Hydroxyurea drug falsely raises readings |
| Z-2980-2020 | 2020-07-15 | II | Medtronic | Guardian Connect app stops uploading data |
| Z-1560..1562-2020 | 2020-02-03 | II | Dexcom | Hydroxyurea drug falsely raises readings |
| Z-1104-2020 | 2019-11-19 | II | Dexcom | G6 iOS low alarm silent with schedule |
| Z-0251-2020 | 2019-09-18 | II | Senseonics | Eversense sensors stop working early |
| Z-0929-2020 | 2019-07-12 | II | Dexcom | Receiver stuck on start-up screen |
| Z-2106-2020 | 2019-05-20 | II | Medtronic | Guardian app on iOS 12 drains transmitter |
| Z-1282-2019 | 2018-07-04 | II | Medtronic | Guardian app closes silently; alerts missed |
| Z-2898-2016 | 2016-08-05 | II | Medtronic | iPro software wrong time stamps |
| Z-1334..1339-2016 | 2016-02-23 | I | Dexcom | G4 receiver alarm may not be heard |
| Z-2442-2015 | 2015-07-22 | II | Medtronic | Guardian monitor Finnish translation error |
| Z-2179-2014 | 2014-07-21 | II | Medtronic | Guardian monitor may not be water-resistant |
| Z-0820..1461-2010 (20) | 2009-04-14 | none | Abbott | Navigator case cracks; moisture, bad readings |
| Z-1196-2009 | 2008-11-01 | none | Abbott | Navigator receiver set to wrong units |

- Libre 3 Nov 2025 sensors in commerce (4 records added up): 2,990,939
- Injury/death count (FDA news page only): "As of January 7, 2026, Abbott has reported 860 serious injuries, and seven deaths."

## 5. What this means for the robot

- Use recall.json as the main source. Query by CGM product code. No API key was needed. guess: the no-key limit is 1,000 requests/day (openFDA docs, not tested).
- Add recall class by joining enforcement.json on recall number. Old records (before ~2012, guess:) have no class.
- Drop or trim the `code_info` field. It can be millions of characters of serial numbers.
- Do not use text search alone. Brand names like "Guardian" pull in unrelated devices. Use it only to find stray sensors under pump codes, then check by hand.
- Injury and death counts are only on fda.gov news pages. These need a browser-like user-agent and 30 s between requests (fda.gov robots.txt). guess: only big recalls get such a page. Treat it as a manual add-on for a few key recalls.
- The CDRH web page adds nothing important beyond the APIs. Skip it. (Its robots.txt also asks for 30 s between requests.)
- Health Canada: one easy download, but few details. Use only as a cross-check.
- Not tested: older pages of the FDA news list; a Health Canada search API.
