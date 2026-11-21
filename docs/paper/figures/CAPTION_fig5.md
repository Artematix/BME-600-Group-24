# Figure 5, caption and how it was built

Files are `fig5_three_faults.png` (300 dpi) and `fig5_three_faults.pdf`. Size is 7.0 x 5.35 inches. The smallest text is 8.5 pt.
Rebuild from the repo root with `python -B docs/paper/figures/make_fig5_three_faults.py "Uncommitted Data/Raw Data Dump"`. It needs the raw trial data and takes about 10 seconds.

## Caption for the paper (shortened by the writer, 2026-11-21)

**Figure 5.** What each of the three reported faults does in six hours. The top row shows one real example of each fault from the trial traces. The black line is the true glucose, the orange line is what the faulty sensor shows, and the fault acts in the shaded stretch. The grey band is the target range, 70 to 180 mg/dL. The bottom row shows four outcomes for the typical participant (the median), with whiskers for the middle half of participants. A bar marked 0 means the fault cannot cause that outcome.

## Longer first version (kept for its definitions, which the paper gives in Methods and Results)

**Figure 5.** What each of the three reported faults does in six hours. We put each fault on the recorded glucose traces of the trial for six hours at a time, and counted what changes for a person who follows the standard rules. The top row shows one real six-hour example of each fault. The black line is the true glucose (the recorded trace), and the orange line is what the faulty sensor shows. The fault acts in the shaded stretch, and outside it the two lines lie on each other. The grey band is the target range, 70 to 180 mg/dL. The dashed lines mark 54 mg/dL, under which the hidden low acts, and 250 mg/dL, over which the floor-pinned fault acts. Each example is the simulated episode whose results are closest to the typical participant's, among episodes with no missing reading. The bottom row shows four outcomes of the six hours, with one bar per fault. Bars show the typical participant (the median), and whiskers show the middle half of participants. A bar marked 0 means the fault cannot cause that outcome. A sugar prompt is the sensor showing under 70 mg/dL while the true glucose is 70 or above, counted at most once every 15 minutes. The sugar count is the most it could be, because a real person would stop eating or check with a fingerstick meter. Insulin not given is the correction insulin that the pump's dose calculator leaves out when it gets the shown value. High glucose not shown is time truly above 180 mg/dL that the sensor does not show as high. Very low glucose not shown is time truly under 54 mg/dL while the sensor shows 70 or above. The bars rest on 226 participants (225 for the hidden low), and the insulin bars on the 203 with dose-calculator records (202 for the hidden low).

## How it was built

Words used below:
- Episode = six hours in which the sensor has the fault. It starts at a moment when the true glucose is inside the fault's range.
- Typical participant = the median (the middle participant). Middle half = from quartile 1 to quartile 3.
- Lookup file = `analysis/simulation_three_faults_lookup.csv`. The figure uses its rows with `episode_hours` = 6 and `size_case` = `main`.

### Bars (bottom row)

Every bar is read from the lookup file by the script. No value is typed in by hand. Each value is `<column>_median`, with `<column>_q1` and `<column>_q3` for the whisker.

| Panel | Column in the lookup file | False low | Hidden low | Floor-pinned |
|---|---|---|---|---|
| Unneeded prompts to eat sugar | `sugar_unneeded_n_per_episode` | 20, exact 20.3 (19.4 to 21.2) | 0 | 8.2, exact 8.18 (6.99 to 9.79) |
| Insulin not given, units | `dose_lower_u_per_episode` | 0.5, exact 0.52 (0.28 to 0.84) | 0 | 1.3, exact 1.29 (0.74 to 1.82) |
| High glucose not shown, minutes | `min_over180_not_shown_per_episode` | 83, exact 83.4 (67.4 to 96.9) | 0 | 115, exact 115 (98.0 to 139) |
| Very low glucose not shown, minutes | `min_under54_no_alert_per_episode` | 0 | 34, exact 33.7 (23.1 to 45.1) | 0 |

- The first number in a cell is what the figure prints. Brackets hold the whisker.
- All seven values match the values expected in the brief (20.3, 8.18, 0.52, 1.29, 83, 115, 33.7).
- Participants are 226, and 203 for insulin (column `participants_with_decisions`). The hidden low has 225 and 202, because one participant had no reading under 54 mg/dL.
- No value is missing. All twelve fault and outcome pairs are in the lookup file.
- The five zeros are real zeros. The median and both quartiles are 0 in the file, and the fault cannot cause the outcome by the way it is built.
  - The hidden low only lifts readings that are truly under 54 mg/dL. So it cannot show a low that is not there (no sugar prompt), cannot make a dose smaller (no insulin lost), and cannot hide a high.
  - The false low and the floor-pinned fault only change readings that are truly 70 mg/dL or above. So they cannot hide time under 54 mg/dL.

### Example traces (top row)

- The traces are real. The script loads the trial data with the simulation's own loader and applies the simulation's own fault functions (`fault_range`, `shown_under`, `sugar_unneeded` in `analysis/simulation_three_faults.py`).
- The script draws the same episode starts as the simulation (seed 20261120, 200 starts per participant and fault).
- The script has a built-in check. It rebuilds all episodes, takes the median across participants, and stops if that differs from the lookup file. It matched for all three faults.
- No participant id is printed, saved or shown.

Rule for picking one episode per fault (function `pick_example`):
1. Start from the six-hour episodes the simulation drew, at the main fault size.
2. Keep episodes with all 72 five-minute readings, so the trace has no gap at all. Also drop episodes with a recorded reading of 39 or 401 mg/dL. These are the display limits of the trial sensor, where the recorded value is cut off.
3. Take the episode closest to the typical participant's values in the lookup file. The outcomes compared are hours the fault acted, sugar prompts, minutes above 180 mg/dL not shown and minutes under 54 mg/dL not shown. Distance is the sum of the differences, each divided by the typical value. Outcomes with a typical value of zero are left out.
4. If several episodes tie, take the one where the fault acts in the fewest separate stretches. If they still tie, take the one whose average true glucose is closest to the middle of the tied episodes.

| Fault | Episodes drawn | Left after step 2 | Tied after step 3 | The picked example | Typical participant |
|---|---|---|---|---|---|
| False low | 45,200 | 30,790 | 2 | fault acts 5.25 hours, 20 sugar prompts, 85 minutes above 180 mg/dL not shown | 5.26 hours, 20.3 prompts, 83.4 minutes |
| Hidden low | 38,556 | 16,360 | 715 | 35 minutes under 54 mg/dL not shown | 33.7 minutes |
| Floor-pinned | 45,021 | 29,080 | 469 | fault acts 1.92 hours, 8 sugar prompts, 115 minutes above 180 mg/dL not shown | 1.92 hours, 8.18 prompts, 115 minutes |

- In all three examples the fault acts in one unbroken stretch that starts at hour 0.
- Minutes can only be multiples of 5, because the sensor reads every 5 minutes. That is why the hidden low example shows 35 and not 33.7.

### Things I had to decide

- Width is 7.0 inches, as the brief asked. Figures 2 to 4 are 6.5 inches wide. If the page text is 6.5 inches wide, the figure shrinks to 93 % of its size and the smallest text is still about 8 pt. At 6.5 inches the fault names under the bars almost touch each other. To change the width, edit `WIDTH` in the script.
- Fonts, text sizes, greys and the save step are imported from `make_paper_figures.py`, so they are the same as in Figures 2 to 4.
- The orange (#D55E00) means the faulty sensor, for the line and the bars. In Figure 2 the same orange marks withheld insulin corrections.
- The orange line is drawn wider than the black line. Where both lie on each other, the reader still sees both.
- The line under the false low title says "glucose is not low", not "glucose is fine". The true glucose can be as high as 250 mg/dL, and in the example it is above 180 for 85 minutes.
- The unit of each bar panel is a plain line under the panel title, not a turned label on the axis. It is easier to read.
- The x axis of the top row says "Hours since the fault began", because every simulated episode starts with the true glucose inside the fault's range.
- In the hidden low and floor-pinned panels the only numbers on the y axis are 54 and 250. The scale is the same as in the first panel.
- Insulin is not part of the picking rule, because insulin cannot be seen on a glucose trace.
- A few lines of the simulation are not separate functions (drawing the starts, and the two "minutes not shown" tests). The script repeats them as they are. The built-in check above confirms they give the same numbers.
