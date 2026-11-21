# Low detection counted with a time window (2026-11-20)

Script: `analysis/low_detection_window.py`. Every number below comes from `analysis/low_detection_window_stats.json`.

## 1. The question
- Our paper says: 31.4 % of true lows (meter under 70 mg/dL) were not shown as low by the sensor.
- Published clinic studies say the sensor's low alert at 70 mg/dL detects 86 to 91 % of lows. This range is taken from `docs/paper/OUTLINE.md` (point D2 b). It was not re-checked here.
- The two numbers are counted in different ways. Ours compares one fingerstick with one sensor reading. The studies count a low as detected if the sensor was under the threshold at any time in a window around the reference reading (15 minutes before or after; some use 30).
- This memo counts our lows the way the studies do.

## 2. Definitions
- Sensor = continuous glucose monitor (CGM), one reading every 5 minutes. Meter = fingerstick blood glucose meter, the reference here.
- Pair = one meter value with the nearest sensor reading within 5 minutes (the "matched reading").
- True low = a pair with the meter under 70 mg/dL (or under 54). Not shown = no sensor reading under the sensor threshold (70 or 54) under the rule of the row.
- Rules: the matched reading only; any reading within 15 or 30 minutes before or after the fingerstick; any reading in the 15 minutes before only; any reading in the 15 minutes after only. The ends of a window count. Windows use the full 5-minute sensor trace.
- Sensor low = a pair whose matched reading is under 70. Not confirmed = the meter is 70 or above. Softer check: the meter is 80 or above.
- Signal gap = no sensor reading at all in the window. Such lows are left out of the row. They are never counted as not shown. Their number is in brackets.
- 95 % CI = confidence interval, the range the true value most likely sits in. It comes from a bootstrap: the participants are re-drawn at random 2,000 times (seed 600).
- Per person = the median (quartiles) of each person's own share, for people with at least 10 events in the row. The last number is how many people that is.
- All 226 = the headline pair set: 168,990 pairs, 226 people. Arm = the check set: CGM+BGM arm, randomised phase, 33,467 pairs, 77 people.

## 3. Results
Rows 1 to 15: share of true lows NOT shown. Rows 16 and 17: share of sensor lows NOT confirmed.

| Row | Events and rule | All 226: events counted (no reading in the window) | All 226: share, % (95 % CI) | All 226: per person, median (quartiles), people | Arm: events counted (no reading) | Arm: share, % (95 % CI) | Arm: per person, median (quartiles), people |
|---|---|---|---|---|---|---|---|
| 1 | Meter under 70, sensor threshold 70: matched reading only | 10,104 (0) | 31.4 (29.3 to 33.7) | 30.9 (22.0 to 41.5), 199 | 2,440 (0) | 28.2 (24.2 to 33.1) | 26.0 (17.8 to 38.5), 58 |
| 2 | Meter under 70, sensor threshold 70: any reading within 15 min before or after | 10,104 (0) | 18.5 (16.8 to 20.5) | 18.0 (10.5 to 26.7), 199 | 2,440 (0) | 16.8 (12.9 to 21.8) | 14.6 (7.4 to 25.4), 58 |
| 3 | Meter under 70, sensor threshold 70: any reading within 30 min before or after | 10,104 (0) | 16.1 (14.5 to 17.9) | 15.6 (8.9 to 22.9), 199 | 2,440 (0) | 14.7 (11.0 to 19.5) | 12.3 (6.8 to 22.5), 58 |
| 4 | Meter under 70, sensor threshold 70: any reading in the 15 min before | 10,019 (85) | 33.9 (31.8 to 36.2) | 33.3 (25.0 to 43.5), 199 | 2,427 (13) | 30.3 (26.6 to 34.8) | 29.8 (19.2 to 39.8), 58 |
| 5 | Meter under 70, sensor threshold 70: any reading in the 15 min after | 10,047 (57) | 20.3 (18.5 to 22.4) | 18.8 (11.9 to 28.6), 199 | 2,428 (12) | 18.5 (14.4 to 23.6) | 16.0 (8.3 to 26.1), 58 |
| 6 | Meter under 54, sensor threshold 70: matched reading only | 2,174 (0) | 18.2 (15.5 to 20.9) | 13.8 (7.1 to 23.1), 85 | 593 (0) | 15.2 (10.1 to 21.4) | 11.2 (2.6 to 20.0), 18 |
| 7 | Meter under 54, sensor threshold 70: any reading within 15 min before or after | 2,174 (0) | 10.1 (8.0 to 12.4) | 7.1 (0.0 to 13.3), 85 | 593 (0) | 9.1 (4.9 to 14.8) | 5.8 (0.0 to 10.0), 18 |
| 8 | Meter under 54, sensor threshold 70: any reading within 30 min before or after | 2,174 (0) | 8.8 (6.8 to 11.0) | 4.3 (0.0 to 10.0), 85 | 593 (0) | 8.4 (4.3 to 14.2) | 4.4 (0.0 to 10.0), 18 |
| 9 | Meter under 54, sensor threshold 70: any reading in the 15 min before | 2,155 (19) | 19.8 (16.9 to 22.7) | 17.0 (7.7 to 29.5), 84 | 591 (2) | 17.1 (11.5 to 23.8) | 11.8 (4.7 to 19.5), 18 |
| 10 | Meter under 54, sensor threshold 70: any reading in the 15 min after | 2,158 (16) | 11.0 (8.8 to 13.5) | 7.1 (0.0 to 15.4), 84 | 590 (3) | 9.5 (5.1 to 15.5) | 7.6 (0.5 to 10.0), 18 |
| 11 | Meter under 54, sensor threshold 54: matched reading only | 2,174 (0) | 50.1 (46.7 to 53.5) | 47.1 (36.8 to 60.0), 85 | 593 (0) | 48.2 (43.1 to 54.5) | 41.0 (37.5 to 54.0), 18 |
| 12 | Meter under 54, sensor threshold 54: any reading within 15 min before or after | 2,174 (0) | 31.7 (28.5 to 35.1) | 28.6 (20.0 to 40.0), 85 | 593 (0) | 28.5 (22.7 to 35.3) | 25.0 (17.0 to 34.7), 18 |
| 13 | Meter under 54, sensor threshold 54: any reading within 30 min before or after | 2,174 (0) | 30.0 (26.9 to 33.3) | 25.0 (16.7 to 40.0), 85 | 593 (0) | 27.2 (21.8 to 33.4) | 21.1 (17.0 to 33.0), 18 |
| 14 | Meter under 54, sensor threshold 54: any reading in the 15 min before | 2,155 (19) | 52.4 (48.9 to 56.0) | 52.6 (39.6 to 63.4), 84 | 591 (2) | 51.3 (45.8 to 57.8) | 45.9 (40.0 to 54.2), 18 |
| 15 | Meter under 54, sensor threshold 54: any reading in the 15 min after | 2,158 (16) | 34.2 (30.9 to 37.6) | 30.2 (22.4 to 40.4), 84 | 590 (3) | 30.7 (25.0 to 37.3) | 25.0 (20.0 to 39.8), 18 |
| 16 | Sensor low (matched reading under 70): meter 70 or above | 11,724 (0) | 40.9 (38.8 to 43.0) | 41.2 (32.4 to 53.8), 201 | 2,818 (0) | 37.9 (33.4 to 42.3) | 40.9 (30.0 to 50.0), 61 |
| 17 | Sensor low (matched reading under 70): meter 80 or above | 11,724 (0) | 20.5 (18.9 to 22.0) | 20.3 (14.1 to 28.6), 201 | 2,818 (0) | 19.0 (15.5 to 22.7) | 19.8 (10.0 to 27.8), 61 |

- Check: rows 1, 11 and 16 match `ACCURACY_V2.md` exactly. All 226: 3,177 of 10,104 not shown; 4,797 of 11,724 not confirmed. Arm: 689 of 2,440; 1,067 of 2,818.
- Signal gaps inside the pair set: none for the 15- and 30-minute windows, because every pair has its matched reading. In the one-sided windows 85 (before) and 57 (after) true lows had no reading.
- Signal gaps outside the pair set: 11,537 verified fingersticks were under 70. 1,433 of them (12.4 %) had no sensor reading within 5 minutes, so they are not pairs. 106 of these had a reading within 15 minutes and 207 within 30 minutes. Adding them gives 18.6 % (16.9 to 20.6) and 16.7 % (15.1 to 18.5) not shown.

## 4. How to read it
- Counted like the clinic studies, the share of true lows not shown falls from 31.4 % to 18.5 % (15 minutes) and 16.1 % (30 minutes). So the sensor showed 81.5 % and 83.9 % of true lows. This is closer to the published 86 to 91 %, but still below it.
- For deeper lows (meter under 54) with the sensor threshold at 70, the sensor showed 89.9 % (15 minutes) and 91.2 % (30 minutes). That is inside the published range.
- Most of the gain comes from readings after the fingerstick. Before only: 33.9 % not shown. After only: 20.3 %. This fits a sensor that runs late. guess: part of it is real glucose still falling when the person tests.
- Of the sensor lows, 40.9 % had a meter value of 70 or above, but only 20.5 % had one of 80 or above. So about half of the unconfirmed sensor lows had a meter value of 70 to 79.

## 5. Limits
- The reference is a home meter with its own error, not lab blood as in clinic studies. A meter value just under 70 can be a true value just above 70, and the reverse.
- A fingerstick is often taken because the person already suspects a low. These are tested moments, not all moments. How this shifts the shares is not known.
- The meter and the sensor have separate clocks, so "before" and "after" are not exact. A wider window also gives the sensor more chances to dip under the threshold by chance.

## 6. How to re-run
- From the repo root (a few seconds): `python analysis/low_detection_window.py "Uncommitted Data/Raw Data Dump" analysis`. It uses the cache in `analysis/cache/` (built first if missing).
- The script stops if the pair sets are not 168,990 pairs from 226 people and 33,467 from 77, or if the matched-reading counts differ from `analysis/accuracy_v2_stats.json`. It writes the stats file and prints the table. No per-participant files.
