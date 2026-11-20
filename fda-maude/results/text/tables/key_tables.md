# Key tables (markdown copies of the CSVs in this folder)

## a. Run facts
| metric | value |
|---|---|
| log_first_line | 2026-10-30 08:23:50 |
| log_last_line | 2026-10-30 17:57:08 |
| elapsed_first_to_last_h | 9.6 |
| segments_started | 1 |
| resumes | 0 |
| run_done_lines | 1 |
| sum_of_run_segments_h | 9.6 |
| errors_in_run_done_lines | 0 |
| last_progress_reports_per_min | 217.4 |
| last_progress_errors | 0 |
| summary_n_requested | 124,599 |
| summary_n_ok | 124,599 |
| summary_n_errors | 0 |
| summary_wall_s | 34395.4 |
| summary_reports_per_min | 217.4 |
| summary_latency_mean_s | 2.2 |
| summary_latency_p50_s | 2.1 |
| summary_latency_p90_s | 2.8 |
| summary_guard_drop_rate | 0.0 |
| summary_guard_drop_reports | 4,324 |
| summary_retries | 0 |
| summary_role_swap_reports | 26 |
| summary_mmol_converted_reports | 4,667 |
| summary_schema_fixed_reports | 0 |
| summary_output_tok_per_s_aggregate | 301.1 |
| summary_prompt_tokens_max | 5,889 |
| summary_guard_drops_by_field | {"parkes_zone_stated:context": 808, "wear_day:range": 59, "wear_day": 1561, "sensor_value_raw": 276, "wear_day:context": 654, "meter_value_raw": 1056} |
| summary_previous_runs | null |
| summary_model | qwen2.5:7b-instruct |
| summary_model_digest | 845dbda0ea48 |
| rows_in_jsonl | 124,599 |
| rows_expected | 124,599 |
| model_errors_in_jsonl | 0 |
| guard_drop_reports | 4,324 |
| guard_drop_rate_pct | 3.5 |
| guard_drops_by_field | {"parkes_zone_stated:context": 808, "wear_day:range": 59, "wear_day": 1561, "sensor_value_raw": 276, "wear_day:context": 654, "meter_value_raw": 1056} |
| zone_guard_drops_rescued_by_regex | 453 |
| zone_guard_drops_total | 808 |
| median_latency_s | 2.1 |
| retried_reports | 0 |
| rows_per_min_over_elapsed | 217.5 |

## a. Coverage
| tier | maker | n_reports | weighted_n | pct_fault_type_known | pct_both_values | pct_parkes_zone | pct_wear_day | pct_fingerstick_stated | pct_user_action_stated | pct_outcome_stated | pct_sensor_from_regex | pct_zone_stated_from_regex | pct_wear_day_from_regex | pct_any_guard_drop | pct_zone_guard_drop | pct_number_guard_drop | pct_model_error |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| serious | Abbott | 74,657 | 74,657 | 98.2 | 10.3 | 5.6 | 8.9 | 38.4 | 93.4 | 99.9 | 35.2 | 100.0 | 81.0 | 3.4 | 0.3 | 1.1 | 0.0 |
| serious | Dexcom | 32,045 | 32,045 | 88.5 | 30.4 | 26.0 | 3.6 | 56.9 | 87.6 | 98.8 | 0.0 | 99.9 | 33.1 | 3.9 | 0.6 | 1.2 | 0.0 |
| serious | Medtronic (undercounted; weakest validation) | 8,660 | 8,660 | 94.1 | 5.9 | 0.0 | 0.2 | 76.0 | 92.9 | 99.4 | 0.0 | 100.0 | 35.7 | 1.2 | 0.0 | 0.5 | 0.0 |
| serious | Other | 3,100 | 3,100 | 88.3 | 17.6 | 0.0 | 1.4 | 31.4 | 65.2 | 94.8 | 0.0 | 100.0 | 66.7 | 1.8 | 0.0 | 0.5 | 0.0 |
| serious | All | 118,462 | 118,462 | 95.0 | 15.6 | 10.6 | 6.6 | 46.0 | 91.1 | 99.4 | 14.7 | 99.9 | 73.9 | 3.3 | 0.4 | 1.1 | 0.0 |
| sample (weighted) | Abbott | 843 | 386,438 | 70.9 | 28.0 | 72.2 | 26.5 | 28.0 | 0.0 | 100.0 | 97.5 | 100.0 | 98.2 | 44.1 | 43.6 | 0.0 | 0.0 |
| sample (weighted) | Dexcom | 4,574 | 2,405,435 | 86.7 | 0.6 | 8.7 | 0.0 | 0.8 | 0.1 | 97.3 | 0.0 | 100.0 | 38.0 | 0.1 | 0.1 | 0.0 | 0.0 |
| sample (weighted) | Medtronic (undercounted; weakest validation) | 407 | 120,676 | 98.0 | 2.4 | 0.0 | 0.0 | 4.3 | 3.7 | 99.8 | 0.0 |  | 0.0 | 0.3 | 0.0 | 0.3 | 0.0 |
| sample (weighted) | Other | 313 | 9,953 | 79.7 | 2.3 | 0.0 | 1.0 | 2.3 | 6.1 | 96.9 | 0.0 |  | 24.1 | 4.1 | 0.0 | 0.0 | 0.0 |
| sample (weighted) | All | 6,137 | 2,922,501 | 85.1 | 4.3 | 16.7 | 3.5 | 4.5 | 0.2 | 97.8 | 82.1 | 100.0 | 98.1 | 6.0 | 5.8 | 0.0 | 0.0 |

## b. Fault type (% of reports)
| fault_type | serious / Abbott | serious / Dexcom | serious / Medtronic | serious / Other | serious / All | sample (weighted) / Abbott | sample (weighted) / Dexcom | sample (weighted) / Medtronic | sample (weighted) / Other | sample (weighted) / All |
|---|---|---|---|---|---|---|---|---|---|---|
| reads_low | 15.9 | 20.2 | 2.6 | 11.6 | 16.0 | 43.7 | 0.3 | 2.4 | 0.7 | 6.2 |
| reads_high | 11.4 | 15.0 | 2.6 | 7.5 | 11.6 | 7.1 | 0.2 | 0.3 | 1.0 | 1.2 |
| erratic | 0.4 | 1.7 | 0.1 | 1.5 | 0.7 | 7.3 | 0.1 | 0.0 | 0.6 | 1.0 |
| stuck | 0.0 | 0.1 | 0.2 | 0.2 | 0.1 | 0.0 | 0.2 | 0.1 | 0.6 | 0.1 |
| signal_loss | 9.5 | 6.0 | 3.7 | 3.7 | 8.0 | 0.1 | 47.9 | 78.1 | 3.2 | 42.7 |
| sensor_error_or_early_end | 26.1 | 5.1 | 1.6 | 3.9 | 18.1 | 10.2 | 16.8 | 1.8 | 17.8 | 15.3 |
| adhesive_or_detachment | 8.2 | 2.4 | 0.2 | 0.7 | 5.9 | 0.2 | 4.3 | 0.1 | 0.0 | 3.5 |
| insertion_or_skin_injury | 14.5 | 22.8 | 2.3 | 26.5 | 16.1 | 0.0 | 0.5 | 0.0 | 0.8 | 0.4 |
| other_device | 12.2 | 15.2 | 80.9 | 32.5 | 18.5 | 2.3 | 16.4 | 15.1 | 55.0 | 14.6 |
| unclear | 1.8 | 11.5 | 5.9 | 11.7 | 5.0 | 29.1 | 13.3 | 2.0 | 20.3 | 14.9 |

## b. Text reads_low vs codes
| tier | maker | n_text_reads_low | reads_low_with_code_low_readings_pct | reads_low_with_code_incorrect_pct | reads_low_with_code_high_readings_pct | reads_low_with_any_wrong_reading_code_pct | reads_low_with_neither_pct | n_text_reads_high | reads_high_with_code_high_readings_pct | reads_high_with_code_low_readings_pct | reads_high_with_any_wrong_reading_code_pct | n_code_low_readings | code_low_text_reads_low_pct | code_low_text_reads_high_pct | code_low_text_unclear_pct | code_low_text_other_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| serious | Abbott | 11,880 | 94.7 | 1.9 | 1.2 | 97.2 | 2.8 | 8,481 | 96.4 | 1.8 | 99.2 | 12,428 | 90.5 | 1.2 | 3.3 | 4.9 |
| serious | Dexcom | 6,470 | 17.9 | 41.9 | 5.5 | 93.3 | 6.7 | 4,817 | 11.4 | 8.7 | 94.3 | 1,802 | 64.4 | 23.3 | 5.3 | 7.0 |
| serious | Medtronic (undercounted; weakest validation) | 224 | 4.0 | 44.6 | 0.4 | 72.3 | 27.7 | 222 | 3.2 | 0.5 | 88.3 | 12 | 75.0 | 8.3 | 16.7 | 0.0 |
| serious | Other | 359 | 0.0 | 0.0 | 0.0 | 94.2 | 5.8 | 234 | 0.0 | 0.0 | 95.3 | 0 |  |  |  |  |
| serious | All | 18,933 | 65.6 | 16.1 | 2.6 | 95.5 | 4.5 | 13,754 | 63.5 | 4.2 | 97.3 | 14,242 | 87.2 | 4.0 | 3.6 | 5.2 |
| sample (weighted) | Abbott | 334 | 57.3 | 43.0 | 0.0 | 100.0 | 0.0 | 66 | 1.3 | 2.1 | 100.0 | 174 | 95.9 | 0.6 | 0.6 | 2.9 |
| sample (weighted) | Dexcom | 18 | 0.0 | 0.2 | 0.0 | 99.0 | 1.0 | 11 | 0.0 | 0.0 | 78.1 | 63 | 0.0 | 0.0 | 100.0 | 0.0 |
| sample (weighted) | Medtronic (undercounted; weakest validation) | 19 | 0.0 | 71.3 | 0.0 | 85.7 | 14.3 | 5 | 0.0 | 0.0 | 96.0 | 0 |  |  |  |  |
| sample (weighted) | Other | 4 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 8 | 0.0 | 0.0 | 99.0 | 0 |  |  |  |  |
| sample (weighted) | All | 375 | 53.7 | 41.5 | 0.0 | 99.7 | 0.3 | 90 | 1.0 | 1.7 | 96.2 | 237 | 70.2 | 0.4 | 27.2 | 2.1 |

## c. Error sizes
| group_type | group | tier | n_pairs | weighted_n | median_mgdl | q1_mgdl | q3_mgdl | p10_mgdl | p90_mgdl | median_pct | q1_pct | q3_pct | p10_pct | p90_pct | pct_low | pct_high | median_sensor_mgdl | median_meter_mgdl |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tier | All | serious | 18,118 | 18,118 | -0.4 | -239.0 | 80.0 | -442.0 | 193.0 | -0.2 | -72.1 | 156.9 | -87.2 | 384.6 | 50.0 | 48.9 | 101.0 | 128.0 |
| tier | All | sample (weighted) | 327 | 125,755 | -105.9 | -149.1 | 41.8 | -209.6 | 191.0 | -63.6 | -71.1 | 59.1 | -79.6 | 151.4 | 73.1 | 26.9 | 67.0 | 174.7 |
| maker | Abbott | serious | 7,556 | 7,556 | -65.0 | -278.0 | 95.0 | -448.0 | 230.0 | -46.7 | -80.0 | 144.2 | -88.7 | 409.9 | 57.6 | 41.7 | 90.0 | 166.5 |
| maker | Abbott | sample (weighted) | 255 | 107,133 | -110.0 | -151.2 | 56.0 | -210.1 | 200.0 | -65.0 | -72.1 | 83.8 | -80.3 | 160.1 | 73.3 | 26.7 | 64.7 | 177.9 |
| maker | Dexcom | serious | 9,518 | 9,518 | 27.0 | -207.0 | 77.0 | -440.0 | 159.0 | 42.1 | -62.8 | 168.8 | -85.7 | 380.0 | 43.7 | 55.2 | 110.0 | 91.5 |
| maker | Dexcom | sample (weighted) | 32 | 15,488 | -61.0 | -100.9 | 38.0 | -158.8 | 116.1 | -44.9 | -57.5 | 29.3 | -72.7 | 97.6 | 68.5 | 31.5 | 92.8 | 150.3 |
| maker | Medtronic (undercounted; weakest validation) | serious | 500 | 500 | -23.5 | -220.0 | 65.0 | -414.0 | 127.0 | -14.5 | -64.5 | 143.5 | -83.1 | 289.4 | 51.4 | 42.4 | 119.0 | 150.0 |
| maker | Medtronic (undercounted; weakest validation) | sample (weighted) | 24 | 2,907 | -144.5 | -185.4 | -100.9 | -213.9 | 23.6 | -65.6 | -72.9 | -49.7 | -76.0 | 47.3 | 91.6 | 8.4 | 68.1 | 216.7 |
| maker | Other | serious | 544 | 544 | -19.5 | -105.0 | 60.0 | -229.1 | 112.0 | -18.6 | -52.8 | 116.8 | -69.7 | 225.2 | 53.5 | 45.8 | 105.0 | 99.5 |
| maker | Other | sample (weighted) | 16 | 226 | -61.9 | -70.7 | 53.7 | -146.2 | 173.3 | -30.7 | -38.6 | 46.8 | -62.0 | 154.8 | 64.3 | 35.7 | 143.8 | 203.9 |
| event_type | Injury | serious | 18,093 | 18,093 | 0.0 | -238.0 | 80.0 | -441.0 | 193.0 | 0.0 | -72.0 | 157.1 | -87.1 | 384.7 | 50.0 | 49.0 | 101.0 | 128.0 |
| event_type | Death | serious | 25 | 25 | -450.0 | -911.5 | -227.5 | -1,272 | 71.0 | -86.2 | -91.1 | -63.4 | -95.2 | 240.4 | 84.0 | 16.0 | 95.0 | 510.0 |
| event_type | Malfunction | sample (weighted) | 327 | 125,755 | -105.9 | -149.1 | 41.8 | -209.6 | 191.0 | -63.6 | -71.1 | 59.1 | -79.6 | 151.4 | 73.1 | 26.9 | 67.0 | 174.7 |
| fault_type | reads_low | serious | 9,194 | 9,194 | -148.0 | -354.0 | 0.0 | -500.1 | 62.0 | -64.4 | -83.9 | 0.0 | -90.0 | 173.5 | 74.5 | 24.9 | 70.0 | 239.0 |
| fault_type | reads_high | serious | 7,485 | 7,485 | 76.0 | 30.0 | 170.0 | -252.0 | 277.0 | 125.9 | 32.3 | 300.0 | -59.3 | 654.7 | 20.3 | 79.0 | 180.0 | 60.0 |
| fault_type | erratic | serious | 317 | 317 | -35.0 | -200.8 | 80.0 | -355.8 | 174.8 | -27.8 | -69.3 | 89.8 | -84.9 | 293.8 | 55.5 | 43.8 | 120.0 | 155.0 |
| fault_type | stuck | serious | 13 | 13 | -169.0 | -334.5 | 40.0 | -456.4 | 132.6 | -74.5 | -83.8 | 43.1 | -90.2 | 105.4 | 69.2 | 30.8 | 63.0 | 270.0 |
| fault_type | signal_loss | serious | 89 | 89 | 0.0 | -71.5 | 23.7 | -239.6 | 104.0 | 0.0 | -45.5 | 56.3 | -74.6 | 154.9 | 46.1 | 43.8 | 70.0 | 79.0 |
| fault_type | sensor_error_or_early_end | serious | 157 | 157 | 0.0 | -107.0 | 44.3 | -338.6 | 128.0 | 0.0 | -60.9 | 57.4 | -80.0 | 300.0 | 49.7 | 33.8 | 70.0 | 105.0 |
| fault_type | adhesive_or_detachment | serious | 29 | 29 | 0.0 | -331.8 | 18.0 | -511.2 | 124.6 | 0.0 | -84.4 | 9.4 | -88.6 | 316.1 | 48.3 | 24.1 | 80.0 | 140.0 |
| fault_type | insertion_or_skin_injury | serious | 36 | 36 | -22.0 | -136.5 | 0.0 | -307.8 | 41.0 | -21.0 | -69.0 | 0.0 | -86.3 | 74.0 | 58.3 | 22.2 | 74.5 | 142.0 |
| fault_type | other_device | serious | 311 | 311 | -10.0 | -148.8 | 22.0 | -359.8 | 92.4 | -8.7 | -55.6 | 49.7 | -77.8 | 214.0 | 54.7 | 36.7 | 107.0 | 132.0 |
| fault_type | unclear | serious | 487 | 487 | 30.0 | -69.5 | 80.0 | -324.8 | 155.8 | 40.4 | -42.0 | 167.5 | -75.0 | 457.2 | 35.9 | 61.8 | 113.0 | 74.0 |
| libre3_recall | Libre 3: received before 2025-11-24 | serious | 1,355 | 1,355 | -180.0 | -440.8 | 40.7 | -649.0 | 151.0 | -70.3 | -87.3 | 62.3 | -91.4 | 310.0 | 69.8 | 29.8 | 70.0 | 270.0 |
| libre3_recall | Libre 3: received on/after 2025-11-24 | serious | 1,044 | 1,044 | -98.0 | -246.0 | 70.0 | -423.2 | 213.2 | -58.8 | -79.3 | 94.7 | -88.3 | 286.8 | 67.3 | 32.2 | 70.0 | 170.0 |
| libre3_recall | Libre 3: event before 2025-11-24 | serious | 1,481 | 1,481 | -185.0 | -440.0 | 37.2 | -647.0 | 150.0 | -71.3 | -87.4 | 47.2 | -91.4 | 290.2 | 71.4 | 28.2 | 69.0 | 269.0 |
| libre3_recall | Libre 3: event on/after 2025-11-24 | serious | 906 | 906 | -78.0 | -222.0 | 90.0 | -396.8 | 225.0 | -54.5 | -77.3 | 108.3 | -87.0 | 300.0 | 64.2 | 35.2 | 74.0 | 162.5 |
| maker_direction | Abbott / sensor reads low | serious | 4,352 | 4,352 | -239.5 | -403.5 | -111.5 | -527.3 | -54.0 | -76.8 | -86.4 | -59.8 | -90.4 | -42.1 | 100.0 | 0.0 | 60.0 | 317.0 |
| maker_direction | Abbott / sensor reads high | serious | 3,149 | 3,149 | 120.0 | 60.0 | 225.0 | 38.0 | 336.0 | 190.0 | 100.0 | 400.0 | 55.6 | 765.5 | 0.0 | 100.0 | 202.0 | 52.0 |
| maker_direction | Dexcom / sensor reads low | serious | 4,160 | 4,160 | -258.0 | -426.0 | -111.0 | -557.0 | -50.0 | -68.4 | -84.6 | -46.8 | -90.9 | -29.3 | 100.0 | 0.0 | 86.0 | 414.0 |
| maker_direction | Dexcom / sensor reads high | serious | 5,255 | 5,255 | 69.0 | 41.0 | 126.0 | 28.0 | 232.0 | 150.0 | 80.1 | 300.0 | 43.3 | 592.3 | 0.0 | 100.0 | 121.0 | 40.0 |

## c. Parkes agreement
| maker | n_pairs_with_stated_zone | exact_agreement_pct | within_one_zone_pct | stated_zone_worse_pct | computed_zone_worse_pct | stated_C_to_E_pct | computed_C_to_E_pct |
|---|---|---|---|---|---|---|---|
| Abbott | 4,134 | 87.9 | 98.1 | 8.9 | 3.3 | 99.9 | 94.8 |
| Dexcom | 6,531 | 86.6 | 96.0 | 7.4 | 6.0 | 71.8 | 71.2 |
| Medtronic (undercounted; weakest validation) | 1 | 100.0 | 100.0 | 0.0 | 0.0 | 100.0 | 100.0 |
| Other | 1 | 100.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| All | 10,667 | 87.1 | 96.8 | 8.0 | 4.9 | 82.6 | 80.4 |

## c. Parkes zone shares
| source | maker | n_with_zone | zone_A_pct | zone_B_pct | zone_C_pct | zone_D_pct | zone_E_pct |
|---|---|---|---|---|---|---|---|
| MAUDE serious | Abbott | 4,177 | 0.0 | 0.2 | 46.6 | 47.8 | 5.4 |
| MAUDE serious | Dexcom | 8,329 | 4.4 | 23.5 | 29.5 | 35.7 | 6.9 |
| MAUDE serious | Medtronic (undercounted; weakest validation) | 2 | 0.0 | 0.0 | 50.0 | 50.0 | 0.0 |
| MAUDE serious | Other | 1 | 0.0 | 100.0 | 0.0 | 0.0 | 0.0 |
| MAUDE serious | All | 12,509 | 3.0 | 15.7 | 35.2 | 39.8 | 6.4 |
| MAUDE sample (weighted) | Abbott | 629 | 0.0 | 0.0 | 34.4 | 5.2 | 60.4 |
| MAUDE sample (weighted) | Dexcom | 380 | 0.5 | 2.5 | 5.3 | 90.3 | 1.4 |
| MAUDE sample (weighted) | All | 1,009 | 0.2 | 1.1 | 21.9 | 41.7 | 35.1 |
| REPLACE-BG trial, Set A (all pairs) | Dexcom G4 | 33,467 | 83.7 | 14.6 | 1.4 | 0.3 | 0.0 |

## d. Wear day summary
| tier | maker | n_with_wear_day | pct_of_reports_with_wear_day | median_wear_day | pct_day_1 | pct_days_1_2 | pct_days_1_3 | sensor_life_days | pct_last_two_days | pct_beyond_life | flat_day_1_pct | flat_days_1_2_pct | flat_last_two_pct | day_1_ratio_to_flat |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| serious | Abbott | 6,627 | 8.9 | 5.0 | 13.4 | 24.3 | 35.3 | 14.0 | 6.6 | 0.4 | 7.1 | 14.3 | 14.3 | 1.9 |
| serious | Dexcom | 1,140 | 3.6 | 6.0 | 7.1 | 17.9 | 32.3 | 10.0 | 18.2 | 1.3 | 10.0 | 20.0 | 20.0 | 0.7 |
| serious | Medtronic (undercounted; weakest validation) | 14 | 0.2 | 3.0 | 21.4 | 28.6 | 57.1 |  |  |  |  |  |  |  |
| serious | Other | 42 | 1.4 | 4.5 | 4.8 | 21.4 | 38.1 |  |  |  |  |  |  |  |
| serious | All | 7,823 | 6.6 | 5.0 | 12.5 | 23.3 | 34.9 |  |  |  |  |  |  |  |
| sample (weighted) | Abbott | 217 | 26.5 | 3.0 | 34.5 | 42.7 | 53.0 | 14.0 | 3.0 | 0.6 | 7.1 | 14.3 | 14.3 | 4.8 |
| sample (weighted) | All | 235 | 3.5 | 3.0 | 34.4 | 42.6 | 52.9 |  |  |  |  |  |  |  |

## e. reads_low: actions and outcomes
| tier | maker | n_reads_low | ate_carbs_pct | skipped_insulin_pct | ate_carbs_or_skipped_insulin_pct | took_insulin_pct | sought_care_pct | fingerstick_yes_pct | hypoglycemia_pct | hyperglycemia_or_dka_pct | hospital_or_er_pct | death_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| serious | Abbott | 11,880 | 20.5 | 0.2 | 20.7 | 16.9 | 50.9 | 56.5 | 8.9 | 0.0 | 72.1 | 0.1 |
| serious | Dexcom | 6,470 | 40.3 | 0.1 | 40.4 | 6.5 | 46.7 | 90.6 | 11.5 | 0.0 | 83.9 | 0.0 |
| serious | Medtronic (undercounted; weakest validation) | 224 | 29.0 | 2.7 | 31.7 | 12.5 | 23.2 | 93.3 | 34.4 | 0.0 | 45.5 | 0.0 |
| serious | Other | 359 | 37.6 | 0.0 | 37.6 | 10.0 | 9.5 | 83.0 | 38.7 | 0.0 | 16.7 | 0.0 |
| serious | All | 18,933 | 27.7 | 0.2 | 27.9 | 13.1 | 48.3 | 69.1 | 10.6 | 0.0 | 74.8 | 0.1 |
| sample (weighted) | Abbott | 334 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 45.4 | 0.0 | 0.0 | 0.0 | 0.0 |
| sample (weighted) | Dexcom | 18 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 100.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| sample (weighted) | Medtronic (undercounted; weakest validation) | 19 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | 4.4 | 0.0 | 0.0 | 0.0 |
| sample (weighted) | All | 375 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 48.9 | 0.2 | 0.0 | 0.0 | 0.0 |

## e. Fingerstick check (all fault types)
| tier | maker | fault_type | n | yes_pct | no_pct | not_stated_pct |
|---|---|---|---|---|---|---|
| serious | Abbott | All | 74,657 | 32.5 | 5.9 | 61.6 |
| serious | Dexcom | All | 32,045 | 50.3 | 6.6 | 43.1 |
| serious | Medtronic (undercounted; weakest validation) | All | 8,660 | 69.9 | 6.1 | 24.0 |
| serious | Other | All | 3,100 | 27.0 | 4.3 | 68.6 |
| serious | All | All | 118,462 | 39.9 | 6.1 | 54.0 |
| sample (weighted) | Abbott | All | 843 | 28.0 | 0.0 | 72.0 |
| sample (weighted) | Dexcom | All | 4,574 | 0.8 | 0.0 | 99.2 |
| sample (weighted) | Medtronic (undercounted; weakest validation) | All | 407 | 3.8 | 0.5 | 95.7 |
| sample (weighted) | Other | All | 313 | 2.3 | 0.0 | 97.7 |
| sample (weighted) | All | All | 6,137 | 4.5 | 0.0 | 95.5 |

## e. Outcome (all fault types)
| tier | maker | fault_type | n | none_pct | symptoms_only_pct | hypoglycemia_pct | hyperglycemia_or_dka_pct | hospital_or_er_pct | death_pct | not_stated_pct | any_glucose_event_or_worse_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|
| serious | Abbott | All | 74,657 | 11.1 | 22.2 | 15.6 | 0.0 | 50.7 | 0.2 | 0.1 | 66.5 |
| serious | Dexcom | All | 32,045 | 8.4 | 21.4 | 9.7 | 0.0 | 58.3 | 1.0 | 1.2 | 69.0 |
| serious | Medtronic (undercounted; weakest validation) | All | 8,660 | 7.2 | 1.5 | 13.6 | 0.0 | 75.9 | 1.2 | 0.6 | 90.7 |
| serious | Other | All | 3,100 | 33.3 | 22.8 | 19.7 | 0.0 | 18.7 | 0.2 | 5.2 | 38.7 |
| serious | All | All | 118,462 | 10.7 | 20.5 | 14.0 | 0.0 | 53.8 | 0.5 | 0.6 | 68.2 |
| sample (weighted) | Abbott | All | 843 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| sample (weighted) | Dexcom | All | 4,574 | 97.3 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2.7 | 0.0 |
| sample (weighted) | Medtronic (undercounted; weakest validation) | All | 407 | 98.2 | 0.6 | 0.8 | 0.0 | 0.3 | 0.0 | 0.2 | 1.0 |
| sample (weighted) | Other | All | 313 | 93.7 | 0.2 | 1.2 | 0.0 | 1.8 | 0.0 | 3.1 | 3.0 |
| sample (weighted) | All | All | 6,137 | 97.7 | 0.0 | 0.1 | 0.0 | 0.0 | 0.0 | 2.2 | 0.1 |

## e. Model outcome vs FDA patient-outcome codes (serious reports; a report may carry several codes)
| model_outcome | n | pct_of_serious | fda_required_intervention_n | fda_required_intervention_pct | fda_hospitalization_n | fda_hospitalization_pct | fda_life_threatening_n | fda_life_threatening_pct | fda_death_n | fda_death_pct | fda_other_n | fda_other_pct | fda_disability_n | fda_disability_pct | fda_none_stated_n | fda_none_stated_pct | fda_care_n | fda_care_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 12,636 | 10.7 | 5,027 | 39.8 | 247 | 2.0 | 544 | 4.3 | 3 | 0.0 | 3,134 | 24.8 | 208 | 1.6 | 4,011 | 31.7 | 5,249 | 41.5 |
| symptoms_only | 24,275 | 20.5 | 14,627 | 60.3 | 126 | 0.5 | 70 | 0.3 | 1 | 0.0 | 8,446 | 34.8 | 560 | 2.3 | 1,070 | 4.4 | 14,740 | 60.7 |
| hypoglycemia | 16,568 | 14.0 | 8,105 | 48.9 | 389 | 2.3 | 363 | 2.2 | 2 | 0.0 | 6,951 | 42.0 | 78 | 0.5 | 1,092 | 6.6 | 8,480 | 51.2 |
| hyperglycemia_or_dka | 4 | 0.0 | 0 | 0.0 | 1 | 25.0 | 0 | 0.0 | 0 | 0.0 | 2 | 50.0 | 0 | 0.0 | 1 | 25.0 | 1 | 25.0 |
| hospital_or_er | 63,700 | 53.8 | 35,121 | 55.1 | 15,597 | 24.5 | 429 | 0.7 | 88 | 0.1 | 21,191 | 33.3 | 96 | 0.2 | 773 | 1.2 | 47,906 | 75.2 |
| death | 559 | 0.5 | 11 | 2.0 | 51 | 9.1 | 26 | 4.7 | 515 | 92.1 | 196 | 35.1 | 21 | 3.8 | 5 | 0.9 | 58 | 10.4 |
| not_stated | 720 | 0.6 | 132 | 18.3 | 64 | 8.9 | 71 | 9.9 | 0 | 0.0 | 357 | 49.6 | 53 | 7.4 | 184 | 25.6 | 193 | 26.8 |
| All serious | 118,462 | 100.0 | 63,023 | 53.2 | 16,475 | 13.9 | 1,503 | 1.3 | 609 | 0.5 | 40,277 | 34.0 | 1,016 | 0.9 | 7,136 | 6.0 | 76,627 | 64.7 |

## f. Join, reads-low pairs (lookup: simulation_v2_lookup_extended.csv, bias -90 to +90 %)
| group | clip | n_pairs | weighted_n | clip_low_pct | clip_high_pct | pct_model_labelled_reads_low | skipped_pct_expected | changed_1_pct_expected | low70_false_per_day_expected | high180_missed_pct_expected | tir_pct_expected | tir_pct_change_vs_true | tbr70_pct_expected | tbr70_pct_change_vs_true | lbgi_expected | lbgi_change_vs_true | skipped_pct_expected_mean_person | median_err_pct | pct_beyond_minus_12 | pct_beyond_minus_20 | pct_beyond_minus_40 | pct_beyond_plus_40 | pct_beyond_clip_low | pct_beyond_clip_high |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Serious / Abbott | table edge (-90 / +90 %) | 4,352 | 4,352 | -90.00 | 90.00 | 93.80 | 49.34 | 38.38 | 0.85 | 96.39 | 19.30 | -43.95 | 79.54 | 76.04 | 26.73 | 25.79 | 48.62 | -76.75 | 99.22 | 98.12 | 90.67 | 0.00 | 8.27 | 0.00 |
| Serious / Dexcom | table edge (-90 / +90 %) | 4,160 | 4,160 | -90.00 | 90.00 | 59.45 | 45.18 | 37.27 | 1.00 | 92.70 | 28.67 | -34.58 | 68.99 | 65.48 | 22.55 | 21.60 | 44.51 | -68.44 | 98.39 | 96.59 | 80.48 | 0.00 | 9.64 | 0.00 |
| Serious / Medtronic (undercounted; weakest validation) | table edge (-90 / +90 %) | 257.00 | 257.00 | -90.00 | 90.00 | 47.47 | 43.67 | 36.43 | 1.08 | 90.93 | 32.11 | -31.14 | 64.99 | 61.48 | 20.59 | 19.65 | 42.97 | -63.77 | 97.67 | 94.16 | 77.82 | 0.00 | 5.06 | 0.00 |
| Serious / all makers | table edge (-90 / +90 %) | 9,060 | 9,060 | -90.00 | 90.00 | 75.64 | 46.94 | 37.72 | 0.94 | 94.25 | 24.83 | -38.42 | 73.32 | 69.82 | 24.23 | 23.28 | 46.24 | -72.10 | 98.73 | 97.09 | 84.96 | 0.00 | 8.55 | 0.00 |
| Malfunction sample (weighted) / all makers | table edge (-90 / +90 %) | 229.00 | 91,903 | -90.00 | 90.00 | 90.09 | 50.63 | 38.91 | 1.22 | 97.98 | 23.01 | -40.24 | 76.34 | 72.84 | 22.90 | 21.95 | 49.65 | -67.43 | 100.00 | 98.67 | 94.14 | 0.00 | 0.65 | 0.00 |
| Malfunction sample (weighted) / Abbott | table edge (-90 / +90 %) | 179.00 | 78,486 | -90.00 | 90.00 | 93.94 | 51.85 | 39.32 | 1.18 | 98.94 | 20.11 | -43.14 | 79.54 | 76.04 | 24.03 | 23.09 | 50.84 | -68.32 | 100.00 | 99.94 | 96.82 | 0.00 | 0.76 | 0.00 |
| Serious / Libre 3 received on/after 2025-11-24 | table edge (-90 / +90 %) | 703.00 | 703.00 | -90.00 | 90.00 | 92.03 | 48.80 | 38.24 | 0.94 | 96.06 | 21.66 | -41.60 | 77.08 | 73.58 | 25.29 | 24.35 | 48.06 | -73.10 | 99.00 | 97.87 | 89.90 | 0.00 | 5.55 | 0.00 |
| Serious / Libre 3 received before 2025-11-24 | table edge (-90 / +90 %) | 946.00 | 946.00 | -90.00 | 90.00 | 94.29 | 50.84 | 38.74 | 0.67 | 97.54 | 13.84 | -49.42 | 85.37 | 81.87 | 29.91 | 28.97 | 50.18 | -83.33 | 99.26 | 98.73 | 94.29 | 0.00 | 16.28 | 0.00 |
| Serious / Injury | table edge (-90 / +90 %) | 9,039 | 9,039 | -90.00 | 90.00 | 75.67 | 46.93 | 37.71 | 0.94 | 94.23 | 24.88 | -38.38 | 73.27 | 69.77 | 24.21 | 23.26 | 46.22 | -72.04 | 98.73 | 97.08 | 84.92 | 0.00 | 8.51 | 0.00 |
| Serious / Death | table edge (-90 / +90 %) | 21.00 | 21.00 | -90.00 | 90.00 | 61.90 | 53.42 | 39.42 | 0.47 | 99.83 | 6.36 | -56.90 | 93.61 | 90.11 | 33.87 | 32.92 | 52.80 | -89.70 | 100.00 | 100.00 | 100.00 | 0.00 | 28.57 | 0.00 |
| Serious / Abbott | clipped at -40 % (floor) | 4,352 | 4,352 | -40.00 | 40.00 | 93.80 | 31.30 | 37.72 | 1.75 | 86.54 | 69.93 | 6.67 | 25.30 | 21.80 | 5.87 | 4.93 | 30.99 | -76.75 | 99.22 | 98.12 | 90.67 | 0.00 | 90.67 | 0.00 |
| Serious / Dexcom | clipped at -40 % (floor) | 4,160 | 4,160 | -40.00 | 40.00 | 59.45 | 29.76 | 36.69 | 1.69 | 84.15 | 70.28 | 7.02 | 24.23 | 20.73 | 5.62 | 4.68 | 29.51 | -68.44 | 98.39 | 96.59 | 80.48 | 0.00 | 80.48 | 0.00 |
| Serious / Medtronic (undercounted; weakest validation) | clipped at -40 % (floor) | 257.00 | 257.00 | -40.00 | 40.00 | 47.47 | 28.90 | 35.87 | 1.65 | 82.69 | 70.41 | 7.15 | 23.66 | 20.15 | 5.49 | 4.55 | 28.68 | -63.77 | 97.67 | 94.16 | 77.82 | 0.00 | 77.82 | 0.00 |
| Serious / all makers | clipped at -40 % (floor) | 9,060 | 9,060 | -40.00 | 40.00 | 75.64 | 30.41 | 37.10 | 1.71 | 85.14 | 70.12 | 6.87 | 24.69 | 21.18 | 5.73 | 4.78 | 30.14 | -72.10 | 98.73 | 97.09 | 84.96 | 0.00 | 84.96 | 0.00 |
| Malfunction sample (weighted) / all makers | clipped at -40 % (floor) | 229.00 | 91,903 | -40.00 | 40.00 | 90.09 | 31.97 | 38.23 | 1.77 | 87.71 | 69.83 | 6.58 | 25.76 | 22.26 | 5.98 | 5.03 | 31.64 | -67.43 | 100.00 | 98.67 | 94.14 | 0.00 | 94.14 | 0.00 |
| Malfunction sample (weighted) / Abbott | clipped at -40 % (floor) | 179.00 | 78,486 | -40.00 | 40.00 | 93.94 | 32.36 | 38.62 | 1.79 | 88.31 | 69.76 | 6.51 | 26.01 | 22.51 | 6.04 | 5.09 | 32.01 | -68.32 | 100.00 | 99.94 | 96.82 | 0.00 | 96.82 | 0.00 |
| Serious / Libre 3 received on/after 2025-11-24 | clipped at -40 % (floor) | 703.00 | 703.00 | -40.00 | 40.00 | 92.03 | 31.23 | 37.60 | 1.74 | 86.44 | 69.93 | 6.67 | 25.27 | 21.77 | 5.87 | 4.92 | 30.93 | -73.10 | 99.00 | 97.87 | 89.90 | 0.00 | 89.90 | 0.00 |
| Serious / Libre 3 received before 2025-11-24 | clipped at -40 % (floor) | 946.00 | 946.00 | -40.00 | 40.00 | 94.29 | 31.79 | 38.06 | 1.76 | 87.26 | 69.81 | 6.55 | 25.64 | 22.13 | 5.95 | 5.00 | 31.46 | -83.33 | 99.26 | 98.73 | 94.29 | 0.00 | 94.29 | 0.00 |
| Serious / Injury | clipped at -40 % (floor) | 9,039 | 9,039 | -40.00 | 40.00 | 75.67 | 30.41 | 37.10 | 1.71 | 85.13 | 70.12 | 6.87 | 24.68 | 21.18 | 5.73 | 4.78 | 30.13 | -72.04 | 98.73 | 97.08 | 84.92 | 0.00 | 84.92 | 0.00 |
| Serious / Death | clipped at -40 % (floor) | 21.00 | 21.00 | -40.00 | 40.00 | 61.90 | 32.64 | 38.69 | 1.80 | 88.67 | 69.65 | 6.40 | 26.23 | 22.72 | 6.09 | 5.14 | 32.27 | -89.70 | 100.00 | 100.00 | 100.00 | 0.00 | 100.00 | 0.00 |
| Reference: constant bias -12 % (lookup row) |  |  |  |  |  |  | 0.69 | 0.14 | 0.50 | 32.57 | 71.51 | 8.25 | 6.77 | 3.27 | 1.60 | 0.65 |  |  |  |  |  |  |  |  |
| Reference: constant bias -20 % (lookup row) |  |  |  |  |  |  | 7.25 | 16.67 | 0.86 | 50.78 | 74.79 | 11.54 | 10.10 | 6.60 | 2.33 | 1.39 |  |  |  |  |  |  |  |  |
| Reference: constant bias -30 % (lookup row) |  |  |  |  |  |  | 19.99 | 36.02 | 1.31 | 70.84 | 74.80 | 11.54 | 15.99 | 12.49 | 3.76 | 2.82 |  |  |  |  |  |  |  |  |
| Reference: constant bias -40 % (lookup row) |  |  |  |  |  |  | 32.64 | 38.69 | 1.80 | 88.67 | 69.65 | 6.40 | 26.23 | 22.72 | 6.09 | 5.14 |  |  |  |  |  |  |  |  |
| Reference: constant bias -60 % (lookup row) |  |  |  |  |  |  | 52.30 | 39.42 | 1.96 | 100.00 | 36.19 | -27.06 | 63.81 | 60.30 | 16.32 | 15.37 |  |  |  |  |  |  |  |  |
| Reference: constant bias -80 % (lookup row) |  |  |  |  |  |  | 54.20 | 39.42 | 0.27 | 100.00 | 0.50 | -62.75 | 99.50 | 96.00 | 35.09 | 34.14 |  |  |  |  |  |  |  |  |
| Reference: constant bias -90 % (lookup row) |  |  |  |  |  |  | 54.20 | 39.42 | 0.19 | 100.00 | 0.00 | -63.25 | 100.00 | 96.50 | 38.20 | 37.25 |  |  |  |  |  |  |  |  |

## f. Join, all pairs (both directions)
| group | clip | n_pairs | weighted_n | clip_low_pct | clip_high_pct | pct_model_labelled_reads_low | skipped_pct_expected | changed_1_pct_expected | low70_false_per_day_expected | high180_missed_pct_expected | tir_pct_expected | tir_pct_change_vs_true | tbr70_pct_expected | tbr70_pct_change_vs_true | lbgi_expected | lbgi_change_vs_true | low70_missed_pct_expected | spurious_pct_expected | high180_false_per_day_expected | skipped_pct_expected_mean_person | median_err_pct | pct_abs_beyond_12 | pct_abs_beyond_20 | pct_beyond_minus_40 | pct_beyond_plus_40 | pct_beyond_clip_low | pct_beyond_clip_high |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Serious / Abbott | table edge (-90 / +90 %) | 7,556 | 7,556 | -90.00 | 90.00 | 55.76 | 28.42 | 57.08 | 0.49 | 55.52 | 18.46 | -44.79 | 45.88 | 42.38 | 15.42 | 14.48 | 40.18 | 9.17 | 0.40 | 28.00 | -46.67 | 98.44 | 97.29 | 52.22 | 39.02 | 4.76 | 32.57 |
| Serious / Dexcom | table edge (-90 / +90 %) | 9,518 | 9,518 | -90.00 | 90.00 | 47.73 | 19.75 | 61.95 | 0.44 | 40.51 | 22.97 | -40.28 | 30.27 | 26.76 | 9.90 | 8.95 | 52.58 | 11.79 | 0.54 | 19.45 | 42.11 | 97.57 | 96.21 | 35.18 | 50.22 | 4.21 | 39.22 |
| Serious / Medtronic (undercounted; weakest validation) | table edge (-90 / +90 %) | 500 | 500 | -90.00 | 90.00 | 34.00 | 22.45 | 54.03 | 0.56 | 46.74 | 27.66 | -35.60 | 33.67 | 30.17 | 10.67 | 9.72 | 40.71 | 9.20 | 0.41 | 22.09 | -14.51 | 92.20 | 90.00 | 40.00 | 39.20 | 2.60 | 33.20 |
| Serious / all makers | table edge (-90 / +90 %) | 18,118 | 18,118 | -90.00 | 90.00 | 50.75 | 23.47 | 59.52 | 0.47 | 47.13 | 21.54 | -41.72 | 36.77 | 33.26 | 12.15 | 11.21 | 46.80 | 10.56 | 0.48 | 23.12 | -0.21 | 97.76 | 96.37 | 42.48 | 44.98 | 4.28 | 36.02 |
| Malfunction sample (weighted) / all makers | table edge (-90 / +90 %) | 327 | 125,755 | -90.00 | 90.00 | 67.87 | 37.00 | 51.52 | 0.89 | 71.60 | 20.96 | -42.30 | 55.81 | 52.31 | 16.74 | 15.80 | 26.37 | 6.09 | 0.26 | 36.28 | -63.64 | 100.00 | 99.03 | 68.80 | 25.51 | 0.48 | 22.39 |
| Malfunction sample (weighted) / Abbott | table edge (-90 / +90 %) | 255 | 107,133 | -90.00 | 90.00 | 71.12 | 37.99 | 52.32 | 0.87 | 72.49 | 18.41 | -44.84 | 58.28 | 54.77 | 17.61 | 16.67 | 26.65 | 6.31 | 0.25 | 37.25 | -65.00 | 100.00 | 99.96 | 70.93 | 26.74 | 0.56 | 24.27 |
| Serious / Libre 3 received on/after 2025-11-24 | table edge (-90 / +90 %) | 1,044 | 1,044 | -90.00 | 90.00 | 63.41 | 32.86 | 53.07 | 0.63 | 64.69 | 20.05 | -43.20 | 51.95 | 48.45 | 17.05 | 16.10 | 31.28 | 7.16 | 0.31 | 32.37 | -58.76 | 98.75 | 97.70 | 60.54 | 30.56 | 3.74 | 25.29 |
| Serious / Libre 3 received before 2025-11-24 | table edge (-90 / +90 %) | 1,355 | 1,355 | -90.00 | 90.00 | 67.31 | 35.49 | 51.36 | 0.47 | 68.10 | 15.23 | -48.03 | 59.66 | 56.16 | 20.91 | 19.96 | 28.21 | 6.32 | 0.29 | 35.04 | -70.30 | 98.67 | 97.49 | 65.83 | 26.79 | 11.37 | 21.77 |
| Serious / Injury | table edge (-90 / +90 %) | 18,093 | 18,093 | -90.00 | 90.00 | 50.74 | 23.44 | 59.54 | 0.47 | 47.08 | 21.56 | -41.70 | 36.71 | 33.21 | 12.13 | 11.18 | 46.84 | 10.57 | 0.48 | 23.09 | 0.00 | 97.76 | 96.36 | 42.43 | 45.02 | 4.25 | 36.05 |
| Serious / Death | table edge (-90 / +90 %) | 25 | 25 | -90.00 | 90.00 | 56.00 | 44.87 | 47.23 | 0.39 | 83.86 | 7.48 | -55.78 | 78.63 | 75.13 | 28.45 | 27.50 | 16.00 | 3.81 | 0.15 | 44.35 | -86.25 | 100.00 | 100.00 | 84.00 | 16.00 | 24.00 | 16.00 |
| Serious / Abbott | clipped at -40 % (floor) | 7,556 | 7,556 | -40.00 | 40.00 | 55.76 | 18.03 | 49.55 | 1.01 | 49.84 | 54.94 | -8.32 | 14.82 | 11.32 | 3.46 | 2.51 | 34.02 | 4.95 | 0.48 | 17.85 | -46.67 | 98.44 | 97.29 | 52.22 | 39.02 | 52.22 | 39.02 |
| Serious / Dexcom | clipped at -40 % (floor) | 9,518 | 9,518 | -40.00 | 40.00 | 47.73 | 13.01 | 52.69 | 0.74 | 36.78 | 50.30 | -12.96 | 10.93 | 7.43 | 2.56 | 1.62 | 44.89 | 6.52 | 0.63 | 12.90 | 42.11 | 97.57 | 96.21 | 35.18 | 50.22 | 35.18 | 50.22 |
| Serious / Medtronic (undercounted; weakest validation) | clipped at -40 % (floor) | 500 | 500 | -40.00 | 40.00 | 34.00 | 14.85 | 46.63 | 0.85 | 42.50 | 54.59 | -8.67 | 12.60 | 9.10 | 2.95 | 2.01 | 34.59 | 5.02 | 0.49 | 14.74 | -14.51 | 92.20 | 90.00 | 40.00 | 39.20 | 40.00 | 39.20 |
| Serious / all makers | clipped at -40 % (floor) | 18,118 | 18,118 | -40.00 | 40.00 | 50.75 | 15.21 | 51.08 | 0.86 | 42.58 | 52.46 | -10.79 | 12.65 | 9.14 | 2.96 | 2.01 | 39.83 | 5.79 | 0.56 | 15.07 | -0.21 | 97.76 | 96.37 | 42.48 | 44.98 | 42.48 | 44.98 |
| Malfunction sample (weighted) / all makers | clipped at -40 % (floor) | 327 | 125,755 | -40.00 | 40.00 | 67.87 | 23.37 | 46.22 | 1.30 | 64.10 | 60.12 | -3.14 | 18.96 | 15.46 | 4.41 | 3.47 | 22.20 | 3.25 | 0.31 | 23.12 | -63.64 | 100.00 | 99.03 | 68.80 | 25.51 | 68.80 | 25.51 |
| Malfunction sample (weighted) / Abbott | clipped at -40 % (floor) | 255 | 107,133 | -40.00 | 40.00 | 71.12 | 23.71 | 46.73 | 1.31 | 64.70 | 60.03 | -3.23 | 19.18 | 15.68 | 4.46 | 3.52 | 22.23 | 3.29 | 0.31 | 23.45 | -65.00 | 100.00 | 99.96 | 70.93 | 26.74 | 70.93 | 26.74 |
| Serious / Libre 3 received on/after 2025-11-24 | clipped at -40 % (floor) | 1,044 | 1,044 | -40.00 | 40.00 | 63.41 | 21.03 | 47.04 | 1.17 | 58.21 | 58.28 | -4.98 | 17.20 | 13.70 | 4.01 | 3.06 | 26.47 | 3.87 | 0.37 | 20.83 | -58.76 | 98.75 | 97.70 | 60.54 | 30.56 | 60.54 | 30.56 |
| Serious / Libre 3 received before 2025-11-24 | clipped at -40 % (floor) | 1,355 | 1,355 | -40.00 | 40.00 | 67.31 | 22.20 | 46.01 | 1.23 | 60.92 | 59.27 | -3.98 | 18.08 | 14.58 | 4.21 | 3.27 | 24.03 | 3.46 | 0.34 | 21.96 | -70.30 | 98.67 | 97.49 | 65.83 | 26.79 | 65.83 | 26.79 |
| Serious / Injury | clipped at -40 % (floor) | 18,093 | 18,093 | -40.00 | 40.00 | 50.74 | 15.19 | 51.09 | 0.86 | 42.53 | 52.45 | -10.81 | 12.63 | 9.13 | 2.96 | 2.01 | 39.87 | 5.79 | 0.56 | 15.05 | 0.00 | 97.76 | 96.36 | 42.43 | 45.02 | 42.43 | 45.02 |
| Serious / Death | clipped at -40 % (floor) | 25 | 25 | -40.00 | 40.00 | 56.00 | 27.42 | 43.53 | 1.51 | 74.49 | 63.85 | 0.59 | 22.11 | 18.61 | 5.14 | 4.19 | 13.30 | 1.97 | 0.19 | 27.11 | -86.25 | 100.00 | 100.00 | 84.00 | 16.00 | 84.00 | 16.00 |
