# Text extraction pilot: patterns + local model

Date: 2026-10-27. Machine: RTX 5080 16 GB, Windows 11, Ollama 0.34.3.
Main pilot set: `data/sample_narratives.jsonl` (287 reports: Abbott 100, Dexcom 100, Medtronic 87).
Extra: the regex on all 123,607 serious reports, and the model on 500 random serious reports.
No gold labels exist yet. "Quality" below means agreement between the two layers and a quick read of 20 reports.

## 1. What was built

| File | What it does |
|---|---|
| `scripts/extract_regex.py` | Pattern layer. Reads the Abbott template, Dexcom/Medtronic prose pairs, LOW/HIGH display words, Parkes zone, wear day, units (mmol/L x 18, flagged). Writes the matched text for audit. Prints hit rates. 123,607 reports in about 70 s. |
| `scripts/llm_extract.py` | Model layer. Ollama + JSON schema (`format=`), so every answer is a valid form. Guard: a number not written in the text is set to null (`guard_dropped`). Compares with the regex (`disagree_fields`, `role_swap`). Resumable JSONL, parallel requests, per-report latency and tokens, model digest in the output. |
| `prompts/v1_system.txt`, `v1_user_template.txt`, `v1_schema.json` | The exact prompt and form, version v1. Fixed prefix (rules, field definitions, 2 short made-up examples) + the report at the end, so the server caches the prefix. |
| `results/text/regex_sample.csv`, `regex_sample_hitrates.md` | Regex output on the 287 sample. |
| `results/text/regex_serious_hitrates.md` | Regex hit rates on the full serious tier (the 123k-row CSV itself is not in git). |
| `results/text/llm_sample_*.jsonl` + `*_summary.json` | Model runs on the 287 sample: `seq`, `p4`, `p8`, `p8fa`, `p16`, `3b_p8`. `llm_serious500_p8.jsonl` = 500 serious reports. |

## 2. Regex hit rates

287-report sample ("pair" = sensor value and meter value both found; "+word" = also counts a LOW/HIGH display word as the sensor value):

| Maker / event type | n | pair | pair +word | Abbott template | any sensor value | any meter value | Parkes zone | wear day |
|---|---|---|---|---|---|---|---|---|
| Abbott / Malfunction | 50 | 96% | 96% | 96% | 98% | 96% | 98% | 94% |
| Abbott / Injury | 49 | 20% | 20% | 18% | 20% | 24% | 16% | 10% |
| Dexcom / Malfunction | 50 | 0% | 0% | 0% | 0% | 0% | 24% | 0% |
| Dexcom / Injury | 50 | 32% | 40% | 0% | 38% | 60% | 30% | 0% |
| Medtronic / Malfunction | 50 | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| Medtronic / Injury | 35 | 9% | 9% | 0% | 11% | 40% | 0% | 0% |
| All 287 | 287 | 27% | 28% | 20% | 29% | 36% | 29% | 18% |

Full serious tier (deaths + injuries, all years):

| Maker | n | pair | pair +word | Abbott template | any meter value | Parkes zone | wear day |
|---|---|---|---|---|---|---|---|
| Abbott | 77,868 | 7% | 7% | 5% | 12% | 6% | 7% |
| Dexcom | 33,783 | 28% | 31% | 0% | 45% | 26% | 1% |
| Medtronic | 8,721 | 5% | 5% | 0% | 73% | 0% | 0% |
| Other makers | 3,235 | 16% | 16% | 0% | 23% | 0% | 1% |

Notes:
- Dexcom states a zone too: "THE REPORTED GLUCOSE VALUES FALL WITHIN THE D ZONE OF THE PARKES ERROR GRID" (24% to 30% of Dexcom reports). The options study only expected this for Abbott.
- Medtronic serious reports are mostly insulin-pump reports with one lone blood glucose ("BG OVER 600 MG/DL"). Lone values are kept in `meter_value_mgdl` but `pair_found` stays "no".
- Abbott serious reports over all years carry the template less often (5%) than the 2024-2026 sample (18%).
- 950 of 123,607 serious reports have no text at all.

## 3. Model quality, quick look (qwen2.5:7b-instruct, prompt v1, sequential run)

Numbers against the regex (287 reports):

| Check | Result |
|---|---|
| Regex found a numeric pair | 77 reports |
| Model gives the same two numbers | 59 of 77 (77%). Abbott 44/58, Dexcom 13/16, Medtronic 2/3 |
| Sensor value: agree / regex only / disagree | 65 / 13 / 4 |
| Meter value: agree / regex only / disagree | 81 / 19 / 4 |
| Parkes zone: agree / model only | 84 / 1 (the 1 is an invented zone "B") |
| Wear day: agree / model only | 52 / 3 (model inferred days from dates) |
| Sensor/meter role swaps | 0 |
| Guard dropped a number | 6 reports (2.1%). All 6 were wrong mmol/L conversions |
| Schema violations | 0 (constrained output works) |

What the disagreements are (read by hand):
- mmol/L: the model multiplies by 18 and loses the decimal point ("2.90 MMOL/L" became 522, "11.10" became 1998, "27.00" became 490). The guard caught every case. One report with 8 mmol/L values got null for both numbers.
- Lists: with "56 MG/DL,53 MG/DL" the model took the second value; with "387, 388, AND 400+" it took 400. The regex takes the first.
- "First pair": where the first comparison has no meter value ("100 MG/DL COMPARED TO UNSPECIFIED READINGS"), the model reports sensor 100 / meter null; the regex reports the later complete pair (350 / 129).
- One Dexcom report: the model mixed two pairs (gave 360 / 91 for "CGM 86, BG 360 ... CGM 91, BG 371").

Judgement fields (no gold yet, so counts only):
- Abbott malfunction templates all carry the code "No Clinical Signs" and say "NO REPORT OF DEATH, SERIOUS INJURY, OR MISTREATMENT". The model still answered outcome = hypoglycemia for 14 of 50 and user_action = ate_carbs for 11 of 50. It infers harm from a low sensor number. This is the biggest quality problem.
- Direction: for "CGM 87 vs FSBG 30" the model said "erratic" instead of reads_high (1 of 20 read).
- Outcome ladder applied unevenly: EMS treated at home was once "hypoglycemia", once "hospital_or_er".
- Run-to-run: same model, temperature 0, but parallel decoding changes answers. Identical forms seq vs p8: 221 of 287 (77%). Numbers and zone identical in 99%+, fault_type 95%, outcome 95%, user_action 91%, confidence 91%.

20 examples (10 Abbott, 10 Dexcom; S = sensor, M = meter; sequential run):

| # | report | maker / type | text snippet (regex match or start of text) | regex S / M / zone / day | model S / M / zone / day | model fault, outcome, action | numbers agree? |
|---|---|---|---|---|---|---|---|
| 1 | 25662869 | Abbott Malfunction | SENSOR SCAN RESULTS OF 17.00 MMOL/L,14.00 MMOL/L,21.00 MMOL/L,21.00 MMOL/L COMPARED TO READINGS OF 9.20 ... | 306 / 166 / C / 1 | - / - / C / 1 | erratic, none, not_stated | no (model gave up on the mmol/L list) |
| 2 | 25663162 | Abbott Malfunction | SENSOR SCAN RESULTS OF 70.00 MG/DL COMPARED TO READINGS OF 250.00 MG/DL ... | 70 / 250 / C / 11 | 70 / 250 / C / 11 | reads_low, hypoglycemia, ate_carbs | yes (outcome invented) |
| 3 | 25663289 | Abbott Malfunction | SENSOR SCAN RESULTS OF 156 MG/DL COMPARED TO READINGS OF 48 MG/DL ... | 156 / 48 / D / 3 | 156 / 48 / D / 3 | reads_high, none, not_stated | yes |
| 4 | 25662805 | Abbott Malfunction | SENSOR SCAN RESULTS OF 50.00 MG/DL COMPARED TO READINGS OF 170.00 MG/DL ... | 50 / 170 / C / 5 | 50 / 170 / C / 5 | reads_low, hypoglycemia, ate_carbs | yes (outcome invented) |
| 5 | 25662917 | Abbott Malfunction | SENSOR SCAN RESULTS OF 80.00 MG/DL COMPARED TO READINGS OF 190.00 MG/DL ... | 80 / 190 / C / 1 | 80 / 190 / C / 1 | reads_low, hypoglycemia, ate_carbs | yes (outcome invented) |
| 6 | 25662508 | Abbott Injury | ... 100 MG/DL COMPARED TO UNSPECIFIED READINGS ... A SENSOR RESULT OF 350 MG/DL WAS COMPARED TO A ... METER READING OF 129 | 350 / 129 / C / 12 | 100 / - / C / 12 | reads_high, symptoms_only, ate_carbs | no (different "first pair") |
| 7 | 25652442 | Abbott Injury | AN UNSPECIFIED ERROR MESSAGE WAS REPORTED ... UNABLE TO OBTAIN GLUCOSE READINGS ... SELF-TREAT WITH GLUCOSE | - / - / - / - | - / - / - / - | sensor_error_or_early_end, symptoms_only, ate_carbs | both empty (model right) |
| 8 | 25661691 | Abbott Injury | A HIGH READING ISSUE ... UNSPECIFIED HIGHER SENSOR SCAN RESULTS COMPARED TO UNSPECIFIED READINGS | - / - / - / - | - / - / - / - | reads_high, none, not_stated | both empty (model right) |
| 9 | 25649048 | Abbott Injury | A LOW GLUCOSE READINGS ISSUE ... LOST CONSCIOUSNESS ... SELF-TREAT WITH A SUGARY DRINK | - / - / - / - | - / - / - / - | reads_low, hypoglycemia, ate_carbs | both empty (model right) |
| 10 | 25652337 | Abbott Injury | READINGS ON THE ADC SENSOR: 387 MG/DL, 388 MG/DL, AND 400+ MG/DL. FINGERSTICK READING WAS 133 MG/DL | 387 / 133 / - / - | 400 / 133 / B / - | reads_high, hospital_or_er, ate_carbs | no (list choice; zone B invented) |
| 11 | 25655911 | Dexcom Injury | ... FINGERSTICK BG, WHICH MEASURED 500 MG/DL ... REPEAT FINGERSTICK BG MEASURED 700 MG/DL (no CGM value recalled) | - / 500 / - / - | - / 700 / - / - | erratic, hospital_or_er, sought_care | no (both defensible, no pair exists) |
| 12 | 25673360 | Dexcom Injury | A WEARABLE FAILURE OCCURRED ... "SENSOR FAILURE" ... ADMITTED TO THE HOSPITAL FOR APPROXIMATELY THREE DAYS | - / - / - / - | - / - / - / - | sensor_error_or_early_end, hospital_or_er, not_stated | both empty (model right) |
| 13 | 25669067 | Dexcom Injury | A DETACHED OR MISSING SENSOR WIRE ... IT IMMEDIATELY FELL OFF ... AFTER 3 DAYS ... SKIN INFLAMMATION | - / - / - / - | - / - / - / 3 | adhesive_or_detachment, none, none | yes (day 3 is not a wear day; outcome "none" wrong: doctor drained the site) |
| 14 | 25666430 | Dexcom Injury | BRIEF SENSOR ERROR ... EMS ... HIS BG METER READING UPON ARRIVAL WAS 54 MG/DL ... TREATED WITH ORAL GLUCOSE | - / 54 / - / - | - / 54 / - / - | signal_loss, hypoglycemia, ate_carbs | yes |
| 15 | 25652423 | Dexcom Injury | THE CGM CONTINUED TO DISPLAY LOW ... EMS PERFORMED AN FSBG, WHICH MEASURED 145 MG/DL | LOW / 145 / C / - | - / 145 / C / - | reads_low, none, ate_carbs | yes (model: Gvoke injection = ate_carbs, as v1 defines it) |
| 16 | 25665516 | Dexcom Injury | THE PATIENT'S CGM WAS READING 141 MG/DL WHILE THE BG METER WAS READING 30 MG/DL (seizure, EMS called) | 141 / 30 / D / - | 141 / 30 / D / - | reads_high, hypoglycemia, ate_carbs | yes |
| 17 | 25659854 | Dexcom Injury | EMTS OBTAINED AN FSBG READING OF APPROXIMATELY 30 MG/DL, WHILE THE CGM READING WAS 87 MG/DL | 87 / 30 / C / - | 87 / 30 / C / - | erratic, hypoglycemia, ate_carbs | yes (fault should be reads_high) |
| 18 | 25673995 | Dexcom Injury | THE CGM READING WAS 4.8 MMOL/L, AND THE BLOOD GLUCOSE READING WAS 53.0 MMOL/L | 86 / 954 / D / - | 86 / - / D / - | reads_high, hospital_or_er, none | no (model wrote 953; guard dropped it) |
| 19 | 25662616 | Dexcom Malfunction | SIGNAL LOSS OCCURRED ... TRANSMITTER AND APP WERE UNABLE TO ESTABLISH A CONNECTION | - / - / - / - | - / - / - / - | signal_loss, none, not_stated | both empty (model right) |
| 20 | 25662672 | Dexcom Malfunction | "SIGNAL LOSS" OCCURRED. NO PRODUCT OR DATA WAS PROVIDED | - / - / - / - | - / - / - / - | signal_loss, none, not_stated | both empty (model right) |

Guard-drop rate: 2.1% on the sample (6 of 287), 6.2% on the 500 serious reports (31 of 500: meter 18, sensor 10, wear day 11). All drops were real errors by the model (mmol/L arithmetic, or a wear day inferred from dates).

## 4. Throughput (measured, 287 reports each unless noted)

| Run | Setting | reports / min | output tokens / s (all slots) | mean latency s | guard drops |
|---|---|---|---|---|---|
| seq | 7B, 1 request at a time (tray app server) | 100.7 | 117 | 0.6 | 2.1% |
| p4 | 7B, `OLLAMA_NUM_PARALLEL=4` | 217.1 | 251 | 1.1 | 1.7% |
| p8 | 7B, 8 parallel | 292.8 | 339 | 1.6 | 1.7% |
| p8fa | 7B, 8 parallel + `OLLAMA_FLASH_ATTENTION=1` | 298.1 | 345 | 1.6 | 2.1% |
| p16 | 7B, 16 parallel | 36.4 | 42 | 26.2 | 1.7% |
| 3b_p8 | qwen2.5:3b-instruct, 8 parallel | 350.5 | 486 | 1.3 | 5.9% |
| serious500 | 7B, 8 parallel + flash attention, 500 serious reports (longer texts: median 1,900 prompt tokens vs 1,640) | 248.9 | 296 | 1.9 | 6.2% |

- 7B = qwen2.5:7b-instruct, Q4_K_M, 4.7 GB, digest 845dbda0ea48. Output is about 70 tokens per report. Prompt is 1,400 to 3,200 tokens (the 1,300-token prefix is cached by the server).
- 16 slots collapsed (3 tokens/s per request). guess: the 16 x 4,096 context plus batch buffers no longer fit well in the 16 GB. 8 slots is the ceiling here.
- Alternative tried: the 3B model (option a). 17% faster, but 7 invented zones, 3 times more guard drops, and far more "none"/"took_insulin" answers. Not worth it. Option b (HF transformers + bitsandbytes) was not run: a Windows wheel exists (bitsandbytes 0.50.2), but the 7B at 8 slots already reaches about 300 per minute and the 3B result shows that model size costs accuracy.
- A crashed runner (the 3B at 16 slots) left zombie `llama-server.exe` processes holding VRAM; the next server then put 69% of the model on the CPU (38 reports/min). Always check that `ollama ps` says "100% GPU" before a long run.

## 5. Estimated wall-clock for 129k reports (123,607 serious + 5,193 sample)

| Step | Rate | Time |
|---|---|---|
| Regex, all 129k | about 1,800 reports/s | about 1.5 minutes |
| Model, 7B, 8 slots, serious-tier texts | 249 reports/min | about 8.6 hours |
| Model, if texts were as short as the sample | 298 reports/min | about 7.2 hours |

So one overnight run. guess: 9 to 10 hours including the model-load, checkpoint and one restart.

## 6. Problems found and what v2 should change (not implemented)

1. mmol/L: do not let the model convert. Ask for `sensor_value_raw` and `unit` as written; convert in code. Or, when the Abbott template matched, take the numbers from the regex and ask the model only for the judgement fields.
2. Invented harm on templates: add a rule "a low or high sensor number is not an event; outcome and user_action describe only what the text says happened to the person" and a third example (an Abbott template with no clinical signs -> outcome none, action not_stated).
3. Pair choice: rule "use the first comparison that has BOTH numbers; in a list take the first value". Check sensor < meter -> reads_low, sensor > meter -> reads_high; "erratic" only when no direction is stated.
4. Zone guard in code: the letter must appear in the text as "<letter> ZONE" or "ZONE <letter>". Wear-day guard: the number must sit within 30 characters of "DAY" or "WEAR" (dates and times make small numbers pass the current guard).
5. Outcome ladder: say where "EMS treated at home, no transport" goes (now answered both ways). Consider an `ems_treated` level between hypoglycemia and hospital_or_er.
6. Dexcom and Abbott serious reports hold several pairs over time (home, EMS, hospital). v2 could ask for a list of pairs, or keep "first pair" and let the regex collect the rest (`sensor_values_all`, `meter_values_all`).
7. Reproducibility: parallel decoding changes 23% of forms with temperature 0. Validate on the gold set with the same server setting used for the full run, and report run-to-run agreement next to kappa.
8. Keep the 7B. Consider adding a one-line `evidence_quote` for outcome and user_action (costs about 15% throughput, makes the human check faster).
