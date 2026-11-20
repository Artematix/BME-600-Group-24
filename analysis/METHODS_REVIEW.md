# Methods review: CGM accuracy and failing-sensor simulation (2026-10-26)

Purpose: for each part of our analysis, say what the current research standard is, what our code does now, and what to add, change, keep or skip. Written as a methods reviewer would. Course-project level: defensible, not over-built.

Files reviewed: `RESULTS.md`, `SIMULATION_RESULTS.md`, `REPRODUCIBILITY.md`, the pairing, accuracy and figure 09/11 code in `explore_raw_data.py`, all of `bias_simulation.py`, and sections 2 and 4 of `docs/plans/2026-10-07_research-plan.md`. Raw data was not opened.

Key terms:
- CGM = continuous glucose monitor. Reference = the fingerstick meter value we treat as truth. Pair = one CGM reading matched in time to one reference.
- MARD = mean absolute relative difference. The average percent gap between CGM and reference. Lower is better.
- Bias = mean of (CGM minus reference). Negative means the sensor reads low.
- 15/15, 20/20, 40/40 = share of pairs within 15 mg/dL (when glucose is low) or 15 % (when higher). Same idea for 20 and 40.
- iCGM = the FDA "integrated CGM" rule of 2018. It sets accuracy limits a sensor must meet.
- Error grid = a chart that sorts each pair into risk zones A (fine) to E (dangerous). Versions: Clarke (1987), Parkes or "consensus" (2000), Surveillance (2014), DTS (2024).
- CI = confidence interval. The range the true number likely sits in. Bootstrap = re-sampling the data many times to get a CI.
- ROC = rate of change of glucose, in mg/dL per minute.
- LBGI / HBGI = low / high blood glucose index. Risk scores computed from a glucose trace. TIR = time in range (70-180 mg/dL).
- Calibration = a fingerstick typed into the receiver to correct the sensor. The Dexcom G4 needs 2 per day.
- Mixed model = a regression that knows which readings come from the same person.

## 1. Accuracy metrics

Standard:
- MARD is the headline number, but it depends on study design, the glucose mix and the reference quality. It must come with range-split metrics and CIs [Reiterer 2017, https://pmc.ncbi.nlm.nih.gov/articles/PMC5375072] [Kirchsteiger 2015, https://pmc.ncbi.nlm.nih.gov/articles/PMC4667347].
- The FDA iCGM rule bins by the SENSOR value, not the reference. Limits, as a lower one-sided 95 % bound: CGM below 70: 85 % within 15 mg/dL and 98 % within 40 mg/dL. 70-180: 70 % within 15 % and 99 % within 40 %. Above 180: 80 % within 15 % and 99 % within 40 %. All pairs: 87 % within 20 %. Also: no CGM below 70 when the reference is above 180, and the reverse [21 CFR 862.1355, https://www.law.cornell.edu/cfr/text/21/862.1355].
- Error grids: the Parkes grid is part of ISO 15197:2013 and is the usual choice. Clarke is older and has hard zone edges [Parkes 2000, https://doi.org/10.2337/diacare.23.8.1143] [Clarke 1987, https://doi.org/10.2337/diacare.10.5.622]. Newer options: Surveillance Error Grid [https://www.diabetestechnology.org/seg.shtml] and the DTS grid [Klonoff 2024, https://scholarworks.indianapolis.iu.edu/items/12f2af06-9bc9-45a9-ba61-941eaf89815c].
- Bland-Altman: plot the difference against the MEAN of the two methods. Adjust the limits of agreement for many pairs per person [Bland & Altman 2007, https://pubmed.ncbi.nlm.nih.gov/17613642/].
- Reporting checklist for CGM accuracy studies: design, device use, comparator, procedures, statistics [Freckmann 2023, https://pubmed.ncbi.nlm.nih.gov/37599389/].

What we do now:
- Bias, MARD, "within 20 %/20 mg/dL", Clarke and Parkes zones (type 1 version, own code, checked at 24 points), by range. Our 20/20 rule equals the usual one with a 100 mg/dL cut (20 mg/dL below 100, 20 % above).
- No CIs anywhere. No 15/15 or 40/40. No table by CGM value in iCGM form. Per-person MARD only for calibration pairs. Figure 09 mixes two axes: counts and MARD by reference, bias by average.

Recommendation:
- Add: an iCGM-style table (15/15, 20/20, 40/40 by CGM value, 3 ranges, lower 95 % bound). Reason: it is the regulator's yardstick and it matches "what the patient sees".
- Add: bootstrap CIs by participant for every headline number. Resample people, not pairs. Reason: pairs inside one person are not independent [cluster bootstrap, Field & Welsh 2007, https://doi.org/10.1111/j.1467-9868.2007.00593.x].
- Change: one axis per figure. Keep Parkes as the only grid in the main text; Clarke goes to an appendix. Keep: bias by average.

## 2. Reference handling

Standard:
- Pair within 5 min. Pivotal studies use a 0 to 5 min window [example protocol, https://cdn.clinicaltrials.gov/large-docs/22/NCT04436822/Prot_000.pdf].
- Fingersticks used for calibration are excluded from accuracy pairs. The sensor is corrected with those same values, so they are not an independent test [Hirota 2020, https://pmc.ncbi.nlm.nih.gov/articles/PMC6944838] [Dexcom 10-day study, https://doi.org/10.1089/dia.2017.0072].
- Readings at the display limits (39 and 401 for the G4) are excluded or flagged [same Dexcom study].
- Meter error: ISO 15197:2013 allows 95 % of meter results within 15 mg/dL (below 100) or 15 % [summary, https://pmc.ncbi.nlm.nih.gov/articles/PMC5851221/]. Our meter (Contour Next) is among the best: lowest MARD of 3 meters in a hospital test [https://pmc.ncbi.nlm.nih.gov/articles/PMC4455362]; 3.1 % in a small Stanford study [https://stanfordhealthcare.org/publications/317/317436.html].
- Home-use MARD against a meter is reported separately from lab MARD. G4 with 505 software: 9.0 % vs lab, 11.3 % vs meter [Bailey 2015, https://pmc.ncbi.nlm.nih.gov/articles/PMC4604574].

What we do now:
- Meter pairs: nearest CGM within 5 min either side. Calibration pairs: the CGM reading up to 10 min before the calibration. Reference kept if 20-600 mg/dL. Clocks noted as separate. Clipped CGM values (39, 401) are kept and not flagged.
- Problem: the meter log also holds the calibration fingersticks. So "meter pairs" include them. guess: about 1 in 4 meter pairs is a calibration. The headline MARD (10.4 %) partly tests readings the sensor was about to be corrected with.

Recommendation:
- Change: tag each meter reading that matches a calibration record (same person, same value, within 10 min). Headline = non-calibration pairs. Report calibration pairs separately as "pre-calibration accuracy".
- Add: a window sensitivity check (2.5, 5, 10 min). Add: a count of pairs with CGM at 39 or 401, and results without them. Keep: the 20-600 filter. State meter error in the limits.

## 3. Error drivers

Standard:
- Lag: blood-to-tissue delay is 5-6 min [Basu 2013, https://pmc.ncbi.nlm.nih.gov/articles/PMC3837059/]. Whole-sensor delay was about 9.5 min (SD 3.7) for 2015-era sensors, estimated by shifting the CGM trace in time against the reference [Schmelzeisen-Redeker 2015, https://pmc.ncbi.nlm.nih.gov/articles/PMC4667340]. Usual estimate: the time shift that gives the lowest MARD.
- ROC bins: below -2, -2 to -1, -1 to 1, 1 to 2, above 2 mg/dL/min [G6 study table, https://pmc.ncbi.nlm.nih.gov/articles/PMC6399785]. MARD roughly doubles when |ROC| is 3 or more [Pleus 2015, https://pmc.ncbi.nlm.nih.gov/articles/PMC4525645]. The iCGM rule also has trend limits [CFR above].
- Wear day: day 1 is worst. G4 Platinum in children: MARD 17 % (old software) vs 10 % (505 software) against lab blood [Laffel 2016, https://pmc.ncbi.nlm.nih.gov/articles/PMC4717517]. guess: their figure shows day 1 to day 7 falling from 21 to 15 % (old) and 13 to 10 % (505).
- Night: lying on the sensor causes false lows ("compression lows"). About 3 % of overnight readings in one trial [Baysal 2014, https://pmc.ncbi.nlm.nih.gov/articles/PMC4455457] [Mensh 2013, https://pmc.ncbi.nlm.nih.gov/articles/PMC3879750]. Libre in 742 inpatients: 3 AM bias -23 % [Wen 2022, https://pmc.ncbi.nlm.nih.gov/articles/PMC9639390].
- Binning: plotting error against the reference creates a fake trend. Use the mean of both [Bland & Altman 1995, https://www-users.york.ac.uk/~mb55/meas/dfplot.pdf]. Binning by CGM value is the iCGM convention ("what the patient sees").

What we do now:
- Range only. Three binnings are saved (reference, CGM, average). Figure 09 uses the average for bias. No lag, ROC, wear day or time of day yet. The plan lists all four.

Recommendation:
- Add: a lag scan. Shift the CGM trace by -15 to +15 min in 5-min steps; MARD per shift. Report the best shift as a side result. Do not "correct" the headline; the patient sees the unshifted value.
- Add: ROC from the CGM trace (slope over the previous 15 min), 5 bins as above. Add: night (00:00-06:00) vs day. Add: wear day. guess: the data has no sensor ID, so infer a session start at any gap of 2 h or more (the G4 warm-up time), cap at 7 days, show days 1-7.
- Keep: bias by average. Change: put MARD on the same axis in figure 09.

## 4. Subgroups (demographics)

Standard:
- The unit of analysis is the person (or the sensor), not the pair. Compute per-person MARD, then regress it on covariates, or fit a mixed model with a person random effect [Bland & Altman 2007 above] [ICU example, https://doi.org/10.1177/19322968251343108]. Example null result: per-person MARD not correlated with age or BMI [Kobe study, https://www.med.kobe-u.ac.jp/journal/contents/68/E5.pdf]. Wen 2022 used logistic regression with odds ratios and 95 % CIs.
- Pre-specify a short covariate list. Label everything else exploratory. Adjust p-values: Holm (strict) [https://www.jstor.org/stable/4615733] or Benjamini-Hochberg (false discovery rate) [https://www.dcscience.net/Benjamini-Hochberg-1995-FDR.pdf].
- Report null results with the CI and the smallest difference the study could have seen. guess: do not test subgroups under about 20 people. This is a rule of thumb, not a published cut.

What we do now:
- Nothing yet. A histogram of per-person MARD (calibration pairs only). Shanghai T1DM vs T2DM pooled, no CI.

Recommendation:
- Add: per-person MARD and bias on non-calibration meter pairs. Headline = median (IQR) across people.
- Add: one linear regression of per-person MARD on 5 pre-specified covariates: age, sex, BMI, HbA1c, years with diabetes. Also study arm, because the 77 CGM+BGM people give most meter pairs (5.4 vs 2.8 tests a day) [Aleppo 2017, https://pubmed.ncbi.nlm.nih.gov/28209654/]. BH-adjust. 95 % CI on each coefficient.
- Skip: race, income, education subgroups. Only 14 non-White people. Say so in the paper. Skip: pair-level mixed models (see the Skip list).

## 5. Hypoglycaemia detection

Standard:
- Event framing with a 15-min window. A reference event (70 or 55 mg/dL and below) is "missed" if no CGM value at or below the alert level appears within 15 min. A CGM excursion is a "false alert" if no reference below 70 appears within 15 min [Welsh 2022/2024, https://pmc.ncbi.nlm.nih.gov/articles/PMC10899839]. Example: G6 missed 14 % of events at 70 and 36 % at 55. Pivotal protocols report true, missed and false alert rates at 15 and 30 min [Dexcom SAP, https://cdn.clinicaltrials.gov/large-docs/11/NCT03966911/SAP_001.pdf].
- Pair-level sensitivity, specificity and PPV at 70 and 54 are the simple version. ADA levels: level 1 = 54-69, level 2 = below 54 [ADA 2025, https://pubmed.ncbi.nlm.nih.gov/39651981/].

What we do now:
- `paired_check` counts "CGM low but fingerstick not low" and the reverse, at 0-30 % bias. Not framed as sensitivity or specificity. No 54 threshold. No time window.

Recommendation:
- Add: 2 x 2 tables at 70 and 54 on non-calibration pairs: sensitivity, specificity, PPV, NPV, bootstrap CI by person. Small.
- Add: the 15-min event version, using the full CGM trace around each low fingerstick. Medium.
- State: fingersticks are taken when a low is suspected, so our sensitivity is not a random-sample estimate.

## 6. Simulation of faults and decisions

Standard:
- Replay: real traces plus simulated error. Kovatchev 2015: 56 pump users, 2,082 bolus segments, 7 error levels (MARD 3-22 %). Outcomes: hypo at or below 50 and 39, hyper at or above 250 and 400. Risk rises sharply above MARD 10 % [https://pmc.ncbi.nlm.nih.gov/articles/PMC4346608] [commentary, https://pmc.ncbi.nlm.nih.gov/articles/PMC4529100].
- Error model: lag + calibration bias and drift + autoregressive noise. Not plain random noise [Facchinetti 2010, https://pmc.ncbi.nlm.nih.gov/articles/PMC2825619] [Facchinetti 2014, https://research.unipd.it/handle/11577/2683479].
- Decision rules: hypo = eat 15-20 g glucose when below 70, recheck in 15 min [ADA 2025 above]. Correction dose = (glucose - target) / ISF. ISF = insulin sensitivity factor, the mg/dL drop per unit, often 1800 / total daily dose [https://www.diabetesnet.com/diabetes-tools/insulin-dose-guide/correction-factor]. Patient decision simulators: [Vettoretti 2015, https://www.research.unipd.it/handle/11577/3232371] [Vettoretti 2018, https://www.research.unipd.it/handle/11577/3255527].
- Meter-error replays on the UVA/Padova simulator: bias drives HbA1c and severe hypos. Outcomes: events, LBGI/HBGI [Breton 2010, https://pmc.ncbi.nlm.nih.gov/articles/PMC2901032] [Campos-Nanez 2017, https://pmc.ncbi.nlm.nih.gov/articles/PMC5951046].
- Outcome reporting: events per patient-day. TIR above 70 %, time below 70 under 4 %, below 54 under 1 % [Battelino 2019, https://doi.org/10.2337/dci19-0028]. LBGI/HBGI [Kovatchev 1998, https://doi.org/10.2337/diacare.21.11.1870]. Monte Carlo = draw the fault size and noise at random, repeat many times, report median and IQR.

What we do now:
- Constant low bias of 10, 20, 30 %. Rules: below 70 = carbs, above 200 = insulin. Flips counted on every 5-min reading, per person per day. Paired check against fingerstick. No noise, drift, lag, dropouts, pump logs, Monte Carlo or risk indices.
- With a constant bias b and fixed cut-offs, the flips are exactly the readings in [70, 70/(1-b)] and [200, 200/(1-b)]. So the result is a property of the glucose distribution, not of the sensor. Our JSON already records this ("flip_band").

Recommendation:
- Change: count decisions at decision points, not readings. Two kinds: (a) each HDeviceWizard bolus-calculator use, (b) the start of each low episode (15 min or more below 70).
- Add: use the wizard's own ISF and target to compute the correction dose with the real and the biased CGM. guess: both are columns in HDeviceWizard; check the Jaeb ReadMe. Report the dose change in units and the share of events with a change of 0.5 U or more.
- Add: a Monte Carlo fault set: bias (0-30 %) + AR(1) noise + per-day drift. 20 repeats per person, fixed seed. Outcomes: TIR/TBR/TAR, LBGI/HBGI, low and high episodes per patient-day, median (IQR) across people. Keep bias-only as the baseline row.
- Skip: the UVA/Padova simulator. Not available to us; replay on real traces is an accepted method.

## 7. Other things a 2026 reviewer expects

- A data-flow table: rows in, readings kept, pairs kept, with the number dropped at each step. The numbers exist in RESULTS.md; put them in one table.
- Pre-specified vs exploratory, labelled. One primary accuracy outcome (MARD on non-calibration pairs, by range) and one primary simulation outcome.
- Effect sizes with CIs, not p-values, for pooled pairs. With 476,000 pairs every p-value is tiny.
- Open code, pinned packages, stats in JSON: done (REPRODUCIBILITY.md). Add a fixed random seed to the Monte Carlo.
- Device and era stated: Dexcom G4 Platinum, 2015 (guess: Software 505; check the Jaeb ReadMe), Libre H for Shanghai. The recalled sensor is Libre 3. Say the transfer is indirect.
- Units: mg/dL, with the mmol/L factor stated. Shanghai values are multiples of 1.8, so they were converted with 18, not 18.016.
- Describe the people behind the pairs, not only the people in the trial. The 77 CGM+BGM people give most meter pairs.

## Do these (priority order)

| # | Item | Effort | Script |
|---|---|---|---|
| 1 | Tag calibration fingersticks in the meter log. Headline on non-calibration pairs | small | explore_raw_data.py |
| 2 | Bootstrap CI by participant (1,000 resamples) for MARD, bias, 20/20, zone A+B | small | explore_raw_data.py (new helper) |
| 3 | iCGM table: 15/15, 20/20, 40/40 by CGM value, 3 ranges, lower 95 % bound, cross-range rule | small | explore_raw_data.py |
| 4 | One axis per figure. Figure 09 all panels by average. Clarke to appendix. Flag 39/401 pairs | small | explore_raw_data.py |
| 5 | Per-person MARD on non-calibration pairs, median (IQR). Regression on 5 covariates + arm, BH | medium | new analysis/subgroups.py |
| 6 | Hypo 2 x 2 at 70 and 54 with CI. Then the 15-min event version | small, then medium | new analysis/drivers.py |
| 7 | Lag scan (-15 to +15 min) and ROC bins | medium | drivers.py |
| 8 | Night vs day. Flag suspected compression lows (sudden drop and recovery) | small | drivers.py |
| 9 | Wear day 1-7 from inferred sessions | medium | drivers.py |
| 10 | Simulation at decision points (wizard uses, low-episode starts) | medium | bias_simulation.py |
| 11 | Correction-dose change using the wizard's ISF and target | medium | bias_simulation.py |
| 12 | Monte Carlo faults (bias + noise + drift). TIR/TBR, LBGI/HBGI, episodes per day | large | bias_simulation.py |

## Skip these, and why

- Surveillance and DTS error grids: need a lookup matrix or their software. Parkes is in ISO 15197 and is enough. Mention as future work.
- Pair-level mixed-effects models on 476,000 pairs: heavy, and p-values are meaningless at that size. The per-person regression answers the same question.
- "Correcting" the headline accuracy for lag: the patient sees the unshifted value. Report the shift as a side result only.
- Precision ARD (PARD): needs two sensors worn at once. We have one.
- Trend-arrow accuracy matrix: needs a reference trend. Fingersticks are too sparse.
- UVA/Padova or any metabolic simulator: not available to us. Replay on real traces is accepted.
- A formal pass/fail test against iCGM: our reference is a home meter, not lab blood. Use the iCGM limits as context only.
- Race, income, education subgroups: too few people (14 non-White). Say it, do not test it.
- Machine-learning fault detectors: out of scope for this question.

## Pitfalls to state in the paper

1. The reference is a home meter (Contour Next, MARD about 3-5 %), not lab blood. Our MARD includes meter error. Numbers are not directly comparable to lab-based iCGM studies.
2. Fingersticks are not random samples. People test at calibration times and when they suspect a low. The sensor is also corrected with the calibration values. Headline numbers use non-calibration pairs.
3. The binning axis changes the sign of low-range bias. Say "by average", "by reference" or "by CGM" on every table and figure.
4. Meter and receiver have separate clocks, and the sensor lags blood by 5-10 min. Pairs during fast change carry lag error that looks like bias.
5. Pairs inside one person are correlated. 476,000 pairs are not 476,000 independent data points. CIs are bootstrapped by person. No p-values from pooled pairs.
6. Devices are 2015-2019 models (Dexcom G4, Libre H). The recalled sensor is Libre 3. The simulation models a bias of the recall's kind, not the recall fault itself.
7. Until the decision-point version runs, the simulation counts time spent with a wrong decision, not real decisions. With constant bias and fixed cut-offs, the flips depend only on the glucose distribution.
8. The people are White, well-controlled, insured adult pump users (REPLACE-BG) or older Chinese inpatients (Shanghai). Results do not transfer to children or other groups.
