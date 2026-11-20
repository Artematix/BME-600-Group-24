# Validation of text extraction v1 against the gold set

Date: 2026-10-30. Gold: `gold_labels_v1.csv` (287 reports). Regex: `regex_sample.csv`. Model run 1: `llm_sample_p8.jsonl`. Model run 2: `llm_sample_p8fa.jsonl`.

Words: kappa = Cohen's kappa, agreement corrected for chance (1.00 = perfect, 0 = chance). Accuracy = share of reports where the system gives the gold label. "Exact among system values" = of the values the system wrote, the share equal to gold. "Exact among gold values" = of the values in the gold, the share the system got right. Presence precision / recall = how well the system knows WHEN a value exists. Invented = system wrote a value where the gold has none. Missed = gold has a value, system wrote none.

Systems: `regex` = pattern layer alone (only numbers, zone, wear day, multiple_pairs). `llm` = model alone. `combined` = regex value when the Abbott template matched, else the model; zone and wear day from the regex when it found one, else the model; judgement fields from the model.

Joined reports: 287. Model errors (no form): 0.

## 1. Headline numbers

| Field | llm kappa | combined kappa | exact (3 dp) | combined accuracy | target kappa | status |
|---|---|---|---|---|---|---|
| fault_type | 0.61 | 0.61 | 0.612 | 67% | 0.70 | MISSED |
| outcome_severity | 0.56 | 0.56 | 0.557 | 73% | 0.75 | MISSED |
| user_action | 0.40 | 0.40 | 0.395 | 62% | - | - |
| fingerstick_check_done | 0.73 | 0.73 | 0.728 | 86% | - | - |
| multiple_pairs | 0.58 | 0.65 | 0.647 | 94% | - | - |

Status compares the kappa rounded to 2 decimals with the target, as the target is written (kappa on 287 reports has a sampling error of about 0.03). The exact value is shown next to it.

Numbers pooled (sensor value, meter value, wear day, zone). Target: 95 % exact among system values.

| System | gold values | system values | exact | exact among system values | exact among gold values | status |
|---|---|---|---|---|---|---|
| regex | 318 | 322 | 311 | 96.6% | 97.8% | met |
| llm | 318 | 296 | 282 | 95.3% | 88.7% | met |
| combined | 318 | 313 | 302 | 96.5% | 95.0% | met |

## 2. Judgement fields: accuracy and kappa, per maker

### fault_type

| Group | n | llm accuracy | llm kappa |
|---|---|---|---|
| All | 287 | 67% | 0.61 |
| Abbott | 100 | 78% | 0.69 |
| Dexcom | 100 | 60% | 0.52 |
| Medtronic | 87 | 62% | 0.50 |

Run 2 (same version, same settings): accuracy 68%, kappa 0.62 (run 1: 67%, 0.61).

### outcome_severity

| Group | n | llm accuracy | llm kappa |
|---|---|---|---|
| All | 287 | 73% | 0.56 |
| Abbott | 100 | 64% | 0.42 |
| Dexcom | 100 | 82% | 0.70 |
| Medtronic | 87 | 74% | 0.52 |

Run 2 (same version, same settings): accuracy 74%, kappa 0.56 (run 1: 73%, 0.56).

### user_action

| Group | n | llm accuracy | llm kappa |
|---|---|---|---|
| All | 287 | 62% | 0.40 |
| Abbott | 100 | 60% | 0.39 |
| Dexcom | 100 | 68% | 0.52 |
| Medtronic | 87 | 56% | 0.21 |

Run 2 (same version, same settings): accuracy 61%, kappa 0.38 (run 1: 62%, 0.40).

### fingerstick_check_done

| Group | n | llm accuracy | llm kappa |
|---|---|---|---|
| All | 287 | 86% | 0.73 |
| Abbott | 100 | 88% | 0.74 |
| Dexcom | 100 | 80% | 0.60 |
| Medtronic | 87 | 92% | 0.74 |

Run 2 (same version, same settings): accuracy 85%, kappa 0.70 (run 1: 86%, 0.73).

### multiple_pairs

| Group | n | regex accuracy | llm accuracy | combined accuracy | regex kappa | llm kappa | combined kappa |
|---|---|---|---|---|---|---|---|
| All | 287 | 99% | 92% | 94% | 0.94 | 0.58 | 0.65 |
| Abbott | 100 | 99% | 93% | 98% | 0.96 | 0.77 | 0.93 |
| Dexcom | 100 | 100% | 88% | 88% | 1.00 | 0.29 | 0.29 |
| Medtronic | 87 | 99% | 95% | 95% | 0.00 | 0.32 | 0.32 |

Run 2 (same version, same settings): accuracy 92%, kappa 0.60 (run 1: 92%, 0.58).

## 3. Number fields

### sensor_value_mgdl

| System | Group | gold has value | system has value | exact | exact among gold values | exact among system values | presence precision | presence recall | wrong value | invented | missed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regex | All | 83 | 82 | 81 | 98% | 99% | 99% | 98% | 0 | 1 | 2 |
| regex | Abbott | 59 | 59 | 59 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| regex | Dexcom | 19 | 19 | 19 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| regex | Medtronic | 5 | 4 | 3 | 60% | 75% | 75% | 60% | 0 | 1 | 2 |
| llm | All | 83 | 69 | 65 | 78% | 94% | 100% | 83% | 4 | 0 | 14 |
| llm | Abbott | 59 | 50 | 47 | 80% | 94% | 100% | 85% | 3 | 0 | 9 |
| llm | Dexcom | 19 | 17 | 16 | 84% | 94% | 100% | 89% | 1 | 0 | 2 |
| llm | Medtronic | 5 | 2 | 2 | 40% | 100% | 100% | 40% | 0 | 0 | 3 |
| combined | All | 83 | 77 | 75 | 90% | 97% | 100% | 93% | 2 | 0 | 6 |
| combined | Abbott | 59 | 58 | 57 | 97% | 98% | 100% | 98% | 1 | 0 | 1 |
| combined | Dexcom | 19 | 17 | 16 | 84% | 94% | 100% | 89% | 1 | 0 | 2 |
| combined | Medtronic | 5 | 2 | 2 | 40% | 100% | 100% | 40% | 0 | 0 | 3 |

### meter_value_mgdl

| System | Group | gold has value | system has value | exact | exact among gold values | exact among system values | presence precision | presence recall | wrong value | invented | missed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regex | All | 100 | 104 | 96 | 96% | 92% | 94% | 98% | 2 | 6 | 2 |
| regex | Abbott | 60 | 60 | 59 | 98% | 98% | 98% | 98% | 0 | 1 | 1 |
| regex | Dexcom | 28 | 30 | 27 | 96% | 90% | 93% | 100% | 1 | 2 | 0 |
| regex | Medtronic | 12 | 14 | 10 | 83% | 71% | 79% | 92% | 1 | 3 | 1 |
| llm | All | 100 | 87 | 83 | 83% | 95% | 99% | 86% | 3 | 1 | 14 |
| llm | Abbott | 60 | 50 | 49 | 82% | 98% | 100% | 83% | 1 | 0 | 10 |
| llm | Dexcom | 28 | 26 | 23 | 82% | 88% | 96% | 89% | 2 | 1 | 3 |
| llm | Medtronic | 12 | 11 | 11 | 92% | 100% | 100% | 92% | 0 | 0 | 1 |
| combined | All | 100 | 96 | 93 | 93% | 97% | 99% | 95% | 2 | 1 | 5 |
| combined | Abbott | 60 | 59 | 59 | 98% | 100% | 100% | 98% | 0 | 0 | 1 |
| combined | Dexcom | 28 | 26 | 23 | 82% | 88% | 96% | 89% | 2 | 1 | 3 |
| combined | Medtronic | 12 | 11 | 11 | 92% | 100% | 100% | 92% | 0 | 0 | 1 |

### wear_day

| System | Group | gold has value | system has value | exact | exact among gold values | exact among system values | presence precision | presence recall | wrong value | invented | missed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regex | All | 51 | 52 | 51 | 100% | 98% | 98% | 100% | 0 | 1 | 0 |
| regex | Abbott | 51 | 52 | 51 | 100% | 98% | 98% | 100% | 0 | 1 | 0 |
| regex | Dexcom | 0 | 0 | 0 | - | - | - | - | 0 | 0 | 0 |
| regex | Medtronic | 0 | 0 | 0 | - | - | - | - | 0 | 0 | 0 |
| llm | All | 51 | 56 | 51 | 100% | 91% | 91% | 100% | 0 | 5 | 0 |
| llm | Abbott | 51 | 52 | 51 | 100% | 98% | 98% | 100% | 0 | 1 | 0 |
| llm | Dexcom | 0 | 2 | 0 | - | 0% | 0% | - | 0 | 2 | 0 |
| llm | Medtronic | 0 | 2 | 0 | - | 0% | 0% | - | 0 | 2 | 0 |
| combined | All | 51 | 56 | 51 | 100% | 91% | 91% | 100% | 0 | 5 | 0 |
| combined | Abbott | 51 | 52 | 51 | 100% | 98% | 98% | 100% | 0 | 1 | 0 |
| combined | Dexcom | 0 | 2 | 0 | - | 0% | 0% | - | 0 | 2 | 0 |
| combined | Medtronic | 0 | 2 | 0 | - | 0% | 0% | - | 0 | 2 | 0 |

### parkes_zone_stated

| System | Group | gold has value | system has value | exact | exact among gold values | exact among system values | presence precision | presence recall | wrong value | invented | missed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regex | All | 84 | 84 | 83 | 99% | 99% | 100% | 100% | 1 | 0 | 0 |
| regex | Abbott | 57 | 57 | 57 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| regex | Dexcom | 27 | 27 | 26 | 96% | 96% | 100% | 100% | 1 | 0 | 0 |
| regex | Medtronic | 0 | 0 | 0 | - | - | - | - | 0 | 0 | 0 |
| llm | All | 84 | 84 | 83 | 99% | 99% | 100% | 100% | 1 | 0 | 0 |
| llm | Abbott | 57 | 57 | 57 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| llm | Dexcom | 27 | 27 | 26 | 96% | 96% | 100% | 100% | 1 | 0 | 0 |
| llm | Medtronic | 0 | 0 | 0 | - | - | - | - | 0 | 0 | 0 |
| combined | All | 84 | 84 | 83 | 99% | 99% | 100% | 100% | 1 | 0 | 0 |
| combined | Abbott | 57 | 57 | 57 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| combined | Dexcom | 27 | 27 | 26 | 96% | 96% | 100% | 100% | 1 | 0 | 0 |
| combined | Medtronic | 0 | 0 | 0 | - | - | - | - | 0 | 0 | 0 |

Combine rule check (exact among system values; multiple_pairs = accuracy): `template` (used) vs `anypair`.

| Field | template | anypair |
|---|---|---|
| sensor_value_mgdl | 97% (75/77) | 100% (80/80) |
| meter_value_mgdl | 97% (93/96) | 97% (95/98) |
| wear_day | 91% (51/56) | 91% (51/56) |
| parkes_zone_stated | 99% (83/84) | 99% (83/84) |
| multiple_pairs | 94% | 96% |

## 4. Confusion tables (model answers)

Rows = gold label. Columns = model label. Short names: low = reads_low, high = reads_high, errat = erratic, signal = signal_loss, error = sensor_error_or_early_end, adhes = adhesive_or_detachment, skin = insertion_or_skin_injury, other = other_device, uncl = unclear; sympt = symptoms_only, hypo = hypoglycemia, hyper = hyperglycemia_or_dka, hosp = hospital_or_er, n/s = not_stated.

### fault_type, all makers

| fault_type (gold down, system across) | low | high | errat | signal | error | adhes | skin | other | uncl |
|---|---|---|---|---|---|---|---|---|---|
| low | 51 | 10 | 9 | 0 | 2 | 0 | 0 | 0 | 3 |
| high | 2 | 20 | 4 | 0 | 1 | 0 | 0 | 0 | 0 |
| errat | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| signal | 0 | 0 | 0 | 52 | 1 | 0 | 0 | 11 | 1 |
| error | 0 | 0 | 1 | 4 | 12 | 0 | 0 | 1 | 1 |
| adhes | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 |
| skin | 0 | 0 | 0 | 0 | 0 | 10 | 12 | 0 | 0 |
| other | 2 | 1 | 0 | 4 | 0 | 2 | 1 | 18 | 15 |
| uncl | 0 | 0 | 7 | 1 | 1 | 0 | 0 | 0 | 21 |

### fault_type, Abbott

| Abbott (gold down, system across) | low | high | errat | signal | error | adhes | skin | other | uncl |
|---|---|---|---|---|---|---|---|---|---|
| low | 42 | 3 | 5 | 0 | 1 | 0 | 0 | 0 | 1 |
| high | 0 | 18 | 3 | 0 | 1 | 0 | 0 | 0 | 0 |
| errat | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| signal | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| error | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 |
| adhes | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| skin | 0 | 0 | 0 | 0 | 0 | 6 | 5 | 0 | 0 |
| other | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 |
| uncl | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 |

### fault_type, Dexcom

| Dexcom (gold down, system across) | low | high | errat | signal | error | adhes | skin | other | uncl |
|---|---|---|---|---|---|---|---|---|---|
| low | 9 | 6 | 3 | 0 | 0 | 0 | 0 | 0 | 1 |
| high | 2 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| errat | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| signal | 0 | 0 | 0 | 27 | 0 | 0 | 0 | 0 | 0 |
| error | 0 | 0 | 0 | 4 | 2 | 0 | 0 | 0 | 1 |
| adhes | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| skin | 0 | 0 | 0 | 0 | 0 | 3 | 5 | 0 | 0 |
| other | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 11 |
| uncl | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 14 |

### fault_type, Medtronic

| Medtronic (gold down, system across) | low | high | errat | signal | error | adhes | skin | other | uncl |
|---|---|---|---|---|---|---|---|---|---|
| low | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 1 |
| high | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| errat | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| signal | 0 | 0 | 0 | 23 | 1 | 0 | 0 | 11 | 1 |
| error | 0 | 0 | 1 | 0 | 4 | 0 | 0 | 1 | 0 |
| adhes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| skin | 0 | 0 | 0 | 0 | 0 | 1 | 2 | 0 | 0 |
| other | 2 | 0 | 0 | 3 | 0 | 1 | 1 | 16 | 4 |
| uncl | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 6 |

### outcome_severity, all makers

| outcome (gold down, system across) | none | sympt | hypo | hyper | hosp | death | n/s |
|---|---|---|---|---|---|---|---|
| none | 143 | 2 | 8 | 0 | 0 | 0 | 0 |
| sympt | 21 | 7 | 2 | 0 | 0 | 0 | 1 |
| hypo | 1 | 0 | 9 | 0 | 0 | 0 | 0 |
| hyper | 4 | 1 | 2 | 2 | 0 | 0 | 0 |
| hosp | 1 | 2 | 4 | 6 | 46 | 0 | 1 |
| death | 0 | 0 | 0 | 0 | 0 | 3 | 0 |
| n/s | 19 | 1 | 1 | 0 | 0 | 0 | 0 |

### outcome_severity, Abbott

| Abbott (gold down, system across) | none | sympt | hypo | hyper | hosp | death |
|---|---|---|---|---|---|---|
| none | 44 | 2 | 8 | 0 | 0 | 0 |
| sympt | 14 | 5 | 2 | 0 | 0 | 0 |
| hypo | 0 | 0 | 5 | 0 | 0 | 0 |
| hyper | 1 | 0 | 0 | 1 | 0 | 0 |
| hosp | 0 | 0 | 0 | 1 | 8 | 0 |
| death | 0 | 0 | 0 | 0 | 0 | 1 |
| n/s | 6 | 1 | 1 | 0 | 0 | 0 |

### outcome_severity, Dexcom

| Dexcom (gold down, system across) | none | sympt | hypo | hyper | hosp | n/s |
|---|---|---|---|---|---|---|
| none | 51 | 0 | 0 | 0 | 0 | 0 |
| sympt | 5 | 2 | 0 | 0 | 0 | 1 |
| hypo | 0 | 0 | 2 | 0 | 0 | 0 |
| hyper | 0 | 1 | 0 | 0 | 0 | 0 |
| hosp | 0 | 2 | 2 | 5 | 27 | 0 |
| n/s | 2 | 0 | 0 | 0 | 0 | 0 |

### outcome_severity, Medtronic

| Medtronic (gold down, system across) | none | hypo | hyper | hosp | death | n/s |
|---|---|---|---|---|---|---|
| none | 48 | 0 | 0 | 0 | 0 | 0 |
| sympt | 2 | 0 | 0 | 0 | 0 | 0 |
| hypo | 1 | 2 | 0 | 0 | 0 | 0 |
| hyper | 3 | 2 | 1 | 0 | 0 | 0 |
| hosp | 1 | 2 | 0 | 11 | 0 | 1 |
| death | 0 | 0 | 0 | 0 | 2 | 0 |
| n/s | 11 | 0 | 0 | 0 | 0 | 0 |

### user_action, all makers

| action (gold down, system across) | none | ate_carbs | took_insulin | skipped_insulin | sought_care | n/s |
|---|---|---|---|---|---|---|
| none | 0 | 0 | 0 | 0 | 0 | 0 |
| ate_carbs | 1 | 15 | 2 | 0 | 0 | 0 |
| took_insulin | 0 | 4 | 5 | 0 | 0 | 0 |
| skipped_insulin | 1 | 0 | 0 | 0 | 0 | 1 |
| sought_care | 31 | 13 | 3 | 4 | 9 | 9 |
| other | 5 | 3 | 0 | 0 | 0 | 1 |
| n/s | 24 | 7 | 0 | 0 | 1 | 148 |

## 5. Run-to-run reproducibility (same version, two runs, same settings)

| Field | identical answers |
|---|---|
| fault_type | 94.8% |
| outcome_severity | 95.5% |
| user_action | 91.3% |
| fingerstick_check_done | 98.6% |
| multiple_pairs | 98.3% |
| sensor_value_mgdl | 98.3% |
| meter_value_mgdl | 98.3% |
| wear_day | 99.3% |
| parkes_zone_stated | 100.0% |
| all fields identical | 80.5% |

Kappa against gold in each run:

| Field | llm run 1 | llm run 2 | combined run 1 | combined run 2 |
|---|---|---|---|---|
| fault_type | 0.61 | 0.62 | 0.61 | 0.62 |
| outcome_severity | 0.56 | 0.56 | 0.56 | 0.56 |
| user_action | 0.40 | 0.38 | 0.40 | 0.38 |
| fingerstick_check_done | 0.73 | 0.70 | 0.73 | 0.70 |
| multiple_pairs | 0.58 | 0.60 | 0.65 | 0.66 |
