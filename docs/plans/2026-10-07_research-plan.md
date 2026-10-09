# Research plan: when a failing CGM sensor changes a treatment decision

- Date: 2026-10-07
- Status: Draft 2. INTERNAL working plan (lead + AI). The team-facing version is 2026-10-07_team-brief.md. Folds in related work.pdf, research description.pdf, and the newer report draft.
- Course: BMEN 600, Group 24
- Research question: When a CGM is wrong, how wrong must it be before it changes what a patient does? (changed to match research description)
- Sub-questions (from the research description): (1) real-life accuracy, (2) accuracy by glucose level, (3) direction of error, (4) how much error flips a decision, (5) is harm spread evenly across groups, (6) would patients have noticed.

Terms used in this file:
- CGM = continuous glucose monitor. A small sensor under the skin. Reads sugar every few minutes.
- Fingerstick = a drop of blood on a test strip. We treat it as the "true" value.
- Pair = one CGM reading matched to one fingerstick taken at nearly the same time.
- Bias = average of (CGM minus fingerstick). Minus means the sensor reads too low.
- MARD = the sensor's average percent error. Lower is better. Under 10 percent is good.
- Lag = the CGM trails blood sugar by about 5 to 15 minutes. Uncorrected, lag looks like bias.
- Monte Carlo = run a simulation many times with random noise. Gives a range, not one number.
- MAUDE = the FDA's public database of medical device problem reports.

## 1. Intro and motivation

- People with diabetes dose insulin and eat sugar based on CGM readings.
- In late 2025 the FDA recalled about 3 million Abbott FreeStyle Libre 3 and 3 Plus sensors. They read too LOW. Low only.
- FDA count (Jan 7, 2026): 860 serious injuries, 7 deaths.
- Why harm happens: a false low makes people eat sugar they do not need, or skip insulin. Very high sugar and DKA (diabetic ketoacidosis, a dangerous acid build-up) can follow.
- Regulators knew Libre read low in 2016 (FDA approval document for Libre Pro). So "does Libre read low" is already answered.
- Our question is the next step: how much low error is dangerous? How close is normal error to that level?

## 2. Background and gap

What is known:
- CGMs are less accurate when sugar is low. MARD roughly doubles below 70 mg/dL.
- Libre reads low in many studies. One study: lower than the reference in 75 percent of pairs (Libre T2D 2022).
- Dosing from a CGM is safe below about 10 percent MARD (Kovatchev 2015). Replaying real data with added error is an accepted method.
- CGM error is lag plus drifting bias plus noise. Not plain random noise (Facchinetti 2010).
- Accuracy studies mostly cover adults. Many do not report ethnicity or sex (Freckmann 2023, numbers to verify).
- A case report (Kogai 2023) shows the harm path: false low, wrong treatment, DKA. The sensor had no visible defect.

What is missing:
- Mulley 2026 compared CGM and meter on REPLACE-BG, but only as two-week averages. No per-reading error by range.
- No full accuracy analysis on the Shanghai Libre data. The authors only noticed the low reading.
- No study links error size to a count of changed decisions, or tests several fault types on the same data.
- Subgroup harm: does the same error flip more decisions for some groups? Not studied.
- MAUDE papers on CGMs (two in 2025) are pre-recall. No post-recall analysis sorted by fault type.

Suggested sources from the related-work doc (18 sources; 9 still need author names for IEEE):

| Source | What it adds | Report section |
|---|---|---|
| Mulley 2026, Diabetic Medicine | Closest prior work. CGM vs meter on REPLACE-BG. Cite it and show how we go further. | 2, 3, 4 |
| Zhao 2023, Scientific Data | Shanghai dataset paper. Column guide. Notes Libre reads low. | 2, 3 |
| FDA SSED Libre Pro 2016 | Regulator knew about low bias in 2016. Reframes our question. | 1, 2 |
| Libre in T2D 2022 (PMC9639390) | 25,579 pairs. Libre low in 75 percent. -23 percent at 3 AM. Subgroup template. | 2, 4, 5 |
| Calibratable Libre, Frontiers 2025 | 1,907 outpatient pairs. MARD 18.3 percent, reads low. Uses consensus grid and Bland-Altman. | 2, 5 |
| Vaughan 2025 meta-analysis | Ten years of Libre accuracy in one citation. Worse when low or changing fast. | 2 |
| CGM in emergencies 2025 (PMC12018364) | MARD by range: 7.7 percent above 250, 13.9 percent below 70. Range cut-points. Wear day 1 worst. | 4, 5 |
| CGM in hypoglycaemia (PMC12890745) | 464 low-range pairs. How to split error by rate of change. | 4 |
| Children, Diabetes Care 2025 | Dexcom. MARD 15.8 percent, bias slightly HIGH. Direction differs by brand. | 2, 5 |
| Closed-loop home studies 2015 (PMC4649721) | 10,597 free-living pairs. MARD 14.2 percent. Fair baseline for REPLACE-BG. | 5 |
| Sinocare commentary, Frontiers 2026 | Results checklist: MARD by range, median error, bias, Bland-Altman, subgroups. | 4, 5 |
| Kovatchev 2015, DTT | Replay method. Safe dosing below about 10 percent MARD. Justifies our simulation. | 2, 4 |
| Breton and Kovatchev 2010, JDST | Earlier replay study for fingerstick meters. No link found yet. | 4 |
| Vettoretti 2015, IEEE EMBC | Model of daily patient decisions under sensor error. Source of treatment rules. | 4 |
| Facchinetti, Sparacino, Cobelli 2010, JDST | CGM error model: lag, drift, noise. Why we correct lag first. | 4 |
| FairGlucose 2026, arXiv | Averages hide subgroup gaps. Concept only, not about sensors. | 2 |
| Krouwer 2025, JDST | MAUDE coding scheme for CGM causes. Pre-recall Abbott vs Dexcom baseline. Web search capped at 500. | 4 (Phase 1) |
| Adverse events in diabetes devices 2025, JDST | Scale of MAUDE: over 1.6 million CGM reports 2019-2024. | 4 (Phase 1) |

Still to find (not covered by the related-work doc):
- REPLACE-BG trial paper (Aleppo 2017). Error grid origin papers (Clarke; consensus/Parkes) and what zones mean for treatment.
- ISO 15197 meter standard (about 15 percent error allowed).
- "Regression to the mean" pitfall in paired data. Compression (pressure) lows.
- Keep Kogai 2023 and Freckmann 2023. Draft already has Sameer 2020, Kubihal 2021, Facchinetti 2016 (not Facchinetti 2010). News and Cleveland Clinic: hook only, not scholarly.

## 3. Dataset and responsible use

| Dataset | Who is in it | Sensor | Size | Role |
|---|---|---|---|---|
| REPLACE-BG (Jaeb Center, US, 2015-16) | 226 adults, type 1 | Dexcom G4 | 14.8M CGM rows, about 600k pairs | PRIMARY |
| Shanghai T1DM/T2DM (Tongji University, China, 2019-21) | 112 hospital patients, 12 type 1, 100 type 2 | Abbott flash CGM (likely Libre H, confirm) | 128k CGM rows, 4,012 pairs | Comparator only |
| OhioT1DM | 12 adults, type 1 | Medtronic | 8 weeks each | Optional. Needs a signed data agreement |
| FDA MAUDE + recall database | Problem reports, mostly US | All CGM brands | Product code QLG, about 148k reports (a 2025 paper says 1.6M; check scope) | Phase 1 source |

One independent case: Phase 1, one MAUDE report or one recall record. Phase 2, one person. Pairs nest inside people, so a pair is NOT a case.

Privacy and data-use terms:
- REPLACE-BG and Shanghai are public and de-identified. Shanghai is CC BY 4.0. Check and cite each licence.
- MAUDE is public. Reports have no names. Do not try to re-identify anyone.
- Raw data stays out of git (919 MB, gitignored). Each teammate downloads their own copy.

Bias limits (who our results do and do not cover):
- REPLACE-BG: median age 43, 94 percent White, 77 percent with a degree, well controlled (HbA1c 7.3 percent).
- Shanghai: median age about 60, all Chinese, hospital in-patients, poorly controlled (HbA1c 8.5 percent).
- No children in either. We cannot claim results for children, non-White, or low-income groups.
- Neither dataset uses the recalled Libre 3. We say nothing about the recalled Abbott lots. That data is not public.
- Subgroup results are exploratory. Some groups are small.
- Dexcom G4 was calibrated with fingersticks twice a day. So the reference is not fully independent.
- MAUDE is voluntary reporting. Counts show reporting behaviour, not true failure rates.

## 4. Methods and evaluation

### Phase 1: FDA recall and MAUDE report mining (preliminary, guides Phase 2)

Note: the research description does not mention Phase 1. We keep it. Lead to confirm.

Steps:
1. Decide: openFDA API vs browser robot. API first. The MAUDE web search is capped at 500 records (Krouwer 2025).
2. Pull CGM reports for Abbott, Dexcom, Medtronic. Save raw JSON (gitignored).
3. Clean: remove duplicates, pull out date, brand, outcome, narrative text.
4. LLM step: label each narrative with a fault type and a severity. Start from Krouwer's cause categories. Save the prompt.
5. Hand-check a random sample of labels (guess: 100 reports) and report the agreement rate.
6. Count by fault type, brand, month. Compare with the pre-recall counts in Krouwer 2025. Write a plain-language summary.

Main result: a table of real CGM fault types with how common and how harmful each one is.
Comparison group: Abbott vs Dexcom vs Medtronic. Also before vs after the recall date.
How we avoid misleading results:
- Say clearly: counts are safety signals, not failure rates. No denominator exists.
- Report the LLM label error rate from the hand-checked sample.
- Scope stays open until we see the data. First look decides the exact questions.

### Phase 2: CGM accuracy, then failing-sensor simulation (main)

Part A, accuracy by glucose range ("Half 1" in the research description):
1. Filter REPLACE-BG to each person's study window (day 0 to end of trial).
2. Build CGM-fingerstick pairs (within 5 min for meter, within 10 min for calibrations).
3. Estimate the lag from the data and correct for it. Otherwise lag looks like bias. (added from research description)
4. Compute bias, MARD, and consensus error grid zones by glucose range. Bland-Altman plots, adjusted for repeated measures.
5. Check what drives error: rate of change, wear day, age, sex, BMI, glucose control. (added from research description)
6. Repeat on Shanghai as a smaller check with an Abbott-type sensor.

Part B, failing-sensor simulation ("Half 2"):
1. Take real CGM traces from REPLACE-BG.
2. Apply a simulated fault to the trace. Keep the fingerstick as truth.
3. Apply simple treatment rules to the clean trace and to the faulty trace.
4. Count how many decisions flip. Per person. Monte Carlo: add realistic noise and repeat many times.
5. Compare flip rates across patient groups. Count how often each group did a fingerstick check. (added from research description)

First run (from the research description): constant low bias of 10, 20, 30 percent, plus noise. This mimics the recall.
Fault list stays OPEN. Phase 1 picks which other types we run.

| Fault type | What it looks like | Guess at real cause |
|---|---|---|
| Constant low bias | Every reading X percent too low | The Libre 3 recall fault |
| Drift over wear days | Error grows each day the sensor is worn | Coating or carbon build-up |
| Added noise | Readings jump around more than normal | Poor sensor contact |
| Dropouts / gaps | Readings go missing for minutes or hours | Lost signal, sensor fell off |
| Lag | Readings trail the true value by many minutes | Slow fluid exchange under skin |
| Pressure-induced lows | Short sharp false lows, often at night | Lying on the sensor |

Treatment rules (from the research description; team can refine, see section 8):
- Treat low sugar if CGM is below 70 mg/dL.
- Give a correction insulin dose if CGM is above 200 mg/dL. (changed to match research description; was 180)

Main result: percent of treatment decisions that flip, per fault type, per fault size, per patient group.
Target shape of the headline: "a 20 percent low bias changes 1 in 8 decisions". (example wording, not a result)
Comparison group: the same traces with no fault added (the clean trace).
How we avoid misleading results:
- Repeated measures: one person gives thousands of pairs. Report per-person results. Show the spread across people, not one pooled number.
- Low-range binning pitfall: group by fingerstick value and the sensor looks too HIGH. Group by CGM value and it looks too LOW. This is a maths effect. Fix: plot error against the average of the two readings (Bland-Altman), or use an error grid.
- Pre-enrolment rows (7.4 percent of CGM rows) are cut. Bad meter values (16 below 20 mg/dL, 34 at 600 or above) are removed.
- Uncertainty: show per-person spread (box plots or ranges) for every headline number.

## 5. Preliminary results (what we already have)

Already done on real data. Any of these could become the required figure. Final pick is being made separately.

| Finding | Number | Possible figure |
|---|---|---|
| REPLACE-BG has enough low-range pairs | 6,600 calibration pairs below 70 mg/dL; Shanghai has 37 | Table |
| Both sensors read a bit low in normal and high range | Dexcom G4: 3-5 percent low. Shanghai: 6-13 percent low | 09_accuracy_by_range.png |
| MARD roughly doubles below 70 mg/dL | 10-14 percent overall; 19-42 percent below 70 | 09_accuracy_by_range.png |
| Low-range bias flips sign with grouping | Below 54: +23 to +33 percent by fingerstick; -23 to -32 percent by CGM | Two-way range table |
| People differ a lot | Per-person MARD 9-23 percent, median 13.9 percent | 10_per_participant_mard.png |
| Error grid zones | Dexcom G4 meter pairs: 87.5 percent zone A, 1.2 percent zone D | 08_cgm_vs_reference_scatter.png |

Baselines to compare against (from the related-work doc): Kovatchev safe-dosing limit 10 percent MARD. Home study 2015: MARD 14.2 percent. Emergencies 2025: 13.9 percent below 70. Libre T2D 2022: -23 percent at 3 AM.

Did the preliminary result change the plan? Yes:
- The README's biggest worry (too few low-range pairs) is resolved. REPLACE-BG is enough. Shanghai moved to comparator only.
- The sensor already reads 10-16 percent low in the 54-69 band as the patient sees it. The simulation must start from this, not from zero. This matches outcome 1 in the research description ("CGMs already read low").
- Simulation will run per person, not on pooled data.

## 6. Teamwork and project plan

Section owners (from team notes):
- Sections 1 and 2 (Intro, Background): Mahlaqa, Laaraib.
- Sections 3 and 4 (Dataset, Methods): Myleni, Artemy, Mirha.
- Sections 5 and 6 (Results, Teamwork): everyone.

Timeline to the plan deadline:

| Date | What |
|---|---|
| Oct 7 (Tue) | This draft. Share with team. Agree on the research question. |
| Oct 8-9 | Owners write their sections in plain language. Pick 6+ sources from section 2. |
| Oct 10-12 | Fill Methods, Results, Teamwork. Pick the figure. Convert references to IEEE. |
| Oct 13, 1 PM | Online team meeting. Polish full draft. Fix all placeholders. Cut duplicate text. |
| Oct 14-15 | Final read. Check page limit (6 pages). Check repo README and code run. |
| Oct 16, 11:59 PM | Submit PDF + GitHub link. |

Rough phases after the plan (guess at dates):
- Late Oct to early Nov: Phase 1. Pull and label MAUDE reports. First counts. Pick fault types for Phase 2.
- Nov to Dec: Phase 2. Lag correction, final accuracy tables, fault simulation. Then final report, figures, code clean-up.

## 7. Draft feedback

Moved to docs/team-docs/2026-10-07_draft-feedback.md (local only, not in git).

## 8. Open questions (team must decide)

- Treatment rules: 70 and 200 are the starting point. Also use real pump dose events? Or a simplified Vettoretti-style model?
- Fault types: first run is 10/20/30 percent low bias plus noise. Which other types after Phase 1? Pick a fallback set now.
- Does Phase 1 (MAUDE) stay in the report? The research description does not mention it. Lead to confirm.
- How do we estimate lag from the data? guess: shift the CGM by 0 to 15 min and keep the best match.
- How do we measure "would patients have noticed"? guess: fingerstick checks per day, per person, per group.
- Accuracy set details: study window cut (day 0 or randomisation)? Meter pairs, calibration pairs, or both?
- openFDA API or browser robot for MAUDE? The 500-record cap points to the API.
- Do we need OhioT1DM at all? If yes, who signs the agreement? Team of 5 vs the stated 3-4: who asks the instructor?
