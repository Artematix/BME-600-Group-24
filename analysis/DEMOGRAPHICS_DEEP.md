# Does who you are predict sensor error? Deep demographics check of REPLACE-BG and Shanghai (2026-11-06)

Script: `analysis/demographics_deep.py`. Numbers: `analysis/demographics_deep_stats.json`. Figures 29-32 in `analysis/figures/`. This extends `SUBGROUPS.md` (first pass, 2026-10-30); the first-pass results stand and are not repeated here.

Terms. MARD = mean absolute relative difference: the average size of the sensor error as a percent of the fingerstick value (lower is better). Bias = mean signed error in percent (negative = sensor reads low). Low range = pairs whose average of sensor and fingerstick is below 70 mg/dL. Missed low = fingerstick below 70 but sensor shows 70 or more. False low = sensor shows below 70 but fingerstick is 70 or more. Within 20/20 = share of pairs within 20 mg/dL (fingerstick below 100) or within 20 %. CV = glucose SD divided by mean glucose: how much a person's glucose swings. IQR = the middle half of people. CI = 95 % confidence interval. p = the chance of a result this big if there were no real difference. BH = Benjamini-Hochberg correction: when many tests are run, it raises each p so that false "findings" stay rare; "BH p" is the corrected p. Rho = Spearman rank correlation, -1 to +1 (0 = no link). ICC = intraclass correlation: the share of the person-to-person spread that sits between clinic sites (0 = sites are all alike). R-squared = the share of the spread in the outcome that a model predicts (0 = nothing; out-of-fold = measured on people the model did not see). Permutation importance = how much a model gets worse when one variable is shuffled. Interaction = whether the effect of one trait depends on another (for example, does age matter only in men?). Mediation = a chain: trait -> glucose pattern -> sensor error. n.t. = not testable.

## Summary in 6 lines
- 680 pre-registered tests on 226 people (67 traits x 7 error measures, 133 interaction tests, 140 worst-quartile tests). 69 had raw p < 0.05; 34 would be expected by chance. One passed the BH correction.
- The one that passed: in the low range the sensor reads lower in women than in men. Low-range bias -6.4 % in women vs -2.2 % in men (difference +4.2 points, CI +2.0 to +6.0, BH p 0.016). About 2.5 mg/dL at 60 mg/dL. It goes with fewer missed lows in women (27.5 % vs 33.9 %, raw p 0.002, BH p 0.16). Low-range MARD is identical by sex (17.5 vs 17.6 %). Real-looking but small, and weaker in the CGM+BGM arm; needs an outside check before it goes in the paper.
- Everything else is null: age, race, education, income, insurance, BMI, weight, height, HbA1c, duration, hypoglycaemia awareness, hypo fear, conditions, medications, insulin type, pump, prior CGM use, arm, run-in, and all 18 pairwise interactions.
- Location: clinic site holds 3.5 % of the MARD spread (ICC 0.035, permutation p 0.10). What little there is tracks the glucose pattern of each site's patients (site median MARD vs site median CV: rho 0.66). Shanghai has no site variable.
- Flexible models (random forest, gradient boosting, ridge) cannot predict a person's MARD from demographics at all (out-of-fold R-squared below zero in every run). Glucose pattern alone reaches 0.03 (0.06 on log MARD; 0.14 for the missed-low rate). Adding demographics on top of glucose pattern makes every model worse.
- Mediation chains exist but are tiny: younger age -> more glucose swings -> higher MARD carries -0.07 SD (CI -0.12 to -0.03), about 0.3 MARD points per 14 years of age. Shanghai (76 patients): nothing in 60 tests.

## 1. What was asked
The first pass found that age, sex, BMI, HbA1c, duration and arm do not predict MARD, while glucose pattern (CV, time below 70) does. The project lead asked for a full look before accepting that: every variable the data hold, pairs of traits together, clinic site, a flexible model that can catch odd patterns, the mediation chain, the worst quartile, and both cohorts described properly. Rule for this memo: every test is listed before it is run (section 3) and every result is reported, null or not.

## 2. Who is in the data

### 2a. REPLACE-BG (226 adults, type 1 diabetes, Dexcom G4, all on insulin pumps)
Filled = share of people with a value. Status: testable = at least two groups of 10 or more people; low variance = the largest group holds 90 % or more of the cohort (a test can only find big differences).

| Variable | Filled | Values (n) | Status |
|---|---|---|---|
| Sex | 100 % | M 114; F 112 | testable |
| Age (years) | 100 % | median 43 (IQR 31-55), range 19-78 | testable |
| Age group | 100 % | <35 69; 35-50 78; >50 79 | testable |
| Race | 100 % | White 212; Black 5; Asian 4; more than one 3; unknown 2 | testable as White vs not (14); low variance |
| Ethnicity | 100 % | not Hispanic 216; Hispanic or Latino 9; unknown 1 | NOT testable (9); low variance |
| Education | 98 % | no bachelor's 47; bachelor's 110; graduate degree 64; missing 5 | testable |
| Income (answered only) | 74 % | <$50k 25; $50k-<$100k 56; $100k-<$200k 55; $200k+ 32; not answered 58 | testable |
| Answered the income question | 100 % | yes 168; no 58 | testable |
| Private insurance | 100 % | yes 198; no 28 | testable |
| Medicare | 100 % | yes 16; no 210 | testable; low variance |
| Medicaid | 100 % | yes 8; no 218 | NOT testable; low variance |
| Other insurance | 100 % | yes 14; no 212 | testable; low variance |
| No insurance | 100 % | yes 4; no 222 | NOT testable; low variance |
| BMI (kg/m2) | 100 % | median 26.7 (IQR 24.0-30.1), range 18.7-42.7 | testable |
| BMI group | 100 % | <25 77; 25-30 92; 30+ 57 | testable |
| Weight (kg) | 100 % | median 79.5 (IQR 69.7-91.4) | testable |
| Height (cm) | 100 % | median 172 (IQR 164-180) | testable |
| HbA1c at screening (%) | 100 % | median 7.3 (IQR 6.8-7.8), range 5.2-8.9 | testable |
| HbA1c group | 100 % | <7 77; 7-8 118; >8 31 | testable |
| HbA1c change, randomisation to week 26 | 96 % | median 0.0 (IQR -0.3 to +0.3) | testable |
| Diabetes duration (years) | 100 % | median 21.5 (IQR 14-31), range 2-64 | testable |
| Age at diagnosis (years) | 100 % | median 18 (IQR 10-29) | testable |
| Fingersticks per day at screening | 100 % | median 5 (IQR 4-6), range 1-12 | testable |
| Severe hypoglycaemia history | 100 % | never 146; more than 12 months ago 80; in the past 12 months 0 | testable |
| DKA history | 100 % | never 166; ever 60 (2 in the past 12 months) | testable |
| Non-insulin glucose-lowering drug | 100 % | yes 16; no 210 | testable; low variance |
| Insulin in the pump | 100 % | aspart 123; lispro 89; other or more than one 14 | testable |
| Pump vs injections | 100 % | pump 226; injections 0 | no variance |
| Pump family | 99 % | Medtronic 126; multiple 36; OmniPod 28; unknown code 18; Animas 15; Tandem 1 | testable |
| CGM model | 100 % | Dexcom G4 226 (23 also a Share receiver, 1 a G5) | no variance; receiver model testable (24 vs 202) |
| Prior CGM use | 100 % | current 107; in the past 79; never 40 | testable |
| CGM brand (current users) | 47 % | Dexcom 77; Medtronic 30 | testable |
| Years of CGM use (current users) | 47 % | <1 year 34; 1-<5 years 49; 5+ years 24 | testable |
| Symptoms when glucose is low | 100 % | always 189; sometimes 37 | testable |
| Has lost some low-glucose symptoms | 100 % | no 187; yes 39 | testable |
| Moderate hypo needing help, past 6 months | 100 % | never 209; any 17 | testable; low variance |
| Lows with symptoms, past month | 100 % | 0-3 times 77; 1 per week 56; 2-3 per week 73; 4+ per week 20 | testable |
| Lows without symptoms, past month | 100 % | never 177; any 49 | testable |
| Glucose where symptoms start | 100 % | 60-69 mg/dL 195; 50-59 mg/dL 31 | testable |
| How often symptoms appear when low | 100 % | always 142; often or sometimes 84 | testable |
| Hypoglycaemia fear score (23 items, 0-92) | 100 % | median 28 (IQR 22-35); worry part 9 (4-14); behaviour part 19 (15-23) | testable |
| Diabetes technology questionnaire (30 items, 30-150) | 100 % | median 111.5 (IQR 97-124) | testable (direction of the scale not interpreted) |
| Number of listed conditions (besides diabetes) | 100 % | median 4 (IQR 2-6), range 0-26 | testable |
| Number of listed medications | 100 % | median 4 (IQR 2-6), range 0-22 | testable |
| Hyperlipidaemia / hypertension / hypothyroidism / any thyroid | 100 % | yes 100 / 63 / 51 / 68 | testable |
| Depression / anxiety | 100 % | yes 40 / 11 | testable (anxiety low variance) |
| Retinopathy / neuropathy / kidney or albuminuria / gastroparesis / any diabetes complication | 100 % | yes 49 / 16 / 13 / 7 / 63 | gastroparesis NOT testable; neuropathy and kidney low variance |
| Obesity listed as a condition | 100 % | yes 16 | testable; low variance |
| Takes a statin | 100 % | yes 101; no 125 | testable |
| Acetaminophen-containing drug listed (a known G4 interferent) | 100 % | yes 7 | NOT testable |
| Study arm | 100 % | CGM-only 149; CGM+BGM 77 | testable |
| Clinic site | 100 % | 14 sites, 8 to 27 people each (site 8 has 8) | testable (13 sites) |
| Run-in CGM type | 100 % | blinded 128; standard 98 | testable |
| Run-in length (days to randomisation) | 100 % | median 69 (IQR 28-75) | testable |
| Completion status | 100 % | completed 217; dropped 9 | NOT testable |
| Days of CGM data in the window | 100 % | median 235 (IQR 200-252) | testable |

Picture: adults (median 43), half women, 94 % White, 77 % with a degree, 88 % privately insured, HbA1c near 7 %, 21 years of diabetes, all on pumps, 84 % say they always feel their lows, nobody had a severe low in the past year (an entry rule of the trial). Figure 29 shows the distributions.

### 2b. Shanghai (112 patients; 76 with 10+ fingerstick pairs are the test set)
Abbott flash CGM, in-patients, 3-14 days each. The files have no hospital or site column, no race, education, income or insurance, and no arm. Values below are for the 76 patients in the test set (the whole cohort is similar: age 62, BMI 23.5, HbA1c 8.5 %, duration 7 years).

| Variable | Filled | Values (n) | Status |
|---|---|---|---|
| Diabetes type | 100 % | type 2: 66; type 1: 10 | testable (type 1 at the 10-person limit) |
| Sex | 100 % | M 44; F 32 | testable |
| Age (years) | 100 % | median 63 (IQR 51-68), range 22-92 | testable |
| BMI (kg/m2) | 100 % | median 23.7 (IQR 22.2-25.4) | testable |
| HbA1c (%) | 95 % | median 9.2 (IQR 7.4-11.4), range 5.3-17.3 | testable |
| Diabetes duration (years) | 100 % | median 8 (IQR 2-15) | testable |
| Smoking history (any pack-years) | 100 % | yes 18; no 58 | testable |
| Alcohol drinker | 100 % | yes 12; no 64 | testable |
| Any macrovascular complication (heart, artery, stroke) | 100 % | yes 36; no 40 | testable |
| Any microvascular complication (eye, nerve, kidney) | 100 % | yes 30; no 46 | testable |
| Any other condition listed | 100 % | yes 57; no 19 | testable |
| Hypoglycaemia recorded (yes/no column) | 100 % | yes 15; no 61 | testable |
| On insulin | 100 % | yes 51; no 25 | testable |
| Glucose-lowering treatment | 100 % | insulin only 21; insulin + oral/GLP-1 30; oral/GLP-1 only 24; none listed 1 | testable |
| eGFR (kidney function) | 86 % | median 113 (IQR 96-137) | testable |
| Fasting C-peptide (nmol/L) | 87 % | median 0.4 (IQR 0.2-0.5) | testable |
| Fasting plasma glucose (mg/dL) | 99 % | median 160 (IQR 126-194) | testable |
| Smoking pack-years | 100 % | median 0 (IQR 0-0), range 0-80 | testable (mostly zero) |

Picture: older (median 63), mostly type 2, thin by Western standards (BMI 24), poorly controlled (HbA1c 9 %), one in three with heart or artery disease. Almost the opposite of REPLACE-BG, which is useful: a trait that mattered in both would be convincing.

## 3. Pre-registered test list (written before any test ran; stored in the JSON under `preregistration`)
Unit = the person. Outcomes per person (7): MARD, low-range MARD, bias, low-range bias, missed-low rate, false-low rate, within 20/20. Low-range values need 20 or more low pairs (150 people); the missed-low rate needs 20 fingersticks below 70 (156 people); the false-low rate needs 20 sensor readings below 70 (174 people).

| Block | What is tested | How |
|---|---|---|
| a. Univariate | every testable trait in section 2a (61 of 67) x 7 outcomes = 407 tests | groups: Mann-Whitney (2 groups) or Kruskal-Wallis (3+), groups under 10 people dropped, each group vs the first as a difference in medians with a bootstrap CI; continuous traits: Spearman rho with a bootstrap CI |
| b. Interactions | 18 pairs x 7 outcomes = 126 tests, plus site x arm x 7 = 7 tests | regression outcome ~ a + b + a x b (robust errors), p of the a x b term; 2x2 tables of group medians (continuous traits split at their median) with a bootstrap CI for the difference of differences; site x arm: F-test of the whole block with a permutation p (arm shuffled within site) |
| c. Site | per-site table; ICC with permutation p and bootstrap CI for 8 outcomes; mixed model with a site random effect, with and without covariates | the Kruskal-Wallis by site is in block a |
| d. Flexible models | random forest, gradient boosting, ridge; 5-fold cross-validation x 10 repeats; feature sets: 91 demographic columns, 3 glucose-pattern columns (CV, % time below 70, mean glucose), both; outcomes MARD, log MARD, low-range MARD, missed-low rate; grouped permutation importance on held-out folds | no p-values; not in the BH family |
| e. Mediation | 14 traits -> (CV, % time below 70) -> MARD, and 8 traits -> low-range MARD; standardised; bootstrap CIs | descriptive; not in the BH family |
| f. Worst quartile | the 25 % with the worst MARD vs the rest, and the same for the missed-low rate; every trait plus the glucose-pattern variables = 140 tests | Mann-Whitney / Fisher / chi-square |
| g. Shanghai | 20 traits x 3 outcomes (MARD, bias, within 20/20) = 60 tests | as block a; own BH family; no interactions or flexible models (too small); no site variable exists |

Multiple testing: one BH family over blocks a, b and f together (680 tests). Shanghai is a second family (60 tests). BH within each block is also stored in the JSON as a softer secondary check. Effect-size rule: a result that passes BH but moves the median by under 1 MARD point (or rho under 0.2) is "statistically detectable, too small to matter".

The 18 pairs: age x sex, age x BMI, age x HbA1c, age x duration, age x arm, sex x BMI, sex x HbA1c, sex x duration, sex x arm, BMI x HbA1c, BMI x duration, BMI x arm, HbA1c x duration, HbA1c x arm, duration x arm, prior CGM use x arm, hypo awareness x HbA1c, hypo awareness x age.

## 4. The seven outcomes per person

| Outcome | n | Median | IQR |
|---|---|---|---|
| MARD (%) | 226 | 12.3 | 10.7 to 14.3 |
| Low-range MARD (%) | 150 | 17.6 | 15.5 to 19.4 |
| Bias (%) | 226 | -1.7 | -2.9 to -0.2 |
| Low-range bias (%) | 150 | -4.0 | -7.6 to -0.1 |
| Missed-low rate (%) | 156 | 30.3 | 22.0 to 40.4 |
| False-low rate (%) | 174 | 40.4 | 32.4 to 53.4 |
| Within 20/20 (%) | 226 | 85.1 | 81.0 to 89.0 |

Pooled over all pairs: 31.4 % of fingerstick lows were missed and 40.9 % of sensor lows were not confirmed (same as `ACCURACY_V2.md`). The missed-low rate correlates with MARD (rho 0.32) and with bias (rho 0.46: a sensor that reads high misses lows). The false-low rate does not correlate with MARD (rho 0.03).

## 5. Block a: one trait at a time

Overall count: 407 tests, 1 passed BH (sex on low-range bias). The pre-specified six and site, on all seven outcomes (cell = effect; raw p; BH p over the whole list; groups: largest difference in medians vs the first group; continuous: rho):

| Trait | MARD | Low-range MARD | Bias | Low-range bias | Missed-low | False-low | Within 20/20 |
|---|---|---|---|---|---|---|---|
| Sex (M vs F) | 0.0; 0.92; 1.00 | 0.1; 0.97; 1.00 | 0.3; 0.97; 1.00 | **+4.2; <0.001; 0.016** | +6.4; 0.002; 0.16 | -3.7; 0.18; 0.70 | 0.3; 0.55; 0.91 |
| Age (rho) | -0.16; 0.01; 0.36 | -0.05; 0.58; 0.92 | +0.04; 0.52; 0.91 | +0.03; 0.69; 0.97 | +0.20; 0.01; 0.36 | +0.16; 0.03; 0.37 | +0.17; 0.01; 0.35 |
| BMI (rho) | +0.13; 0.05; 0.46 | +0.09; 0.26; 0.74 | +0.09; 0.16; 0.68 | +0.11; 0.18; 0.70 | +0.04; 0.63; 0.93 | 0.00; 0.99; 1.00 | -0.18; 0.007; 0.29 |
| HbA1c (rho) | -0.08; 0.22; 0.72 | +0.07; 0.36; 0.83 | -0.01; 0.91; 1.00 | -0.11; 0.19; 0.71 | -0.10; 0.22; 0.72 | +0.06; 0.46; 0.91 | +0.04; 0.56; 0.91 |
| Duration (rho) | -0.09; 0.20; 0.71 | +0.18; 0.03; 0.37 | -0.05; 0.44; 0.90 | +0.07; 0.39; 0.87 | +0.02; 0.84; 1.00 | +0.04; 0.59; 0.92 | +0.09; 0.20; 0.71 |
| Arm (CGM+BGM vs CGM-only) | -0.1; 0.54; 0.91 | +0.2; 0.85; 1.00 | 0.0; 0.89; 1.00 | -1.1; 0.50; 0.91 | -3.7; 0.06; 0.49 | -3.2; 0.07; 0.50 | 0.8; 0.12; 0.60 |
| Clinic site (13 sites) | 1.9; 0.03; 0.37 | 3.8; 0.03; 0.37 | 2.0; 0.06; 0.48 | 5.4; 0.14; 0.67 | 9.9; 0.73; 0.99 | 14.8; 0.63; 0.93 | 5.0; 0.13; 0.65 |

The full matrix for all 67 traits is Appendix A. The strongest raw signals that did NOT pass (all BH p 0.05 or more):

| Trait and outcome | Effect | Raw p | BH p | Note |
|---|---|---|---|---|
| Number of medications vs MARD | rho -0.24 (CI -0.37 to -0.11) | <0.001 | 0.05 | more drugs, lower MARD; see section 12b |
| Number of conditions vs MARD | rho -0.21 | 0.001 | 0.14 | same thing; vanished after adjustment in the first pass |
| Run-in length vs bias | rho +0.22 | <0.001 | 0.12 | longer run-in, sensor reads slightly higher; run-in length is set by the trial design (blinded run-in is longer) |
| Weight vs low-range bias | rho +0.24 | 0.003 | 0.17 | heavier people, sensor reads less low; this is the sex difference in disguise (men are 14 kg heavier); within each sex rho is -0.04 (F) and +0.14 (M) |
| Height vs low-range bias | rho +0.22 | 0.006 | 0.28 | same |
| Retinopathy vs MARD | -1.3 points (yes 11.3 vs no 12.6) | 0.009 | 0.35 | first pass: gone after adjusting for age and CV |
| Any diabetes complication vs MARD | -1.1 points | 0.01 | 0.35 | same people as above |
| Age vs missed-low rate | rho +0.20 | 0.01 | 0.36 | older people, more missed lows |
| Any thyroid condition vs missed-low rate | -7.2 points | 0.02 | 0.36 | 43 vs 113 people |
| Statin vs missed-low rate | +4.0 points | 0.02 | 0.36 | statin users are older |
| BMI vs within 20/20 | rho -0.18 | 0.007 | 0.29 | mirrors the weak BMI-MARD link |

Sex and the missed-low rate (women 27.5 %, men 33.9 %; difference +6.4, CI +2.4 to +12.8) did not pass BH (0.16) but points the same way as the low-range bias result (section 12a).

Not testable (described only, median MARD): Hispanic or Latino 13.1 % (n 9) vs 12.3 %; Medicaid 12.9 % (8); no insurance 13.3 % (4); gastroparesis 13.5 % (7); acetaminophen-containing drug 11.6 % (7); dropped out 12.3 % (9).

## 6. Block b: two traits together (interactions)
For MARD, every pair. Cells = median MARD (n). DoD = difference of differences: how much the effect of the second trait changes between the two levels of the first; 0 = no interaction. Continuous traits are split at the median (age 43, BMI 26.75, HbA1c 7.3 %, duration 21.5 years).

| Pair | Cell medians, % (n) | DoD (CI) | Interaction p | BH p |
|---|---|---|---|---|
| Age x Sex | <43 F 12.7 (65); <43 M 12.7 (46); 43+ F 11.6 (47); 43+ M 11.8 (68) | +0.2 (-1.3 to +1.9) | 0.24 | 0.73 |
| Age x BMI | <43 low 12.1 (51); <43 high 13.0 (60); 43+ low 11.7 (62); 43+ high 11.8 (53) | -0.8 (-2.3 to +0.9) | 0.14 | 0.66 |
| Age x HbA1c | <43 low 12.8 (48); <43 high 12.3 (63); 43+ low 12.1 (59); 43+ high 11.3 (56) | -0.3 (-2.0 to +1.0) | 0.63 | 0.93 |
| Age x Duration | <43 short 12.8 (76); <43 long 12.3 (35); 43+ short 11.4 (37); 43+ long 12.2 (78) | +1.2 (-1.2 to +2.4) | 0.95 | 1.00 |
| Age x Arm | <43 CGM-only 12.8 (76); <43 CGM+BGM 12.6 (35); 43+ CGM-only 11.8 (73); 43+ CGM+BGM 11.6 (42) | +0.1 (-1.7 to +1.9) | 0.51 | 0.90 |
| Sex x BMI | F low 12.1 (62); F high 12.5 (50); M low 11.6 (51); M high 12.8 (63) | +0.7 (-1.1 to +2.0) | 0.64 | 0.93 |
| Sex x HbA1c | F low 12.8 (50); F high 11.9 (62); M low 12.5 (57); M high 12.3 (57) | +0.7 (-0.5 to +2.4) | 0.48 | 0.90 |
| Sex x Duration | F short 12.4 (56); F long 12.1 (56); M short 12.6 (57); M long 12.3 (57) | 0.0 (-1.6 to +1.5) | 0.32 | 0.79 |
| Sex x Arm | F CGM-only 12.3 (71); F CGM+BGM 12.3 (41); M CGM-only 12.6 (78); M CGM+BGM 12.1 (36) | -0.5 (-2.2 to +1.0) | 0.93 | 1.00 |
| BMI x HbA1c | low/low 12.0 (62); low/high 11.9 (51); high/low 13.0 (45); high/high 12.2 (68) | -0.6 (-3.1 to +1.0) | 0.64 | 0.93 |
| BMI x Duration | low/short 12.2 (56); low/long 11.7 (57); high/short 12.6 (57); high/long 12.7 (56) | +0.6 (-1.0 to +2.2) | 0.53 | 0.91 |
| BMI x Arm | low CGM-only 11.7 (66); low CGM+BGM 12.3 (47); high CGM-only 12.8 (83); high CGM+BGM 12.2 (30) | -1.2 (-2.3 to +0.8) | 0.10 | 0.56 |
| HbA1c x Duration | low/short 12.9 (52); low/long 12.2 (55); high/short 12.0 (61); high/long 12.2 (58) | +1.0 (-0.8 to +2.4) | 0.50 | 0.90 |
| HbA1c x Arm | low CGM-only 12.7 (64); low CGM+BGM 12.7 (43); high CGM-only 12.1 (85); high CGM+BGM 12.0 (34) | -0.1 (-2.4 to +1.4) | 0.47 | 0.90 |
| Duration x Arm | short CGM-only 12.4 (79); short CGM+BGM 12.4 (34); long CGM-only 12.2 (70); long CGM+BGM 12.2 (43) | -0.1 (-1.6 to +1.6) | 0.99 | 1.00 |
| Prior CGM x Arm | not current, CGM-only 12.4 (80); not current, CGM+BGM 12.9 (39); current, CGM-only 12.3 (69); current, CGM+BGM 12.0 (38) | -0.8 (-2.5 to +1.0) | 0.75 | 0.99 |
| Hypo awareness x HbA1c | always, low 12.7 (89); always, high 12.0 (100); sometimes, low 11.9 (18); sometimes, high 12.9 (19) | +1.7 (-0.8 to +4.1) | 0.25 | 0.73 |
| Hypo awareness x Age | always, <43 12.7 (99); always, 43+ 11.7 (90); sometimes, <43 12.6 (12); sometimes, 43+ 11.9 (25) | +0.4 (-2.2 to +2.7) | 0.88 | 1.00 |
| Site x Arm | 14 sites x 2 arms | F 1.35 (13 and 198 df) | 0.19 (permutation 0.21) | 0.71 |

Every cell sits between 11.3 and 13.0 %. No combination of traits is a bad or a good group. Figure 30 shows six of these tables.

The other six outcomes (108 pair tests + 6 site x arm): 7 of the 126 pair tests had raw p < 0.05 (6.3 expected by chance); the smallest BH p is 0.35. They are listed for completeness: on low-range bias, age x sex (p 0.02), sex x duration (0.02), sex x arm (0.02; the sex gap is +6.2 in the CGM-only arm and +1.8 in CGM+BGM, section 12a) and HbA1c x arm (0.03); on the false-low rate, age x BMI (0.02), sex x arm (0.02) and HbA1c x duration (0.009). Site x arm: null for six outcomes (p 0.09 to 0.95); for the false-low rate the permutation p is 0.007 (BH p 0.30; 13 extra terms explain 16 % of the spread in 160 people, which is what 13 free parameters do).

## 7. Block c: location (clinic site)

| Site | n | MARD median (IQR) | Low-range MARD | Missed-low | CV | % time <70 | Age | HbA1c | % CGM+BGM | % female |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 15 | 12.3 (9.7-13.6) | 17.6 | 28.6 | 37.3 | 3.5 | 34 | 7.1 | 33 | 80 |
| 2 | 16 | 11.9 (10.4-13.3) | 19.1 | 21.6 | 36.9 | 4.4 | 58 | 7.4 | 38 | 62 |
| 3 | 17 | 12.6 (11.2-13.1) | 18.0 | 38.5 | 37.6 | 2.8 | 35 | 7.4 | 35 | 47 |
| 5 | 19 | 12.6 (12.2-14.0) | 19.1 | 28.7 | 38.6 | 3.6 | 46 | 7.4 | 32 | 58 |
| 6 | 27 | 13.0 (11.6-15.4) | 17.1 | 30.0 | 37.9 | 3.9 | 52 | 7.5 | 33 | 33 |
| 7 | 14 | 11.3 (10.3-12.2) | 18.4 | 25.8 | 34.9 | 2.9 | 44 | 7.4 | 36 | 36 |
| 8 | 8 | 14.9 (12.6-18.5) | 16.7 | 37.9 | 37.4 | 2.7 | 46 | 7.2 | 38 | 50 |
| 9 | 14 | 13.2 (10.4-16.0) | 13.0 | 20.0 | 41.5 | 5.3 | 41 | 7.6 | 36 | 36 |
| 10 | 15 | 11.6 (10.4-14.4) | 15.4 | 30.0 | 38.4 | 3.6 | 34 | 7.6 | 33 | 53 |
| 11 | 18 | 11.7 (9.8-12.8) | 18.3 | 29.4 | 35.5 | 2.6 | 54 | 7.4 | 33 | 28 |
| 12 | 13 | 13.8 (11.9-16.5) | 16.5 | 27.5 | 39.7 | 3.9 | 30 | 7.1 | 38 | 77 |
| 13 | 12 | 12.2 (11.2-14.4) | 17.5 | 37.5 | 35.6 | 1.8 | 47 | 7.0 | 25 | 42 |
| 14 | 15 | 10.4 (9.8-12.2) | 13.8 | 34.8 | 35.5 | 2.6 | 42 | 7.1 | 33 | 40 |
| 15 | 23 | 12.7 (11.3-14.3) | 19.0 | 33.3 | 36.4 | 3.5 | 44 | 6.8 | 35 | 61 |

Site medians span 10.4 to 14.9 % MARD (site 8 has only 8 people). Kruskal-Wallis over the 13 sites with 10+ people: p 0.03, BH p 0.37 (block a). How much of the spread is between sites:

| Outcome | ICC (CI) | Permutation p | Mixed-model ICC | Site SD vs person SD |
|---|---|---|---|---|
| MARD | 0.035 (0.02 to 0.21) | 0.10 | 0.031 | 0.8 vs 4.4 points |
| Low-range MARD | 0.090 (0.05 to 0.31) | 0.02 | 0.085 | 1.0 vs 3.4 |
| Missed-low rate | -0.009 (-0.02 to 0.20) | 0.55 | 0.005 | 1.0 vs 14.0 |
| False-low rate | -0.024 (-0.02 to 0.16) | 0.76 | 0.001 | 0.4 vs 14.5 |
| Bias | 0.005 (-0.02 to 0.22) | 0.39 | 0.002 | 0.1 vs 3.0 |
| Glucose CV | 0.049 (0.02 to 0.20) | 0.04 | 0.049 | 1.1 vs 4.6 |
| % time below 70 | 0.050 (0.02 to 0.22) | 0.04 | 0.049 | 0.6 vs 2.5 |
| Mean glucose | 0.004 (0.00 to 0.16) | 0.38 | 0.003 | 1.1 vs 21.2 |

Reading: 3.5 % of the MARD spread is between sites, which a chance assignment of people to sites would produce one time in ten. The low-range MARD ICC (0.09) is the largest, driven by sites 9 and 14 (13.0 and 13.8 % vs 17-19 % elsewhere); sites 9 and 14 are also the sites with the lowest and highest time below 70, so this is not a tidy story. Site holds as much of the glucose pattern (CV, time low: ICC 0.05, p 0.04) as of the error. Mixed model of MARD with a site random effect: site variance 0.60 alone, 0.72 with the six pre-specified terms, 0.24 once CV and time below 70 are added (ICC 0.031 -> 0.013). Across the 14 sites, site median MARD follows site median CV (rho 0.66, p 0.01) more than site median time low (rho 0.41, p 0.14). Figure 31. Verdict: location is not a driver; the little site spread there is comes with the patients' glucose pattern. Shanghai: no site or hospital variable exists, so location cannot be tested there.

## 8. Block d: can a flexible model find anything?
Out-of-fold R-squared (mean over 10 repeats of 5-fold cross-validation; range in brackets). 0 = no better than guessing the average; below 0 = worse than guessing the average.

| Outcome | Model | Demographics only (91 columns) | Glucose pattern only (3 columns) | Both | Added by demographics |
|---|---|---|---|---|---|
| MARD | random forest | -0.03 (-0.06 to 0.00) | 0.01 (-0.01 to 0.03) | -0.02 (-0.04 to 0.00) | -0.03 |
| MARD | gradient boosting | -0.03 (-0.04 to 0.00) | 0.00 (-0.02 to 0.02) | -0.02 (-0.05 to 0.02) | -0.02 |
| MARD | ridge (linear) | -0.03 (-0.05 to -0.02) | 0.03 (0.02 to 0.04) | -0.03 (-0.05 to -0.02) | -0.06 |
| log MARD | random forest | -0.01 (-0.04 to 0.00) | 0.04 (0.03 to 0.06) | 0.01 (-0.02 to 0.03) | -0.03 |
| log MARD | gradient boosting | -0.03 (-0.08 to 0.00) | 0.02 (0.00 to 0.05) | 0.00 (-0.05 to 0.02) | -0.03 |
| log MARD | ridge | -0.02 (-0.03 to -0.01) | 0.06 (0.06 to 0.07) | 0.00 (-0.02 to 0.02) | -0.06 |
| Low-range MARD | all three | -0.02 to -0.06 | -0.02 to -0.07 | -0.02 to -0.06 | about 0 |
| Missed-low rate | random forest | 0.02 (-0.01 to 0.06) | 0.14 (0.10 to 0.16) | 0.11 (0.06 to 0.15) | -0.03 |
| Missed-low rate | gradient boosting | 0.00 (-0.04 to 0.05) | 0.10 (0.07 to 0.14) | 0.05 (-0.01 to 0.10) | -0.05 |
| Missed-low rate | ridge | -0.01 (-0.04 to 0.02) | 0.14 (0.12 to 0.17) | 0.03 (-0.01 to 0.06) | -0.10 |

Reading: 91 demographic, clinical, device and questionnaire columns predict nothing about a person's MARD, in a linear model or in two tree models that can catch any non-linear pattern or interaction. The three glucose-pattern columns predict a little (3 % of raw MARD, 6 % of log MARD, 14 % of the missed-low rate). Adding the 91 columns on top of the 3 makes every model worse (the "added" column is negative in all 10 rows): the demographics bring noise, not signal. Low-range MARD is not predictable by anything here. Raw MARD is hard to predict because two people above 30 % dominate its variance; log MARD softens that and the picture is the same.

Grouped permutation importance (random forest, both sets, MARD; drop in held-out R-squared when the group is shuffled): CV +0.015, number of medications +0.015, obesity flag +0.009, % time below 70 +0.008, everything else 0.003 or less (site, all 14 columns: 0.000). Shuffling all 91 demographic columns at once changes R-squared by -0.015 (the model gets slightly better); shuffling the 3 glucose columns costs 0.042 (random forest) and 0.028 (gradient boosting). Figure 32, right.

## 9. Block e: mediation (trait -> glucose pattern -> MARD)
All in SD units (standard deviations: 1 SD of age = 14 years, of MARD = 4.4 points, of CV = 4.7 points). a = effect of the trait on the mediator; b = effect of the mediator on MARD with the trait held fixed; indirect = a x b summed over both mediators; direct = what is left of the trait after the mediators; total = the trait alone. CI in brackets. A chain "exists" when the indirect CI excludes 0.

| Trait | a: trait -> CV | a: trait -> time below 70 | b: CV -> MARD | b: time low -> MARD | Indirect | Direct | Total |
|---|---|---|---|---|---|---|---|
| Age | -0.28 (-0.41 to -0.16) | -0.21 (-0.32 to -0.09) | +0.18 (+0.01 to +0.37) | +0.09 (-0.09 to +0.28) | **-0.07 (-0.12 to -0.03)** | +0.04 (-0.10 to +0.17) | -0.03 (-0.16 to +0.10) |
| Male | -0.04 | +0.04 | +0.17 | +0.09 | 0.00 (-0.04 to +0.03) | 0.00 | -0.01 |
| BMI | +0.05 | -0.12 | +0.16 | +0.11 | -0.01 (-0.05 to +0.04) | +0.07 | +0.06 |
| HbA1c | +0.18 (+0.05 to +0.32) | -0.22 (-0.35 to -0.08) | +0.25 (+0.03 to +0.50) | +0.01 | +0.04 (-0.05 to +0.15) | -0.13 (-0.31 to +0.01) | -0.09 (-0.22 to +0.03) |
| Diabetes duration | -0.04 | 0.00 | +0.17 | +0.09 | -0.01 (-0.05 to +0.03) | -0.04 | -0.05 |
| CGM+BGM arm | +0.02 | +0.05 | +0.17 | +0.09 | +0.01 (-0.02 to +0.04) | +0.03 | +0.04 |
| Current CGM user | -0.14 (-0.27 to 0.00) | +0.04 | +0.18 | +0.09 | -0.02 (-0.07 to +0.03) | 0.00 | -0.02 |
| Impaired hypo awareness | -0.04 | +0.01 | +0.17 | +0.09 | -0.01 (-0.04 to +0.04) | 0.00 | -0.01 |
| Hypo fear score | -0.03 | -0.09 | +0.17 | +0.09 | -0.01 (-0.05 to +0.02) | -0.01 | -0.02 |
| Fingersticks per day | -0.21 (-0.33 to -0.08) | -0.03 | +0.17 | +0.09 | -0.04 (-0.09 to +0.01) | -0.02 | -0.06 |
| Number of conditions | -0.16 (-0.29 to -0.02) | -0.17 (-0.28 to -0.05) | +0.17 | +0.08 | **-0.04 (-0.08 to -0.01)** | -0.06 (-0.23 to +0.13) | -0.10 (-0.27 to +0.10) |
| Education years | -0.12 (-0.24 to 0.00) | +0.02 | +0.18 | +0.08 | -0.02 (-0.06 to +0.02) | +0.01 | -0.01 |
| Self-reported lows per month | +0.09 | +0.30 (+0.17 to +0.42) | +0.16 | +0.12 | **+0.05 (+0.01 to +0.09)** | -0.08 (-0.21 to +0.07) | -0.03 (-0.17 to +0.14) |
| Hypo fear: behaviour | -0.03 | -0.13 | +0.18 | +0.09 | -0.02 (-0.06 to +0.02) | -0.01 | -0.03 |

Reading: three chains exist and all are tiny. Younger people swing more and spend more time low, and that costs them 0.07 SD of MARD (0.3 points per 14 years of age); their direct effect is +0.04, so the total is nothing. People with more listed conditions swing less (they are older), worth -0.04 SD. People who report more lows per month do spend more time low (a 0.30 SD link, which says the questionnaire is honest), worth +0.05 SD of MARD. HbA1c pulls both ways (higher HbA1c = more swings but less time low) and nets to nothing. No chain carries even half a MARD point. With low-range MARD as the outcome (8 traits, JSON `mediation_low_mard`) no indirect CI excludes 0. Figure 32, left.

## 10. Block f: the worst quartile
MARD above 14.3 % (57 people) vs the rest (169). 70 tests; none passed BH (smallest BH p 0.17). The traits with raw p < 0.05, plus the pre-specified six:

| Trait | Rest (n 169) | Worst quartile (n 57) | Raw p | BH p |
|---|---|---|---|---|
| Glucose CV, median | 36.7 % | 39.2 % | 0.003 | 0.17 |
| Number of medications, median | 4 | 3 | 0.005 | 0.26 |
| % time below 70, median | 3.2 | 4.0 | 0.01 | 0.35 |
| Education: no bachelor's | 17 % | 34 % | 0.03 | 0.37 |
| Days of CGM data, median | 231 | 244 | 0.03 | 0.37 |
| Moderate hypo needing help, past 6 months | 5 % | 14 % | 0.04 | 0.45 |
| Number of conditions, median | 4 | 2 | 0.04 | 0.43 |
| Sex: male | 49 % | 56 % | 0.36 | 0.82 |
| Age, median | 43 | 43 | 0.78 | 1.00 |
| BMI, median | 26.5 | 27.3 | 0.13 | 0.65 |
| HbA1c, median | 7.4 | 7.0 | 0.18 | 0.70 |
| Duration, median | 21 | 23 | 0.65 | 0.93 |
| Arm: CGM+BGM | 35 % | 32 % | 0.75 | 0.99 |

The worst quartile swings more and spends more time low; otherwise it looks like everyone else.

Same check for the missed-low rate (above 40.4 %, 39 people vs 187): men 72 % vs 46 % (p 0.004, BH 0.25); age 55 vs 40 (p < 0.001, BH 0.13); HbA1c 6.9 vs 7.4 (p 0.02, BH 0.36); age at diagnosis 25 vs 17 (p 0.02); hyperlipidaemia 62 % vs 41 % and statin 62 % vs 41 % (p 0.02 each); any thyroid condition 15 % vs 33 % (p 0.03); fewer fast-changing pairs (28 vs 31 %, p 0.02) and more fingerstick pairs per day (3.6 vs 3.1, p 0.01). Nothing passes. The pattern (older men with tight control who test often and whose glucose moves slowly) is coherent and worth one sentence in the paper as a lead, not a finding.

## 11. Block g: Shanghai
76 patients with 10+ pairs (3,926 pairs). Median MARD 11.9 % (IQR 9.5-17.3); bias -8.0 % (reads low); within 20/20 85.3 %. Type 1: MARD 15.7 % (n 10), type 2: 11.8 % (66). 60 tests; 1 raw p < 0.05 (3 expected); nothing passes BH (smallest BH p 0.97). Every result (groups: median; continuous: rho; "detectable" = smallest difference the group sizes could find):

| Trait | MARD: groups or rho | p | Bias: groups or rho | p |
|---|---|---|---|---|
| Diabetes type (T2 vs T1) | 11.8 vs 15.7; -3.9 (CI -8.8 to +1.7; detectable 7.3) | 0.25 | -8.0 vs -9.1 | 0.54 |
| Sex (M vs F) | 11.9 vs 11.9; 0.0 (CI -3.9 to +3.9) | 0.97 | -7.4 vs -9.2 | 0.77 |
| Age | rho +0.15 (CI -0.06 to +0.36) | 0.20 | rho -0.24 (CI -0.45 to -0.02) | 0.03 |
| Age tertile (<=57, 57-66, >66) | 10.9, 14.7, 13.4 | 0.39 | -5.1, -9.4, -10.7 | 0.12 |
| BMI | rho +0.19 | 0.11 | rho -0.13 | 0.26 |
| HbA1c | rho -0.21 (CI -0.42 to +0.05) | 0.08 | rho +0.10 | 0.42 |
| HbA1c tertile (<=7.6, 7.6-10.5, >10.5) | 12.2, 14.9, 10.9 | 0.19 | -9.2, -10.8, -7.3 | 0.62 |
| Diabetes duration | rho +0.07 | 0.54 | rho -0.18 | 0.12 |
| Smoking history (yes vs no) | 11.7 vs 11.9 | 0.89 | -8.0 vs -8.0 | 0.43 |
| Alcohol drinker | 14.6 vs 11.8 (CI -3.6 to +8.2) | 0.70 | -11.6 vs -7.7 | 0.25 |
| Any macrovascular complication | 12.6 vs 11.4 | 0.62 | -10.8 vs -6.2 (CI -8.2 to -0.1) | 0.10 |
| Any microvascular complication | 13.8 vs 11.6 | 0.51 | -10.0 vs -6.3 | 0.12 |
| Any other condition listed | 11.8 vs 15.6 | 0.51 | -7.8 vs -8.1 | 0.59 |
| Hypoglycaemia recorded | 14.5 vs 11.8 | 0.40 | -6.4 vs -8.1 | 0.83 |
| On insulin | 11.8 vs 13.4 | 0.57 | -7.5 vs -11.2 | 0.46 |
| Treatment (insulin only, insulin + oral, oral only) | 11.3, 11.9, 12.8 | 0.77 | -7.5, -8.3, -10.9 | 0.86 |
| eGFR | rho -0.04 | 0.75 | rho -0.07 | 0.55 |
| Fasting C-peptide | rho 0.00 | 0.99 | rho +0.08 | 0.55 |
| Fasting plasma glucose | rho -0.02 | 0.83 | rho -0.04 | 0.75 |
| Smoking pack-years | rho +0.01 | 0.92 | rho -0.11 | 0.35 |

Within 20/20: all p 0.18 or more (JSON). The one raw signal (older patients, sensor reads lower: rho -0.24) is what 60 tests produce by chance. Group sizes can only detect differences of 5-10 MARD points. Missed lows: only 37 fingersticks below 70 in the whole cohort (15 patients), 40 % missed pooled, too few for per-patient rates. Interactions and flexible models were not run (n 76).

## 12. Follow-ups on the two strongest signals (ad hoc, labelled as such)

### 12a. Sex and low-range bias
The one result that passed the whole-list BH. Where does it live?

| Pairs | Women: bias (n) | Men: bias (n) | Men minus women (CI) | p | Median error, mg/dL (W / M) |
|---|---|---|---|---|---|
| Below 54 mg/dL | -5.8 % (18) | -0.5 % (13) | +5.4 (-4.4 to +12.0) | 0.06 | -4.3 / -1.6 |
| 54-69 mg/dL | -5.6 % (70) | -1.4 % (65) | +4.2 (+2.6 to +6.3) | <0.001 | -4.9 / -2.3 |
| Below 70 (the tested outcome) | -6.4 % (76) | -2.2 % (74) | +4.2 (+1.9 to +6.2) | <0.001 | -5.2 / -2.4 |
| 70-180 mg/dL | -1.8 % (112) | -1.8 % (114) | 0.0 (-0.9 to +1.1) | 0.30 | -4.6 / -4.7 |
| Above 180 mg/dL | -0.9 % (111) | -1.8 % (112) | -0.9 (-1.9 to -0.2) | 0.002 | -5.3 / -7.8 |
| Calibration pairs below 70 (other pair type) | -11.9 % (68) | -7.6 % (67) | +4.3 (+1.8 to +9.7) | <0.001 | -9.6 / -6.3 |
| Below 70, sensor day 1 | -11.0 % (18) | -5.6 % (17) | +5.4 (-0.9 to +9.6) | 0.22 | -8.2 / -5.4 |
| Below 70, sensor days 2+ | -3.6 % (69) | -0.3 % (65) | +3.3 (+0.8 to +5.2) | <0.001 | -3.5 / -1.5 |

- It is a low-range thing. In the mid range the two sexes are identical; above 180 the sign flips and the gap is under 1 point.
- It repeats in calibration pairs (a different selection of fingersticks) and after sensor day 1.
- Adjusting for age, BMI, HbA1c, duration, arm, CV and time below 70: +4.0 (CI +2.0 to +6.0). Adding weight: +4.0 (weight itself 0.00 per kg). Adding how low the person's low pairs were (mean fingerstick of low pairs): +2.4 (CI +1.1 to +3.8). Within each sex, weight does not go with low-range bias (rho -0.04 in women, +0.14 in men). So it is not body size.
- Selection check: women and men had low pairs at the same depth (mean fingerstick 62.5 vs 61.5 mg/dL), the same number of them (39 vs 30 median), and the same time below 70 (3.4 vs 3.6 %).
- By arm: CGM-only +6.2 (CI +3.3 to +8.6, n 101); CGM+BGM +1.8 (CI -1.6 to +3.6, n 49); sex x arm interaction p 0.02 (BH 0.36). The CGM+BGM arm is the randomised check set, and there the gap is small and not significant. The two arm estimates do not clearly disagree (the CIs overlap), but this is the reason for caution.
- What it means in mg/dL: at 60 mg/dL a 4.2-point bias gap is about 2.5 mg/dL. Pooled over low pairs, the sensor read 10 or more mg/dL below the fingerstick in 32 % of women's low pairs and 27 % of men's.
- Knock-on: because the sensor reads lower in women at low glucose, it misses fewer of their lows (27.5 vs 33.9 %, raw p 0.002, BH 0.16) and may show more false lows (42.6 vs 38.9 %, p 0.18).
- Verdict: statistically detectable, small in mg/dL, coherent across checks, weak in the randomised arm, and with no mechanism we can name (guess: sensor-site tissue differences, but this data cannot say). Report as "one exploratory lead" with its caveats, not as a finding. It does not change the paper's message: low-range MARD is the same in both sexes (17.5 vs 17.6 %).

### 12b. Number of medications and MARD
Rho -0.24 (BH p 0.05 on the whole list; 0.049 within block a). By tertile: 0-2 drugs 12.8 %, 3-5 drugs 12.6 %, 6+ drugs 11.5 % (most vs fewest -1.4, CI -2.6 to -0.6).

| Check | Result |
|---|---|
| Who takes more drugs | older people (rho +0.47 with age), with more conditions (rho +0.68), calmer glucose (rho -0.23 with CV) and less time low (rho -0.28) |
| Regression, MARD per drug listed, unadjusted | -0.14 points (CI -0.36 to +0.08, p 0.22); the rank correlation is stronger than the linear one because of the two outliers |
| Adjusted for age, CV, % time below 70 | -0.12 (CI -0.38 to +0.14, p 0.36); CV stays (+0.18 per 1 %, p 0.05) |
| Also adjusted for number of conditions | -0.10 (p 0.34) |
| log MARD, adjusted | -1 % per drug (p 0.17) |
| Calibration pairs (other pair type), adjusted | +0.01 (p 0.81): not there at all |
| Low-range MARD | rho -0.03 (p 0.76) |

Verdict: the same story as "more conditions, lower MARD" in the first pass. People on more drugs are older and have calmer glucose; once that is in the model nothing is left, and the link is absent in calibration pairs. Not a finding.

## 13. What is a finding, what is not
1. Finding (null, strong): who the person is does not predict sensor error. 67 traits, 7 error measures, 18 pairs of traits, 14 sites, three model types, two cohorts: the only thing that predicts a person's MARD is the person's glucose pattern, and even that only weakly (3-6 % of the spread). This confirms the first pass with far more effort behind it.
2. Finding (null, strong): no combination of traits is a bad group. Every 2x2 cell median sits between 11.3 and 13.0 %.
3. Finding (null): location does not matter. Site ICC 0.035 for MARD, and it shrinks to 0.013 once the patients' glucose pattern is in the model.
4. Lead, not a finding: the sensor reads about 2.5 mg/dL lower in women than in men in the low range, with fewer missed lows in women. Passes BH, small, weaker in the randomised arm. Needs an outside dataset.
5. Lead, not a finding: older men with tight control, who test often, have the highest missed-low rates. Nothing in that list passes BH.

## 14. Null results that matter
- Race, ethnicity, education, income, insurance: no link to any of the seven error measures (all BH p 0.46 or more). But 94 % of the cohort is White and 77 % has a degree, so only a difference of 2-3 MARD points in the minority groups could have been seen.
- Hypoglycaemia awareness (7 questionnaire items), hypo fear (3 scores), diabetes technology attitudes: nothing (all raw p 0.06 or more on every outcome). People who say they sometimes miss their lows do not have a sensor that misses more lows (missed-low rate 29.5 vs 30.6 %).
- Prior CGM use, brand, years of use, pump family, receiver model, insulin type: nothing.
- HbA1c, duration, age at diagnosis, DKA or severe-hypo history, every listed condition, statins: nothing after correction.
- Study arm, run-in type and length, days of data: nothing after correction.
- The flexible models did not find any hidden pattern or interaction (R-squared below 0 for demographics in every run).
- Shanghai: nothing in 60 tests; type 1 vs type 2 (-3.9 points, CI -8.8 to +1.7) is the only difference that could still hide a real effect.

## 15. Caveats
- 680 tests in one family is deliberately harsh. A real but small effect (under about 1.5 MARD points, or rho under 0.2) would fail here. The secondary within-block BH (in the JSON) passes the same one result plus medications vs MARD (BH 0.049), so the conclusion does not depend on the family size.
- Groups under 10 people were not tested (Hispanic, Medicaid, uninsured, gastroparesis, acetaminophen users, drop-outs). Nine "low variance" traits were tested but could only show large effects.
- The missed-low and false-low rates exist only for people with 20+ low readings (156 and 174 people), who are the people who go low more often.
- Interaction tests on 226 people have little power: a difference-of-differences under about 2 MARD points cannot be seen.
- The flexible models have 226 rows and 94 columns; out-of-fold R-squared near 0 can mean "nothing there" or "too little data to learn it". The three-column glucose set reaching 0.03-0.14 shows the method can find a signal when one exists.
- Mediation is correlational; the chains are shown in SD units and all are small.
- Site is confounded with region, clinic practice and who enrols; with 8-27 people per site, the ICC CIs are wide (upper bounds 0.2).
- Shanghai: in-patients, 15-minute rows, 3-14 days; different sensor; no site variable.
- The reference is a home meter (ISO 15197 allows 15 mg/dL or 15 % error), so a 2.5 mg/dL sex gap is small against meter error, though meter error has no reason to differ by sex.

## 16. How to run
`python analysis/subgroups.py "Uncommitted Data/Raw Data Dump" analysis` first (it writes `cache/participant_metrics.parquet`), then `python analysis/demographics_deep.py "Uncommitted Data/Raw Data Dump" analysis` (150 s with the cache; seed 600; 2,000 bootstrap resamples, 1,000 for mediation and the site x arm permutation, 2,000 permutations for the ICC; 5-fold cross-validation x 10 repeats). Outputs: `demographics_deep_stats.json`, figures 29-32, and the markdown tables printed to the screen. Reads 7 raw tables directly (hypoglycaemia-awareness, hypo-fear and technology questionnaires, medications, medical conditions, insulin) plus the cache.

## Appendix A. Every trait x every outcome (block a)
Cell = effect; raw p; BH p over the whole list. Groups: the largest absolute difference in median vs the first group (points of the outcome). Continuous traits: rho. n.t. = not testable (a group under 10 people, or no low-range value for enough people). Group medians and CIs for every row are in the JSON (`univariate`).

| Trait | MARD | Low-range MARD | Bias | Low-range bias | Missed-low | False-low | Within 20/20 |
|---|---|---|---|---|---|---|---|
| Sex | 0.0; 0.92; 1.00 | 0.1; 0.97; 1.00 | 0.3; 0.97; 1.00 | 4.2; <0.001; 0.016 | 6.4; 0.002; 0.16 | 3.7; 0.18; 0.70 | 0.3; 0.55; 0.91 |
| Age (years) | -0.16; 0.01; 0.36 | -0.05; 0.58; 0.92 | +0.04; 0.52; 0.91 | +0.03; 0.69; 0.97 | +0.20; 0.01; 0.36 | +0.16; 0.03; 0.37 | +0.17; 0.01; 0.35 |
| Age group | 1.2; 0.08; 0.52 | 1.0; 0.51; 0.91 | 0.4; 0.50; 0.91 | 1.0; 0.54; 0.91 | 6.3; 0.09; 0.54 | 5.3; 0.20; 0.71 | 3.5; 0.06; 0.46 |
| Race (not White vs White) | 0.4; 0.80; 1.00 | n.t. | 0.3; 0.21; 0.72 | n.t. | n.t. | n.t. | 0.5; 0.76; 0.99 |
| Ethnicity | n.t. | n.t. | n.t. | n.t. | n.t. | n.t. | n.t. |
| Education | 0.6; 0.25; 0.74 | 0.6; 0.54; 0.91 | 0.3; 0.85; 1.00 | 2.5; 0.10; 0.56 | 0.9; 0.86; 1.00 | 2.1; 0.46; 0.91 | 2.5; 0.20; 0.71 |
| Education (years, coded) | -0.11; 0.10; 0.56 | +0.04; 0.63; 0.93 | -0.02; 0.76; 0.99 | +0.03; 0.75; 0.99 | 0.00; 0.99; 1.00 | +0.04; 0.57; 0.92 | +0.10; 0.12; 0.61 |
| Income (answered only) | 1.0; 0.59; 0.92 | 1.9; 0.61; 0.93 | 0.2; 0.89; 1.00 | 2.2; 0.86; 1.00 | 2.6; 0.55; 0.91 | 2.7; 0.87; 1.00 | 4.2; 0.39; 0.87 |
| Answered the income question | 0.5; 0.34; 0.82 | 1.2; 0.12; 0.60 | 0.0; 0.49; 0.91 | 2.6; 0.06; 0.46 | 1.1; 0.45; 0.91 | 10.4; 0.14; 0.66 | 1.4; 0.41; 0.87 |
| Private insurance | 0.2; 0.66; 0.94 | 1.3; 0.28; 0.78 | 0.1; 0.48; 0.91 | 2.0; 0.70; 0.97 | 3.1; 0.57; 0.92 | 7.7; 0.62; 0.93 | 1.7; 0.39; 0.87 |
| Medicare | 0.6; 0.61; 0.93 | n.t. | 0.8; 0.29; 0.78 | n.t. | n.t. | 12.7; 0.07; 0.50 | 2.3; 0.74; 0.99 |
| Medicaid | n.t. | n.t. | n.t. | n.t. | n.t. | n.t. | n.t. |
| Other insurance | 0.5; 0.51; 0.91 | 1.9; 0.06; 0.46 | 1.2; 0.06; 0.48 | 4.7; 0.20; 0.71 | n.t. | 10.9; 0.24; 0.74 | 0.1; 0.93; 1.00 |
| No insurance | n.t. | n.t. | n.t. | n.t. | n.t. | n.t. | n.t. |
| BMI (kg/m2) | +0.13; 0.05; 0.46 | +0.09; 0.26; 0.74 | +0.09; 0.16; 0.68 | +0.11; 0.18; 0.70 | +0.04; 0.63; 0.93 | 0.00; 0.99; 1.00 | -0.18; 0.007; 0.29 |
| BMI group | 0.8; 0.07; 0.50 | 1.1; 0.32; 0.80 | 0.7; 0.40; 0.87 | 1.5; 0.32; 0.80 | 1.5; 0.44; 0.91 | 1.9; 0.59; 0.92 | 2.2; 0.02; 0.36 |
| Weight (kg) | +0.08; 0.22; 0.72 | +0.08; 0.34; 0.82 | +0.07; 0.28; 0.78 | +0.24; 0.003; 0.17 | +0.15; 0.06; 0.48 | +0.01; 0.86; 1.00 | -0.16; 0.02; 0.36 |
| Height (cm) | -0.07; 0.31; 0.80 | -0.02; 0.79; 1.00 | -0.02; 0.81; 1.00 | +0.22; 0.006; 0.28 | +0.16; 0.05; 0.46 | +0.02; 0.78; 1.00 | +0.01; 0.93; 1.00 |
| HbA1c at screening (%) | -0.08; 0.22; 0.72 | +0.07; 0.36; 0.83 | -0.01; 0.91; 1.00 | -0.11; 0.19; 0.71 | -0.10; 0.22; 0.72 | +0.06; 0.46; 0.91 | +0.04; 0.56; 0.91 |
| HbA1c group | 0.7; 0.32; 0.80 | 0.7; 0.58; 0.92 | 0.3; 0.34; 0.82 | 3.1; 0.05; 0.46 | 7.7; 0.10; 0.56 | 7.6; 0.82; 1.00 | 0.7; 0.70; 0.97 |
| HbA1c change to week 26 | +0.02; 0.79; 1.00 | -0.03; 0.70; 0.97 | +0.11; 0.10; 0.56 | -0.07; 0.42; 0.89 | +0.07; 0.42; 0.89 | +0.09; 0.23; 0.72 | -0.05; 0.43; 0.89 |
| Diabetes duration (years) | -0.09; 0.20; 0.71 | +0.18; 0.03; 0.37 | -0.05; 0.44; 0.90 | +0.07; 0.39; 0.87 | +0.02; 0.84; 1.00 | +0.04; 0.59; 0.92 | +0.09; 0.20; 0.71 |
| Diabetes duration tertile | 0.3; 0.55; 0.91 | 2.0; 0.04; 0.45 | 0.2; 0.65; 0.94 | 1.4; 0.62; 0.93 | 0.6; 0.89; 1.00 | 1.9; 0.65; 0.94 | 1.4; 0.24; 0.73 |
| Age at diagnosis (years) | -0.07; 0.32; 0.80 | -0.19; 0.02; 0.36 | +0.13; 0.06; 0.46 | 0.00; 0.98; 1.00 | +0.15; 0.05; 0.46 | +0.08; 0.31; 0.80 | +0.08; 0.20; 0.71 |
| Fingersticks per day at screening | -0.09; 0.16; 0.68 | -0.04; 0.64; 0.94 | -0.12; 0.07; 0.50 | -0.01; 0.86; 1.00 | +0.10; 0.21; 0.72 | +0.13; 0.09; 0.54 | +0.10; 0.15; 0.68 |
| Severe hypoglycaemia history | 0.7; 0.11; 0.59 | 0.1; 0.56; 0.91 | 0.5; 0.13; 0.65 | 0.9; 0.58; 0.92 | 0.7; 0.64; 0.94 | 2.0; 0.45; 0.91 | 0.6; 0.19; 0.71 |
| DKA history | 0.8; 0.16; 0.68 | 1.9; 0.02; 0.36 | 0.2; 0.86; 1.00 | 2.1; 0.15; 0.68 | 2.8; 0.27; 0.76 | 5.6; 0.05; 0.46 | 1.6; 0.19; 0.70 |
| Non-insulin glucose-lowering drug | 0.0; 0.90; 1.00 | n.t. | 0.5; 0.50; 0.91 | n.t. | n.t. | n.t. | 1.1; 0.91; 1.00 |
| Insulin in the pump | 0.6; 0.70; 0.97 | 1.5; 0.67; 0.95 | 0.8; 0.34; 0.82 | 2.1; 0.75; 0.99 | 2.2; 0.48; 0.91 | 6.9; 0.23; 0.73 | 1.0; 0.90; 1.00 |
| Symptoms when glucose is low | 0.1; 0.65; 0.94 | 1.2; 0.24; 0.73 | 0.4; 0.80; 1.00 | 2.3; 0.25; 0.74 | 1.2; 0.95; 1.00 | 1.1; 0.87; 1.00 | 1.0; 0.34; 0.82 |
| Has lost some low-glucose symptoms | 0.6; 0.31; 0.80 | 0.5; 0.73; 0.99 | 0.5; 0.32; 0.80 | 1.5; 0.25; 0.74 | 0.6; 0.17; 0.69 | 5.5; 0.47; 0.91 | 1.4; 0.56; 0.91 |
| Moderate hypo needing help, past 6 months | 1.5; 0.16; 0.68 | n.t. | 0.7; 0.82; 1.00 | n.t. | n.t. | n.t. | 2.9; 0.19; 0.71 |
| Lows with symptoms, past month | 0.7; 0.20; 0.71 | 1.0; 0.88; 1.00 | 1.1; 0.08; 0.51 | 0.5; 0.83; 1.00 | 2.7; 0.53; 0.91 | 1.0; 0.83; 1.00 | 2.3; 0.14; 0.66 |
| Lows with symptoms (0-5 score) | 0.00; 1.00; 1.00 | -0.07; 0.40; 0.87 | -0.11; 0.09; 0.56 | -0.02; 0.80; 1.00 | 0.00; 0.98; 1.00 | -0.03; 0.73; 0.99 | -0.01; 0.86; 1.00 |
| Lows without symptoms, past month | 0.1; 0.80; 1.00 | 0.9; 0.25; 0.74 | 1.0; 0.02; 0.36 | 1.2; 0.38; 0.86 | 2.7; 0.52; 0.91 | 3.2; 0.95; 1.00 | 1.1; 1.00; 1.00 |
| Glucose where symptoms start | 0.3; 0.58; 0.92 | 1.1; 0.10; 0.56 | 0.1; 0.67; 0.95 | 1.5; 0.43; 0.89 | 2.3; 0.48; 0.91 | 6.6; 0.08; 0.51 | 0.6; 0.96; 1.00 |
| How often symptoms appear when low | 0.2; 0.56; 0.91 | 0.1; 0.91; 1.00 | 0.1; 0.49; 0.91 | 1.2; 0.17; 0.68 | 2.0; 0.85; 1.00 | 3.4; 0.34; 0.82 | 0.4; 0.42; 0.89 |
| Hypoglycaemia fear score | -0.04; 0.59; 0.92 | -0.05; 0.51; 0.91 | 0.00; 0.97; 1.00 | 0.00; 0.96; 1.00 | -0.04; 0.62; 0.93 | 0.00; 0.95; 1.00 | 0.00; 0.94; 1.00 |
| Hypo fear: worry items | -0.04; 0.55; 0.91 | -0.06; 0.46; 0.91 | -0.03; 0.70; 0.97 | +0.03; 0.75; 0.99 | -0.06; 0.49; 0.91 | -0.04; 0.62; 0.93 | +0.02; 0.74; 0.99 |
| Hypo fear: behaviour items | -0.01; 0.84; 1.00 | -0.02; 0.76; 0.99 | +0.05; 0.43; 0.89 | -0.04; 0.62; 0.93 | 0.00; 0.98; 1.00 | +0.06; 0.43; 0.89 | -0.05; 0.49; 0.91 |
| Diabetes technology questionnaire | +0.07; 0.30; 0.80 | +0.01; 0.91; 1.00 | +0.12; 0.07; 0.49 | +0.08; 0.33; 0.80 | -0.03; 0.74; 0.99 | -0.11; 0.15; 0.68 | 0.00; 0.98; 1.00 |
| Number of listed conditions | -0.21; 0.001; 0.14 | +0.03; 0.75; 0.99 | +0.01; 0.90; 1.00 | +0.09; 0.26; 0.75 | +0.04; 0.62; 0.93 | +0.12; 0.13; 0.63 | +0.20; 0.002; 0.15 |
| Number of listed medications | -0.24; <0.001; 0.05 | -0.03; 0.76; 0.99 | +0.02; 0.79; 1.00 | +0.05; 0.53; 0.91 | +0.04; 0.59; 0.92 | +0.08; 0.30; 0.79 | +0.21; 0.001; 0.14 |
| Hyperlipidaemia | 0.7; 0.02; 0.36 | 0.2; 0.85; 1.00 | 0.2; 0.46; 0.91 | 1.1; 0.51; 0.91 | 0.6; 0.09; 0.54 | 3.4; 0.21; 0.72 | 1.4; 0.07; 0.50 |
| Hypertension | 0.6; 0.35; 0.83 | 0.5; 0.42; 0.89 | 0.2; 0.73; 0.99 | 1.9; 0.05; 0.46 | 6.0; 0.05; 0.46 | 2.2; 0.23; 0.72 | 0.9; 0.47; 0.91 |
| Hypothyroidism | 0.3; 0.95; 1.00 | 0.2; 0.82; 1.00 | 0.2; 0.82; 1.00 | 0.9; 0.50; 0.91 | 5.5; 0.05; 0.46 | 2.1; 0.70; 0.97 | 0.7; 0.85; 1.00 |
| Any thyroid condition | 0.1; 0.68; 0.96 | 0.1; 0.82; 1.00 | 0.1; 0.48; 0.91 | 2.5; 0.04; 0.45 | 7.2; 0.02; 0.36 | 0.8; 0.94; 1.00 | 0.8; 0.55; 0.91 |
| Depression | 0.8; 0.12; 0.61 | 0.3; 0.56; 0.91 | 0.2; 0.97; 1.00 | 2.4; 0.26; 0.75 | 4.5; 0.53; 0.91 | 0.6; 0.39; 0.87 | 1.5; 0.17; 0.69 |
| Anxiety | 1.0; 0.55; 0.91 | n.t. | 0.9; 0.35; 0.83 | n.t. | n.t. | 9.6; 0.09; 0.54 | 2.3; 0.73; 0.99 |
| Retinopathy | 1.3; 0.009; 0.35 | 0.2; 0.90; 1.00 | 0.1; 0.83; 1.00 | 1.4; 0.48; 0.91 | 2.5; 0.35; 0.82 | 2.4; 0.63; 0.93 | 2.1; 0.03; 0.37 |
| Neuropathy | 1.3; 0.17; 0.68 | 0.9; 0.28; 0.78 | 0.1; 0.82; 1.00 | 1.8; 0.75; 0.99 | n.t. | 8.4; 0.11; 0.60 | 3.2; 0.15; 0.68 |
| Kidney disease or albuminuria | 2.2; 0.10; 0.56 | n.t. | 0.6; 0.51; 0.91 | n.t. | n.t. | n.t. | 2.9; 0.09; 0.56 |
| Gastroparesis | n.t. | n.t. | n.t. | n.t. | n.t. | n.t. | n.t. |
| Any diabetes complication listed | 1.1; 0.01; 0.35 | 0.2; 0.35; 0.83 | 0.1; 0.75; 0.99 | 1.8; 0.31; 0.80 | 0.9; 0.53; 0.91 | 0.6; 0.95; 1.00 | 2.3; 0.02; 0.36 |
| Obesity listed as a condition | 0.7; 0.04; 0.45 | n.t. | 1.6; 0.02; 0.36 | n.t. | n.t. | 0.3; 0.70; 0.97 | 1.7; 0.07; 0.50 |
| Takes a statin | 0.7; 0.08; 0.53 | 0.4; 0.93; 1.00 | 0.1; 1.00; 1.00 | 1.2; 0.46; 0.91 | 4.0; 0.02; 0.36 | 3.8; 0.18; 0.70 | 1.4; 0.17; 0.69 |
| Acetaminophen-containing drug | n.t. | n.t. | n.t. | n.t. | n.t. | n.t. | n.t. |
| Study arm | 0.1; 0.54; 0.91 | 0.2; 0.85; 1.00 | 0.0; 0.89; 1.00 | 1.1; 0.50; 0.91 | 3.7; 0.06; 0.48 | 3.2; 0.07; 0.50 | 0.8; 0.12; 0.60 |
| Clinic site | 1.9; 0.03; 0.37 | 3.8; 0.03; 0.37 | 2.0; 0.06; 0.48 | 5.4; 0.14; 0.67 | 9.9; 0.73; 0.99 | 14.8; 0.63; 0.93 | 5.0; 0.13; 0.65 |
| Run-in CGM type | 0.3; 0.33; 0.81 | 0.3; 0.88; 1.00 | 0.5; 0.05; 0.46 | 0.8; 0.86; 1.00 | 2.1; 0.87; 1.00 | 1.4; 0.17; 0.69 | 0.8; 0.94; 1.00 |
| Run-in length (days) | +0.10; 0.15; 0.68 | +0.04; 0.59; 0.92 | +0.22; <0.001; 0.12 | -0.05; 0.54; 0.91 | +0.07; 0.41; 0.87 | -0.06; 0.47; 0.91 | -0.06; 0.39; 0.87 |
| Completion status | n.t. | n.t. | n.t. | n.t. | n.t. | n.t. | n.t. |
| Days of CGM data | +0.07; 0.27; 0.76 | +0.02; 0.79; 1.00 | +0.14; 0.03; 0.37 | -0.01; 0.87; 1.00 | +0.05; 0.53; 0.91 | -0.03; 0.68; 0.96 | -0.01; 0.88; 1.00 |
| Prior CGM use | 0.6; 0.65; 0.94 | 0.5; 0.56; 0.91 | 0.9; 0.04; 0.44 | 1.3; 0.68; 0.96 | 2.2; 0.97; 1.00 | 3.4; 0.44; 0.91 | 1.4; 0.92; 1.00 |
| CGM brand (current users) | 0.3; 0.95; 1.00 | 0.4; 0.61; 0.93 | 0.2; 0.62; 0.93 | 1.1; 0.65; 0.94 | 2.3; 0.31; 0.80 | 7.2; 0.06; 0.48 | 1.2; 0.87; 1.00 |
| Years of CGM use (current users) | 0.3; 0.76; 0.99 | 0.5; 0.59; 0.92 | 0.6; 0.81; 1.00 | 2.1; 0.50; 0.91 | 5.4; 0.47; 0.91 | 3.0; 0.98; 1.00 | 1.0; 0.67; 0.95 |
| Pump family | 0.9; 0.87; 1.00 | 1.3; 0.56; 0.91 | 1.1; 0.05; 0.46 | 3.1; 0.02; 0.36 | 6.1; 0.78; 1.00 | 6.9; 0.40; 0.87 | 2.0; 0.85; 1.00 |
| CGM receiver model | 0.8; 0.14; 0.66 | 0.3; 0.88; 1.00 | 1.0; 0.03; 0.37 | 0.6; 0.84; 1.00 | 0.6; 0.95; 1.00 | 4.6; 0.21; 0.72 | 1.8; 0.25; 0.74 |
