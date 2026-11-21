# Fact sheet for the paper (built 2026-11-20)

One place to look up every fact the paper states. Facts only. Each fact has its source.

- "NOT FOUND" = the repo does not record it. "guess:" = an inference. "derived" = worked out from counts in the row.
- Minus signs are plain hyphens. Ranges are written "a to b". Sources: `file:line`, `file sN` (section N) or `file -> json key`. Paths start at the repo root.
- CGM = continuous glucose monitor (the skin sensor). Meter = fingerstick blood glucose meter, treated as the truth. Pair = one sensor reading matched in time to one meter value.
- MARD = mean absolute relative difference, the average percent error. Bias = average of (sensor minus meter); negative = the sensor reads low. CI = 95 % confidence interval. IQR = the middle half (Q1 to Q3).
- Set B = verified pairs from all 226 people (headline). Set A = same rules, CGM+BGM arm after randomisation, 77 people.
- Research question given for the paper: "How large must a CGM error be before it changes a treatment decision, and how large are CGM errors in practice, both in reported failures and in normal operation?" Repo wording: OV:10.

Short names for source files:

- `docs/`: OV = PROJECT_OVERVIEW.md. NC = team-docs/2026-11-09_team-update_number-check.md. PLAN = team-docs/2026-10-26_midterm-plan-summary.md (summary of plans/2026-10-23_midterm-research-plan.pdf). README = README.md at the repo root.
- `analysis/`: FIND = FINDINGS.md. METH = METHODOLOGY.md. PRE = PREPROCESSING.md. REPRO = REPRODUCIBILITY.md. ACC = ACCURACY_V2.md. ACCJ = accuracy_v2_stats.json. ED = ERROR_DRIVERS.md. SUB = SUBGROUPS.md. DD = DEMOGRAPHICS_DEEP.md. DF = DEMOGRAPHICS_FOLLOWUP.md. WD = WEAR_DAY.md. SIM2 = SIMULATION_V2.md. S2J = simulation_v2_stats.json. SIM3 = SIMULATION_THREE_FAULTS.md. S3J = simulation_three_faults_stats.json. LOOKX = simulation_v2_lookup_extended.csv. LOOK3 = simulation_three_faults_lookup.csv. RES = RESULTS.md and SIM1 = SIMULATION_RESULTS.md (first pass, superseded).
- `fda-maude/`: FR = README.md. FM = METHODOLOGY.md. DN = DATA_NOTES.md. GOLD = gold/GOLD_SET.md. CHG = prompts/CHANGELOG.md. PULL = results/PULL_SUMMARY.md. FI = results/FIELD_INVENTORY.md. RR = results/report/report_results.md. CS = results/report/country_spread.md. In results/text/: TR = TEXT_RESULTS.md, VAL = VALIDATION.md, RUN = RUN_SET.md, BC = BRAND_COMPARISON.md, RX = REGEX_V2_FULL_CORPUS.md, PILOT = PILOT.md, BRAND CSV = tables/g_brand_error_sizes.csv, MALF CSV = tables/h_malf_vs_serious_errors.csv.
- RBG-README = `Uncommitted Data/Raw Data Dump/Replace-BG Dataset/ReadMe.rtf` (the dataset's own documentation).
- Two files appeared on 2026-11-20 while this sheet was built. REFS = `docs/paper/REFERENCES.md` (a checked reference list; cited here by its own entry numbers, such as REFS [7]). TAIL = `analysis/TAIL_COMPARISON.md` (numbers in `analysis/tail_comparison_stats.json`).

## A. Datasets

### A1. REPLACE-BG (primary)

| Item | Fact | Source |
|---|---|---|
| Name and maker | Dataset title: "A Randomized Trial Comparing Continuous Glucose Monitoring With and Without Routine Blood Glucose Monitoring in Adults with Type 1 Diabetes". Older memos use only "REPLACE-BG"; the dataset ReadMe header reads "T1D Exchange" and calls the study "Protocol H". Made by the Jaeb Center for Health Research / T1D Exchange (US). Trial registration number: NOT FOUND | REFS [8]; RBG-README; README:76; RES ("The data we have") |
| Where, version, date | `https://public.jaeb.org/dataset/546` (Jaeb public dataset 546). Version or release: NOT FOUND. "Accessed Oct 7, 2026". guess: local raw files were last modified 2026-10-07 11:52 | README:76 |
| Publication | G. Aleppo et al., "REPLACE-BG: A Randomized Trial Comparing Continuous Glucose Monitoring With and Without Routine Blood Glucose Monitoring in Adults With Well-Controlled Type 1 Diabetes," Diabetes Care, vol. 40, no. 4, pp. 538-545, Apr. 2017, doi:10.2337/dc16-2482. Design as recorded: randomised noninferiority trial, 14 sites, 26 weeks, 2:1, HbA1c 9.0 % or less | REFS [7]; README:76 |
| Population | 226 US adults with type 1 diabetes, 14 clinic sites, 2015-16, all on insulin pumps. Age median 43 (IQR 31 to 55), range 19 to 78. 114 men, 112 women. Race: White 212 (94 %), Black 5, Asian 4, more than one 3, unknown 2. Ethnicity: not Hispanic 216, Hispanic or Latino 9, unknown 1 | README:76; DD:20,25-29 |
| Other traits, arms | HbA1c median 7.3 % (IQR 6.8 to 7.8); BMI 26.7; diabetes for 21.5 years; 77 % with a degree; 88 % privately insured; no severe low in the past 12 months (entry rule). Arms: CGM-only 149, CGM+BGM 77. Run-in before randomisation: median 69 days | DD:38-45,75-78,82 |
| Sensor | Dexcom G4 Platinum ("G4 Platinum Receiver"). Shows 39 to 401 mg/dL only. One reading per 5 min. 7-day sensor, 2-hour warm-up, user calibration (2 at start, then every 12 h). Software version: not stated in the data or the ReadMe (the memos write "guess: Software 505"); the trial paper's full text says "Dexcom G4 Platinum CGM System with an enhanced algorithm (Software 505)" | PRE:59,84,108; WD:5; FIND:226; REFS [7] |
| Reference meter | Contour Next: 168,781 of 168,990 verified pairs. Precision Xtra: 209 (used as a ketone meter) | SUB:152; `analysis/demographics_followup_stats.json` -> run.meter_models_in_verified_pairs |
| Study length | 26 weeks after the run-in. Analysis window: day 0 to 329 from enrolment. Sensor data per person: median 235 days (IQR 200 to 252). 217 completed, 9 dropped | OV:33; PRE:57; DD:79-80 |
| Independent case; records per person | The participant (226). One person gives many records: 14,807,435 sensor readings in all (13,705,193 in the window), median 286 per person-day. Verified pairs per person: median 719 (IQR 517 to 970), range 42 to 1,976 (Set B); Set A median 399, range 1 to 1,368 | METH:33; PRE:27,31; SUB:45,61; ACCJ -> sets.B.definition_counts; ACC:35 |
| Main variables | Sensor glucose and time, calibrations (HDeviceCGM); meter readings (HDeviceBGM); device per upload (HDeviceUploads); pump dose-calculator records: typed glucose, insulin sensitivity factor, target, insulin on board (HDeviceWizard); arm; screening traits, questionnaires, medications, conditions | REPRO:44-47,19; PRE:98-106 |
| Terms and privacy in the dataset's own ReadMe | "Fields that were deemed unnecessary for analysis are not included in public data tables". "All patient IDs and dates have been de-identified. Some data which may contain identifiable information is not contained within the data files." Dates are "number of days from enrollment". No data-use or sharing terms are written in `ReadMe.rtf` or `ReadMe_BasalData.rtf` | RBG-README (intro); PRE:55 |
| Terms as stated in the repo | "Jaeb terms of use. No redistribution." (README). "Data-use terms were not checked; leaving them out is the safe choice." (log). Dataset web page, as read on 2026-11-20: the download needs name, email, institution, planned use and a tick box for the terms of use; the terms ask for a set attribution sentence, give no warranty and put all liability on the user; the page names no licence, and the words "no redistribution" are not on it. The attribution sentence itself: NOT FOUND (it is not in the local ReadMe) | README:76,80; `logs/2026-11-20_1400_push-and-three-fault-simulation.md`; REFS [8] |
| Bias and representation limits | Adults only; 94 % White; 77 % with a degree; well-controlled pump users; no recent severe hypoglycaemia; home-meter reference; fingersticks chosen by the patient | SUB:187-189; FIND:225-228 |

### A2. Shanghai T1DM / T2DM (comparator only)

| Item | Fact | Source |
|---|---|---|
| Name, maker, where | "ShanghaiT1DM / T2DM" (a longer official name: NOT FOUND). Zhao et al. (2023). Figshare, doi:10.6084/m9.figshare.c.6310860 | README:77; RES ("The data we have") |
| Version, date, publication | Figshare collection ver. 2 (2023-01-04); data file version 5 (2023-10-30). Which version the team downloaded: NOT FOUND (guess: the local folder name starts "2022.11"). "Accessed Oct 7, 2026"; guess: local files last modified 2026-10-07 11:49. Paper: Q. Zhao et al., "Chinese diabetes datasets for data-driven machine learning," Sci. Data, vol. 10, no. 1, Art. no. 35, Jan. 2023, doi:10.1038/s41597-023-01940-7 | REFS [11], [12]; README:77 |
| Population | 112 adults from two Shanghai hospitals, in-patients, "all Chinese adults": 12 type 1 (16 records) and 100 type 2 (109 records). Type 1: 7 women, 5 men, age mean 57.8 (37 to 73). Type 2: 44 women, 56 men, age mean 60.2 (22 to 97). HbA1c median 8.5 % in both. No race, education, income, insurance or site column | README:77; OV:112; RES s4; DD:85 |
| Sensor | Abbott flash CGM, "FreeStyle Libre H". One reading per 15 min. Values 39.6 to 475 mg/dL. Older memos say the model is "not confirmed from the paper"; the dataset paper's full text names the FreeStyle Libre H and does not name the meter. Software version: NOT FOUND | README:60,77; RES s5; PRE:133,150; REFS [11] |
| Study length | 3 to 14 days per patient. Per file: median 12.7 days, range 2.6 to 13.9. (OV:34 and README:77 say "about 2 weeks".) | DD:85; RES s5 |
| Independent case; records | The patient. 125 files, one per patient visit (10 patients had 2 or 3 visits). 127,982 sensor readings; 4,012 fingersticks; 17 files with none. 98 of 112 patients have a pair; pairs per patient median 37.5, range 1 to 176 | RES s4-5; PRE:46-47; ACC:32; ACCJ -> sets.S.definition_counts |
| Main variables | Sensor glucose, fingerstick glucose (CBG), blood ketone, diet, insulin dose; summary sheets: sex, age, BMI, diabetes type and duration, complications, lab tests | `analysis/preprocess.py:636-645`; DD:87-106 |
| Terms and privacy | No ReadMe or documentation file is in the local Shanghai folder. Repo: "CC BY 4.0 (reuse allowed with credit)"; the Figshare record gives CC BY 4.0 as the licence of the data file | README:77; REFS [12] |
| Bias and representation limits | Low range not estimable (6 pairs under 54, 44 at 54 to 69). Timing known only to 7.5 min. 10 type 1 patients with pairs. Lab tests missing in 20 to 50 % of type 2 records | ACC:193; ED:136-137; RES s4 |

### A3. FDA MAUDE problem reports and FDA recall records

| Item | Fact | Source |
|---|---|---|
| MAUDE: name, maker, where | "Manufacturer and User Facility Device Experience (MAUDE) Database"; older memos say "FDA database of device problem reports". US FDA, served by openFDA (updated weekly): `https://api.fda.gov/device/event.json`, and openFDA bulk files (375 zip files, 19.6 GB). Publication: NOT FOUND | REFS [13], [14]; FR:31; `fda-maude/access-check/01_openfda-event-api.md:5`; DN:10 |
| MAUDE: version and pull date | Pull 1 (API): FDA data last updated 2026-10-07, pulled 2026-10-19, cleaned 2026-10-20. Pull 2 (bulk files; used by the text step): FDA data as of 2026-10-21, bulk export 2026-10-23, memo titled "full pull of 2026-10-26". Both hold the same 3,382,071 reports | FR:15; PULL:3-4; DN:1,5,12 |
| MAUDE: scope and population | All reports for 13 CGM product codes, all brands, received 1992-03 to 2026-09. Devices: Dexcom G4, G5, G6, G7; Abbott Libre 14 day, 2, 3 (and Plus); Medtronic Guardian, Simplera; Senseonics Eversense; Stelo; Lingo (software versions: NOT FOUND). Reporter country: US 63.8 %, other 29.0 %, blank 7.2 %. Age filled 73.8 %, median 52. Sex filled 45.7 % (776,666 female, 767,341 male). Race and ethnicity filled 0.3 %. Diabetes type: NOT FOUND | RR:7-8; DN:18-24,99,103-111; CS (Result 1); PULL:79-82 |
| MAUDE: independent case | One report (`mdr_report_key`). 0 duplicate keys. 91 reports list two CGM codes and are kept once | DN:134-135; FR:228-230 |
| MAUDE: many records per event? | Possible. The same event can be reported by the patient and by the maker; repeat reports about one sensor are not removed; 44 rows share a report number; FDA merges follow-ups into the first report. How many events are reported more than once: NOT FOUND | RR:206; BC:339; DN:134-136 |
| MAUDE: main variables | Event type, product code, brand, maker, product problems, patient problems, patient outcome, age, sex, reporter country, date received, date of event, event text (D5), maker narrative (H10); 88 columns | DN:52-53 |
| MAUDE: terms and privacy | "Public US government data". Texts carry FDA redactions "(B)(6)" and "(B)(4)". Team rule: no personal details quoted from report texts | README:78,164; DN:118,122 |
| MAUDE: bias and representation limits | Voluntary reporting; counts are not failure rates; no count of sensors in use; 3.5 % of reports arrive more than 2 years after the event; only about 20 % of Medtronic Guardian reports sit under the 13 codes; age and sex often missing. FDA's own words: "MDR data is not intended to be used either to evaluate rates of adverse events, evaluate a change in event rates over time, or to compare adverse event occurrence rates across devices." | RR:203-209; DN:38,139; FR:248-252; REFS [13] |
| Recalls: source and date | FDA recall database via openFDA (`api.fda.gov/device/recall.json`, `api.fda.gov/device/enforcement.json`). Pulled 2026-10-19; refreshed 2026-10-26 | `fda-maude/access-check/04_recalls.md:13-14`; PULL:3; DN:50 |
| Recalls: size and classes | 95 records, 32 recall events (2026-10-19); 96 records, 33 events after the refresh. Memos and tables use 32: 7 Class I (most serious), 23 Class II, 2 old events with no class | PULL:16,34; DN:50,149; `fda-maude/results/recalls_cgm.csv` |
| Recalls: independent case; search | A recall event = one FDA action; it can have several records, one per product model. Search: the 13 CGM codes, extra codes PYV, QDL, SJD, PJT, PHV, QRX, pump code OZP with the word "sensor", and text searches; 9 pump or meter events removed by a fixed list | RR:138; `fda-maude/scripts/config.json:27-47` |
| Recalls: variables; harm counts; limits | Recall number, event id, class, dates, firm, product, reason, root cause, quantity ("quantity" is the sum of numbers in the FDA records; units differ; rough size only). Harm counts exist only for the Nov 2025 Libre 3 recall: 860 injuries, 7 deaths, as of 2026-01-07, typed by hand from the fda.gov recall page ("As of January 7, 2026, Abbott has reported 860 serious injuries, and seven deaths associated with this issue"). The action started 2025-11-24 and was classified Class I on 2026-02-04. "Approximately 3 million" sensors is Abbott's number; the FDA records sum to 2,990,939 | `fda-maude/results/recalls_cgm.csv` (header); RR:154; `fda-maude/results/recall_harm_manual.csv`; PULL:86; REFS [1], [2], [3] and its section 3 |

## B. Inclusion and exclusion, with counts

| Data | Step | Rule (plain fact) | Count left | Source |
|---|---|---|---|---|
| Trial | 0 | Rows in the meter table; ketone rows removed | 583,985; then 580,577 meter readings (312,756 from meter logs, 267,821 from pump uploads) | PRE:34-35 |
| Trial | 1 | Meter value must be 20 to 599 mg/dL (16 below 20 and 34 at or above 600 removed) | 580,527 | PRE:36,42,60 |
| Trial | 2 | A sensor reading must exist within 5 minutes; the nearest one is used | 475,502 pairs (81.9 %), 226 people; MARD 10.4 % (9.9 to 10.9). This was the midterm set | PRE:42; ACC:41 |
| Trial | 3 | Inside the study window, day 0 to 329 | 460,634; MARD 10.2 % (9.8 to 10.7) | ACC:42 |
| Trial | 4 | Meter value comes from the meter's own log (pump "BG" entries removed) | 285,166; MARD 11.9 % (11.4 to 12.3) | ACC:43 |
| Trial | 5 | Meter value was not used to calibrate the sensor (no calibration with the same value within 5 min) = verified pairs, Set B | 168,990, 226 people; MARD 13.3 % (12.7 to 13.9) | ACC:44; PRE:63,65 |
| Trial | 6 | CGM+BGM arm only | 43,255, 77 people; MARD 13.7 % (12.4 to 15.3) | ACC:45 |
| Trial | 7 | Randomised phase only = Set A | 33,467, 77 people; MARD 13.8 % (12.3 to 15.7) | ACC:46 |
| Shanghai | 1 | Excel files read (3 lock files skipped; 92 rows without a date dropped, all in one empty file) | 125 files; 127,982 sensor readings | PRE:46-47 |
| Shanghai | 2 | Fingerstick written on a sensor row (the nearest 15-min row) | 4,012 pairs from 4,012 fingersticks; 98 of 112 patients | PRE:45; ACC:32 |
| Shanghai | 3 | Per-patient tests need 10 or more pairs | 76 patients; 3,926 pairs | SUB:159 |
| MAUDE | 1 | Reports whose device has one of the 13 CGM product codes; each report once | 3,382,071 (Malfunction 3,257,570; Injury 122,984; Death 623; Other 819; blank 75) | DN:24,77 |
| MAUDE | 2 | Event type Death or Injury ("serious") | 123,607 (65 double-coded copies removed from 123,672 downloads) | PULL:14,33; RR:88 |
| MAUDE | 3 | Serious, received on or before 2026-07-21 (3 months before the data snapshot), with text | 118,462 (5,135 too recent, 10 without text) | RUN:18-22 |
| MAUDE | 4 | Malfunction reports received by the same date; random sample by product code x year (95 groups, target 5,000, at least 25 per group, seed 20261019) | frame 2,936,278; 6,168 drawn; 6,137 with text | RUN:23-27 |
| MAUDE | 5 | Texts read by patterns and the model (the run set) | 124,599 | RUN:29; TR:17 |
| MAUDE | 6 | Text states both a sensor value and a meter value | 18,866 | TR:40 |
| MAUDE | 7 | Plausible values only (sensor 20 to 600, meter 20 to 1,500 mg/dL); first pair in the text | 18,445 (18,118 serious + 327 sample); 421 dropped | TR:40 |
| MAUDE | 8 | Serious wrong-reading reports (by the text or by the FDA code family) | 39,667 reports; 17,573 pairs (Abbott 7,470; Dexcom 9,189; Medtronic 379; Senseonics 532; other 3) | BC:34-39 |
| MAUDE | 9 | Patterns alone over all 3,382,071 reports (3,144,535 have text) | 209,388 pairs | RX:76,90 |
| MAUDE | 10 | Of these, in malfunction-only reports (never read by the model) | 191,112 (Abbott 162,072; Dexcom 25,273; Medtronic 3,651; Senseonics 74) | RX:80-84 |
| MAUDE | 11 | Of these, in death or injury reports | 18,237 (18,212 injury, 25 death) | RX:8; MALF CSV (rows All / injury, All / death) |

- Headline set: Set B (decided 2026-10-30). Set A is the check the plan promised. Reason recorded: both give the same numbers and B has tighter CIs (METH:86,104; OV:136; FIND:10). ACC:17,27 (written 2026-10-27) still labels Set A "the headline set"; see D6.
- Other trial sets: C = CGM-only arm, randomised phase, 104,195 pairs, 148 people. D = calibration pairs in the window, 116,244 (ACC:29-30).
- Trial sensor readings: 14,950,661 rows; 143,226 calibration rows moved out; 1,102,160 readings before day 0 (7.4 %); 1,356 duplicate timestamps (lowest record id kept); 13,705,193 in the window. Readings clipped at 39 (28,885) and 401 (48,935) are kept and flagged (PRE:25-32,57-59). 155,636 of the 475,502 pairs are flagged as calibration fingersticks (PRE:43).
- MAUDE values not counted as pairs: 6,433 pairs where a value is a bound ("over 400") and 7,347 reports where the sensor showed a word (LOW, HI) (RX:202).

## C. Methods facts

### C1. FDA pull and text step

| Item | Fact | Source |
|---|---|---|
| Query | `device.device_report_product_code:<code>`, sliced by `date_received`. Codes: QBJ, PQF, MDS, QLG, PZE, SFI, SBA, SAF, QHJ, QCD, QDK, QII, SBH. A start or end date limit: NOT FOUND (none recorded); reports span 1992-03 to 2026-09 | `fda-maude/scripts/maude_robot.py:55,740`; `fda-maude/scripts/config.json:3`; RR:8 |
| Tool and pull date | `fda-maude/scripts/maude_robot.py` (openFDA API; no web scraping). 2026-10-19: 5,011 API calls; full pull 16:05 to 17:55, 4 workers, 997 slices. Second pull from 375 bulk zip files (6 workers, 14 min; clean 6 min) because that computer had no API key | PULL:6,17,23; OV:16; DN:9-12 |
| Cleaning | One row per report; duplicate keys removed; a report with two CGM codes kept once; blank, "NA", "N/A", "Unknown", "UNK", "None" = missing; device fields from the device with a CGM code; brand spellings grouped by keyword; 391 problem terms grouped into 8 families | FR:228-237; RR:13,67 |
| Text step design | Three layers: FDA codes, then patterns (regex = fixed text rules), then a local language model that fills a fixed form; checked against a reference set | FM:65-69 |
| Pattern layer | `fda-maude/scripts/extract_regex.py`: reads the Abbott template, prose pairs, LOW/HIGH display words, Parkes zone, wear day, units (mmol/L x 18, flagged). 124,599 reports in 95 s. Finds both values in Dexcom 25 %, Abbott 7 %, Medtronic 4 % of reports | PILOT:12; VAL:107 |
| Language model | qwen2.5:7b-instruct (7 billion parameters), Q4_K_M (4-bit), 4.7 GB, digest 845dbda0ea48, run locally on Ollama 0.34.3, output forced to a JSON schema. Temperature 0; seed 42; 8 parallel requests; context window 6,144 tokens; report text cut at 6,000 characters; checkpoint every 500 reports. Other sampling settings: NOT FOUND | VAL:3,108; PILOT (s4 note); FR:286; `fda-maude/scripts/llm_extract.py:67` |
| Prompt | Version v3: `fda-maude/prompts/v3_system.txt`, `v3_user_template.txt`, `v3_schema.json` (about 2,900 tokens; frozen after scoring). Input: maker, brand, FDA event type and the event text (D5), plus the maker narrative (H10) when it is longer than 20 characters | FR:267,286; CHG:39-56; FM:106 |
| Fixed form (12 fields) | fault_type (reads_low, reads_high, erratic, stuck, signal_loss, sensor_error_or_early_end, adhesive_or_detachment, insertion_or_skin_injury, other_device, unclear); sensor_value_raw; sensor_unit; meter_value_raw; meter_unit; multiple_pairs; parkes_zone_stated (A to E); wear_day; fingerstick_check_done (yes, no, not_stated); user_action (none, ate_carbs, took_insulin, skipped_insulin, sought_care, other, not_stated); outcome_severity (none, symptoms_only, hypoglycemia, hyperglycemia_or_dka, hospital_or_er, death, not_stated); confidence | `fda-maude/prompts/v3_schema.json` |
| Rules in code | A number the model writes must appear word-for-word in the text, or it is dropped. mmol/L is converted in code (x 18). Final value = the pattern value when the Abbott template matched (and for zone and wear day whenever a pattern found one), else the model value. Error direction is taken from the two numbers, not from the model's label | FM:91-93; TR:8,60 |
| Run and hardware | 2026-10-30, 08:23:50 to 17:57:08 = 9.55 h (34,395 s): 124,599 reports, 217 per minute, 0 errors, 538 million tokens read, 10.4 million written; numbers dropped by the word-for-word rule in 4,324 reports (3.5 %). NVIDIA RTX 5080, 16 GB (11 GB used), Windows 11. CPU and RAM: NOT FOUND | TR:17-21; FM:140-143; VAL:3,109 |
| Reference set | 287 reports from `fda-maude/data/sample_narratives.jsonl`: 50 malfunction and 50 death or injury per maker (Medtronic has 37 serious). Abbott Libre 3: 100; Dexcom G7: 100; Medtronic Guardian: 87. How the 287 were drawn (random or not): NOT FOUND | GOLD:7,17-20 |
| Who labelled it; self-check | One reviewer, "an AI assistant, labeller `ai_reviewer_v1`", read every report in full with a written rubric (`fda-maude/gold/RUBRIC.md`); no language model pipeline was used for any label; which AI: NOT FOUND. Self-check: the same reviewer re-labelled 40 random reports (seed 2026) blind: 100 % agreement on all 11 fields (kappa 1.00); "It is not an independent second labeller" | GOLD:8-12,36-46 |
| Teammate check | "A teammate checked 100 of the 287 reports on 2026-11-08 and found no issues." "No human-versus-model agreement number has been computed." Who, how, and a label file: NOT FOUND | VAL:92; OV:45 |
| Agreement, v3, patterns + model (kappa = agreement beyond chance; 1 = perfect, 0 = chance) | fault_type 0.77 (n 287; Abbott 0.88, n 100; Dexcom 0.71, n 100; Medtronic 0.63, n 87). outcome_severity 0.75, exact 0.745 (0.71 / 0.87 / 0.62). user_action 0.77 (0.84 / 0.81 / 0.58). fingerstick_check_done 0.74. multiple_pairs 0.69. Sampling error of kappa about 0.03. Targets set in advance: 0.70, 0.75, numbers 95 % exact | VAL:14,20-28,34-42 |
| Numbers and repeat run, v3 | Exact among the system's values: 96.2 % (307 of 319): sensor 98 % (80 of 82), meter 94 % (93 of 99), wear day 94 % (51 of 54), zone 99 % (83 of 84). Two runs with the same settings: all ten fields identical in 90.6 % of forms; outcome 100 % | VAL:50-54,69-76 |
| Pattern-only pass | `extract_regex_v2.py`, tuned against the model's pairs on the run set, then run over all 3,382,071 reports in 7.8 min (20 workers, seed 20261106). Share of the model's 18,436 pairs it finds (recall): 89.1 % (was 73.1 %); Abbott 88.3 % (was 62.6), Dexcom 90.5 % (was 81.3), Medtronic 70.0 %. Same two numbers as the model: 88.4 %. Wear-day recall 95 % (was 71 %). Precision not measured on the reference set: of 48 pattern pairs the model did not find, 28 right, 15 join numbers from two moments, 5 wrong | RX:29-38,62-72,76 |

### C2. Accuracy

| Item | Fact | Source |
|---|---|---|
| Matching | Each meter value is paired with the nearest sensor reading within 5 minutes. Calibration pairs: the last sensor reading up to 10 minutes before. Shanghai: the fingerstick sits on the nearest 15-minute sensor row | `analysis/preprocess.py:67-68`; PRE:41-45 |
| Glucose ranges | Under 54, 54 to 69, 70 to 180 (both ends included), 181 to 250, over 250 mg/dL, assigned by the average of the sensor and meter values. The iCGM table bins by the sensor value | ACCJ -> bin_rules; ACC:80,104 |
| Bias, MARD | Error = sensor minus meter. Bias = mean error, in mg/dL and as a percent of the meter value. MARD = mean of the absolute error as a percent of the meter value. Median ARD = the middle such value | ACC:8-9; SUB:5 |
| 15/15, 20/20, 40/40 | Share of pairs within 15 (20, 40) mg/dL when the meter is below 100 mg/dL, or within 15 (20, 40) % at 100 or above | ACC:10 |
| iCGM criteria used (FDA rule 21 CFR 862.1355(b)(6)) | By sensor value. Under 70: within 15 mg/dL (needs above 85 %) and within 40 mg/dL (above 98 %). 70 to 180: within 15 % (above 70 %) and 40 % (above 99 %). Over 180: within 15 % (above 80 %) and 40 % (above 99 %). All pairs: within 20 % (above 87 %). The lower one-sided 95 % bound must pass. No pair may have sensor under 70 with meter over 180, or the reverse | ACC:104-116 |
| Misclassification at 70 and 180; missed low; unconfirmed low | Low = under 70; in range = 70 to 180; high = over 180 (check: 200). Missed low = meter low and sensor not low, as a share of meter lows. False low = meter not low and sensor low, as a share of meter not-lows. Unconfirmed low = the same pairs as a share of all sensor lows (100 % minus the positive predictive value). Missed high, false high, "any wrong category" the same way | ACC:121-141; NC row 19 |
| Confidence intervals | Percentile bootstrap that resamples participants, not pairs. 1,000 resamples, seed 600 (accuracy); 1,000, seed 20261027 (error drivers, simulation v2); 2,000, seed 600 (subgroups, deep demographics, sex follow-up, tail comparison); 1,000, seed 20261106 (wear day, one shared set) | ACC:12; `analysis/error_drivers_stats.json` -> ci; SUB:196; DD:399; WD:233; TAIL:10 |
| Lag (how far the sensor trails blood) | Each fingerstick is re-paired with the sensor reading nearest to (fingerstick time + T), T = -5, 0, 5, 10, 15, 20 min; finer scan on a straight line between readings, 1-min steps from -10 to 20; only pairs with a value at every T (163,174 and 152,072). Best shift = lowest MARD. Lag correction = the reading 5 min later | ED:52 |
| Rate of change | (next reading minus previous reading) / minutes between them; missing unless both neighbours are 4 to 6 min away. Bins in mg/dL per min: falling fast under -2; falling -2 to -1; stable -1 to 1; rising 1 to 2; rising fast over 2 | PRE:61; ED:70-74 |
| Wear day; time of day | No sensor-start marker exists. A new session starts at a gap of 115 min or more. Wear day 1 = the first 24 h after the first reading. A session is "confirmed" when a calibration was entered in the 30 min before its first reading; error-driver results use confirmed sessions, days 1 to 7 (150,690 pairs). Night = 00:00 to 06:00 (device time; for pairs, the meter clock) | PRE:62,83-85; ED:82,97 |
| Day-1 settling vs early removal | Unconfirmed pieces are glued to the session before unless the result passes 170 h: 8,521 sessions. Early removal (selection) = day-1 MARD of all sessions minus day-1 MARD of sessions that reached day 7. Settling = the rest of the day-1 excess over day 7. Settling speed from a floor-plus-exponential fit on 6-hour bins | WD:20-33; METH:170 |
| Mixed model (a regression that knows which pairs belong to one person) | Outcome: percent error of each pair. Fixed effects: range, trend bin, wear day group (1, 2 to 6, 7), night, arm. Random intercept per person. 143,051 pairs, 226 people | ED:106 |
| Pre-specified participant-trait tests | First pass: unit = the participant; 6 traits (age, sex, BMI, HbA1c, diabetes duration, arm); Mann-Whitney or Kruskal-Wallis, Spearman, one regression; Benjamini-Hochberg (BH, a correction for many tests) within the list of 10 tests; 22 exploratory tests with BH; groups under 10 people not tested. Deep check: 680 tests listed before any ran = 407 single-trait tests (61 testable traits x 7 error measures) + 133 interaction tests (18 trait pairs x 7, plus site x arm x 7) + 140 worst-quartile tests; one BH family. Shanghai: 60 tests, own family. Flexible models and mediation: outside the family | SUB:68,79,85,121-122; DD:110-123; `analysis/demographics_deep_stats.json` -> bh_summary |
| Sex follow-up | 74 tests listed in advance in three BH families: 66 REPLACE-BG, 3 Shanghai, 5 MAUDE. Per-person test needs 20 pairs per person and 10 people per sex; else pooled pairs with a participant bootstrap. Matching on glucose bin and trend; adjustment for body size, HbA1c, age, insulin dose. One post-hoc block (blinded run-in) is outside the families | DF:20-35,208 |
| Shanghai comparison | The same metrics and CIs on 4,012 pairs; per-patient tests on 76 patients | ACC:184-193; SUB:158-168 |

### C3. Simulation

| Item | Fact | Source |
|---|---|---|
| True glucose | The recorded trial sensor trace (Dexcom G4) on a 5-minute grid, study window, 226 people, 13,705,193 readings; 19,280 readings (0.14 %) dropped in the gridding. Shown values are clipped to 39 to 401 mg/dL | SIM2:23,33,41; SIM3:7 |
| Dose calculator | Dose = (glucose - target) / insulin sensitivity factor - insulin on board, not below 0, and only when glucose is above the pump's "correct above" level. All four settings come from the patient's own pump record. The rule matches the pump's own recorded correction within 0.15 units in 90 % of records | SIM2:36; S2J -> data.wizard |
| A decision; how many | One use of the pump's dose calculator with a typed glucose and a sensor reading within 5 min. 159,878 decisions from 203 people (median 777 per person, IQR 421 to 991), from 232,329 calculator records in the window (172,929 with a typed glucose). Withheld (skipped) = dose above 0.5 U without the error, 0 U with it. Spurious = the reverse. Changed by more than 0.5 U or 1 U | SIM2:25-26,37 |
| Episodes and alerts | Episode = at least 15 minutes (3 readings) beyond a threshold; it ends after 15 minutes back in range. Thresholds: under 70, under 54, over 180, over 200 mg/dL. A true episode is detected if a shown episode is ongoing from 30 min before its start to its end; else missed. A shown episode with no true one = false alert. True episodes: 47,250 (under 70), 14,823 (under 54), 120,363 (over 180), 99,423 (over 200) over 50,775 participant-days | SIM2:10,24,28-29,39-40 |
| Bias sweep | Constant bias from -40 to +40 % in 2 % steps (41 rows); extended on 2026-10-30 to -90 to +90 % in 2 % steps (91 rows) | SIM2:46,164 |
| Other fault families (version 2) | White noise SD 5, 10, 20 mg/dL. AR(1) noise (each error keeps 80 % of the one before) SD 5, 10, 20. Drift from 0 to -10, -20, -30 % at wear day 7. Dropouts: 2, 5, 10 % of readings lost in gaps of 15 to 120 min. Lag 5, 10, 15 min. Mixed: -20 % bias + AR noise SD 10. 10 random draws per person, seed 20261027 | SIM2:46-53; S2J -> method.faults |
| Three faults: ranges and sizes | False low: true glucose 70 to 250, shown = true - 69.4 % (small -61.9, large -76.7). Hidden low: true under 54, shown = true + 163.6 % (small +88.9, large +328.6). Floor-pinned: true over 250, shown = 39 mg/dL (small case: not pinned, -72.7 %) | SIM3:20-22,47-49 |
| Three faults: FDA source of each size | False low: median error of malfunction-only pairs that read low (quartiles from 10-point bins). Hidden low: serious pairs with the sensor above the meter (8,644 pairs; median and quartiles). Floor: 39 = the lowest value the simulation lets a sensor show; the FDA memo quotes "LO (LESS THAN 40 MG/DL)". "No FDA table holds the exact groups"; sizes come from the nearest group | SIM3:30-37; S3J -> fault_sizes |
| Three faults: episodes, seed, sugar rule | Lengths 2, 6, 12 hours. 200 random starts per participant, fault and length, no repeats, seed 20261120; a start is a reading where the true glucose is inside the fault's range. 45,200 false-low and 45,021 floor-pinned episodes per length; 38,575 hidden-low episodes at 2 hours (66 people had fewer than 200 readings under 54; 1 person had none). Sugar rule: sensor shows under 70: eat 15 g of fast sugar, at most once every 15 minutes while it still shows under 70; "unneeded" = the true glucose was 70 or above | SIM3:42-46,51-52; S3J -> data.episodes |
| Three faults: outcomes and reference rows | Per episode and per affected hour, median and quartiles across people: unneeded sugar treatments and grams; doses withheld or reduced; insulin not given; doses raised while truly under 70; low alerts not shown (under 70, under 54); minutes truly under 54 with the sensor at 70 or above; false low alerts; high episodes never shown; minutes over 180 not shown. Reference rows: a constant bias of -20, -40, -66 % on every reading in the same episode windows; and a no-fault row | SIM3:27,62-75,92; LOOK3 (header) |
| Not modelled | Meals, exercise, insulin action; a changed dose or eaten sugar does not change glucose; no closed loop; how often or how long a real fault lasts; a smooth start or end of a fault | SIM2:150; SIM3:137-140 |

### C4. Sensitivity checks that exist

| Check | Result | Source |
|---|---|---|
| High line 180 vs 200 | Missed highs on real pairs (Set A) 18.1 % vs 20.3 %; high episodes hidden at -20 % bias 51 % vs 59 % | ACC:133; SIM2:143 |
| Arm (Set A) vs all (Set B) vs CGM-only arm (Set C); calibration pairs (Set D) | MARD 13.8 / 13.3 / 13.1 %; missed lows 28 / 31 / 33 %. Set D: MARD 14.1 % (13.7 to 14.4) | ACC:68-71,144 |
| Set A without clipped sensor values; with the run-in; with pump entries back | MARD 13.6 %; 13.7 %; 12.2 % | ACC:76 |
| Meter error at the ISO 15197 limit added to the meter (20 draws, seed 601) | MARD 15.7 % (+1.9); the low-range bias moves toward zero | ACC:160-170 |
| Meter as truth in the simulation (15,034 decisions, 67 people) | Real sensor, no added bias: 1.4 % of corrections withheld, 4.2 % changed by more than 1 U. At -20 %: 12.3 % withheld | SIM2:115-121 |
| Lag shifts 0, 5, 10, 15 min and 7 min interpolated | The low-range bias stays below zero at every shift | ED:26-31 |
| Wear day with all sessions; with raw (unglued) sessions | Same curve (15.2 to 11.9 %); early-removal share 12 % instead of 8 % | ED:93; WD:47 |
| Three-fault size cases (small, main, large), 6 hours | False low: 16.2 / 20.3 / 21.4 unneeded sugar treatments; doses withheld 0.35 in all three. Hidden low: 33.7 minutes in all three | SIM3:99-104 |
| FDA side: lookup join clipped at -40 % vs -90 %; same-sentence pattern pairs only; weighted sample vs full corpus | Abbott 31.3 % vs 49.3 % of decisions withheld; tables differ by at most a few points; all inside the sample's intervals except the Dexcom pair rate | TR:154,160; RX:71,162-172 |

### C5. Software, hardware, run times

| Item | Fact | Source |
|---|---|---|
| Language and packages | Python 3.11 (3.11.9 at the last verified run). Pinned: pandas 2.3.3; numpy 2.3.5; matplotlib 3.10.7; pyarrow 22.0.0; openpyxl 3.1.5; xlrd 2.0.2; scipy 1.16.3; statsmodels 0.14.6; requests 2.32.5; scikit-learn 1.8.0; ollama 0.6.3 (the Python client) | REPRO:7,71; `requirements.txt:7-17` |
| Hardware | Phase 2: "SSD laptop", Windows 11; about 1 GB of memory for the sensor table. Text step: RTX 5080 16 GB, Windows 11. CPU and RAM: NOT FOUND | REPRO:24,57,71; VAL:3 |
| Seeds | 600 (accuracy, subgroups, demographics); 20261027 (error drivers, simulation v2); 20261106 (wear day, brand comparison, patterns v2, field inventory); 20261120 (three faults); 20261019 (MAUDE samples); 42 (model); 2026 (self-check sample) | REPRO:19-24; FM:168,179; SIM3:44; RUN:11; FR:286; GOLD:11 |
| Scripts in `analysis/`: result (figures), run time | `preprocess.py`: cleaned tables, 47 s. `explore_raw_data.py`, `bias_simulation.py`: first pass (01 to 12, superseded), 5 s and 4 s. `accuracy_v2.py`: accuracy, iCGM, misclassification (13 to 16), 5 s. `error_drivers.py`: lag, rate of change, wear day, time of day (17 to 20), 26 s. `subgroups.py`: first-pass trait tests (21 to 24), 8 s. `simulation_v2.py`: bias sweep and fault families (25 to 28), 102 s; extended lookup, 53 s. `demographics_deep.py` (29 to 32), 150 s. `wear_day.py` (33, 34), 4 s. `demographics_followup.py` (35), 24 s. `simulation_three_faults.py` (36, 37), 23 s. `tail_comparison.py`: trial against reported errors (38), about 10 s | REPRO:11-22; TAIL:86 |
| Scripts in `fda-maude/scripts/`: result (figures), run time | `maude_robot.py`: pull and clean, about 2 h by API or 14 + 6 min by bulk files. `report_results.py`: counts report (fig1 to fig6), about 35 s. `country_spread.py` (fig7), about 4 s. `extract_regex.py`: patterns, 95 s. `llm_extract.py`: model run, 9.55 h. `score_against_gold.py`: agreement scores, run time NOT FOUND. `text_results.py` (t1 to t6), about 10 s. `brand_comparison.py` (t7 to t10), about 70 s. `extract_regex_v2.py`, `report_regex_v2.py` (t11 to t13), 8 min + 1 min. `field_inventory.py`, about 7 min | FR:113-114,141,261-263,288,294,304-305; DN:12; VAL:107; TR:18; FM:192 |
| Checks of the numbers | Last verified re-run of the Phase 2 scripts: 2026-10-30, 29,584 values identical to the run before. Team update: 169 numbers traced to sources, 26 corrected. Three-fault simulation: three sanity checks, "No independent number check" | PRE:120; REPRO:72-84; NC; `logs/2026-11-09_1500_team-update-docx.md`; `logs/2026-11-20_1400_push-and-three-fault-simulation.md` |

## D. Results numbers for the five claims

### D1. Claim 1: the error-to-decision curve (constant-bias sweep)

- Values: the median person, with Q1 to Q3 across people; "0" = median and both quartiles are 0. Condition: a constant bias on the whole trace; 159,878 calculator decisions. Source: LOOKX, columns `skipped_pct`, `skipped_of_needed_pct`, `high180_missed_pct`, `low70_false_per_day`, `changed_1_pct`. LOOKX holds every 2 % step from -90 to +90; the table shows 2 % steps to -20, then 10 % steps.
- Figure: `analysis/figures/25_decision_impact_vs_bias.png` (bias -40 to +40 %). With the reported errors marked: `fda-maude/results/text/figures/t6_join.png`.

| Bias % | Withheld, % of decisions | Withheld, % of needed corrections | High episodes (over 180) not displayed, % | False low alerts (under 70) per day | Dose changed by more than 1 U, % of decisions |
|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 | 0 |
| -2 | 0 | 0 | 5.6 (4.6 to 6.7) | 0.10 (0.08 to 0.14) | 0 |
| -4 | 0 | 0 | 11.8 (10.0 to 14.5) | 0.16 (0.12 to 0.20) | 0 |
| -6 | 0 | 0 | 17.6 (14.3 to 21.3) | 0.26 (0.20 to 0.33) | 0 |
| -8 | 0 (0 to 0.26) | 0 (0 to 0.51) | 22.5 (18.5 to 27.0) | 0.36 (0.28 to 0.45) | 0 |
| -10 | 0.15 (0 to 0.89) | 0.34 (0 to 1.6) | 28.4 (23.2 to 33.7) | 0.40 (0.32 to 0.51) | 0 (0 to 1.3) |
| -12 | 0.69 (0.11 to 2.0) | 1.2 (0.31 to 3.5) | 32.6 (26.9 to 38.7) | 0.50 (0.39 to 0.63) | 0.14 (0 to 6.4) |
| -14 | 1.6 (0.54 to 4.1) | 3.0 (1.1 to 7.9) | 36.9 (31.3 to 43.7) | 0.59 (0.46 to 0.74) | 2.1 (0 to 14.8) |
| -16 | 3.0 (1.4 to 6.2) | 5.5 (2.6 to 12.0) | 41.7 (35.5 to 49.0) | 0.69 (0.53 to 0.83) | 5.7 (0.49 to 22.3) |
| -18 | 4.9 (2.5 to 8.2) | 9.1 (4.9 to 16.9) | 45.8 (39.2 to 53.5) | 0.77 (0.62 to 0.93) | 10.1 (1.5 to 31.5) |
| -20 | 7.2 (4.3 to 10.9) | 13.5 (7.8 to 21.3) | 50.8 (43.4 to 58.7) | 0.86 (0.68 to 1.03) | 16.7 (3.5 to 40.3) |
| -30 | 20.0 (15.1 to 25.0) | 37.5 (28.9 to 49.9) | 70.8 (63.5 to 79.6) | 1.31 (1.05 to 1.56) | 36.0 (18.4 to 54.3) |
| -40 | 32.6 (25.9 to 39.0) | 64.2 (51.5 to 75.5) | 88.7 (82.4 to 93.5) | 1.80 (1.53 to 2.04) | 38.7 (22.2 to 55.2) |
| -50 | 44.6 (33.3 to 53.1) | 85.4 (76.6 to 92.4) | 97.5 (95.3 to 98.9) | 2.06 (1.81 to 2.41) | 39.4 (22.5 to 55.2) |
| -60 | 52.3 (38.1 to 62.9) | 97.1 (93.2 to 99.1) | 100 (100 to 100) | 1.96 (1.61 to 2.32) | 39.4 (22.5 to 55.2) |
| -70 | 54.2 (39.7 to 66.9) | 100 (99.5 to 100) | 100 (100 to 100) | 1.16 (0.75 to 1.51) | 39.4 (22.5 to 55.2) |
| -80 | 54.2 (40.2 to 67.2) | 100 (100 to 100) | 100 (100 to 100) | 0.27 (0.14 to 0.46) | 39.4 (22.5 to 55.2) |

- People behind each column (LOOKX `_n` columns): decisions 203; needed corrections 202; high episodes 226; false low alerts 226; dose changed 203.
- Bootstrap CIs exist only at -10, -20 and -30 % (S2J -> bootstrap_ci_headline; SIM2:80-82). Withheld, % of decisions: 0.15 (0.09 to 0.25); 7.2 (6.6 to 8.2); 20.0 (18.8 to 21.1). Changed by more than 1 U: 0; 16.7 (11.1 to 22.9); 36.0 (30.3 to 40.9). False low alerts per day: 0.40 (0.39 to 0.44); 0.86 (0.81 to 0.91); 1.31 (1.26 to 1.37).
- "Skipping starts at about -12 %" (SIM2:85). Withheld reaches 100 % of needed corrections at -70 %. High episodes not displayed is 100 % from -56 % on. False low alerts peak at 2.1 per day near -54 % and then fall, because the shown trace sits under 70 all day (SIM2:166-167).

### D2. Claim 2: accuracy of a working sensor

By glucose range (average of sensor and meter), value (CI). Figure for Set A: `analysis/figures/13_accuracy_by_range_setA.png`. Source: ACCJ -> sets.B and sets.A (overall, by_avg_range); ACC:68-69,84-88.

| Range mg/dL | Set B: pairs (people) | Set B: MARD % | Set B: bias % | Set B: 20/20 % | Set A: pairs (people) | Set A: MARD % | Set A: bias % | Set A: 20/20 % |
|---|---|---|---|---|---|---|---|---|
| All | 168,990 (226) | 13.3 (12.7 to 13.9) | -1.3 (-1.6 to -0.9) | 83.8 (82.7 to 84.9) | 33,467 (77) | 13.8 (12.3 to 15.7) | -1.1 (-2.1 to +0.1) | 84.0 (81.2 to 86.3) |
| Under 54 | 2,156 (197) | 19.6 (18.7 to 20.6) | -5.2 (-6.8 to -3.7) | 91.3 | 597 (59) | 19.1 (18.0 to 20.4) | -4.9 (-7.6 to -2.2) | 92.0 |
| 54 to 69 | 7,866 (222) | 16.9 (16.3 to 17.5) | -2.7 (-3.7 to -1.7) | 85.7 | 1,826 (74) | 16.4 (15.3 to 17.6) | -2.7 (-4.1 to -1.3) | 86.4 |
| 70 to 180 | 99,544 (226) | 14.2 (13.5 to 14.9) | -1.1 (-1.7 to -0.5) | 81.5 | 19,680 (76) | 14.8 (12.9 to 17.4) | -0.5 (-1.9 to +1.3) | 81.3 |
| 181 to 250 | 40,262 (226) | 11.4 (10.8 to 12.2) | -1.2 (-1.6 to -0.8) | 86.6 | 7,747 (76) | 11.6 (10.3 to 13.2) | -1.7 (-2.5 to -0.9) | 87.2 |
| Over 250 | 19,162 (226) | 10.3 (9.8 to 10.9) | -1.1 (-1.4 to -0.7) | 88.5 | 3,617 (77) | 10.2 (9.5 to 11.4) | -1.3 (-2.2 to -0.4) | 89.1 |

- Set B, all pairs: bias -5.0 mg/dL (-5.4 to -4.6); median ARD 9.0 %; 15/15 73.6 %; 40/40 96.5 %; Parkes zones A / B / C / D / E 83.6 / 15.0 / 1.2 / 0.2 / 0.0 %; sensor below the meter in 58.0 % of pairs (ACCJ -> sets.B.overall).
- Set A, all pairs: bias -5.2 mg/dL (-6.1 to -4.3); median ARD 9.1 %; 15/15 73.8 %; 40/40 96.0 %; Parkes 83.7 / 14.6 / 1.4 / 0.3 / 0.0 %; sensor below the meter in 58.1 % (ACCJ -> sets.A.overall).

iCGM table: observed % (lower one-sided 95 % bound). Figure: `analysis/figures/14_icgm_agreement_by_cgm_range.png` (Set A). Source: ACCJ -> sets.A.icgm.rules, sets.B.icgm.rules; ACC:108-114.

| Sensor value | Criterion | Needs | Set A: pairs; observed (bound) | Set B: pairs; observed (bound) | Result |
|---|---|---|---|---|---|
| Under 70 | within 15 mg/dL | above 85 | 2,818; 69.6 (66.1) | 11,724; 68.1 (66.6) | fail |
| Under 70 | within 40 mg/dL | above 98 | 2,818; 92.7 (90.6) | 11,724; 92.5 (91.8) | fail |
| 70 to 180 | within 15 % | above 70 | 19,733; 69.8 (67.3) | 100,016; 69.6 (68.5) | fail |
| 70 to 180 | within 40 % | above 99 | 19,733; 95.6 (93.9) | 100,016; 96.1 (95.5) | fail |
| Over 180 | within 15 % | above 80 | 10,916; 78.4 (76.0) | 57,250; 78.4 (77.3) | fail |
| Over 180 | within 40 % | above 99 | 10,916; 96.2 (94.3) | 57,250; 96.6 (96.0) | fail |
| All | within 20 % | above 87 | 33,467; 81.5 (79.3) | 168,990; 81.7 (80.7) | fail |

- Pairs with sensor under 70 and meter over 180, and the reverse: Set A 34 and 33; Set B 101 and 125 (ACCJ -> icgm.cross_range_pairs).

Misclassification and missed lows. Figure: `analysis/figures/15_misclassification_70_180.png` (Set A). Source: ACCJ -> sets.A.misclassification, sets.B.misclassification; ACC:125-142.

| Rate (70 / 180 rule) | Set A: value (CI); denominator | Set B: value (CI); denominator |
|---|---|---|
| Missed low: meter under 70, sensor 70 or more | 28.2 % (24.4 to 32.8); 689 of 2,440 meter lows | 31.4 % (29.4 to 33.8); 3,177 of 10,104 |
| Unconfirmed low: sensor under 70, meter 70 or more | 37.9 %; 1,067 of 2,818 sensor lows (PPV 62.1 %, 57.8 to 66.5) | 40.9 %; 4,797 of 11,724 (PPV 59.1 %, 56.9 to 61.2) |
| False low, as a share of meter values 70 or more | 3.4 % (2.9 to 4.0); of 31,027 | 3.0 % (2.8 to 3.3); of 158,886 |
| Missed high: meter over 180, sensor not | 18.1 % (15.6 to 20.9); of 11,897 | 17.2 % (16.1 to 18.3); of 61,788 |
| False high | 5.4 % (4.3 to 6.7); of 21,570 | 5.7 % (5.2 to 6.2); of 107,202 |
| Any pair in the wrong category | 15.0 % (13.6 to 16.6); of 33,467 | 14.5 % (13.9 to 15.1); of 168,990 |
| Lows detected at 70; at 54 (sensitivity) | 71.8 % (67.2 to 75.6); 51.8 % (45.7 to 56.7), 307 of 593 | 68.6 % (66.2 to 70.6); 49.9 % (46.5 to 53.4), 1,085 of 2,174 |


Lag. Figures: `analysis/figures/17_lag_scan.png`, `analysis/figures/18_low_range_bias_lag_corrected.png`. Source: ED:9-18,54-62.

- Best shift: 5 min on real readings (98 % of bootstrap draws; 163,174 pairs); 7 min on the interpolated trace (CI 7 to 7; 152,072 pairs). Per person: median 7 min (IQR 5 to 9), range -10 to 17.
- MARD at shifts -5 / 0 / 5 / 10 / 15 / 20 min: 14.5 / 13.2 / 12.2 / 12.3 / 12.9 / 14.1 %.
- Bias under 54, as paired -> lag-corrected: -5.1 % (-6.7 to -3.6) -> -6.5 % (-7.9 to -5.1); 2,133 pairs; -4.1 -> -4.6 mg/dL.
- Bias at 54 to 69: -2.8 % (-3.7 to -1.7) -> -4.1 % (-4.9 to -3.2); 7,816 pairs; -3.3 -> -3.9 mg/dL. All 167,847 pairs: bias -1.3 % -> -1.7 % (-2.1 to -1.3); MARD 13.2 -> 12.2 %.
- CGM+BGM arm after randomisation, lag-corrected: -6.5 % (under 54) and -4.8 % (54 to 69).

Published values the memos compare against (ACC:176-180; ACCJ -> published_mard). Citations as recorded:

| Device and setting | Reference | MARD % | Citation as recorded |
|---|---|---|---|
| Dexcom G4 Platinum, Software 505; adults, clinic sessions | YSI lab / meter | 9.0 (lab), 11.3 (meter) | Bailey 2015, https://pmc.ncbi.nlm.nih.gov/articles/PMC4604574 |
| Dexcom G4 Platinum, original vs Software 505; children 2 to 17, clinic | YSI lab | 17 (original), 10 (505) | Laffel 2016, https://pmc.ncbi.nlm.nih.gov/articles/PMC4717517 |
| Abbott FreeStyle Navigator II; adults at home, 10,597 pairs | built-in meter | 14.2 overall; 30.6 under 70; 13.9 at 70 to 180; 9.8 over 180 | Thabit 2015, https://pmc.ncbi.nlm.nih.gov/articles/PMC4649721 |
| Abbott FreeStyle Libre (first generation); 72 adults, 14 days at home, 13,195 pairs | reader meter / YSI | 11.4 (meter), 12 (lab) | Bailey 2015, https://doi.org/10.1089/dia.2014.0378 |
| Abbott FreeStyle Libre; 742 inpatients with type 2 diabetes, 25,579 pairs | hospital meter | 14 overall; 24.5 at 3 AM | Wen 2022, https://pmc.ncbi.nlm.nih.gov/articles/PMC9639390 |

- Notes on this table from the reference check (REFS section 6): the 11.3 % is a home-use, meter-reference number, not a clinic number (REFS [17]); Wen 2022 gives 75 % in the abstract and 72.3 % in the results text for pairs reading low (REFS [24]); Thabit 2015 gives 10,597 pairs in the abstract and 10,647 in its Table 2 (REFS [25]). Full citations: REFS [17], [18], [21], [24], [25].
- The plan's cited review (22 studies, 2,294 people, average MARD 9.4 %; PLAN:107) is Dávila-Ruales et al., Ther. Adv. Endocrinol. Metab., vol. 15, Dec. 2024, doi:10.1177/20420188241304459 (abstract only was read) (REFS [27]).

### D3. Claim 3: reported failures (FDA report texts)

Serious wrong-reading pairs by maker (patterns + model), and malfunction-only pairs (patterns only). Figures: `fda-maude/results/text/figures/t7_brand_error_sizes.png`, `t8_brand_meter_bands.png`, `t12_malfunction_vs_serious_errors.png`. Sources: BRAND CSV (rows tier = serious); MALF CSV (row All / malfunction); BC:54-67,97-107.

| Measure | Abbott | Dexcom | Medtronic (caution) | Senseonics | Malfunction-only, all makers |
|---|---|---|---|---|---|
| Pairs | 7,470 | 9,189 | 379 | 532 | 191,112 |
| Median error, % of meter (IQR) | -47 (-80 to +146) | +44 (-64 to +172) | 0 (-63 to +166) | -19 (-53 to +117) | -66 (-74 to +22) |
| Median absolute error, % | 85.5 | 86.7 | 83.3 | 65.5 | 72.4 |
| Sensor read lower than the meter, % of pairs | 57.8 | 43.8 | 48.8 | 54.1 | 74.7 |
| Reads-low pairs: number; median error % (IQR) | 4,315; -77 (-86 to -60) | 4,029; -69 (-85 to -48) | 185; -64 (-80 to -44) | 288; -51 (-66 to -37) | 142,817 (TAIL:49); -69.4 |
| Reads-low pairs: median sensor / meter, mg/dL | 60 / 318 | 86 / 420 | 91 / 400 | 78 / 208 | all pairs: 63 / 178 |
| Reads-high pairs: number; median error % | 3,126; +191 | 5,088; +152 | 186; +170 | 241; +126 | +135 |
| False low: sensor under 70, meter 70 or more, % | 35.6 | 17.3 | 16.4 | 23.9 | 57.6 |
| Meter under 70, % | 28.1 | 45.7 | 42.5 | 39.8 | 4.7 |
| Hidden low: meter under 70, sensor 70 or more, % | 26.1 | 39.1 | 38.8 | 35.7 | 4.5 |
| Meter over 250, % | 37.0 | 33.8 | 35.9 | 20.5 | 18.3 |
| Absolute error over 20 %: all pairs; reads-low pairs | 97.7; 98.3 | 97.0; 97.2 | 94.5; 95.1 | 92.3; 91.3 | 99.6; 99.6 (derived from bins, NC row 85) |
| Absolute error over 40 %, all pairs | 92.2 | 87.3 | 84.4 | 79.3 | 95.8 |

- Abbott minus Dexcom, with CIs (BC:73-83,104-106): absolute error -1.1 points (-2.2 to -0.2), no difference in size; share reading low +13.8 points (12.4 to 15.3); meter under 70: -17.6 (-19.0 to -16.2); false low +18.3 (16.9 to 19.5); hidden low -13.0 (-14.4 to -11.6).
- Malfunction-only pairs by maker (RX:101-116): Abbott 162,072 pairs, median -67 %, 74 % read low, false low 59 %. Dexcom 25,273 pairs, median -52 %, 80 % read low, false low 54 %. 85 % of malfunction pairs are Abbott template reports; 81 % are from 2025-2026 (RX:8).
- Death or injury pairs found by patterns (18,237; MALF CSV row All / serious): median error -7 %; absolute 84.8 %; 50.4 % read low; meter under 54 in 31.1 % and over 250 in 34.9 %; false low 24.3 %; hidden low 32.9 %.
- Model-only pair set (TR:69-87; slightly different pairs): Abbott 7,556 pairs, Dexcom 9,518; reads-low median -77 % (Abbott) and -68 % (Dexcom); 96 to 97 % of all serious pairs are more than 20 % off.
- Reported reads-low errors put into the bias lookup, median trial person (TR:154-155): Abbott 49.3 % of decisions withheld, 96.4 % of high episodes missed, under 70 shown 79.5 % of the day (true 3.5 %). Dexcom 45.2 %, 92.7 %, 69.0 %.
- Outcomes, all 118,462 serious reports, model field (TR:124,136-141): "hospital or ER" 53.8 % (read as "sought medical care"); symptoms only 20.5 %; hypoglycaemia 14.0 %; none 10.7 %; death 0.5 %. Reads-low reports (18,933): ate carbs 27.7 %; took insulin 13.1 %; skipped insulin 0.2 %; sought care 48.3 %.
- Outcomes, FDA codes, all 123,607 serious reports (RR:72,88-105): 623 deaths, 122,984 injuries. Required Intervention 52.5 %; Other 35.0 %; Hospitalization 13.9 %; Life Threatening 1.2 %. Top patient problems: hypoglycaemia 40.8 %, loss of consciousness 27.8 %, hyperglycaemia 19.0 %. Top device problem family: wrong readings 33.1 %.
- Deaths in the wrong-reading set: Abbott 0.2 % (56 reports), Dexcom 0.1 % (21) (BC:135). Pairs in death reports: 25; median error -86 % (IQR -91 to -63); 84 % read low (TR:74).
- Wear day in reports (TR:112-114; figure `fda-maude/results/text/figures/t5_wear_day.png`): Abbott serious, 6,627 reports state a day (8.9 %): day 1 in 13.4 % (flat expectation 7.1 % for a 14-day sensor). Abbott malfunction sample: 34.5 %. Dexcom serious, 1,140 reports (3.6 %): day 1 in 7.1 % (flat 10 %). In the wrong-reading set: Abbott 15.8 % of 2,197; Dexcom 7.9 % of 378 (BC:110-111).
- Children (BC:254,275-279,290-295; figure `fda-maude/results/text/figures/t10_demographics.png`): age is filled in 49.1 % of the 39,667 serious wrong-reading reports. Under 18 = 11.7 % of the 19,462 with an age (Abbott 9.3 %, Dexcom 13.2 %). Under 18 vs 65 and over: read low 54.6 % vs 42.6 % (+11.9 points, CI 8.8 to 15.1); hypoglycaemia outcome 19.6 % vs 11.4 % (+8.3, CI 6.5 to 10.0); took insulin 13.1 % vs 5.6 %. One child death. All CGM reports with a known age: 17.5 % under 18 (RR:177). The trial has no children.
- Libre 3 / 3 Plus (RR:111-124,164): 18,292 serious reports all time; 6,785 received on or after 2025-11-24 (71 deaths, 6,714 injuries); 2,638 of those coded "Low Readings". Recall of 2025-11-24: 2,990,939 units.

Trial errors and reported errors on one axis. Source: TAIL (line numbers below); `analysis/tail_comparison_stats.json`. Figure: `analysis/figures/38_trial_vs_reported_error.png`. CIs: 2,000 participant resamples, seed 600. Report values have no CI.

- Trial pairs (Set B, 168,990) with an error at or beyond a size: -20 % or lower 10.8 % (10.2 to 11.4); -40 % or lower 1.69 % (1.48 to 1.95); -66 % or lower 0.16 % (0.12 to 0.22); -69 % or lower 0.11 % (0.073 to 0.15); -77 % or lower 0.033 % (0.018 to 0.052); +20 % or higher 7.72 % (7.14 to 8.34); +100 % or higher 0.61 % (0.47 to 0.79). Set A, the five low sizes: 10.9, 2.00, 0.22, 0.13, 0.039 % (TAIL:30-39).
- The same sizes in reports, share of pairs (Abbott death or injury / Dexcom death or injury / malfunction-only): -20 % or lower 56.8 / 42.6 / 74.4 %; -69 % or lower 36.2 / 22.0 / 38.4 % (TAIL:30,35).
- Where the median reported reads-low error sits in the trial: Abbott -76.8 % = 1 trial check in 2,965 (57 pairs; 30 of 226 people had at least one). Dexcom -69.2 % = 1 in 966 (175 pairs; 66 people). Malfunction-only -69.4 % = 1 in 982 (172 pairs; 65 people). Malfunction-only pairs that read low: 142,817; that read high: 48,295 (TAIL:45-50).
- In the 26 trial weeks only (137,662 pairs, 225 people, median 607 checks each): 57 people (25 %) had at least one error of -69 % or lower; 25 people (11 %) had one of -77 % or lower (TAIL:17,35-36).
- The range that holds 95 % of trial pairs is -35.3 % to +40.4 %. Report pairs inside it: Abbott 6.63 % (6.17 to 7.38), Dexcom 11.4 % (10.3 to 12.8), malfunction-only 3.25 % (2.85 to 3.75) (TAIL:57-59,76).
- The same fault rule on both sides, as a share of the pairs where it can happen (trial; then Abbott / Dexcom / malfunction-only) (TAIL:64-68). False low (sensor under 70, meter 70 or above): 3.02 % (2.75 to 3.29); 49.5 / 31.9 / 60.4 %. Hidden low (sensor 70 or above, meter under 70): 31.4 % (29.3 to 33.7); 92.7 / 85.5 / 97.0 %. Hidden low with the meter under 54: 18.2 % (15.5 to 20.9), 395 of 2,174; 92.5 / 84.5 / 96.5 %. Floor reading (sensor 40 or below, meter over 250): 2 of 20,655 (0.010 %); 7.56 / 7.31 / 7.99 %.

### D4. Claim 4: three-fault simulation

- Values: median (Q1 to Q3) across participants, per episode, main size. "0" = median and both quartiles are 0. Source: LOOK3 (size_case `main`); memo tables SIM3:62-90 show 6 hours only. Figures: `analysis/figures/36_three_faults_outcomes.png`, `analysis/figures/37_three_faults_by_episode_length.png`.

| Outcome, per episode | False low, 2 h | False low, 6 h | False low, 12 h | Hidden low, 2 h | Hidden low, 6 h | Hidden low, 12 h | Floor-pinned, 2 h | Floor-pinned, 6 h | Floor-pinned, 12 h |
|---|---|---|---|---|---|---|---|---|---|
| Hours of readings the fault changed | 1.84 (1.80 to 1.88) | 5.26 (5.05 to 5.42) | 10.3 (9.77 to 10.7) | 0.48 (0.36 to 0.62) | 0.56 (0.39 to 0.75) | 0.64 (0.43 to 0.85) | 1.23 (1.12 to 1.34) | 1.92 (1.63 to 2.32) | 2.48 (1.96 to 3.18) |
| Dose decisions inside the episode | 0.30 (0.20 to 0.38) | 0.91 (0.65 to 1.11) | 1.87 (1.31 to 2.21) | 0.18 (0.08 to 0.31) | 0.79 (0.51 to 1.04) | 1.68 (1.09 to 2.14) | 0.43 (0.31 to 0.56) | 1.04 (0.79 to 1.30) | 1.96 (1.49 to 2.43) |
| Unneeded sugar treatments (15 g each) | 7.14 (6.96 to 7.36) | 20.3 (19.4 to 21.2) | 39.4 (37.2 to 41.5) | 0 | 0 | 0 | 5.25 (4.78 to 5.64) | 8.18 (6.99 to 9.79) | 10.5 (8.35 to 13.5) |
| Correction doses withheld | 0.12 (0.07 to 0.17) | 0.35 (0.20 to 0.47) | 0.69 (0.40 to 0.91) | 0 | 0 | 0 | 0.27 (0.19 to 0.34) | 0.44 (0.31 to 0.56) | 0.56 (0.40 to 0.74) |
| Insulin not given, units | 0.17 (0.10 to 0.28) | 0.52 (0.28 to 0.84) | 1.02 (0.55 to 1.66) | 0 | 0 | 0 | 0.75 (0.45 to 1.09) | 1.29 (0.74 to 1.82) | 1.63 (0.97 to 2.52) |
| Doses raised while true glucose under 70 | 0 | 0 | 0 | 0 (0 to 0.005) | 0 (0 to 0.005) | 0 (0 to 0.005) | 0 | 0 | 0 |
| Low alerts under 70 not shown | 0 | 0 | 0 | 0.08 (0.05 to 0.12) | 0.10 (0.07 to 0.15) | 0.13 (0.08 to 0.19) | 0 | 0 | 0 |
| Low alerts under 54 not shown | 0 | 0 | 0 | 0.41 (0.35 to 0.47) | 0.48 (0.42 to 0.56) | 0.57 (0.49 to 0.68) | 0 | 0 | 0 |
| Minutes truly under 54 while the sensor shows 70 or above | 0 | 0 | 0 | 28.7 (21.3 to 37.2) | 33.7 (23.1 to 45.1) | 38.6 (25.5 to 51.3) | 0 | 0 | 0 |
| False low alerts under 70 | 0.90 (0.85 to 0.94) | 1.02 (0.93 to 1.14) | 1.29 (1.11 to 1.53) | 0 | 0 | 0 | 0.95 (0.92 to 0.98) | 1.12 (1.03 to 1.18) | 1.38 (1.22 to 1.53) |
| False low alerts under 54 | 0.87 (0.82 to 0.94) | 1.38 (1.31 to 1.47) | 2.17 (2.02 to 2.29) | 0 | 0 | 0 | 0.95 (0.92 to 0.98) | 1.12 (1.04 to 1.18) | 1.38 (1.22 to 1.53) |
| High episodes (over 180) never shown as high | 0.07 (0.06 to 0.09) | 0.33 (0.28 to 0.38) | 0.73 (0.61 to 0.82) | 0 | 0 | 0 | 0 (0 to 0.005) | 0 (0 to 0.01) | 0.005 (0 to 0.01) |
| Minutes truly over 180 not shown as high | 29.0 (23.5 to 35.2) | 83.4 (67.4 to 96.9) | 166 (138 to 189) | 0 | 0 | 0 | 73.6 (67.2 to 80.1) | 115 (98.0 to 139) | 149 (118 to 191) |

- Main sizes: False low -69.4 %; Hidden low +163.6 %; Floor-pinned shows 39 mg/dL. People per row (LOOK3 `participants`, `participants_with_decisions`): False low 226 people (203 with dose decisions); Hidden low 225 people (202 with dose decisions); Floor-pinned 226 people (203 with dose decisions).
- Doses reduced by more than 0.5 U equal doses withheld in every row above: yes (LOOK3 `dose_lower_n` vs `dose_withheld_n`). Unneeded sugar in grams = 15 x treatments in every row: yes (LOOK3 `sugar_unneeded_g`).

Reference rows: a constant bias on every reading in the same episode windows (medians; quartiles in LOOK3, size_case `bias_-20`, `bias_-40`, `bias_-66`).

| Outcome, median per episode: bias -20 / -40 / -66 % | False low windows, 2 h | False low windows, 6 h | False low windows, 12 h | Hidden low windows, 2 h | Hidden low windows, 6 h | Hidden low windows, 12 h | Floor-pinned windows, 2 h | Floor-pinned windows, 6 h | Floor-pinned windows, 12 h |
|---|---|---|---|---|---|---|---|---|---|
| Unneeded sugar treatments | 0.62 / 2.09 / 6.50 | 1.83 / 5.99 / 18.5 | 3.38 / 11.2 / 36.0 | 1.05 / 2.31 / 4.05 | 2.31 / 6.03 / 15.0 | 4.08 / 11.4 / 32.0 | 0.03 / 0.10 / 1.23 | 0.79 / 2.58 / 10.7 | 2.34 / 7.79 / 27.5 |
| Correction doses withheld | 0.02 / 0.10 / 0.14 | 0.06 / 0.29 / 0.43 | 0.12 / 0.58 / 0.89 | 0 / 0.02 / 0.04 | 0.03 / 0.20 / 0.35 | 0.08 / 0.48 / 0.81 | 0.04 / 0.12 / 0.31 | 0.07 / 0.30 / 0.68 | 0.12 / 0.58 / 1.14 |
| Insulin not given, units | 0.13 / 0.20 / 0.22 | 0.43 / 0.70 / 0.80 | 0.91 / 1.43 / 1.66 | 0.04 / 0.06 / 0.07 | 0.34 / 0.56 / 0.65 | 0.80 / 1.25 / 1.45 | 0.39 / 0.68 / 0.87 | 0.80 / 1.42 / 1.75 | 1.30 / 2.19 / 2.65 |
| False low alerts under 70 | 0.10 / 0.34 / 0.86 | 0.26 / 0.65 / 1.06 | 0.46 / 1.11 / 1.41 | 0.04 / 0.04 / 0.02 | 0.17 / 0.28 / 0.29 | 0.38 / 0.74 / 0.73 | 0.005 / 0.03 / 0.30 | 0.12 / 0.31 / 0.78 | 0.33 / 0.73 / 1.16 |
| Minutes over 180 not shown as high | 23.0 / 33.2 / 33.9 | 63.3 / 99.7 / 106 | 124 / 203 / 213 | 5.12 / 7.30 / 7.72 | 41.8 / 76.5 / 86.4 | 101 / 182 / 202 | 15.9 / 81.0 / 108 | 62.3 / 178 / 227 | 124 / 287 / 345 |

- Under every constant bias, in every window and length, "low alerts under 54 not shown" and "minutes under 54 while the sensor shows 70 or above" are 0. No-fault rows (size_case `no_fault`): every outcome is 0 (LOOK3; SIM3:89-92).

### D5. Claim 5: what predicts error

| Factor | Numbers | Denominator and condition | Source; figure |
|---|---|---|---|
| Wear day | MARD day 1: 15.2 % (14.6 to 15.9); day 2: 13.2 %; day 7: 11.8 % (11.2 to 12.5). 86 % of people worse on day 1; per-person day 1 minus days 2 to 7: +2.2 points (IQR 0.9 to 3.4). Mixed model: day 1 +2.3 points (2.1 to 2.6), day 7 -0.9 (-1.2 to -0.6) | 150,690 pairs in confirmed sessions; 29,508 on day 1, 13,143 on day 7 | ED:84-90,116; `analysis/figures/20_wear_day_and_time_of_day.png` |
| Day 1: settling vs early removal | Day-1 excess over day 7: 3.27 points (2.83 to 3.72). Settling 3.02 = 92 % (85 to 100 %). Early removal 0.25 = 8 % (0.5 to 15 %). Same sensors: 15.1 % day 1, 13.1 % day 2, 12.0 % days 5 to 7. The extra error halves about every 24 h (time constant 34 h, CI 25 to 48). Sensors removed on day 1: 19.4 % vs 15.1 % (+4.3, CI 2.2 to 6.6); 7 % of sessions, 3.5 % of day-1 pairs | 163,198 pairs in 8,521 rebuilt sessions; 5,647 reached day 7 | WD:11-14,53-57,68-73; `analysis/figures/33_wear_day_selection_vs_settling.png` |
| Day 1, low range | Bias under 70 on day 1: -10.4 % (-12.1 to -8.6); days 2 to 6: -1.1 %; day 7: 0.0 %. False lows 4.5 % on day 1 vs 2.3 % on day 7 (+2.2 points, CI 1.6 to 2.7). Missed lows 28.5 % vs 31.1 % (no difference). Errors over 20 %: 23.5 % of pairs on day 1 vs 15.3 % on day 7 | sessions that reached day 7; 1,413 low pairs on day 1 | WD:178-199,204 |
| Glucose range | Mixed model, points of percent error added vs 70 to 180: under 54 +5.8 (4.9 to 6.6); 54 to 69 +3.0 (2.5 to 3.4); 181 to 250 -3.2; over 250 -4.6. Per person: low-range MARD 17.6 % (IQR 15.5 to 19.4) vs 12.3 % overall | 143,051 pairs; 150 people with 20 or more low pairs | ED:110-113; SUB:47,52 |
| Rate of change | Bias as paired -> lag-corrected: falling fast +12.7 % (11.6 to 13.9) -> +0.7 % (-0.2 to 1.7); rising fast -9.4 % (-10.5 to -8.2) -> +0.4 % (-0.6 to 1.6); stable -1.8 % -> -2.3 %. MARD in the fast bins 18.3 and 17.9 % -> 12.5 and 12.9 % | 159,633 pairs; 6,974 falling fast, 9,200 rising fast | ED:70-74; `analysis/figures/19_error_by_rate_of_change.png` |
| Time of day | Pooled MARD night 14.3 % (13.2 to 15.6) vs day 13.2 % (12.6 to 13.7). Per person: night minus day -0.2 points (IQR -2.1 to 2.3); 47 % worse at night. Errors over 40 % about twice as common at night. Mixed model: night +0.9 (0.6 to 1.3) | 14,430 night pairs, 154,560 day pairs | ED:97-100,117; figure 20 |
| Participant traits, first pass | 6 pre-specified traits: none passes BH (smallest corrected p 0.15, age); the six-term model explains 2 % of the spread. Sex: 0.0 points (-0.8 to +0.8). Arm: -0.1 (-0.9 to +0.7). 22 exploratory tests: 1 passed (more listed conditions, lower MARD), gone after adjusting for age and glucose swings | 226 people; per-person MARD median 12.3 % (IQR 10.7 to 14.3) | SUB:72-85,144-150; `analysis/figures/22_prespecified_forest.png` |
| Participant traits, deep check | 680 tests: 69 with raw p under 0.05 (34 expected by chance); 1 survived BH: sex vs low-range bias (corrected p 0.016). Every 2x2 group median sits between 11.3 and 13.0 % MARD. Models (forest, boosting, ridge): R-squared below 0 for traits | 226 people; 67 traits (61 testable), 7 error measures | DD:8-12; `analysis/demographics_deep_stats.json` -> bh_summary; `analysis/figures/30_demographic_interactions.png`, `32_demographics_vs_glucose_pattern.png` |
| Glucose pattern | Glucose swings (CV) and time under 70 each correlate with MARD: rho 0.33 (0.20 to 0.44). Pattern alone predicts R-squared 0.03 for MARD and 0.14 for the missed-low rate | 226 people | SUB:105-106; DD:12; `analysis/figures/23_strongest_association.png` |
| Site | 14 sites, 8 to 27 people each; site medians 10.4 to 14.9 % MARD. Share of the spread between sites (ICC) 0.035 (0.02 to 0.21), permutation p 0.10; 0.013 once glucose pattern is in the model | 226 people | DD:223-227,374; `analysis/figures/31_site_effects.png` |
| Sex gap, low range | Bias under 70: women -6.4 %, men -2.2 %; men minus women +4.2 points (CI +2.0 to +6.3); about 2.5 mg/dL at 60 mg/dL. Low-range MARD 17.5 vs 17.6 %. After matching on glucose level and trend +3.7 (+1.9 to +5.6); after adjusting for body size, HbA1c, age, insulin dose +4.0 (+0.9 to +7.0). CGM-only arm, randomised: +6.1 (+3.3 to +8.8). CGM+BGM arm, randomised: +0.6 (-2.5 to +3.5). Blinded run-in, pooled: +5.8 (+2.0 to +9.9). Near 70: false lows 36.0 % vs 31.1 %; missed lows 36.5 % vs 41.8 %. Lookup: no dose change; +0.17 false low alerts per day | 76 women, 74 men with 20 or more low pairs (5,198 and 4,824 pairs); check arm: 24 women, 12 men | DF:10-15,42,58-59,187-198,213; `analysis/figures/35_sex_low_range_bias.png` |
| Shanghai | MARD 13.9 % (12.2 to 16.1); bias -7.4 % (-10.7 to -4.5); 20/20 76.8 %; 68 % of pairs below the meter. Type 1: 18.4 % (10 patients, 750 pairs); type 2: 12.9 % (88 patients). Per patient: type 2 minus type 1 -3.9 points (-8.9 to +1.9), p 0.25. 60 trait tests: nothing (smallest corrected p 0.97) | 4,012 pairs, 98 patients; 76 patients for per-patient tests | ACC:188-193; SUB:163; DD:304 |

### D6. Places where two sources disagree

| Fact | Source 1 | Source 2 | Machine-readable one |
|---|---|---|---|
| Which pair set is "the headline" | Set A (ACC:17,27; written 2026-10-27) | Set B (METH:86,104; OV:136; PRE:44; FIND:10; decided 2026-10-30) | Neither; ACCJ holds both sets |
| Recall records and events | 95 records, 32 events (PULL:16; FR:22; RR s g) | 96 records, 33 events (DN:50,149) | `fda-maude/results/recalls_cgm.csv`: 96 rows, 33 event ids |
| CI of the sex gap (+4.2 points) | +2.0 to +6.0 (DD:9); +1.9 to +6.2 (DD:340) | +2.0 to +6.3 (DF:10,42; FIND:96) | Both: `analysis/demographics_deep_stats.json` 2.02 to 6.02; `analysis/demographics_followup_stats.json` -> A_splits.anchor_low 2.05 to 6.27 |
| Set A pairs in Parkes zones C to E | 570 (ACC:75) | 563 | ACCJ -> sets.A.overall.parkes_CDE_pairs |
| Dexcom reads-low median error | -68 % (TR:85, 4,160 pairs; OV:80) | -69 % (BC:65, 4,029 pairs); -67 % (RX:105, pattern pairs) | BRAND CSV: -69.18. Different pair sets |
| Medtronic false low and hidden low | 14.5 % and 40.1 % (BC:105-106) | 16.4 % and 38.8 % | BRAND CSV; `fda-maude/results/text/tables/g_key_tables.md:267` |
| Serious false low and hidden low shares | Dexcom 17.3 % and 39.1 %; Abbott 35.6 % and 26.1 % (model pairs) | Dexcom 16.1 % and 37.6 %; Abbott 35.6 % and 25.9 % (pattern pairs; SIM3:32-33) | Both: BRAND CSV and MALF CSV. Different pair sets |
| Meaning of "hidden low" | Meter under 70 (BC:20; OV:88: Dexcom 46 %, Abbott 28 %) | Meter under 70 and sensor 70 or more (RX:115; NC row 13: 39 %, 26 %) | BRAND CSV has both (`pct_meter_under_70`, `pct_missed_low_70`) |
| Wear day 1 and day 7 MARD | 15.2 % and 11.8 % (ED:87; confirmed raw sessions) | 15.3 % and 12.0 % (WD:68-70; rebuilt sessions) | Both (`analysis/error_drivers_stats.json`, `analysis/wear_day_stats.json`). Different methods |
| MARD under 54 in summaries | 19.1 % (Set A; README:53; FIND:266) | 19.6 % (Set B; NC row 16) | ACCJ. The summaries mix Set A and Set B rows |
| MARD of the "true" trace, in the simulation limits | "about 11 %" (SIM2:147) | 13.3 % on verified pairs (ACC:44) | ACCJ |
| Report counts | Injury reports 123,049 (PULL:32,45; counts double-coded reports twice). Malfunction reports the sample stands for: 2.92 million (TR:6; FI) | Injury reports 122,984 (RR:88; DN:77). 2.94 million (FM:135; RX:21); frame 2,936,278 (RUN:24) | Injuries: the clean tables (not in git). Sample weight total: NOT FOUND in a results file |
| Shanghai days per patient | "about 2 weeks" (OV:34; README:77) | 3 to 14 days (DD:85); median 12.7, range 2.6 to 13.9 per file (RES s5) | `analysis/summary_stats.json` |
| CGM-only arm size | 149 people (SUB:77; ACCJ -> sets.B.definition_counts) | 148 people in Set C (ACC:29) | ACCJ |
| Lines that are out of date | "the full run is in progress" (FR:8); "100-report human check is still pending" (TR:187; BC:338); README:170. "requirements.txt pins 3.0.6" (PRE:134); statsmodels and scipy "not listed yet" (REPRO:37) | Run done 2026-10-30; check done 2026-11-08 (OV:45; VAL:92). pandas 2.3.3, scipy and statsmodels are pinned | `requirements.txt:7,13-14` |
| Were report texts cut before the model read them? | "no report was cut" (context window 6,144 tokens; longest prompt 5,889; TR:20) | "text cut at 6,000 characters" (FM:141); the longest event text is 21,030 characters (DN:117). How many reports were cut: NOT FOUND | `fda-maude/scripts/llm_extract.py:67` (`MAX_TEXT_CHARS = 6000`) |
| False low and hidden low shares in reports: the denominator | Share of all pairs. False low: Abbott 35.6 %, Dexcom 17.3 %, malfunction-only 57.6 %. Hidden low: 26.1 %, 39.1 %, 4.5 % (BRAND CSV; MALF CSV) | Share of the pairs where it can happen. False low: 49.5 %, 31.9 %, 60.4 %. Hidden low: 92.7 %, 85.5 %, 97.0 % (TAIL:64,66) | Both: the CSV tables and `analysis/tail_comparison_stats.json` -> fault_shares |
| CI of the Set B missed-low rate (31.4 %) | 29.4 to 33.8 (ACC s7; 1,000 resamples) | 29.3 to 33.7 (TAIL:66; 2,000 resamples) | Both: ACCJ and `analysis/tail_comparison_stats.json` |
| Published values in ACC s10 | Bailey 2015 G4: setting "adults, clinic sessions", 11.3 % against the meter (ACC:176); Wen 2022: 72 % of pairs read low; Thabit 2015: 10,597 pairs | 11.3 % is a home-use number; Wen gives 75 % (abstract) and 72.3 % (results); Thabit gives 10,597 (abstract) and 10,647 (Table 2) (REFS section 6) | ACCJ -> published_mard holds the memo's wording |
| Device facts written as guesses | G4 software "guess: Software 505" (PRE:108; ACC:182); Shanghai sensor "not confirmed from the paper" (PRE:133) | The trial paper says Software 505 (REFS [7]); the dataset paper names the FreeStyle Libre H (REFS [11]) | - |
| Jaeb sharing terms | "No redistribution" (README:76,80) | The words "no redistribution" are not on the dataset page (REFS [8]); "Data-use terms were not checked" (`logs/2026-11-20_1400_push-and-three-fault-simulation.md`) | - |
| Year of the Class I recall | "2025 FDA Class I recall" (`CLAUDE.md` section 2) | Action started 2025-11-24; classified Class I on 2026-01-13; public notice updated 2026-02-04 (`fda-maude/results/RECALL_DATE_CHECK.md`) | `fda-maude/results/recalls_cgm.csv` (columns `date_initiated`, `date_classified`) |

## E. Every analysis the team ran

| # | Analysis | Question | Method | Result | Memo |
|---|---|---|---|---|---|
| 1 | FDA access check | Which FDA data route works? | Live tests of the API, bulk files, website, recall endpoints | The API works; 13 CGM codes; 3.4 million reports need a free key | `fda-maude/access-check/` |
| 2 | MAUDE pull and counts | How many reports, for which problem, maker and year? | openFDA pull for 13 codes; counts by FDA code fields | 3,382,071 reports; wrong readings top family in serious reports, 33.1 % | RR; PULL |
| 3 | Libre 3 recall timeline | Did reports rise around the recalls? | Monthly serious reports by date received and date of event | 6,785 serious reports since 2025-11-24; 2,638 coded "Low Readings" | RR s f |
| 4 | Recalls | How many CGM recalls, of what class? | openFDA recall and enforcement records grouped by event | 32 events, 7 Class I | RR s g |
| 5 | MAUDE demographics (codes) | Who is in the reports? | Fill rates and medians of the FDA age and sex fields | Age filled 73.4 %, median 52; sex missing 53.4 % | RR s h |
| 6 | Keyword signals (superseded by the text step) | Do texts mention low readings? | Word patterns in serious event texts | Low-reading words in 12.1 % of serious reports | RR s i |
| 7 | Country spread | Where do reports come from? | One API count per country code; two code lists merged | US 63.8 % of all reports, 44.3 % of death or injury | CS |
| 8 | Bulk re-pull check | Do bulk files give the same data? | Per-code totals and report tables compared with the API pull | Same 3,382,071 reports; 24 of 33 tables byte-identical | DN s10 |
| 9 | Text options study | How to read the report texts? | Six methods compared on cost, clarity and repeatability | Chosen: codes, then patterns, then a local model with a fixed form | `fda-maude/OPTIONS.md`; FM |
| 10 | Pilot | Is the pipeline fast and safe enough? | Patterns and model on 287 and 500 reports; speed runs | About 300 reports per minute; 2 to 6 % of answers held an unsupported number | PILOT |
| 11 | Reference set | What is the yardstick? | One AI reviewer labelled 287 reports with a rubric | Self-check 100 % on 40; teammate checked 100, no issues | GOLD; VAL:92 |
| 12 | Validation, prompts v1 to v3 | Does the system agree with the reference set? | Kappa per field and maker; three prompt versions | v3: fault type 0.77, outcome 0.75, numbers 96.2 % exact | VAL |
| 13 | Repeat-run check | Is the model output repeatable? | Two identical v3 runs compared field by field | 90.6 % of forms identical | VAL s6 |
| 14 | Full text run: coverage and fault mix | What do 124,599 texts say? | Patterns plus model; word-for-word number rule | Both values in 15.6 % of serious reports; reads low 16.0 % | TR s1-3 |
| 15 | Reported error sizes | How big are the reported errors? | Sensor minus meter from stated pairs; median and IQR | Reads-low median -77 % (Abbott), -68 % (Dexcom) | TR s4 |
| 16 | Stated vs computed Parkes zone | Do makers' zones match the numbers? | Parkes grid computed from each stated pair | Exact match 87.1 %; within one zone 96.8 % | TR s5 |
| 17 | Wear day in complaints | When in the wear do complaints fall? | Share of stated wear days against a flat expectation | Abbott day 1: 13.4 % vs 7.1 % flat; Dexcom 7.1 % vs 10 % | TR s6 |
| 18 | Actions and outcomes | What did people do; what happened? | Model fields; cross-table with FDA outcome codes | Ate carbs in 27.7 % of reads-low reports; "hospital or ER" 53.8 % | TR s7 |
| 19 | Join to the bias lookup, clipped at -40 % (superseded) | What would reported errors do to decisions? | Lookup rows weighted by reported error sizes | Abbott 31.3 % of decisions withheld (a floor) | TR s8 |
| 20 | Join to the extended lookup | Same, without the clip | Lookup extended to -90 %; same weighting | Abbott 49.3 % of decisions withheld; 96.4 % of highs missed | TR s8 |
| 21 | Brand comparison | Do brands fail differently? | Rank tests, effect sizes, bootstrap CIs on 17,573 pairs | Same size (86 vs 87 %); false low 36 % (Abbott) vs 17 %; meter under 70 in 46 % (Dexcom) vs 28 % | BC s3-5 |
| 22 | Brand by year and recall window | Is the direction gap stable? | Shares per year and per recall window | 14 points overall; 2 points in 2026 (64 vs 62 %) | BC s6 |
| 23 | Brand confound checks | Is it the template, the sample or the year? | Template vs prose; serious vs sample; by year | The template does not change the numbers (delta 0.00) | BC s7 |
| 24 | MAUDE age and sex cuts | Do age or sex change the complaints? | The same tests by age group and sex | Under 18: 11.7 %; children read low 54.6 % vs 42.6 %; sex negligible | BC s8 |
| 25 | Pattern tuning (version 2) | Can patterns alone find the pairs? | New patterns tuned against model output; eye checks | Recall 73.1 -> 89.1 % of the model's pairs | RX s2-4 |
| 26 | Patterns over all reports | What errors sit in malfunction-only reports? | Version 2 patterns over 3,382,071 reports | 191,112 pairs: median -66 %, 75 % read low | RX s5-6 |
| 27 | Harm gradient (unclear) | Does harm coding follow error size? | Share of pairs coded death or injury per error band | U-shaped; partly real, partly coding; not settled | RX s7 |
| 28 | Weighted sample check | Does the sample match the full corpus? | Bootstrap intervals of the sample against full counts | All inside except the Dexcom pair rate (0.57 vs 1.05 %) | RX s8 |
| 29 | Field inventory | What else do the reports hold? | Fill rates; 300 texts read; 52 theme patterns | "No defect found" in 81 % of returned devices; a model run on malfunction texts is not worth it | FI |
| 30 | First data check (superseded) | What is in the data; first accuracy? | All meter pairs, calibration and pump entries included | 475,502 pairs; MARD 10.4 % | RES |
| 31 | Bias simulation, version 1 (superseded) | How many readings flip under a low bias? | Constant bias on every reading; lines at 70 and 200 | At -20 %: 17.2 false low and 39.8 missed high readings per day | SIM1; SIM2 s8 |
| 32 | Methods review | Which methods do CGM accuracy papers use? | Literature check against the plan | Priority list adopted (CIs, iCGM table, lag, decisions) | `analysis/METHODS_REVIEW.md` |
| 33 | Preprocessing and pair funnel | Which pairs are a fair test? | One shared module; pump entries and calibration fingersticks removed | 475,502 -> 168,990 pairs; MARD 10.4 -> 13.3 % | PRE; ACC s3 |
| 34 | Pump-entry check | Are pump "BG" entries fingersticks? | Share of pairs with zero error, by source and arm | 36.9 % exact matches vs 2.2 % for meter-log values | ACC s3; SUB s1 |
| 35 | Overall accuracy | How accurate is a working sensor? | MARD, bias, agreement shares; participant bootstrap | MARD 13.3 % (12.7 to 13.9), Set B | ACC s4 |
| 36 | Accuracy by range | Where is the error largest? | Pairs binned by the average of sensor and meter | MARD 19.6 % under 54 vs 10.3 % over 250 (Set B) | ACC s5 |
| 37 | iCGM benchmark | Does it meet the FDA rule's limits? | Binned by sensor value; lower one-sided 95 % bound | Fails all 7 criteria; within 20 %: 81.5 % (Set A) | ACC s6 |
| 38 | Misclassification and low detection | How often is a reading on the wrong side of 70 or 180? | 3 x 3 table of meter category against sensor category | Missed lows 28.2 % (Set A), 31.4 % (Set B) | ACC s7 |
| 39 | Limits of agreement | How far can one reading sit from the meter? | Bland-Altman with repeated measures | -67 to +57 mg/dL (Set A) | ACC s8 |
| 40 | Meter uncertainty | Could meter error explain the results? | ISO 15197-size random error added to the meter | At most +1.9 MARD points; low bias moves toward zero | ACC s9 |
| 41 | Shanghai comparator | Same picture with a flash sensor? | Same metrics on 4,012 pairs | MARD 13.9 %; bias -7.4 % | ACC s11 |
| 42 | Lag scan | How far does the sensor trail blood? | Re-pairing at shifts of -5 to 20 min | Best shift 5 min (real), 7 min (interpolated) | ED s3 |
| 43 | Lag-corrected low bias | Does the low bias survive lag correction? | Pair with the reading 5 min later | -6.5 % under 54 (-7.9 to -5.1) | ED s1 |
| 44 | Rate of change | Is fast change a separate fault? | Bias and MARD by trend bin, before and after the shift | Falling fast +12.7 % -> +0.7 % after the shift | ED s4 |
| 45 | Wear day | Is day 1 worse? | MARD by wear day in confirmed sessions | 15.2 % on day 1 vs 11.8 % on day 7 | ED s5 |
| 46 | Time of day (null per person) | Is night worse? | Night vs day, pooled and per person | Pooled 14.3 vs 13.2 %; per person -0.2 points | ED s6 |
| 47 | Mixed model | Which factors add error together? | Random-intercept regression on 143,051 pairs | Under 54 +5.8 points; day 1 +2.3; night +0.9 | ED s7 |
| 48 | Binning axis | Does the bin axis change the sign? | The same pairs binned three ways | Under 54: +29.8 % by meter, -22.5 % by sensor, -5.2 % by average | ED s8 |
| 49 | Trait tests, first pass (null) | Do six traits predict MARD? | Per-person MARD by group; BH correction | Nothing passes (smallest corrected p 0.15) | SUB s3 |
| 50 | Glucose pattern | What does predict MARD? | Spearman correlation per person | Glucose swings and time under 70: rho 0.33 each | SUB s4 |
| 51 | Exploratory traits (null) | Do other traits matter? | 22 tests with BH | One passed, gone after adjustment | SUB s5 |
| 52 | Deep trait check (null, one exception) | Any trait, pair of traits or site? | 680 tests listed in advance; one BH family | 1 of 680 survives: sex vs low-range bias | DD |
| 53 | Site | Does the clinic matter? | Share of spread between sites; permutation test | ICC 0.035, p 0.10 | DD s7 |
| 54 | Flexible models (null) | Is there a hidden pattern? | Forest, boosting, ridge; cross-validated | R-squared below 0 for traits; 0.03 for glucose pattern | DD s8 |
| 55 | Mediation | Trait -> glucose pattern -> MARD? | Standardised indirect effects with bootstrap CIs | Age chain -0.07 SD (-0.12 to -0.03) | DD s9 |
| 56 | Worst quartile (null) | Who is in the worst 25 %? | 140 tests, worst quartile against the rest | Nothing passes BH | DD s10 |
| 57 | Shanghai traits (null) | Do traits matter in the comparator? | 60 tests in a separate BH family | Smallest corrected p 0.97 | DD s11 |
| 58 | Medications follow-up (null) | Is "more drugs, lower MARD" real? | Adjustment for age and glucose pattern | Gone after adjustment (-0.12 points per drug, p 0.36) | DD s12b |
| 59 | Sex follow-up | Is the low-range sex gap real? | 74 tests listed in advance; matching; adjustment | +4.2 points (CI +2.0 to +6.3); absent in the CGM+BGM arm (+0.6) | DF |
| 60 | Day 1: settling vs early removal | Why is day 1 worse? | Rebuilt sessions; same sensors compared across days | Settling 92 % (85 to 100); early removal 8 % | WD s3-4 |
| 61 | Calibration timing | Does calibration timing explain day 1? | Error by time since the last calibration | Day 1 worse at every time; 19.3 vs 11.9 % just before a calibration | WD s6 |
| 62 | Simulation version 2: bias sweep | What does a constant bias do to decisions? | Real calculator records; bias -40 to +40 % | At -20 %: 7.2 % of decisions withheld; 50.8 % of highs not displayed | SIM2 s5 |
| 63 | Fault families | Which kind of fault hurts most? | Six families at matched size; 10 draws per person | Bias worst for doses; noise SD 10 misses 13 to 14 % of low episodes | SIM2 s6 |
| 64 | Meter as truth | What if the truth is a fingerstick? | 15,034 decisions with a verified fingerstick | The real sensor changes 4.2 % of doses by more than 1 U | SIM2 s7 |
| 65 | 180 vs 200 | Which high line? | Same outcomes at both lines | Hidden highs 51 % vs 59 % at -20 % | SIM2 s10 |
| 66 | Who is hurt most | Who gets the most false lows? | Spearman correlation with glucose metrics | rho -0.74 with mean glucose | SIM2 s9 |
| 67 | Summary metrics under bias | Does a low-reading sensor look better? | Time in range and risk indices on the shown trace | Time in range 63.3 -> 74.8 %; LBGI 0.95 -> 2.33 at -20 % | SIM2 s5 |
| 68 | Extended lookup | What happens past -40 %? | Bias -90 to +90 % in 2 % steps | Withheld flat at 54.2 % of decisions from -70 % | SIM2 s13 |
| 69 | Three-fault simulation | What do the FDA-described faults do? | Episodes of 2, 6, 12 h in fixed glucose bands | Per 6 h: 20.3 unneeded sugar treatments; 33.7 min hidden under 54; 1.29 U not given | SIM3 |
| 70 | Trial errors against reported errors | How often does a working sensor make a report-sized error? | Trial pairs counted at reported error sizes; participant bootstrap | -69 % or lower in 0.11 % of trial checks (0.073 to 0.15); 3.25 to 11.4 % of report pairs sit inside the trial's central 95 % range | TAIL |

## F. Limits already recorded in the memos

| Limit | What it does, and to which claim | Source |
|---|---|---|
| The reference is a home meter, not lab blood | Accuracy numbers (claims 2, 5) include meter error; error at the ISO limit would add up to 1.9 MARD points | ACC:160-170,205 |
| Fingersticks are not random; people test when they doubt the sensor | Missed-low and false-low rates (claim 2) describe tested moments, not all moments | ACC:144,206 |
| Narrow cohorts: adults; REPLACE-BG 94 % White; Shanghai Chinese in-patients | Claims 2 and 5 do not cover children or other groups | SUB:187; OV:112 |
| Old devices: Dexcom G4 (2012-2015), Libre H; the recalled sensor is the Libre 3; G4 software version not stated | Claims 1, 2, 4 transfer in kind, not in number; the comparison with published G4 values rests on a guess | ACC:211; FIND:226; PRE:108 |
| Set A has 77 people; all pump entries were dropped, including real fingersticks | Wide CIs for Set A rows; fewer pairs (5 people keep under 100) (claim 2) | ACC:207-208; SUB:191 |
| Readings clipped at 39 and 401 are kept; meter and receiver clocks differ by 1 to 2 minutes; 1,973 clock changes not corrected | Errors at the display limits are understated; slack in the lag estimate; some sessions split or merged (claims 2, 5) | PRE:126,128; ED:144-145 |
| Sensor sessions are inferred from gaps; no sensor ID; a restart looks like a replacement | Wear-day results (claim 5) rest on the session rules; early-removal share 8 % or 12 % | WD:220-221; PRE:94 |
| The day-1 low-range split was not pre-specified | Exploratory (claim 5) | ED:92; FIND:62 |
| Two-group splits can only detect 1.7 to 2.2 MARD points; groups under 10 not tested; 680 tests in one family is harsh | Small real trait effects could be missed (claim 5) | SUB:188; DD:388-389 |
| The sex gap is absent in the CGM+BGM arm; haematocrit and sensor site are not in the data | The sex gap (claim 5) stays modest and unexplained | DF:241-245 |
| The "true" glucose in the simulation is itself a sensor reading | Simulated decisions (claims 1, 4) start from a trace with its own error | SIM2:147; SIM3:139 |
| The simulation assumes the patient types the sensor value and follows the calculator | True for part of the trial: 68 % of typed values within 5 % of the sensor (CGM-only arm), 45 % (CGM+BGM arm) (claims 1, 4) | SIM2:149 |
| No meal, exercise or insulin-action model; no closed loop; a constant bias is a model, not the real error pattern | A changed dose is not followed to a changed glucose; claim 1 says what a bias would do, not what sensors do (claims 1, 4) | SIM2:150-151; FIND:47 |
| Pump settings are from 2015-16 pumps; 203 of 226 people have calculator records; fault sizes of the version 2 families were chosen, not measured | Dose results (claims 1, 4); the fault-family comparison | SIM2:148,153; FIND:75 |
| Three faults: sugar and missing insulin do not change glucose; sizes come from the nearest FDA groups; lengths of 2, 6, 12 hours are assumptions | Sugar counts are an upper bound; claim 4 is not a measured rate or duration | SIM3:137-138 |
| Three faults: all three hidden-low sizes give the same result; faults switch on sharply; "never shown as high" understates the floor-pinned fault; checking was light (three sanity checks, no independent number check) | Size cases say little for the hidden low; use the minutes row (claim 4) | SIM3:139-141; `logs/2026-11-20_1400_push-and-three-fault-simulation.md` |
| MAUDE is voluntary; counts are not failure rates; no count of sensors in use; reported errors are the harmful tail | Claim 3 describes reports, not typical sensors | RR:203-204; TR:172; OV:91 |
| Medtronic is undercounted (pump codes) and had the weakest agreement (about 0.6) | Medtronic rows are indicative only (claim 3) | DN:38; VAL:44 |
| The reference set was labelled by one AI reviewer; a teammate checked 100; no human-vs-model number | Limits how far the agreement numbers can be trusted (claim 3) | VAL:92 |
| Model weak spots: Dexcom direction (6 of 100), "none" overcounted, "hospital or ER" = any medical care | Outcome and fault-type shares (claim 3) | VAL:84-88; TR:143-145 |
| First pair only; "LOW" and "HI" display words are not pairs; pattern-only pairs have estimated, not measured, precision; about 1 in 5 serious prose pairs joins two moments | The most extreme reads-low cases are undercounted, more for Abbott; malfunction-only numbers (claim 3) | TR:188; RX:201-202 |
| Brand and era are mixed (Abbott 2024-2026 templates, Dexcom 2019-2021 prose); FDA outcome codes are coding habits; age and sex are filled mostly by Dexcom; sex not recorded before 2021 | Pooled malfunction numbers; brand gaps in outcomes; the children numbers (claim 3) | RX:94,200; BC:143,264-266 |
| Repeat reports about one sensor are not removed; texts arrive months late | CIs assume independent reports; post-recall numbers still changing (claim 3) | BC:339,341 |
| The lookup join uses the median person and a constant bias; reads-high errors are clipped at +90 % | Decision impact of reported errors (claims 1, 3) | TR:189 |
| Shanghai: 50 low pairs, 7.5 min timing slack, 10 type 1 patients | Comparator only (claim 5) | ACC:193; FIND:234 |
| Trial against reports: the reports are a selected set of failures, about other and newer sensors than the trial's G4; both sides lose the most extreme values (display limits 39 to 401; "LO" and "HI" are not pairs) | The comparison of trial and reported errors (claims 2, 3) is not a comparison of rates | TAIL:80-82 |

## G. Changes since the midterm plan

Plan = `docs/plans/2026-10-23_midterm-research-plan.pdf`, as summarised in PLAN. Tally recorded in FIND:160: done 11, done differently 5, not done 1.

| Topic | The plan promised | What was done | Reason recorded | Source |
|---|---|---|---|---|
| Research question | "how the magnitude and direction of CGM measurement errors vary across glycemic ranges and how frequently these errors result in glucose misclassification at the 70 and 180 mg/dL thresholds" | "how wrong does a glucose sensor have to be before a treatment decision goes wrong, and how wrong do sensors actually get, both when they fail and when they work?" | "the paper's spine felt weak and unclear"; decision: one question, three claims. A formal decision to replace the plan's question: NOT FOUND | PLAN:38; OV:10; `logs/2026-11-06_1400_spine-demographics-brands-regex-wearday.md` |
| Reference pairs; headline MARD | Meter pairs within 5 min (475,502), calibration pairs separately; MARD 10.4 % | Verified pairs: meter log, not a calibration, in the window (168,990); MARD 13.3 % (12.7 to 13.9) | Pump entries are often sensor values typed into the pump; a calibration fingerstick is not a fair test | PLAN:49,57; FIND:121-132 |
| Primary sample | CGM+BGM arm (77) primary; CGM-only arm as a check | Set B (226) leads; Set A is the check | The arms agree (13.8 vs 13.1 %); B has tighter CIs | PLAN:58; FIND:143 |
| Cleaning | Drop sensor-limit values | Kept and flagged | MARD 13.6 % without them vs 13.8 % | FIND:141 |
| Lag | Offsets 0, 5, 10, 15 min | Also -5 and 20 min and a 1-min interpolated scan | NOT FOUND | FIND:145 |
| Metrics | "within specified accuracy limits" | 15/15, 20/20, 40/40, median ARD, iCGM-style table | Standard toolkit in CGM accuracy papers | FIND:146; METH:26-27 |
| Subgroups | Age, sex, diabetes type, HbA1c, BMI, duration, arm, wear day, rate of change | All done with the participant as unit and BH; diabetes type only in Shanghai; then 680 tests and a sex follow-up | REPLACE-BG is all type 1; the null "surprised the project lead" | FIND:148; METH:146 |
| Low-range MARD claim; "calibration pairs are much worse" | 18.7 % (54 to 69) and 41.8 % (under 54); calibration pairs 14.1 % vs meter pairs 10.4 % (plan Table B1) | 16.4 % and 19.1 % (Set A); 16.9 % and 19.6 % (Set B). The calibration story is dropped (14.1 % vs 13.3 %) | The old numbers were binned by the meter value on contaminated pairs; the gap was mostly the pump-entry contamination | PLAN:86,90; FIND:133-134,173; ACCJ |
| Simulation | Bias 10, 20, 30 %; lines at 70 and 200; counts per person-day | Decisions from real calculator records; bias -40 to +40 % (then -90 to +90 %) in 2 % steps; six fault families; 180 leads, 200 is a check | Version 1 counted readings and measured the glucose pattern, not the sensor (15 to 30 times larger) | FIND:152; SIM2:17,131,143 |
| Simulation judged against iCGM criteria | Promised | Not done | iCGM limits are agreement percentages; the simulation gives decision counts | FIND:153 |
| "Simulated negative bias mostly causes missed highs" | Claimed | Changed: at -20 %, 1.19 missed high episodes vs 0.86 false low alerts per day, plus 7.2 % withheld doses | Version 1 counted readings | FIND:176 |
| Three-fault simulation | Not in the plan | Added 2026-11-20 | The report texts show faults tied to a glucose band, not one bias size | FIND:283; RX:177-180 |
| Day-1 settling analysis; sex follow-up | Not in the plan | Added 2026-11-06 | The project lead asked which story explains day 1, and whether the sex lead is real | METH:156,168 |
| MAUDE narrative review | "Remaining work" | Patterns, local model, reference set; then brand comparison, patterns over all reports, field inventory | The FDA codes say "wrong reading" but not how wrong | FIND:155; FM:13-14 |
| Role of FDA records | "Context only" | Reported error sizes feed the lookup join and set the three fault sizes | "That is the bridge to Phase 2" | PLAN:51; FM:14; SIM3:30-37 |
| MAUDE data route | openFDA API | Re-pulled from openFDA bulk files on the second computer | No API key there; the API road would take 5 days | DN:9-10 |
| Scripts; timeline; harm counts for other Class I recalls | explore_raw_data.py, bias_simulation.py, maude_pull.py, report_results.py; results about Nov 9, final repo about Nov 15; harm counts on the plan's gap list | New scripts (maude_pull.py is maude_robot.py; old scripts kept); three-fault simulation and first push on Nov 20; still only the Libre 3 row | NOT FOUND for all three | FIND:157,160; PLAN:156-159; OV:116 |

## H. NOT FOUND list

Asked for above and not recorded anywhere in the repo (checked again after REFS and TAIL appeared):

1. REPLACE-BG: trial registration number; dataset version or release; the attribution sentence that the Jaeb terms of use ask for (REFS [8] says one exists; the local ReadMe has none).
2. REPLACE-BG: sensor insertion site; ethics approval or consent statement.
3. Shanghai: collection years; hospital names; which data file version the team downloaded; a local ReadMe or licence file; sensor software or reader version; the meter brand ("not named", REFS [11]).
4. MAUDE: a licence text; a dataset publication; diabetes type of the people in the reports; sensor software versions; how many events are reported more than once.
5. FDA pull: any start or end date filter in the query (none is recorded). Recalls: harm counts for the six Class I recalls other than the Nov 2025 Libre 3 recall.
6. Reference set: how the 287 reports were drawn; which AI did the labelling.
7. Teammate check: who did it, how, the label file, and any agreement number between the human and the AI labels or between the human and the model.
8. Language model: sampling settings other than temperature 0, seed 42 and context 6,144; the model's licence; how many report texts were cut at 6,000 characters.
9. Hardware: CPU and RAM of both computers. Run time of the scoring script.
10. Confidence intervals: for the bias sweep at steps other than -10, -20, -30 % (and any CI for "withheld, % of needed corrections" or the share of high episodes not displayed); for the three-fault outcomes (only quartiles exist); for the medians of reported errors by maker (only IQRs, and CIs for differences); for kappa (only "about 0.03" sampling error).
11. Pattern-only pass: precision measured against the reference set.
12. A test of the difference in missed lows between Set A (28.2 %) and Set B (31.4 %).
13. How often, and for how long, a real sensor fault lasts; any failure rate per sensor.
14. Which Parkes grid version the makers use; which Parkes grid type the trial analysis uses.
15. Recorded reasons for the extra lag offsets, the script renames and the later timeline; a formal decision that replaces the midterm plan's research question.
