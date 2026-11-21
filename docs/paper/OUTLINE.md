# Paper outline

Status: Stage 1 approved by Artemy 2026-11-20 (message, five findings, section list). Stage 2 (one line per paragraph) below: all sections drafted. Artemy read it on 2026-11-20: content is fine; Results rewritten the same day by the number rules below. References verified 2026-11-20 (`docs/paper/REFERENCES.md`). Artemy reviewed the display items and picked the voice on 2026-11-21 (see "Voice"). First prose version of the Results: `docs/paper/PAPER.md`. Full draft of every section written 2026-11-21, with the team's working draft merged in (see `logs/2026-11-21_0500_full-paper-draft.md`). Artemy decided on 2026-11-21 not to cut text for length. The PDF build prints the figures at 85 % to stay inside 10 pages.
Rules: 10 pages max (title page and references not counted), single column, IEEE references. Rubric: `docs/BMEN600 Final Project.pdf`.
Rubric facts checked 2026-11-21: it names no font, spacing or margins. It does not mention appendices or supplements, so read strictly they would count toward the 10 pages (gap G14). Its section lengths: Abstract about 0.5 page, Introduction 1.5 to 2, Dataset and Methods about 2, Results about 2, Discussion 1.5 to 2, Conclusion about 0.5. Every figure and table must be numbered, captioned and discussed in the text.

## Research question
How large must a continuous glucose monitor (CGM) error be before it changes a treatment decision, and how large are CGM errors in practice, both in reported failures and in normal operation?

## Message (approved)
1. Insulin corrections start to be withheld at about a 12 % low bias. At 20 %, 7 % are withheld and half of high episodes are not shown.
2. A working sensor sits inside that margin on average (bias -1.3 %), but its scatter still leaves 31 % of true lows not shown as low.
3. Errors in FDA failure reports sit far outside it (median -69 to -77 % when reading low; corrected 2026-11-21 from "-66", which is the median over all malfunction-only pairs) and come as three faults, each breaking a different decision.
4. Who the patient is does not predict error (680 tests); wear day 1 and the low range do.

The same message, written by the number rules (use this wording):
1. Doses have a margin. A sensor that always reads too low changes no insulin corrections until it reads about 12 % too low. At 20 % too low, about 1 in 7 of the corrections people needed is withheld, and half of their high-glucose episodes are not shown as high.
2. A working sensor is inside that margin on average (it reads 1.3 % too low). But single readings scatter: about 3 in 10 meter-confirmed lows were not shown as low at that moment.
3. Reported failures are far outside it: the typical report that reads low has the sensor 69 to 77 % too low. They come as three faults, each breaking a different decision.
4. Who the patient is does not predict error (680 tests). The first day of wear and low glucose do.

## Sections

| # | Section | Pages | What it says |
|---|---|---|---|
| - | Abstract | 0.5 | Problem, question, three data sources, the four message lines, main limit. 200 to 250 words. |
| 1 | Introduction | 1.5 | People dose insulin from the sensor. The 2025 recall shows what a wrong sensor does. Accuracy studies describe working sensors; failure reports describe failing ones; neither says which decisions break. Question and three contributions. |
| 2 | Dataset and Methods | 2.25 | Three data sources and what one case is in each. Then three analyses: read the FDA reports, measure a working sensor, simulate decisions. How each was checked. |
| 3 | Results | 2.75 | Five findings, one subsection each (below). |
| 4 | Discussion | 1.5 | Answer the question. Compare with published work. What it means for users. Four limits. Next step. |
| 5 | Conclusion | 0.4 | Answer, contribution, main limit. |
| - | Statements | 0.6 | Data and code availability. AI-assisted work. Author contributions. |

Total 9.5 pages. Half a page spare.

## Results: five findings (these become the subheadings)

| # | Finding | Evidence |
|---|---|---|
| R1 | Insulin corrections start to be withheld when the sensor reads about 12 % too low | Constant-bias sweep on 226 people's traces, 159,878 calculator decisions |
| R2 | A working sensor reads only 1.3 % too low on average, but about 3 in 10 true lows are not shown as low | 168,990 verified sensor-meter pairs; accuracy by glucose range; FDA iCGM criteria; published values |
| R3 | In reported failures the sensor is typically 69 to 77 % too low, and the failures are three distinct faults | 124,599 report texts read; 16,659 serious pairs by manufacturer; 191,112 malfunction-only pairs |
| R4 | Each fault breaks a different decision | Three-fault simulation in episodes of 2, 6 and 12 hours, against the constant bias |
| R5 | Error follows wear day and glucose range, not who the patient is | Wear day 1; 680 pre-specified tests with one modest survivor; Shanghai comparator; who the reports come from |

Primary result: R1 (the error-to-decision curve).
Meaningful comparison: where a working sensor (R2) and reported failures (R3) sit on that curve.

## Figures and tables (7)

| Item | Where | What it shows | State |
|---|---|---|---|
| Table 1 | Methods | The data sources: who, how many, sensor, what one case is, what we used. For the reports also: share from the US (63.8 %), and how often age, sex and race are filled in | built: `docs/paper/tables/table1_data_sources.md` |
| Figure 1 | Methods | Workflow: three sources, the steps, the result each feeds | built: `docs/paper/figures/fig1_workflow.png` |
| Figure 2 | Results R1 | The error-to-decision curve, with marks for a working sensor and for reported failures | built: `docs/paper/figures/fig2_decision_curve.png` |
| Figure 3 | Results R2 | Working-sensor accuracy by glucose range, and true lows shown or not shown | built: `docs/paper/figures/fig3_working_sensor.png` |
| Figure 4 | Results R3 | Trial errors and reported errors on one axis | built: `docs/paper/figures/fig4_trial_vs_reports.png` (captions for Figures 2 to 4: `docs/paper/figures/CAPTIONS_fig2-4.md`) |
| Figure 5 | Results R4 | The three faults: one real six-hour example of each, and four outcomes as bars. Replaces Table 2, which Artemy found hard to read (2026-11-21) | `docs/paper/figures/fig5_three_faults.png`. The numbers move to supplement Table S2: `docs/paper/tables/tableS2_three_faults.md` |
| Table S1 | Supplement. Introduced by the last paragraph of R5 and pointed to from Methods | Every analysis we ran: question, what we did, what we found, in full sentences. Includes the null results | built: `docs/paper/tables/tableS1_analyses.md` (18 rows; full list of 74 in `tableS1_full.md`). Was Table 3 until 2026-11-21 |

## In the paper only as a row of Table S1 (no prose)
Country spread of reports. Field inventory. Children in reports. Bland-Altman and Parkes grid. Rate of change. Time of day. Site effects. The six fault families of simulation version 2. Risk indices. Simulation version 1.

## Not in the paper
The story of how the pair set was cleaned (one sentence in Methods states the inclusion rule). The midterm MARD of 10.4 %.

# How numbers are written (set by Artemy 2026-11-20; holds for these notes and for the paper)

The paper has many percentages of different kinds: how wrong the sensor is, shares of people, shares of readings, shares of decisions, shares of reports. A reader must never have to work out which kind a number is.

1. A percentage never stands alone. The words next to it say what it is a share of. Write "13 % of the corrections that were needed", not "13 %".
2. Sensor error is written in words with a direction: "reads 20 % too low". No minus signs in sentences. Minus signs appear only on figure axes and in tables.
3. Each share is written once, in one form (changed by Artemy, 2026-11-21). Never the same share twice in one sentence. Not "about 1 in 7 (13.5 %)". Not "57 of 225, which is 1 in 4". Which form to pick:
   - A plain percentage when the sentence holds no sensor-error percentage. This is the usual form for a single share and for a range across groups ("85 to 97 % of pairs").
   - "1 in N", "half" or "N in 10" when the sentence already holds a sensor-error percentage ("at 20 % too low they lost about 1 in 7"), or when the fraction is simple and round ("1 in 4").
   - A plain count when it is easy to grasp ("57 of the 225 participants").
   - A rounded form gets a small raised letter. The exact value, its range and its count base go in the "Exact values" list at the end of the paper (`tables/tableS3_exact_values.md`).
   - A 95 % interval stays in the text only for the headline numbers (average error, MARD, true lows not shown, the sex gap). All other ranges go in the "Exact values" list.
4. One condition per sentence. First how wrong the sensor is, then what happens. No chains like "X % at Y %, X % at Y %". A run of values over many error levels goes in a figure or a table. The text names two levels only.
5. The two error levels named in text: 12 % too low (where doses begin to change) and 20 % too low (the usual accuracy line).
6. Every kind of error gets one example in mg/dL on first use: "a sensor that reads 20 % too low shows 160 when glucose is 200".
7. The word "size" is not used alone. Say "how far the reading is from the true value".
8. Simulation results start with the setup in plain words: "in six hours with this fault, the typical participant...". Typical participant = the median.
9. Ranges are labelled every time: "95 % interval 29 to 34" or "middle half of participants 19 to 21".
10. Simple is not the same as short. A paragraph may be longer if each sentence carries one number and says what it counts. Each fault and each outcome gets a plain description and an example before its numbers.
11. No semicolons. Colons only before a real list. Use commas or connecting words (Artemy, 2026-11-21).
12. Merged into rule 3 on 2026-11-21. The text mixes plain percentages and "1 in N".

# Words fixed for the paper (one name per thing)

| Word | Meaning, stated once at first use |
|---|---|
| Sensor | The CGM. It reads glucose under the skin every 5 minutes. |
| Meter | The fingerstick meter: a drop of blood from the finger. The reference in this paper. |
| Display | What the wearer sees and hears: the current glucose number, a trend arrow, a graph of the last hours, and alerts when the number crosses a low line or a high line. Defined in the first paragraph of the Introduction and again in Methods with the lines used (70, 54 and 180 mg/dL). |
| Reads too low / too high | The sensor value is below / above the true value. Given as a percentage of the true value. |
| Bias | The average error with its direction. Defined once in Methods. In Results sentences say "reads X % too low". |
| MARD | The average distance between sensor and meter, ignoring direction, as a percentage of the meter value. Always written with the word "MARD". |
| Insulin correction | Extra insulin the dose calculator adds when glucose is above target. |
| Withheld | The calculator gives a correction with the true glucose and none with the wrong reading. |
| True low | Meter under 70 mg/dL. |
| False low | The sensor shows under 70 while true glucose is 70 or above. |
| Hidden low | True glucose is low while the sensor shows 70 or above. |
| Floor-pinned | The sensor shows its lowest value while true glucose is over 250. |
| Pair | In the trial: one meter value with the sensor reading from the same moment (within 5 minutes). Defined in Methods. |
| Report pair | (Was "pair" until 2026-11-21. Artemy asked whether the two kinds of pair are the same thing. They are the same kind of thing from two sources, so the second one has its own name.) A report that states both the sensor value and a reference value for the same moment. The reference is a fingerstick meter, or in Abbott's standard report text "the comparison device" (about 1 in 4 sampled Abbott malfunction-only pairs). Methods says this once; after that the paper says "meter". |
| Serious report | A report of a death or an injury. |
| Malfunction-only report | A report with no death or injury. |
| Typical participant | The median across participants. |

# Voice (picked by Artemy 2026-11-21)

- Version A of the two samples. Each paragraph opens with its point in plain words. Then one example in mg/dL. Then the numbers, each with what it counts.
- The text lets the reader follow how we got there ("To find out how large, we made every reading too low by the same steady amount...").
- Artemy's model sentence: "The dose calculator still adds a correction, but a smaller one."
- No semicolons. Colons only before a real list. No dashes used as pauses.
- Figures carry little text. The caption explains.
- Table cells are full sentences in natural language. A table must not make the reader complete a sentence across columns.
- First prose version of the Results: `docs/paper/PAPER.md`.

## Sentence rules (from Artemy's read of the Results, 2026-11-21). They hold for every section.

Artemy: "I don't want to have to make the same fixes for each section." Check every new paragraph against this list before he sees it.

1. A comparison names both sides. Not "59 % of high episodes, against 51 %". Say what each number belongs to ("compared with half of them when the line was at 180").
2. An assumption is stated plainly, with "we" or "our" as the subject. "Our simulation assumes that the recorded sensor trace is the true glucose."
3. When a result rests on part of the participants, the same passage says why that part exists ("one arm was asked to check with a meter before dosing").
4. Every sentence names its own subject. No sentence that only works through the one before it ("The amount of disagreement does not." "It changes no dose."). No very short sentence used as a beat.
5. A paragraph does not open by pointing back ("errors of this kind", "such a reading", "the reported errors are not all of one kind"). It names the thing.
6. No sentence written for effect. If it sounds like a saying, write the plain point. "For a person wearing the sensor, the average matters less than the single reading in front of them" became "The sensor often did not show a low that the meter confirmed."
7. A simple idea gets a short, plain explanation. The range-sorting paragraph was the example of too many steps.
8. A vague word is replaced by the fact. Not "the fields are thin". Write "many reports do not record who the patient was".
9. A caveat gets a clause, not its own sentence, and only when it changes how a number should be read. A check that changes nothing stays out of the text (it stays in Table S1). The "92 % settling" check was the example.
10. A source is named. "Welsh et al. [77] use a count that...", never "a published way of counting".
11. A term is defined once, where it is first needed. "Typical (median)" goes in brackets, not in its own sentence. If one word would cover two things, the second gets its own name. Pairs from the trial are "pairs". Pairs read from report texts are "report pairs", and the three groups are "Abbott serious pairs", "Dexcom serious pairs" and "malfunction-only pairs".
12. No number twice (see number rule 3). No point twice inside one paragraph.
13. A caption says only what is needed to read the figure. No build detail (for example the width of a bar), and nothing the text already says.
14. The rest of the sections may use the teammates' draft for ideas and wording (Artemy, 2026-11-21). Reuse notes: `docs/team-docs/2026-11-21_teammate_draft_reuse_notes.md` (local only).

# Stage 2: one line per paragraph

"[pending]" = a number an agent is collecting now.

## Results (second prose version after Artemy's read, 2026-11-21: about 2,490 words, 21 paragraphs, Figures 2 to 5, raised letters a to o for exact values)

Changed in the second version: the sentence rules above applied throughout. Bracketed percentages replaced by raised letters. "Pair" from reports is now "report pair". The 92 % settling check and the lab-reference sentence are out (the lab reference is now a clause). The 15-minute count is named as Welsh et al. [77]. Captions of Figures 3, 4 and 5 shortened.

Cut from the Results text on 2026-11-21 to save space. Each is still in a figure, in Table S1, or planned for the Discussion.
- The share of readings inside the usual accuracy band (83.8 %).
- "7,301 of 7,470 Abbott pairs were 20 % or more away from the meter". The sentence on the trial's 95 % range says the same.
- The meter-as-truth baseline with no fault added (2.1 % of needed corrections withheld, 4.2 % of doses changed by more than 1 unit).
- "How far the hidden low reads too high makes no difference". It goes in Discussion D1.
- For the false low: 0.35 corrections withheld per episode. For the floor-pinned fault: the 8 sugar prompts. Both are in Figure 5 or Table S2.
- Age fill rates by maker (Dexcom 93 in 100, Abbott 19 in 100), median age 54, half female.
- Sensor lows not confirmed by the meter (4,797 of 11,724). Reason: the same 4,797 readings are in R3.3 as "3 times in 100 when the meter was not low". Two shares of one count would confuse the reader.

How to read the lines below:
- "Point" = the one thing the paragraph says. "Example" = one case in mg/dL. "Numbers" = full sentences, each naming what is counted.
- "Typical participant" = the middle participant (median). Brackets after it give the middle half of participants, unless they say "95 % interval".
- [check] = a detail to confirm against the source file before writing.

### R1. Insulin corrections start to be withheld when the sensor reads about 12 % too low (Figure 2)

- R1.1 Doses have a margin.
  - Point: a sensor that always reads a little too low changes no insulin corrections. Corrections start to disappear only when it reads about 12 % too low.
  - What is counted: an insulin correction is the extra insulin that the pump's dose calculator adds when glucose is above the person's target. "Withheld" means the calculator gives a correction (more than 0.5 units) with the true glucose and gives none with the wrong reading.
  - Example: true glucose is 200 mg/dL. A sensor that reads 12 % too low shows 176. The calculator still gives a correction, only a smaller one. A correction disappears only when the shown number falls to about the person's target. This is why small errors change no decisions.
  - Numbers. Base: 159,878 calculator decisions from 203 participants; 202 of them had at least one needed correction. Each share is "of the corrections that were needed", for the typical participant.
    - Sensor reads up to 8 % too low: no corrections are withheld.
    - Sensor reads 12 % too low: about 1 correction in 80 is withheld (1.2 %; middle half of participants 0.3 to 3.5).
    - Sensor reads 20 % too low: about 1 in 7 (13.5 %; middle half of participants 7.8 to 21.3).
    - Sensor reads 40 % too low: about 2 in 3 (64.2 %).
    - Sensor reads 70 % too low or more: all of them.
  - In the paper: the text names the 12 % and the 20 % level only. The other levels are read from Figure 2.

- R1.2 The display has no margin.
  - Point: what the screen shows goes wrong from the first step of error, long before doses do.
  - What is counted: a high episode = 15 minutes or more with true glucose above 180 mg/dL. "Not shown as high" = the screen did not show above 180 during it. A false low alert = the screen shows under 70 for 15 minutes while true glucose is 70 or above.
  - Example: true glucose is 200. A sensor that reads 12 % too low shows 176, so this high is not shown as high. Many highs sit only a little above 180, so even a small error takes them under the line.
  - Numbers. Base: 226 participants, the typical participant.
    - Sensor reads 2 % too low: about 1 high episode in 18 is not shown as high (5.6 %).
    - Sensor reads 12 % too low: about 1 in 3 (32.6 %; middle half of participants 26.9 to 38.8).
    - Sensor reads 20 % too low: half (50.8 %; middle half of participants 43.4 to 58.7).
    - Sensor reads 40 % too low: almost 9 in 10 (88.7 %).
    - False low alerts: one every ten days when the sensor reads 2 % too low (0.10 per day). Almost one a day when it reads 20 % too low (0.86 per day).
  - Two checks, both for a sensor that reads 20 % too low:
    - With the high line at 200 instead of 180: 59 % of high episodes are not shown, against 51 %.
    - With the meter as the true value instead of the sensor trace (15,034 decisions, 67 people): about 1 in 4 needed corrections is withheld (23.8 %; middle half of participants 13.6 to 34.5), against 1 in 7 (13.5 %). The effect points the same way and is larger.

### R2. A working sensor reads only 1.3 % too low on average, but about 3 in 10 true lows are not shown as low (Figure 3)

- R2.1 On average the working sensor is well inside the margin.
  - Point: the trial sensor is nearly unbiased. Its average error is a tenth of the 12 % at which doses begin to change.
  - Numbers. Base: 168,990 sensor-meter pairs from 226 participants.
    - Average direction of error (bias): the sensor reads 1.3 % too low (95 % interval: 0.9 to 1.6 % too low). Example: at a true 150 mg/dL the average reading is 148.
    - Average distance from the meter, ignoring direction (MARD, defined in Methods): 13.3 % of the meter value (95 % interval 12.7 to 13.9). Example: at a true 150, a typical reading is off by about 20 mg/dL, up or down.
    - About 5 readings in 6 (83.8 %; 95 % interval 82.7 to 84.9) are within the usual accuracy band: within 20 mg/dL of the meter when the meter is under 100 mg/dL, within 20 % when it is 100 or above.
  - Comparison with published values for the same sensor: MARD 11.3 % in home use against a meter (Bailey 2015), which is the like-for-like figure; 9.0 % in clinic against a laboratory analyser. Ours is 2 points above the like-for-like figure.
  - Comparison with the FDA rules for sensors that feed dosing systems (iCGM criteria, written in 2018, after this sensor): the trial sensor meets none of the seven.

- R2.2 The sensor and the meter disagree most where glucose is low.
  - Point: the error is largest at the bottom of the glucose range. This holds however the pairs are sorted into ranges. The direction of the error does not.
  - How the ranges are set (explained once, in Results 3.2, next to the numbers. Methods M6 only points to it. Changed 2026-11-21): each pair is put in a glucose range by the average of its sensor value and its meter value. Reason: the device you sort by has its own errors sorted with it, so the other device looks wrong in the opposite direction. The average favours neither.
  - Numbers for the range under 54 mg/dL, all 226 participants, three ways of sorting (source: `analysis/ACCURACY_BY_RANGE_SORTING.md`):

    | Pairs sorted by | MARD under 54 | What the sensor does there |
    |---|---|---|
    | the meter alone | 37.5 % | reads 29.8 % too high |
    | the sensor alone | 25.7 % | reads 22.5 % too low |
    | the average of both (used in Figure 3) | 19.6 % | reads 5.2 % too low |

  - What holds under every sorting:
    - MARD is largest in the range under 54. It is 1.4 to 2.8 times the MARD of the 70 to 180 range.
    - In the 70 to 180 range, which holds about 6 in 10 pairs, the sorting hardly matters: MARD is 13.2 to 14.2 %.
    - All pairs together do not depend on sorting: MARD 13.3 %, sensor reads 1.3 % too low.
  - In the paper: Figure 3 shows MARD by range (average sorting: 19.6 % in the lowest range, 10.3 % in the highest). The text gives the "1.4 to 2.8 times" line and one sentence saying that the direction flips with the sorting. It gives no by-range direction as a finding.
  - Delay: the sensor runs 5 to 7 minutes behind the blood. This is used in R2.3. The delay-corrected value (6.5 % too low under 54, average sorting; 5.2 % before the correction) stays in the full analyses list only (`tableS1_full.md`).
  - The two sides of the same scatter, in decision terms, are in R2.3: when the meter is low the sensor often is not (3 in 10), and when the sensor is low the meter often is not (4 in 10).

- R2.3 The scatter of single readings, not the average, is what changes decisions.
  - Point: an average error near zero hides many single readings that are far off. These are the readings a person acts on.
  - Numbers. Base: all 226 participants.
    - True lows not shown. The meter read under 70 on 10,104 checks. At that moment the sensor showed 70 or above on 3,177 of them: about 3 in 10 (31.4 %; 95 % interval 29.3 to 33.7).
    - The same, counted the way clinic studies count (any sensor reading under 70 within 15 minutes before or after the check): about 2 in 10 were still not shown (18.5 %; 95 % interval 16.8 to 20.5). Most of the difference comes from readings after the check, which fits a sensor that runs late.
    - Sensor lows not confirmed. The sensor showed under 70 at 11,724 meter checks. The meter read 70 or above on 4,797 of them: about 4 in 10 (40.9 %). About half were near misses. The meter was 80 or above in 2 in 10 of all 11,724 sensor lows (20.5 %), so about half of the 4,797 unconfirmed ones had a meter value of 70 to 79 (`analysis/LOW_DETECTION_WINDOW.md`, line 53). An earlier version of this line said "most", which was wrong. This whole item is not in the paper text (see the cut list above).
    - Readings far too low. About 1 reading in 9 was 20 % or more too low (10.8 %; 95 % interval 10.2 to 11.4), although the average reading is only 1.3 % too low.
    - Effect on doses, with the meter as the true value (15,034 calculator decisions, 67 people): the working sensor, with no fault added, withheld about 1 in 50 of the corrections that were needed (2.1 %) and changed about 1 in 24 calculator doses by more than 1 unit (4.2 % of all calculator decisions).

### R3. In reported failures the sensor is typically 69 to 77 % too low, and the failures are three distinct faults (Figure 4)

- R3.1 What was read.
  - Point: wrong readings are the most common problem in reports of death or injury, and many reports state both numbers.
  - Numbers.
    - 3,382,071 reports about CGMs in total. 123,607 of them report a death or an injury ("serious reports").
    - In the serious reports, a wrong reading is the most common problem type: about 1 report in 3 (33.1 %).
    - 124,599 report texts were read.
    - A "pair" = a report that states both what the sensor showed and what the meter showed. Pairs found in serious reports: 7,470 for Abbott, 9,189 for Dexcom. Pairs found in malfunction-only reports (no death or injury): 191,112.

- R3.2 How far off the sensor was.
  - Point: the reported errors are about six times larger than the 12 % at which doses begin to change, and a working sensor almost never makes them.
  - Example: the meter reads 200 mg/dL. The typical Abbott report that reads low has the sensor at 46 (77 % too low). The typical Dexcom one has it at 62 (69 % too low).
  - Numbers.
    - Among pairs where the sensor read lower than the meter, the middle pair (median) was 77 % too low for Abbott, 69 % too low for Dexcom, and 69 % too low in malfunction-only reports (4,315, 4,029 and 142,817 pairs). One definition everywhere: the median over pairs that read low. Never the 66 %, which is the median over all malfunction-only pairs.
    - Almost all pairs were 20 % or more away from the meter, in one direction or the other: 7,301 of 7,470 Abbott pairs and 8,914 of 9,189 Dexcom pairs (97 to 98 in 100).
  - Comparison with the working sensor (Figure 4).
    - In the 26 randomised weeks of the trial, a reading 69 % or more too low came up in 159 of 137,662 meter checks: about 1 check in 900.
    - It is rare per check but not rare per person: 57 of 225 participants, 1 in 4, had at least one such reading in those weeks.
    - The middle 95 % of trial readings lie between 35 % too low and 40 % too high. Only 3 to 11 in 100 report pairs fall inside that range.

- R3.3 The reported errors are three different faults.
  - Point: the reports do not describe one kind of error. Sorting each pair by what the meter said and what the sensor showed gives three faults.

    | Fault | The meter says | The sensor shows | Example from the reports |
    |---|---|---|---|
    | False low | 70 or above (not low) | under 70 | meter 178, sensor 63 (the middle malfunction-only pair) |
    | Hidden low | under 70 (low) | 70 or above | meter 45, sensor 144 (the middle serious pair that read high) |
    | Floor-pinned | over 250 (very high) | its lowest value, 40 or below ("LO") | meter 300, sensor "LO" |

  - Numbers, asked as the same question of the trial and of the reports. [rule change, see "Rules fixed for the writing"]
    - "When the meter was not low (70 or above), how often did the sensor show a low?" Trial: 3 times in 100. Abbott serious reports: 50 in 100. Dexcom serious reports: 32 in 100. Malfunction-only reports: 60 in 100.
    - "When the meter was low (under 70), how often did the sensor fail to show a low?" Trial: 31 times in 100 (the same number as in R2.3). Abbott: 93 in 100. Dexcom: 86 in 100. Malfunction-only: 97 in 100.
    - "When the meter was over 250, how often did the sensor show its lowest value?" Trial: 2 of 20,655 checks. Reports: 7 to 8 in 100 in each group.
  - Which fault leads where (corrected 2026-11-21 by the number check). As shares of all pairs in a group: false lows are about 6 in 10 malfunction-only pairs (57.6 %), hidden lows fewer than 1 in 20 (4.5 %). Hidden lows are about 4 in 10 Dexcom serious pairs (39.1 %) and 1 in 4 Abbott serious pairs (26.1 %). An earlier version said malfunction-only reports are "almost all false lows", which was wrong.
  - Coverage: about 6 in 10 pairs in each group are one of the three faults. The floor-pinned reading is the extreme case of the false low (meter over 250, sensor 40 or below), so it is counted inside the false lows. In the other 4 in 10 pairs the two values are far apart but on the same side of the low line.
  - The examples "meter 178, sensor 63" and "meter 45, sensor 144" are each two separate medians over a group of pairs, not one real pair. Write "the median meter value was ... and the median sensor value was ...".
  - Share of pairs in which the sensor read lower than the meter: 58 % Abbott, 44 % Dexcom, 75 % malfunction-only. The "69 to 77 % too low" holds for these pairs only, and the text says so.
  - One caution, stated once here: these are shares of reports that state both numbers. They show what gets reported, not how often sensors fail.

### R4. Each fault breaks a different decision (Figure 5)

Setup for all three paragraphs: we put each fault on the real glucose traces for six hours and counted what a person following the standard rules would do differently. Results are for the typical participant in one six-hour episode. Figure 5 shows one real example of each fault and four outcomes. Supplement Table S2 holds every number. The text gives the example and two or three numbers per fault.

- R4.1 The false low makes people eat sugar they do not need and lose insulin they do need.
  - What the fault is: glucose is normal or high (70 to 250 mg/dL), but the sensor shows a number about 69 % lower.
  - Example: glucose is 150. The sensor shows 46.
  - What the person is told: "you are low". The standard advice for a low is to eat 15 g of fast sugar and check again in 15 minutes.
  - Numbers, six hours with this fault:
    - The fault changed the reading for about 5 of the 6 hours (5.26 hours), because glucose was between 70 and 250 most of the time.
    - The sensor called for sugar about 20 times (20.3; middle half of participants 19.4 to 21.2). That is nearly once every 15 minutes for the whole time, or about 300 g of sugar (304 g) that was not needed. A real person would stop or check with a meter, so this is the most it could be.
    - About 1 episode in 3 lost an insulin correction (0.35 corrections withheld per episode). On average half a unit of insulin was not given (0.52 units per episode).
    - 83 minutes of truly high glucose (above 180) were not shown as high.
  - Comparison with a plain steady error: a sensor that simply reads 66 % too low for the same six hours gives almost the same sugar count (18.5). A sensor that reads 20 % too low gives about 2 (1.83). So the false low behaves like a very large steady error, and the curve of R1 already covers it.

- R4.2 The hidden low takes away the warning.
  - What the fault is: glucose is dangerously low (under 54 mg/dL), but the sensor shows a normal number.
  - Example: glucose is 50. The sensor shows 132.
  - What the person is told: nothing. There is no alert and no reason to eat.
  - Numbers, six hours that contain this fault:
    - About 34 minutes were spent truly under 54 while the screen showed 70 or above (33.7 minutes; middle half of participants 23.1 to 45.1).
    - About one under-54 alert was lost for every two episodes (0.48 per episode).
    - No sugar prompts and no dose changes. This fault removes a warning. It does not add a wrong action.
  - Comparison with a plain steady error: a sensor that reads too low, by any amount, gives zero for both numbers. A sensor that reads too low cannot hide a low. So the curve of R1 does not contain this fault at all.
  - How far off the sensor is did not matter: reading 89 % too high or 329 % too high gave the same result. Once the screen shows 70 or above, the alert is gone.

- R4.3 The floor-pinned sensor costs the most insulin.
  - What the fault is: glucose is very high (over 250 mg/dL), but the sensor shows its lowest possible value.
  - Example: glucose is 300. The screen shows "LO" (39 mg/dL).
  - What the person is told: "you are very low", at the moment they most need insulin.
  - Numbers, six hours that contain this fault:
    - Glucose was over 250 for about 2 of the 6 hours (1.92 hours), so the fault acted for less time than the false low.
    - In that time the sensor called for sugar about 8 times (8.18; middle half 6.99 to 9.79), about 120 g, while glucose was above 250.
    - 1.29 units of insulin were not given. That is two and a half times the false low (0.52 units) in about a third of the time. Per hour that the fault acted: 0.64 units against 0.10.
  - Why: the needed correction is largest when glucose is highest, so losing it there costs the most insulin.

### R5. Error follows wear day and glucose range, not who the patient is (Table S1)

- R5.1 The sensor is least accurate on its first day.
  - Point (corrected 2026-11-21 by the number check): three things clearly move accuracy. The glucose range (R2.2). The sensor's delay, which shows when glucose changes fast: MARD 18.3 % falling fast and 17.9 % rising fast, against 12.3 % when stable (`analysis/ERROR_DRIVERS.md` lines 70 to 74). And the day of wear. In the project's joint model fast change adds about 6 points of error and the first day of wear adds 2.3. Rate of change is therefore not a "did not change the conclusions" item.
  - Numbers.
    - MARD is 15.2 % on day 1 of wear and 11.8 % on day 7.
    - The extra error fades fast: it halves about every 24 hours.
    - Is it the sensor settling, or are poor sensors removed early so that later days look better? Almost all of it is settling: 92 % of the day-1 excess (95 % interval 85 to 100).
  - Reports and wear day: of the 6,627 Abbott serious reports that name a wear day, 891 name day 1 (13 %), against 7 % for an even spread. But Dexcom serious reports show no first-day excess (81 of 1,140, 7.1 %), only 8.9 % of Abbott serious reports name a day, and the source memo calls the Abbott excess "a template feature as much as a sensor feature". Not in the paper text. It is in Table S1, row 6, with both makers.

- R5.2 Who the participant is does not predict error.
  - Point: age, sex, body size, diabetes control and the other traits we had do not tell which participants get larger errors.
  - Numbers.
    - 680 planned comparisons of a participant trait against an error measure, with a correction for running many tests (Benjamini-Hochberg, defined in Methods).
    - By chance alone about 34 would look significant before the correction. 69 did. After the correction 1 remained.
    - The one that remained: in the low range (average of sensor and meter under 70 mg/dL) the sensor read 6.4 % too low for women and 2.2 % too low for men. The gap is 4.2 points (95 % interval 2.0 to 6.0; 76 women and 74 men with enough low pairs). At 60 mg/dL that is a difference of about 2.5 mg/dL. It changes no dose. It does shift low alerts a little: in the lookup women get 0.28 false low alerts per day and men 0.11, an upper limit (`analysis/DEMOGRAPHICS_FOLLOWUP.md`). An earlier version said "no alert", which was wrong.
  - A second population: in the Shanghai data (a different sensor, 98 Chinese hospital in-patients, 88 with type 2 diabetes, 4,012 pairs) MARD is 13.9 %, similar to the trial's. The average error is not similar: 7.4 % too low against 1.3 %. No trait predicted error there (60 tests). [check this last claim against `demographics_deep_stats.json` before the build]

- R5.3 Who the reports come from. (Moved here from R3.)
  - Point: the reports reach groups that the trial does not cover, and as far as their fields go they also show no difference by age or sex.
  - Numbers. Base: the 39,667 serious reports about a wrong reading.
    - About half record an age (49 %; 19,462 reports) and 4 in 10 record a sex (41 %; 16,356 reports). Most of these come from one maker: Dexcom fills in age in 93 of 100 of its reports in this set, Abbott in 19 of 100.
    - Where age and sex are recorded: the middle age is 54, half are female (51 %), and about 1 in 8 is under 18 (12 %).
  - Numbers. Base: all CGM reports of any kind that record an age (about 2.48 million of 3.38 million; 2.33 million of them from Dexcom).
    - About 1 in 6 concerns a child under 18 (17.5 %). More than 1 in 4 concerns a person aged 65 or over (28 %).
    - The trial has no children, and 1 participant in 12 is aged 65 or over (8 %).
  - Race or ethnicity is almost never recorded: about 3 in 1,000 of all 3.38 million reports, and 2 to 3 in 100 of the 123,607 serious reports.
  - How far off the sensor was, and in which direction, differed little by age or sex in the reports.
  - What this shows: reported failures reach children and older adults, groups our trial data cannot speak for. What it does not show: that any group's sensors fail more. The fields are too empty for that, and reports are not rates.

- R5.4 Table S1 in context.
  - Point: the five findings are what remained after many analyses. Table S1 lists every analysis we ran, with its question, its method and what came out, so the reader can see what was tried.
  - It names the ones that did not change the conclusions: rate of glucose change, time of day, study site, error grids, country of report, the earlier fault families.

## Dataset and Methods (first prose version 2026-11-21: about 1,540 words, 13 paragraphs, Table 1, Figure 1. The plan was 950 words.)

First version notes:
- Headings follow the rubric: 2.1 Study design, 2.2 Dataset, 2.3 Computational workflow (reading the reports, measuring the working sensor, simulating decisions), 2.4 Evaluation.
- From the teammates' draft: the full name of MAUDE and the wording of the midterm question. Their Methods section is empty.
- References still to add to `REFERENCES.md`: Qwen 2.5 (the language model), the Benjamini-Hochberg method.
- Left out of the text on purpose: Abbott's "comparison device" wording, the two downloads of the reports, the model's detailed settings, the bootstrap seeds. They are in the repository.
- Access dates for the trial data and the Shanghai data are not in the text yet (gap G6).
Facts for this section, each with its source file and line: `docs/paper/METHODS_FACTS.md` (built 2026-11-21). Read its five flags before writing:
- The texts that were read come from the second pull (FDA bulk files, data of 2026-10-21). The first pull through the openFDA service was on 2026-10-19. Both hold the same 3,382,071 reports.
- The 287 reference reports are not a random sample. They are the newest 50 malfunction reports and the newest 50 death or injury reports per maker.
- "68 in 100 typed glucose values within 5 % of the sensor reading" includes the run-in weeks.
- Write "407 single-trait tests", not "61 traits times 7".
- Median days of data per participant: 244 from first pair to last pair (used in M2), 235 counting days with sensor data.
- M1 Design. Three sources, each answering one part of the question: failure reports (what errors are reported), trial data (errors in normal use), simulation on the trial traces (which decisions change at which error). Figure 1.
- M2 Data sources (Table 1). REPLACE-BG: 226 adults with type 1 diabetes, Dexcom G4, 26 weeks; one case = one participant, who contributes many pairs. The 226-person pair set covers the run-in and the 26 randomised weeks (median 244 days per person). Shanghai: 112 patients, Abbott flash sensor, comparator only. FDA MAUDE: reports 1992-03 to 2026-09, pulled through the openFDA service on 2026-10-19; one case = one report; one event can produce several reports. Source, version and access date for each [pending, from Artemy].
- M3 Inclusion. Trial pairs: a fingerstick from the meter log, not used to calibrate the sensor, inside the study window, matched to the nearest sensor reading [window pending]: 168,990 of 475,502 candidate pairs. Reports: all CGM product codes; texts read = all 118,462 death or injury reports plus 6,137 sampled malfunction reports; a pair needs both values stated.
- M4 Responsible use. Public, de-identified data; data-use terms [pending]; no participant-level rows in the repository. Representation: adults only, 94 % White (trial); Chinese adults from two hospitals (Shanghai); reports are voluntary and cannot give rates.
- M5 Reading the reports. Coded fields counted first. Texts: text patterns, then a local open-source language model filling a fixed form [model, version, settings pending]; prompt in the repository. Checked against 287 reference reports. Their labels were written by an AI reviewer (Claude Opus 5.5, high reasoning setting). One author (Artemy) then read 100 of the 287 one by one and found no label to change. Agreement of the pipeline with the reference set (kappa = agreement beyond chance, 1 = perfect): 0.77 for fault type, 0.75 for severity. Patterns alone then run over all 3.38 million reports. Two checks of the patterns, each named for what it measures: they find 89 in 100 of the pairs the model finds; and of 100 random malfunction-only pairs read against their texts by an AI reader, 97 were right and none was wrong (3 unclear; 95 % interval 91.5 to 99.0).
- M6 Measuring the working sensor. Error = (sensor - meter) / meter. MARD, bias, 20/20 agreement, by glucose range. One sentence on how ranges are set: by the average of the sensor and meter value. The reason is given in Results 3.2. Misclassification at 70 and 180. Lag, wear day, 680 trait tests with Benjamini-Hochberg correction. 95 % intervals by bootstrap over participants.
- M7 Simulation, decision model. The recorded sensor trace is taken as true glucose. A fault changes what is displayed. Each recorded use of a participant's own dose calculator is recalculated with the displayed value and that person's settings. The display is defined here with the lines used: low alerts under 70 and under 54 mg/dL, high over 180 mg/dL; an episode = 15 minutes or more beyond a line.
- M8 Simulation, faults. Constant bias from 0 to -80 %. Three faults sized from the report pairs, in episodes of 2, 6 and 12 hours, 200 random starts per participant. Sugar rule: 15 g when the display is under 70, at most every 15 minutes. Glucose does not respond to the changed treatment.
- M9 Evaluation and software. Primary result: the error-to-decision curve. Comparison: where a working sensor and reported failures sit on it. Sensitivity checks. Python 3.11 and packages; local model runner; scripts and Table S1. One sentence on the change from the midterm plan: its question (misclassification at 70 and 180) is answered in R2.3; the report reading and the fault simulation were added to it.

## Introduction (about 800 words, 6 paragraphs)
Reference numbers in square brackets point to `docs/paper/REFERENCES.md`.
- I1 The problem and who is affected. People who take insulin read their glucose from a CGM and dose from it. Since 2016 the FDA allows dosing from a CGM without a confirming fingerstick, and REPLACE-BG, the trial used here, tested exactly that. A wrong reading therefore goes straight into a dose. One sentence here on what the wearer sees and hears (the display): the current glucose number, a trend arrow, a graph of the last hours, and alerts when the number crosses a low line or a high line.
- I2 What a wrong sensor does. Abbott began a recall of FreeStyle Libre 3 sensors on 24 November 2025 (Abbott's own term: "medical device correction"): about 3 million sensors in the US (Abbott's figure) could read falsely low. The FDA classified it as a Class I recall, the most serious class, on 13 January 2026 and announced this on 4 February 2026. Its notice lists 860 serious injuries and 7 deaths reported as of 7 January 2026. People ate carbohydrate they did not need or skipped insulin.
- I3 What is known about accuracy. Accuracy is reported as MARD against a reference. For the trial's sensor: 9.0 % against a lab reference in clinic, 11.3 % against a home meter (Bailey 2015). The FDA iCGM criteria set thresholds by glucose range. One average says nothing about which decision goes wrong. The reference meter has its own allowed error (ISO 15197).
- I4 What is known about error and decisions. Simulation studies link error size to outcomes: Kovatchev 2015 [49] (56 pump users, seven error levels, lows and highs rise sharply above MARD 10 %); Breton and Kovatchev 2010 [53] and Campos-Nanez 2017 [54] for meters. They study the random error of a working device. None simulates a sensor that reads far too low for hours.
- I5 What is known from failure reports. Shapiro 2017 [48]: 25,966 Dexcom complaints, 415 with both values, 55 % off by 100 mg/dL or more. Krouwer 2025 [63]: 281,963 CGM reports in 2022, inaccuracy a leading cause. Neither links the error sizes to treatment decisions.
- I6 The gap, the question, the contribution. No study puts the error of a working sensor and the error in reported failures on one scale of treatment decisions. Research question. Three contributions: (1) an error-to-decision curve from the real records of 226 people; (2) error sizes and fault types from 207,771 report pairs, on the same axis as trial error; (3) a simulation of the three reported faults.

## Discussion (about 800 words, 5 paragraphs)
- D1 The answer. For a sensor that reads steadily too low, dose decisions begin to change when it reads about 12 % too low; what the display shows changes from the first step. A working sensor reads 1.3 % too low on average, a tenth of that margin. But its single readings scatter: about 1 reading in 9 was 20 % or more too low, and about 3 in 10 meter-confirmed lows were not shown as low at that moment. In reported failures the typical sensor reading was 69 to 77 % too low, about six times beyond the margin. And they are a different kind of error: three faults, each breaking a different decision. So "how large" answers the question only for a steady error. For the reported faults, where glucose truly is and which way the sensor is wrong decide which decision fails. Making the false low smaller or larger (62 to 77 % too low) barely moved the outcomes. A hidden low cannot be produced by a sensor that reads too low at all.
- D2 Against published work. (a) Our MARD of 13.3 % is 2 points above the closest like-for-like figure (11.3 %, home use, meter reference); possible reasons to state briefly. (b) Published low-alert detection is 86 to 91 % with a time window. Counted the same way, ours is 81.5 % for meter values under 70 and 89.9 % for meter values under 54; the point-in-time figure (69 % shown) is the stricter measure. (c) Kovatchev's threshold of MARD 10 % is consistent with scatter mattering in a working sensor; our curve adds bias, which those studies left out. (d) Shapiro's error sizes from 2015 to 2016 match ours: reported failure sizes look stable across a decade and two manufacturers. (e) The FDA's 2016 summary for an earlier Abbott sensor already recorded a negative bias and false lows.
- D3 What it means. Fault type, not one accuracy number, tells which decision fails: a false low prompts unneeded sugar and withholds insulin; a hidden low removes the alert. A fingerstick check when a reading does not match symptoms, and extra care on wear day 1, are supported by the data. The reports include children and adults over 65, who are absent or few in the trial data, and almost never record race.
- D4 Limits (four). Reports are voluntary and selected, so they give the size and type of reported failures, not rates, and mostly concern newer sensors than the trial's. The reference is a home meter with its own error, which widens scatter and the missed-low share more than it moves bias (adding meter error at the ISO limit raises MARD by 1.9 points). The simulation counts changed decisions and does not let glucose or the person respond, so it cannot give harm, and its sugar counts are an upper bound. One sensor generation in mostly White adults; the text reader was checked against a reference set labelled by an AI; one author read 100 of its 287 reports and changed none.
- D5 Next step. Run the three faults through a validated physiological simulator, so that changed decisions become glucose outcomes. Second: paired sensor-meter data for current sensors in children and older adults.

## Abstract and Conclusion
- Abstract (200 to 250 words): problem (one sentence), question, the three data sources with sizes, the approach, the four message lines with their numbers, what it means, the main limit (reports are not rates; simulation counts decisions, not harm).
- Conclusion (about 180 words): the answer in two sentences; the contribution (working-sensor error and reported-failure error on one decision scale; three faults simulated); the main qualification.

## Statements
- Data and code availability: dataset sources and their terms; repository link and the commit graded; raw data and per-participant tables are not in the repository, and why.
- AI-assisted work: tools and what each was used for (coding, analysis, drafting; a local language model as a method for reading reports); how results were verified (number check against source files, every reference opened, 100 of the 287 reference labels read one by one by one author with none changed, author review of each section).
- Author contributions: [from Artemy].

# Fix list for the repository (found by the reference check, not yet fixed)
- `analysis/ACCURACY_V2.md` section 10: Bailey 2015 11.3 % is a home-use figure against a meter, not a clinic figure.
- `README.md`: "No redistribution" for the Jaeb data is not the wording of the dataset terms.
- Recall wording everywhere: the action began 24 November 2025; the FDA classified it Class I on 13 January 2026 and said so publicly on 4 February 2026; 860 serious injuries and 7 deaths is the FDA figure as of 7 January 2026. Write "recall". Do not write "a correction, not a removal": Abbott calls it a "medical device correction", but the FDA notice says it removes devices. Source: `fda-maude/results/RECALL_DATE_CHECK.md`.
- `analysis/ERROR_DRIVERS.md` line 13 and `docs/paper/FACT_SHEET.md` line 265: the lag-corrected result under 54 rests on 2,365 pairs from 202 people, not 2,133.
- `fda-maude/results/text/REGEX_V2_FULL_CORPUS.md`: the text says 16,426 and 17,426 pairs; its own table and a re-count give 16,434 and 17,429.
- Recall count: add event 99765 to the drop list in `fda-maude/scripts/config.json` and rebuild `recalls_cgm.csv` (see G3). The 22 places that state 32 events are then right as they stand.

# Rules fixed for the writing (from the fact sheet, 2026-11-20)
- Headline pair set: all 226 participants. The 77-person arm is the check.
- "False low" and "hidden low" shares use one form everywhere, changed 2026-11-20 to the question form: "when the meter was not low, how often did the sensor show a low?" and "when the meter was low, how often did the sensor fail to show it?". Same question for the trial and for the reports (`analysis/TAIL_COMPARISON.md`). Reason: it reads as a plain question and it is the same measure as the 31 % in R2.3. The share-of-all-pairs form (false low 36 % Abbott, 17 % Dexcom) is not used in text. The memos use three different denominators; do not mix them.
- Withheld corrections are given as a share of the corrections that were needed (about 1 in 7 at 20 % too low), not as a share of all calculator decisions (7 %). Same data. Reason: the reader does not need to know that only about half of calculator uses include a correction.
- The bias sweep and the three-fault outcomes are reported as the median participant with quartiles. Bootstrap intervals exist only at -10, -20 and -30 %.
- Sex gap interval: cite one stats file (`demographics_deep_stats.json`: +2.0 to +6.0).
- Glucose ranges, two kinds, never mixed in one sentence. "In the range under 54" = the average of sensor and meter is under 54 (used for MARD by range, for the 6.5 % too low, and for the sex gap). "When the meter was under 70" = sorted by the meter alone (used for true lows shown or not shown, and for the three faults). Methods gives the reason once.
- Reported error when the sensor read low: always the median over pairs that read low (77, 69 and 69 % too low). Never 66 %.

# Stage 3: gap list (waiting for Artemy)
| # | Gap | Size | State |
|---|---|---|---|
| G1 | Low detection with a 15-minute window, to compare with published 86 to 91 % | small | done: `analysis/LOW_DETECTION_WINDOW.md` |
| G2 | Precision of the text patterns against the reference set (the 191,112 malfunction-only pairs rest on it) | small | done: `fda-maude/results/text/PATTERN_PRECISION.md`. An AI reader read 100 random malfunction-only pairs: 97 right, 3 unclear, 0 wrong (95 % interval 91.5 to 99.0). Against the reference set: 74 of 74 pattern pairs right; 3 of 77 reference pairs missed. In 23 of the 85 sampled Abbott pairs the report calls the reference "the comparison device", not a meter (see the word list). Artemy confirmed on 2026-11-21 that this counts as the meter |
| G3 | Recall records: memos say 32 events, `recalls_cgm.csv` holds 33 | tiny | done: `fda-maude/results/RECALL_COUNT_CHECK.md`. The 33rd event (99765, added by the refresh of 2026-10-26) is Medtronic CareLink software that gives wrong insulin dose settings. No glucose reading is wrong. Paper uses 32 events, 95 records (7 Class I, 23 Class II, 2 old events with no class). Confirmed by Artemy 2026-11-21. Repo follow-up: add 99765 to the drop list in `fda-maude/scripts/config.json` and rebuild the CSV (with G9) |
| G4 | Check of 100 reference reports: who did it, how, any agreement number | from Artemy | done: Artemy read 100 one by one; no label changed |
| G5 | Which AI labelled the 287 reference reports, named for the AI statement | from Artemy | done: Claude Opus 5.5, high reasoning setting |
| G6 | Dataset access dates and versions | from Artemy | later |
| G7 | Author contributions | from Artemy | later |
| G8 | Build Table 1, Figure 1, Figure 2 (curve with marks), Figure 3, Table 2, Table 3 | medium | done 2026-11-21: all seven items are in `docs/paper/figures/` and `docs/paper/tables/`. After Artemy's review the same day: Table 2 became Figure 5 plus Table S2, Table 3 became Table S1, Figures 2 and 4 got less text, Table 1 got shorter |
| G9 | Repository wording fixes (list above) and the memo slips in `docs/paper/FACT_SHEET.md` section D6 | small | after the paper text is fixed |
| G10 | Confirm every line marked [check] in Results (what each share is a share of; 66 or 69 % in the message; the 20/20 rule) | small | done: `docs/paper/CHECKS.md`. All fixes are written into the Results lines above (2026-11-21) |
| G11 | Page budget. The first Results version is about 2,480 words of text and 470 words of captions (after the number-check fixes), against 1,300 planned. With Figures 2 to 5 that is about 4.5 pages, where the rubric suggests about 2. Guess: the paper still fits 10 pages at 10.5 pt if Introduction and Discussion stay near 650 words each. | medium | measure real pages at the first document build, then cut or resize |
| G15 | Number check of the Results prose: `docs/paper/CHECKS_RESULTS_PROSE.md` (80 rows). 4 must-fix and 13 should-fix items, all applied to `PAPER.md` on 2026-11-21 except should-fix 10 (small) and 12 (the text already speaks only of how far off the sensor was). Open for Artemy: message line 4 and the R5 heading do not name fast-changing glucose | small | done, one point open |
| G14 | Supplement. Artemy wants Table S1 outside the page count. The rubric does not mention supplements. Options: put it after the references in the PDF, or keep it in the repository and link it. | from Artemy | open |
| G12 | Date the Libre 3 recall was classified Class I: `docs/paper/REFERENCES.md` says 2026-02-04, `recalls_cgm.csv` holds 2026-01-13 (posted 2026-01-14) | tiny | done: `fda-maude/results/RECALL_DATE_CHECK.md`. Classified 13 January 2026 (FDA enforcement data); 4 February 2026 is the day the FDA updated its public notice. If a reviewer cannot find the January date, the fallback is "classified in January 2026" |
| G13 | Accuracy by range under three sortings (meter alone, sensor alone, average) for all 226 participants | small | done: `analysis/ACCURACY_BY_RANGE_SORTING.md`. Written into R2.2 |

# Stage 3: objection list

What a careful reader will push back on, and the one place in the paper that answers it. Each answer appears once.

| # | The reader says | Our answer | Where |
|---|---|---|---|
| O1 | "You treat the sensor trace as true glucose, but the sensor has its own error." | We repeated the main run with the meter as the true value (15,034 decisions, 67 people). The effect points the same way and is larger. | R1.2 |
| O2 | "People do not follow the sensor blindly." | In the trial arm that dosed from the sensor, 68 in 100 typed glucose values were within 5 % of the sensor reading. The sugar counts are stated as the most it could be. | Methods M7, Limits |
| O3 | "Reports are complaints. They cannot tell you how often sensors fail." | We use them only for how far off the sensor was and which kind of fault. We give no rates. Said once. | R3.3, Limits |
| O4 | "The reference meter has error too." | Adding meter error at the allowed limit (ISO 15197) raises MARD by 1.9 points. It widens scatter; it barely moves the average direction. | Limits |
| O5 | "Published studies say sensors catch 86 to 91 % of lows. You say 3 in 10 are not shown." | Counted their way (any reading within 15 minutes) ours shows 81.5 % of lows under 70 and 89.9 % of lows under 54. Our figure is for the moment of the check. | R2.3, Discussion D2 |
| O6 | "Your MARD of 13.3 % is worse than the published value for this sensor." | The like-for-like published value (home use, meter reference) is 11.3 %. The 9.0 % is against a laboratory analyser. | R2.1, Discussion D2 |
| O7 | "An AI model read the reports. How do you know it read them right?" | Fixed form; a number is kept only if it appears word for word in the text; agreement with 287 reference reports (kappa 0.77 and 0.75); one author read 100 of them; of 100 random pattern pairs read against their texts, 97 were right and none wrong. | Methods M5 |
| O8 | "With 680 tests something will look significant by chance." | Correction for many tests. 69 passed before it (34 expected by chance), 1 after it. | R5.2 |
| O9 | "The trial sensor is from 2015. The recalled sensor is a different one." | The curve of R1 depends on the dose calculator and on real glucose traces, not on the sensor model. The reported errors come from current sensors. | Methods M1, Limits |
| O10 | "You assumed how long a fault lasts." | Unneeded sugar and withheld doses per hour of fault are the same for 2, 6 and 12 hours, so those conclusions do not rest on the length. False low alerts per hour are not the same (0.49, 0.20 and 0.13), so the paper does not claim it for alerts (`docs/paper/METHODS_FACTS.md`, flag 2). | Methods M8 |
| O11 | "Why 180 mg/dL as the high line?" | With 200 the result is 59 % against 51 %. Same conclusion. | R1.2 |
| O12 | "Day 1 looks worse only because bad sensors are pulled early." | 92 % of the day-1 excess is the sensor settling. | R5.1 |
| O13 | "Sorted by the meter, this sensor reads too high at low glucose, not too low." | True: 29.8 % too high sorted by the meter, 22.5 % too low sorted by the sensor. We sort ranges by the average of both and say why. Our claim is that MARD is largest under 54 under every sorting (1.4 to 2.8 times the 70 to 180 range), not a direction. | Methods M6, R2.2 |
