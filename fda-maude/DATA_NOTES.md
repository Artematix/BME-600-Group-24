# MAUDE CGM data notes (full pull of 2026-10-26)

What this is: every FDA MAUDE report for CGM sensors, flattened to one row per report, with the two story texts.
MAUDE = FDA database of device problem reports. CGM = continuous glucose monitor. Product code = FDA's 3-letter device type.
Pulled by `scripts/maude_robot.py` (new `bulk` command). FDA data as of 2026-10-21 (bulk export 2026-10-23). Newest report received 2026-09-30.

## 1. Where the data came from, and why not the API

- The team's plan was the openFDA API (`api.fda.gov/device/event.json`). That needs about 4,100 calls. The no-key limit is 1,000 calls a day, and the free API key from the 2026-10-19 pull is not on this computer. So the API road would take 5 days.
- The backup road from `access-check/02_bulk-files.md` was used instead: openFDA's bulk files (all of MAUDE, 375 zip files, 19.6 GB). Plain downloads, no key, no daily limit.
- The robot downloaded every zip, read it in a stream, and kept only reports whose device has one of the 13 CGM product codes. Whole reports are kept (nothing trimmed).
- Result: exactly the same reports as the 2026-10-19 API pull (3,382,071; same count for every code). Download: 14 minutes with 6 workers. Clean step: 6 minutes.

## 2. Product codes used (same 13 as before) and why

| Code | FDA device name (short) | Main devices | Reports |
|---|---|---|---|
| QBJ | Integrated CGM, factory calibrated | Dexcom G6/G7, Libre 2 Plus/3/3 Plus | 2,352,192 |
| PQF | Glucose sensor, invasive, non-adjunctive | Dexcom G5, Medtronic Guardian 4 / Simplera | 327,332 |
| MDS | Glucose sensor, invasive | Dexcom G4/G5, older Medtronic | 282,266 |
| QLG | Integrated CGM, not for insulin pumps | Libre 2, Libre 3 | 260,781 |
| PZE | Factory calibrated, user-initiated | Libre 14 day | 143,132 |
| SFI, SBA, SAF, QHJ, QCD, QDK, QII, SBH | smaller CGM codes | Simplera Sync, Eversense, Stelo, Lingo, G6 Pro | 16,459 |
| All 13 | | | 3,382,071 (each report once; 91 reports list two codes) |

Check with the API count feature (`count=device.device_report_product_code.exact`, 2026-10-26):

| Brand word in `brand_name` | Reports | Inside the 13 codes | Biggest code outside |
|---|---|---|---|
| Dexcom | 2,445,171 | 100.0% | OYC 130 |
| Libre | 713,534 | 100.0% | NBW 86 (blood glucose meters) |
| Eversense | 7,753 | 100.0% | - |
| Stelo | 2,716 | 100.0% | - |
| Simplera | 4,643 | 99.8% | OZP 8 |
| Guardian (Medtronic) | 28,045 | 20.0% | OZP 20,334 |

- Not used: OZP, OZO (automated insulin dosing systems), OYC (insulin pump used with a glucose sensor), QFG (pump), NBW (blood glucose meters), PHV (CGM software).
- Caveat: most Medtronic sensor reports sit under the pump-system codes OZP and OYC (reports listing a "glucose sensor" device: OYC 414,246). The 13 codes cover Dexcom, Abbott and Senseonics almost fully, but only a small part of Medtronic. Same scope as the earlier pull; kept so results stay comparable.

## 3. Files made (all gitignored; layout follows `README.md`, not a new `data/` folder)

| File | What | Size | Rows |
|---|---|---|---|
| `raw/bulk/<quarter>_<part>.jsonl.gz` (375 files) | whole CGM reports as JSON lines, one file per FDA zip | 1,014 MB | 3,382,071 |
| `raw/bulk/manifest.json`, `download_log.jsonl`, `raw/state.json` | file list from FDA, download log, finished-file list | small | |
| `raw/bulk_zips/` (375 zips) | the FDA zips themselves (kept for re-filtering, e.g. pump codes). Safe to delete | 19.6 GB | 26,557,775 (all MAUDE) |
| `clean/full.parquet` | the flattened table (fast; read with pandas/pyarrow) | 254 MB | 3,382,071 x 88 columns |
| `clean/full.csv.gz` | same rows and columns as CSV | 452 MB | 3,382,071 |
| `clean/serious.csv.gz` | death + injury rows only (input of `report_results.py`) | 43 MB | 123,607 |
| `results/recalls_cgm.csv` | CGM recall records (refreshed 2026-10-26) | 0.3 MB | 96 records, 33 events |

Columns: the 25 original ones (`mdr_report_key`, `report_number`, `date_received`, `date_of_event`, `event_type`, `product_code`, `brand_name`, `generic_name`, `manufacturer`, `model_number`, `lot_number`, `product_problems`, `patient_outcome`, `patient_problems`, `patient_age`, `patient_sex`, `patient_weight`, `patient_race`, `patient_ethnicity`, `report_source_code`, `reporter_country_code`, `n_devices`, `n_patients`, `event_text`, `mfr_narrative`) plus 63 new ones after them: `openfda_device_name`, `patient_age_value` + `patient_age_unit`, `all_product_codes`, `n_mdr_text`, `event_text_len`, `mfr_narrative_len`, `type_of_report`, `remedial_action`, `source_type`, `summary_report_flag`, more dates, flags, UDI, and `repeated_report_number`.
- `event_text` = story type "Description of Event or Problem" (D5). `mfr_narrative` = "Additional Manufacturer Narrative" (H10). Several stories of one type are joined with " | ".
- Lists (problems, outcomes, report types) are joined with "; " (not "|"), because `report_results.py` splits on ";".
- Dates are text `YYYYMMDD`. Manufacturer address and contact fields are not in the table; they are in `raw/bulk/`.

## 4. How to re-run (from the repo root; Windows: plain `python`, not `python -I`)

```
python fda-maude/scripts/maude_robot.py bulk --workers 6           # download + filter. Resumes. Add --keep-zips to keep the zips
python fda-maude/scripts/maude_robot.py clean --tiers bulk          # full.csv.gz, full.parquet, serious.csv.gz
python fda-maude/scripts/maude_robot.py recalls                     # results/recalls_cgm.csv (43 API calls)
python fda-maude/scripts/maude_robot.py status                      # progress
```
Needs `requests`, `pandas`, `pyarrow` (for the parquet). A re-run later gives newer FDA data, so numbers will change a little.

## 5. Counts

By year received (all 13 codes). Before 2014: 14,075 reports (17 of them before 2008).

| Year | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (to Sep) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Reports | 36,209 | 39,944 | 97,218 | 114,093 | 164,535 | 130,936 | 221,133 | 352,236 | 286,649 | 344,344 | 415,499 | 447,015 | 718,185 |
| Deaths | 8 | 71 | 104 | 29 | 12 | 9 | 10 | 5 | 11 | 22 | 32 | 94 | 118 |
| Injuries | 1,049 | 1,291 | 1,865 | 1,423 | 3,306 | 4,780 | 4,777 | 7,963 | 13,726 | 20,598 | 20,231 | 16,410 | 18,163 |

By event type: Malfunction 3,257,570 | Injury 122,984 | Death 623 | Other 819 | blank 75.

By brand (`brand_name` upper-cased, spaces squeezed; spellings still vary) and by manufacturer (top 10):

| Brand (top 15) | Reports | Manufacturer | Reports |
|---|---|---|---|
| DEXCOM G6 CONTINUOUS GLUCOSE MONITORING SYSTEM | 1,341,417 | DEXCOM, INC. | 2,481,737 |
| DEXCOM G7 CONTINUOUS GLUCOSE MONITORING SYSTEM | 659,816 | ABBOTT DIABETES CARE INC | 558,357 |
| DEXCOM G5 MOBILE CONTINUOUS GLUCOSE MONITORING SYSTEM | 332,470 | ABBOTT DIABETES CARE LTD | 160,484 |
| FREESTYLE LIBRE 2 | 159,550 | MEDTRONIC MINIMED | 128,918 |
| FREESTYLE LIBRE 3 | 145,818 | DEXCOM INC. | 22,457 |
| FREESTYLE LIBRE 3 PLUS | 110,139 | SENSEONICS INC. | 7,255 |
| LIBRE SENSOR FREESTYLE | 77,783 | ABBOTT DIABETES CARE INC. | 4,774 |
| LIBRE 2 SENSOR FREESTYLE | 76,422 | ANIMAS CORPORATION | 4,323 |
| FREESTYLE LIBRE 2 PLUS | 65,376 | MEDTRONIC PUERTO RICO OPERATIONS MED-REL | 3,545 |
| DEXCOM G4 PLATINUM CONTINUOUS GLUCOSE MONITORING SYSTEM | 53,653 | MEDTRONIC PUERTO RICO OPERATIONS CO. | 2,434 |
| G4 PLATINUM CONTINUOUS GLUCOSE MONITORING SYSTEM | 48,908 | | |
| TRANSMITTER MMT-7841ZN GST5G US (Medtronic) | 42,331 | | |
| FREESTYLE LIBRE 14 DAY | 34,693 | | |
| TRANSMITTER MMT-7841ZW GST5G OUS (Medtronic) | 32,371 | | |
| DEXCOM G7 15 DAY CONTINUOUS GLUCOSE MONITORING SYSTEM | 17,754 | | |

Brand families (simple word rules on `brand_name`; all reports / death + injury): Dexcom G6 1,350,954 / 13,113; Dexcom G7 680,526 / 13,451; Dexcom G5 334,115 / 3,200; Dexcom G4 130,266 / 2,801; Libre 2 (+Plus) 307,014 / 41,503; Libre 3 (+Plus) 271,168 / 18,354; Libre 14 day 48,471 / 13,216; Libre unclear 95,856 / 4,534; Simplera 14,080 / 254; Eversense 7,754 / 2,992; Guardian/Enlite 6,538 / 150; Stelo 2,716 / 161; other or blank 130,166 / 9,615.

## 6. How often fields are filled in (% of 3,382,071 reports; blank, "NA", "Unknown" count as empty)

| Field | Filled | Field | Filled |
|---|---|---|---|
| patient age (`patient_age_value`) | 73.8% | event text, D5 (`event_text`) | 93.0% |
| patient sex = Male or Female | 45.7% (Female 776,666; Male 767,341; "Prefer Not To Disclose" 31,496) | manufacturer narrative, H10 (`mfr_narrative`) | 92.2% |
| `product_problems` | 99.9% | H10 longer than 20 characters | 31.2% |
| `patient_problems` | 100% (but 2,284,557 say "No Clinical Signs, Symptoms or Conditions") | `date_of_event` | 99.7% |
| `patient_outcome` | 4.0% (mostly filled for deaths and injuries) | `lot_number` / `model_number` | 67.5% / 78.8% |

Age: median 52 years; units YR 2,484,843, MO 11,822, DA 289, WK 33.

## 7. Story (narrative) length

| Text | Median | 90th percentile | Longest | Note |
|---|---|---|---|---|
| D5 event text | 405 characters, about 66 words | 740 characters, about 117 words | 21,030 characters | 237,536 reports (7.0%) have no text at all |
| H10 manufacturer narrative | 7 characters, 1 word | 1,107 characters, about 180 words | 25,557 characters | 1,631,024 (48%) are only "(B)(4)." = redacted by FDA |

Words are estimated as spaces + 1. Total text: 1.42 billion characters (D5) + 0.92 billion (H10). Many stories are template sentences: the top D5 text ("A customer reported receiving erroneous glucose results from an Abbott Diabetes Care...") appears 103,690 times.

## 8. Example stories (public FDA text, cut at 300 characters; "(B)(6)" = FDA redaction)

1. Abbott, Injury, QLG, FreeStyle Libre 2, 2024: "A HIGH READINGS ISSUE WITH THE ABBOTT DIABETES CARE (ADC) DEVICE WAS REPORTED. CUSTOMER RECEIVED UNSPECIFIED HIGHER SENSOR SCAN RESULTS COMPARED TO UNSPECIFIED READINGS OBTAINED ON A COMPETITOR BRAND METER AND EXPERIENCED FEELING DIZZY, WEAKNESS, AND A SEIZURE. CUSTOMER WAS UNABLE TO SELF-TREAT AND ..."
2. Abbott, Malfunction, QBJ, Libre 2 Plus, 2026: "A customer reported receiving erroneous glucose results from an Abbott Diabetes Care device. The customer received sensor scan results of 4.60 mmol/L,5.20 mmol/L compared to glucose values of 11.10 mmol/L,13.20 mmol/L respectively obtained on the comparison device, when plotted on a Parkes Error Gri..."
3. Dexcom, Injury, QBJ, G7, 2026: "It was reported that a detached or missing sensor wire occurred. The sensor was inserted into the arm. According to the patient, on (b)(6) 2026, the patient felt something under the skin and went to the hospital. The doctor examined the arm where the sensor had been inserted but did not find anythin..."
4. Dexcom, Malfunction, QBJ, G6, 2024: "IT WAS REPORTED THAT A SIGNAL LOSS OCCURRED. NO PRODUCT OR DATA WAS PROVIDED FOR EVALUATION. THE ALLEGATION AND A PROBABLE CAUSE COULD NOT BE DETERMINED. NO INJURY OR MEDICAL INTERVENTION WAS REPORTED."
5. Dexcom, Death, QBJ, G7, 2026 (consumer report): "MY MOTHER WENT INTO DIABETIC KETOACIDOSIS (B)(6) 2025 AND WAS HOSPITALIZED UNTIL (B)(6) 2025. THIS CAME A WEEK AFTER STOPPING PREDNISONE FROM HER HAVING A BAD ALLERGIC REACTION TO THE DRUG SHE WAS TAKING FOR HER POISON IVY, HER FACE SWELLED UP PRETTY BAD IT WAS HARD FOR HER TO SEE. ON (B)(6) 2025 SH..."

Style: Dexcom and Abbott stories are short and template-like. Older reports are ALL CAPS, 2026 reports are mixed case. Consumer reports (8,258) are free text.

## 9. Oddities

- Duplicates: 0 duplicate `mdr_report_key` (each report sits in one FDA file). 44 rows share a `report_number` (flag `repeated_report_number`); kept, not removed.
- 91 reports list two CGM codes (`all_product_codes`). They are counted once here. The old tier-1 count tables count them twice, so by-code sums there are 91 higher (65 of the 91 are injuries).
- Follow-up reports: `type_of_report` is "Initial submission" 2,548,790; "Initial submission; Followup" 821,291; "Followup" only 2,785. FDA merges follow-ups into the first report, so there is no separate supplemental row. 117,128 have `mfr_report_type` "Follow-Up"; 56,686 "FDA Requested".
- Summary reports: none (`summary_report_flag` always "N", `noe_summarized` always 1). One row = one event.
- 75 reports have a blank `event_type`; 819 say "Other".
- Dates: all `date_received` parse. 456 reports have an event date after the received date. 116,855 (3.5%) were received more than 2 years after the event (late reporting; this makes the 2026 Libre 3 surge). Median lag event to received: 26 days. 17 reports with CGM codes were received 1992-2007, before these devices existed (guess: code assigned later).
- Patient outcome uses two styles: words ("Required Intervention" 66,368, "Hospitalization" 13,282) and letters ("O" 4,674, "H" 4,286, "R" 2,414). Treat as the same.
- `source_type` casing varies ("Consumer" 1,863,548 vs "CONSUMER" 870,353). Country codes mix two systems: "GM" 181,254 and "DE" 76,298 are both Germany; "UK" and "GB" both Britain; "SP" = Spain.
- Brand names are spelled many ways (see section 5). Not cleaned.
- Libre 3 reports by month received: 1,303 to 1,927 per month Jan-Nov 2025, then 4,571 (Dec 2025), 31,712 (Apr 2026), 48,271 (Aug 2026). Same picture as the 2026-10-19 check.

## 10. Checks against the earlier (2026-10-19) pull

- Per-code totals: identical for all 13 codes. Deaths per code: identical. Serious table: 123,607 rows, same as before.
- `report_results.py` run in a sandbox with the new `serious.csv.gz`: 24 of 33 tables byte-identical (all headline tables: scope, reports by maker/code/family, per year, problem families, Libre 3 months, recalls). 2 tables have the same rows in a different order. 7 tables (patient outcome, age, sex, keyword counts) move by less than 0.5% (e.g. "Required Intervention" 64,888 -> 64,748). guess: FDA edited patient fields of some reports between the 10-07 and 10-21 updates. The committed report files were not touched.
- Recalls: 96 records, 33 events (was 95 / 32). New: Z-0203-2027 (Medtronic CareLink Clinic software, 2026). One record (Z-0318-2026) has edited text. git shows the whole file changed only because of line endings.
- Libre 3 early alert (860 injuries, 7 deaths): not in any FDA API; only on the fda.gov news page. Already typed in by hand in `results/recall_harm_manual.csv`. Nothing new fetched.

## 11. Where this differs from the task brief

- Table is at `clean/full.parquet` and `clean/full.csv.gz`, not `data/maude_cgm.parquet`: the README's layout was kept.
- Download by bulk files, not by API date slices: no API key here. The robot's API road (`full`) still exists and gives the same result with a key.
- Lists are joined with "; " not "|" (compatibility with the report script).
- Recalls stayed in `results/recalls_cgm.csv` (README path), refreshed by the robot's own `recalls` command.
