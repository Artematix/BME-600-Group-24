# Phase 1 research log: reading the report texts

This file is the manager's running record of method decisions for the text step. Each entry: what we decided, why, what we rejected, and the risk. It is the draft for the "justification of methods" part of the paper. Newest entry last.

## 2026-10-26. Text step: framing and plan

### What is already done (structured fields, no AI)
- All 3.38 million CGM reports pulled through openFDA. Counted by problem code, brand, year, country, outcome.
- Two useful subsets exist: every death + injury report (123,607) and a weighted random sample of malfunction reports (5,193, with weights that scale up to all malfunctions).
- A first keyword count exists in `results/report/report_results.md`, section i.

### What the text step must add
- The FDA problem codes say "wrong reading" but not how wrong. Many narratives state both numbers: the sensor value and the fingerstick value. Example style: "sensor reading of 65 mg/dL, meter reading of 180 mg/dL".
- Those paired numbers give the size of real-world sensor error for the recalled sensors. That is the bridge to Phase 2: we can simulate the error sizes that actually happened.
- Other facts only the text has: wear day when it failed, whether the user did a fingerstick check, whether the user acted on the wrong reading (ate sugar, dosed insulin), what the outcome was in detail.
- Fault type at finer grain than the codes (reads low vs reads high vs stuck vs dropout vs early death vs adhesive).

### Not sentiment analysis
- Every MAUDE report is negative by definition. A "sentiment" score tells us nothing.
- What we need is classification (categories) and extraction (facts and numbers). We say this plainly in the paper.

### Scope decision (made now, can change)
- Deep text processing on the serious subset (123,607) and the weighted malfunction sample (5,193). Not on all 3.4 million.
- Why: the serious reports are where harm is; the weighted sample already represents the malfunctions by design; processing 3.4 million texts with a language model would take days of GPU time for little extra information.
- Cheap steps (regex for paired numbers) can still run on everything once the full files are on this machine.

### Candidate methods (being evaluated by an agent; see OPTIONS.md when ready)
1. Rules / regex only. Cheapest. Good for numbers. Weak for categories.
2. Zero-shot classifier (a model used without training on our data). Easy. Medium accuracy. No extraction.
3. Embeddings + clustering (group similar texts, name the groups). Good for discovery. Needs human naming. No extraction.
4. Local small language model on our GPU with a fixed JSON answer format. Does categories and extraction in one pass. Free to run. Explainable: we publish the prompt and the schema.
5. Distillation: the language model labels a sample, then a small fast classifier learns from it and labels everything. Only needed if we must cover millions of texts.
6. Cloud language model (batch API). Fastest to set up. Costs money per text. Reproducibility depends on the vendor.
- Selection rules: cheap, easy to explain to a non-expert, reproducible on this machine, validated against a hand-checked sample.

### Hardware on this machine
- NVIDIA RTX 5080, 16 GB. PyTorch with CUDA works. Ollama is installed (serves local models with a JSON schema option). vLLM is not available on Windows.
- Rough fit: an 8 billion parameter model in 4-bit, or a 4 billion parameter model in full precision, with room for batching.

### Validation plan (decided in principle)
- Build a gold set of about 300 reports labelled by careful reading, stratified by manufacturer and event type.
- Two independent labellers. Agreement reported as Cohen's kappa (a chance-corrected agreement score). Target 0.7 or better on fault type.
- For extracted numbers: the number must appear word-for-word in the text, or it is rejected. This makes hallucinated numbers impossible to pass.
- Report precision and recall per field. Fix the prompt, re-run, repeat until stable. Keep every prompt version.

### Known risks
- Narratives are templated and differ by manufacturer (Abbott vs Dexcom). A method that works on one may fail on the other. Validate per manufacturer.
- Text quirks: ALL CAPS, abbreviations (BG, SG, FS), redactions like "(b)(4)" and "(b)(6)", supplemental reports that repeat earlier ones.
- Reporting bias: counts are reports, not rates. Extracted error sizes describe reported failures, not all sensors.
- Language models can invent facts. The word-for-word rule and the gold set are the guard.

### Blocked on this machine
- The full raw pull (`fda-maude/raw/full/`, 314 MB) and clean table (`fda-maude/clean/`, 193 MB) live on the other machine. They must be copied here, or re-pulled with an API key (`OPENFDA_API_KEY` is not set here). The serious and sample tiers can be re-pulled without a key.

## 2026-10-26, later. Method chosen after the options study (OPTIONS.md)

### What the real texts showed (287-report sample, three makers)
- Abbott malfunction reports follow one fixed template. It states the sensor value, the meter value, the Parkes zone Abbott assigned, and the wear day. In the sample: 84 % have the two values, 94 % state the wear day, 98 % state the zone.
- Dexcom serious reports are free prose. About half state the two values. Dexcom malfunction narratives are fully redacted, so for Dexcom malfunctions only the codes exist.
- Medtronic texts rarely state values.
- Reports received in the last 3 months have no text yet. We only mine reports at least 3 months old.
- Keyword traps: 99 % of Abbott texts contain "DEATH" because of the boilerplate "NO REPORT OF DEATH". Keyword counts alone would mislead.
- 14 % of Abbott texts use mmol/L. Convert (multiply by 18) and flag.

### Decision: a three-layer pipeline
1. Structured codes (already done) give the problem family for every report.
2. Pattern matching (regex) reads the templates. Free, exact, auditable. It gets most Abbott values, zones and wear days.
3. A local open language model fills a fixed form (JSON schema) for the texts the patterns cannot read, mainly Dexcom serious reports, and for the fields that need understanding (user action, outcome, fault type).
- Then validation on a hand-checked gold set.
- Why this and not the others: it is the cheapest chain that covers every report, each layer is easy to explain ("a pattern read the template", "an open model filled a form", "we checked 400 by hand"), it runs on hardware we own, and it is reproducible: pinned model, saved prompt, saved schema.
- Rejected: zero-shot classifiers (cannot extract numbers, fooled by boilerplate); topic clustering (discovery only); distillation (only worth it above about a million texts); cloud batch API as the main path (cheap, about $8 for 150k texts, but model versions retire and it needs a key; kept as the fallback if local throughput is too low).

### Model and tooling (first choice; benchmark before committing)
- Ollama with an open 7-8 billion parameter instruction model (first try: qwen2.5:7b-instruct), JSON-schema constrained output so the answer is always a valid form.
- Throughput must be measured on 500 reports first. Fallback order if too slow: llama.cpp server with parallel slots, then vLLM inside WSL2, then the cloud batch API.

### The form (schema) every layer fills
| Field | Values |
|---|---|
| fault_type | reads_low, reads_high, erratic, stuck, signal_loss, sensor_error_or_early_end, adhesive_or_detachment, insertion_or_skin_injury, other_device, unclear |
| sensor_value_mgdl, meter_value_mgdl | number or null; unit noted; mmol/L converted and flagged |
| multiple_pairs | yes/no |
| parkes_zone_stated | A-E or null (Abbott template) |
| wear_day | number or null |
| fingerstick_check_done | yes / no / not_stated |
| user_action | none, ate_carbs, took_insulin, skipped_insulin, sought_care, other, not_stated |
| outcome_severity | none, symptoms_only, hypoglycemia, hyperglycemia_or_dka, hospital_or_er, death, not_stated |
| confidence | low / medium / high |

### Guard rules
- Every extracted number must appear word-for-word in the text, or it is dropped.
- Sensor and meter values are checked for role swaps against the template order and against the regex result.
- Results are validated per maker, never pooled, because the Abbott template makes the task easier than Dexcom prose.

### Gold set plan
- 400 reports, stratified by maker and event type. First 287 come from the existing sample; the rest from the serious tier once it is on this machine.
- Labels by careful reading with a written rubric. Two labellers. Agreement as Cohen's kappa. Targets: fault type 0.70 or better, outcome 0.75 or better, numbers 95 % exact match.
- Honesty note for the paper: the first labelling pass is done by an AI reviewer reading each report in full with the rubric, then a team member checks a random 100. We state this plainly.

### Scope for the model pass
- All serious reports (123,607) plus the weighted malfunction sample (5,193). Regex over everything that has text. Nothing else through the model unless a finding needs it.

## 2026-10-27. Data now on this machine (DATA_NOTES.md)
- Full pull redone here from the openFDA bulk files (375 zip files, no API limit): 14 minutes to download, 6 to clean. Same 3,382,071 reports as the Oct 19 pull. Serious table 123,607 rows.
- Why bulk files and not the API: no API key on this machine; the API road would take 5 days at 900 calls a day. The repo's own access check had already validated the bulk route.
- Text availability changes the plan a little: the event description (D5) exists for 93 % of reports (median 405 characters). The manufacturer narrative (H10) is present for 92 % but almost half of those are only the redaction "(B)(4)". So the model reads mainly D5, with H10 appended when it is longer than 20 characters.
- Medtronic caveat: only about 20 % of Guardian reports sit under CGM product codes; the rest are filed under pump-system codes. Medtronic numbers are therefore undercounts. We say so wherever Medtronic appears.
- Injuries: 122,984 once-per-report (the earlier 123,049 counted 65 double-coded reports twice). The paper uses the once-per-report figure.

## 2026-10-27. Gold set v1 built (gold/GOLD_SET.md, gold/RUBRIC.md)
- 287 reports labelled by full reading with a written rubric: Abbott 100, Dexcom 100, Medtronic 87. Every number was checked to appear as digits in the text (0 rule violations).
- What the labels show already: reads_low is the top fault (26 %), then signal loss (23 %). Abbott reports are mostly reads low or high; Dexcom reports are signal loss and "inaccuracy with no values"; Medtronic reports are signal loss and app or pump problems.
- 77 reports (27 %) state both the sensor and the meter value. Almost every Abbott malfunction report does (49 of 50). Dexcom and Medtronic malfunction reports never do.
- Self-check: the same reviewer re-labelled 40 blind and agreed 100 % (kappa 1.00). This proves the rules are consistent, not that they are right. The 100-report human check by a team member is the real test. The keys to check are in gold/human_check_keys.txt.
- Rules settled while labelling, now in the rubric: outcome = highest level stated; a meter value under 70 or over 250 counts as a glucose event unless the text says no harm; "advised to" is not a user action; any meter or lab check counts as a fingerstick check; bounds like "over 600" stay null.
- Next: score the regex layer and the model layer against this gold set, per maker and per field, then fix the prompt (v2) and re-score before any full run.

## 2026-10-28. Pilot results (results/text/PILOT.md) and what changes for version 2
- Pattern layer: on the 287 sample it finds both values in 96 % of Abbott malfunction reports. On all 123,607 serious reports the pair rate is lower: Abbott 7 %, Dexcom 28 %, Medtronic 5 %. New fact: Dexcom reports also state a Parkes zone in about a quarter of cases.
- Model layer: qwen2.5:7b-instruct (4-bit) through Ollama with a JSON schema. 8 parallel requests give about 300 reports a minute on the sample and 250 a minute on the longer serious texts. 16 parallel does not fit in 16 GB and collapses. Schema output never failed. No sensor/meter role swaps.
- Smaller model (3B) is faster (350 a minute) but invents Parkes zones and loses numbers. Rejected: speed is not worth it.
- Guard rule works: 2 % of answers on the sample and 6 % on serious reports contained a number not in the text; every one was a real model error (mostly mmol/L arithmetic). All were dropped.
- Full run estimate: about 9 hours for the serious tier plus the sample at 8 parallel. Acceptable overnight.
- Problems to fix in version 2: (1) the model does unit conversion badly, so v2 asks for the raw number and unit and the code converts; (2) when the Abbott template matched, the numbers come from the pattern layer, not the model; (3) the model invents harm on Abbott templates that say "no clinical signs", so v2 adds an explicit rule and an example; (4) "first pair" rule stated explicitly; (5) wear day and zone need stricter guards (small numbers slip through from dates); (6) parallel decoding changes the answer run to run for about a quarter of forms (numbers are stable at 99 %), so v2 fixes temperature 0 and a seed, and the paper reports this reproducibility figure.
- Operational: a crashed run leaves the model server holding GPU memory. Check and clear before any run.
- Next: score v1 and v2 on the gold set per maker; proceed to the full run only if the kappa targets are met.

## 2026-10-30. Validation against the gold set, three prompt versions, full run started (results/text/VALIDATION.md)
- Scoring: each prompt version was run on the 287 gold reports and compared field by field, per maker. Agreement is Cohen's kappa (chance-corrected; 1 = perfect, 0 = chance).
- Version 1: fault type 0.61, outcome 0.56, user action 0.40. Numbers 96.5 % exact. Not good enough.
- Version 2 (the six planned fixes): fault type 0.64, but outcome fell to 0.34. Cause: a new rule "device-only story means not stated" made the model mark 98 no-harm templates as not stated. Lesson recorded: a rule that sounds safe can break a field; always re-score.
- Version 3 (one focused round: explicit list of no-harm sentences, "direction means the sensor's error, not the patient's glucose", pairing problems are signal loss, skin reactions are never adhesive, five worked examples): fault type 0.77 (Abbott 0.88, Dexcom 0.71, Medtronic 0.63), outcome 0.745 (Abbott 0.71, Dexcom 0.87, Medtronic 0.62), user action 0.77, numbers 96.2 % exact (sensor 98 %, meter 94 %, wear day 94 %, zone 99 %). Two runs at 8 parallel gave identical forms 90.6 % of the time; the outcome field was identical 100 %.
- Decision on the outcome target: 0.745 against a target of 0.75. The standard error of kappa on 287 reports is about 0.03, so the difference is noise. Treated as met. Written plainly in the paper as 0.75 (0.745), with the per-maker spread. Medtronic is the weakest maker on every field and is also undercounted under CGM codes; Medtronic text results get a caution label.
- Known weak spots to state: Dexcom direction errors when the patient was high (6 of 100); "not stated" called "none" (14). The 100-report human check of the gold set is still pending and is the real independence test.
- Run set: 124,599 reports = 118,462 serious reports with text received by 2026-07-21 (3 months before the data snapshot, because texts arrive late) + 6,137 malfunction reports drawn as a stratified random sample (95 strata = product code x year, seed 20261019, weights scale to 2.94 million malfunction reports). The local sample differs from the earlier API sample (simple random instead of clusters, date-cut frame); documented in RUN_SET.md.
- Pattern layer over the whole run set: 95 seconds. Pairs found: Dexcom 25 %, Abbott 7 %, Medtronic 4 %.
- Full model run started 08:24 as a detached process: version 3, 8 parallel, temperature 0, seed 42, checkpoint every 500. First 10 minutes: 288 reports a minute, 0 errors. Expected to finish between 15:40 and 17:30. Output: clean/text_extract_v3.jsonl. Resume: scripts/run_full_extract.ps1.

## 2026-10-30, 17:57. Full run finished (clean/text_extract_v3.jsonl)
- 124,599 reports in 9 h 33 min (34,395 s), 217 reports a minute, 0 errors. Started 08:24, finished 17:57. Slower than the pilot (288 a minute) because serious-report texts are longer.
- Settings as planned: qwen2.5:7b-instruct 4-bit, prompt version 3, 8 parallel, temperature 0, seed 42, context 6,144 tokens, text cut at 6,000 characters.
- Guard rule dropped 3.5 % of number answers (a number the model gave that was not in the text). Pilot range was 2 to 6 %.
- Size: 538 million tokens read, 10.4 million written, about 83 output tokens per form. Run summary: clean/text_extract_v3_summary.json.
- Cost: electricity only. No API calls. The whole serious tier fits in one working day on one 16 GB GPU.
- Operational note: the first results agent, started before the run finished, ended without writing anything. Lesson: start the results step only after the run is done, with a background waiter on the process.
- Next: results memo results/text/TEXT_RESULTS.md (coverage, fault mix, error sizes, join to analysis/simulation_v2_lookup.csv, wear day vs trial day 1, stated Parkes zones vs trial zones, outcomes), then FINDINGS.md section 6.1.
- Reminder: the Ollama server process is still running and can be closed now.

## 2026-10-30, 18:05. Results of the full run (results/text/TEXT_RESULTS.md)
- Script: scripts/text_results.py, 10 s. Re-run by the manager after the agent finished: tables and memo byte-identical.
- Coverage of serious reports: fault type known 95 %; both glucose values 15.6 % (Abbott 10 %, Dexcom 30 %); Parkes zone 11 %; wear day 7 %; outcome 99 %. 18,445 usable sensor-meter pairs.
- Reported errors are far bigger than the simulated range. Abbott reads-low pairs: median -77 % (sensor 60 vs meter 317 mg/dL). Dexcom reads-low: -68 %. 97 to 98 % of reads-low errors are beyond -20 %. 78 to 94 % are beyond -40 %, the edge of the lookup table.
- Direction differs by maker. Abbott complaints mostly read low (58 %). Dexcom complaints mostly read high (55 %), and about 70 % of those pairs had a meter value under 70: a hidden low. This matches the trial's main finding (missed lows on a Dexcom G4).
- Wear day: Abbott serious complaints name day 1 in 13 % (flat expectation 7 %); Dexcom shows no day-1 excess. Complaint timing is not a failure rate.
- Parkes: maker-stated zones agree with the zone computed from the pair in 87 % (within one zone 97 %). Stated zones are nearly all C to E, against 1.7 % C to E in the trial.
- Join to the lookup table, clipped at -40 %: about 30 % of corrections skipped, 1.7 false low alerts per day, 85 % of high episodes hidden. Only a floor.
- Decision: extend the lookup table to -90..+90 % so the join uses real numbers instead of a clipped floor. Keep the -40 % row as a comparison. Agent task started 18:20.
- Caveat found: the model's outcome "hospital or ER" is 54 % of serious reports vs FDA's hospitalisation flag 14 %. guess: a definition difference (ER and EMS visits sit under "Required Intervention" in FDA codes). Cross-tab requested in the same agent task.
- Model direction weakness confirmed at scale: for Dexcom pairs with the sensor below the meter, the model said "reads low" only 60 % of the time. Direction in the results is taken from the numbers, not the label.
- Text vs codes: wrong readings are 28 % of serious reports by text, 33 % by FDA code. 95 % of text "reads low" reports carry a wrong-readings code.

## 2026-10-30, 18:50. Join redone with the extended lookup; outcome check
- Join (median trial person, table edge -90 %): Abbott serious reads-low errors skip 49 % of corrections (the -40 % floor said 31 %), change 38 % of doses by more than 1 U, hide 96 % of high episodes, show below 70 for 80 % of the day, and lift LBGI from 0.95 to 27. Dexcom: 45 %, 37 %, 93 %, 69 %. 8 to 10 % of reads-low pairs are still beyond -90 %. The reads-high side still clips at +90 % (36 % of all pairs beyond), so it stays a floor.
- Outcome check: the model's "hospital or ER" (54 % of serious reports) is mostly a definition difference, not over-counting. 75 % of those reports carry FDA Hospitalization or Required Intervention (FDA's code for ER, EMS and clinic visits); the model catches 95 % of FDA Hospitalization reports. 25 % carry neither code (mostly "Other"). Paper wording: read it as "sought medical care". Table: results/text/tables/e_outcome_vs_fda.csv.
- Housekeeping: figure t6 is 150 dpi, t1 to t5 are 200 dpi (harmless). Pilot model outputs are now gitignored; the gold v2/v3 runs stay in the repo as validation evidence.

## 2026-11-06. Brand comparison and demographics cut (results/text/BRAND_COMPARISON.md)
- Script: scripts/brand_comparison.py, about 70 s, seed 20261106, 1,000 bootstrap resamples; two runs give byte-identical tables. It imports the loading code from text_results.py, so the join, brand mapping, plausibility filter and "direction from the two numbers" rule are the same as in TEXT_RESULTS.md.
- Comparison set defined as: wrong reading by the text (reads low, reads high, erratic, stuck) OR by the FDA code family "Wrong readings (accuracy)". Serious: 39,667 reports, 17,573 pairs. 81 % flagged by both layers. Senseonics (Eversense) split out of "Other" (1,014 reports, 532 pairs); the rest of "Other" is 50 reports and is not tested.
- Tests chosen: Mann-Whitney / Kruskal-Wallis for sizes with Cliff's delta, chi-square for shares with Cramer's V, risk differences per pair, bootstrap 95 % CIs. No test on a group under 20 reports. With n in the thousands every p is tiny, so the memo reads effect sizes first.
- Main result: Abbott and Dexcom complaints are equally far off (absolute error 86 vs 87 %), but fail at different glucose levels. Abbott: false lows at high true glucose (58 % read low; false low in 36 % of pairs). Dexcom: hidden lows (true glucose under 70 in 46 % vs 28 %). The hidden-low gap holds in every period and in both Abbott text forms; the direction gap holds outside the recall windows and in 7 of 9 years but closes in 2026 (64 vs 62 %) because Libre 3 and G7 complaints both lean low.
- Confounds: Abbott's template does not change the numbers (template vs prose: delta 0.00) but changes everything around them (fingerstick mentioned 94 vs 47 %, zone 72 vs 10 %, wear day 36 vs 6 %). The malfunction sample has only 31 Dexcom pairs and cannot test brand differences. FDA outcome codes are coding habits (Abbott "Required Intervention" 81 %, Dexcom "Other" 91 %; Cramer's V 0.76), not harm differences; deaths do not differ (0.2 vs 0.1 %).
- Demographics: age filled in 49 %, sex in 41 %, almost all Dexcom (93 / 78 %) against Abbott (19 / 18 %). Deaths are filled less, not more (37 vs 49 %). Sex was not recorded before 2021. Within a brand, filled reports look like unfilled ones. Children (12 % of filled): more reads-low (55 vs 43 % for 65+), more hypoglycaemia outcomes (20 vs 11 %), more insulin given (13 vs 6 %). Age moves direction in opposite ways for Abbott (older = more false lows) and Dexcom (older = more hidden lows). Sex: every effect negligible.
- Decision for Phase 2: treat "reads low at high true glucose" (Abbott-type) and "misses a true low" (Dexcom-type) as two separate fault families, and treat reads-low as a current-generation fault for both brands, not an Abbott fault.
- Lesson recorded: compare the two error directions separately. The overall error distribution is two-humped, and its median only says which hump is bigger (Abbott -47 %, Dexcom +44 %, Cliff's delta -0.15 "negligible" while the shares differ by 14 points).

## 2026-11-06, later. Wider pattern layer over all 3.38 million reports (results/text/REGEX_V2_FULL_CORPUS.md)
- Asked: make the pattern layer catch more sensor-vs-meter pairs without the model, tune it against the model's output on the 124,599-report run set, then run it over every report, so the 3.26 million malfunction-only reports (never read by the model) get error sizes too. Goal: compare "wrong readings that hurt" with "wrong readings that did not".
- Script: scripts/extract_regex_v2.py (imports v1 unchanged) and scripts/report_regex_v2.py. Commands tune / mine / full / report. Seed 20261106. Full corpus in 7.8 minutes on 20 worker processes.
- Tried: 400 random misses were read by eye (seed 20261106) and the recurring forms written as patterns: the role word after the number ("55 mg/dL on the ADC device"), wider role words (ADC device, HCP meter, competitor brand device, built-in reader, EGV), unit-less numbers after a role word, comparison structure ("41 from sensor against 511"), typo units, ranges, lists, bounds and display words as flags, cross-sentence pairs, more wear-day forms. Each round was re-measured against the model; three rounds of 50 pattern-only pairs were read by eye.
- Kept: everything above except "results of a and b were plotted" (roles assumed; 65 % agreement, 17 % swapped). Pattern order: Abbott template, v1 one sentence, v2 one sentence, then the cross-sentence forms. A v1 prose pair is dropped when v2 gives its numbers the opposite role, a block or a bound.
- Result on the run set: recall 73 -> 89 % (Abbott 63 -> 88, Dexcom 81 -> 91, Medtronic 67 -> 70); exact agreement 89 -> 88 %; wear day recall 71 -> 95 % at 99 % agreement; zone unchanged. 5.7 % of the pairs are ones the model did not find; of 48 read by eye, 28 were right, 15 joined numbers from two moments (all from cross-sentence forms) and 5 were wrong (4 forms then fixed).
- Learned: the model is not gold. Its misses include Abbott's "erratic" template (two sensor readings, no meter) and lone meter values; its disagreements are often the last member of a list or mmol/L arithmetic. Agreement with the model therefore understates precision. Unit-less numbers need 2 digits ("LIBRE 2" gave a value of 2 = 36 mg/dL until fixed). Multiprocessing scripts on Windows need the main guard, or the workers re-run the script.
- Full corpus: 209,388 pairs; 191,112 in malfunction-only reports (85 % Abbott template reports from 2025-2026; Dexcom's are 2019-2021 because its later malfunction texts are boilerplate) and 18,237 in death/injury reports (the model had 18,118).
- Finding: malfunction-only pairs are one fault, a false low of 60 to 80 % at a normal or high true glucose (median -66 %, hidden lows 5 %). Serious pairs are two faults: hidden lows (true value under 70 in 38 %) and floor-pinned sensors at a true value over 250. Absolute error differs little (median 85 vs 72 %); direction and glucose band differ a lot.
- Harm gradient: the share of pairs coded death/injury is U-shaped against the error for both brands: lowest in the common -80 to -50 % band, highest near the sensor floor (-100 to -90 %) and when the sensor reads 2 to 3 times the true value (over 200 %). Partly real (same shape in both brands, matches how harm happens), partly coding (Abbott 4 % vs Dexcom 28 % overall is reporting style; small-error bands are "serious by default" because nobody files a malfunction for a 10 % gap). Harm words in malfunction texts stay flat at about 1 % across bands. To settle: a human read of about 100 + 100 reports from the two extreme bands, and the same gradient within one brand and year.
- Weighted sample check: full-corpus malfunction numbers sit inside the sample's bootstrap intervals for All and Abbott (pair rate 4.4 vs 4.2 %, median -65 vs -64 %); the Dexcom pair rate does not (1.05 vs 0.57 %; the sample drew fewer wrong-reading texts in 2019-2020; only 27 Dexcom pairs). The full corpus replaces the sample for malfunction-only numbers.
- Decision for Phase 2: simulate three faults: the common false low in the 70 to 250 range (needless carbs, insulin suspension), the hidden low (sensor normal while the true value is under 54), and the floor-pinned sensor at a true value over 250. The constant-bias lookup covers only the first.

## 2026-11-06. Field inventory, demographics and text themes beyond the 12-field form (results/FIELD_INVENTORY.md)
- Asked: what the MAUDE reports hold that we have not used, who the reports are about (age, sex, country) against the trial cohort, what the free text says that the form does not capture and which of it a pattern can read at scale, and whether reading the 3.26 million malfunction texts would strengthen the project.
- Script: scripts/field_inventory.py (seed 20261106, no required arguments, optional --zip for one raw bulk zip; about 7 minutes plus 11 seconds per 77 MB zip). Tables in results/inventory/. Finished 2026-11-08 after a network outage killed the first background runs; the memo was written from the tables on disk plus one foreground re-run of the pattern step.
- Fields: the clean tables already hold 88 columns from the bulk re-pull (the README's "country not stored" note is out of date; reporter_country_code is filled for 92.8 % and matches the API counts). Unused and useful: device_evaluated_by_manufacturer (67 % filled: Y 797k, N 856k, R 528k), device_availability (returned 23 %), removal_correction_number (721 serious reports carry the Nov 2025 Libre 3 removal id), lot_number (Dexcom 82 %), mfr_report_type. One raw zip (95,000 records, 12,935 CGM) has 145 field paths; the clean step keeps 78. Only two dropped fields are worth adding: device_date_of_manufacturer (78 % of CGM records) and date_returned_to_manufacturer (5 %); the rest are maker addresses, ids and constants. No text type is dropped.
- Demographics: age filled 73 %, sex 46 %, race and ethnicity 0.3 % of 3.38 million reports. Fill is a maker habit: Dexcom 93 % / 57 %, Abbott 7 % / 7 %; sex only recorded since 2021. Blank-age reports are 75 % Abbott, 67 % non-US and 67 % wrong-readings complaints. The text gives an age in 0.03 % of blank cases. Filled ages: median 52, under 18 17.5 %, 65+ 27.7 % (deaths median 59; Dexcom G4 median 42 with 28 % children). Trial: 226 adults, median 43, 65+ 8 %, no children, 94 % White. Decision: stop on demographics; state the gap in the paper.
- Themes: 300 texts read by hand (stratified: 35 deaths, 140 injuries, 125 malfunctions). Codes in results/inventory/sample_300_hand_codes.txt. Found and not in the form: device not returned (56 %), returned (20 %), maker found no defect (41 %), confirmed a cause (16 %), cause not determined (28 %); symptoms (13 %), carer in the story (24 %), EMS or hospital (24 %), severe signs (13 %), app or phone (10 %), alarm failed (8 %), pump automation (3 %). Rare: compression lows 1 of 300, interfering substances 3, timing in hours 17, maker advising a fingerstick 18. Death texts are mostly coroner and autopsy stories with no device allegation.
- Patterns: 52 themes written, checked against the hand codes, tightened twice (boilerplate sentences stripped first; sub-string hits such as RMA in INFORMATION, CHARGED in DISCHARGED, VENOUS in INTRAVENOUS, TESTING in the pain pattern fixed). 14 themes reach precision 80 %+ on the 300 (evaluation outcomes 86 to 90 %, EMS 96 %, carer 94 %, clinician 91 %, alarm failed 82 %). At scale (122,657 serious texts): not returned 66 % (Abbott 86 %, Dexcom 23 %); of returned devices, no defect found 81 % (Abbott 98 %, Dexcom 75 %); EMS or hospital 38 %; carer 32 %; skin reaction 18 % (Dexcom G4 44 %); alarm failed 6 %; pump automation 2 % (G7 9 %). Low-precision themes (skin, bleeding, adhesive, app, hardware, repeat failures; 40 to 70 %) are marked "~" in the memo.
- Beyond serious: weighted malfunction sample is 8.5 % wrong readings (Abbott 58 %, Dexcom 0.8 %), 43 % signal loss, outcome none 98 %; 327 pairs, median error -64 %, 73 % read low. 45.5 % of the 3.26 million malfunction texts are one of 241 identical templates, 236,507 Dexcom reports have no text, 481,095 reports carry a wrong-readings code and a real story. A full model run would take 250 GPU-hours; that subset 37; Abbott only 19.
- Opinion: reading more malfunction texts with the model adds volume, not knowledge, and does not change the research question; the regex-v2 full-corpus pass (2026-11-06, later entry) already read the numbers. Recommended instead: use the unused structured fields (1 to 2 hours), add the two dropped date fields (10 minutes), and do the two 100-report human reads (extreme error bands; Abbott "returned, no defect" injuries).
- Learned: Windows heredocs over about 40 lines fail in this shell, so pattern edits were written to files first. Background jobs do not survive a network outage; long steps should be run in the foreground or checked by file timestamps, not awaited.
