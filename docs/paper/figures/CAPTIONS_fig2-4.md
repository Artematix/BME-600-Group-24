# Captions and number sources, Figures 2 to 4

Made by `docs/paper/figures/make_paper_figures.py`. Run: `python -B docs/paper/figures/make_paper_figures.py`. All source files are in `analysis/`.

- Sensor = the CGM (continuous glucose monitor). Meter = the fingerstick meter. Pair = one sensor value with the meter value from the same moment. Serious report = a report of a death or an injury. Malfunction-only report = a report with no death or injury.
- Typical = the median (the middle value). Middle half = from the lower quartile to the upper quartile. 95 % interval = the range the true value most likely sits in.

## Figure 2 (`fig2_decision_curve`)

**Caption.** What a sensor that reads too low does to decisions. The black line is the share of high-glucose episodes that are not shown as high (226 participants). The orange line is the share of needed insulin corrections that are withheld (202 participants). Each line shows the typical participant (the median), and the shaded band around it shows the middle half of participants. The grey zone is the dose margin, where the sensor reads up to 12 % too low and almost no corrections are withheld. The blue line marks the working sensor, which reads 1.3 % too low on average. The pink band marks the typical reported failure that reads low, from 69 % too low (Dexcom and malfunction-only reports) to 77 % too low (Abbott).

| On the figure or in the caption | What it is | File | Field |
|---|---|---|---|
| 1.3 % too low (blue line, value in the caption) | Average error of the working sensor, all 226 participants | `accuracy_v2_stats.json` | `sets.B.overall.bias_pct.value` |
| 69 % too low (left edge of the pink band) | Dexcom serious pairs that read low, median. Exact: 69.2. Pairs: 4,029 | `tail_comparison_stats.json` | `median_reported_error_in_trial`, row `dexcom_serious` / `reads low`: `median_reported_error_pct`, `n_report_pairs` |
| 77 % too low (right edge of the pink band) | Abbott serious pairs that read low, median. Exact: 76.8. Pairs: 4,315 | same | same, row `abbott_serious` / `reads low` |
| 69 % too low (caption only, lies inside the pink band) | Malfunction-only pairs that read low, median. Exact: 69.4. Pairs: 142,817 | same | same, row `malfunction` / `reads low` |
| 12 (axis tick, right edge of the grey zone) | Where corrections begin to be withheld. A setting stored in the file, not a computed result | `tail_comparison_stats.json` | `figure_38.marks_pct` |
| Lower line and band | Corrections withheld, share of the corrections that were needed | `simulation_v2_lookup_extended.csv` | `skipped_of_needed_pct_median`, `_q1`, `_q3`, `_n` (202); rows `bias_pct` 0 to -80 |
| Upper line and band | High episodes not shown as high, share of the true episodes | same | `high180_missed_pct_median`, `_q1`, `_q3`, `_n` (226) |

## Figure 3 (`fig3_working_sensor`)

**Caption.** The working sensor in the trial (226 participants). (a) MARD by glucose range. The whiskers show the 95 % interval. (b) Meter checks that read low, split by what the sensor showed. The upper bar holds the 10,104 checks with the meter under 70 mg/dL, and the lower bar holds the 2,174 checks with the meter under 54 mg/dL. In both bars the sensor shows a low when it reads under 70 mg/dL.

| On the figure | What it is | File | Field |
|---|---|---|---|
| 19.6, 16.9, 14.2, 11.4, 10.3 | (a) MARD per range, in % of the meter value | `accuracy_v2_stats.json` | `sets.B.by_avg_range.<range>.mard_pct.value` |
| Whiskers: 18.7 to 20.6, 16.3 to 17.5, 13.5 to 14.9, 10.8 to 12.2, 9.8 to 10.9 | (a) 95 % interval | same | same block: `ci_low`, `ci_high` |
| 226 participants, 168,990 pairs | (a) count base | same | `sets.B.overall.n_participants`, `n_pairs` |
| 68.6 and 81.8 | (b) sensor showed a low at that moment | `low_detection_window_stats.json` | `sets.all_226.true_lows.<bar>.rules.matched.shown_pct.value` |
| 12.9 and 8.0 | (b) sensor showed a low within 15 minutes, not at that moment | same | `rules.within_15.shown_pct.value` minus `rules.matched.shown_pct.value` |
| 18.5 and 10.1 | (b) not shown, also not within 15 minutes | same | `rules.within_15.not_shown_pct.value` |
| 31.4 % and 18.2 % | (b) not shown at that moment (the two right parts together) | same | `rules.matched.not_shown_pct.value` |
| n = 10,104 and n = 2,174 | (b) meter checks under 70 and under 54 | same | `rules.matched.counted` |

- `<bar>` = `meter_under_70_sensor_under_70` (upper bar, first number) and `meter_under_54_sensor_under_70` (lower bar). The parts of the lower bar add to 99.9 because of rounding.

### MARD by range, two ways of sorting

- Rule of the plotted values: each pair goes into the range of the average of its sensor value and meter value (`by_avg_range`; `analysis/accuracy_v2.py` line 725).
- Sorted by the meter alone: this stats file holds it only for the 77-person check set (`sets.A.by_ref_range_for_reconciliation`). Not plotted. The same for all 226 participants, under three ways of sorting, is in `analysis/ACCURACY_BY_RANGE_SORTING.md` (added 2026-11-21). The paper text uses those numbers.
- 77-person check set = the trial arm that used both sensor and meter, randomised weeks only (33,467 pairs).

| Range, mg/dL | All 226, by average (plotted): MARD %, pairs | 77-person set, by average: MARD %, pairs | 77-person set, by meter alone: MARD %, pairs |
|---|---|---|---|
| Under 54 | 19.6, 2,156 | 19.1, 597 | 37.0, 593 |
| 54 to 69 | 16.9, 7,866 | 16.4, 1,826 | 22.5, 1,847 |
| 70 to 180 | 14.2, 99,544 | 14.8, 19,680 | 13.8, 19,130 |
| 181 to 250 | 11.4, 40,262 | 11.6, 7,747 | 10.9, 7,906 |
| Over 250 | 10.3, 19,162 | 10.2, 3,617 | 11.6, 3,991 |

## Figure 4 (`fig4_trial_vs_reports`)

**Caption.** Sensor error against the meter in the trial and in reports to the FDA, on one scale. Bars show the share of each panel's pairs at each error. The last bar on the right holds all pairs that read more than 200 % too high. The grey band holds 19 of every 20 errors in the trial. Each triangle marks the median of the pairs in which the sensor read lower than the meter.

| On the figure or in the caption | What it is | Field in `tail_comparison_stats.json` |
|---|---|---|
| 168,990, 7,470, 9,189 and 191,112 pairs. 226 participants (caption) | Count base of the four panels | `pair_sets.<set>.n_pairs` (trial also `n_participants`) |
| 35 % too low to 40 % too high (caption) | Edges of the grey band | `inside_trial_central_95.trial_all.range_low_pct.value`, `range_high_pct.value` |
| 77, 69, 69 % too low | Triangles: median of pairs that read low (Abbott, Dexcom, malfunction-only) | `median_reported_error_in_trial`, rows `reads low`: `median_reported_error_pct` |
| 6.6, 11.4, 3.3 % (caption) | Share of the pairs inside the grey band (Abbott, Dexcom, malfunction-only) | `inside_trial_central_95.trial_all.groups.<set>.share_inside_pct.value` |
| Last bar, height 0.14, 20, 21, 6 % | Share of the pairs over 200 % too high (trial, Abbott, Dexcom, malfunction-only) | `figure_38.sets.<set>.share_above_drawn_range_pct` |
| All other bars | Share of the pairs per 5-point step | `figure_38.sets.<set>.share_per_bin_pct`, `figure_38.bin_edges_pct` |
| 5 points (caption) | Width of one step | `figure_38.bin_width_pct` |

- `<set>` = `trial_all`, `abbott_serious`, `dexcom_serious`, `malfunction`. All four panels share one vertical scale. The older figure 38 gave each panel its own scale.
- Malfunction-only, exact: 69.4 % too low (142,817 pairs that read low). This is not 66, which is the median over all malfunction-only pairs.
- Last bar: the file counts pairs over 200 % too high. A pair at exactly 200 % too high sits in the bar before it. The tick label on the figure says "+200 or more".
- The script stops if the bars of a panel do not add up to 100 % of its pairs. On this run each panel adds up to 100.00 %.
- No longer on the figure or in the caption: the dashed lines at 12 % and 20 % too low, and the triangles for the typical report that reads high (191, 152, 135 % too high).
