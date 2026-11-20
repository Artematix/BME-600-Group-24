# Preprocessing audit: analysis/preprocess.py (2026-10-27; verified-fingerstick rule added 2026-10-30)

Terms: CGM = continuous glucose monitor (skin sensor, a reading every 5 min). Meter / BGM = fingerstick blood glucose meter. Calibration = a fingerstick value typed into the Dexcom receiver to correct the sensor. Pair = one CGM reading matched to one reference (fingerstick) value. Sensor session = the days one sensor was worn. Pump BG entry = a glucose value stored by the insulin pump (typed by hand or sent by a linked meter). Verified fingerstick = a reference value from the meter's own log that was not used for calibration. Cache = cleaned tables saved as parquet files (a fast binary table format) in `analysis/cache/`, not in git.

## 1. How to run and use

Build or refresh the cache (about 40 s, 390 MB): `python analysis/preprocess.py "Uncommitted Data/Raw Data Dump" analysis/cache --rebuild`
Scripts build it on their own the first time they need it. Every rule change must bump `CACHE_VERSION` in the module; old caches are then rebuilt automatically.

```python
import sys; sys.path.insert(0, "analysis")
import preprocess as pp
ROOT = "Uncommitted Data/Raw Data Dump"
cgm = pp.load_cgm(ROOT)                           # 14.8 M rows, about 1 s; filter with cgm.in_study_window
pairs = pp.verified_pairs(ROOT)                   # HEADLINE set: verified fingerstick pairs in the study window (168,990 pairs)
allp  = pp.build_pairs(ROOT)["meter"]             # every meter-table pair, flagged (from_meter_log, is_verified_fingerstick, ...)
```

Other loaders: `load_calibrations`, `load_bgm`, `load_pump` (dict: bolus, basal, wizard), `load_participants`, `load_shanghai` (dict: patients, cgm, cbg, files), `read_manifest` (all counts below). `build_pairs` returns a dict: calibration, meter, independent_meter (old view, pump entries kept), verified (= `verified_pairs()`), shanghai. Every function takes the data folder first; `rebuild=True` forces a rebuild.

## 2. Data flow (rows kept and dropped)

| Table | Step | Rows |
|---|---|---|
| CGM | rows in HDeviceCGM.txt | 14,950,661 |
| CGM | calibration rows moved to their own table | 143,226 |
| CGM | CGM readings kept in the cache (all days, flagged) | 14,807,435 |
| CGM | duplicate person+timestamp rows (flag `is_duplicate`; dropped by default) | 1,356 (1,274 before day 0, 82 in window) |
| CGM | rows before day 0 (flag `in_study_window` = False) | 1,102,160 |
| CGM | rows after day 329 | 0 (the file already stops at day 329) |
| CGM | in window, duplicates dropped | 13,705,193 |
| CGM | clipped at 39 / at 401 (kept, flagged) | 28,885 / 48,935 |
| Calibrations | rows / value outside 20-600 (flagged) | 143,226 / 2 |
| BGM | rows in HDeviceBGM.txt / ketone rows excluded | 583,985 / 3,408 |
| BGM | meter rows kept (all days, flagged) | 580,577 (312,756 from meters, 267,821 from pumps) |
| BGM | value below 20 / at or above 600 (flagged, excluded from pairs) | 16 / 34 |
| BGM | before day 0 / after day 329 (flagged) | 77,554 / 47 |
| BGM | exact repeats (same person, time, value; flagged, kept) | 6,422 |
| BGM | pump rows that copy a meter reading (flagged, kept) | 71,809 |
| BGM | rows from the meter log (`from_meter_log`) / of which verified fingersticks (`is_verified_fingerstick`, not used for calibration) | 312,756 / 191,320 |
| Pairs | calibration pairs (calibrations 20-600 with a CGM reading up to 10 min before) | 120,202 of 143,224 (116,244 in window) |
| Pairs | meter pairs (meter rows 20-600 with a CGM reading within 5 min) | 475,502 of 580,527 = 81.9 % (460,634 in window) |
| Pairs | meter pairs flagged `used_for_calibration` / independent pairs | 155,636 / 319,866 |
| Pairs | meter pairs in window -> drop pump BG entries (`from_meter_log`) -> drop calibration fingersticks = verified (`is_verified_fingerstick`; the headline set, `verified_pairs()`) | 460,634 -> 285,166 -> 168,990 (226 people, MARD 13.3 %) |
| Pairs | Shanghai pairs (CBG on a CGM row) | 4,012 of 4,012 |
| Shanghai | files read / lock files skipped / rows without a date dropped | 125 / 3 / 92 (one file, all empty) |
| Shanghai | CGM readings / fingersticks / files with no fingerstick | 127,982 / 4,012 / 17 |

Pairs by reference range: calibration 1,319 / 5,270 / 73,246 / 27,474 / 12,893; meter 4,166 / 15,944 / 261,471 / 128,495 / 65,426; Shanghai 7 / 30 / 2,531 / 967 / 477 (ranges <54, 54-69, 70-180, 181-250, >250 mg/dL).

## 3. Cleaning rules

| Rule | Reason | Source |
|---|---|---|
| Time = `DeviceDtTmDaysFromEnroll` * 86400 + `DeviceTm` seconds (`t`). `dt` is a fake date: day 0 = 2000-01-01. | Dates are de-identified; only days from enrolment exist. | ReadMe: "number of days from enrollment". |
| `DexInternalTm` not used. | It differs from `DeviceTm` by whole hours (-6 to -9 h) and is blank in 592,772 rows. guess: it is the receiver's UTC clock. | Observed. |
| Study window = day 0 to 329 (`in_study_window`). | 7.4 % of CGM rows are old receiver data from before enrolment. | RESULTS.md pitfall 2; observed. |
| Duplicates = same person and same `t`; keep the row with the lowest RecID. | 1,356 repeats, mostly the same data uploaded twice. In 436 groups the two copies differ (median gap 112 mg/dL): guess, two devices or a clock change. Neither copy is "right"; the rule is only deterministic. | Observed. |
| Clipped values: `is_clipped_low` (39) and `is_clipped_high` (401). Kept. | The G4 cannot show values outside 39-401. | Observed (min 39, max 401). |
| Reference values must be 20 to 599 mg/dL for pairing. | Below 20 = LO code or a mmol/L entry; 600+ = HI code. | Meter range; observed values 2, 3, 8, 9, 19, 600, 601. |
| Rate of change = (next - previous reading) / minutes between them; NaN unless both neighbours are 4-6 min away. | Gaps and clock-change overlaps would give nonsense slopes. | Observed: 99.0 % of gaps are 4-6 min. |
| `is_night` = 00:00 to 06:00 device time. | Project definition. | - |
| Meter row `used_for_calibration` = a calibration with the same value within 5 min. | Receiver and meter clocks differ by up to a few minutes. 1 min catches 94,706 rows, 2 min 139,315, 5 min 162,746, 15 min 168,590. Chance matches (calibration times shifted by 6 h): 44. | Observed. |
| Meter row `source` = meter or pump; `pump_copy_of_meter` = same value as a meter row within 5 min. | 267,821 BGM rows come from pump uploads (typed or sent to the pump); 71,809 repeat a meter reading, so they double-count in pairs. | HDeviceUploads device type. |
| `from_meter_log` = the value comes from the meter's own log (source = meter). `is_verified_fingerstick` = from_meter_log and not `used_for_calibration`. Headline pairs = verified and in window (`verified_pairs()`). | Pump BG entries are often CGM values typed into the pump's bolus calculator: in the CGM-only arm about a third of them have an error of exactly 0 (a real fingerstick: about 2 %); elsewhere 9-20 % do. `used_for_calibration` does not catch them; `pump_copy_of_meter` catches only 12 %. Details in section 3b. | ACCURACY_V2.md section 3; ERROR_DRIVERS.md; SUBGROUPS.md section 1. |
| Wizard glucose fields * 18.01559 (mmol/L to mg/dL). | ReadMe says mg/dL; data max is 33.3 = 600 mg/dL, so the unit is mmol/L (Tidepool stores mmol/L). | Observed. |
| Bolus `Duration`: minutes for Diasend uploads (13,933 rows), milliseconds for Tidepool. Bolus types unified (Normal = normal, Combination = dual/square). | Two upload systems. | ReadMe HDeviceBolus. |
| Basal `duration_suspect` = negative or over 24 h (99 rows). | Pump log errors. | Observed. |
| Shanghai: columns matched by name prefix; Chinese names mapped; lock files skipped; rows without a date dropped; "/" = missing in lab columns; HbA1c % = mmol/mol / 10.929 + 2.15. | 7 files have odd headers. All glucose values are multiples of 1.8, so no file needs mmol/L conversion. | Observed; IFCC-NGSP formula. |

## 3b. The verified-fingerstick rule (added 2026-10-30)

The BGM table mixes two sources: 312,756 rows from the meters' own logs and 267,821 from pump uploads (BG values typed into the pump or sent by a linked meter). In the CGM-only arm people dosed from the CGM and typed its number into the bolus calculator, so about a third of those pump entries have an error of exactly 0 against the CGM; a real fingerstick does that about 2 % of the time. In the other arm and in run-in, 9-20 % of pump entries look the same. The `used_for_calibration` flag does not catch them, and `pump_copy_of_meter` catches only 12 %. Pump entries made the sensor look better than it is: MARD 10.4 % (midterm, all pairs) against 13.3 % on verified pairs. Rule: a reference is a verified fingerstick when it comes from the meter log AND was not used for calibration. Every BGM row and meter pair carries `from_meter_log` and `is_verified_fingerstick`; `verified_pairs()` (same as `build_pairs()["verified"]`) returns the verified pairs inside the study window and is the headline set for the paper: 168,990 pairs, 226 people, MARD 13.3 %. We drop all pump entries, including real fingersticks that only reached the pump: we lose pairs, not validity.

| Who uses what | Flag |
|---|---|
| accuracy_v2.py (sets A, B, C), error_drivers.py (analysis set), subgroups.py (participant metrics) | `is_verified_fingerstick` |
| simulation_v2.py (meter-as-truth check) and the timing-slack check in error_drivers.py | `from_meter_log` only: they match calibration rows first, then drop and count them themselves |
| explore_raw_data.py, bias_simulation.py (midterm numbers, kept as history) | none: all meter pairs, pump entries and calibrations included |

## 4. Sensor sessions and wear day

Rule: a new session starts when the gap to the previous reading of the same person is 115 min or more (`SESSION_GAP_S` = 6,900 s). `wear_day` = 1 on the session's first day. `session_confirmed_by_cal` = a calibration was entered in the 30 min before the first reading.
Why 115 min: the G4 has a 2-hour warm-up with no readings after every sensor start. Gaps between 95 and 115 min are rare (about 25 per minute); at 115-120 min they jump to 462 per 5 min, with spikes at exactly 2 h, 2 h 5 min, 2 h 10 min. A 3-hour rule would miss a third of the restarts.
No table marks a sensor start: `RecordType` holds only CGM and Calibration, `HDeviceEvents` holds only clock changes, and `HComplUnblindCGM.UnblindCGMSensor` only records the first study sensor at the end of run-in.

| Check (sessions touching the window, duplicates dropped) | Value |
|---|---|
| Sessions | 10,812 |
| Length 6.5-7.1 days (the G4 7-day limit minus warm-up gives 6.92 days) | 41.7 % (4,506); this is the peak of the histogram |
| Length over 7.5 days / under 1 day | 0.55 % / 16.4 % |
| Preceded by a start-up calibration: all / 6.5-7.1-day sessions / under-1-day sessions | 78.8 % / 98.3 % / 49.1 % |

Limits: the G4 asks for two calibrations after warm-up, so a real start is almost always "confirmed". Half of the sub-day fragments are not, so guess: they are signal-loss gaps of 2 h or more inside one sensor wear, not new sensors. `wear_day` restarts at 1 for them. Use `session_confirmed_by_cal` and `session_days` to keep only clean sessions. Clock changes (see section 7) can also split or merge sessions.

## 5. Pump wizard fields (HDeviceWizard) and the two ReadMe facts

| Raw column | ReadMe says | Unit in the data | Cache column |
|---|---|---|---|
| BgInput | "Blood glucose as inputted into wizard in mg" | mmol/L (max 33.3); 0 = none entered | `bg_input_mgdl` (0 becomes NaN), `bg_input_entered` |
| CarbInput | "Carbohydrates ... in mg" | grams (0-370) | `carb_input_g` |
| InsulinCarbRatio | "mg carbs covered by unit" | grams per unit (3-45) | `icr_g_per_u` |
| InsulinSensitivity | "bgs covered by unit" | mmol/L per unit (0.56-11.1) | `isf_mgdl_per_u` |
| BgTargetLow / High / Target (Range always empty) | target range | mmol/L | `target_low_mgdl`, `target_high_mgdl`, `target_mgdl` |
| RecommendedCarb / Correction / Net, InsulinOnBoard | units | units | `rec_carb_u`, `rec_correction_u`, `rec_net_u`, `iob_u` |
| ParentHDeviceBolusID | link to HDeviceBolus | 309,442 of 309,507 rows link | `delivered_u` (normal + extended units of that bolus) |

G4 software version: the ReadMe files never state it. The only device text is the inventory label "G4 Platinum Receiver"; upload models are G4Receiver (3,674 uploads), G4ShareReceiver (25), G5MobileReceiver (1). guess: the trial paper (Aleppo et al., Diabetes Care 2017) names the G4 Platinum with Software 505; confirm from the paper before quoting.

## 6. Refactor check (old scripts vs cache-based scripts, same machine, same day)

| File | Values compared | Identical | Moved in the last printed digit | Why |
|---|---|---|---|---|
| summary_stats.json | 946 | 932 | 14 (counts by 1, percentages by 0.01) | 1 calibration pair and 5 meter pairs now match the other copy of a duplicate CGM timestamp. |
| simulation_stats.json | 165 | 133 | 31 (counts by at most 10 of about 1 million) + runtime | 12 in-window duplicates (3 people) where the old code kept the copy an unstable sort put first; the cache keeps the lowest RecID. |
| figures | 12 | 01-07, 10 | 08, 09, 11, 12 | Sampled scatter dots drawn in a new order; value labels follow the numbers above. |

Old outputs on this machine matched the committed JSON files exactly before the switch. Headline numbers (pairs, MARD, Parkes zones) are unchanged. Neither duplicate copy is more correct; the new rule is deterministic and documented.

2026-10-30 re-check (verified-fingerstick rule, cache 2026-10-30.1, the four v2 scripts switched to the module flags): cache rebuilt, all six scripts re-run (151 s). 29,584 values in the six stats JSON files, 3 CSV files and 28 figures are identical to the run before the change; only runtimes, timestamps and the cache-version string differ. Details: REPRODUCIBILITY.md section 4.

## 7. Known issues and open points

- Shanghai pairs: the fingerstick sits on the nearest 15-min row, so up to 7.5 min of timing slack.
- G4 accuracy depends on its calibrations: calibration pairs test the sensor just before correction; meter pairs include 155,636 calibration fingersticks, and "nearest within 5 min" can match the corrected reading taken just after. Independent meter pairs give MARD 10.8 % against 10.4 % for all meter pairs, and verified pairs (independent AND from the meter log) 13.3 %. Use `verified_pairs()` for the headline; `independent_meter` alone still holds pump entries.
- Clipped values (39 and 401) are kept and flagged; errors at the clip are understated.
- Pre-enrolment rows and post-window BGM rows are kept and flagged; filter on `in_study_window`.
- Clock changes: 1,973 manual time changes on 203 people's devices (1,231 on CGM receivers). When a clock is set back, readings interleave; 27,529 gaps under 4 min on 295 person-days. Rate of change is NaN there; sessions may split or merge; `DexInternalTm` could fix this but is blank for 4 % of rows. Not done.
- The 2 clocks (receiver, meter) drift between visits; meter pairs are less exact in time than calibration pairs.
- 82 in-window duplicate timestamps, 46 with different readings (guess: two devices). Kept the lowest RecID.
- Pump BG rows: 190,329 meter pairs come from pump entries; 64,714 of those repeat a meter reading. Kept in `meter` and `independent_meter` (flagged), excluded from `verified` (section 3b).
- Wizard BG unit is inferred from the data, not stated. ICR and ISF are the pump's settings at that moment.
- One Shanghai file (2029_0) has 92 empty rows without a date; 7 files have odd headers (handled). Sensor model is not confirmed from the paper.
- Installed pandas is 2.3.3; `requirements.txt` pins 3.0.6. Outputs were verified with 2.3.3.

## 8. Pipeline complete?

| Item | Done |
|---|---|
| Participants table (demographics, HbA1c local and lab, devices, comorbidities, coverage) | yes |
| CGM table with window, duplicate, clip flags, sessions, wear day, rate of change, night flag | yes |
| Calibrations, BGM (sources, calibration flag), pump bolus / basal / wizard (mg/dL) | yes |
| Three pairings with error columns, range bins, context columns; independent meter view | yes |
| Shanghai patients, CGM, CBG, files tables with header fixes | yes |
| Parquet cache with version stamp, --rebuild, loads in about 1-2 s | yes |
| Old scripts refactored, outputs compared and explained | yes |
| Clock-change correction using the internal clock | no |
| Removing pump BG entries (including copies of meter readings) from the headline pairs | yes (2026-10-30): `is_verified_fingerstick` flag and `verified_pairs()`; `meter` / `independent_meter` keep them, flagged |
| Verified-fingerstick rule in the module, four v2 scripts switched to it, all six scripts re-run and compared | yes (2026-10-30), see section 6 |
| Shanghai sensor model confirmed from the paper | no |
