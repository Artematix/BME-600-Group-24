# Methods facts for the paper (built 2026-11-21)

- Facts for the "Dataset and Methods" section. No prose to copy. Each line has the fact, the exact value and where it is written. "not found" = the repo does not record it. "guess:" = an inference. "derived" = worked out from numbers on the same line or table.
- Words: sensor = continuous glucose monitor (CGM). Meter = fingerstick blood glucose meter. Pair = one sensor reading matched in time to one meter value. Seed = a fixed starting number that makes a random step repeat exactly. CGM-only arm = people told to dose from the sensor. CGM+BGM arm = sensor plus routine fingersticks.
- Sources are `file:line`. In `analysis/`: PRE = PREPROCESSING.md, ACC = ACCURACY_V2.md, ED = ERROR_DRIVERS.md, WD = WEAR_DAY.md, DD = DEMOGRAPHICS_DEEP.md, DDJ = demographics_deep_stats.json, SIM2 = SIMULATION_V2.md, S2J = simulation_v2_stats.json, SIM3 = SIMULATION_THREE_FAULTS.md, TAIL = TAIL_COMPARISON.md, REPRO = REPRODUCIBILITY.md, pp.py = preprocess.py, acc.py = accuracy_v2.py, sim2.py = simulation_v2.py, sim3.py = simulation_three_faults.py.
- In `fda-maude/`: FM = METHODOLOGY.md, DN = DATA_NOTES.md, FR = README.md, OPT = OPTIONS.md, GOLD = gold/GOLD_SET.md, PULL = results/PULL_SUMMARY.md, RR = results/report/report_results.md, llm.py = scripts/llm_extract.py. In `fda-maude/results/text/`: RUN = RUN_SET.md, VAL = VALIDATION.md, TR = TEXT_RESULTS.md, RX = REGEX_V2_FULL_CORPUS.md, PP = PATTERN_PRECISION.md, PILOT = PILOT.md. README = root README.md. REQ = requirements.txt. REFS = `docs/paper/REFERENCES.md`. OUT = `docs/paper/OUTLINE.md`.

## 1. Trial pairs (REPLACE-BG)
- **Matching rule.** A meter value is paired with the nearest sensor reading of the same person within 5 minutes, before or after. Source: pp.py:68,831, PRE:42.
- **Study window.** Day 0 to day 329 counted from enrolment, both ends included. It holds the run-in and the 26 randomised weeks. The sensor file stops at day 329. 7.4 % of sensor rows are older receiver data from before day 0. Source: pp.py:60, PRE:30,57, ACC:28,34.
- **Days of data per participant, median.** Two numbers exist. 235 days with sensor data in the window (middle half 200 to 252). 244 days from a person's first pair to the last pair. OUT M2 uses 244. Source: DD:80, SIM2:24, TAIL:15.

| Step | Rule | Left | Dropped (derived) | Source |
|---|---|---|---|---|
| 1 | Meter table without 3,408 ketone rows: 580,577 values. Keep 20 to 599 mg/dL. Other values are meter codes or unit errors | 580,527 | 50 | PRE:34-36,60 |
| 2 | A sensor reading exists within 5 minutes. These are the candidate pairs | 475,502 | 105,025 | PRE:42, ACC:41 |
| 3 | Inside the study window | 460,634 | 14,868 | ACC:42 |
| 4 | The value comes from the meter's own log. Pump "BG" entries removed | 285,166 | 175,468 | ACC:43, PRE:65 |
| 5 | The value was not used to calibrate the sensor. This is the final set | 168,990 (226 people) | 116,176 | ACC:44, PRE:44 |

- **Calibration values.** Calibration = a fingerstick typed into the sensor's receiver to correct the sensor. Why left out: "Those fingersticks are not a fair test" (ACC:13). How spotted: the meter value equals a calibration entry of the same person within 5 minutes (PRE:63, pp.py:69).
- **Pump entries.** Why left out: many are sensor values typed into the pump's dose calculator, not fingersticks. In the CGM-only arm about a third equal the sensor reading exactly. A real fingerstick does that about 2 % of the time. Source: PRE:65,73.

## 2. The language model that read the report texts
- **Model and program.** qwen2.5:7b-instruct. 7 billion parameters ("7B"). 4-bit version Q4_K_M, 4.7 GB, digest 845dbda0ea48. Run by Ollama 0.34.3 on the team's own computer. Python client `ollama` 0.6.3. Source: PILOT:3,115, VAL:3, llm.py:59, REQ:17.
- **Settings.** Temperature 0 (no randomness in word choice). Seed 42 (a retry uses 43). Context length 6,144 tokens (how much text the model holds at once). Answer cap 350 tokens. 8 requests at once. Report text cut at 6,000 characters. Answer forced into the fixed form (JSON schema). Source: llm.py:64-67,167-168, VAL:108, FM:141, FR:286.
- **Settings not set.** top_p, top_k and repeat penalty are not in the code (llm.py:168). guess: the Ollama defaults applied. The script's built-in defaults are prompt v2 and context 5,120 (llm.py:62-63). The real run passed `--prompt-version v3 --num-ctx 6144` (VAL:110).
- **Prompt files.** `fda-maude/prompts/v3_system.txt`, `v3_user_template.txt`, `v3_schema.json`. Version v3, about 2,900 tokens. History: `fda-maude/prompts/CHANGELOG.md:39-56`. The model reads the event text (FDA field D5), plus the maker's narrative (H10) when that is longer than 20 characters. Source: FR:286, FM:106.
- **Fixed form, 12 fields.** fault_type (10 choices), sensor_value_raw, sensor_unit, meter_value_raw, meter_unit, multiple_pairs, parkes_zone_stated, wear_day, fingerstick_check_done, user_action (7 choices), outcome_severity (7 choices), confidence. Source: `fda-maude/prompts/v3_schema.json`, FM:78-88.
- **Word-for-word rule.** "Every extracted number must appear word-for-word in the text, or it is dropped." Numbers were dropped in 4,324 of 124,599 reports (3.5 %). Final value = the pattern value when the Abbott template matched, else the model value. Source: FM:91, llm.py:184-204, TR:21, VAL:6.
- **Run.** 2026-10-30, 9.55 hours, 124,599 reports, 0 errors, 0 retries. No text was cut by the context length (longest prompt 5,889 tokens). Source: TR:16-20.

## 3. The text patterns
- **What and where.** Fixed text rules (regular expressions) written by the team. `fda-maude/scripts/extract_regex.py` (version 1) and `fda-maude/scripts/extract_regex_v2.py` (version 2, keeps every version 1 pattern). Source: FM:67, PILOT:12, RX:3,196.
- **How many.** No memo gives a count. Counted in the code: 36 lines that define a pattern in version 1 and 40 more in version 2, so about 76 (search the two scripts for `re.compile`).
- **What they look for.** The Abbott template sentence, sensor and meter values in free prose, display words (LOW, HI), bounds ("over 400"), a stated Parkes zone, the wear day, units (mmol/L x 18). Source: PILOT:12, RX:43-56.
- **How a pair is decided.** The text states both a sensor value and a meter value. First pair in the text. Sensor 20 to 600 and meter 20 to 1,500 mg/dL. Two equal values are not a pair. Bounds and display words are flags, not values. Source: RX:16,22,196, TR:40.
- **"Tuned patterns".** Version 2 was adjusted against the model's pairs on the 124,599 texts the model read. Then it ran alone over all 3,382,071 reports (3,144,535 have text) in 7.8 minutes. It found 209,388 pairs, 191,112 of them in malfunction-only reports. Source: RX:3,8,25,76.
- **"89 in 100".** The model found 18,436 pairs. Version 2 found 89.1 % of them (version 1: 73.1 %). Where both found a pair, the two numbers were the same in 88.4 %. Source: RX:33.
- **Check by reading.** 100 random malfunction-only pairs (seed 20261120) read by an AI reader (Claude): 97 right, 3 unclear, 0 wrong. 95 % interval 91.5 to 99.0. Against the reference set: 74 of 74 pattern pairs right, 3 of 77 missed. Source: PP:8-13,25.

## 4. The reference set of 287 reports
- **How picked.** Not random. Per maker, 50 malfunction and 50 death or injury reports, "newest first", pulled from openFDA. Abbott Libre 3: 100. Dexcom G7: 100. Medtronic Guardian: 87 (it has only 37 serious reports). File: `fda-maude/data/sample_narratives.jsonl`. The script that made it: not found ("made by a small script"). Source: OPT:25-27, GOLD:7,17-20.
- **Dates received.** OPT:26 says 2024-01 to 2026-06. GOLD:7 says 2011 to 2026, most from 2026. The two do not match.
- **Who labelled.** One AI reviewer read every report in full with a written rubric (`fda-maude/gold/RUBRIC.md`). OUT names it: Claude Opus 5.5, high reasoning setting. One author (Artemy) read 100 of the 287 and changed no label. Source: GOLD:8, OUT:314,368-369.
- **Kappa (agreement beyond chance, 1 = perfect).** 0.77 fault type. 0.75 severity (exact 0.745). Compared: the final output of patterns plus model (prompt v3) against the reference labels, on all 287 reports. Cohen's kappa from scikit-learn. Source: VAL:6,11,20-21, `fda-maude/scripts/score_against_gold.py:41,198`.
- **Interval.** not found. None is computed. VAL:28 only states "a sampling error of about 0.03".
- **By maker and targets.** Fault type: Abbott 0.88, Dexcom 0.71, Medtronic 0.63. Severity: 0.71, 0.87, 0.62. Targets set before scoring: 0.70, 0.75, and 95 % of numbers exact (result 96.2 %). Source: VAL:14,25,34-39.

## 5. Accuracy measures as the code computes them
- **Error, bias, MARD.** Error = sensor - meter, in mg/dL. Percent error = (sensor - meter) / meter x 100. Bias = the mean error (negative = the sensor reads low). MARD = the mean of the absolute percent error. Source: pp.py:777-780, acc.py:221, ACC:9.
- **20/20 agreement.** A pair agrees when it is within 20 mg/dL if the meter is under 100 mg/dL, or within 20 % if the meter is 100 or more. Source: acc.py:124-127.
- **Range edges.** Under 54. 54 to 69. 70 to 180 (both ends in). 181 to 250. Over 250 mg/dL. A pair is placed by the average of its sensor and meter value. Low = under 70. High = over 180 (check: 200). Source: acc.py:106-109,118-121,725, pp.py:781.
- **Bootstrap (redo the count on random re-draws to get a 95 % interval).** 1,000 resamples. Participants are re-drawn, not pairs. Seed 600. Interval = 2.5th to 97.5th percentile. Source: acc.py:45-46,157-171,191, ACC:12.
- **Bootstrap, other analyses.** Sensor delay: 1,000, seed 20261027. Wear day: 1,000, seed 20261106. Trait tests: 2,000, seed 600. Trial against reports: 2,000, seed 600. Source: `analysis/error_drivers.py:59-60`, `analysis/wear_day.py:69-70`, `analysis/demographics_deep.py:82-83`, TAIL:10.

## 6. Sensor delay, day of wear, settling
- **Delay.** Each meter value is paired again with the sensor reading nearest to (meter time + T), for T = -5, 0, 5, 10, 15, 20 minutes. A finer scan uses a straight line between readings, in 1-minute steps from -10 to 20. The delay is the T with the lowest MARD. Result: 5 minutes on real readings, 7 minutes on the straight-line trace (163,174 and 152,072 pairs). Source: ED:52,58, `analysis/error_drivers.py:62-65`.
- **Day of wear.** The data has no sensor-start marker. A gap of 115 minutes or more between readings starts a new sensor session (the sensor has a 2-hour warm-up). Wear day 1 = the first 24 hours after the first reading. A session is "confirmed" when a calibration was entered in the 30 minutes before its first reading. Source: PRE:83-85, pp.py:63-64, WD:5,20.
- **Joining pieces.** An unconfirmed piece is joined to the session before it, unless the result would pass 170 hours. 8,521 sessions. 163,198 of the 168,990 pairs kept. Source: WD:22,29,33.
- **Settling against early removal.** Extra error on day 1 = day-1 MARD of all sessions - day-7 MARD. Early-removal part = day-1 MARD of all sessions - day-1 MARD of sessions that reached day 7. Settling part = day-1 MARD of sessions that reached day 7 - day-7 MARD. Result: extra error 3.3 points, settling 3.0 points (92 %, interval 85 to 100), early removal 0.25 points (8 %). Source: `analysis/wear_day.py:436-437`, WD:13.

## 7. The 680 trait tests
- **Unit and measures.** One participant (226). Seven error measures per person: MARD, low-range MARD, bias, low-range bias, missed-low rate, false-low rate, share within 20/20. Source: DD:111.
- **Split.** 407 single-trait + 133 interaction + 140 worst-quartile = 680. The list was written before any test ran. Source: DD:110,115-123, DDJ (bh_summary.tests_per_block).
- **Single-trait tests.** Each testable trait against each error measure. Two groups: Mann-Whitney test. Three or more groups: Kruskal-Wallis test. Number traits: Spearman correlation. Groups under 10 people dropped. Source: DD:115.
- **Interaction tests.** 18 trait pairs x 7 measures = 126, plus clinic site x arm x 7 = 7. Regression with a product term and robust errors. Site x arm: F-test with a permutation p-value. Source: DD:116,125.
- **Worst-quartile tests.** The 25 % of people with the worst MARD against the rest, and the same for the missed-low rate. 70 tests each. Mann-Whitney, Fisher or chi-square. Source: DD:120,281.
- **Which traits.** 62 tested, 6 only described (too few people). Kinds: age, sex, race, education, income, insurance, body size, HbA1c, diabetes duration, low-glucose history and awareness, questionnaires, conditions, medications, pump and sensor use, study arm, clinic site, run-in. Source: DD:20-80, DDJ (preregistration).
- **Correction and result.** Benjamini-Hochberg (a correction for running many tests) at 0.05, over all 680 as one family. 69 tests had a raw p under 0.05 (34 expected by chance). 1 passed. Source: DD:8,123, `analysis/demographics_deep.py:92,187,215`.

## 8. The simulation
- **True glucose.** The recorded sensor trace on a 5-minute grid. 226 people, 13,705,193 readings. Shown values stay inside 39 to 401 mg/dL. Source: SIM2:23,33,41.
- **Dose formula.** dose = (glucose - target) / ISF - IOB. Never below 0. Zero unless glucose is above the pump's "correct above" level. It matches the pump's own recorded correction within 0.15 units in 90 % of records. Source: SIM2:36, sim2.py:192,797, S2J:101.
- **Personal settings.** Target, "correct above" level, ISF (insulin sensitivity factor: mg/dL that one unit lowers glucose) and IOB (insulin on board: insulin still working). All four come from the same calculator record. Source: SIM2:7-8,36, sim2.py:187-196.
- **Records used.** 232,329 calculator records in the window. 172,929 with a typed glucose. 159,878 of these also have a sensor reading within 5 minutes. These are the decisions. Why 203 of 226: "Only 203 of 226 people have wizard records with a typed glucose". Outcomes that need no dose use all 226. Source: SIM2:25-26,153, S2J:98-104.
- **Needed correction.** A dose above 0.5 units without the error. Withheld = that dose becomes 0 with the error. Source: sim2.py:123,410-411, SIM2:37.
- **Display lines and episodes.** Low under 70 and under 54 mg/dL. High over 180 (check: 200). 15 minutes (3 readings) beyond a line starts an episode. 15 minutes back ends it. A true episode counts as shown when a shown episode runs at any time from 30 minutes before its start to its end. Source: sim2.py:116-119, SIM2:10,39.
- **Steady error levels.** -40 to +40 % in 2 % steps (41 levels). Widened on 2026-10-30 to -90 to +90 % in 2 % steps (91 levels). Source: SIM2:46,164, REPRO:18.
- **Sugar rule.** The sensor shows under 70: 15 g of fast sugar, at most once every 15 minutes while it still shows under 70. "Unneeded" = the true glucose was 70 or above. Source: SIM3:51-52, sim3.py:65-67.
- **Fault episodes.** Lengths 2, 6 and 12 hours. 200 random starts per participant, per fault and per length, no repeats. A start is a reading where the true glucose is inside the fault's range. 45,200 false-low and 45,021 floor-pinned episodes per length. 38,575 hidden-low at 2 hours (66 people had fewer than 200 readings under 54, and 1 had none). Source: SIM3:24,43-46, sim3.py:60-61,289-291.
- **Seeds and reference rows.** Seed 20261120 for the three faults. Seed 20261027 for the steady error (1,000 bootstrap resamples). Reference rows: a steady error of -20, -40 and -66 % in the same episode windows, and a no-fault row. Source: sim3.py:58, sim2.py:114,145, SIM3:27,92.

| Fault | Acts when the true glucose is | Sensor shows | Small and large case | Report numbers behind the size | Source |
|---|---|---|---|---|---|
| False low | 70 to 250 mg/dL | true value - 69.4 % | -61.9 % and -76.7 % | Median error of the malfunction-only pairs that read low (191,112 pairs, 74.7 % read low). Quartiles read from 10-point bins | SIM3:20,30-31,47 |
| Hidden low | under 54 mg/dL | true value + 163.6 % | +88.9 % and +328.6 % | Median and quartiles of the 8,644 death-or-injury pairs where the sensor read above the meter | SIM3:21,34,48 |
| Floor-pinned | over 250 mg/dL | 39 mg/dL | Small: -72.7 %, not pinned. No large case | 39 = the lowest value the simulation lets a sensor show. Reports quote "LO (LESS THAN 40 MG/DL)". -72.7 % = median of death-or-injury pairs that read low | SIM3:22,36,49 |

- "No FDA table holds the exact groups asked for". Each size comes from the nearest group in the tables (SIM3:37).
- **Source of "68 in 100".** 68.4 % of 111,221 typed values in the CGM-only arm were within 5 % of the nearest sensor reading. 25 % were identical. CGM+BGM arm: 45.1 % of 48,657. Source: SIM2:38, sim2.py:208-210, S2J:107-115.
- **Source of "same per hour for 2, 6 and 12 hours".** SIM3:106-118 (table 4d, medians per hour of fault). Unneeded sugar: false low 3.88, 3.86, 3.84 and floor-pinned 4.25, 4.25, 4.25. Doses withheld: 0.066, 0.067, 0.067 and 0.22, 0.22, 0.22. See flag 2.

## 9. FDA reports
- **13 product codes.** QBJ, PQF, MDS, QLG, PZE, SFI, SBA, SAF, QHJ, QCD, QDK, QII, SBH. Source: `fda-maude/scripts/config.json:3`, DN:18-24.
- **Date range.** Reports received 1992-03 to 2026-09. Newest report 2026-09-30. The query sets no start or end date. Source: RR:8, DN:5, `fda-maude/scripts/maude_robot.py:55,740`.
- **Pull 1.** openFDA web service (API), 2026-10-19. FDA data last updated 2026-10-07. Used for the counts by code, maker and year. Source: PULL:3-4,17, RR:8.
- **Pull 2.** openFDA bulk files (375 zip files, 19.6 GB). FDA data as of 2026-10-21, bulk export 2026-10-23. The memo title says "full pull of 2026-10-26". Used for the texts. Both pulls hold the same 3,382,071 reports, with the same count for every code. Source: DN:1,5,10,12, RUN:3, FM:104.
- **Counts.** 3,382,071 reports (each once, 91 list two codes). 123,607 serious (death or injury). 3,257,570 malfunction. Source: DN:24, PULL:14, RUN:18,23.
- **Serious texts read.** 118,462 = 123,607 - 5,135 received after 2026-07-21 - 10 with no text. Why the date cut: texts arrive late, so only reports received 3 months or more before the 2026-10-21 data are read. Source: RUN:3,18-22, FM:61.
- **How the 6,137 were sampled.** From the 2,936,278 malfunction reports received by 2026-07-21. Groups = product code x year received (95 groups). Target 5,000. At least 25 per group. Groups smaller than 25 taken whole (19 groups). Simple random draw inside each group, seed 20261019. 6,168 drawn, 6,137 have text. One sampled report stands for (group size / number sampled) reports. Source: RUN:4,11,23-28, `fda-maude/scripts/build_run_set.py:8-12`.
- **Texts read.** 118,462 + 6,137 = 124,599. Source: RUN:29.

## 10. Shanghai data
- **Files.** `Shanghai_T1DM_Summary.xlsx`, `Shanghai_T2DM_Summary.xlsx`, and the folders `Shanghai_T1DM/` and `Shanghai_T2DM/` with one Excel file per patient visit. 125 files read, 3 lock files skipped. Source: REPRO:48-53, PRE:46, pp.py:105.
- **How a pair is defined.** A fingerstick value (column "CBG") written on a sensor row. Sensor rows are 15 minutes apart, so the two can be up to 7.5 minutes apart. Source: pp.py:642,851-855, PRE:45,124.
- **Counts.** 112 patients. 98 have a pair. 4,012 pairs from 4,012 fingersticks. 127,982 sensor readings. 17 files have no fingerstick. Per-patient tests need 10 or more pairs: 76 patients, 3,926 pairs. Source: ACC:32, PRE:45-47, DD:304.

## 11. Software and hardware
- **Python and packages.** Python 3.11 (3.11.9 at the last checked run). pandas 2.3.3, numpy 2.3.5, matplotlib 3.10.7, pyarrow 22.0.0, openpyxl 3.1.5, xlrd 2.0.2, scipy 1.16.3, statsmodels 0.14.6, requests 2.32.5, scikit-learn 1.8.0, ollama 0.6.3. Source: REQ:2,7-17, REPRO:71. REPRO:37 and REPRO:71 are out of date about the package list.
- **Model runner and hardware.** Ollama 0.34.3. Text step: NVIDIA RTX 5080 with 16 GB, Windows 11. Trial analysis: "SSD laptop", Windows 11, about 1 GB of memory for the sensor table. CPU and RAM: not found. Source: VAL:3, REPRO:24,57,71.

## 12. Data-use terms, as the repo's own documents state them
| Dataset | Wording | Source |
|---|---|---|
| REPLACE-BG | "Jaeb terms of use. No redistribution." Also: "We follow each source's terms: REPLACE-BG (Jaeb) may not be redistributed, so only code and summary numbers are in this repo, and Shanghai is credited under CC BY 4.0." | README:76,164 |
| REPLACE-BG, dataset page read on 2026-11-20 | "terms = users must include a set attribution sentence ("The source of the data is ..."), the publisher gives no warranty, and users carry all responsibility and liability." Also: "the page names no licence. The words "no redistribution" are not on the page." Warning: "Do not state "no redistribution" on the strength of the web page." | REFS:96-97,791 |
| Shanghai | "CC BY 4.0 (reuse allowed with credit)". Also: "Licence of the data file = CC BY 4.0." | README:77, REFS:127 |
| openFDA (MAUDE) | "Public US government data". No licence text or terms page is recorded | README:78 |
| All three | "All data is public and de-identified, and we never try to re-identify anyone." Also: "We do not quote personal details from MAUDE report texts." Team log: "Data-use terms were not checked" | README:164, `logs/2026-11-20_1400_push-and-three-fault-simulation.md:27` |

## 13. Dataset versions, download sources, access dates
- **REPLACE-BG.** Source: `https://public.jaeb.org/dataset/546`. Version: not found. The dataset's ReadMe file was last saved on 2018-01-09 (a file property, not a release number). Access date: "Oct 7, 2026". Written in: README:76, `Uncommitted Data/Raw Data Dump/Replace-BG Dataset/ReadMe.rtf:398`.
- **Shanghai.** Source: Figshare, doi:10.6084/m9.figshare.c.6310860. Collection version 2 (2023-01-04). Data file version 5 (2023-10-30). Which one the team downloaded: not found. The local folder name starts "2022.11". Access date: "Oct 7, 2026". Written in: README:77, REFS:124-127.
- **FDA MAUDE.** Source: openFDA API (`api.fda.gov/device/event.json`) and openFDA bulk files. Pull 1: FDA data of 2026-10-07, pulled 2026-10-19. Pull 2: FDA data of 2026-10-21, memo dated 2026-10-26. Written in: PULL:3-4, DN:1,5, README:78.

## Flags for the writer (the outline and the sources differ)
1. OUT M2 says the reports were "pulled through the openFDA service on 2026-10-19". That is pull 1. The texts that were read come from pull 2 (bulk files, FDA data of 2026-10-21). Both hold the same 3,382,071 reports.
2. "Same per hour for 2, 6 and 12 hours" (OUT O10) holds for unneeded sugar and withheld doses. It does not hold for false low alerts under 70 per hour: 0.49, 0.20, 0.13 (false low) and 0.78, 0.57, 0.55 (floor-pinned). Low alerts under 54 not shown: 0.85, 0.90, 0.95. Source: SIM3:116-118.
3. "68 in 100" counts every calculator record of CGM-only-arm people in the study window. The code splits by arm, not by phase, so the run-in weeks are inside. Source: sim2.py:185,204-210.
4. DD:115 writes "61 of 67 traits x 7 = 407". 61 x 7 is 427. DDJ lists 62 tested traits and 6 described only. Counted from DDJ: 62 tests each for MARD, bias and 20/20, 55 each for the two low-range measures, 53 for missed lows, 58 for false lows. That adds to 407. Write "407 single-trait tests", not "61 x 7".
5. README says "No redistribution" for REPLACE-BG. REFS found no such words on the dataset page (section 12).

## Still missing
- Item 2: sampling settings other than temperature and seed (top_p, top_k, repeat penalty). The model's licence. How many report texts were cut at 6,000 characters. Looked in llm.py, VAL, TR, FR, PILOT.
- Items 3 and 4: a count of the patterns in any memo (only the code-line count). The script that pulled the 287 reports. A confidence interval for kappa. Looked in PILOT, RX, FM, FR, OPT, VAL, `fda-maude/gold/`, `fda-maude/scripts/`, `logs/`.
- Items 9 and 11: the exact day the bulk files were downloaded (DN title says 2026-10-26, the FM entry is dated 2026-10-27). CPU and RAM of both computers. Looked in DN, FM, PULL, REPRO, VAL, PILOT.
- Item 12: the attribution sentence the Jaeb terms ask for (not in the local ReadMe). The full text of the Jaeb terms (REFS gives a summary only). Any licence or terms text for openFDA. Looked in README, REFS, `fda-maude/`, `docs/plans/`, `logs/`.
- Item 13: the REPLACE-BG dataset version or release. Which Shanghai file version was downloaded. A source for the access dates other than README (OUT G6: "from Artemy", "later").
