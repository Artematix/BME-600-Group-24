# Sensor lag and the drivers of CGM error (2026-10-30)

Script: `analysis/error_drivers.py`. Numbers: `analysis/error_drivers_stats.json`. Figures 17-20 in `analysis/figures/`.

Terms. CGM = continuous glucose monitor (skin sensor, a reading every 5 min). Fingerstick = blood-drop meter reading, treated as the truth. Pair = one CGM reading matched to one fingerstick. Bias = average of (CGM minus fingerstick); minus means the sensor reads low. MARD = average percent error; lower is better. ARD = the percent error of one pair. Lag = the sensor trails blood glucose by some minutes. Lag correction = compare the fingerstick with the CGM reading taken T minutes later. Range bins use the average of CGM and fingerstick (see section 8). CI = 95 % confidence interval, from a bootstrap that resamples participants (1,000 draws, fixed seed). "By average" = pairs grouped by the mean of the two readings.

## 1. The answer to the primary uncertainty

The low-glucose bias is real. It does not come from lag or from calibration fingersticks. On fingerstick pairs that were not used for calibration, and after the best lag correction (CGM reading 5 min after the fingerstick), the Dexcom G4 reads 6.5 % low below 54 mg/dL (CI 5.1 to 7.9) and 4.1 % low at 54-69 mg/dL (CI 3.2 to 4.9). Lag correction makes the low-range bias slightly larger, not smaller. The same holds in the CGM+BGM arm after randomisation (6.5 % and 4.8 % low).

| Average of CGM and fingerstick (mg/dL) | Pairs | Bias, as paired (T = 0) | Bias, lag-corrected (T = 5 min) | MARD, as paired | MARD, lag-corrected |
|---|---|---|---|---|---|
| <54 | 2,133 | -5.1 % (-6.7 to -3.6) | -6.5 % (-7.9 to -5.1) | 19.6 % | 18.2 % |
| 54-69 | 7,816 | -2.8 % (-3.7 to -1.7) | -4.1 % (-4.9 to -3.2) | 16.8 % | 15.5 % |
| 70-180 | 98,510 | -1.1 % (-1.7 to -0.5) | -1.7 % (-2.2 to -1.1) | 14.1 % | 13.1 % |
| 181-250 | 40,172 | -1.2 % (-1.6 to -0.8) | -1.3 % (-1.7 to -0.9) | 11.4 % | 10.6 % |
| >250 | 19,216 | -1.1 % (-1.5 to -0.7) | -1.4 % (-1.8 to -1.0) | 10.2 % | 9.5 % |
| All | 167,847 | -1.3 % (-1.7 to -0.9) | -1.7 % (-2.1 to -1.3) | 13.2 % | 12.2 % |

Same pairs in both columns (pairs with a CGM reading 5 min later). In mg/dL: below 54, -4.1 before and -4.6 after; 54-69, -3.3 before and -3.9 after. Figure 18 shows this table.

Why the bias grows after correction: in the low range, many fingersticks happen while glucose is falling. A lagging sensor then reads too HIGH (it still shows the older, higher value). That hid part of the true low reading. Section 3 shows it: below 54, fast-falling pairs go from +13 % to -5 % after correction, while stable pairs stay at -7 %.

The same bias at every promised offset (bias by average, low ranges only):

| Offset T | 0 min | 5 min | 10 min | 15 min | 7 min (interpolated) |
|---|---|---|---|---|---|
| <54 | -5.2 % | -6.5 % | -6.7 % | -5.3 % | -6.2 % |
| 54-69 | -2.7 % | -4.1 % | -4.1 % | -1.9 % | -4.2 % |

Every CI is below zero (JSON `lag_correction.offsets`).

## 2. Which pairs: a reference-quality problem found on the way

- Planned set ("Set B"): independent meter pairs, all participants, in-window days. 306,853 pairs.
- Problem: 137,863 of those pairs come from BG values stored by the insulin pump, not from the study meters. A real fingerstick equals the CGM reading by chance in about 2 % of pairs. Pump values typed by the patient in the CGM-only arm after randomisation equal the CGM reading in 35 % of pairs, and have MARD 4.9 %. They are CGM values typed into the pump's dose calculator, not fingersticks. (The trial asked that arm to dose from the CGM.) Pump values in the other arm and in run-in match exactly 9-10 % of the time, so they are partly contaminated too.

| Arm, phase | Source | Pairs | MARD | CGM equals reference |
|---|---|---|---|---|
| CGM-only, randomised | meter | 104,195 | 13.1 % | 2.2 % |
| CGM-only, randomised | pump | 82,136 | 4.9 % | 35.1 % |
| CGM-only, run-in | meter / pump | 21,540 / 18,948 | 12.9 % / 11.2 % | 2.3 % / 9.4 % |
| CGM+BGM, randomised | meter / pump | 33,467 / 28,529 | 13.8 % / 10.5 % | 2.2 % / 8.7 % |
| CGM+BGM, run-in | meter / pump | 9,788 / 8,250 | 13.6 % / 10.6 % | 2.0 % / 10.3 % |

- Decision in this script: keep meter rows only. Analysis set = 168,990 independent in-window pairs, 226 participants. MARD 13.3 % (CI 12.7 to 13.9) against 10.6 % for Set B. Set B numbers are kept in the JSON for comparison.
- Effect on lag: with pump rows, the best shift is 2 min; pump rows alone give -2 min (the typed value is the CGM value seen a moment earlier). Meter rows give 5-7 min. The pump rows hide the lag.
- Other scripts that use Set B should drop pump rows (`source == "pump"`), or at least the CGM-only-arm rows after randomisation.

## 3. Lag (figure 17)

Method. Each fingerstick was re-paired with the CGM reading nearest to (fingerstick time + T), T = -5, 0, 5, 10, 15, 20 min, within 5 min. T = -5 is a sanity check and should be worse. A finer scan used the straight line between the two readings around (fingerstick time + T), 1-min steps from -10 to 20. Only pairs with a value at every T are used (163,174 and 152,072 pairs). Re-pairing at T = 0 gives exactly the cached pairs.

| T (min) | -5 | 0 | 5 | 10 | 15 | 20 |
|---|---|---|---|---|---|---|
| MARD, nearest reading | 14.5 % | 13.2 % | 12.2 % | 12.3 % | 12.9 % | 14.1 % |

- Best shift: 5 min on real readings (98 % of bootstrap draws). 7 min on the interpolated trace (CI 7 to 7; MARD 13.1 % at 0 to 12.2 % at 7).
- Per participant (interpolated): median 7 min, IQR 5 to 9, range -10 to 17. On real readings: 121 people best at 5 min, 88 at 10, 9 at 15, 8 at 0 or less.
- The same 7 min in run-in, in the CGM-only arm, and in the CGM+BGM arm after randomisation. Check set (CGM+BGM arm, randomised, 33,214 pairs, 77 people): best 5 min, MARD 13.7 % to 12.9 %.
- By trend: best shift 6-8 min in every bin. The gain is large only when glucose moves: fast falling 17.5 % to 12.0 %, fast rising 17.4 % to 12.8 %, stable 12.3 % to 12.0 %.
- This matches published whole-sensor delays of 5-10 min for sensors of that time. The patient sees the unshifted value, so headline accuracy stays unshifted; the corrected numbers are a check.

## 4. Rate of change (figure 19)

ROC = rate of change of the CGM trace at the fingerstick time, mg/dL per minute, from the cache (central difference; missing at gaps). 159,633 pairs with a 5-min-later reading and a ROC value.

| Trend (mg/dL per min) | Pairs | Bias, as paired | Bias, lag-corrected | MARD, as paired | MARD, lag-corrected |
|---|---|---|---|---|---|
| Falling fast (< -2) | 6,974 | +12.7 % (11.6 to 13.9) | +0.7 % (-0.2 to 1.7) | 18.3 % | 12.5 % |
| Falling (-2 to -1) | 16,756 | +5.0 % (4.5 to 5.6) | -0.7 % (-1.2 to -0.2) | 13.1 % | 12.0 % |
| Stable (-1 to 1) | 112,609 | -1.8 % (-2.2 to -1.4) | -2.3 % (-2.7 to -1.8) | 12.3 % | 12.1 % |
| Rising (1 to 2) | 14,094 | -5.9 % (-6.6 to -5.1) | -1.2 % (-1.9 to -0.4) | 15.3 % | 13.5 % |
| Rising fast (> 2) | 9,200 | -9.4 % (-10.5 to -8.2) | +0.4 % (-0.6 to 1.6) | 17.9 % | 12.9 % |

- As paired, the sign of the bias follows the trend: falling = reads high, rising = reads low. That is the lag signature. The 5-min shift removes almost all of it. MARD in the fast bins drops by 5-6 points to about the stable level.
- Range x trend (JSON `roc.range_x_roc_*`): in 54-69, fast falling +18.9 % to -1.4 %, rising -17.1 % to -1.1 %, stable -4.2 % to -4.7 %. In 70-180, fast falling +14.9 % to +1.6 %, fast rising -11.5 % to +0.8 %. Below 54, the rising bins have under 60 pairs (rising fast: 13 pairs, 9 people): not testable.
- So after lag correction, the remaining low-range bias sits in the STABLE pairs, which are the large majority.

## 5. Wear day (figure 20, left and middle)

- Sessions are inferred from gaps of 115 min or more (no sensor-start marker exists). Only sessions "confirmed" by a calibration entered in the 30 min before the first reading are used: unconfirmed sessions are mostly signal-loss fragments, where wear day restarts at 1 by mistake. Kept 150,690 pairs (wear days 1-7); dropped 17,576 unconfirmed and 724 beyond day 7.

| Wear day | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| Pairs | 29,508 | 25,843 | 23,234 | 21,538 | 19,702 | 17,722 | 13,143 |
| MARD | 15.2 % (14.6 to 15.9) | 13.2 % | 13.2 % | 12.7 % | 12.2 % | 12.1 % | 11.8 % (11.2 to 12.5) |
| Bias | -1.1 % | -1.1 % | -1.9 % | -2.7 % | -0.9 % | -0.5 % | -0.6 % |

- Day 1 is worst by about 2 points. Per person: day-1 MARD minus days-2-7 MARD has median +2.2 points (IQR 0.9 to 3.4); 86 % of people are worse on day 1. Then a slow improvement to day 7.
- Day 1 by hours since the first reading (after the 2-h warm-up): 0-6 h 15.2 % (14.4 to 16.0), 6-12 h 16.2 % (15.4 to 17.0), 12-24 h 14.8 % (14.1 to 15.6). The first hours are not clearly the worst; the whole first day is.
- Exploratory, not pre-specified: the low-range bias is concentrated on day 1. Below 54: day 1 -12.3 % (CI -14.5 to -10.1; 513 pairs, 146 people), days 2-6 -2.3 % (-4.1 to -0.6), day 7 -0.6 % (-4.6 to 3.2). At 54-69: day 1 -9.0 % (-10.8 to -7.2), days 2-6 -1.1 % (-2.2 to 0.0), day 7 +0.4 % (-1.1 to 2.0). guess: the new sensor reads low until the first day's calibrations settle it.
- Using all sessions (no confirmation filter) gives the same curve (15.2 to 11.9 %).

## 6. Time of day (figure 20, right)

- Night = 00:00 to 06:00 on the meter clock. 14,430 night pairs, 154,560 day pairs.
- Pooled MARD: night 14.3 % (13.2 to 15.6) vs day 13.2 % (12.6 to 13.7). Bias the same (-1.3 % both).
- Per person: night MARD minus day MARD has median -0.2 points (IQR -2.1 to 2.3); 47 % of people are worse at night. So there is no general night shift; the pooled gap comes from a small number of large errors.
- Confound check inside the 70-180, stable subset (4,777 night pairs, 214 people): night 16.5 % (14.1 to 19.1) vs day 12.7 % (12.0 to 13.3). Per person: median -0.4 points, 46 % worse at night. Large errors (over 40 %) are twice as common at night, in both directions: CGM too low 3.0 % vs 1.5 %, CGM too high 4.5 % vs 2.2 %.
- Night pairs are more often low (9.4 % below 70 by average, vs 5.6 % in the day) and slightly more often stable. guess: night fingersticks are mostly taken because an alarm or symptoms made the patient check, so they over-sample moments when the sensor is wrong. Compression lows (lying on the sensor) would give only CGM-too-low errors; we see both directions.
- By 3-hour block, MARD runs from 12.6 % (21-24 h) to 14.7 % (00-03 h). The 06-09 h block has the lowest bias, -3.9 % (guess: the morning fingerstick before breakfast, after the overnight low-glucose period).

## 7. One mixed-effects model

A mixed-effects model is a regression that knows which pairs belong to the same person; each person gets their own baseline (random intercept). Outcome = ARD (%) of each pair as paired; fixed effects = range (by average), trend bin, wear day group (1, 2-6, 7), night, study arm. Fitted on all 143,051 pairs that have every covariate (confirmed sessions, days 1-7, ROC available), 226 people; restricted maximum likelihood, converged in 1 s.

| Effect (vs the baseline: 70-180 mg/dL, stable, wear day 2-6, daytime, CGM-only arm) | Points of ARD added (95 % CI) |
|---|---|
| Baseline ARD | 12.7 (12.0 to 13.4) |
| Range <54 | +5.8 (4.9 to 6.6) |
| Range 54-69 | +3.0 (2.5 to 3.4) |
| Range 181-250 / >250 | -3.2 (-3.4 to -2.9) / -4.6 (-4.9 to -4.2) |
| Falling fast / falling | +6.3 (5.9 to 6.8) / +0.6 (0.3 to 0.9) |
| Rising / rising fast | +3.5 (3.1 to 3.8) / +6.1 (5.7 to 6.5) |
| Wear day 1 / wear day 7 | +2.3 (2.1 to 2.6) / -0.9 (-1.2 to -0.6) |
| Night | +0.9 (0.6 to 1.3) |
| CGM+BGM arm | +0.6 (-0.7 to 1.9), not different from zero |

Between-person spread of the baseline: SD 4.5 points. Pair-to-pair spread: SD 17.2 points. Plain reading: fast-moving glucose and the low range each add about 6 points of error; day 1 adds about 2; night about 1; the arm does not matter once the other factors are in.

## 8. Regression to the mean: why we bin by the average

Both devices have noise. Pick pairs where the fingerstick is very low and you mostly pick fingerstick-noise lows; the CGM then looks too high. Pick by low CGM and the reverse happens. Binning by the average of the two is fair to both.

| Range | Binned by fingerstick | Binned by CGM | Binned by average | By average, lag-corrected |
|---|---|---|---|---|
| <54 | +29.8 % (25.2 to 35.8), 2,174 pairs | -22.5 % (-23.8 to -21.2), 3,536 | -5.2 % (-6.8 to -3.7), 2,156 | -6.5 % (-7.9 to -5.1), 2,365 |
| 54-69 | +10.1 % (7.7 to 12.7), 7,930 | -9.3 % (-10.2 to -8.4), 8,188 | -2.7 % (-3.6 to -1.7), 7,866 | -4.1 % (-4.9 to -3.2), 7,961 |
| 70-180 | -0.7 % (-1.3 to -0.1), 96,311 | -2.5 % (-2.9 to -2.1), 99,296 | -1.1 % (-1.7 to -0.5), 99,161 | -1.7 % (-2.2 to -1.1), 98,117 |

Same sensor, same pairs; the sign below 70 flips with the binning axis. Only the average column is a sensor fact.

## 9. Shanghai (Abbott flash sensor, 15-min readings)

- 4,012 pairs, 98 patients. The fingerstick sits on the nearest 15-min row, so timing is only known to 7.5 min. Fingerstick equals CGM in 2.8 % of pairs: no typed-CGM problem here.
- Lag at 15-min steps: MARD 13.8 % at -15 min, 13.9 % at 0, 15.3 % at +15, 17.9 % at +30 (4,000 complete pairs). -15 and 0 are equal within the CI (12.0 to 15.8 and 12.0 to 16.1). A lag under 15 min cannot be measured here.
- By trend: stable 3,640 pairs, bias -7.9 % (-11.3 to -4.5), MARD 13.8 %. Falling 230 pairs (65 patients): -5.9 %, 13.1 %. Rising 101 pairs (46 patients): -0.7 %, 16.7 %. Falling fast 15 pairs and rising fast 18 pairs: too few to read.
- The Libre reads 6-8 % low at every trend; T1DM patients (10 people, 750 pairs) -13 %, T2DM (88 people) -6 %.

## 10. Limits

- Reference = a home meter, not lab blood. MARD includes meter error (about 3-5 %).
- Timing: meter and receiver clocks are separate. Calibration entries (123,469) sit a median 0.1 min after the matching meter reading; 85 % within 2 min, 98 % within 5 min (this includes the time to type the value in). Pairs are matched within 5 min (quartiles -77 to +78 s). So the lag estimate has about 1-2 min of slack.
- Clock changes (1,973 manual changes) can interleave readings; the cache sets ROC to missing there, and interpolation across such points is wrong for a few hundred person-days. Not corrected.
- Sessions are inferred from gaps, not from a sensor ID. Wear-day results rely on the confirmed-session filter.
- Lag correction uses the nearest real reading 5 min later; the interpolated 7-min version smooths noise a little, which lowers MARD by itself (12.1 % vs 12.2 %).
- Fingersticks are not random samples; night and low-range pairs over-sample moments when the patient doubted the sensor.
- The shared range bins are left-closed: exactly 180 and 250 fall in the upper bin. Same rule in every script.
- Pump-sourced BG rows were dropped here but are still in the cache and in "Set B" results of other scripts.

## 11. How to run

- `python analysis/error_drivers.py "Uncommitted Data/Raw Data Dump" analysis` from the repo root. Optional third argument: cache folder.
- Needs the parquet cache from `analysis/preprocess.py` (built on first use, about 40 s). Runtime about 25 s on the cached tables.
- Seed 20261027 for the bootstrap. Figures: 17 lag scan, 18 low-range bias with and without lag correction, 19 trend bins, 20 wear day / first hours / night.
