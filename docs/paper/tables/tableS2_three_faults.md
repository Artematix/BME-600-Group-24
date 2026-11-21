# Table S2. What each fault changes in six hours

Supplement table for Figure 5. Each fault was put on the recorded glucose traces of the trial for six hours at a time. Each cell gives the typical participant (the median), with quartile 1 to quartile 3 in brackets. Every number is for one six-hour episode.

| Condition | What the sensor does | Hours the fault acted (hours) | Unneeded sugar prompts (count) | Insulin not given (units) | Insulin corrections withheld (count) | High glucose not shown (minutes above 180 mg/dL) | Very low glucose not shown (minutes under 54 mg/dL) | Under-54 alerts not shown (count) | False low alerts (count) |
|---|---|---|---|---|---|---|---|---|---|
| False low | True glucose is 70 to 250 mg/dL. The sensor shows a number 69.4 % lower than the true glucose. For example, a true 150 mg/dL is shown as 46. | 5.26 (5.05 to 5.42) | 20.3 (19.4 to 21.2) | 0.52 (0.28 to 0.84) | 0.35 (0.20 to 0.47) | 83.4 (67.4 to 96.9) | 0 | 0 | 1.02 (0.93 to 1.14) |
| Hidden low | True glucose is under 54 mg/dL. The sensor shows a number 163.6 % higher than the true glucose, which looks normal. For example, a true 50 mg/dL is shown as 132. | 0.56 (0.39 to 0.75) | 0 | 0 | 0 | 0 | 33.7 (23.1 to 45.1) | 0.48 (0.42 to 0.56) | 0 |
| Floor-pinned | True glucose is over 250 mg/dL. The sensor shows its lowest value, 39 mg/dL, which the display writes as "LO". For example, a true 300 mg/dL is shown as 39. | 1.92 (1.63 to 2.32) | 8.18 (6.99 to 9.79) | 1.29 (0.74 to 1.82) | 0.44 (0.31 to 0.56) | 115 (98.0 to 139) | 0 | 0 | 1.12 (1.03 to 1.18) |
| Sensor steadily 20 % too low | Every reading is 20 % lower than the true glucose, at any glucose level. For example, a true 150 mg/dL is shown as 120. | 5.82 (5.75 to 5.87) | 1.83 (1.34 to 2.33) | 0.43 (0.25 to 0.65) | 0.06 (0.02 to 0.10) | 63.3 (52.8 to 73.1) | 0 | 0 | 0.26 (0.21 to 0.32) |
| Sensor steadily 66 % too low | Every reading is 66 % lower than the true glucose, at any glucose level. For example, a true 150 mg/dL is shown as 51. | 5.82 (5.75 to 5.87) | 18.5 (17.4 to 19.8) | 0.80 (0.40 to 1.21) | 0.43 (0.28 to 0.57) | 106 (81.5 to 128) | 0 | 0 | 1.06 (0.94 to 1.16) |

## Notes

1. One episode is six hours in which the sensor has the fault. It starts at a random moment when the true glucose is inside the fault's range. True glucose means the recorded glucose trace of the trial. Inside the episode the fault changes a reading only while the true glucose is inside the fault's range. Each episode is compared with the same six hours without a fault.
2. The typical participant is the median, which is the middle participant when all are put in order. The brackets hold the middle half of participants, from quartile 1 to quartile 3. A plain "0" means zero for the typical participant and for the whole middle half.
3. The last two rows are comparison rows. They show what a plain steady error does in the same six-hour windows as the false low. They are there so the reader can see how the three faults differ from a steady error. A sensor that reads 20 % too low sits at the usual accuracy line. A sensor that reads 66 % too low has the typical error of all malfunction-only report pairs, and it is close to the false low, which reads 69 % too low. A steady low error hides no time under 54 mg/dL, so it cannot stand in for the hidden low.
4. A sugar prompt is counted when the sensor shows under 70 mg/dL while the true glucose is 70 or above, at most once every 15 minutes. The count assumes the person eats 15 g of sugar at every prompt. A real person would stop eating or check with a fingerstick meter, so the count is the most it could be.
5. "Insulin not given" adds up every dose-calculator decision that came out lower with the shown glucose than with the true glucose. It also counts doses that became smaller, not only corrections that were withheld. In the row for the sensor that reads 20 % too low, most of the 0.43 units come from doses that became smaller.
6. A correction counts as withheld when the calculator gives more than 0.5 units with the true glucose and 0 units with the shown glucose.
7. An alert starts when the glucose stays beyond a line for 15 minutes. "Under-54 alerts not shown" counts true lows under 54 mg/dL for which the sensor showed no under-54 alert. "False low alerts" counts alerts at the under-70 line with no true low behind them.
8. The count base is 226 participants. The two insulin columns use the 203 participants with dose-calculator records. For the hidden low the numbers are 225 and 202, because one participant had no reading under 54 mg/dL.
9. Each participant got 200 random episode starts per fault, or fewer if the participant had fewer readings in the fault's range. The random seed is 20261120. The six-hour episodes add up to 45,200 for the false low, 38,556 for the hidden low and 45,021 for the floor-pinned fault.
10. The hours in the two comparison rows are 5.82 and not 6. The count takes only readings that exist, and some five-minute readings are missing in the recorded traces.
11. The sugar and the missing insulin do not change the glucose in this simulation. The table counts changed actions, not changed glucose.
12. Numbers are rounded to three figures. That means no decimals from 100, one decimal from 10 and two decimals under 10.

## Where the numbers come from

- File `analysis/simulation_three_faults_lookup.csv`, rows with `episode_hours` = 6.
- Each cell is `<column>_median` (`<column>_q1` to `<column>_q3`).
- The numbers are the same as in the old Table 2 (`table2_three_faults.md`). All 40 cells were checked against `analysis/simulation_three_faults_stats.json` and all agree.

| Table row | `fault` | `size_case` |
|---|---|---|
| False low | `false_low` | `main` |
| Hidden low | `hidden_low` | `main` |
| Floor-pinned | `floor_pinned` | `main` |
| Sensor steadily 20 % too low | `false_low` | `bias_-20` |
| Sensor steadily 66 % too low | `false_low` | `bias_-66` |

| Table column | Column in the file |
|---|---|
| Hours the fault acted | `affected_h_per_episode` |
| Unneeded sugar prompts | `sugar_unneeded_n_per_episode` |
| Insulin not given | `dose_lower_u_per_episode` |
| Insulin corrections withheld | `dose_withheld_n_per_episode` |
| High glucose not shown | `min_over180_not_shown_per_episode` |
| Very low glucose not shown | `min_under54_no_alert_per_episode` |
| Under-54 alerts not shown | `low54_missed_n_per_episode` |
| False low alerts | `low70_false_n_per_episode` |

- The examples in the second column follow the rules in `analysis/simulation_three_faults.py` (functions `fault_range` and `shown_under`). 150 x 0.306 = 45.9, 50 x 2.636 = 131.8, 150 x 0.80 = 120 and 150 x 0.34 = 51.
- Some values in the file sit exactly halfway between two rounded values, for example 2.3350 and 0.4350. They are written the way the old table and the simulation memo round them, here 2.33 and 0.43.
