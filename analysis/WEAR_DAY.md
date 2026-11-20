# Wear day 1: bad sensors discarded early, or every sensor settling in? (2026-11-06)

Script: `analysis/wear_day.py`. Numbers: `analysis/wear_day_stats.json`. Figures 33 and 34 in `analysis/figures/`.

Terms. CGM = continuous glucose monitor (skin sensor, a reading every 5 min). Fingerstick = blood-drop meter reading, treated as the truth. Pair = one CGM reading matched to one fingerstick. Verified pair = the fingerstick comes from the meter's own log and was not used to calibrate the sensor (the headline set, 168,990 pairs, 226 people). MARD = average percent error of the sensor; lower is better. Bias = average of (CGM minus fingerstick) in percent; minus means the sensor reads low. Session = the days one sensor was worn (inferred from gaps in the readings, section 2). Wear day = day 1 is the first 24 h after the sensor's first reading. Calibration = a fingerstick typed into the receiver to correct the sensor; the G4 needs two after its 2-hour warm-up, then one every 12 hours. Bootstrap = the 226 people are re-drawn with replacement 1,000 times and the statistic is recomputed each time. CI = the 95 % range of those 1,000 values. Every statistic in this memo uses the same 1,000 draws, so a difference between two groups has its own CI. "Points" = points of MARD (percentage points).

The question. `ERROR_DRIVERS.md` section 5 found the sensor worst on wear day 1 (MARD 15.2 % vs 11.8 % on day 7). Two stories could explain that. (a) Selection: some sensors are bad from the start, get pulled early and replaced, so day 1 holds more bad sensors than later days. (b) Settling: every sensor is worse on its first day and improves afterwards. This memo separates them.

## 1. Summary

- The day-1 effect is almost all settling. The same sensors that lasted 7 days read 15.1 % MARD on day 1, 13.1 % on day 2 and 12.0 % on days 5 to 7.
- Sensors pulled on day 1 do read worse (19.4 % vs 15.1 %, +4.3 points, CI 2.2 to 6.6). But they are 7 % of sessions and 3.5 % of day-1 pairs. Dropping every session that did not reach day 7 moves day-1 MARD from 15.3 % to 15.1 %.
- Split of the 3.3-point day-1 excess over day 7: settling 3.0 points (92 %, CI 85 to 100), selection 0.25 points (8 %, CI 0.5 to 15).
- Settling is fast, then slow. The extra error halves about every 24 h (time constant 34 h, CI 25 to 48). Two thirds of it is gone after day 1, it is within half a point of the final level by about day 3, and flat from day 5.
- Day 1 is noisier, not biased: bias -0.9 % vs -0.5 % on day 7, but errors over 20 % are 1.5 times more common, in both directions. Only in the low range (< 70 mg/dL) is day 1 biased: a new sensor reads about 10 % low there, fading from -14 % in its first 6 h to -7 % at 18 to 24 h, and gone by day 2.
- Calibration timing does not explain it. Day 1 is worse at every time since the last calibration, and the sensor's error just before each calibration is 19.3 % on day 1 vs 11.9 % on day 7.

## 2. What a session is here

- The cache has no sensor ID. It starts a new "raw session" at every gap of 115 min or more between readings (`preprocess.py`). A session is "confirmed" when a calibration was entered in the 30 min before its first reading; the G4 shows no readings until the two start-up calibrations are in, so a real start is almost always confirmed (98 % of 7-day sessions).
- Problem with raw sessions: a signal gap of 2 h or more inside one wear also starts a new raw session. The second piece has no start-up calibration (unconfirmed) and its wear day restarts at 1. `ERROR_DRIVERS.md` dropped those pieces. For this memo that is not enough: the first piece would then look like a sensor that ended early.
- Fix used here: an unconfirmed piece is glued back onto the session it follows (same sensor after a signal gap), unless the glued session would run past 170 h (the G4 stops itself at 7 days = 168 h from the sensor start, which leaves about 166 h of readings). Wear day is then recomputed from the glued session's first reading with the cache's own rule. On the confirmed pieces the recomputed wear day equals the cache value in 100 % of pairs.

| Count | Value |
|---|---|
| Raw sessions touching the study window | 10,812 (8,514 confirmed, 2,298 unconfirmed) |
| Unconfirmed pieces glued onto the session before | 2,102 (median gap before them 2.5 h; 84 % under 6 h) |
| Unconfirmed pieces left alone (no session to glue to, or over 170 h) | 196, forming 199 unconfirmed sessions: excluded (3,637 pairs) |
| Glued, confirmed sessions | 8,521 (226 people; median 38 sessions per person) |
| Ended before day 3 | 967 (11.4 %) |
| Reached day 7 | 5,647 (66.3 %); 4,050 of them are 164 to 166 h long (7 days minus the 2-h warm-up) |
| Beyond day 7 | 53 (0.6 %): impossible for a G4, so clock changes or wrong glueing. Excluded (2,155 pairs) |
| Verified pairs kept | 163,198 of 168,990 (13,876 of them on glued pieces); 132,542 in 5,515 sessions that reached day 7 |

By how long the session lasted (last wear day reached):

| Session ended | Sessions | Share | People | Median length (h) | Pieces per session | Next session starts within 6 h | Day-1 pairs | Share of all day-1 pairs |
|---|---|---|---|---|---|---|---|---|
| On day 1 | 559 | 6.6 % | 183 | 10.5 (IQR 5.1 to 17.8) | 1.08 | 66 % | 1,053 | 3.5 % |
| Days 2 to 3 | 778 | 9.1 % | 206 | 46.9 (36.3 to 61.0) | 1.19 | 59 % | 2,781 | 9.3 % |
| Days 4 to 6 | 1,484 | 17.4 % | 224 | 114.9 (93.7 to 131.1) | 1.28 | 62 % | 5,363 | 18.0 % |
| Reached day 7 | 5,647 | 66.3 % | 226 | 165.2 (163.8 to 165.7) | 1.26 | 83 % | 20,584 | 69.1 % |
| Beyond day 7 (artefact) | 53 | 0.6 % | 45 | 233 | 1.15 | 92 % | excluded | - |

- There is no tail past 7 days, and there cannot be one: every start (new sensor or a restart of the same sensor) forces a 2-h warm-up and two calibrations, so a restart begins a new session. The data cannot tell a restart from a replacement.
- Replacement is quick. The next session starts a median 2.9 h (7-day sessions) to 3.8 h (ended on day 1) after the last reading, which is the warm-up time. So sessions that ended early were mostly replaced right away, not followed by a break from the CGM.
- Limits of inferred sessions: a real start whose calibration was entered more than 30 min before the first reading looks unconfirmed (1.7 % of 7-day raw sessions) and is then glued to the previous session by mistake, which makes its wear day too high. Clock changes (1,973 in the data) can split or merge sessions. Without glueing (the raw sessions, exactly the `ERROR_DRIVERS.md` filter) the selection share below is 12 % (CI 2 to 20) instead of 8 % (`sensitivity_raw_sessions` in the JSON).

## 3. Selection test: day-1 error by how long the session lasted (figure 33, left)

| Session ended | Day-1 pairs | Sessions | Day-1 MARD | Difference vs 7-day sessions | Day-1 bias | Day-1 MARD, first 12 h only |
|---|---|---|---|---|---|---|
| On day 1 | 1,053 | 372 | 19.4 % (17.1 to 21.9) | +4.3 (2.2 to 6.6) | -2.7 % (-5.0 to -0.4) | 18.8 % (16.5 to 21.4) |
| Days 2 to 3 | 2,781 | 684 | 15.7 % (14.7 to 16.9) | +0.6 (-0.4 to 1.8) | -3.1 % (-4.3 to -1.8) | 16.2 % (14.7 to 17.8) |
| Days 4 to 6 | 5,363 | 1,303 | 15.3 % (14.3 to 16.3) | +0.2 (-0.8 to 1.2) | -1.0 % (-1.9 to 0.0) | 14.9 % (13.8 to 16.0) |
| Reached day 7 | 20,584 | 4,947 | 15.1 % (14.4 to 15.8) | - | -0.9 % (-1.5 to -0.3) | 15.6 % (14.9 to 16.4) |
| All sessions | 29,781 | 7,306 | 15.3 % (14.7 to 16.1) | | -1.2 % (-1.7 to -0.6) | |

- Only the sensors pulled on day 1 are worse. Sensors that lasted 2 to 6 days read the same on day 1 as sensors that lasted 7 days.
- The "first 12 h only" column makes the comparison fair in time (a sensor pulled after 10 h has only early-hours pairs, and the first hours are the worst for every sensor). The gap stays: +3.2 points (CI 0.8 to 5.6).
- Within person: 211 people had day-1 pairs on both a session that ended early (days 1 to 6) and a 7-day session. Their own difference has median -0.1 points (CI -1.0 to 0.7); 49 % were worse on the early-ended ones. For sessions that ended on day 1 only: 106 people, median +1.6 points (CI -0.9 to 3.7), mean +4.2, 58 % worse (CI 48 to 67). Same direction as the pooled +4.3, too few pairs per person to be sure.
- These sensors were checked more often: 2.8 fingersticks in a median 10.5 h of wear, against 4.2 per 24 h on 7-day sensors. guess: people checked a sensor that looked wrong, then pulled it.

How much of the day-1 excess comes from the short-lived sessions:

| Quantity | Points of MARD | CI |
|---|---|---|
| Day-1 MARD, all sessions | 15.31 | 14.66 to 16.05 |
| Day-1 MARD, 7-day sessions only | 15.06 | 14.37 to 15.82 |
| Day-7 MARD | 12.04 | 11.42 to 12.71 |
| Day-1 excess over day 7, all sessions | 3.27 | 2.83 to 3.72 |
| Of which: from sessions that never reached day 7 (selection) | 0.25 = 8 % | 0.01 to 0.50 (0.5 to 15 %) |
| Of which: inside the 7-day sensors (settling) | 3.02 = 92 % | 2.58 to 3.45 (85 to 100 %) |

The day-1 vs day-7 gap recomputed on sessions that reached day 7 only: 3.02 points (CI 2.58 to 3.45), against 3.27 with every session.

## 4. Settling test: the same sensors over their 7 days (figure 33, right)

Pairs in sessions that reached day 7 (132,542 pairs, 5,515 sessions, 226 people). "Final level" = pooled MARD over hours 96 to 168 (days 5 to 7): 12.01 % (CI 11.41 to 12.67).

| Wear day | Pairs | MARD | Extra over the final level | Drop to the next day |
|---|---|---|---|---|
| 1 | 20,584 | 15.06 % (14.37 to 15.82) | +3.05 (2.67 to 3.41) | 1.99 (1.59 to 2.41) |
| 2 | 19,733 | 13.07 % (12.45 to 13.79) | +1.06 (0.69 to 1.43) | 0.07 (-0.33 to 0.46) |
| 3 | 19,272 | 13.01 % (12.28 to 13.83) | +1.00 (0.67 to 1.33) | 0.51 (0.14 to 0.89) |
| 4 | 19,289 | 12.50 % (11.91 to 13.25) | +0.49 (0.17 to 0.81) | 0.48 (0.12 to 0.83) |
| 5 | 19,190 | 12.02 % (11.40 to 12.70) | +0.01 (-0.20 to 0.22) | |
| 6 | 19,170 | 11.98 % (11.30 to 12.72) | -0.03 (-0.27 to 0.22) | |
| 7 | 15,304 | 12.04 % (11.42 to 12.71) | +0.03 (-0.21 to 0.27) | |

By 12-hour block since the first reading (MARD, %):

| Hours | 0-12 | 12-24 | 24-36 | 36-48 | 48-60 | 60-72 | 72-84 |
|---|---|---|---|---|---|---|---|
| MARD | 15.6 | 14.5 | 13.3 | 12.8 | 13.1 | 13.0 | 12.5 |

| Hours | 84-96 | 96-108 | 108-120 | 120-132 | 132-144 | 144-156 | 156-168 |
|---|---|---|---|---|---|---|---|
| MARD | 12.5 | 12.1 | 12.0 | 12.0 | 12.0 | 12.2 | 11.9 |

The 6-hour version (28 bins, with CIs and bias) is in the JSON (`settling.by_6h_bin`) and drawn in figure 33.

Where the curve flattens (the settling time):

| Method | Result |
|---|---|
| First 12-h block after which the curve stays within 1 point of the final level | 60 h (CI 36 to 72) |
| Same, within 0.5 point | 72 h (CI 72 to 156) |
| Fit: MARD = final level + extra x exp(-hours / time constant), 6-h bins | final level 12.0; extra at start 4.1 points (3.6 to 4.8); time constant 34 h (25 to 48) |
| Extra error from the fit at 0 / 24 / 48 / 72 / 96 h | 4.1 / 2.0 / 1.0 / 0.5 / 0.25 points |
| Hour when the extra error falls below 0.5 point (fit) | 72 h (CI 53 to 100) |
| First 12 h vs second 12 h of day 1 | 15.6 % vs 14.5 %: drop 1.1 (0.4 to 1.8) |

Plain reading: the extra error halves about every 24 h. Two thirds of it is gone after day 1. The rest fades over days 2 to 4. From day 5 the sensor is at its final level.

Same sensor, its own days compared (sessions with at least 3 pairs on each of the two days):

| Comparison | Sessions | People | Median difference | Mean | Share worse on the earlier day |
|---|---|---|---|---|---|
| Day 1 minus day 2 | 2,974 | 206 | +1.35 points (1.01 to 1.67) | +2.05 | 58 % (56 to 60) |
| Day 1 minus day 7 | 2,355 | 202 | +2.85 points (2.40 to 3.27) | +3.18 | 64 % (62 to 66) |
| Day 2 minus day 7 | 2,374 | 199 | +1.21 points (0.91 to 1.48) | +1.07 | 58 % (55 to 60) |

One sensor-day has only a few pairs, so single differences are noisy (IQR for day 1 minus day 2: -3.3 to +6.7). The mean of the per-sensor differences (2.05) matches the pooled drop (1.99); the median is smaller because the spread is skewed.

Within person (each person's own day-1 MARD minus their own later-day MARD, on 7-day sessions, at least 5 pairs on each day):

| Comparison | People | Median | IQR | Share worse on day 1 |
|---|---|---|---|---|
| Day 1 minus day 7 | 222 | +2.93 points (2.40 to 3.38) | 0.8 to 4.8 | 81 % (76 to 86) |
| Day 1 minus day 2 | 221 | +1.76 points (1.22 to 2.19) | 0.1 to 3.9 | 77 % (72 to 83) |

This is not driven by who wears sensors longer: it holds inside the 7-day sessions, inside the same sensor, and inside the same person.

## 5. Direction: biased, or just noisier?

7-day sessions. "Over 20 % low / high" = share of pairs where the CGM reads more than 20 % below / above the meter.

| Wear day | Bias (%) | Bias (mg/dL) | Spread of the % error (SD) | Over 20 % low | Over 20 % high |
|---|---|---|---|---|---|
| 1 | -0.9 (-1.5 to -0.3) | -3.6 | 23.9 | 13.3 % | 10.2 % |
| 2 | -0.7 (-1.3 to -0.1) | -4.0 | 22.1 | 9.9 % | 8.1 % |
| 3 | -1.9 (-2.5 to -1.3) | -6.3 | 22.3 | 10.8 % | 6.9 % |
| 4 | -2.6 (-3.1 to -2.1) | -7.0 | 20.0 | 10.6 % | 6.1 % |
| 5 | -0.9 (-1.4 to -0.3) | -4.2 | 20.7 | 8.4 % | 6.7 % |
| 6 | -0.6 (-1.2 to 0.0) | -3.5 | 20.9 | 8.3 % | 6.6 % |
| 7 | -0.5 (-1.0 to 0.1) | -3.6 | 21.3 | 8.3 % | 7.0 % |

Day 1 minus day 7: bias -0.45 points (CI -1.12 to 0.13, no difference); spread +2.6 (CI -0.2 to 4.8, borderline); over 20 % low +4.9 (4.1 to 5.8); over 20 % high +3.2 (2.5 to 3.9).

- Overall, day 1 is noisier, not biased. Large errors are more common in both directions, a little more often on the low side.
- The most negative bias sits on days 3 and 4 (-1.9 and -2.6 %), as in `ERROR_DRIVERS.md`. Not part of this question.
- The low range is the exception: there day 1 is biased low (section 7).

## 6. Calibration check (figure 34)

- Day 1 by 6-h block (7-day sessions): 15.5 % (0-6 h), 15.7 % (6-12 h), 14.7 % (12-18 h), 14.4 % (18-24 h). The first 12 h (only the two start-up calibrations entered so far) are the worst, but only by 1.1 points (CI 0.4 to 1.8) over the second 12 h. The whole day sits 2.4 to 3.5 points above the final level.
- Calibrations entered per session-day: 4.4 on day 1 (two start-up plus two 12-hour ones), 2.4 to 2.5 on days 2 to 6, 1.85 on day 7 (a 22-h day). 104,350 entries in 5,647 sessions.

MARD by hours since the last calibration, 7-day sessions:

| Hours since the last calibration | Day 1 | Days 2 to 7 | Day 1 minus days 2 to 7 |
|---|---|---|---|
| 0 to 1 | 11.4 % (10.2 to 12.8) | 10.3 % (9.5 to 11.4) | +1.1 (0.4 to 1.8) |
| 1 to 3 | 16.1 % (15.0 to 17.2) | 13.3 % (12.4 to 14.5) | +2.7 (2.0 to 3.5) |
| 3 to 6 | 15.3 % (14.5 to 16.1) | 12.2 % (11.6 to 13.0) | +3.1 (2.4 to 3.8) |
| 6 to 12 | 15.7 % (15.0 to 16.4) | 12.5 % (12.0 to 13.0) | +3.2 (2.6 to 3.7) |
| 12 to 24 | 18.5 % (16.6 to 21.0) | 13.8 % (13.2 to 14.5) | +4.8 (3.1 to 6.8) |

- A calibration pulls the sensor onto the meter: on every day the error is lowest in the hour after one. Within 1 to 3 h the error is back up (that is the "jump after calibration": the correction decays). On day 1 it comes back faster and further, and the longer since the last calibration, the larger the day-1 gap.
- Error at the moment of calibration (the fingerstick typed in vs the CGM reading just before it, i.e. the raw sensor error the calibration then corrects): day 1 19.3 % (18.6 to 20.2), day 2 13.8 %, day 3 13.1 %, day 4 13.0 %, day 5 11.8 %, day 6 11.6 %, day 7 11.9 %. Day 1 minus day 7: 7.4 points (6.7 to 8.2). This is the clearest settling signal: before any correction, a day-1 sensor is 7 points worse than the same sensor on day 7.
- Verdict for this check: calibration timing does not explain day 1. Day-1 sensors drift away from each calibration faster than they do later.

## 7. Low range (< 70 mg/dL by the average of CGM and meter)

| Set | Wear day | Pairs | Bias | MARD |
|---|---|---|---|---|
| 7-day sessions | 1 | 1,413 | -10.4 % (-12.1 to -8.6) | 20.2 % (19.1 to 21.3) |
| 7-day sessions | 2 to 6 | 5,446 | -1.1 % (-2.3 to 0.0) | 16.7 % (16.1 to 17.4) |
| 7-day sessions | 7 | 914 | 0.0 % (-1.6 to 1.6) | 15.8 % (14.8 to 16.8) |
| Sessions that ended early | 1 | 639 | -9.1 % (-11.7 to -6.6) | 20.8 % (19.2 to 22.8) |
| Sessions that ended early | 2 to 6 | 1,269 | -2.8 % (-4.3 to -1.3) | 17.3 % (16.3 to 18.5) |

- Day-1 bias minus days-2-to-6 bias, 7-day sessions: -9.3 points (CI -11.1 to -7.5). Early-ended minus 7-day on day 1: +1.4 (CI -1.5 to 4.2), no difference. So the low-range day-1 bias is settling, not selection: every new sensor reads about 10 % low in the low range on its first day.
- It fades within the day (7-day sessions, day 1): -14.4 % at 0-6 h, -10.8 % at 6-12 h, -8.6 % at 12-18 h, -6.6 % at 18-24 h.

Missed lows (meter < 70, CGM 70 or more, as a share of meter-low pairs) and false lows (meter 70 or more, CGM < 70, as a share of the rest), 7-day sessions:

| Wear day | Meter-low pairs | Missed lows | False lows |
|---|---|---|---|
| 1 | 1,292 | 28.5 % (24.7 to 32.5) | 4.5 % (4.0 to 5.1) |
| 2 | 1,245 | 31.9 % | 2.9 % |
| 3 | 1,160 | 35.8 % | 2.9 % |
| 4 | 1,118 | 31.9 % | 2.8 % |
| 5 | 1,068 | 33.1 % | 2.3 % |
| 6 | 1,056 | 31.7 % | 2.3 % |
| 7 | 940 | 31.1 % (27.6 to 34.4) | 2.3 % (2.0 to 2.7) |

Day 1 minus day 7: missed lows -2.6 points (CI -7.0 to 1.7, no difference); false lows +2.2 points (CI 1.6 to 2.7). On its first day the sensor errs on the low side, so it does not miss more lows; it shows about twice as many lows that are not there.

## 8. Link to the FDA reports

- `fda-maude/results/text/TEXT_RESULTS.md` section 6: Abbott complaints name wear day 1 in 13.4 % of serious reports (1.9 times the flat 7.1 %) and 34.5 % of the malfunction sample; Dexcom reports show no day-1 excess (7.1 % vs 10 % flat).
- The trial says the day-1 problem of the G4 is universal settling, not a defective subset. But a complaint needs a noticeable error, and day 1 has 1.5 times as many errors over 20 % (23.5 % of pairs vs 15.3 % on day 7) and twice the false lows. So a day-1 cluster of complaints is expected even when no sensor is defective.
- The sensors pulled on day 1 (7 % of sessions, 4 points worse, checked 60 % more often per hour) are the trial's closest match to a day-1 complaint. They are too few to move the average, but they are exactly the sensors a user would report.
- guess: both stories feed the Abbott day-1 excess, and complaint counts cannot split them, because a complaint is filed only when the error was noticed. guess: the part of the G4's settling that comes from user calibrations (section 6) does not transfer to the factory-calibrated Libre 3; the low-range "reads low on day 1" part may, since it looks like the sensor in fresh tissue.
- Dexcom complaints show no day-1 peak although the trial's Dexcom sensor is clearly worst on day 1: complaint timing is not an error rate, as TEXT_RESULTS already says.

## 9. Verdict

- Bad sensors being discarded: about 8 % of the day-1 effect (0.25 of 3.3 points; CI 0.5 to 15 %). The sensors involved (pulled on day 1) read 4.3 points worse than the rest, but they are 7 % of sessions and 3.5 % of day-1 pairs.
- Settling: about 92 % (3.0 of 3.3 points; CI 85 to 100 %). The same sensor reads 2.0 points worse on day 1 than on day 2 and 3.0 points worse than on day 7; 81 % of people show it on their own sensors.
- Settling time: the extra error halves every 24 h; two thirds gone after day 1; within half a point of the final level by about 72 h (CI 53 to 100); flat from day 5.
- Day 1 is noisier, not biased, except in the low range, where a new sensor reads 10 % low and this fades within the day. That is also why day 1 has twice the false lows and no more missed lows.
- Calibration timing is not the cause: day 1 is worse at every time since the last calibration, and the uncorrected sensor is 7 points worse on day 1 than on day 7.
- What the paper should say: "Wear day 1 is the sensor settling in, not a subset of bad sensors. The same sensor reads about 2 points worse on its first day than on its second and 3 points worse than on day 7, and 81 % of people show it. Sensors pulled on the first day are worse (about 4 points) but are only 7 % of sessions, so removing them changes day-1 MARD from 15.3 to 15.1 %. In the low range a new sensor reads about 10 % low on its first day; this fades within the day and is gone by day 2, and it doubles false low readings on day 1. A day-1 cluster of complaints is therefore expected even when no sensor is defective."

## 10. Caveats

- Sessions are inferred, not read from a sensor ID. The glueing rule is a judgement: a missed start-up calibration (1.7 % of real starts) wrongly glues a new sensor to the old one. The raw-session version gives a selection share of 12 % instead of 8 %; the conclusion is the same.
- A restart of the same sensor looks exactly like a replacement, so "7-day sessions" may include sensors in their second week. If anything this dilutes the settling effect.
- The sensor's insertion time is not in the data; wear day 1 starts at the first reading, about 2 h after insertion.
- Fingersticks are not random. Day 1 of 7-day sessions has 3.7 pairs per session, days 2 to 6 have 3.5 (7 % more), and sensors pulled on day 1 were checked 60 % more often per hour. Some of the day-1 excess may be checks made because the sensor looked wrong. This cannot be removed with these data.
- "Settling" here means everything that happens to the same sensor over time: the sensor in the tissue, the receiver's algorithm, and the calibrations piling up. The memo does not split those.
- Same-sensor comparisons need at least 3 pairs on each day, so they use 2,355 to 2,974 of the 5,515 7-day sessions.
- The 53 sessions beyond day 7 (2,155 pairs) are excluded as artefacts; day 7 is a 22-h day; the low-range day-1 blocks have 274 to 452 pairs each.
- The reference is a home meter (3 to 5 % error of its own), as in every memo.

## 11. How to run

- `python analysis/wear_day.py "Uncommitted Data/Raw Data Dump" analysis` from the repo root. Optional third argument: cache folder.
- Needs the parquet cache from `analysis/preprocess.py` (built on first use, about 50 s). Runtime 3.4 s on the cached tables.
- Seed 20261106, 1,000 bootstrap draws of the 226 participants, shared by every statistic. Outputs: `wear_day_stats.json`, figures 33 (selection vs settling) and 34 (calibration timing).
