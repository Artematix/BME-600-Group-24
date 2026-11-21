# Accuracy by glucose range: three ways to sort the pairs (2026-11-21)

Script: `analysis/accuracy_by_range_sorting.py`. Every number below comes from `analysis/accuracy_by_range_sorting_stats.json`.

## 1. The question
- Each pair must go into one of five glucose ranges. The range can be picked by the meter value, by the sensor value, or by the average of the two.
- Our paper uses the average. Published studies usually use the meter alone (given in the task; not re-checked here). This memo gives all three for all 226 participants.

## 2. Words
- Sensor = continuous glucose monitor (CGM), reads glucose every 5 minutes. Meter = fingerstick blood glucose meter, the reference. Pair = one meter value with the nearest sensor reading within 5 minutes.
- Error = sensor minus meter, in % of the meter value. MARD = mean absolute relative difference: the average size of the error, ignoring direction. Average direction = the average error with its direction kept. "Too low" = the sensor is below the meter.
- 95 % interval = the range the true value most likely sits in. From a bootstrap: participants are re-drawn at random 1,000 times (seed 600), as in `accuracy_v2.py`. In the tables it is in brackets.
- Pair set = Set B of `accuracy_v2.py` (verified fingersticks, all 226 people). Plain matched pairs, no delay correction. Exactly 180 mg/dL belongs to "70 to 180", exactly 250 to "181 to 250". People = participants with at least one pair in the range.

## 3. Checks (all passed)
- Pairs: 168,990 from 226 people. As expected.
- Sorting by the average gives MARD 19.6, 16.9, 14.2, 11.4, 10.3 % of the meter value. Same as before. The average and sensor sortings match `accuracy_v2_stats.json` to 4 decimals, intervals included.
- The meter sorting under 54 matches the earlier check in `ERROR_DRIVERS.md` section 8 (2,174 pairs, 29.8 % too high). The interval there differs a little (other random seed).

## 4. Sorted by the meter value alone (the usual way in published studies)
| Range (mg/dL) | Pairs | People | MARD, % of meter value (95 % interval) | Average direction, % of meter value (95 % interval) | Same in mg/dL |
|---|---|---|---|---|---|
| under 54 | 2,174 | 206 | 37.5 (33.0 to 42.7) | 29.8 % too high (25.1 to 35.4) | 13.0 mg/dL too high |
| 54 to 69 | 7,930 | 224 | 22.5 (20.7 to 24.7) | 10.0 % too high (8.0 to 12.6) | 6.1 mg/dL too high |
| 70 to 180 | 97,098 | 226 | 13.4 (12.8 to 14.0) | 0.8 % too low (0.1 to 1.3) | 1.7 mg/dL too low |
| 181 to 250 | 41,133 | 226 | 10.9 (10.5 to 11.3) | 3.9 % too low (3.5 to 4.3) | 8.3 mg/dL too low |
| over 250 | 20,655 | 226 | 11.1 (10.5 to 11.8) | 6.2 % too low (5.5 to 7.0) | 20.0 mg/dL too low |

## 5. Sorted by the sensor value alone
| Range (mg/dL) | Pairs | People | MARD, % of meter value (95 % interval) | Average direction, % of meter value (95 % interval) | Same in mg/dL |
|---|---|---|---|---|---|
| under 54 | 3,536 | 210 | 25.7 (24.7 to 26.7) | 22.5 % too low (21.2 to 23.7) | 18.8 mg/dL too low |
| 54 to 69 | 8,188 | 223 | 16.6 (16.1 to 17.2) | 9.3 % too low (8.4 to 10.2) | 10.7 mg/dL too low |
| 70 to 180 | 100,016 | 226 | 13.2 (12.7 to 13.7) | 2.5 % too low (2.1 to 2.9) | 7.3 mg/dL too low |
| 181 to 250 | 38,439 | 226 | 11.8 (11.1 to 12.7) | 2.1 % too high (1.3 to 2.9) | 1.9 mg/dL too low |
| over 250 | 18,811 | 226 | 12.8 (11.7 to 14.2) | 5.6 % too high (4.5 to 7.0) | 5.9 mg/dL too high |

- Row "181 to 250": the last two columns point opposite ways. Both are right. The % column divides each error by its own meter value, so pairs with a small meter value count more.

## 6. Sorted by the average of sensor and meter (our paper)
| Range (mg/dL) | Pairs | People | MARD, % of meter value (95 % interval) | Average direction, % of meter value (95 % interval) | Same in mg/dL |
|---|---|---|---|---|---|
| under 54 | 2,156 | 197 | 19.6 (18.7 to 20.6) | 5.2 % too low (3.7 to 6.8) | 4.2 mg/dL too low |
| 54 to 69 | 7,866 | 222 | 16.9 (16.3 to 17.5) | 2.7 % too low (1.7 to 3.7) | 3.3 mg/dL too low |
| 70 to 180 | 99,544 | 226 | 14.2 (13.5 to 14.9) | 1.1 % too low (0.5 to 1.7) | 4.4 mg/dL too low |
| 181 to 250 | 40,262 | 226 | 11.4 (10.8 to 12.2) | 1.2 % too low (0.8 to 1.6) | 5.8 mg/dL too low |
| over 250 | 19,162 | 226 | 10.3 (9.8 to 10.9) | 1.1 % too low (0.7 to 1.4) | 7.3 mg/dL too low |

## 7. Why the three sortings differ
- Both devices make chance errors. Sort by the meter, and "under 54" collects pairs where the meter happened to read low. The sensor did not share that error. So the sensor looks too high.
- Sort by the sensor, and the same happens the other way round. "Under 54" collects the sensor's own low errors. So the sensor looks too low.
- Sort by the average, and a chance error in either device moves the pair the same way. Neither device is favoured.
- The counts show it. The meter is under 54 in 2,174 pairs. The sensor is under 54 in 3,536 pairs. Both are under 54 in only 1,085 pairs.

## 8. What holds under every sorting
- The numbers for all pairs together. MARD 13.3 % (12.7 to 13.9). The sensor reads 1.3 % too low (0.9 to 1.6), which is 5.0 mg/dL too low.
- MARD is largest under 54. Against 70 to 180 it is this many times larger (95 % interval):
  - meter 2.80 (2.48 to 3.15); sensor 1.95 (1.86 to 2.05); average 1.39 (1.29 to 1.48).
- MARD falls from "under 54" to "54 to 69" to "70 to 180". Each step is clear: no interval of a gap includes zero.
- In 70 to 180 the sorting hardly matters. MARD is 13.2 to 14.2 %. The sensor reads 0.8 to 2.5 % too low. This range holds 57 to 59 % of all pairs.
- Over 180, MARD is 10.3 to 12.8 %, lower than in 70 to 180. One case is not clear: over 250 sorted by the sensor (12.8 against 13.2 %; the interval of the gap includes zero).

## 9. What does NOT hold (name the sorting when you quote these)
- The size of MARD under 54. It runs from 19.6 % (average) to 37.5 % (meter).
- The direction of the error outside 70 to 180. It flips with the sorting:
  - Under 54: 29.8 % too high (meter), 22.5 % too low (sensor), 5.2 % too low (average).
  - Over 250: 6.2 % too low (meter), 5.6 % too high (sensor), 1.1 % too low (average).
- For the paper: compare published by-range numbers with section 4, not section 6. The paper's "6.5 % too low under 54" is the average sorting after a delay correction; without the correction it is 5.2 % (section 6).
- Limit: this memo cannot split the sorting effect from real sensor behaviour. guess: the real direction at low glucose lies between the meter-sorted and the sensor-sorted value.
