# Validation of text extraction v2 against the gold set

Date: 2026-10-30. Gold: `gold_labels_v1.csv` (287 reports). Regex: `regex_sample.csv`. Model run 1: `llm_gold_v2_run1.jsonl`. Model run 2: `llm_gold_v2_run2.jsonl`.

Words: kappa = Cohen's kappa, agreement corrected for chance (1.00 = perfect, 0 = chance). Accuracy = share of reports where the system gives the gold label. "Exact among system values" = of the values the system wrote, the share equal to gold. "Exact among gold values" = of the values in the gold, the share the system got right. Presence precision / recall = how well the system knows WHEN a value exists. Invented = system wrote a value where the gold has none. Missed = gold has a value, system wrote none.

Systems: `regex` = pattern layer alone (only numbers, zone, wear day, multiple_pairs). `llm` = model alone. `combined` = regex value when the Abbott template matched, else the model; zone and wear day from the regex when it found one, else the model; judgement fields from the model.

Joined reports: 287. Model errors (no form): 0.

## 1. Headline numbers

| Field | llm kappa | combined kappa | exact (3 dp) | combined accuracy | target kappa | status |
|---|---|---|---|---|---|---|
| fault_type | 0.64 | 0.64 | 0.642 | 70% | 0.70 | MISSED |
| outcome_severity | 0.34 | 0.34 | 0.340 | 49% | 0.75 | MISSED |
| user_action | 0.66 | 0.66 | 0.663 | 81% | - | - |
| fingerstick_check_done | 0.76 | 0.76 | 0.765 | 88% | - | - |
| multiple_pairs | 0.71 | 0.80 | 0.803 | 97% | - | - |

Status compares the kappa rounded to 2 decimals with the target, as the target is written (kappa on 287 reports has a sampling error of about 0.03). The exact value is shown next to it.

Numbers pooled (sensor value, meter value, wear day, zone). Target: 95 % exact among system values.

| System | gold values | system values | exact | exact among system values | exact among gold values | status |
|---|---|---|---|---|---|---|
| regex | 318 | 322 | 311 | 96.6% | 97.8% | met |
| llm | 318 | 315 | 296 | 94.0% | 93.1% | MISSED |
| combined | 318 | 321 | 306 | 95.3% | 96.2% | met |

## 2. Judgement fields: accuracy and kappa, per maker

### fault_type

| Group | n | llm accuracy | llm kappa |
|---|---|---|---|
| All | 287 | 70% | 0.64 |
| Abbott | 100 | 78% | 0.69 |
| Dexcom | 100 | 65% | 0.58 |
| Medtronic | 87 | 66% | 0.52 |

Run 2 (same version, same settings): accuracy 69%, kappa 0.63 (run 1: 70%, 0.64).

### outcome_severity

| Group | n | llm accuracy | llm kappa |
|---|---|---|---|
| All | 287 | 49% | 0.34 |
| Abbott | 100 | 75% | 0.58 |
| Dexcom | 100 | 41% | 0.28 |
| Medtronic | 87 | 30% | 0.16 |

Run 2 (same version, same settings): accuracy 50%, kappa 0.35 (run 1: 49%, 0.34).

### user_action

| Group | n | llm accuracy | llm kappa |
|---|---|---|---|
| All | 287 | 81% | 0.66 |
| Abbott | 100 | 80% | 0.66 |
| Dexcom | 100 | 83% | 0.72 |
| Medtronic | 87 | 80% | 0.53 |

Run 2 (same version, same settings): accuracy 82%, kappa 0.67 (run 1: 81%, 0.66).

### fingerstick_check_done

| Group | n | llm accuracy | llm kappa |
|---|---|---|---|
| All | 287 | 88% | 0.76 |
| Abbott | 100 | 88% | 0.73 |
| Dexcom | 100 | 83% | 0.67 |
| Medtronic | 87 | 94% | 0.83 |

Run 2 (same version, same settings): accuracy 87%, kappa 0.75 (run 1: 88%, 0.76).

### multiple_pairs

| Group | n | regex accuracy | llm accuracy | combined accuracy | regex kappa | llm kappa | combined kappa |
|---|---|---|---|---|---|---|---|
| All | 287 | 99% | 95% | 97% | 0.94 | 0.71 | 0.80 |
| Abbott | 100 | 99% | 95% | 100% | 0.96 | 0.83 | 1.00 |
| Dexcom | 100 | 100% | 95% | 95% | 1.00 | 0.42 | 0.42 |
| Medtronic | 87 | 99% | 97% | 97% | 0.00 | 0.39 | 0.39 |

Run 2 (same version, same settings): accuracy 95%, kappa 0.71 (run 1: 95%, 0.71).

## 3. Number fields

### sensor_value_mgdl

| System | Group | gold has value | system has value | exact | exact among gold values | exact among system values | presence precision | presence recall | wrong value | invented | missed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regex | All | 83 | 82 | 81 | 98% | 99% | 99% | 98% | 0 | 1 | 2 |
| regex | Abbott | 59 | 59 | 59 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| regex | Dexcom | 19 | 19 | 19 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| regex | Medtronic | 5 | 4 | 3 | 60% | 75% | 75% | 60% | 0 | 1 | 2 |
| llm | All | 83 | 79 | 74 | 89% | 94% | 100% | 95% | 5 | 0 | 4 |
| llm | Abbott | 59 | 57 | 53 | 90% | 93% | 100% | 97% | 4 | 0 | 2 |
| llm | Dexcom | 19 | 19 | 18 | 95% | 95% | 100% | 100% | 1 | 0 | 0 |
| llm | Medtronic | 5 | 3 | 3 | 60% | 100% | 100% | 60% | 0 | 0 | 2 |
| combined | All | 83 | 81 | 79 | 95% | 98% | 100% | 98% | 2 | 0 | 2 |
| combined | Abbott | 59 | 59 | 58 | 98% | 98% | 100% | 100% | 1 | 0 | 0 |
| combined | Dexcom | 19 | 19 | 18 | 95% | 95% | 100% | 100% | 1 | 0 | 0 |
| combined | Medtronic | 5 | 3 | 3 | 60% | 100% | 100% | 60% | 0 | 0 | 2 |

### meter_value_mgdl

| System | Group | gold has value | system has value | exact | exact among gold values | exact among system values | presence precision | presence recall | wrong value | invented | missed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regex | All | 100 | 104 | 96 | 96% | 92% | 94% | 98% | 2 | 6 | 2 |
| regex | Abbott | 60 | 60 | 59 | 98% | 98% | 98% | 98% | 0 | 1 | 1 |
| regex | Dexcom | 28 | 30 | 27 | 96% | 90% | 93% | 100% | 1 | 2 | 0 |
| regex | Medtronic | 12 | 14 | 10 | 83% | 71% | 79% | 92% | 1 | 3 | 1 |
| llm | All | 100 | 98 | 88 | 88% | 90% | 95% | 93% | 5 | 5 | 7 |
| llm | Abbott | 60 | 57 | 55 | 92% | 96% | 100% | 95% | 2 | 0 | 3 |
| llm | Dexcom | 28 | 29 | 25 | 89% | 86% | 93% | 96% | 2 | 2 | 1 |
| llm | Medtronic | 12 | 12 | 8 | 67% | 67% | 75% | 75% | 1 | 3 | 3 |
| combined | All | 100 | 101 | 93 | 93% | 92% | 95% | 96% | 3 | 5 | 4 |
| combined | Abbott | 60 | 60 | 60 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| combined | Dexcom | 28 | 29 | 25 | 89% | 86% | 93% | 96% | 2 | 2 | 1 |
| combined | Medtronic | 12 | 12 | 8 | 67% | 67% | 75% | 75% | 1 | 3 | 3 |

### wear_day

| System | Group | gold has value | system has value | exact | exact among gold values | exact among system values | presence precision | presence recall | wrong value | invented | missed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| regex | All | 51 | 52 | 51 | 100% | 98% | 98% | 100% | 0 | 1 | 0 |
| regex | Abbott | 51 | 52 | 51 | 100% | 98% | 98% | 100% | 0 | 1 | 0 |
| regex | Dexcom | 0 | 0 | 0 | - | - | - | - | 0 | 0 | 0 |
| regex | Medtronic | 0 | 0 | 0 | - | - | - | - | 0 | 0 | 0 |
| llm | All | 51 | 54 | 51 | 100% | 94% | 94% | 100% | 0 | 3 | 0 |
| llm | Abbott | 51 | 51 | 51 | 100% | 100% | 100% | 100% | 0 | 0 | 0 |
| llm | Dexcom | 0 | 1 | 0 | - | 0% | 0% | - | 0 | 1 | 0 |
| llm | Medtronic | 0 | 2 | 0 | - | 0% | 0% | - | 0 | 2 | 0 |
| combined | All | 51 | 55 | 51 | 100% | 93% | 93% | 100% | 0 | 4 | 0 |
| combined | Abbott | 51 | 52 | 51 | 100% | 98% | 98% | 100% | 0 | 1 | 0 |
| combined | Dexcom | 0 | 1 | 0 | - | 0% | 0% | - | 0 | 1 | 0 |
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
| sensor_value_mgdl | 98% (79/81) | 100% (81/81) |
| meter_value_mgdl | 92% (93/101) | 93% (94/101) |
| wear_day | 93% (51/55) | 93% (51/55) |
| parkes_zone_stated | 99% (83/84) | 99% (83/84) |
| multiple_pairs | 97% | 98% |

## 4. Confusion tables (model answers)

Rows = gold label. Columns = model label. Short names: low = reads_low, high = reads_high, errat = erratic, signal = signal_loss, error = sensor_error_or_early_end, adhes = adhesive_or_detachment, skin = insertion_or_skin_injury, other = other_device, uncl = unclear; sympt = symptoms_only, hypo = hypoglycemia, hyper = hyperglycemia_or_dka, hosp = hospital_or_er, n/s = not_stated.

### fault_type, all makers

| fault_type (gold down, system across) | low | high | errat | signal | error | adhes | skin | other | uncl |
|---|---|---|---|---|---|---|---|---|---|
| low | 47 | 10 | 6 | 0 | 2 | 0 | 0 | 6 | 4 |
| high | 3 | 21 | 2 | 0 | 0 | 0 | 0 | 0 | 1 |
| errat | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| signal | 0 | 0 | 0 | 53 | 0 | 0 | 0 | 12 | 0 |
| error | 0 | 0 | 0 | 3 | 13 | 0 | 0 | 3 | 0 |
| adhes | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 |
| skin | 0 | 0 | 0 | 0 | 0 | 19 | 1 | 2 | 0 |
| other | 0 | 0 | 0 | 2 | 1 | 0 | 0 | 39 | 1 |
| uncl | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 6 | 22 |

### fault_type, Abbott

| Abbott (gold down, system across) | low | high | errat | signal | error | adhes | other | uncl |
|---|---|---|---|---|---|---|---|---|
| low | 44 | 2 | 4 | 0 | 1 | 0 | 0 | 1 |
| high | 0 | 20 | 2 | 0 | 0 | 0 | 0 | 0 |
| errat | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| signal | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 |
| error | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 |
| adhes | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| skin | 0 | 0 | 0 | 0 | 0 | 11 | 0 | 0 |
| other | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| uncl | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |

### fault_type, Dexcom

| Dexcom (gold down, system across) | low | high | errat | signal | error | adhes | other | uncl |
|---|---|---|---|---|---|---|---|---|
| low | 3 | 7 | 1 | 0 | 1 | 0 | 4 | 3 |
| high | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| errat | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| signal | 0 | 0 | 0 | 27 | 0 | 0 | 0 | 0 |
| error | 0 | 0 | 0 | 2 | 3 | 0 | 2 | 0 |
| adhes | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| skin | 0 | 0 | 0 | 0 | 0 | 7 | 1 | 0 |
| other | 0 | 0 | 0 | 1 | 0 | 0 | 13 | 0 |
| uncl | 0 | 0 | 1 | 0 | 0 | 0 | 2 | 17 |

### fault_type, Medtronic

| Medtronic (gold down, system across) | low | high | errat | signal | error | adhes | skin | other | uncl |
|---|---|---|---|---|---|---|---|---|---|
| low | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 2 | 0 |
| high | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| errat | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| signal | 0 | 0 | 0 | 24 | 0 | 0 | 0 | 12 | 0 |
| error | 0 | 0 | 0 | 1 | 4 | 0 | 0 | 1 | 0 |
| adhes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| skin | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 0 |
| other | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 24 | 1 |
| uncl | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 3 | 4 |

### outcome_severity, all makers

| outcome (gold down, system across) | none | sympt | hypo | hosp | death | n/s |
|---|---|---|---|---|---|---|
| none | 54 | 0 | 1 | 0 | 0 | 98 |
| sympt | 17 | 7 | 2 | 4 | 0 | 1 |
| hypo | 0 | 0 | 5 | 4 | 0 | 1 |
| hyper | 5 | 0 | 3 | 1 | 0 | 0 |
| hosp | 1 | 0 | 1 | 58 | 0 | 0 |
| death | 0 | 0 | 0 | 0 | 3 | 0 |
| n/s | 5 | 0 | 1 | 0 | 0 | 15 |

### outcome_severity, Abbott

| Abbott (gold down, system across) | none | sympt | hypo | hosp | death | n/s |
|---|---|---|---|---|---|---|
| none | 53 | 0 | 1 | 0 | 0 | 0 |
| sympt | 11 | 6 | 2 | 2 | 0 | 0 |
| hypo | 0 | 0 | 2 | 3 | 0 | 0 |
| hyper | 1 | 0 | 0 | 1 | 0 | 0 |
| hosp | 0 | 0 | 0 | 9 | 0 | 0 |
| death | 0 | 0 | 0 | 0 | 1 | 0 |
| n/s | 3 | 0 | 1 | 0 | 0 | 4 |

### outcome_severity, Dexcom

| Dexcom (gold down, system across) | none | sympt | hypo | hosp | n/s |
|---|---|---|---|---|---|
| none | 1 | 0 | 0 | 0 | 50 |
| sympt | 5 | 1 | 0 | 2 | 0 |
| hypo | 0 | 0 | 2 | 0 | 0 |
| hyper | 0 | 0 | 1 | 0 | 0 |
| hosp | 0 | 0 | 1 | 35 | 0 |
| n/s | 0 | 0 | 0 | 0 | 2 |

### outcome_severity, Medtronic

| Medtronic (gold down, system across) | none | hypo | hosp | death | n/s |
|---|---|---|---|---|---|
| none | 0 | 0 | 0 | 0 | 48 |
| sympt | 1 | 0 | 0 | 0 | 1 |
| hypo | 0 | 1 | 1 | 0 | 1 |
| hyper | 4 | 2 | 0 | 0 | 0 |
| hosp | 1 | 0 | 14 | 0 | 0 |
| death | 0 | 0 | 0 | 2 | 0 |
| n/s | 2 | 0 | 0 | 0 | 9 |

### user_action, all makers

| action (gold down, system across) | none | ate_carbs | took_insulin | skipped_insulin | sought_care | other | n/s |
|---|---|---|---|---|---|---|---|
| none | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ate_carbs | 1 | 14 | 3 | 0 | 0 | 0 | 0 |
| took_insulin | 0 | 2 | 6 | 0 | 1 | 0 | 0 |
| skipped_insulin | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| sought_care | 17 | 5 | 0 | 0 | 37 | 4 | 6 |
| other | 2 | 2 | 0 | 0 | 0 | 2 | 3 |
| n/s | 3 | 1 | 0 | 1 | 1 | 0 | 174 |

## 5. Run-to-run reproducibility (same version, two runs, same settings)

| Field | identical answers |
|---|---|
| fault_type | 94.4% |
| outcome_severity | 97.6% |
| user_action | 98.6% |
| fingerstick_check_done | 99.3% |
| multiple_pairs | 99.3% |
| sensor_value_mgdl | 98.6% |
| meter_value_mgdl | 98.6% |
| wear_day | 99.7% |
| parkes_zone_stated | 100.0% |
| all fields identical | 89.5% |

Kappa against gold in each run:

| Field | llm run 1 | llm run 2 | combined run 1 | combined run 2 |
|---|---|---|---|---|
| fault_type | 0.64 | 0.63 | 0.64 | 0.63 |
| outcome_severity | 0.34 | 0.35 | 0.34 | 0.35 |
| user_action | 0.66 | 0.67 | 0.66 | 0.67 |
| fingerstick_check_done | 0.76 | 0.75 | 0.76 | 0.75 |
| multiple_pairs | 0.71 | 0.71 | 0.80 | 0.80 |

## 6. v1 vs v2

Kappa of the combined system, per field and maker. Numbers: exact among system values (combined).

| Field | Group | v1 kappa | v2 kappa | change |
|---|---|---|---|---|
| fault_type | All | 0.61 | 0.64 | +0.03 |
| fault_type | Abbott | 0.69 | 0.69 | -0.00 |
| fault_type | Dexcom | 0.52 | 0.58 | +0.06 |
| fault_type | Medtronic | 0.50 | 0.52 | +0.02 |
| outcome_severity | All | 0.56 | 0.34 | -0.22 |
| outcome_severity | Abbott | 0.42 | 0.58 | +0.17 |
| outcome_severity | Dexcom | 0.70 | 0.28 | -0.42 |
| outcome_severity | Medtronic | 0.52 | 0.16 | -0.37 |
| user_action | All | 0.40 | 0.66 | +0.27 |
| user_action | Abbott | 0.39 | 0.66 | +0.27 |
| user_action | Dexcom | 0.52 | 0.72 | +0.20 |
| user_action | Medtronic | 0.21 | 0.53 | +0.31 |
| fingerstick_check_done | All | 0.73 | 0.76 | +0.04 |
| fingerstick_check_done | Abbott | 0.74 | 0.73 | -0.01 |
| fingerstick_check_done | Dexcom | 0.60 | 0.67 | +0.07 |
| fingerstick_check_done | Medtronic | 0.74 | 0.83 | +0.09 |
| multiple_pairs | All | 0.65 | 0.80 | +0.16 |
| multiple_pairs | Abbott | 0.93 | 1.00 | +0.07 |
| multiple_pairs | Dexcom | 0.29 | 0.42 | +0.13 |
| multiple_pairs | Medtronic | 0.32 | 0.39 | +0.07 |

| Field | Group | v1 exact among system | v2 exact among system | v1 exact among gold | v2 exact among gold |
|---|---|---|---|---|---|
| sensor_value_mgdl | All | 97% (75/77) | 98% (79/81) | 90% | 95% |
| sensor_value_mgdl | Abbott | 98% (57/58) | 98% (58/59) | 97% | 98% |
| sensor_value_mgdl | Dexcom | 94% (16/17) | 95% (18/19) | 84% | 95% |
| sensor_value_mgdl | Medtronic | 100% (2/2) | 100% (3/3) | 40% | 60% |
| meter_value_mgdl | All | 97% (93/96) | 92% (93/101) | 93% | 93% |
| meter_value_mgdl | Abbott | 100% (59/59) | 100% (60/60) | 98% | 100% |
| meter_value_mgdl | Dexcom | 88% (23/26) | 86% (25/29) | 82% | 89% |
| meter_value_mgdl | Medtronic | 100% (11/11) | 67% (8/12) | 92% | 67% |
| wear_day | All | 91% (51/56) | 93% (51/55) | 100% | 100% |
| wear_day | Abbott | 98% (51/52) | 98% (51/52) | 100% | 100% |
| wear_day | Dexcom | 0% (0/2) | 0% (0/1) | - | - |
| wear_day | Medtronic | 0% (0/2) | 0% (0/2) | - | - |
| parkes_zone_stated | All | 99% (83/84) | 99% (83/84) | 99% | 99% |
| parkes_zone_stated | Abbott | 100% (57/57) | 100% (57/57) | 100% | 100% |
| parkes_zone_stated | Dexcom | 96% (26/27) | 96% (26/27) | 96% | 96% |
| parkes_zone_stated | Medtronic | - (0/0) | - (0/0) | - | - |

| Field | v1 identical | v2 identical |
|---|---|---|
| fault_type | 94.8% | 94.4% |
| outcome_severity | 95.5% | 97.6% |
| user_action | 91.3% | 98.6% |
| fingerstick_check_done | 98.6% | 99.3% |
| multiple_pairs | 98.3% | 99.3% |
| sensor_value_mgdl | 98.3% | 98.6% |
| meter_value_mgdl | 98.3% | 98.6% |
| wear_day | 99.3% | 99.7% |
| parkes_zone_stated | 100.0% | 100.0% |
| all_fields_identical | 80.5% | 89.5% |
