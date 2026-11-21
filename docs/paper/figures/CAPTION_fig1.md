# Figure 1: caption and number check

Files: `fig1_workflow.png` (300 dpi), `fig1_workflow.pdf`. Size: 6.5 x 3.88 inches. Smallest text: 8 pt.
Rebuild: `python -B docs/paper/figures/make_fig1_workflow.py` (no data needed).

## Caption

Figure 1. How the three data sources (coloured columns) lead to the five findings (white boxes R1 to R5, reported in Sections 3.1 to 3.5). The grey boxes are the two simulations. Both run on the glucose traces of the trial, and Simulation B takes its three faults from the FDA reports.

(Shortened 2026-11-21, no semicolons. The terms sensor, meter and pair are defined in the text and under Table 1.)

## Numbers shown in the figure

Line numbers are lines of `docs/paper/FACT_SHEET.md`. "derived" = worked out from numbers in those lines.

| Number in the figure | What it counts | Fact-sheet line |
|---|---|---|
| 3,382,071 | Reports about CGMs (13 CGM product codes) | B, MAUDE step 1 (line 86) |
| 124,599 | Report texts read by the text patterns and the language model | B, MAUDE step 5 (line 90) |
| 287 | Reference reports used to check the reading | C1, "Reference set" (line 119) |
| 3,382,071 (second time) | Reports that the text patterns alone were run over | B, MAUDE step 9 (line 94); C1, "Pattern-only pass" (line 124) |
| 207,771 | Pairs. derived: 7,470 + 9,189 + 191,112 | B, MAUDE step 8 (line 93) and step 10 (line 95) |
| 226 | Adults with type 1 diabetes in the trial | A1, "Population" (line 29) |
| Dexcom G4 | The trial sensor | A1, "Sensor" (line 31) |
| 159,878 | Dose-calculator decisions | C3, "A decision; how many" (line 152) |
| 168,990 | Sensor-meter pairs after the inclusion rule | B, Trial step 5 (line 80) |
| 680 | Tests of participant traits | C2, "Pre-specified participant-trait tests" (line 142); D5 (line 369) |
| 0 to 80 % too low | How far the sensor reads too low in Simulation A | D1 table (lines 196 to 212) |
| three faults | False low, hidden low, floor-pinned | C3, "Three faults: ranges and sizes" (line 156) |
| 2, 6 and 12 hours | Length of a fault episode in Simulation B | C3, "Three faults: episodes" (line 158) |
| 98 | Shanghai patients who have a pair (of 112 patients) | B, Shanghai step 2 (line 84) |
| 4,012 | Shanghai pairs | B, Shanghai step 2 (line 84) |
| "a different sensor" | Abbott FreeStyle Libre H | A2, "Sensor" (line 47) |

## Where the figure differs from the first brief, and why

- One box was added: "Then run the text patterns alone over all 3,382,071 reports".
  - Reason: 191,112 of the 207,771 pairs come from this step, not from the 124,599 texts read (lines 94 and 95).
  - Without it the figure shows 124,599 texts giving 207,771 pairs. That cannot be.
- "159,878 dose-calculator decisions", not "records".
  - Reason: the fact sheet counts 232,329 calculator records. 159,878 of them are usable decisions (line 152).
- The arrow label is "fault types and how far off", not "fault types and sizes".
  - Reason: the paper rule says the word "size" is not used alone.
  - To change it back: edit `ARROW_LABEL` in the script.
- Simulation A says "0 to 80 % too low". The simulation itself was run wider: from 90 % too low to 90 % too high (line 154). The paper's table shows 0 to 80 % too low.
- 207,771 is not written in the fact sheet. It is the sum of three numbers that are (see the table above).

## Layout notes

- Simulation B sits left of Simulation A. This keeps the arrow from R3 short and stops arrows from crossing.
- R3 sits one row above the other findings, because it also feeds Simulation B.
- Colours, as set in the brief: FDA reports #E69F00, trial #0072B2, Shanghai #009E73.
- Watch out: in Figures 2 to 4 (`make_paper_figures.py`) the same orange means Abbott and the same green means Dexcom.
