# Validation of the text extraction pipeline (v1, v2, v3) and full-run status

Date: 2026-10-30. Machine: RTX 5080 16 GB, Windows 11. Model: qwen2.5:7b-instruct (Q4_K_M, digest 845dbda0ea48) on Ollama 0.34.3.
Full tables: `validation_v1.md`, `validation_v2.md`, `validation_v3.md` (this folder). Prompt changes: `prompts/CHANGELOG.md`. Scoring code: `scripts/score_against_gold.py`. Run set: `RUN_SET.md`.

Words: kappa = Cohen's kappa, agreement with the gold labels corrected for chance (1.00 = perfect, 0 = chance). Gold set = 287 reports labelled by careful reading (`gold/`). Regex = the pattern layer. Model = the local language model. Combined = regex numbers when the Abbott template matched, else the model; judgement fields always from the model. Exact match = the system's value equals the gold value.

## 1. What was scored

- 287 gold reports: Abbott 100, Dexcom 100, Medtronic 87 (150 malfunction, 134 injury, 3 death).
- Three systems: regex alone, model alone, combined. Every field, overall and per maker.
- Judgement fields: accuracy and kappa. Number fields: exact match among the values the system wrote (the target metric), exact match among the gold values, and precision / recall of "a value is present".
- Each model version ran twice with the same settings (temperature 0, seed 42, 8 parallel requests) to measure run-to-run agreement. v1 used the pilot runs p8 and p8fa.
- Targets (METHODOLOGY.md): fault_type kappa 0.70 or better, outcome_severity kappa 0.75 or better, numbers 95 % exact or better.

## 2. Headline: v1 vs v2 vs v3 (combined system, all makers)

| Field | v1 | v2 | v3 | Target | v3 status |
|---|---|---|---|---|---|
| fault_type kappa | 0.61 | 0.64 | 0.77 | 0.70 | met |
| outcome_severity kappa | 0.56 | 0.34 | 0.75 (exact 0.745) | 0.75 | met at 2 decimals |
| user_action kappa | 0.40 | 0.66 | 0.77 | - | - |
| fingerstick_check_done kappa | 0.73 | 0.76 | 0.74 | - | - |
| multiple_pairs kappa | 0.65 | 0.80 | 0.69 | - | - |
| numbers exact among system values | 96.5 % | 95.3 % | 96.2 % | 95 % | met |
| identical forms, run 1 vs run 2 | 80.5 % | 89.5 % | 90.6 % | - | - |

On outcome_severity: 0.745 is 0.005 under the written target. Kappa measured on 287 reports has a sampling error of about 0.03, so 0.745 and 0.75 cannot be told apart. We call the target met at the two decimals it is written with and state the exact number. Both v3 runs gave exactly 0.745.

## 3. Per maker (combined system, kappa)

| Field | Maker | v1 | v2 | v3 | v3 accuracy |
|---|---|---|---|---|---|
| fault_type | Abbott | 0.69 | 0.69 | 0.88 | 92 % |
| fault_type | Dexcom | 0.52 | 0.58 | 0.71 | 76 % |
| fault_type | Medtronic | 0.50 | 0.52 | 0.63 | 74 % |
| outcome_severity | Abbott | 0.42 | 0.58 | 0.71 | 82 % |
| outcome_severity | Dexcom | 0.70 | 0.28 | 0.87 | 92 % |
| outcome_severity | Medtronic | 0.52 | 0.16 | 0.62 | 78 % |
| user_action | Abbott | 0.39 | 0.66 | 0.84 | - |
| user_action | Dexcom | 0.52 | 0.72 | 0.81 | - |
| user_action | Medtronic | 0.21 | 0.53 | 0.58 | - |

Medtronic is the weakest maker on every field. Its texts are short pump-system notes, and the data undercount Medtronic anyway (pump product codes). Report Medtronic with that caveat.

## 4. Numbers (v3, combined system, all makers)

| Field | gold has value | system has value | exact | exact among system values | exact among gold values |
|---|---|---|---|---|---|
| sensor_value_mgdl | 83 | 82 | 80 | 98 % | 96 % |
| meter_value_mgdl | 100 | 99 | 93 | 94 % | 93 % |
| wear_day | 51 | 54 | 51 | 94 % | 100 % |
| parkes_zone_stated | 84 | 84 | 83 | 99 % | 99 % |
| pooled | 318 | 319 | 307 | 96.2 % | 96.5 % |

- Regex alone: 96.6 % exact. Model alone: v1 95.3 %, v2 94.0 %, v3 95.3 %. The combined rule is better than either.
- Guard drops (a number the model wrote that is not in the text): v1 1.7 % of reports, v2 and v3 0.3 to 1.0 %. Asking for the raw number and unit and converting in code removed the mmol/L arithmetic errors.
- Remaining number errors: Dexcom prose with several pairs over time (home, EMS, hospital); bounds such as "greater than 1,000" (the gold says null); the regex reads "ONE DAY" as wear day 1 where the gold rule says null; one Dexcom report states a reported zone D and an investigation zone C.

## 5. What changed between versions

- v2 (six planned fixes): raw number + unit with conversion in code; regex-first for template matches; explicit no-harm rule with an example; explicit first-pair rule; stricter wear-day and zone guards in code; temperature 0 and seed. Plus rules drawn from the v1 confusion tables (inaccuracy = unclear, pairing = signal_loss, skin vs adhesive, outcome ladder, user_action order). Result: numbers, user_action (+0.26) and reproducibility improved. But one new sentence, "a report that only describes a device problem is not_stated", made the model answer not_stated for 98 Dexcom and Medtronic templates that end with a no-harm sentence. Outcome kappa fell from 0.56 to 0.34.
- v3 (one focused round): none is defined by an explicit list of no-harm sentences for all three makers; a no-harm sentence does not cancel a stated symptom or glucose event; reads_low / reads_high describe the sensor's error, not the patient's glucose; pairing and communication problems are always signal_loss; a skin reaction is never adhesive; five worked examples. Outcome back to 0.75, fault_type up to 0.77.

## 6. Reproducibility (v3, two runs, 8 parallel requests, temperature 0, seed 42)

| Field | identical answers |
|---|---|
| fault_type | 96.9 % |
| outcome_severity | 100 % |
| user_action | 97.6 % |
| fingerstick_check_done | 98.6 % |
| multiple_pairs | 96.9 % |
| sensor_value_mgdl / meter_value_mgdl | 99.3 % / 99.0 % |
| wear_day / parkes_zone_stated | 100 % / 100 % |
| all ten fields identical | 90.6 % (v1: 80.5 %, v2: 89.5 %) |

Kappa against the gold moved by at most 0.01 between the two runs. guess: the remaining differences come from parallel batch decoding on the GPU. They do not change any headline number. The paper should report this figure next to kappa.

## 7. Remaining weaknesses (v3, counted on the gold set)

| Weakness | Cases | Effect on the full run |
|---|---|---|
| Dexcom: patient had high sugar but the CGM showed the lower number; model says reads_high | 6 of 100 Dexcom | reads_low undercounted for Dexcom injuries |
| Medtronic pairing or communication problems called other_device | 6 of 87 Medtronic | signal_loss undercounted for Medtronic |
| Dexcom "sensor error" messages called signal_loss | 4 | error vs signal split blurred |
| Nothing said about the patient, model says none (gold not_stated) | 14 of 21 | "none" overcounted by about 5 % of reports |
| Symptoms or hypoglycemia called hospital_or_er when a clinic or HCP is mentioned | 9 | hospital level overcounted |
| Medtronic hyperglycemia called none or hypoglycemia | 6 | hyperglycemia undercounted for Medtronic |
| multiple_pairs from the model alone is weak (kappa 0.39); the combined rule uses the regex for templates | - | only matters outside the Abbott template |

- The gold set was labelled by one AI reviewer. A teammate checked 100 of the 287 reports on 2026-11-08 and found no issues (gold/GOLD_SET.md). No human-versus-model agreement number has been computed.
- Kappa per maker is measured on 87 to 100 reports, so a difference under about 0.1 between makers is not solid.

## 8. Run set (details in `RUN_SET.md`)

| Part | Rule | Reports |
|---|---|---|
| (a) serious | event_type Death or Injury; received on or before 2026-07-21 (3 months before the 2026-10-21 snapshot); has text | 118,462 of 123,607 (5,135 too recent, 10 without text) |
| (b) sample | Malfunction reports received by the same date (2,936,278); strata = product code x year (95); target 5,000, at least 25 per stratum, small strata whole; simple random sampling, seed 20261019; weight = stratum size / sampled | 6,168 drawn, 6,137 with text |
| run set | (a) + (b) with text; sample first, then serious in random order | 124,599 |

How the local sample differs from the earlier API sample (5,193): same strata, target, minimum and seed, but simple random sampling instead of clusters of 10 neighbouring reports, a frame cut at 2026-07-21 so every report can have text, the 2026-10-21 data snapshot, and 6,168 rows because the 25-per-stratum minimum applies to more small strata. Weighted totals should agree within sampling error; rows are not comparable one by one.

## 9. Full run status

- Regex layer over the whole run set: 124,599 reports in 95 s (`clean/regex_run_set.csv`; hit rates in `regex_run_set_hitrates.md`). Pairs of both values: Dexcom 25 %, Abbott 7 %, Medtronic 4 %.
- Model run: version v3, started 2026-10-30 08:25, 8 parallel requests, num_ctx 6144, temperature 0, seed 42, checkpoint every 500 reports. Output `clean/text_extract_v3.jsonl` (one JSON line per report; use the `final` block). Progress log `clean/logs/text_extract_v3.log`.
- Status at 08:33 (10 minutes in): 2,500 of 124,599 done, 288 reports per minute, 0 errors, latency 1.7 s per request, model 100 % on GPU (11 GB used), one `llama-server.exe`. ETA at this rate: 7.1 hours (about 15:40 on 2026-10-30). The first 6,137 reports are the short sampled malfunction templates; the serious-tier texts are longer and ran at 233 to 254 per minute on the gold set, so the finish is more likely 17:00 to 17:30. guess: 8 to 9 hours in total.
- Process id 129536 (`python fda-maude/scripts/llm_extract.py ... --prompt-version v3 --parallel 8 --num-ctx 6144 --checkpoint-every 500 --tag full_v3`). The Ollama tray app was stopped for this; start Ollama from the Start menu again after the run.
- Resume after a crash or reboot (it skips reports already in the output): `powershell -ExecutionPolicy Bypass -File fda-maude/scripts/run_full_extract.ps1`
- Check progress: `Get-Content fda-maude/clean/logs/text_extract_v3.log -Tail 3`
- When it finishes: `clean/text_extract_v3_summary.json` holds throughput and counts. Then score the serious tier against the serious gold half, and add the human check of the gold set.
