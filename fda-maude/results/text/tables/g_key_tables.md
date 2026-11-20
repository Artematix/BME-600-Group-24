# Brand comparison: markdown copies of the g_*.csv tables in this folder

Made by `scripts/brand_comparison.py`. Memo: `../BRAND_COMPARISON.md`. Medtronic rows carry a caution (undercounted; weakest validation). MAUDE counts reflect reporting behaviour, not failure rates.

## g. Comparison set counts
| tier | brand | reports_in_run_set | weighted_reports | wrong_reading_by_text | wrong_reading_by_code | wrong_reading_by_both | wrong_reading_either | wrong_reading_either_weighted | pct_of_reports_wrong_reading | pct_text_only | pct_code_only | pairs_both_values | pairs_in_wrong_reading_set | pct_of_wrong_reading_reports_with_pair |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| serious | Abbott | 74,657 | 74,657 | 20,694 | 22,506 | 20,265 | 22,935 | 22,935 | 30.7 | 1.9 | 9.8 | 7,556 | 7,470 | 32.6 |
| serious | Dexcom | 32,045 | 32,045 | 11,845 | 14,109 | 11,043 | 14,911 | 14,911 | 46.5 | 5.4 | 20.6 | 9,518 | 9,189 | 61.6 |
| serious | Medtronic (caution) | 8,660 | 8,660 | 470 | 655 | 368 | 757 | 757 | 8.7 | 13.5 | 37.9 | 500 | 379 | 50.1 |
| serious | Senseonics (Eversense) | 2,878 | 2,878 | 634 | 979 | 599 | 1,014 | 1,014 | 35.2 | 3.5 | 37.5 | 539 | 532 | 52.5 |
| serious | Other makers | 222 | 222 | 11 | 48 | 9 | 50 | 50 | 22.5 | 4.0 | 78.0 | 5 | 3 | 6.0 |
| serious | All | 118,462 | 118,462 | 33,654 | 38,297 | 32,284 | 39,667 | 39,667 | 33.5 | 3.5 | 15.2 | 18,118 | 17,573 | 44.3 |
| sample (weighted) | Abbott | 843 | 386,438 | 478 | 797 | 478 | 797 | 376,494 | 97.4 | 0.0 | 40.4 | 255 | 255 | 32.0 |
| sample (weighted) | Dexcom | 4,574 | 2,405,435 | 40 | 623 | 29 | 634 | 349,517 | 14.5 | 1.6 | 94.3 | 32 | 31 | 4.9 |
| sample (weighted) | Medtronic (caution) | 407 | 120,676 | 26 | 36 | 22 | 40 | 5,343 | 4.4 | 10.9 | 35.3 | 24 | 24 | 60.0 |
| sample (weighted) | Senseonics (Eversense) | 290 | 4,111 | 18 | 86 | 17 | 87 | 2,310 | 56.2 | 2.7 | 87.5 | 15 | 15 | 17.2 |
| sample (weighted) | Other makers | 23 | 5,842 | 1 | 0 | 0 | 1 | 1 | 0.0 | 100.0 | 0.0 | 1 | 1 | 100.0 |
| sample (weighted) | All | 6,137 | 2,922,501 | 563 | 1,542 | 546 | 1,559 | 733,665 | 25.1 | 0.8 | 66.2 | 327 | 326 | 20.9 |

## g. Error sizes by brand
| tier | brand | pairs | n_pairs | weighted_n | median_mgdl | q1_mgdl | q3_mgdl | median_pct | q1_pct | q3_pct | p10_pct | p90_pct | pct_low | pct_high | median_sensor_mgdl | median_meter_mgdl | pct_meter_under_70 | pct_meter_over_250 | pct_zone_DE_computed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| serious | Abbott | all pairs | 7,470 | 7,470 | -67.0 | -280.0 | 96.0 | -47.1 | -80.0 | 146.3 | -88.8 | 413.1 | 57.8 | 41.8 | 91.0 | 167.0 | 28.1 | 37.0 | 43.6 |
| serious | Abbott | sensor below meter | 4,315 | 4,315 | -240.0 | -407.0 | -112.0 | -76.8 | -86.4 | -59.9 | -90.4 | -42.5 | 100.0 | 0.0 | 60.0 | 318.0 | 0.8 | 62.2 | 42.7 |
| serious | Abbott | sensor above meter | 3,126 | 3,126 | 120.0 | 60.0 | 225.0 | 191.2 | 100.0 | 400.0 | 56.2 | 769.4 | 0.0 | 100.0 | 202.0 | 52.0 | 65.5 | 2.4 | 45.3 |
| serious | Dexcom | all pairs | 9,189 | 9,189 | 29.0 | -217.0 | 77.2 | 44.1 | -64.0 | 172.3 | -86.0 | 382.8 | 43.8 | 55.4 | 110.0 | 95.0 | 45.7 | 33.8 | 35.4 |
| serious | Dexcom | sensor below meter | 4,029 | 4,029 | -266.0 | -430.0 | -119.0 | -69.2 | -85.0 | -48.2 | -91.0 | -30.4 | 100.0 | 0.0 | 86.0 | 420.0 | 1.3 | 74.8 | 35.9 |
| serious | Dexcom | sensor above meter | 5,088 | 5,088 | 70.0 | 41.0 | 128.0 | 151.7 | 83.3 | 300.0 | 44.8 | 595.4 | 0.0 | 100.0 | 122.0 | 40.0 | 80.8 | 1.5 | 35.5 |
| serious | Medtronic (caution) | all pairs | 379 | 379 | 0.0 | -220.0 | 73.0 | 0.0 | -63.1 | 165.9 | -83.7 | 300.0 | 48.8 | 49.1 | 110.0 | 124.0 | 42.5 | 35.9 | 34.0 |
| serious | Medtronic (caution) | sensor below meter | 185 | 185 | -220.0 | -360.0 | -100.0 | -64.0 | -80.2 | -43.5 | -90.0 | -29.5 | 100.0 | 0.0 | 91.0 | 400.0 | 1.1 | 69.7 | 30.8 |
| serious | Medtronic (caution) | sensor above meter | 186 | 186 | 74.0 | 54.0 | 120.0 | 170.3 | 100.0 | 270.0 | 50.1 | 379.6 | 0.0 | 100.0 | 120.5 | 47.0 | 82.8 | 2.2 | 38.7 |
| serious | Senseonics (Eversense) | all pairs | 532 | 532 | -21.5 | -105.0 | 60.0 | -19.0 | -52.8 | 116.8 | -69.7 | 226.9 | 54.1 | 45.3 | 104.5 | 98.5 | 39.8 | 20.5 | 16.0 |
| serious | Senseonics (Eversense) | sensor below meter | 288 | 288 | -97.0 | -170.5 | -46.0 | -51.3 | -65.5 | -37.1 | -76.7 | -21.4 | 100.0 | 0.0 | 78.0 | 207.5 | 2.8 | 36.8 | 8.0 |
| serious | Senseonics (Eversense) | sensor above meter | 241 | 241 | 63.0 | 42.0 | 100.8 | 126.0 | 75.0 | 210.9 | 41.5 | 363.7 | 0.0 | 100.0 | 113.0 | 50.0 | 84.2 | 0.8 | 25.7 |
| serious | Other makers | all pairs | 3 | 3 | 179.0 | 110.0 | 272.8 | 70.7 | 68.0 | 153.4 | 67.0 | 181.0 | 0.0 | 100.0 | 446.0 | 168.0 | 0.0 | 33.3 | 0.0 |
| serious | Other makers | sensor above meter | 3 | 3 | 179.0 | 110.0 | 272.8 | 70.7 | 68.0 | 153.4 | 67.0 | 181.0 | 0.0 | 100.0 | 446.0 | 168.0 | 0.0 | 33.3 | 0.0 |
| serious | All | all pairs | 17,573 | 17,573 | -5.0 | -244.0 | 81.0 | -5.1 | -72.9 | 160.0 | -87.5 | 389.3 | 50.2 | 49.2 | 102.0 | 130.0 | 38.0 | 34.8 | 38.3 |
| serious | All | sensor below meter | 8,817 | 8,817 | -243.0 | -410.0 | -110.0 | -72.7 | -85.7 | -52.8 | -90.5 | -34.3 | 100.0 | 0.0 | 68.0 | 378.0 | 1.1 | 67.3 | 38.2 |
| serious | All | sensor above meter | 8,644 | 8,644 | 83.0 | 47.0 | 164.0 | 163.6 | 88.9 | 328.6 | 48.6 | 650.0 | 0.0 | 100.0 | 144.0 | 45.0 | 75.4 | 1.9 | 38.8 |
| sample (weighted) | Abbott | all pairs | 255 | 107,133 | -110.0 | -151.2 | 56.0 | -65.0 | -72.1 | 83.8 | -80.3 | 160.1 | 73.3 | 26.7 | 64.7 | 177.9 | 6.3 | 16.0 | 12.1 |
| sample (weighted) | Abbott | sensor below meter | 179 | 78,486 | -130.0 | -169.5 | -105.1 | -68.3 | -75.7 | -63.1 | -82.0 | -51.8 | 100.0 | 0.0 | 57.0 | 197.8 | 0.0 | 21.8 | 10.9 |
| sample (weighted) | Abbott | sensor above meter | 76 | 28,647 | 182.8 | 129.0 | 225.3 | 138.1 | 116.4 | 191.6 | 98.7 | 294.2 | 0.0 | 100.0 | 296.6 | 113.5 | 23.6 | 0.0 | 15.3 |
| sample (weighted) | Dexcom | all pairs | 31 | 15,472 | -61.0 | -100.9 | 37.7 | -44.9 | -57.6 | 29.1 | -72.8 | 97.5 | 68.6 | 31.4 | 92.2 | 150.3 | 4.3 | 15.2 | 8.1 |
| sample (weighted) | Dexcom | sensor below meter | 21 | 10,609 | -81.9 | -102.0 | -61.0 | -55.0 | -68.6 | -44.8 | -74.8 | -27.9 | 100.0 | 0.0 | 67.7 | 158.0 | 0.0 | 22.1 | 5.5 |
| sample (weighted) | Dexcom | sensor above meter | 10 | 4,863 | 95.5 | 43.0 | 126.3 | 70.8 | 32.1 | 98.9 | 24.6 | 298.3 | 0.0 | 100.0 | 211.0 | 139.7 | 13.8 | 0.0 | 13.8 |
| sample (weighted) | Medtronic (caution) | all pairs | 24 | 2,907 | -144.5 | -185.4 | -100.9 | -65.6 | -72.9 | -49.7 | -76.0 | 47.3 | 91.6 | 8.4 | 68.1 | 216.7 | 3.7 | 42.8 | 0.0 |
| sample (weighted) | Medtronic (caution) | sensor below meter | 21 | 2,664 | -157.0 | -186.9 | -113.4 | -66.2 | -74.3 | -56.2 | -76.4 | -35.4 | 100.0 | 0.0 | 64.4 | 224.7 | 0.0 | 46.7 | 0.0 |
| sample (weighted) | Medtronic (caution) | sensor above meter | 3 | 244 | 73.7 | 60.4 | 85.7 | 106.8 | 99.1 | 114.9 | 98.3 | 121.3 | 0.0 | 100.0 | 142.2 | 72.4 | 44.7 | 0.0 | 0.0 |
| sample (weighted) | Senseonics (Eversense) | all pairs | 15 | 225 | -61.7 | -70.4 | 53.9 | -30.6 | -38.5 | 47.3 | -62.1 | 155.2 | 64.2 | 35.8 | 143.4 | 203.7 | 7.4 | 14.5 | 0.0 |
| sample (weighted) | Senseonics (Eversense) | sensor below meter | 7 | 145 | -69.6 | -84.7 | -63.8 | -37.7 | -53.4 | -31.3 | -66.7 | -30.4 | 100.0 | 0.0 | 121.3 | 221.4 | 0.0 | 22.6 | 0.0 |
| sample (weighted) | Senseonics (Eversense) | sensor above meter | 8 | 81 | 73.7 | 52.6 | 180.6 | 116.0 | 40.7 | 163.4 | 26.3 | 205.8 | 0.0 | 100.0 | 262.4 | 154.9 | 20.7 | 0.0 | 0.0 |
| sample (weighted) | Other makers | all pairs | 1 | 1 | -351.0 | -351.0 | -351.0 | -48.7 | -48.7 | -48.7 | -48.7 | -48.7 | 100.0 | 0.0 | 370.0 | 721.0 | 0.0 | 100.0 | 0.0 |
| sample (weighted) | Other makers | sensor below meter | 1 | 1 | -351.0 | -351.0 | -351.0 | -48.7 | -48.7 | -48.7 | -48.7 | -48.7 | 100.0 | 0.0 | 370.0 | 721.0 | 0.0 | 100.0 | 0.0 |
| sample (weighted) | All | all pairs | 326 | 125,738 | -105.9 | -149.2 | 41.8 | -63.6 | -71.1 | 59.0 | -79.6 | 151.4 | 73.1 | 26.9 | 66.0 | 174.7 | 6.0 | 16.5 | 11.3 |
| sample (weighted) | All | sensor below meter | 229 | 91,903 | -126.8 | -167.9 | -102.0 | -67.4 | -74.4 | -60.9 | -81.4 | -46.0 | 100.0 | 0.0 | 58.0 | 195.4 | 0.0 | 22.6 | 10.0 |
| sample (weighted) | All | sensor above meter | 97 | 33,835 | 151.7 | 110.6 | 220.1 | 132.7 | 102.7 | 183.9 | 69.0 | 296.4 | 0.0 | 100.0 | 285.7 | 116.0 | 22.3 | 0.0 | 14.9 |

## g. Error percentiles by brand (serious)
| brand | measure | n | p1 | p5 | p10 | p25 | p50 | p75 | p90 | p95 | p99 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Abbott | error, % of meter | 7,470 | -94.3 | -90.8 | -88.8 | -80.0 | -47.1 | 146.3 | 412.9 | 694.0 | 1308.8 |
| Abbott | error, mg/dL | 7,470 | -945.3 | -550.0 | -448.0 | -280.0 | -67.0 | 96.0 | 230.0 | 313.0 | 447.0 |
| Abbott | absolute error, % of meter | 7,470 | 11.3 | 30.8 | 44.4 | 66.7 | 85.5 | 146.3 | 412.9 | 694.0 | 1308.8 |
| Dexcom | error, % of meter | 9,189 | -93.9 | -90.4 | -86.0 | -64.0 | 44.1 | 172.2 | 382.8 | 627.1 | 1201.2 |
| Dexcom | error, mg/dL | 9,189 | -865.0 | -546.6 | -445.0 | -217.0 | 29.0 | 77.0 | 160.0 | 247.0 | 360.0 |
| Dexcom | absolute error, % of meter | 9,189 | 3.8 | 24.7 | 34.6 | 58.5 | 86.7 | 172.2 | 382.8 | 627.1 | 1201.2 |
| Medtronic (caution) | error, % of meter | 379 | -91.7 | -89.4 | -83.7 | -63.1 | 0.0 | 164.0 | 300.0 | 379.4 | 776.3 |
| Medtronic (caution) | error, mg/dL | 379 | -613.2 | -450.2 | -382.2 | -220.0 | 0.0 | 73.0 | 151.0 | 200.5 | 354.0 |
| Medtronic (caution) | absolute error, % of meter | 379 | 0.0 | 19.7 | 30.0 | 53.4 | 83.3 | 164.0 | 300.0 | 379.4 | 776.3 |
| Senseonics (Eversense) | error, % of meter | 532 | -85.8 | -77.1 | -69.7 | -52.7 | -19.0 | 116.7 | 226.6 | 342.0 | 679.7 |
| Senseonics (Eversense) | error, mg/dL | 532 | -480.5 | -311.9 | -228.6 | -104.5 | -21.5 | 60.0 | 110.0 | 160.4 | 267.2 |
| Senseonics (Eversense) | absolute error, % of meter | 532 | 1.6 | 17.0 | 25.2 | 43.2 | 65.5 | 116.7 | 226.6 | 342.0 | 679.7 |
| Other makers | error, % of meter | 3 | 67.1 | 67.4 | 67.8 | 68.9 | 70.7 | 125.8 | 158.9 | 169.9 | 178.7 |
| Other makers | error, mg/dL | 3 | 88.8 | 96.2 | 105.4 | 133.0 | 179.0 | 241.5 | 279.0 | 291.5 | 301.5 |
| Other makers | absolute error, % of meter | 3 | 67.1 | 67.4 | 67.8 | 68.9 | 70.7 | 125.8 | 158.9 | 169.9 | 178.7 |
| All | error, % of meter | 17,573 | -94.0 | -90.5 | -87.5 | -72.9 | -5.1 | 160.0 | 389.1 | 647.7 | 1233.3 |
| All | error, mg/dL | 17,573 | -900.6 | -543.0 | -444.0 | -244.0 | -5.0 | 81.0 | 196.0 | 270.0 | 397.3 |
| All | absolute error, % of meter | 17,573 | 5.9 | 25.7 | 38.0 | 61.1 | 85.7 | 160.0 | 389.1 | 647.7 | 1233.3 |

## g. Kruskal-Wallis across brands (serious)
| pairs | measure | median_Abbott | n_Abbott | median_Dexcom | n_Dexcom | median_Medtronic | n_Medtronic | median_Senseonics | n_Senseonics | k_groups | n | kruskal_H | kruskal_p | epsilon_squared | p_text |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all pairs | error, % of meter | -47.115 | 7,470 | 44.068 | 9,189 | 0.000 | 379 | -19.029 | 532 | 4 | 17,570 | 279.974 | 0.000 | 0.016 | < 0.001 |
| all pairs | error, mg/dL | -67.000 | 7,470 | 29.000 | 9,189 | 0.000 | 379 | -21.500 | 532 | 4 | 17,570 | 42.273 | 0.000 | 0.002 | < 0.001 |
| all pairs | absolute error, % of meter | 85.525 | 7,470 | 86.667 | 9,189 | 83.333 | 379 | 65.513 | 532 | 4 | 17,570 | 103.255 | 0.000 | 0.006 | < 0.001 |
| all pairs | meter value, mg/dL | 167.000 | 7,470 | 95.000 | 9,189 | 124.000 | 379 | 98.500 | 532 | 4 | 17,570 | 256.286 | 0.000 | 0.014 | < 0.001 |
| all pairs | sensor value, mg/dL | 91.000 | 7,470 | 110.000 | 9,189 | 110.000 | 379 | 104.500 | 532 | 4 | 17,570 | 110.617 | 0.000 | 0.006 | < 0.001 |
| sensor below meter | error, % of meter | -76.768 | 4,315 | -69.182 | 4,029 | -64.018 | 185 | -51.262 | 288 | 4 | 8,817 | 338.996 | 0.000 | 0.038 | < 0.001 |
| sensor below meter | error, mg/dL | -240.000 | 4,315 | -266.000 | 4,029 | -220.000 | 185 | -97.000 | 288 | 4 | 8,817 | 217.111 | 0.000 | 0.024 | < 0.001 |
| sensor below meter | absolute error, % of meter | 76.768 | 4,315 | 69.182 | 4,029 | 64.018 | 185 | 51.262 | 288 | 4 | 8,817 | 338.996 | 0.000 | 0.038 | < 0.001 |
| sensor below meter | meter value, mg/dL | 318.000 | 4,315 | 420.000 | 4,029 | 400.000 | 185 | 207.500 | 288 | 4 | 8,817 | 376.948 | 0.000 | 0.042 | < 0.001 |
| sensor below meter | sensor value, mg/dL | 60.000 | 4,315 | 86.000 | 4,029 | 91.000 | 185 | 78.000 | 288 | 4 | 8,817 | 411.035 | 0.000 | 0.046 | < 0.001 |
| sensor above meter | error, % of meter | 191.245 | 3,126 | 151.712 | 5,088 | 170.270 | 186 | 126.000 | 241 | 4 | 8,641 | 111.767 | 0.000 | 0.013 | < 0.001 |
| sensor above meter | error, mg/dL | 120.000 | 3,126 | 70.000 | 5,088 | 74.000 | 186 | 63.000 | 241 | 4 | 8,641 | 578.725 | 0.000 | 0.067 | < 0.001 |
| sensor above meter | absolute error, % of meter | 191.245 | 3,126 | 151.712 | 5,088 | 170.270 | 186 | 126.000 | 241 | 4 | 8,641 | 111.767 | 0.000 | 0.013 | < 0.001 |
| sensor above meter | meter value, mg/dL | 52.000 | 3,126 | 40.000 | 5,088 | 47.000 | 186 | 50.000 | 241 | 4 | 8,641 | 322.528 | 0.000 | 0.037 | < 0.001 |
| sensor above meter | sensor value, mg/dL | 202.000 | 3,126 | 122.000 | 5,088 | 120.500 | 186 | 113.000 | 241 | 4 | 8,641 | 711.659 | 0.000 | 0.082 | < 0.001 |

## g. Pairwise brand tests on sizes (serious)
| pairs | measure | brand_a | brand_b | n_a | n_b | median_a | median_b | median_diff_a_minus_b | median_diff_ci_low | median_diff_ci_high | cliffs_delta | cliffs_delta_ci_low | cliffs_delta_ci_high | effect_size_word | p_text |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all pairs | error, % of meter | Abbott | Dexcom | 7,470 | 9,189 | -47.12 | 44.07 | -91.18 | -97.37 | -85.96 | -0.15 | -0.16 | -0.13 | negligible | < 0.001 |
| all pairs | error, % of meter | Abbott | Medtronic (caution) | 7,470 | 379 | -47.12 | 0.00 | -47.12 | -94.09 | -22.34 | -0.13 | -0.18 | -0.08 | negligible | < 0.001 |
| all pairs | error, % of meter | Abbott | Senseonics (Eversense) | 7,470 | 532 | -47.12 | -19.03 | -28.09 | -47.12 | -19.28 | -0.16 | -0.20 | -0.13 | small | < 0.001 |
| all pairs | error, % of meter | Dexcom | Medtronic (caution) | 9,189 | 379 | 44.07 | 0.00 | 44.07 | -3.39 | 69.42 | 0.03 | -0.03 | 0.09 | negligible | 0.274 |
| all pairs | error, % of meter | Dexcom | Senseonics (Eversense) | 9,189 | 532 | 44.07 | -19.03 | 63.10 | 44.84 | 73.43 | 0.05 | 0.01 | 0.08 | negligible | 0.064 |
| all pairs | error, % of meter | Medtronic (caution) | Senseonics (Eversense) | 379 | 532 | 0.00 | -19.03 | 19.03 | -12.12 | 64.28 | 0.01 | -0.07 | 0.09 | negligible | 0.842 |
| all pairs | error, mg/dL | Abbott | Dexcom | 7,470 | 9,189 | -67.00 | 29.00 | -96.00 | -104.00 | -88.49 | -0.05 | -0.07 | -0.04 | negligible | < 0.001 |
| all pairs | error, mg/dL | Abbott | Medtronic (caution) | 7,470 | 379 | -67.00 | 0.00 | -67.00 | -99.00 | -25.00 | -0.05 | -0.10 | 0.01 | negligible | 0.130 |
| all pairs | error, mg/dL | Abbott | Senseonics (Eversense) | 7,470 | 532 | -67.00 | -21.50 | -45.50 | -67.51 | -28.00 | -0.11 | -0.14 | -0.07 | negligible | < 0.001 |
| all pairs | error, mg/dL | Dexcom | Medtronic (caution) | 9,189 | 379 | 29.00 | 0.00 | 29.00 | -2.00 | 72.00 | 0.01 | -0.05 | 0.07 | negligible | 0.654 |
| all pairs | error, mg/dL | Dexcom | Senseonics (Eversense) | 9,189 | 532 | 29.00 | -21.50 | 50.50 | 30.00 | 65.01 | 0.01 | -0.03 | 0.05 | negligible | 0.826 |
| all pairs | error, mg/dL | Medtronic (caution) | Senseonics (Eversense) | 379 | 532 | 0.00 | -21.50 | 21.50 | -26.00 | 60.00 | -0.03 | -0.11 | 0.05 | negligible | 0.477 |
| all pairs | absolute error, % of meter | Abbott | Dexcom | 7,470 | 9,189 | 85.52 | 86.67 | -1.14 | -2.19 | -0.20 | 0.01 | -0.00 | 0.03 | negligible | 0.150 |
| all pairs | absolute error, % of meter | Abbott | Medtronic (caution) | 7,470 | 379 | 85.52 | 83.33 | 2.19 | -2.69 | 6.52 | 0.07 | 0.01 | 0.13 | negligible | 0.021 |
| all pairs | absolute error, % of meter | Abbott | Senseonics (Eversense) | 7,470 | 532 | 85.52 | 65.51 | 20.01 | 15.41 | 24.82 | 0.27 | 0.22 | 0.33 | small | < 0.001 |
| all pairs | absolute error, % of meter | Dexcom | Medtronic (caution) | 9,189 | 379 | 86.67 | 83.33 | 3.33 | -2.06 | 7.60 | 0.05 | -0.00 | 0.12 | negligible | 0.072 |
| all pairs | absolute error, % of meter | Dexcom | Senseonics (Eversense) | 9,189 | 532 | 86.67 | 65.51 | 21.15 | 16.31 | 25.97 | 0.23 | 0.18 | 0.28 | small | < 0.001 |
| all pairs | absolute error, % of meter | Medtronic (caution) | Senseonics (Eversense) | 379 | 532 | 83.33 | 65.51 | 17.82 | 10.96 | 23.97 | 0.18 | 0.11 | 0.25 | small | < 0.001 |
| all pairs | meter value, mg/dL | Abbott | Dexcom | 7,470 | 9,189 | 167.00 | 95.00 | 72.00 | 63.00 | 81.51 | 0.14 | 0.12 | 0.16 | negligible | < 0.001 |
| all pairs | meter value, mg/dL | Abbott | Medtronic (caution) | 7,470 | 379 | 167.00 | 124.00 | 43.00 | 6.98 | 79.00 | 0.09 | 0.03 | 0.15 | negligible | 0.003 |
| all pairs | meter value, mg/dL | Abbott | Senseonics (Eversense) | 7,470 | 532 | 167.00 | 98.50 | 68.50 | 57.49 | 82.51 | 0.19 | 0.15 | 0.23 | small | < 0.001 |
| all pairs | meter value, mg/dL | Dexcom | Medtronic (caution) | 9,189 | 379 | 95.00 | 124.00 | -29.00 | -62.00 | 8.05 | -0.06 | -0.11 | -0.00 | negligible | 0.061 |
| all pairs | meter value, mg/dL | Dexcom | Senseonics (Eversense) | 9,189 | 532 | 95.00 | 98.50 | -3.50 | -16.00 | 13.00 | -0.01 | -0.05 | 0.03 | negligible | 0.713 |
| all pairs | meter value, mg/dL | Medtronic (caution) | Senseonics (Eversense) | 379 | 532 | 124.00 | 98.50 | 25.50 | -12.00 | 61.00 | 0.06 | -0.02 | 0.14 | negligible | 0.107 |
| sensor below meter | error, % of meter | Abbott | Dexcom | 4,315 | 4,029 | -76.77 | -69.18 | -7.59 | -8.98 | -6.15 | -0.15 | -0.17 | -0.12 | negligible | < 0.001 |
| sensor below meter | error, % of meter | Abbott | Medtronic (caution) | 4,315 | 185 | -76.77 | -64.02 | -12.75 | -16.00 | -7.25 | -0.25 | -0.34 | -0.17 | small | < 0.001 |
| sensor below meter | error, % of meter | Abbott | Senseonics (Eversense) | 4,315 | 288 | -76.77 | -51.26 | -25.51 | -29.19 | -22.59 | -0.56 | -0.61 | -0.52 | large | < 0.001 |
| sensor below meter | error, % of meter | Dexcom | Medtronic (caution) | 4,029 | 185 | -69.18 | -64.02 | -5.16 | -7.75 | 0.66 | -0.09 | -0.17 | -0.01 | negligible | 0.030 |
| sensor below meter | error, % of meter | Dexcom | Senseonics (Eversense) | 4,029 | 288 | -69.18 | -51.26 | -17.92 | -21.73 | -14.75 | -0.38 | -0.43 | -0.33 | medium | < 0.001 |
| sensor below meter | error, % of meter | Medtronic (caution) | Senseonics (Eversense) | 185 | 288 | -64.02 | -51.26 | -12.76 | -18.96 | -8.86 | -0.30 | -0.39 | -0.19 | small | < 0.001 |
| sensor below meter | error, mg/dL | Abbott | Dexcom | 4,315 | 4,029 | -240.00 | -266.00 | 26.00 | 13.98 | 41.00 | 0.05 | 0.03 | 0.07 | negligible | < 0.001 |
| sensor below meter | error, mg/dL | Abbott | Medtronic (caution) | 4,315 | 185 | -240.00 | -220.00 | -20.00 | -62.00 | 30.00 | -0.07 | -0.15 | 0.01 | negligible | 0.114 |
| sensor below meter | error, mg/dL | Abbott | Senseonics (Eversense) | 4,315 | 288 | -240.00 | -97.00 | -143.00 | -160.00 | -126.00 | -0.47 | -0.53 | -0.42 | medium | < 0.001 |
| sensor below meter | error, mg/dL | Dexcom | Medtronic (caution) | 4,029 | 185 | -266.00 | -220.00 | -46.00 | -86.00 | 7.02 | -0.12 | -0.20 | -0.05 | negligible | 0.005 |
| sensor below meter | error, mg/dL | Dexcom | Senseonics (Eversense) | 4,029 | 288 | -266.00 | -97.00 | -169.00 | -187.00 | -150.49 | -0.50 | -0.55 | -0.45 | large | < 0.001 |
| sensor below meter | error, mg/dL | Medtronic (caution) | Senseonics (Eversense) | 185 | 288 | -220.00 | -97.00 | -123.00 | -179.00 | -81.00 | -0.42 | -0.51 | -0.32 | medium | < 0.001 |
| sensor above meter | error, % of meter | Abbott | Dexcom | 3,126 | 5,088 | 191.25 | 151.71 | 39.53 | 26.70 | 48.52 | 0.12 | 0.10 | 0.15 | negligible | < 0.001 |
| sensor above meter | error, % of meter | Abbott | Medtronic (caution) | 3,126 | 186 | 191.25 | 170.27 | 20.97 | -1.05 | 46.01 | 0.12 | 0.05 | 0.19 | negligible | 0.006 |
| sensor above meter | error, % of meter | Abbott | Senseonics (Eversense) | 3,126 | 241 | 191.25 | 126.00 | 65.25 | 45.38 | 78.48 | 0.27 | 0.20 | 0.33 | small | < 0.001 |
| sensor above meter | error, % of meter | Dexcom | Medtronic (caution) | 5,088 | 186 | 151.71 | 170.27 | -18.56 | -35.71 | 6.17 | -0.02 | -0.09 | 0.06 | negligible | 0.723 |
| sensor above meter | error, % of meter | Dexcom | Senseonics (Eversense) | 5,088 | 241 | 151.71 | 126.00 | 25.71 | 9.26 | 38.49 | 0.14 | 0.08 | 0.21 | negligible | < 0.001 |
| sensor above meter | error, % of meter | Medtronic (caution) | Senseonics (Eversense) | 186 | 241 | 170.27 | 126.00 | 44.27 | 16.14 | 64.79 | 0.18 | 0.07 | 0.28 | small | 0.001 |
| sensor above meter | error, mg/dL | Abbott | Dexcom | 3,126 | 5,088 | 120.00 | 70.00 | 50.00 | 46.00 | 57.01 | 0.31 | 0.28 | 0.33 | small | < 0.001 |
| sensor above meter | error, mg/dL | Abbott | Medtronic (caution) | 3,126 | 186 | 120.00 | 74.00 | 46.00 | 38.50 | 56.00 | 0.27 | 0.20 | 0.34 | small | < 0.001 |
| sensor above meter | error, mg/dL | Abbott | Senseonics (Eversense) | 3,126 | 241 | 120.00 | 63.00 | 57.00 | 51.00 | 64.01 | 0.40 | 0.34 | 0.46 | medium | < 0.001 |
| sensor above meter | error, mg/dL | Dexcom | Medtronic (caution) | 5,088 | 186 | 70.00 | 74.00 | -4.00 | -12.00 | 3.00 | -0.07 | -0.14 | 0.02 | negligible | 0.126 |
| sensor above meter | error, mg/dL | Dexcom | Senseonics (Eversense) | 5,088 | 241 | 70.00 | 63.00 | 7.00 | 1.00 | 10.00 | 0.09 | 0.02 | 0.16 | negligible | 0.022 |
| sensor above meter | error, mg/dL | Medtronic (caution) | Senseonics (Eversense) | 186 | 241 | 74.00 | 63.00 | 11.00 | 2.00 | 18.51 | 0.17 | 0.05 | 0.27 | small | 0.003 |

## g. Shares by brand (serious wrong-reading reports / pairs)
| variable | base | category | n_Abbott | pct_Abbott | n_Dexcom | pct_Dexcom | n_Medtronic | pct_Medtronic | n_Senseonics | pct_Senseonics |
|---|---|---|---|---|---|---|---|---|---|---|
| direction (from the two numbers) | pairs with a direction | low | 4,315 | 58.0 | 4,029 | 44.2 | 185 | 49.9 | 288 | 54.4 |
| direction (from the two numbers) | pairs with a direction | high | 3,126 | 42.0 | 5,088 | 55.8 | 186 | 50.1 | 241 | 45.6 |
| meter (true glucose) band, mg/dL | pairs | <54 | 1,629 | 21.8 | 3,647 | 39.7 | 143 | 37.7 | 143 | 26.9 |
| meter (true glucose) band, mg/dL | pairs | 54-69 | 471 | 6.3 | 555 | 6.0 | 18 | 4.7 | 69 | 13.0 |
| meter (true glucose) band, mg/dL | pairs | 70-180 | 1,846 | 24.7 | 1,397 | 15.2 | 61 | 16.1 | 146 | 27.4 |
| meter (true glucose) band, mg/dL | pairs | 181-250 | 759 | 10.2 | 485 | 5.3 | 21 | 5.5 | 65 | 12.2 |
| meter (true glucose) band, mg/dL | pairs | >250 | 2,765 | 37.0 | 3,105 | 33.8 | 136 | 35.9 | 109 | 20.5 |
| sensor reading band, mg/dL | pairs | <54 | 1,551 | 20.8 | 1,256 | 13.7 | 55 | 14.5 | 72 | 13.5 |
| sensor reading band, mg/dL | pairs | 54-69 | 1,260 | 16.9 | 945 | 10.3 | 21 | 5.5 | 77 | 14.5 |
| sensor reading band, mg/dL | pairs | 70-180 | 2,720 | 36.4 | 4,432 | 48.2 | 212 | 55.9 | 287 | 53.9 |
| sensor reading band, mg/dL | pairs | 181-250 | 621 | 8.3 | 1,063 | 11.6 | 30 | 7.9 | 52 | 9.8 |
| sensor reading band, mg/dL | pairs | >250 | 1,318 | 17.6 | 1,493 | 16.2 | 61 | 16.1 | 44 | 8.3 |
| Parkes zone computed from the pair | pairs | A | 279 | 3.7 | 569 | 6.2 | 30 | 7.9 | 53 | 10.0 |
| Parkes zone computed from the pair | pairs | B | 1,311 | 17.6 | 2,300 | 25.0 | 84 | 22.2 | 187 | 35.2 |
| Parkes zone computed from the pair | pairs | C | 2,624 | 35.1 | 3,065 | 33.4 | 136 | 35.9 | 207 | 38.9 |
| Parkes zone computed from the pair | pairs | D | 2,813 | 37.7 | 2,690 | 29.3 | 122 | 32.2 | 70 | 13.2 |
| Parkes zone computed from the pair | pairs | E | 443 | 5.9 | 565 | 6.1 | 7 | 1.8 | 15 | 2.8 |
| Parkes zone stated by the maker | reports with a stated zone | A | 1 | 0.0 | 369 | 4.4 | 0 | 0.0 | 0 |  |
| Parkes zone stated by the maker | reports with a stated zone | B | 8 | 0.2 | 1,955 | 23.5 | 0 | 0.0 | 0 |  |
| Parkes zone stated by the maker | reports with a stated zone | C | 1,946 | 46.6 | 2,456 | 29.5 | 1 | 50.0 | 0 |  |
| Parkes zone stated by the maker | reports with a stated zone | D | 1,996 | 47.8 | 2,974 | 35.7 | 1 | 50.0 | 0 |  |
| Parkes zone stated by the maker | reports with a stated zone | E | 224 | 5.4 | 571 | 6.9 | 0 | 0.0 | 0 |  |
| wear day of the failure | reports with a wear day | day 1 | 347 | 15.8 | 30 | 7.9 | 3 | 50.0 | 0 | 0.0 |
| wear day of the failure | reports with a wear day | days 2-3 | 455 | 20.7 | 94 | 24.9 | 0 | 0.0 | 8 | 40.0 |
| wear day of the failure | reports with a wear day | days 4-7 | 722 | 32.9 | 153 | 40.5 | 1 | 16.7 | 6 | 30.0 |
| wear day of the failure | reports with a wear day | days 8-10 | 363 | 16.5 | 99 | 26.2 | 0 | 0.0 | 3 | 15.0 |
| wear day of the failure | reports with a wear day | days 11-14 | 293 | 13.3 | 1 | 0.3 | 2 | 33.3 | 0 | 0.0 |
| wear day of the failure | reports with a wear day | day 15+ | 17 | 0.8 | 1 | 0.3 | 0 | 0.0 | 3 | 15.0 |
| fingerstick check mentioned | wrong-reading reports | yes | 12,250 | 53.4 | 12,010 | 80.5 | 650 | 85.9 | 681 | 67.2 |
| fingerstick check mentioned | wrong-reading reports | no | 1,618 | 7.1 | 1,084 | 7.3 | 34 | 4.5 | 96 | 9.5 |
| fingerstick check mentioned | wrong-reading reports | not_stated | 9,067 | 39.5 | 1,817 | 12.2 | 73 | 9.6 | 237 | 23.4 |
| user action (model) | wrong-reading reports | none | 1,089 | 4.7 | 860 | 5.8 | 186 | 24.6 | 285 | 28.1 |
| user action (model) | wrong-reading reports | ate_carbs | 6,992 | 30.5 | 5,184 | 34.8 | 178 | 23.5 | 320 | 31.6 |
| user action (model) | wrong-reading reports | took_insulin | 2,387 | 10.4 | 805 | 5.4 | 93 | 12.3 | 121 | 11.9 |
| user action (model) | wrong-reading reports | skipped_insulin | 30 | 0.1 | 22 | 0.1 | 13 | 1.7 | 0 | 0.0 |
| user action (model) | wrong-reading reports | sought_care | 10,515 | 45.8 | 7,092 | 47.6 | 201 | 26.6 | 126 | 12.4 |
| user action (model) | wrong-reading reports | other | 21 | 0.1 | 9 | 0.1 | 0 | 0.0 | 1 | 0.1 |
| user action (model) | wrong-reading reports | not_stated | 1,901 | 8.3 | 939 | 6.3 | 86 | 11.4 | 161 | 15.9 |
| outcome severity (model) | wrong-reading reports | none | 2,936 | 12.8 | 997 | 6.7 | 137 | 18.1 | 329 | 32.4 |
| outcome severity (model) | wrong-reading reports | symptoms_only | 2,020 | 8.8 | 371 | 2.5 | 7 | 0.9 | 35 | 3.5 |
| outcome severity (model) | wrong-reading reports | hypoglycemia | 2,584 | 11.3 | 1,869 | 12.5 | 252 | 33.3 | 472 | 46.5 |
| outcome severity (model) | wrong-reading reports | hyperglycemia_or_dka | 1 | 0.0 | 1 | 0.0 | 0 | 0.0 | 0 | 0.0 |
| outcome severity (model) | wrong-reading reports | hospital_or_er | 15,301 | 66.7 | 11,562 | 77.5 | 355 | 46.9 | 177 | 17.5 |
| outcome severity (model) | wrong-reading reports | death | 34 | 0.1 | 12 | 0.1 | 0 | 0.0 | 1 | 0.1 |
| outcome severity (model) | wrong-reading reports | not_stated | 59 | 0.3 | 99 | 0.7 | 6 | 0.8 | 0 | 0.0 |
| FDA event type | wrong-reading reports | Injury | 22,879 | 99.8 | 14,890 | 99.9 | 756 | 99.9 | 1,013 | 99.9 |
| FDA event type | wrong-reading reports | Death | 56 | 0.2 | 21 | 0.1 | 1 | 0.1 | 1 | 0.1 |
| FDA outcome code: Required Intervention | wrong-reading reports | yes | 18,474 | 80.5 | 560 | 3.8 | 118 | 15.6 | 2 | 0.2 |
| FDA outcome code: Hospitalization | wrong-reading reports | yes | 1,803 | 7.9 | 4,007 | 26.9 | 259 | 34.2 | 124 | 12.2 |
| FDA outcome code: Life Threatening | wrong-reading reports | yes | 178 | 0.8 | 687 | 4.6 | 17 | 2.2 | 7 | 0.7 |
| FDA outcome code: Death | wrong-reading reports | yes | 57 | 0.2 | 19 | 0.1 | 1 | 0.1 | 1 | 0.1 |
| FDA outcome code: Other | wrong-reading reports | yes | 2,636 | 11.5 | 13,598 | 91.2 | 218 | 28.8 | 446 | 44.0 |
| FDA outcome code: Disability | wrong-reading reports | yes | 89 | 0.4 | 116 | 0.8 | 4 | 0.5 | 0 | 0.0 |
| FDA outcome code: none stated | wrong-reading reports | yes | 1,634 | 7.1 | 446 | 3.0 | 191 | 25.2 | 441 | 43.5 |
| who reported (FDA occupation field) | wrong-reading reports | patient or family | 498 | 2.2 | 940 | 6.3 | 333 | 44.0 | 1 | 0.1 |
| who reported (FDA occupation field) | wrong-reading reports | health professional | 485 | 2.1 | 206 | 1.4 | 13 | 1.7 | 1 | 0.1 |
| who reported (FDA occupation field) | wrong-reading reports | other / code only | 21,934 | 95.6 | 13,535 | 90.8 | 410 | 54.2 | 964 | 95.1 |
| who reported (FDA occupation field) | wrong-reading reports | not filled | 18 | 0.1 | 230 | 1.5 | 1 | 0.1 | 48 | 4.7 |
| text form | wrong-reading reports | Abbott template | 3,098 | 13.5 | 0 | 0.0 | 0 | 0.0 | 0 | 0.0 |
| text form | wrong-reading reports | prose | 19,837 | 86.5 | 14,911 | 100.0 | 757 | 100.0 | 1,014 | 100.0 |

## g. Chi-square tests on the shares
| variable | base | n_Abbott | n_Dexcom | n_Medtronic | n_Senseonics | n | k_groups | chi2 | df | chi_square_p | cramers_v | effect_size_word | p_text |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| direction (from the two numbers) | pairs with a direction | 7,441 | 9,117 | 371 | 529 | 17,458 | 4 | 315.437 | 3 | 0.000 | 0.134 | small | < 0.001 |
| meter (true glucose) band, mg/dL | pairs | 7,470 | 9,189 | 379 | 532 | 17,570 | 4 | 865.016 | 12 | 0.000 | 0.128 | small | < 0.001 |
| sensor reading band, mg/dL | pairs | 7,470 | 9,189 | 379 | 532 | 17,570 | 4 | 515.807 | 12 | 0.000 | 0.099 | negligible | < 0.001 |
| Parkes zone computed from the pair | pairs | 7,470 | 9,189 | 379 | 532 | 17,570 | 4 | 401.538 | 12 | 0.000 | 0.087 | negligible | < 0.001 |
| Parkes zone stated by the maker | reports with a stated zone | 4,175 | 8,325 | 2 | 0 | 12,500 | 2 | 1486.146 | 4 | 0.000 | 0.345 | medium | < 0.001 |
| wear day of the failure | reports with a wear day | 2,197 | 378 | 6 | 20 | 2,595 | 3 | 147.090 | 10 | 0.000 | 0.168 | small | < 0.001 |
| fingerstick check mentioned | wrong-reading reports | 22,935 | 14,911 | 757 | 1,014 | 39,617 | 4 | 3597.574 | 6 | 0.000 | 0.213 | small | < 0.001 |
| user action (model) | wrong-reading reports | 22,935 | 14,911 | 757 | 1,014 | 39,617 | 4 | 2240.397 | 18 | 0.000 | 0.137 | small | < 0.001 |
| outcome severity (model) | wrong-reading reports | 22,935 | 14,911 | 757 | 1,014 | 39,617 | 4 | 3237.868 | 18 | 0.000 | 0.165 | small | < 0.001 |
| FDA event type | wrong-reading reports | 22,935 | 14,911 | 757 | 1,014 | 39,617 | 4 | 5.569 | 3 | 0.135 | 0.012 | negligible | 0.135 |
| FDA outcome code: Required Intervention | wrong-reading reports | 22,935 | 14,911 | 757 | 1,014 | 39,617 | 4 | 22662.976 | 3 | 0.000 | 0.756 | large | < 0.001 |
| FDA outcome code: Hospitalization | wrong-reading reports | 22,935 | 14,911 | 757 | 1,014 | 39,617 | 4 | 2685.739 | 3 | 0.000 | 0.260 | small | < 0.001 |
| FDA outcome code: Life Threatening | wrong-reading reports | 22,935 | 14,911 | 757 | 1,014 | 39,617 | 4 | 616.098 | 3 | 0.000 | 0.125 | small | < 0.001 |
| FDA outcome code: Death | wrong-reading reports | 22,935 | 14,911 | 757 | 1,014 | 39,617 | 4 | 7.434 | 3 | 0.059 | 0.014 | negligible | 0.059 |
| FDA outcome code: Other | wrong-reading reports | 22,935 | 14,911 | 757 | 1,014 | 39,617 | 4 | 23527.774 | 3 | 0.000 | 0.771 | large | < 0.001 |
| FDA outcome code: Disability | wrong-reading reports | 22,935 | 14,911 | 757 | 1,014 | 39,617 | 4 | 31.698 | 3 | 0.000 | 0.028 | negligible | < 0.001 |
| FDA outcome code: none stated | wrong-reading reports | 22,935 | 14,911 | 757 | 1,014 | 39,617 | 4 | 2886.819 | 3 | 0.000 | 0.270 | small | < 0.001 |
| who reported (FDA occupation field) | wrong-reading reports | 22,935 | 14,911 | 757 | 1,014 | 39,617 | 4 | 3743.212 | 9 | 0.000 | 0.177 | small | < 0.001 |
| text form | wrong-reading reports | 22,935 | 14,911 | 757 | 1,014 | 39,617 | 4 | 2444.519 | 3 | 0.000 | 0.248 | small | < 0.001 |

## g. Pairwise brand risk differences
| measure | base | group_a | group_b | n_a | n_b | share_a_pct | share_b_pct | risk_diff_points | risk_diff_ci_low | risk_diff_ci_high | p_text |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sensor read low (of pairs with a direction) | pairs | Abbott | Dexcom | 7,441 | 9,117 | 58.0 | 44.2 | 13.8 | 12.4 | 15.3 | < 0.001 |
| sensor read low (of pairs with a direction) | pairs | Abbott | Medtronic (caution) | 7,441 | 371 | 58.0 | 49.9 | 8.1 | 2.9 | 13.2 | 0.002 |
| sensor read low (of pairs with a direction) | pairs | Abbott | Senseonics (Eversense) | 7,441 | 529 | 58.0 | 54.4 | 3.5 | -0.5 | 8.0 | 0.111 |
| sensor read low (of pairs with a direction) | pairs | Dexcom | Medtronic (caution) | 9,117 | 371 | 44.2 | 49.9 | -5.7 | -10.9 | -0.4 | 0.031 |
| sensor read low (of pairs with a direction) | pairs | Dexcom | Senseonics (Eversense) | 9,117 | 529 | 44.2 | 54.4 | -10.3 | -14.5 | -5.6 | < 0.001 |
| sensor read low (of pairs with a direction) | pairs | Medtronic (caution) | Senseonics (Eversense) | 371 | 529 | 49.9 | 54.4 | -4.6 | -11.8 | 2.1 | 0.176 |
| meter under 70 (hidden low) | pairs | Abbott | Dexcom | 7,470 | 9,189 | 28.1 | 45.7 | -17.6 | -19.0 | -16.2 | < 0.001 |
| meter under 70 (hidden low) | pairs | Abbott | Medtronic (caution) | 7,470 | 379 | 28.1 | 42.5 | -14.4 | -19.3 | -9.2 | < 0.001 |
| meter under 70 (hidden low) | pairs | Abbott | Senseonics (Eversense) | 7,470 | 532 | 28.1 | 39.8 | -11.7 | -16.0 | -7.7 | < 0.001 |
| meter under 70 (hidden low) | pairs | Dexcom | Medtronic (caution) | 9,189 | 379 | 45.7 | 42.5 | 3.2 | -1.6 | 8.8 | 0.213 |
| meter under 70 (hidden low) | pairs | Dexcom | Senseonics (Eversense) | 9,189 | 532 | 45.7 | 39.8 | 5.9 | 1.5 | 10.1 | 0.008 |
| meter under 70 (hidden low) | pairs | Medtronic (caution) | Senseonics (Eversense) | 379 | 532 | 42.5 | 39.8 | 2.6 | -3.9 | 8.6 | 0.426 |
| meter over 250 | pairs | Abbott | Dexcom | 7,470 | 9,189 | 37.0 | 33.8 | 3.2 | 1.8 | 4.7 | < 0.001 |
| meter over 250 | pairs | Abbott | Medtronic (caution) | 7,470 | 379 | 37.0 | 35.9 | 1.1 | -3.4 | 5.8 | 0.656 |
| meter over 250 | pairs | Abbott | Senseonics (Eversense) | 7,470 | 532 | 37.0 | 20.5 | 16.5 | 12.7 | 20.2 | < 0.001 |
| meter over 250 | pairs | Dexcom | Medtronic (caution) | 9,189 | 379 | 33.8 | 35.9 | -2.1 | -6.9 | 2.6 | 0.399 |
| meter over 250 | pairs | Dexcom | Senseonics (Eversense) | 9,189 | 532 | 33.8 | 20.5 | 13.3 | 9.8 | 16.8 | < 0.001 |
| meter over 250 | pairs | Medtronic (caution) | Senseonics (Eversense) | 379 | 532 | 35.9 | 20.5 | 15.4 | 9.4 | 21.1 | < 0.001 |
| sensor under 70 | pairs | Abbott | Dexcom | 7,470 | 9,189 | 37.6 | 24.0 | 13.7 | 12.2 | 14.9 | < 0.001 |
| sensor under 70 | pairs | Abbott | Medtronic (caution) | 7,470 | 379 | 37.6 | 20.1 | 17.6 | 13.4 | 21.4 | < 0.001 |
| sensor under 70 | pairs | Abbott | Senseonics (Eversense) | 7,470 | 532 | 37.6 | 28.0 | 9.6 | 5.6 | 13.4 | < 0.001 |
| sensor under 70 | pairs | Dexcom | Medtronic (caution) | 9,189 | 379 | 24.0 | 20.1 | 3.9 | -0.4 | 8.0 | 0.081 |
| sensor under 70 | pairs | Dexcom | Senseonics (Eversense) | 9,189 | 532 | 24.0 | 28.0 | -4.1 | -8.1 | -0.4 | 0.034 |
| sensor under 70 | pairs | Medtronic (caution) | Senseonics (Eversense) | 379 | 532 | 20.1 | 28.0 | -8.0 | -13.5 | -2.0 | 0.006 |
| false low: sensor under 70, meter not | pairs | Abbott | Dexcom | 7,470 | 9,189 | 35.6 | 17.3 | 18.3 | 16.9 | 19.5 | < 0.001 |
| false low: sensor under 70, meter not | pairs | Abbott | Medtronic (caution) | 7,470 | 379 | 35.6 | 16.4 | 19.2 | 15.4 | 22.8 | < 0.001 |
| false low: sensor under 70, meter not | pairs | Abbott | Senseonics (Eversense) | 7,470 | 532 | 35.6 | 23.9 | 11.7 | 7.9 | 15.6 | < 0.001 |
| false low: sensor under 70, meter not | pairs | Dexcom | Medtronic (caution) | 9,189 | 379 | 17.3 | 16.4 | 1.0 | -2.9 | 4.8 | 0.630 |
| false low: sensor under 70, meter not | pairs | Dexcom | Senseonics (Eversense) | 9,189 | 532 | 17.3 | 23.9 | -6.6 | -10.6 | -2.9 | < 0.001 |
| false low: sensor under 70, meter not | pairs | Medtronic (caution) | Senseonics (Eversense) | 379 | 532 | 16.4 | 23.9 | -7.5 | -13.0 | -1.9 | 0.006 |
| missed low: meter under 70, sensor not | pairs | Abbott | Dexcom | 7,470 | 9,189 | 26.1 | 39.1 | -13.0 | -14.4 | -11.6 | < 0.001 |
| missed low: meter under 70, sensor not | pairs | Abbott | Medtronic (caution) | 7,470 | 379 | 26.1 | 38.8 | -12.7 | -17.7 | -7.8 | < 0.001 |
| missed low: meter under 70, sensor not | pairs | Abbott | Senseonics (Eversense) | 7,470 | 532 | 26.1 | 35.7 | -9.7 | -13.8 | -5.4 | < 0.001 |
| missed low: meter under 70, sensor not | pairs | Dexcom | Medtronic (caution) | 9,189 | 379 | 39.1 | 38.8 | 0.3 | -4.4 | 5.0 | 0.905 |
| missed low: meter under 70, sensor not | pairs | Dexcom | Senseonics (Eversense) | 9,189 | 532 | 39.1 | 35.7 | 3.4 | -1.0 | 7.7 | 0.120 |
| missed low: meter under 70, sensor not | pairs | Medtronic (caution) | Senseonics (Eversense) | 379 | 532 | 38.8 | 35.7 | 3.1 | -3.4 | 9.2 | 0.344 |
| Parkes zone D or E (computed) | pairs | Abbott | Dexcom | 7,470 | 9,189 | 43.6 | 35.4 | 8.2 | 6.7 | 9.6 | < 0.001 |
| Parkes zone D or E (computed) | pairs | Abbott | Medtronic (caution) | 7,470 | 379 | 43.6 | 34.0 | 9.6 | 4.6 | 14.3 | < 0.001 |
| Parkes zone D or E (computed) | pairs | Abbott | Senseonics (Eversense) | 7,470 | 532 | 43.6 | 16.0 | 27.6 | 24.3 | 30.9 | < 0.001 |
| Parkes zone D or E (computed) | pairs | Dexcom | Medtronic (caution) | 9,189 | 379 | 35.4 | 34.0 | 1.4 | -3.5 | 6.1 | 0.580 |
| Parkes zone D or E (computed) | pairs | Dexcom | Senseonics (Eversense) | 9,189 | 532 | 35.4 | 16.0 | 19.4 | 16.5 | 22.6 | < 0.001 |
| Parkes zone D or E (computed) | pairs | Medtronic (caution) | Senseonics (Eversense) | 379 | 532 | 34.0 | 16.0 | 18.1 | 12.6 | 23.6 | < 0.001 |
| fingerstick check: yes | wrong-reading reports | Abbott | Dexcom | 22,935 | 14,911 | 53.4 | 80.5 | -27.1 | -28.1 | -26.2 | < 0.001 |
| fingerstick check: yes | wrong-reading reports | Abbott | Medtronic (caution) | 22,935 | 757 | 53.4 | 85.9 | -32.5 | -35.0 | -29.9 | < 0.001 |
| fingerstick check: yes | wrong-reading reports | Abbott | Senseonics (Eversense) | 22,935 | 1,014 | 53.4 | 67.2 | -13.7 | -16.6 | -10.7 | < 0.001 |
| fingerstick check: yes | wrong-reading reports | Dexcom | Medtronic (caution) | 14,911 | 757 | 80.5 | 85.9 | -5.3 | -7.8 | -2.7 | < 0.001 |
| fingerstick check: yes | wrong-reading reports | Dexcom | Senseonics (Eversense) | 14,911 | 1,014 | 80.5 | 67.2 | 13.4 | 10.6 | 16.2 | < 0.001 |
| fingerstick check: yes | wrong-reading reports | Medtronic (caution) | Senseonics (Eversense) | 757 | 1,014 | 85.9 | 67.2 | 18.7 | 14.9 | 22.6 | < 0.001 |
| ate carbs | wrong-reading reports | Abbott | Dexcom | 22,935 | 14,911 | 30.5 | 34.8 | -4.3 | -5.2 | -3.3 | < 0.001 |
| ate carbs | wrong-reading reports | Abbott | Medtronic (caution) | 22,935 | 757 | 30.5 | 23.5 | 7.0 | 3.9 | 10.0 | < 0.001 |
| ate carbs | wrong-reading reports | Abbott | Senseonics (Eversense) | 22,935 | 1,014 | 30.5 | 31.6 | -1.1 | -4.0 | 1.8 | 0.468 |
| ate carbs | wrong-reading reports | Dexcom | Medtronic (caution) | 14,911 | 757 | 34.8 | 23.5 | 11.3 | 8.0 | 14.3 | < 0.001 |
| ate carbs | wrong-reading reports | Dexcom | Senseonics (Eversense) | 14,911 | 1,014 | 34.8 | 31.6 | 3.2 | 0.2 | 6.2 | 0.038 |
| ate carbs | wrong-reading reports | Medtronic (caution) | Senseonics (Eversense) | 757 | 1,014 | 23.5 | 31.6 | -8.0 | -12.1 | -4.2 | < 0.001 |
| took insulin | wrong-reading reports | Abbott | Dexcom | 22,935 | 14,911 | 10.4 | 5.4 | 5.0 | 4.5 | 5.5 | < 0.001 |
| took insulin | wrong-reading reports | Abbott | Medtronic (caution) | 22,935 | 757 | 10.4 | 12.3 | -1.9 | -4.3 | 0.5 | 0.097 |
| took insulin | wrong-reading reports | Abbott | Senseonics (Eversense) | 22,935 | 1,014 | 10.4 | 11.9 | -1.5 | -3.6 | 0.5 | 0.121 |
| took insulin | wrong-reading reports | Dexcom | Medtronic (caution) | 14,911 | 757 | 5.4 | 12.3 | -6.9 | -9.2 | -4.5 | < 0.001 |
| took insulin | wrong-reading reports | Dexcom | Senseonics (Eversense) | 14,911 | 1,014 | 5.4 | 11.9 | -6.5 | -8.6 | -4.5 | < 0.001 |
| took insulin | wrong-reading reports | Medtronic (caution) | Senseonics (Eversense) | 757 | 1,014 | 12.3 | 11.9 | 0.4 | -2.7 | 3.4 | 0.822 |
| sought care | wrong-reading reports | Abbott | Dexcom | 22,935 | 14,911 | 45.8 | 47.6 | -1.7 | -2.7 | -0.6 | 0.001 |
| sought care | wrong-reading reports | Abbott | Medtronic (caution) | 22,935 | 757 | 45.8 | 26.6 | 19.3 | 16.4 | 22.3 | < 0.001 |
| sought care | wrong-reading reports | Abbott | Senseonics (Eversense) | 22,935 | 1,014 | 45.8 | 12.4 | 33.4 | 31.1 | 35.5 | < 0.001 |
| sought care | wrong-reading reports | Dexcom | Medtronic (caution) | 14,911 | 757 | 47.6 | 26.6 | 21.0 | 17.9 | 24.2 | < 0.001 |
| sought care | wrong-reading reports | Dexcom | Senseonics (Eversense) | 14,911 | 1,014 | 47.6 | 12.4 | 35.1 | 32.8 | 37.4 | < 0.001 |
| sought care | wrong-reading reports | Medtronic (caution) | Senseonics (Eversense) | 757 | 1,014 | 26.6 | 12.4 | 14.1 | 10.3 | 17.9 | < 0.001 |
| outcome hypoglycaemia (model) | wrong-reading reports | Abbott | Dexcom | 22,935 | 14,911 | 11.3 | 12.5 | -1.3 | -1.9 | -0.6 | < 0.001 |
| outcome hypoglycaemia (model) | wrong-reading reports | Abbott | Medtronic (caution) | 22,935 | 757 | 11.3 | 33.3 | -22.0 | -25.4 | -18.6 | < 0.001 |
| outcome hypoglycaemia (model) | wrong-reading reports | Abbott | Senseonics (Eversense) | 22,935 | 1,014 | 11.3 | 46.5 | -35.3 | -38.4 | -32.2 | < 0.001 |
| outcome hypoglycaemia (model) | wrong-reading reports | Dexcom | Medtronic (caution) | 14,911 | 757 | 12.5 | 33.3 | -20.8 | -24.2 | -17.5 | < 0.001 |
| outcome hypoglycaemia (model) | wrong-reading reports | Dexcom | Senseonics (Eversense) | 14,911 | 1,014 | 12.5 | 46.5 | -34.0 | -37.1 | -31.0 | < 0.001 |
| outcome hypoglycaemia (model) | wrong-reading reports | Medtronic (caution) | Senseonics (Eversense) | 757 | 1,014 | 33.3 | 46.5 | -13.3 | -17.6 | -8.8 | < 0.001 |
| outcome hospital or ER (model) | wrong-reading reports | Abbott | Dexcom | 22,935 | 14,911 | 66.7 | 77.5 | -10.8 | -11.7 | -9.9 | < 0.001 |
| outcome hospital or ER (model) | wrong-reading reports | Abbott | Medtronic (caution) | 22,935 | 757 | 66.7 | 46.9 | 19.8 | 16.2 | 23.4 | < 0.001 |
| outcome hospital or ER (model) | wrong-reading reports | Abbott | Senseonics (Eversense) | 22,935 | 1,014 | 66.7 | 17.5 | 49.3 | 46.7 | 51.5 | < 0.001 |
| outcome hospital or ER (model) | wrong-reading reports | Dexcom | Medtronic (caution) | 14,911 | 757 | 77.5 | 46.9 | 30.6 | 27.1 | 34.3 | < 0.001 |
| outcome hospital or ER (model) | wrong-reading reports | Dexcom | Senseonics (Eversense) | 14,911 | 1,014 | 77.5 | 17.5 | 60.1 | 57.6 | 62.5 | < 0.001 |
| outcome hospital or ER (model) | wrong-reading reports | Medtronic (caution) | Senseonics (Eversense) | 757 | 1,014 | 46.9 | 17.5 | 29.4 | 25.1 | 33.4 | < 0.001 |
| outcome death (model) | wrong-reading reports | Abbott | Dexcom | 22,935 | 14,911 | 0.1 | 0.1 | 0.1 | 0.0 | 0.1 | 0.064 |
| outcome death (model) | wrong-reading reports | Abbott | Medtronic (caution) | 22,935 | 757 | 0.1 | 0.0 | 0.1 | 0.1 | 0.2 | 0.289 |
| outcome death (model) | wrong-reading reports | Abbott | Senseonics (Eversense) | 22,935 | 1,014 | 0.1 | 0.1 | 0.0 | -0.2 | 0.2 | 0.686 |
| outcome death (model) | wrong-reading reports | Dexcom | Medtronic (caution) | 14,911 | 757 | 0.1 | 0.0 | 0.1 | 0.0 | 0.1 | 0.435 |
| outcome death (model) | wrong-reading reports | Dexcom | Senseonics (Eversense) | 14,911 | 1,014 | 0.1 | 0.1 | -0.0 | -0.2 | 0.1 | 0.845 |
| outcome death (model) | wrong-reading reports | Medtronic (caution) | Senseonics (Eversense) | 757 | 1,014 | 0.0 | 0.1 | -0.1 | -0.3 | 0.0 | 0.387 |
| FDA event type Death | wrong-reading reports | Abbott | Dexcom | 22,935 | 14,911 | 0.2 | 0.1 | 0.1 | 0.0 | 0.2 | 0.029 |
| FDA event type Death | wrong-reading reports | Abbott | Medtronic (caution) | 22,935 | 757 | 0.2 | 0.1 | 0.1 | -0.2 | 0.3 | 0.536 |
| FDA event type Death | wrong-reading reports | Abbott | Senseonics (Eversense) | 22,935 | 1,014 | 0.2 | 0.1 | 0.1 | -0.1 | 0.3 | 0.352 |
| FDA event type Death | wrong-reading reports | Dexcom | Medtronic (caution) | 14,911 | 757 | 0.1 | 0.1 | 0.0 | -0.3 | 0.2 | 0.950 |
| FDA event type Death | wrong-reading reports | Dexcom | Senseonics (Eversense) | 14,911 | 1,014 | 0.1 | 0.1 | 0.0 | -0.2 | 0.2 | 0.726 |
| FDA event type Death | wrong-reading reports | Medtronic (caution) | Senseonics (Eversense) | 757 | 1,014 | 0.1 | 0.1 | 0.0 | -0.3 | 0.4 | 0.836 |
| FDA code Hospitalization | wrong-reading reports | Abbott | Dexcom | 22,935 | 14,911 | 7.9 | 26.9 | -19.0 | -19.8 | -18.2 | < 0.001 |
| FDA code Hospitalization | wrong-reading reports | Abbott | Medtronic (caution) | 22,935 | 757 | 7.9 | 34.2 | -26.4 | -29.5 | -23.1 | < 0.001 |
| FDA code Hospitalization | wrong-reading reports | Abbott | Senseonics (Eversense) | 22,935 | 1,014 | 7.9 | 12.2 | -4.4 | -6.7 | -2.3 | < 0.001 |
| FDA code Hospitalization | wrong-reading reports | Dexcom | Medtronic (caution) | 14,911 | 757 | 26.9 | 34.2 | -7.3 | -10.7 | -4.0 | < 0.001 |
| FDA code Hospitalization | wrong-reading reports | Dexcom | Senseonics (Eversense) | 14,911 | 1,014 | 26.9 | 12.2 | 14.6 | 12.5 | 16.7 | < 0.001 |
| FDA code Hospitalization | wrong-reading reports | Medtronic (caution) | Senseonics (Eversense) | 757 | 1,014 | 34.2 | 12.2 | 22.0 | 18.1 | 25.9 | < 0.001 |
| FDA code Required Intervention | wrong-reading reports | Abbott | Dexcom | 22,935 | 14,911 | 80.5 | 3.8 | 76.8 | 76.2 | 77.4 | < 0.001 |
| FDA code Required Intervention | wrong-reading reports | Abbott | Medtronic (caution) | 22,935 | 757 | 80.5 | 15.6 | 65.0 | 62.1 | 67.6 | < 0.001 |
| FDA code Required Intervention | wrong-reading reports | Abbott | Senseonics (Eversense) | 22,935 | 1,014 | 80.5 | 0.2 | 80.4 | 79.8 | 80.9 | < 0.001 |
| FDA code Required Intervention | wrong-reading reports | Dexcom | Medtronic (caution) | 14,911 | 757 | 3.8 | 15.6 | -11.8 | -14.4 | -9.4 | < 0.001 |
| FDA code Required Intervention | wrong-reading reports | Dexcom | Senseonics (Eversense) | 14,911 | 1,014 | 3.8 | 0.2 | 3.6 | 3.1 | 3.9 | < 0.001 |
| FDA code Required Intervention | wrong-reading reports | Medtronic (caution) | Senseonics (Eversense) | 757 | 1,014 | 15.6 | 0.2 | 15.4 | 12.9 | 18.0 | < 0.001 |
| FDA code Life Threatening | wrong-reading reports | Abbott | Dexcom | 22,935 | 14,911 | 0.8 | 4.6 | -3.8 | -4.2 | -3.5 | < 0.001 |
| FDA code Life Threatening | wrong-reading reports | Abbott | Medtronic (caution) | 22,935 | 757 | 0.8 | 2.2 | -1.5 | -2.6 | -0.5 | < 0.001 |
| FDA code Life Threatening | wrong-reading reports | Abbott | Senseonics (Eversense) | 22,935 | 1,014 | 0.8 | 0.7 | 0.1 | -0.5 | 0.6 | 0.760 |
| FDA code Life Threatening | wrong-reading reports | Dexcom | Medtronic (caution) | 14,911 | 757 | 4.6 | 2.2 | 2.4 | 1.2 | 3.4 | 0.002 |
| FDA code Life Threatening | wrong-reading reports | Dexcom | Senseonics (Eversense) | 14,911 | 1,014 | 4.6 | 0.7 | 3.9 | 3.3 | 4.5 | < 0.001 |
| FDA code Life Threatening | wrong-reading reports | Medtronic (caution) | Senseonics (Eversense) | 757 | 1,014 | 2.2 | 0.7 | 1.6 | 0.5 | 2.8 | 0.005 |
| FDA code Death | wrong-reading reports | Abbott | Dexcom | 22,935 | 14,911 | 0.2 | 0.1 | 0.1 | 0.0 | 0.2 | 0.010 |
| FDA code Death | wrong-reading reports | Abbott | Medtronic (caution) | 22,935 | 757 | 0.2 | 0.1 | 0.1 | -0.2 | 0.3 | 0.524 |
| FDA code Death | wrong-reading reports | Abbott | Senseonics (Eversense) | 22,935 | 1,014 | 0.2 | 0.1 | 0.1 | -0.1 | 0.3 | 0.342 |
| FDA code Death | wrong-reading reports | Dexcom | Medtronic (caution) | 14,911 | 757 | 0.1 | 0.1 | -0.0 | -0.3 | 0.2 | 0.972 |
| FDA code Death | wrong-reading reports | Dexcom | Senseonics (Eversense) | 14,911 | 1,014 | 0.1 | 0.1 | 0.0 | -0.2 | 0.2 | 0.802 |
| FDA code Death | wrong-reading reports | Medtronic (caution) | Senseonics (Eversense) | 757 | 1,014 | 0.1 | 0.1 | 0.0 | -0.3 | 0.4 | 0.836 |

## g. Confound (a): Abbott template vs prose, pairs
| group | n_pairs | weighted_n | median_mgdl | q1_mgdl | q3_mgdl | p10_mgdl | p90_mgdl | median_pct | q1_pct | q3_pct | p10_pct | p90_pct | pct_low | pct_high | pct_equal | median_sensor_mgdl | median_meter_mgdl | pct_reads_low_label | pct_false_low_70 | pct_missed_low_70 | pct_false_high_180 | pct_missed_high_180 | pct_abs_err_over_20 | pct_abs_err_over_40 | median_abs_err_pct | pct_meter_under_70 | pct_meter_over_250 | pct_sensor_under_70 | pct_zone_DE_computed | pct_fingerstick_yes | pct_outcome_hospital_or_er | pct_outcome_none | pct_fda_death | pct_meter_<54 | pct_meter_54-69 | pct_meter_70-180 | pct_meter_181-250 | pct_meter_>250 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Abbott, template pairs | 2,982 | 2,982 | -81.0 | -270.0 | 100.0 | -432.0 | 217.0 | -50.0 | -80.0 | 150.0 | -88.2 | 365.6 | 56.2 | 43.6 | 0.2 | 90.0 | 174.0 | 55.8 | 36.4 | 26.6 | 20.9 | 43.9 | 98.4 | 94.5 | 86.2 | 28.1 | 36.7 | 37.9 | 43.0 | 94.9 | 69.4 | 11.1 | 0.1 | 21.7 | 6.4 | 23.8 | 11.5 | 36.7 |
| Abbott, prose pairs | 4,488 | 4,488 | -63.0 | -288.0 | 92.0 | -467.7 | 236.0 | -45.9 | -79.6 | 142.3 | -89.0 | 463.4 | 58.8 | 40.7 | 0.5 | 92.0 | 163.0 | 56.8 | 35.0 | 25.7 | 20.4 | 40.4 | 97.3 | 90.7 | 84.6 | 28.1 | 37.3 | 37.5 | 44.0 | 97.0 | 75.5 | 10.3 | 0.3 | 21.9 | 6.2 | 25.3 | 9.3 | 37.3 |
| Dexcom, all pairs (prose) | 9,189 | 9,189 | 29.0 | -217.0 | 77.2 | -445.0 | 160.0 | 44.1 | -64.0 | 172.3 | -86.0 | 382.8 | 43.8 | 55.4 | 0.8 | 110.0 | 95.0 | 49.4 | 17.3 | 39.1 | 14.4 | 25.7 | 97.0 | 87.3 | 86.7 | 45.7 | 33.8 | 24.0 | 35.4 | 97.4 | 81.3 | 4.6 | 0.1 | 39.7 | 6.0 | 15.2 | 5.3 | 33.8 |
| Senseonics, all pairs (prose) | 532 | 532 | -21.5 | -105.0 | 60.0 | -229.3 | 110.6 | -19.0 | -52.8 | 116.8 | -69.7 | 226.9 | 54.1 | 45.3 | 0.6 | 104.5 | 98.5 | 50.4 | 23.9 | 35.7 | 8.3 | 22.9 | 92.3 | 79.3 | 65.5 | 39.8 | 20.5 | 28.0 | 16.0 | 98.1 | 15.8 | 33.8 | 0.0 | 26.9 | 13.0 | 27.4 | 12.2 | 20.5 |

## g. Confound (a): tests
| measure | group_a | group_b | n_a | n_b | median_a | median_b | iqr_a | iqr_b | median_diff_a_minus_b | median_diff_ci_low | median_diff_ci_high | cliffs_delta | cliffs_delta_ci_low | cliffs_delta_ci_high | effect_size_word | mann_whitney_p | p_text | share_a_pct | share_b_pct | risk_diff_points | risk_diff_ci_low | risk_diff_ci_high | chi_square_p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| error, % of meter | Abbott, template pairs | Abbott, prose pairs | 2,982 | 4,488 | -50.00 | -45.94 | -80 to 150 | -80 to 142 | -4.06 | -8.55 | 2.22 | -0.00 | -0.03 | 0.02 | negligible | 0.86 | 0.858 |  |  |  |  |  |  |
| error, mg/dL | Abbott, template pairs | Abbott, prose pairs | 2,982 | 4,488 | -81.00 | -63.00 | -270 to 100 | -288 to 92 | -18.00 | -38.51 | 2.00 | 0.01 | -0.01 | 0.04 | negligible | 0.34 | 0.343 |  |  |  |  |  |  |
| meter value, mg/dL | Abbott, template pairs | Abbott, prose pairs | 2,982 | 4,488 | 174.00 | 163.00 | 60 to 356 | 60 to 380 | 11.00 | -1.00 | 22.00 | -0.01 | -0.03 | 0.02 | negligible | 0.52 | 0.516 |  |  |  |  |  |  |
| error, % of meter: sensor below meter only | Abbott, template pairs | Abbott, prose pairs | 1,675 | 2,640 | -78.04 | -75.66 | -86 to -65 | -86 to -57 | -2.39 | -3.93 | -0.91 | -0.06 | -0.10 | -0.03 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| share reading low (of pairs with a direction) | Abbott, template pairs | Abbott, prose pairs | 2,976 | 4,465 |  |  |  |  |  |  |  |  |  |  |  |  | 0.015 | 56.28 | 59.13 | -2.84 | -5.31 | -0.54 | 0.01 |
| share meter under 70 | Abbott, template pairs | Abbott, prose pairs | 2,982 | 4,488 |  |  |  |  |  |  |  |  |  |  |  |  | 0.987 | 28.10 | 28.12 | -0.02 | -2.14 | 2.16 | 0.99 |
| share meter over 250 | Abbott, template pairs | Abbott, prose pairs | 2,982 | 4,488 |  |  |  |  |  |  |  |  |  |  |  |  | 0.598 | 36.65 | 37.25 | -0.60 | -2.88 | 1.54 | 0.60 |
| share Parkes D or E (computed) | Abbott, template pairs | Abbott, prose pairs | 2,982 | 4,488 |  |  |  |  |  |  |  |  |  |  |  |  | 0.397 | 42.99 | 43.98 | -0.99 | -3.24 | 1.32 | 0.40 |
| error, % of meter | Abbott, prose pairs | Dexcom, all pairs (prose) | 4,488 | 9,189 | -45.94 | 44.07 | -80 to 142 | -64 to 172 | -90.01 | -96.27 | -84.90 | -0.15 | -0.17 | -0.13 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| error, mg/dL | Abbott, prose pairs | Dexcom, all pairs (prose) | 4,488 | 9,189 | -63.00 | 29.00 | -288 to 92 | -217 to 77 | -92.00 | -99.00 | -84.00 | -0.06 | -0.09 | -0.04 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| meter value, mg/dL | Abbott, prose pairs | Dexcom, all pairs (prose) | 4,488 | 9,189 | 163.00 | 95.00 | 60 to 380 | 40 to 400 | 68.00 | 58.00 | 79.00 | 0.14 | 0.12 | 0.16 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| error, % of meter: sensor below meter only | Abbott, prose pairs | Dexcom, all pairs (prose) | 2,640 | 4,029 | -75.66 | -69.18 | -86 to -57 | -85 to -48 | -6.48 | -8.16 | -4.88 | -0.12 | -0.15 | -0.09 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| share reading low (of pairs with a direction) | Abbott, prose pairs | Dexcom, all pairs (prose) | 4,465 | 9,117 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 59.13 | 44.19 | 14.93 | 13.13 | 16.64 | 0.00 |
| share meter under 70 | Abbott, prose pairs | Dexcom, all pairs (prose) | 4,488 | 9,189 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 28.12 | 45.73 | -17.61 | -19.19 | -15.87 | 0.00 |
| share meter over 250 | Abbott, prose pairs | Dexcom, all pairs (prose) | 4,488 | 9,189 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 37.25 | 33.79 | 3.46 | 1.90 | 5.22 | 0.00 |
| share Parkes D or E (computed) | Abbott, prose pairs | Dexcom, all pairs (prose) | 4,488 | 9,189 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 43.98 | 35.42 | 8.56 | 6.89 | 10.37 | 0.00 |
| error, % of meter | Abbott, template pairs | Dexcom, all pairs (prose) | 2,982 | 9,189 | -50.00 | 44.07 | -80 to 150 | -64 to 172 | -94.07 | -100.90 | -87.76 | -0.14 | -0.17 | -0.12 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| error, mg/dL | Abbott, template pairs | Dexcom, all pairs (prose) | 2,982 | 9,189 | -81.00 | 29.00 | -270 to 100 | -217 to 77 | -110.00 | -129.00 | -90.00 | -0.04 | -0.06 | -0.01 | negligible | 0.00 | 0.001 |  |  |  |  |  |  |
| meter value, mg/dL | Abbott, template pairs | Dexcom, all pairs (prose) | 2,982 | 9,189 | 174.00 | 95.00 | 60 to 356 | 40 to 400 | 79.00 | 67.00 | 91.00 | 0.13 | 0.11 | 0.16 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| error, % of meter: sensor below meter only | Abbott, template pairs | Dexcom, all pairs (prose) | 1,675 | 4,029 | -78.04 | -69.18 | -86 to -65 | -85 to -48 | -8.86 | -10.38 | -7.31 | -0.19 | -0.22 | -0.16 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| share reading low (of pairs with a direction) | Abbott, template pairs | Dexcom, all pairs (prose) | 2,976 | 9,117 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 56.28 | 44.19 | 12.09 | 10.03 | 14.18 | 0.00 |
| share meter under 70 | Abbott, template pairs | Dexcom, all pairs (prose) | 2,982 | 9,189 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 28.10 | 45.73 | -17.63 | -19.52 | -15.59 | 0.00 |
| share meter over 250 | Abbott, template pairs | Dexcom, all pairs (prose) | 2,982 | 9,189 |  |  |  |  |  |  |  |  |  |  |  |  | 0.004 | 36.65 | 33.79 | 2.86 | 0.81 | 4.74 | 0.00 |
| share Parkes D or E (computed) | Abbott, template pairs | Dexcom, all pairs (prose) | 2,982 | 9,189 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 42.99 | 35.42 | 7.57 | 5.37 | 9.61 | 0.00 |
| error, % of meter | Abbott, prose pairs | Senseonics, all pairs (prose) | 4,488 | 532 | -45.94 | -19.03 | -80 to 142 | -53 to 117 | -26.91 | -44.12 | -17.84 | -0.16 | -0.20 | -0.13 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| error, mg/dL | Abbott, prose pairs | Senseonics, all pairs (prose) | 4,488 | 532 | -63.00 | -21.50 | -288 to 92 | -104 to 60 | -41.50 | -62.00 | -24.50 | -0.11 | -0.15 | -0.07 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| meter value, mg/dL | Abbott, prose pairs | Senseonics, all pairs (prose) | 4,488 | 532 | 163.00 | 98.50 | 60 to 380 | 51 to 224 | 64.50 | 52.00 | 78.00 | 0.19 | 0.15 | 0.24 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| error, % of meter: sensor below meter only | Abbott, prose pairs | Senseonics, all pairs (prose) | 2,640 | 288 | -75.66 | -51.26 | -86 to -57 | -65 to -37 | -24.40 | -27.94 | -21.31 | -0.52 | -0.57 | -0.48 | large | 0.00 | < 0.001 |  |  |  |  |  |  |
| share reading low (of pairs with a direction) | Abbott, prose pairs | Senseonics, all pairs (prose) | 4,465 | 529 |  |  |  |  |  |  |  |  |  |  |  |  | 0.039 | 59.13 | 54.44 | 4.68 | -0.11 | 8.85 | 0.04 |
| share meter under 70 | Abbott, prose pairs | Senseonics, all pairs (prose) | 4,488 | 532 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 28.12 | 39.85 | -11.73 | -16.21 | -7.01 | 0.00 |
| share meter over 250 | Abbott, prose pairs | Senseonics, all pairs (prose) | 4,488 | 532 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 37.25 | 20.49 | 16.77 | 12.96 | 20.42 | 0.00 |
| share Parkes D or E (computed) | Abbott, prose pairs | Senseonics, all pairs (prose) | 4,488 | 532 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 43.98 | 15.98 | 28.01 | 24.49 | 31.29 | 0.00 |

## g. Confound (a): what the text forms report (all Abbott wrong-reading reports)
| group | n | pct_with_pair | pct_fault_reads_low | pct_fault_reads_high | pct_zone_stated | pct_wear_day | pct_fingerstick_yes | pct_user_action_stated | pct_ate_carbs | pct_took_insulin | pct_sought_care | pct_outcome_none | pct_outcome_hospital_or_er | pct_outcome_death | pct_fda_hospitalization | pct_fda_required_intervention | pct_fda_death | pct_age_filled | pct_sex_filled | median_text_chars |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Abbott template reports | 3,098 | 98.1 | 55.0 | 44.4 | 71.6 | 35.8 | 93.6 | 93.7 | 39.2 | 16.4 | 36.2 | 10.9 | 69.6 | 0.0 | 5.6 | 81.1 | 0.1 | 14.7 | 10.4 | 3152.5 |
| Abbott prose reports | 19,837 | 23.2 | 51.3 | 35.8 | 9.9 | 5.5 | 47.1 | 91.4 | 29.1 | 9.5 | 47.4 | 13.1 | 66.3 | 0.2 | 8.2 | 80.5 | 0.3 | 19.8 | 19.4 | 2,767 |
| Dexcom reports | 14,911 | 63.1 | 43.4 | 32.3 | 55.8 | 2.5 | 80.5 | 93.7 | 34.8 | 5.4 | 47.6 | 6.7 | 77.5 | 0.1 | 26.9 | 3.8 | 0.1 | 93.2 | 78.1 | 1,350 |

## g. Confound (b): serious vs weighted malfunction sample
| tier | brand | wrong_reading_reports | weighted_reports | pct_with_pair | label_reads_low_pct | label_reads_high_pct | label_low_share_of_low_plus_high_pct | code_low_readings_pct | code_high_readings_pct | pairs | pairs_weighted | median_err_pct | q1_err_pct | q3_err_pct | median_err_mgdl | pct_low | pct_high | pct_meter_under_70 | pct_meter_over_250 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| serious | Abbott | 22,935 | 22,935 | 33.3 | 51.8 | 37.0 | 58.3 | 54.2 | 38.0 | 7,470 | 7,470 | -47.1 | -80.0 | 146.3 | -67.0 | 57.8 | 41.8 | 28.1 | 37.0 |
| serious | Dexcom | 14,911 | 14,911 | 63.1 | 43.4 | 32.3 | 57.3 | 12.1 | 6.9 | 9,189 | 9,189 | 44.1 | -64.0 | 172.3 | 29.0 | 43.8 | 55.4 | 45.7 | 33.8 |
| serious | Medtronic (caution) | 757 | 757 | 51.0 | 29.6 | 29.3 | 50.2 | 1.6 | 1.6 | 379 | 379 | 0.0 | -63.1 | 165.9 | 0.0 | 48.8 | 49.1 | 42.5 | 35.9 |
| serious | Senseonics (Eversense) | 1,014 | 1,014 | 52.8 | 35.2 | 22.6 | 60.9 | 0.0 | 0.0 | 532 | 532 | -19.0 | -52.8 | 116.8 | -21.5 | 54.1 | 45.3 | 39.8 | 20.5 |
| sample (weighted) | Abbott | 797 | 376,494 | 28.8 | 44.9 | 7.3 | 86.0 | 26.8 | 0.3 | 255 | 107,133 | -65.0 | -72.1 | 83.8 | -110.0 | 73.3 | 26.7 | 6.3 | 16.0 |
| sample (weighted) | Dexcom | 634 | 349,517 | 4.4 | 2.4 | 1.6 | 59.3 | 10.6 | 3.5 | 31 | 15,472 | -44.9 | -57.6 | 29.1 | -61.0 | 68.6 | 31.4 | 4.3 | 15.2 |
| sample (weighted) | Medtronic (caution) | 40 | 5,343 | 54.4 | 54.7 | 7.3 | 88.3 | 0.0 | 0.0 | 24 | 2,907 | -65.6 | -72.9 | -49.7 | -144.5 | 91.6 | 8.4 | 3.7 | 42.8 |
| sample (weighted) | Senseonics (Eversense) | 87 | 2,310 | 9.8 | 2.8 | 4.2 | 40.0 | 0.0 | 0.0 | 15 | 225 | -30.6 | -38.5 | 47.3 | -61.7 | 64.2 | 35.8 | 7.4 | 14.5 |

## g. Confound (b): tests
| tier | measure | brand_a | brand_b | n_a | n_b | median_a | median_b | iqr_a | iqr_b | median_diff_a_minus_b | median_diff_ci_low | median_diff_ci_high | cliffs_delta | cliffs_delta_ci_low | cliffs_delta_ci_high | effect_size_word | mann_whitney_p | p_text | share_a_pct | share_b_pct | risk_diff_points | risk_diff_ci_low | risk_diff_ci_high | chi_square_p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| serious | error, % of meter | Abbott | Dexcom | 7,470 | 9,189 | -47.12 | 44.07 | -80 to 146 | -64 to 172 | -91.18 | -97.19 | -85.93 | -0.15 | -0.16 | -0.13 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| serious | share reading low | Abbott | Dexcom | 7,441 | 9,117 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 57.99 | 44.19 | 13.80 | 12.33 | 15.22 | 0.00 |
| serious | error, % of meter | Abbott | Medtronic (caution) | 7,470 | 379 | -47.12 | 0.00 | -80 to 146 | -63 to 164 | -47.12 | -91.41 | -22.11 | -0.13 | -0.18 | -0.08 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| serious | share reading low | Abbott | Medtronic (caution) | 7,441 | 371 |  |  |  |  |  |  |  |  |  |  |  |  | 0.002 | 57.99 | 49.87 | 8.12 | 2.85 | 13.44 | 0.00 |
| serious | error, % of meter | Abbott | Senseonics (Eversense) | 7,470 | 532 | -47.12 | -19.03 | -80 to 146 | -53 to 117 | -28.09 | -45.54 | -18.89 | -0.16 | -0.20 | -0.13 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| serious | share reading low | Abbott | Senseonics (Eversense) | 7,441 | 529 |  |  |  |  |  |  |  |  |  |  |  |  | 0.111 | 57.99 | 54.44 | 3.55 | -1.08 | 7.86 | 0.11 |
| sample (unweighted rows) | error, % of meter | Abbott | Dexcom | 255 | 31 | -64.46 | -44.85 | -73 to 102 | -57 to 32 | -19.61 | -48.86 | -9.54 | -0.21 | -0.38 | -0.05 | small | 0.06 | 0.055 |  |  |  |  |  |  |
| sample (unweighted rows) | share reading low | Abbott | Dexcom | 255 | 31 |  |  |  |  |  |  |  |  |  |  |  |  | 0.778 | 70.20 | 67.74 | 2.45 | -14.76 | 19.76 | 0.78 |
| sample (unweighted rows) | error, % of meter | Abbott | Medtronic (caution) | 255 | 24 | -64.46 | -64.94 | -73 to 102 | -67 to -54 | 0.48 | -8.48 | 4.88 | 0.01 | -0.16 | 0.18 | negligible | 0.94 | 0.942 |  |  |  |  |  |  |
| sample (unweighted rows) | share reading low | Abbott | Medtronic (caution) | 255 | 24 |  |  |  |  |  |  |  |  |  |  |  |  | 0.072 | 70.20 | 87.50 | -17.30 | -29.56 | -2.59 | 0.07 |
| sample (unweighted rows) | error, % of meter | Abbott | Senseonics (Eversense) | 255 | 15 | -64.46 | 25.48 | -73 to 102 | -38 to 99 |  |  |  |  |  |  |  |  | too few |  |  |  |  |  |  |
| sample (unweighted rows) | share reading low | Abbott | Senseonics (Eversense) | 255 | 15 |  |  |  |  |  |  |  |  |  |  |  |  | too few | 70.20 | 46.67 |  |  |  |  |

## g. Confound (c): by year
| year | brand | wrong_reading_reports | pairs | pct_reports_with_pair | recall_window_in_year | pct_fda_death | pct_outcome_hospital_or_er | median_err_pct | q1_err_pct | q3_err_pct | pct_low | pct_meter_under_70 | pct_meter_over_250 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2,007 | Abbott | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,007 | Dexcom | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,007 | Medtronic (caution) | 4 | 1 | 25.0 |  | 0.0 | 100.0 |  |  |  |  |  |  |
| 2,007 | Senseonics (Eversense) | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,008 | Abbott | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,008 | Dexcom | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,008 | Medtronic (caution) | 3 | 0 | 0.0 |  | 0.0 | 100.0 |  |  |  |  |  |  |
| 2,008 | Senseonics (Eversense) | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,009 | Abbott | 1 | 1 | 100.0 |  | 0.0 | 100.0 |  |  |  |  |  |  |
| 2,009 | Dexcom | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,009 | Medtronic (caution) | 11 | 3 | 27.3 |  | 0.0 | 81.8 |  |  |  |  |  |  |
| 2,009 | Senseonics (Eversense) | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,010 | Abbott | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,010 | Dexcom | 22 | 15 | 68.2 |  | 0.0 | 81.8 |  |  |  |  |  |  |
| 2,010 | Medtronic (caution) | 50 | 14 | 28.0 |  | 0.0 | 86.0 |  |  |  |  |  |  |
| 2,010 | Senseonics (Eversense) | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,011 | Abbott | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,011 | Dexcom | 19 | 12 | 63.2 |  | 0.0 | 78.9 |  |  |  |  |  |  |
| 2,011 | Medtronic (caution) | 49 | 11 | 22.4 |  | 0.0 | 83.7 |  |  |  |  |  |  |
| 2,011 | Senseonics (Eversense) | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,012 | Abbott | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,012 | Dexcom | 49 | 29 | 59.2 |  | 0.0 | 95.9 | 233.3 | 140.9 | 390.1 | 10.3 | 86.2 | 3.4 |
| 2,012 | Medtronic (caution) | 63 | 5 | 7.9 |  | 0.0 | 87.3 |  |  |  |  |  |  |
| 2,012 | Senseonics (Eversense) | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,013 | Abbott | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,013 | Dexcom | 40 | 27 | 67.5 |  | 0.0 | 95.0 | 120.7 | 67.6 | 224.4 | 11.1 | 85.2 | 7.4 |
| 2,013 | Medtronic (caution) | 30 | 11 | 36.7 |  | 0.0 | 93.3 |  |  |  |  |  |  |
| 2,013 | Senseonics (Eversense) | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,014 | Abbott | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,014 | Dexcom | 51 | 18 | 35.3 |  | 0.0 | 54.9 |  |  |  |  |  |  |
| 2,014 | Medtronic (caution) | 113 | 46 | 40.7 |  | 0.0 | 38.9 | -4.4 | -53.1 | 148.0 | 50.0 | 37.0 | 21.7 |
| 2,014 | Senseonics (Eversense) | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,015 | Abbott | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,015 | Dexcom | 55 | 37 | 67.3 |  | 0.0 | 69.1 | 129.2 | 16.7 | 258.6 | 21.6 | 62.2 | 8.1 |
| 2,015 | Medtronic (caution) | 129 | 68 | 52.7 |  | 0.0 | 20.9 | -28.3 | -69.8 | 111.3 | 58.8 | 33.8 | 36.8 |
| 2,015 | Senseonics (Eversense) | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,016 | Abbott | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,016 | Dexcom | 160 | 120 | 75.0 |  | 0.0 | 64.4 | 113.5 | 46.5 | 238.2 | 19.2 | 72.5 | 10.0 |
| 2,016 | Medtronic (caution) | 1 | 1 | 100.0 |  | 0.0 | 0.0 |  |  |  |  |  |  |
| 2,016 | Senseonics (Eversense) | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,017 | Abbott | 16 | 11 | 68.8 |  | 0.0 | 81.2 |  |  |  |  |  |  |
| 2,017 | Dexcom | 275 | 143 | 52.0 |  | 0.0 | 60.0 | 94.4 | 0.0 | 215.2 | 23.8 | 67.8 | 11.2 |
| 2,017 | Medtronic (caution) | 14 | 6 | 42.9 |  | 0.0 | 14.3 |  |  |  |  |  |  |
| 2,017 | Senseonics (Eversense) | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,018 | Abbott | 452 | 249 | 55.1 |  | 0.0 | 84.5 | 27.9 | -72.7 | 246.0 | 46.6 | 33.3 | 37.3 |
| 2,018 | Dexcom | 479 | 287 | 59.9 |  | 0.0 | 61.4 | 105.4 | -1.8 | 232.9 | 25.1 | 68.3 | 17.8 |
| 2,018 | Medtronic (caution) | 3 | 1 | 33.3 |  | 0.0 | 66.7 |  |  |  |  |  |  |
| 2,018 | Senseonics (Eversense) | 0 | 0 |  |  |  |  |  |  |  |  |  |  |
| 2,019 | Abbott | 782 | 426 | 54.5 |  | 0.1 | 82.6 | -33.3 | -70.9 | 176.4 | 53.3 | 27.9 | 40.6 |
| 2,019 | Dexcom | 646 | 445 | 68.9 |  | 0.0 | 68.0 | 82.9 | -48.5 | 181.2 | 33.9 | 58.0 | 21.1 |
| 2,019 | Medtronic (caution) | 4 | 0 | 0.0 |  | 0.0 | 25.0 |  |  |  |  |  |  |
| 2,019 | Senseonics (Eversense) | 31 | 0 | 0.0 |  | 0.0 | 9.7 |  |  |  |  |  |  |
| 2,020 | Abbott | 800 | 329 | 41.1 |  | 0.0 | 74.9 | -42.9 | -74.9 | 213.4 | 59.0 | 32.8 | 39.5 |
| 2,020 | Dexcom | 514 | 369 | 71.8 |  | 0.2 | 64.6 | 60.0 | -54.8 | 192.8 | 39.0 | 50.7 | 27.9 |
| 2,020 | Medtronic (caution) | 5 | 4 | 80.0 |  | 0.0 | 40.0 |  |  |  |  |  |  |
| 2,020 | Senseonics (Eversense) | 72 | 1 | 1.4 |  | 0.0 | 18.1 |  |  |  |  |  |  |
| 2,021 | Abbott | 1,807 | 673 | 37.2 |  | 0.0 | 71.3 | 12.0 | -73.1 | 200.0 | 49.0 | 35.1 | 29.1 |
| 2,021 | Dexcom | 672 | 476 | 70.8 |  | 0.0 | 60.7 | 49.3 | -67.5 | 202.2 | 45.2 | 44.5 | 31.5 |
| 2,021 | Medtronic (caution) | 1 | 1 | 100.0 |  | 0.0 | 0.0 |  |  |  |  |  |  |
| 2,021 | Senseonics (Eversense) | 26 | 0 | 0.0 |  | 0.0 | 15.4 |  |  |  |  |  |  |
| 2,022 | Abbott | 2,361 | 710 | 30.1 |  | 0.1 | 65.5 | 45.9 | -75.0 | 219.2 | 46.3 | 37.0 | 29.4 |
| 2,022 | Dexcom | 1,015 | 708 | 69.8 |  | 0.1 | 80.0 | 84.9 | -43.6 | 219.4 | 34.3 | 55.1 | 29.1 |
| 2,022 | Medtronic (caution) | 8 | 6 | 75.0 |  | 0.0 | 0.0 |  |  |  |  |  |  |
| 2,022 | Senseonics (Eversense) | 48 | 6 | 12.5 |  | 0.0 | 18.8 |  |  |  |  |  |  |
| 2,023 | Abbott | 3,567 | 886 | 24.8 |  | 0.1 | 67.8 | 26.8 | -72.9 | 200.0 | 47.7 | 35.4 | 26.0 |
| 2,023 | Dexcom | 1,996 | 1,355 | 67.9 |  | 0.0 | 82.9 | 90.8 | -38.7 | 233.3 | 32.0 | 55.9 | 24.4 |
| 2,023 | Medtronic (caution) | 17 | 5 | 29.4 |  | 0.0 | 0.0 |  |  |  |  |  |  |
| 2,023 | Senseonics (Eversense) | 170 | 83 | 48.8 |  | 0.0 | 15.3 | 71.4 | -33.7 | 150.0 | 36.1 | 53.0 | 6.0 |
| 2,024 | Abbott | 4,215 | 1,131 | 26.8 | W1 | 0.0 | 71.9 | -39.4 | -78.4 | 148.3 | 54.0 | 32.0 | 34.1 |
| 2,024 | Dexcom | 2,500 | 1,538 | 61.5 | W1 | 0.0 | 82.6 | 34.6 | -64.0 | 153.8 | 43.6 | 43.6 | 34.3 |
| 2,024 | Medtronic (caution) | 15 | 6 | 40.0 | W1 | 0.0 | 26.7 |  |  |  |  |  |  |
| 2,024 | Senseonics (Eversense) | 297 | 198 | 66.7 | W1 | 0.0 | 16.8 | 47.7 | -50.0 | 150.0 | 46.5 | 48.0 | 15.2 |
| 2,025 | Abbott | 4,437 | 1,432 | 32.3 | W1; W2 | 0.6 | 77.4 | -75.0 | -87.9 | 47.9 | 72.2 | 19.1 | 54.3 |
| 2,025 | Dexcom | 4,099 | 2,333 | 56.9 | W1; W2 | 0.3 | 78.8 | -25.0 | -76.0 | 133.3 | 52.8 | 36.2 | 42.3 |
| 2,025 | Medtronic (caution) | 111 | 88 | 79.3 | W1; W2 | 0.0 | 36.0 | 45.5 | -67.3 | 164.9 | 48.9 | 50.0 | 42.0 |
| 2,025 | Senseonics (Eversense) | 240 | 158 | 65.8 | W1; W2 | 0.0 | 14.6 | -38.6 | -59.1 | 56.7 | 69.0 | 27.8 | 23.4 |
| 2,026 | Abbott | 4,497 | 1,622 | 36.1 | W2 | 0.4 | 43.1 | -57.6 | -78.5 | 113.4 | 64.4 | 20.8 | 34.9 |
| 2,026 | Dexcom | 2,319 | 1,277 | 55.1 | W2 | 0.3 | 80.9 | -42.0 | -77.1 | 100.0 | 62.0 | 30.9 | 48.5 |
| 2,026 | Medtronic (caution) | 126 | 102 | 81.0 | W2 | 0.8 | 39.7 | 6.3 | -63.0 | 150.0 | 49.0 | 40.2 | 45.1 |
| 2,026 | Senseonics (Eversense) | 130 | 86 | 66.2 | W2 | 0.8 | 28.5 | -38.0 | -60.3 | 63.2 | 64.0 | 29.1 | 43.0 |

## g. Confound (c): recall windows
| period | brand | wrong_reading_reports | pairs | median_err_pct | q1_err_pct | q3_err_pct | median_err_mgdl | pct_low | pct_high | pct_meter_under_70 | pct_meter_over_250 | median_err_pct_low_only |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | Abbott | 2,373 | 683 | -47.7 | -80.0 | 112.6 | -62.0 | 58.3 | 41.1 | 29.1 | 36.0 | -76.8 |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | Dexcom | 1,222 | 751 | 21.2 | -71.6 | 146.3 | 15.0 | 48.1 | 51.0 | 40.1 | 39.7 | -73.2 |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | Medtronic (caution) | 8 | 2 | 46.7 | 46.7 | 46.7 | 57.0 | 0.0 | 100.0 | 0.0 | 0.0 |  |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | Senseonics (Eversense) | 39 | 29 | -23.2 | -58.1 | 104.8 | -35.0 | 62.1 | 37.9 | 37.9 | 10.3 | -51.8 |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | Abbott | 5,264 | 1,854 | -58.6 | -79.5 | 105.6 | -100.0 | 65.7 | 33.8 | 20.3 | 36.1 | -73.6 |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | Dexcom | 2,764 | 1,550 | -41.9 | -77.1 | 100.0 | -95.0 | 61.2 | 38.1 | 31.1 | 48.1 | -71.4 |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | Medtronic (caution) | 142 | 114 | 16.3 | -63.0 | 159.2 | 28.5 | 48.2 | 50.9 | 42.1 | 43.9 | -63.0 |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | Senseonics (Eversense) | 151 | 102 | -35.8 | -59.9 | 70.2 | -67.5 | 64.7 | 35.3 | 29.4 | 42.2 | -55.5 |
| outside the windows | Abbott | 15,298 | 4,933 | -39.8 | -80.0 | 167.4 | -53.0 | 54.7 | 45.0 | 30.9 | 37.5 | -78.0 |
| outside the windows | Dexcom | 10,925 | 6,888 | 64.3 | -58.1 | 188.5 | 36.0 | 39.5 | 59.7 | 49.6 | 29.9 | -68.0 |
| outside the windows | Medtronic (caution) | 607 | 263 | 0.0 | -65.3 | 173.8 | 0.0 | 49.4 | 47.9 | 43.0 | 32.7 | -65.4 |
| outside the windows | Senseonics (Eversense) | 824 | 401 | -4.8 | -51.1 | 125.6 | -6.0 | 50.9 | 48.4 | 42.6 | 15.7 | -50.3 |
| all time | Abbott | 22,935 | 7,470 | -47.1 | -80.0 | 146.3 | -67.0 | 57.8 | 41.8 | 28.1 | 37.0 | -76.8 |
| all time | Dexcom | 14,911 | 9,189 | 44.1 | -64.0 | 172.3 | 29.0 | 43.8 | 55.4 | 45.7 | 33.8 | -69.2 |
| all time | Medtronic (caution) | 757 | 379 | 0.0 | -63.1 | 165.9 | 0.0 | 48.8 | 49.1 | 42.5 | 35.9 | -64.0 |
| all time | Senseonics (Eversense) | 1,014 | 532 | -19.0 | -52.8 | 116.8 | -21.5 | 54.1 | 45.3 | 39.8 | 20.5 | -51.3 |

## g. Confound (c): tests by period
| period | measure | brand_a | brand_b | n_a | n_b | median_a | median_b | iqr_a | iqr_b | median_diff_a_minus_b | median_diff_ci_low | median_diff_ci_high | cliffs_delta | cliffs_delta_ci_low | cliffs_delta_ci_high | effect_size_word | mann_whitney_p | p_text | share_a_pct | share_b_pct | risk_diff_points | risk_diff_ci_low | risk_diff_ci_high | chi_square_p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | error, % of meter | Abbott | Dexcom | 683 | 751 | -47.69 | 21.17 | -80 to 113 | -72 to 146 | -68.86 | -80.72 | -25.00 | -0.12 | -0.18 | -0.06 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | error, % of meter: sensor below meter only | Abbott | Dexcom | 398 | 361 | -76.83 | -73.23 | -86 to -61 | -86 to -50 | -3.60 | -7.99 | -0.33 | -0.09 | -0.17 | -0.01 | negligible | 0.03 | 0.026 |  |  |  |  |  |  |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | share reading low | Abbott | Dexcom | 679 | 744 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 58.62 | 48.52 | 10.09 | 4.51 | 15.11 | 0.00 |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | share meter under 70 | Abbott | Dexcom | 683 | 751 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 29.14 | 40.08 | -10.94 | -15.82 | -5.82 | 0.00 |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | error, % of meter | Abbott | Senseonics (Eversense) | 683 | 29 | -47.69 | -23.20 | -80 to 113 | -58 to 105 | -24.49 | -115.63 | 6.01 | -0.14 | -0.29 | 0.01 | negligible | 0.19 | 0.195 |  |  |  |  |  |  |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | error, % of meter: sensor below meter only | Abbott | Senseonics (Eversense) | 398 | 18 | -76.83 | -51.77 | -86 to -61 | -68 to -37 |  |  |  |  |  |  |  |  | too few |  |  |  |  |  |  |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | share reading low | Abbott | Senseonics (Eversense) | 679 | 29 |  |  |  |  |  |  |  |  |  |  |  |  | 0.711 | 58.62 | 62.07 | -3.45 | -21.00 | 16.44 | 0.71 |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | share meter under 70 | Abbott | Senseonics (Eversense) | 683 | 29 |  |  |  |  |  |  |  |  |  |  |  |  | 0.309 | 29.14 | 37.93 | -8.79 | -26.33 | 8.16 | 0.31 |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | error, % of meter | Dexcom | Senseonics (Eversense) | 751 | 29 | 21.17 | -23.20 | -72 to 146 | -58 to 105 | 44.37 | -62.22 | 74.69 | 0.02 | -0.14 | 0.18 | negligible | 0.83 | 0.826 |  |  |  |  |  |  |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | error, % of meter: sensor below meter only | Dexcom | Senseonics (Eversense) | 361 | 18 | -73.23 | -51.77 | -86 to -50 | -68 to -37 |  |  |  |  |  |  |  |  | too few |  |  |  |  |  |  |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | share reading low | Dexcom | Senseonics (Eversense) | 744 | 29 |  |  |  |  |  |  |  |  |  |  |  |  | 0.152 | 48.52 | 62.07 | -13.55 | -32.09 | 5.13 | 0.15 |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | share meter under 70 | Dexcom | Senseonics (Eversense) | 751 | 29 |  |  |  |  |  |  |  |  |  |  |  |  | 0.817 | 40.08 | 37.93 | 2.15 | -15.36 | 18.86 | 0.82 |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | error, % of meter | Abbott | Medtronic (caution) | 683 | 2 | -47.69 | 46.72 | -80 to 113 | 47 to 47 |  |  |  |  |  |  |  |  | too few |  |  |  |  |  |  |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | error, % of meter: sensor below meter only | Abbott | Medtronic (caution) | 398 | 0 | -76.83 |  | -86 to -61 |  |  |  |  |  |  |  |  |  | too few |  |  |  |  |  |  |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | share reading low | Abbott | Medtronic (caution) | 679 | 2 |  |  |  |  |  |  |  |  |  |  |  |  | too few | 58.62 | 0.00 |  |  |  |  |
| W1: Jul 2024 recall, Libre 3 falsely HIGH (2024-07-24 to 2025-01-23) | share meter under 70 | Abbott | Medtronic (caution) | 683 | 2 |  |  |  |  |  |  |  |  |  |  |  |  | too few | 29.14 | 0.00 |  |  |  |  |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | error, % of meter | Abbott | Dexcom | 1,854 | 1,550 | -58.57 | -41.91 | -79 to 106 | -77 to 100 | -16.66 | -22.15 | -10.40 | -0.05 | -0.09 | -0.01 | negligible | 0.01 | 0.008 |  |  |  |  |  |  |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | error, % of meter: sensor below meter only | Abbott | Dexcom | 1,219 | 948 | -73.57 | -71.41 | -84 to -60 | -86 to -50 | -2.16 | -5.24 | -0.04 | -0.06 | -0.11 | -0.01 | negligible | 0.02 | 0.018 |  |  |  |  |  |  |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | share reading low | Abbott | Dexcom | 1,846 | 1,539 |  |  |  |  |  |  |  |  |  |  |  |  | 0.007 | 66.03 | 61.60 | 4.44 | 1.20 | 7.61 | 0.01 |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | share meter under 70 | Abbott | Dexcom | 1,854 | 1,550 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 20.33 | 31.10 | -10.76 | -13.47 | -7.80 | 0.00 |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | error, % of meter | Abbott | Senseonics (Eversense) | 1,854 | 102 | -58.57 | -35.82 | -79 to 106 | -60 to 68 | -22.75 | -37.27 | -12.21 | -0.18 | -0.26 | -0.10 | small | 0.00 | 0.002 |  |  |  |  |  |  |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | error, % of meter: sensor below meter only | Abbott | Senseonics (Eversense) | 1,219 | 66 | -73.57 | -55.47 | -84 to -60 | -69 to -38 | -18.10 | -28.17 | -13.27 | -0.49 | -0.60 | -0.38 | large | 0.00 | < 0.001 |  |  |  |  |  |  |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | share reading low | Abbott | Senseonics (Eversense) | 1,846 | 102 |  |  |  |  |  |  |  |  |  |  |  |  | 0.783 | 66.03 | 64.71 | 1.33 | -7.56 | 10.96 | 0.78 |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | share meter under 70 | Abbott | Senseonics (Eversense) | 1,854 | 102 |  |  |  |  |  |  |  |  |  |  |  |  | 0.028 | 20.33 | 29.41 | -9.08 | -17.90 | -0.92 | 0.03 |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | error, % of meter | Dexcom | Senseonics (Eversense) | 1,550 | 102 | -41.91 | -35.82 | -77 to 100 | -60 to 68 | -6.09 | -21.56 | 4.33 | -0.09 | -0.18 | -0.01 | negligible | 0.12 | 0.123 |  |  |  |  |  |  |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | error, % of meter: sensor below meter only | Dexcom | Senseonics (Eversense) | 948 | 66 | -71.41 | -55.47 | -86 to -50 | -69 to -38 | -15.94 | -26.03 | -10.49 | -0.36 | -0.47 | -0.25 | medium | 0.00 | < 0.001 |  |  |  |  |  |  |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | share reading low | Dexcom | Senseonics (Eversense) | 1,539 | 102 |  |  |  |  |  |  |  |  |  |  |  |  | 0.532 | 61.60 | 64.71 | -3.11 | -12.97 | 6.30 | 0.53 |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | share meter under 70 | Dexcom | Senseonics (Eversense) | 1,550 | 102 |  |  |  |  |  |  |  |  |  |  |  |  | 0.722 | 31.10 | 29.41 | 1.69 | -7.72 | 11.29 | 0.72 |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | error, % of meter | Abbott | Medtronic (caution) | 1,854 | 114 | -58.57 | 16.34 | -79 to 106 | -63 to 157 | -74.91 | -139.41 | -18.04 | -0.22 | -0.32 | -0.12 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | error, % of meter: sensor below meter only | Abbott | Medtronic (caution) | 1,219 | 55 | -73.57 | -63.00 | -84 to -60 | -76 to -55 | -10.57 | -12.00 | -5.14 | -0.21 | -0.36 | -0.05 | small | 0.01 | 0.007 |  |  |  |  |  |  |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | share reading low | Abbott | Medtronic (caution) | 1,846 | 113 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 66.03 | 48.67 | 17.36 | 8.35 | 26.61 | 0.00 |
| W2: Nov 2025 recall, Libre 3 falsely LOW (2025-11-24 onward) | share meter under 70 | Abbott | Medtronic (caution) | 1,854 | 114 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 20.33 | 42.11 | -21.77 | -31.01 | -11.74 | 0.00 |
| outside the windows | error, % of meter | Abbott | Dexcom | 4,933 | 6,888 | -39.79 | 64.35 | -80 to 167 | -58 to 188 | -104.14 | -110.69 | -95.99 | -0.16 | -0.18 | -0.13 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| outside the windows | error, % of meter: sensor below meter only | Abbott | Dexcom | 2,698 | 2,720 | -77.97 | -68.00 | -87 to -60 | -84 to -47 | -9.97 | -11.62 | -8.47 | -0.19 | -0.21 | -0.16 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| outside the windows | share reading low | Abbott | Dexcom | 4,916 | 6,834 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 54.88 | 39.80 | 15.08 | 13.43 | 16.86 | 0.00 |
| outside the windows | share meter under 70 | Abbott | Dexcom | 4,933 | 6,888 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 30.89 | 49.64 | -18.74 | -20.49 | -16.98 | 0.00 |
| outside the windows | error, % of meter | Abbott | Senseonics (Eversense) | 4,933 | 401 | -39.79 | -4.84 | -80 to 167 | -51 to 126 | -34.95 | -65.02 | -15.45 | -0.14 | -0.18 | -0.10 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| outside the windows | error, % of meter: sensor below meter only | Abbott | Senseonics (Eversense) | 2,698 | 204 | -77.97 | -50.27 | -87 to -60 | -63 to -37 | -27.69 | -31.67 | -24.12 | -0.59 | -0.64 | -0.54 | large | 0.00 | < 0.001 |  |  |  |  |  |  |
| outside the windows | share reading low | Abbott | Senseonics (Eversense) | 4,916 | 398 |  |  |  |  |  |  |  |  |  |  |  |  | 0.162 | 54.88 | 51.26 | 3.63 | -1.62 | 8.52 | 0.16 |
| outside the windows | share meter under 70 | Abbott | Senseonics (Eversense) | 4,933 | 401 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 30.89 | 42.64 | -11.75 | -16.21 | -6.70 | 0.00 |
| outside the windows | error, % of meter | Dexcom | Senseonics (Eversense) | 6,888 | 401 | 64.35 | -4.84 | -58 to 188 | -51 to 126 | 69.18 | 40.36 | 88.52 | 0.08 | 0.03 | 0.13 | negligible | 0.01 | 0.007 |  |  |  |  |  |  |
| outside the windows | error, % of meter: sensor below meter only | Dexcom | Senseonics (Eversense) | 2,720 | 204 | -68.00 | -50.27 | -84 to -47 | -63 to -37 | -17.73 | -21.55 | -13.72 | -0.38 | -0.45 | -0.31 | medium | 0.00 | < 0.001 |  |  |  |  |  |  |
| outside the windows | share reading low | Dexcom | Senseonics (Eversense) | 6,834 | 398 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 39.80 | 51.26 | -11.46 | -16.51 | -6.80 | 0.00 |
| outside the windows | share meter under 70 | Dexcom | Senseonics (Eversense) | 6,888 | 401 |  |  |  |  |  |  |  |  |  |  |  |  | 0.006 | 49.64 | 42.64 | 6.99 | 2.00 | 12.09 | 0.01 |
| outside the windows | error, % of meter | Abbott | Medtronic (caution) | 4,933 | 263 | -39.79 | 0.00 | -80 to 167 | -65 to 173 | -39.79 | -87.69 | -13.17 | -0.09 | -0.15 | -0.03 | negligible | 0.01 | 0.014 |  |  |  |  |  |  |
| outside the windows | error, % of meter: sensor below meter only | Abbott | Medtronic (caution) | 2,698 | 130 | -77.97 | -65.40 | -87 to -60 | -81 to -40 | -12.57 | -23.60 | -5.00 | -0.27 | -0.37 | -0.17 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| outside the windows | share reading low | Abbott | Medtronic (caution) | 4,916 | 256 |  |  |  |  |  |  |  |  |  |  |  |  | 0.199 | 54.88 | 50.78 | 4.10 | -2.01 | 9.92 | 0.20 |
| outside the windows | share meter under 70 | Abbott | Medtronic (caution) | 4,933 | 263 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 30.89 | 42.97 | -12.07 | -17.84 | -6.23 | 0.00 |
| all time | error, % of meter | Abbott | Dexcom | 7,470 | 9,189 | -47.12 | 44.07 | -80 to 146 | -64 to 172 | -91.18 | -97.63 | -86.32 | -0.15 | -0.16 | -0.13 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| all time | error, % of meter: sensor below meter only | Abbott | Dexcom | 4,315 | 4,029 | -76.77 | -69.18 | -86 to -60 | -85 to -48 | -7.59 | -9.11 | -6.11 | -0.15 | -0.17 | -0.12 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| all time | share reading low | Abbott | Dexcom | 7,441 | 9,117 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 57.99 | 44.19 | 13.80 | 12.27 | 15.37 | 0.00 |
| all time | share meter under 70 | Abbott | Dexcom | 7,470 | 9,189 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 28.11 | 45.73 | -17.62 | -18.98 | -16.23 | 0.00 |
| all time | error, % of meter | Abbott | Senseonics (Eversense) | 7,470 | 532 | -47.12 | -19.03 | -80 to 146 | -53 to 117 | -28.09 | -45.75 | -18.88 | -0.16 | -0.20 | -0.13 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| all time | error, % of meter: sensor below meter only | Abbott | Senseonics (Eversense) | 4,315 | 288 | -76.77 | -51.26 | -86 to -60 | -65 to -37 | -25.51 | -28.95 | -22.39 | -0.56 | -0.61 | -0.51 | large | 0.00 | < 0.001 |  |  |  |  |  |  |
| all time | share reading low | Abbott | Senseonics (Eversense) | 7,441 | 529 |  |  |  |  |  |  |  |  |  |  |  |  | 0.111 | 57.99 | 54.44 | 3.55 | -0.60 | 8.03 | 0.11 |
| all time | share meter under 70 | Abbott | Senseonics (Eversense) | 7,470 | 532 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 28.11 | 39.85 | -11.74 | -16.13 | -7.78 | 0.00 |
| all time | error, % of meter | Dexcom | Senseonics (Eversense) | 9,189 | 532 | 44.07 | -19.03 | -64 to 172 | -53 to 117 | 63.10 | 43.86 | 73.60 | 0.05 | 0.01 | 0.09 | negligible | 0.06 | 0.064 |  |  |  |  |  |  |
| all time | error, % of meter: sensor below meter only | Dexcom | Senseonics (Eversense) | 4,029 | 288 | -69.18 | -51.26 | -85 to -48 | -65 to -37 | -17.92 | -21.42 | -14.46 | -0.38 | -0.43 | -0.33 | medium | 0.00 | < 0.001 |  |  |  |  |  |  |
| all time | share reading low | Dexcom | Senseonics (Eversense) | 9,117 | 529 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 44.19 | 54.44 | -10.25 | -14.49 | -5.90 | 0.00 |
| all time | share meter under 70 | Dexcom | Senseonics (Eversense) | 9,189 | 532 |  |  |  |  |  |  |  |  |  |  |  |  | 0.008 | 45.73 | 39.85 | 5.88 | 1.64 | 9.92 | 0.01 |
| all time | error, % of meter | Abbott | Medtronic (caution) | 7,470 | 379 | -47.12 | 0.00 | -80 to 146 | -63 to 164 | -47.12 | -95.52 | -22.77 | -0.13 | -0.18 | -0.08 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| all time | error, % of meter: sensor below meter only | Abbott | Medtronic (caution) | 4,315 | 185 | -76.77 | -64.02 | -86 to -60 | -80 to -44 | -12.75 | -15.38 | -7.25 | -0.25 | -0.33 | -0.17 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| all time | share reading low | Abbott | Medtronic (caution) | 7,441 | 371 |  |  |  |  |  |  |  |  |  |  |  |  | 0.002 | 57.99 | 49.87 | 8.12 | 3.29 | 13.46 | 0.00 |
| all time | share meter under 70 | Abbott | Medtronic (caution) | 7,470 | 379 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 28.11 | 42.48 | -14.37 | -19.16 | -9.02 | 0.00 |

## g. Confound (c): Abbott vs Dexcom by year
| year | measure | brand_a | brand_b | n_a | n_b | median_a | median_b | iqr_a | iqr_b | median_diff_a_minus_b | median_diff_ci_low | median_diff_ci_high | cliffs_delta | cliffs_delta_ci_low | cliffs_delta_ci_high | effect_size_word | mann_whitney_p | p_text | share_a_pct | share_b_pct | risk_diff_points | risk_diff_ci_low | risk_diff_ci_high | chi_square_p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2,018 | error, % of meter | Abbott | Dexcom | 249 | 287 | 27.89 | 105.36 | -72 to 245 | -1 to 232 | -77.46 | -149.84 | -33.05 | -0.18 | -0.29 | -0.08 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| 2,018 | share reading low | Abbott | Dexcom | 249 | 284 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 46.59 | 25.35 | 21.23 | 13.75 | 29.22 | 0.00 |
| 2,019 | error, % of meter | Abbott | Dexcom | 426 | 445 | -33.33 | 82.89 | -71 to 175 | -48 to 181 | -116.23 | -139.67 | -69.40 | -0.19 | -0.26 | -0.12 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| 2,019 | share reading low | Abbott | Dexcom | 425 | 443 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 53.41 | 34.09 | 19.33 | 12.82 | 25.78 | 0.00 |
| 2,020 | error, % of meter | Abbott | Dexcom | 329 | 369 | -42.86 | 60.00 | -75 to 213 | -55 to 193 | -102.86 | -127.11 | -83.33 | -0.14 | -0.24 | -0.06 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| 2,020 | share reading low | Abbott | Dexcom | 327 | 368 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 59.33 | 39.13 | 20.20 | 12.99 | 27.91 | 0.00 |
| 2,021 | error, % of meter | Abbott | Dexcom | 673 | 476 | 12.05 | 49.35 | -73 to 200 | -68 to 201 | -37.30 | -90.38 | 18.12 | -0.01 | -0.09 | 0.06 | negligible | 0.71 | 0.710 |  |  |  |  |  |  |
| 2,021 | share reading low | Abbott | Dexcom | 671 | 475 |  |  |  |  |  |  |  |  |  |  |  |  | 0.191 | 49.18 | 45.26 | 3.92 | -2.14 | 9.31 | 0.19 |
| 2,022 | error, % of meter | Abbott | Dexcom | 710 | 708 | 45.94 | 84.92 | -75 to 219 | -44 to 219 | -38.98 | -87.15 | -9.76 | -0.13 | -0.18 | -0.06 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| 2,022 | share reading low | Abbott | Dexcom | 705 | 705 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 46.67 | 34.47 | 12.20 | 7.09 | 17.16 | 0.00 |
| 2,023 | error, % of meter | Abbott | Dexcom | 886 | 1,355 | 26.76 | 90.78 | -73 to 200 | -39 to 233 | -64.02 | -111.93 | -28.07 | -0.16 | -0.20 | -0.11 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| 2,023 | share reading low | Abbott | Dexcom | 880 | 1,346 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 48.07 | 32.17 | 15.90 | 11.74 | 19.92 | 0.00 |
| 2,024 | error, % of meter | Abbott | Dexcom | 1,131 | 1,538 | -39.44 | 34.57 | -78 to 148 | -64 to 154 | -74.01 | -87.14 | -51.08 | -0.11 | -0.16 | -0.07 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| 2,024 | share reading low | Abbott | Dexcom | 1,127 | 1,520 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 54.21 | 44.08 | 10.14 | 6.28 | 14.02 | 0.00 |
| 2,025 | error, % of meter | Abbott | Dexcom | 1,432 | 2,333 | -75.00 | -25.00 | -88 to 48 | -76 to 133 | -50.00 | -60.17 | -43.16 | -0.27 | -0.31 | -0.23 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| 2,025 | share reading low | Abbott | Dexcom | 1,431 | 2,316 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 72.26 | 53.20 | 19.06 | 16.06 | 22.25 | 0.00 |
| 2,026 | error, % of meter | Abbott | Dexcom | 1,622 | 1,277 | -57.61 | -41.96 | -79 to 113 | -77 to 100 | -15.66 | -22.50 | -8.59 | -0.03 | -0.07 | 0.01 | negligible | 0.16 | 0.158 |  |  |  |  |  |  |
| 2,026 | share reading low | Abbott | Dexcom | 1,614 | 1,266 |  |  |  |  |  |  |  |  |  |  |  |  | 0.226 | 64.75 | 62.56 | 2.19 | -1.19 | 5.88 | 0.23 |

## g. Product lines
| product_line | brand | wrong_reading_reports | pairs | pct_fda_death | pct_outcome_hospital_or_er | median_err_pct | q1_err_pct | q3_err_pct | median_err_mgdl | pct_low | pct_high | pct_meter_under_70 | pct_meter_over_250 | pct_zone_DE_computed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Libre 3 Plus | Abbott | 3,118 | 1,061 | 0.5 | 51.2 | -62.9 | -81.1 | 64.2 | -108.0 | 71.4 | 28.3 | 15.6 | 39.5 | 37.7 |
| Libre 3 | Abbott | 4,568 | 1,321 | 0.5 | 69.0 | -66.7 | -87.0 | 84.1 | -144.0 | 66.7 | 32.9 | 23.4 | 48.4 | 53.8 |
| Libre 2 Plus | Abbott | 1,588 | 650 | 0.1 | 55.9 | -63.4 | -81.5 | 137.1 | -116.5 | 63.5 | 36.0 | 24.0 | 40.8 | 46.3 |
| Libre 2 | Abbott | 8,589 | 2,462 | 0.1 | 69.6 | 31.2 | -76.1 | 186.1 | 25.0 | 47.7 | 52.0 | 35.6 | 30.4 | 42.5 |
| Libre 14 day | Abbott | 4,059 | 1,499 | 0.1 | 73.2 | -36.8 | -74.3 | 174.8 | -57.0 | 55.9 | 43.6 | 29.9 | 35.1 | 39.5 |
| Libre (other) | Abbott | 903 | 436 | 0.1 | 75.1 | -1.2 | -68.5 | 215.3 | -1.5 | 50.2 | 49.5 | 31.9 | 35.6 | 44.5 |
| Dexcom G7 | Dexcom | 6,677 | 3,760 | 0.2 | 79.7 | -29.0 | -76.0 | 125.0 | -57.0 | 54.5 | 44.5 | 36.1 | 43.3 | 37.7 |
| Dexcom G6 | Dexcom | 6,752 | 4,499 | 0.1 | 77.5 | 66.0 | -54.2 | 200.0 | 37.0 | 38.6 | 60.9 | 49.8 | 29.6 | 34.7 |
| Dexcom G5 | Dexcom | 915 | 580 | 0.1 | 72.6 | 107.6 | -34.3 | 238.3 | 45.0 | 29.5 | 69.5 | 64.1 | 18.4 | 28.4 |
| Dexcom G4 | Dexcom | 327 | 212 | 0.0 | 59.9 | 109.4 | 49.5 | 233.3 | 49.5 | 19.8 | 79.7 | 71.7 | 13.2 | 30.2 |
| Eversense | Senseonics (Eversense) | 1,014 | 532 | 0.1 | 17.5 | -19.0 | -52.8 | 116.8 | -21.5 | 54.1 | 45.3 | 39.8 | 20.5 | 16.0 |
| Simplera | Medtronic (caution) | 35 | 28 | 0.0 | 31.4 | 2.8 | -64.4 | 150.0 | -35.5 | 50.0 | 50.0 | 46.4 | 39.3 | 32.1 |
| unspecified | Medtronic (caution) | 1,105 | 526 | 0.1 | 49.8 | 30.5 | -58.4 | 186.4 | 27.0 | 43.9 | 54.2 | 44.1 | 28.1 | 33.8 |

## g. Product line tests
| measure | line_a | line_b | n_a | n_b | median_a | median_b | iqr_a | iqr_b | median_diff_a_minus_b | median_diff_ci_low | median_diff_ci_high | cliffs_delta | cliffs_delta_ci_low | cliffs_delta_ci_high | effect_size_word | mann_whitney_p | p_text | share_a_pct | share_b_pct | risk_diff_points | risk_diff_ci_low | risk_diff_ci_high | chi_square_p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| error, % of meter | Libre 3 | Libre 2 | 1,321 | 2,462 | -66.67 | 31.23 | -87 to 84 | -76 to 186 | -97.89 | -117.04 | -66.91 | -0.26 | -0.29 | -0.22 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| share reading low | Libre 3 | Libre 2 | 1,315 | 2,454 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 67.00 | 47.84 | 19.16 | 15.78 | 22.46 | 0.00 |
| error, % of meter | Libre 3 Plus | Libre 3 | 1,061 | 1,321 | -62.94 | -66.67 | -81 to 64 | -87 to 84 | 3.73 | -1.05 | 8.75 | 0.07 | 0.03 | 0.12 | negligible | 0.00 | 0.003 |  |  |  |  |  |  |
| share reading low | Libre 3 Plus | Libre 3 | 1,058 | 1,315 |  |  |  |  |  |  |  |  |  |  |  |  | 0.015 | 71.64 | 67.00 | 4.65 | 1.18 | 8.52 | 0.01 |
| error, % of meter | Dexcom G7 | Dexcom G6 | 3,760 | 4,499 | -29.02 | 66.04 | -76 to 125 | -54 to 200 | -95.05 | -102.11 | -86.91 | -0.20 | -0.23 | -0.18 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| share reading low | Dexcom G7 | Dexcom G6 | 3,723 | 4,473 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 55.01 | 38.79 | 16.22 | 14.05 | 18.42 | 0.00 |
| error, % of meter | Libre 3 | Dexcom G7 | 1,321 | 3,760 | -66.67 | -29.02 | -87 to 84 | -76 to 125 | -37.65 | -43.77 | -31.48 | -0.19 | -0.23 | -0.15 | small | 0.00 | < 0.001 |  |  |  |  |  |  |
| share reading low | Libre 3 | Dexcom G7 | 1,315 | 3,723 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 67.00 | 55.01 | 11.99 | 9.04 | 14.96 | 0.00 |
| error, % of meter | Libre 2 | Dexcom G6 | 2,462 | 4,499 | 31.23 | 66.04 | -76 to 186 | -54 to 200 | -34.81 | -61.65 | -14.84 | -0.11 | -0.14 | -0.08 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| share reading low | Libre 2 | Dexcom G6 | 2,454 | 4,473 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 47.84 | 38.79 | 9.05 | 6.78 | 11.40 | 0.00 |

## g. Demographics: fill rates
| cut | tier | group | n | pct_age_filled | pct_sex_filled | pct_both_filled | pct_sex_undisclosed | pct_reporter_patient_or_family |
|---|---|---|---|---|---|---|---|---|
| brand | serious | Abbott | 22,935 | 19.1 | 18.2 | 9.2 | 0.0 | 2.2 |
| brand | serious | Dexcom | 14,911 | 93.2 | 78.1 | 74.5 | 0.3 | 6.3 |
| brand | serious | Medtronic (caution) | 757 | 88.0 | 23.5 | 23.5 | 0.0 | 44.0 |
| brand | serious | Senseonics (Eversense) | 1,014 | 47.3 | 35.2 | 34.3 | 0.4 | 0.1 |
| brand | serious | Other makers | 50 | 66.0 | 4.0 | 4.0 | 0.0 | 36.0 |
| brand | serious | All | 39,667 | 49.1 | 41.2 | 34.7 | 0.1 | 4.5 |
| brand | sample (weighted) | Abbott | 797 | 4.1 | 5.7 | 3.5 | 0.0 | 0.0 |
| brand | sample (weighted) | Dexcom | 634 | 95.9 | 56.3 | 54.3 | 0.2 | 0.2 |
| brand | sample (weighted) | Medtronic (caution) | 40 | 44.0 | 14.6 | 14.6 | 0.0 | 0.9 |
| brand | sample (weighted) | Senseonics (Eversense) | 87 | 77.2 | 75.3 | 75.3 | 0.0 | 0.0 |
| brand | sample (weighted) | Other makers | 1 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| brand | sample (weighted) | All | 1,559 | 48.4 | 30.1 | 28.0 | 0.1 | 0.1 |
| model outcome | serious | none | 4,400 | 47.5 | 42.5 | 34.3 |  |  |
| model outcome | serious | symptoms_only | 2,443 | 25.9 | 22.6 | 16.8 |  |  |
| model outcome | serious | hypoglycemia | 5,196 | 51.4 | 37.4 | 31.2 |  |  |
| model outcome | serious | hospital_or_er | 27,415 | 50.8 | 43.3 | 36.8 |  |  |
| model outcome | serious | death | 47 | 38.3 | 38.3 | 36.2 |  |  |
| model outcome | serious | not_stated | 164 | 67.7 | 60.4 | 53.7 |  |  |
| FDA event type | serious | Injury | 39,588 | 49.1 | 41.2 | 34.7 |  |  |
| FDA event type | serious | Death | 79 | 36.7 | 39.2 | 34.2 |  |  |
| FDA outcome code | serious | Required Intervention | 19,184 | 19.3 | 15.6 | 6.9 |  |  |
| FDA outcome code | serious | Hospitalization | 6,201 | 72.5 | 62.6 | 58.0 |  |  |
| FDA outcome code | serious | Life Threatening | 927 | 73.1 | 61.3 | 56.0 |  |  |
| FDA outcome code | serious | Death | 78 | 35.9 | 37.2 | 33.3 |  |  |
| FDA outcome code | serious | Other | 16,903 | 80.1 | 68.8 | 64.6 |  |  |
| FDA outcome code | serious | Disability | 209 | 91.4 | 84.7 | 77.5 |  |  |
| FDA outcome code | serious | none stated | 2,715 | 62.8 | 54.4 | 46.7 |  |  |
| brand x FDA event type | serious | Abbott / Injury | 22,879 | 19.2 | 18.2 | 9.2 |  |  |
| brand x FDA event type | serious | Abbott / Death | 56 | 16.1 | 16.1 | 14.3 |  |  |
| brand x FDA event type | serious | Dexcom / Injury | 14,890 | 93.2 | 78.1 | 74.5 |  |  |
| brand x FDA event type | serious | Dexcom / Death | 21 | 85.7 | 95.2 | 81.0 |  |  |
| brand x FDA event type | serious | Medtronic (caution) / Injury | 756 | 88.0 | 23.4 | 23.4 |  |  |
| brand x FDA event type | serious | Senseonics (Eversense) / Injury | 1,013 | 47.3 | 35.1 | 34.3 |  |  |
| year | serious | 2018 | 934 | 84.5 | 0.0 | 0.0 |  |  |
| year | serious | 2019 | 1,464 | 78.3 | 0.1 | 0.1 |  |  |
| year | serious | 2020 | 1,391 | 76.9 | 0.4 | 0.1 |  |  |
| year | serious | 2021 | 2,506 | 57.0 | 20.3 | 8.7 |  |  |
| year | serious | 2022 | 3,432 | 35.1 | 54.2 | 34.5 |  |  |
| year | serious | 2023 | 5,752 | 37.5 | 44.3 | 37.0 |  |  |
| year | serious | 2024 | 7,027 | 39.7 | 44.3 | 39.1 |  |  |
| year | serious | 2025 | 8,887 | 50.8 | 55.0 | 49.8 |  |  |
| year | serious | 2026 | 7,074 | 45.8 | 48.5 | 43.0 |  |  |

## g. Demographics: age and sex by brand
| brand | n_with_age | median_age | q1_age | q3_age | p10_age | p90_age | pct_age_<18 | pct_age_18-39 | pct_age_40-64 | pct_age_65+ | n_with_sex | pct_female_of_filled |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Abbott | 4,391 | 58.0 | 42.0 | 69.0 | 19.0 | 77.0 | 9.3 | 13.2 | 41.7 | 35.8 | 4,169 | 46.6 |
| Dexcom | 13,892 | 53.0 | 32.0 | 67.0 | 15.0 | 75.0 | 13.2 | 19.2 | 38.3 | 29.3 | 11,650 | 52.9 |
| Medtronic (caution) | 666 | 54.0 | 39.0 | 64.0 | 25.5 | 72.0 | 5.7 | 19.7 | 49.7 | 24.9 | 178 | 50.6 |
| Senseonics (Eversense) | 480 | 57.0 | 43.0 | 64.0 | 33.0 | 70.1 | 1.5 | 17.7 | 57.1 | 23.8 | 357 | 48.2 |
| All | 19,462 | 54.0 | 35.0 | 67.0 | 16.0 | 76.0 | 11.7 | 17.8 | 39.9 | 30.5 | 16,356 | 51.1 |

## g. Demographics: age and sex by brand, tests
| k_groups | n | kruskal_H | kruskal_p | epsilon_squared | p_text | measure | group_a | group_b | n_a | n_b | median_a | median_b | iqr_a | iqr_b | median_diff_a_minus_b | median_diff_ci_low | median_diff_ci_high | cliffs_delta | cliffs_delta_ci_low | cliffs_delta_ci_high | effect_size_word | mann_whitney_p | share_a_pct | share_b_pct | risk_diff_points | risk_diff_ci_low | risk_diff_ci_high | chi_square_p | chi2 | df | cramers_v |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4.000 | 19,429 | 158.150 | 0.000 | 0.008 | < 0.001 | age, years, across brands |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  | < 0.001 | age, years | Abbott | Dexcom | 4,391 | 13,892 | 58.000 | 53.000 | 42 to 69 | 32 to 67 | 5.000 | 4.000 | 6.000 | 0.123 | 0.104 | 0.142 | negligible | 0.000 |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  | < 0.001 | share female (of filled) | Abbott | Dexcom | 4,169 | 11,650 |  |  |  |  |  |  |  |  |  |  |  |  | 46.558 | 52.867 | -6.309 | -8.101 | -4.687 | 0.000 |  |  |  |
|  |  |  |  |  | < 0.001 | age, years | Abbott | Medtronic (caution) | 4,391 | 666.000 | 58.000 | 54.000 | 42 to 69 | 39 to 64 | 4.000 | 2.000 | 5.500 | 0.110 | 0.065 | 0.154 | negligible | 0.000 |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  | 0.294 | share female (of filled) | Abbott | Medtronic (caution) | 4,169 | 178.000 |  |  |  |  |  |  |  |  |  |  |  |  | 46.558 | 50.562 | -4.004 | -11.510 | 3.769 | 0.294 |  |  |  |
|  |  |  |  |  | 0.007 | age, years | Abbott | Senseonics (Eversense) | 4,391 | 480.000 | 58.000 | 57.000 | 42 to 69 | 43 to 64 | 1.000 | 0.000 | 3.500 | 0.075 | 0.028 | 0.124 | negligible | 0.007 |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  | 0.556 | share female (of filled) | Abbott | Senseonics (Eversense) | 4,169 | 357.000 |  |  |  |  |  |  |  |  |  |  |  |  | 46.558 | 48.179 | -1.621 | -6.941 | 4.156 | 0.556 |  |  |  |
|  |  |  |  |  | 0.142 | age, years | Dexcom | Medtronic (caution) | 13,892 | 666.000 | 53.000 | 54.000 | 32 to 67 | 39 to 64 | -1.000 | -3.000 | 0.000 | -0.034 | -0.071 | 0.003 | negligible | 0.142 |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  | 0.541 | share female (of filled) | Dexcom | Medtronic (caution) | 11,650 | 178.000 |  |  |  |  |  |  |  |  |  |  |  |  | 52.867 | 50.562 | 2.305 | -5.129 | 9.874 | 0.541 |  |  |  |
|  |  |  |  |  | 0.003 | age, years | Dexcom | Senseonics (Eversense) | 13,892 | 480.000 | 53.000 | 57.000 | 32 to 67 | 43 to 64 | -4.000 | -5.000 | -2.000 | -0.079 | -0.117 | -0.040 | negligible | 0.003 |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  | 0.081 | share female (of filled) | Dexcom | Senseonics (Eversense) | 11,650 | 357.000 |  |  |  |  |  |  |  |  |  |  |  |  | 52.867 | 48.179 | 4.688 | -0.563 | 9.887 | 0.081 |  |  |  |
|  |  |  |  |  | 0.120 | age, years | Medtronic (caution) | Senseonics (Eversense) | 666.000 | 480.000 | 54.000 | 57.000 | 39 to 64 | 43 to 64 | -3.000 | -4.500 | 0.000 | -0.054 | -0.124 | 0.012 | negligible | 0.120 |  |  |  |  |  |  |  |  |  |
|  |  |  |  |  | 0.603 | share female (of filled) | Medtronic (caution) | Senseonics (Eversense) | 178.000 | 357.000 |  |  |  |  |  |  |  |  |  |  |  |  | 50.562 | 48.179 | 2.383 | -6.877 | 11.367 | 0.603 |  |  |  |
| 4.000 | 16,354 |  |  |  | < 0.001 | sex (female / male) across brands |  |  |  |  |  |  |  |  |  |  |  |  |  |  | negligible |  |  |  |  |  |  | 0.000 | 50.211 | 3.000 | 0.055 |
| 4.000 | 19,429 |  |  |  | < 0.001 | age group mix across brands |  |  |  |  |  |  |  |  |  |  |  |  |  |  | negligible |  |  |  |  |  |  | 0.000 | 302.263 | 9.000 | 0.072 |

## g. Demographics: by age group and sex
| cut | brand | group | wrong_reading_reports | pairs | pct_fingerstick_yes | pct_ate_carbs | pct_took_insulin | pct_sought_care | pct_outcome_hypoglycemia | pct_outcome_hospital_or_er | pct_outcome_death | pct_fda_death | pct_fda_hospitalization | pct_fda_life_threatening | pct_reporter_patient_or_family | median_err_pct | q1_err_pct | q3_err_pct | median_err_mgdl | pct_low | pct_high | median_sensor_mgdl | median_meter_mgdl | pct_zone_DE_computed | pct_meter_<54 | pct_meter_54-69 | pct_meter_70-180 | pct_meter_181-250 | pct_meter_>250 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| age group | All | <18 | 2,286 | 1,373 | 84.3 | 33.3 | 13.1 | 42.4 | 19.6 | 67.3 | 0.1 | 0.0 | 23.9 | 4.0 | 6.0 | -31.8 | -71.2 | 137.6 | -69.0 | 54.6 | 44.9 | 118.0 | 189.0 | 36.3 | 29.4 | 7.7 | 12.4 | 4.6 | 45.9 |
| age group | All | 18-39 | 3,471 | 2,030 | 78.2 | 30.8 | 6.7 | 48.4 | 14.5 | 74.9 | 0.1 | 0.2 | 25.8 | 5.1 | 8.6 | 25.5 | -66.3 | 148.0 | 20.5 | 47.7 | 51.9 | 110.0 | 120.0 | 32.6 | 36.6 | 5.9 | 13.3 | 5.2 | 39.0 |
| age group | All | 40-64 | 7,770 | 4,124 | 73.8 | 33.3 | 5.9 | 44.0 | 13.4 | 71.0 | 0.1 | 0.2 | 22.4 | 3.1 | 8.5 | 30.8 | -65.5 | 172.7 | 20.0 | 46.8 | 52.2 | 104.0 | 107.5 | 34.9 | 36.7 | 5.7 | 18.9 | 6.6 | 32.0 |
| age group | All | 65+ | 5,935 | 3,205 | 73.0 | 35.0 | 5.6 | 42.8 | 11.4 | 72.2 | 0.1 | 0.2 | 22.2 | 2.8 | 6.2 | 50.0 | -61.9 | 200.0 | 30.0 | 42.6 | 56.6 | 104.0 | 86.0 | 37.4 | 40.5 | 6.4 | 18.8 | 6.9 | 27.4 |
| age group | Abbott | <18 | 409 | 196 | 77.0 | 42.1 | 20.0 | 32.0 | 21.3 | 62.1 | 0.0 | 0.0 | 11.7 | 1.2 | 3.4 | 16.2 | -75.0 | 162.7 | 22.0 | 49.0 | 51.0 | 112.0 | 135.5 | 41.3 | 26.5 | 11.2 | 19.9 | 5.6 | 36.7 |
| age group | Abbott | 18-39 | 581 | 266 | 67.5 | 33.2 | 9.8 | 43.4 | 10.5 | 73.0 | 0.2 | 0.2 | 13.1 | 2.2 | 7.9 | -28.0 | -64.3 | 211.1 | -30.5 | 51.5 | 48.5 | 139.5 | 140.0 | 38.7 | 27.4 | 8.6 | 19.5 | 7.9 | 36.5 |
| age group | Abbott | 40-64 | 1,829 | 654 | 57.1 | 29.2 | 8.3 | 37.3 | 10.7 | 57.8 | 0.2 | 0.3 | 7.4 | 4.3 | 10.4 | -42.6 | -73.9 | 141.0 | -50.0 | 58.4 | 41.4 | 98.0 | 152.5 | 39.3 | 21.7 | 5.0 | 29.7 | 12.2 | 31.3 |
| age group | Abbott | 65+ | 1,572 | 534 | 53.5 | 25.3 | 8.3 | 35.9 | 9.9 | 52.2 | 0.0 | 0.2 | 8.2 | 3.7 | 11.1 | -50.0 | -73.6 | 70.7 | -62.0 | 66.9 | 32.6 | 72.0 | 150.0 | 29.0 | 15.0 | 5.4 | 40.1 | 11.6 | 27.9 |
| age group | Dexcom | <18 | 1,827 | 1,163 | 86.0 | 31.7 | 11.5 | 45.2 | 18.8 | 69.1 | 0.1 | 0.1 | 26.2 | 4.4 | 5.9 | -33.7 | -70.7 | 133.1 | -80.0 | 55.6 | 43.9 | 118.0 | 213.0 | 35.3 | 29.8 | 7.1 | 11.2 | 4.4 | 47.5 |
| age group | Dexcom | 18-39 | 2,670 | 1,692 | 81.2 | 31.1 | 5.8 | 51.1 | 13.1 | 78.0 | 0.1 | 0.2 | 27.8 | 5.9 | 7.2 | 33.3 | -66.6 | 144.9 | 22.5 | 46.8 | 52.7 | 109.0 | 117.5 | 31.6 | 38.2 | 5.3 | 12.4 | 4.7 | 39.4 |
| age group | Dexcom | 40-64 | 5,319 | 3,209 | 79.9 | 35.5 | 4.7 | 48.9 | 12.1 | 79.6 | 0.1 | 0.1 | 27.1 | 2.7 | 5.1 | 47.9 | -63.9 | 180.7 | 29.0 | 44.1 | 54.9 | 108.0 | 90.0 | 34.9 | 40.5 | 5.5 | 15.8 | 5.6 | 32.5 |
| age group | Dexcom | 65+ | 4,076 | 2,522 | 80.1 | 39.2 | 3.9 | 47.2 | 9.5 | 82.9 | 0.1 | 0.1 | 28.0 | 2.4 | 3.2 | 75.0 | -55.2 | 233.3 | 39.0 | 36.6 | 62.6 | 111.0 | 59.5 | 39.9 | 46.4 | 6.6 | 14.3 | 5.7 | 27.0 |
| sex | All | Female | 8,362 | 4,433 | 73.1 | 30.6 | 6.0 | 47.6 | 11.6 | 74.4 | 0.1 | 0.2 | 25.7 | 3.4 | 6.2 | -20.9 | -70.0 | 145.6 | -27.0 | 51.6 | 47.4 | 106.0 | 137.0 | 34.3 | 33.3 | 5.8 | 16.2 | 6.5 | 38.2 |
| sex | All | Male | 7,994 | 4,123 | 71.0 | 29.9 | 5.7 | 45.5 | 12.2 | 70.7 | 0.1 | 0.2 | 21.6 | 3.6 | 6.9 | 20.0 | -68.5 | 157.6 | 19.0 | 48.3 | 51.1 | 106.0 | 119.0 | 36.2 | 34.5 | 6.1 | 19.2 | 6.4 | 33.8 |
| sex | Abbott | Female | 1,941 | 544 | 49.0 | 22.8 | 7.5 | 42.8 | 10.4 | 54.8 | 0.1 | 0.1 | 7.3 | 3.0 | 8.9 | -51.5 | -75.0 | 60.5 | -70.0 | 69.3 | 30.0 | 69.5 | 160.0 | 27.6 | 13.1 | 5.3 | 37.7 | 15.1 | 28.9 |
| sex | Abbott | Male | 2,228 | 681 | 51.4 | 22.8 | 6.9 | 37.4 | 10.6 | 50.8 | 0.1 | 0.3 | 6.8 | 4.4 | 11.0 | -45.5 | -71.8 | 98.8 | -53.0 | 63.4 | 36.3 | 80.0 | 143.0 | 30.1 | 15.0 | 7.8 | 38.6 | 11.9 | 26.7 |
| sex | Dexcom | Female | 6,159 | 3,736 | 80.5 | 32.8 | 5.2 | 50.4 | 10.5 | 82.5 | 0.1 | 0.2 | 31.9 | 3.7 | 5.7 | 2.2 | -68.8 | 153.9 | 2.0 | 49.0 | 50.1 | 111.0 | 130.0 | 35.8 | 36.4 | 5.6 | 13.0 | 5.4 | 39.6 |
| sex | Dexcom | Male | 5,491 | 3,294 | 78.8 | 32.9 | 4.8 | 50.2 | 11.3 | 81.1 | 0.1 | 0.1 | 28.2 | 3.4 | 5.5 | 43.6 | -68.8 | 175.0 | 27.0 | 44.6 | 54.7 | 110.0 | 103.0 | 38.3 | 38.9 | 5.6 | 14.7 | 5.2 | 35.6 |

## g. Demographics: tests across groups
| k_groups | n | kruskal_H | kruskal_p | epsilon_squared | p_text | cut | brand | measure | chi2 | df | chi_square_p | cramers_v | effect_size_word |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4 | 10,732 | 55.265 | 0.000 | 0.005 | < 0.001 | age group | All | error, % of meter, across groups (Kruskal-Wallis) |  |  |  |  |  |
| 4 | 10,732 | 29.017 | 0.000 | 0.002 | < 0.001 | age group | All | absolute error, % of meter, across groups (Kruskal-Wallis) |  |  |  |  |  |
| 4 | 10,648 |  |  |  | < 0.001 | age group | All | direction (low / high) across groups (chi-square) | 55.806 | 3.000 | 0.000 | 0.072 | negligible |
| 4 | 10,732 |  |  |  | < 0.001 | age group | All | meter band across groups (chi-square) | 219.252 | 12.000 | 0.000 | 0.083 | negligible |
| 4 | 19,462 |  |  |  | < 0.001 | age group | All | outcome (model) across groups (chi-square) | 202.760 | 18.000 | 0.000 | 0.059 | negligible |
| 4 | 19,462 |  |  |  | 0.500 | age group | All | FDA event type (injury / death) across groups (chi-square) | 2.368 | 3.000 | 0.500 | 0.011 | negligible |
| 4 | 1,650 | 19.287 | 0.000 | 0.010 | < 0.001 | age group | Abbott | error, % of meter, across groups (Kruskal-Wallis) |  |  |  |  |  |
| 4 | 1,650 | 22.891 | 0.000 | 0.012 | < 0.001 | age group | Abbott | absolute error, % of meter, across groups (Kruskal-Wallis) |  |  |  |  |  |
| 4 | 1,646 |  |  |  | < 0.001 | age group | Abbott | direction (low / high) across groups (chi-square) | 29.266 | 3.000 | 0.000 | 0.133 | small |
| 4 | 1,650 |  |  |  | < 0.001 | age group | Abbott | meter band across groups (chi-square) | 77.868 | 12.000 | 0.000 | 0.125 | small |
| 4 | 4,391 |  |  |  | < 0.001 | age group | Abbott | outcome (model) across groups (chi-square) | 202.284 | 15.000 | 0.000 | 0.124 | small |
| 4 | 4,391 |  |  |  | 0.728 | age group | Abbott | FDA event type (injury / death) across groups (chi-square) | 1.304 | 3.000 | 0.728 | 0.017 | negligible |
| 4 | 8,586 | 110.903 | 0.000 | 0.013 | < 0.001 | age group | Dexcom | error, % of meter, across groups (Kruskal-Wallis) |  |  |  |  |  |
| 4 | 8,586 | 84.056 | 0.000 | 0.009 | < 0.001 | age group | Dexcom | absolute error, % of meter, across groups (Kruskal-Wallis) |  |  |  |  |  |
| 4 | 8,516 |  |  |  | < 0.001 | age group | Dexcom | direction (low / high) across groups (chi-square) | 124.587 | 3.000 | 0.000 | 0.121 | small |
| 4 | 8,586 |  |  |  | < 0.001 | age group | Dexcom | meter band across groups (chi-square) | 197.668 | 12.000 | 0.000 | 0.088 | negligible |
| 4 | 13,892 |  |  |  | < 0.001 | age group | Dexcom | outcome (model) across groups (chi-square) | 168.478 | 18.000 | 0.000 | 0.064 | negligible |
| 4 | 13,892 |  |  |  | 0.684 | age group | Dexcom | FDA event type (injury / death) across groups (chi-square) | 1.494 | 3.000 | 0.684 | 0.010 | negligible |
| 2 | 8,556 | 5.170 | 0.023 | 0.000 | 0.023 | sex | All | error, % of meter, across groups (Kruskal-Wallis) |  |  |  |  |  |
| 2 | 8,556 | 6.351 | 0.012 | 0.001 | 0.012 | sex | All | absolute error, % of meter, across groups (Kruskal-Wallis) |  |  |  |  |  |
| 2 | 8,486 |  |  |  | 0.001 | sex | All | direction (low / high) across groups (chi-square) | 10.589 | 1.000 | 0.001 | 0.035 | negligible |
| 2 | 8,556 |  |  |  | < 0.001 | sex | All | meter band across groups (chi-square) | 23.202 | 4.000 | 0.000 | 0.052 | negligible |
| 2 | 16,356 |  |  |  | < 0.001 | sex | All | outcome (model) across groups (chi-square) | 52.279 | 6.000 | 0.000 | 0.057 | negligible |
| 2 | 16,356 |  |  |  | 0.957 | sex | All | FDA event type (injury / death) across groups (chi-square) | 0.003 | 1.000 | 0.957 | 0.000 | negligible |
| 2 | 1,225 | 5.658 | 0.017 | 0.004 | 0.017 | sex | Abbott | error, % of meter, across groups (Kruskal-Wallis) |  |  |  |  |  |
| 2 | 1,225 | 0.859 | 0.354 | 0.000 | 0.354 | sex | Abbott | absolute error, % of meter, across groups (Kruskal-Wallis) |  |  |  |  |  |
| 2 | 1,219 |  |  |  | 0.023 | sex | Abbott | direction (low / high) across groups (chi-square) | 5.166 | 1.000 | 0.023 | 0.065 | negligible |
| 2 | 1,225 |  |  |  | 0.173 | sex | Abbott | meter band across groups (chi-square) | 6.375 | 4.000 | 0.173 | 0.072 | negligible |
| 2 | 4,169 |  |  |  | < 0.001 | sex | Abbott | outcome (model) across groups (chi-square) | 37.430 | 5.000 | 0.000 | 0.095 | negligible |
| 2 | 4,169 |  |  |  | 0.143 | sex | Abbott | FDA event type (injury / death) across groups (chi-square) | 2.147 | 1.000 | 0.143 | 0.023 | negligible |
| 2 | 7,030 | 5.185 | 0.023 | 0.001 | 0.023 | sex | Dexcom | error, % of meter, across groups (Kruskal-Wallis) |  |  |  |  |  |
| 2 | 7,030 | 8.628 | 0.003 | 0.001 | 0.003 | sex | Dexcom | absolute error, % of meter, across groups (Kruskal-Wallis) |  |  |  |  |  |
| 2 | 6,971 |  |  |  | < 0.001 | sex | Dexcom | direction (low / high) across groups (chi-square) | 14.437 | 1.000 | 0.000 | 0.046 | negligible |
| 2 | 7,030 |  |  |  | 0.007 | sex | Dexcom | meter band across groups (chi-square) | 14.168 | 4.000 | 0.007 | 0.045 | negligible |
| 2 | 11,650 |  |  |  | 0.483 | sex | Dexcom | outcome (model) across groups (chi-square) | 5.488 | 6.000 | 0.483 | 0.022 | negligible |
| 2 | 11,650 |  |  |  | 0.522 | sex | Dexcom | FDA event type (injury / death) across groups (chi-square) | 0.409 | 1.000 | 0.522 | 0.006 | negligible |

## g. Demographics: pairwise tests between groups
| cut | measure | group_a | group_b | n_a | n_b | median_a | median_b | iqr_a | iqr_b | median_diff_a_minus_b | median_diff_ci_low | median_diff_ci_high | cliffs_delta | cliffs_delta_ci_low | cliffs_delta_ci_high | effect_size_word | mann_whitney_p | p_text | share_a_pct | share_b_pct | risk_diff_points | risk_diff_ci_low | risk_diff_ci_high | chi_square_p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| age group | error, % of meter | <18 | 18-39 | 1,373 | 2,030 | -31.84 | 25.54 | -71 to 138 | -66 to 148 | -57.38 | -74.00 | -25.88 | -0.06 | -0.10 | -0.02 | negligible | 0.00 | 0.003 |  |  |  |  |  |  |
| age group | absolute error, % of meter | <18 | 18-39 | 1,373 | 2,030 | 80.40 | 84.30 | 58 to 138 | 58 to 148 | -3.90 | -6.67 | -0.40 | -0.04 | -0.08 | -0.00 | negligible | 0.06 | 0.057 |  |  |  |  |  |  |
| age group | share reading low | <18 | 18-39 | 1,367 | 2,021 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 54.86 | 47.90 | 6.97 | 3.76 | 10.44 | 0.00 |
| age group | share meter under 70 | <18 | 18-39 | 1,373 | 2,030 |  |  |  |  |  |  |  |  |  |  |  |  | 0.002 | 37.14 | 42.51 | -5.37 | -9.02 | -2.07 | 0.00 |
| age group | share outcome hospital or ER (model) | <18 | 18-39 | 2,286 | 3,471 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 67.32 | 74.94 | -7.61 | -9.92 | -5.20 | 0.00 |
| age group | share outcome hypoglycaemia (model) | <18 | 18-39 | 2,286 | 3,471 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 19.64 | 14.52 | 5.12 | 3.04 | 6.98 | 0.00 |
| age group | share FDA event type Death | <18 | 18-39 | 2,286 | 3,471 |  |  |  |  |  |  |  |  |  |  |  |  | 0.116 | 0.04 | 0.20 | -0.16 | -0.33 | 0.02 | 0.12 |
| age group | error, % of meter | <18 | 40-64 | 1,373 | 4,124 | -31.84 | 30.75 | -71 to 138 | -66 to 173 | -62.59 | -74.78 | -41.92 | -0.09 | -0.12 | -0.05 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| age group | absolute error, % of meter | <18 | 40-64 | 1,373 | 4,124 | 80.40 | 85.91 | 58 to 138 | 58 to 173 | -5.51 | -7.84 | -2.88 | -0.06 | -0.10 | -0.03 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| age group | share reading low | <18 | 40-64 | 1,367 | 4,083 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 54.86 | 47.32 | 7.55 | 4.44 | 10.67 | 0.00 |
| age group | share meter under 70 | <18 | 40-64 | 1,373 | 4,124 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 37.14 | 42.41 | -5.27 | -8.15 | -2.42 | 0.00 |
| age group | share outcome hospital or ER (model) | <18 | 40-64 | 2,286 | 7,770 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 67.32 | 70.97 | -3.64 | -5.87 | -1.42 | 0.00 |
| age group | share outcome hypoglycaemia (model) | <18 | 40-64 | 2,286 | 7,770 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 19.64 | 13.42 | 6.22 | 4.52 | 7.98 | 0.00 |
| age group | share FDA event type Death | <18 | 40-64 | 2,286 | 7,770 |  |  |  |  |  |  |  |  |  |  |  |  | 0.195 | 0.04 | 0.15 | -0.11 | -0.21 | 0.02 | 0.20 |
| age group | error, % of meter | <18 | 65+ | 1,373 | 3,205 | -31.84 | 50.00 | -71 to 138 | -62 to 200 | -81.84 | -94.29 | -67.18 | -0.13 | -0.17 | -0.09 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| age group | absolute error, % of meter | <18 | 65+ | 1,373 | 3,205 | 80.40 | 87.80 | 58 to 138 | 59 to 200 | -7.40 | -9.68 | -4.44 | -0.09 | -0.13 | -0.06 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| age group | share reading low | <18 | 65+ | 1,367 | 3,177 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 54.86 | 42.93 | 11.93 | 8.76 | 15.11 | 0.00 |
| age group | share meter under 70 | <18 | 65+ | 1,373 | 3,205 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 37.14 | 46.93 | -9.78 | -12.75 | -6.76 | 0.00 |
| age group | share outcome hospital or ER (model) | <18 | 65+ | 2,286 | 5,935 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 67.32 | 72.17 | -4.84 | -6.89 | -2.61 | 0.00 |
| age group | share outcome hypoglycaemia (model) | <18 | 65+ | 2,286 | 5,935 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 19.64 | 11.36 | 8.28 | 6.49 | 10.03 | 0.00 |
| age group | share FDA event type Death | <18 | 65+ | 2,286 | 5,935 |  |  |  |  |  |  |  |  |  |  |  |  | 0.209 | 0.04 | 0.15 | -0.11 | -0.24 | 0.03 | 0.21 |
| age group | error, % of meter | 18-39 | 40-64 | 2,030 | 4,124 | 25.54 | 30.75 | -66 to 148 | -66 to 173 | -5.21 | -36.08 | 18.14 | -0.03 | -0.06 | -0.00 | negligible | 0.05 | 0.053 |  |  |  |  |  |  |
| age group | absolute error, % of meter | 18-39 | 40-64 | 2,030 | 4,124 | 84.30 | 85.91 | 58 to 148 | 58 to 173 | -1.61 | -4.02 | 0.55 | -0.03 | -0.06 | 0.00 | negligible | 0.08 | 0.085 |  |  |  |  |  |  |
| age group | share reading low | 18-39 | 40-64 | 2,021 | 4,083 |  |  |  |  |  |  |  |  |  |  |  |  | 0.670 | 47.90 | 47.32 | 0.58 | -1.96 | 3.07 | 0.67 |
| age group | share meter under 70 | 18-39 | 40-64 | 2,030 | 4,124 |  |  |  |  |  |  |  |  |  |  |  |  | 0.939 | 42.51 | 42.41 | 0.10 | -2.53 | 2.80 | 0.94 |
| age group | share outcome hospital or ER (model) | 18-39 | 40-64 | 3,471 | 7,770 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 74.94 | 70.97 | 3.97 | 2.10 | 5.74 | 0.00 |
| age group | share outcome hypoglycaemia (model) | 18-39 | 40-64 | 3,471 | 7,770 |  |  |  |  |  |  |  |  |  |  |  |  | 0.119 | 14.52 | 13.42 | 1.10 | -0.33 | 2.50 | 0.12 |
| age group | share FDA event type Death | 18-39 | 40-64 | 3,471 | 7,770 |  |  |  |  |  |  |  |  |  |  |  |  | 0.573 | 0.20 | 0.15 | 0.05 | -0.10 | 0.23 | 0.57 |
| age group | error, % of meter | 18-39 | 65+ | 2,030 | 3,205 | 25.54 | 50.00 | -66 to 148 | -62 to 200 | -24.46 | -55.00 | -7.14 | -0.07 | -0.11 | -0.04 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| age group | absolute error, % of meter | 18-39 | 65+ | 2,030 | 3,205 | 84.30 | 87.80 | 58 to 148 | 59 to 200 | -3.50 | -6.25 | -1.14 | -0.06 | -0.09 | -0.03 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| age group | share reading low | 18-39 | 65+ | 2,021 | 3,177 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 47.90 | 42.93 | 4.96 | 2.15 | 7.56 | 0.00 |
| age group | share meter under 70 | 18-39 | 65+ | 2,030 | 3,205 |  |  |  |  |  |  |  |  |  |  |  |  | 0.002 | 42.51 | 46.93 | -4.41 | -7.19 | -1.71 | 0.00 |
| age group | share outcome hospital or ER (model) | 18-39 | 65+ | 3,471 | 5,935 |  |  |  |  |  |  |  |  |  |  |  |  | 0.003 | 74.94 | 72.17 | 2.77 | 1.13 | 4.73 | 0.00 |
| age group | share outcome hypoglycaemia (model) | 18-39 | 65+ | 3,471 | 5,935 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 14.52 | 11.36 | 3.16 | 1.73 | 4.62 | 0.00 |
| age group | share FDA event type Death | 18-39 | 65+ | 3,471 | 5,935 |  |  |  |  |  |  |  |  |  |  |  |  | 0.570 | 0.20 | 0.15 | 0.05 | -0.12 | 0.23 | 0.57 |
| age group | error, % of meter | 40-64 | 65+ | 4,124 | 3,205 | 30.75 | 50.00 | -66 to 173 | -62 to 200 | -19.25 | -38.37 | -7.00 | -0.04 | -0.07 | -0.02 | negligible | 0.00 | 0.001 |  |  |  |  |  |  |
| age group | absolute error, % of meter | 40-64 | 65+ | 4,124 | 3,205 | 85.91 | 87.80 | 58 to 173 | 59 to 200 | -1.90 | -3.62 | 0.19 | -0.03 | -0.06 | -0.00 | negligible | 0.03 | 0.028 |  |  |  |  |  |  |
| age group | share reading low | 40-64 | 65+ | 4,083 | 3,177 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 47.32 | 42.93 | 4.38 | 2.22 | 6.71 | 0.00 |
| age group | share meter under 70 | 40-64 | 65+ | 4,124 | 3,205 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 42.41 | 46.93 | -4.52 | -6.77 | -2.24 | 0.00 |
| age group | share outcome hospital or ER (model) | 40-64 | 65+ | 7,770 | 5,935 |  |  |  |  |  |  |  |  |  |  |  |  | 0.123 | 70.97 | 72.17 | -1.20 | -2.78 | 0.35 | 0.12 |
| age group | share outcome hypoglycaemia (model) | 40-64 | 65+ | 7,770 | 5,935 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 13.42 | 11.36 | 2.07 | 0.98 | 3.12 | 0.00 |
| age group | share FDA event type Death | 40-64 | 65+ | 7,770 | 5,935 |  |  |  |  |  |  |  |  |  |  |  |  | 0.967 | 0.15 | 0.15 | 0.00 | -0.14 | 0.14 | 0.97 |
| sex | error, % of meter | Female | Male | 4,433 | 4,123 | -20.90 | 20.00 | -70 to 146 | -68 to 158 | -40.90 | -52.45 | -16.96 | -0.03 | -0.05 | -0.00 | negligible | 0.02 | 0.023 |  |  |  |  |  |  |
| sex | absolute error, % of meter | Female | Male | 4,433 | 4,123 | 83.02 | 84.63 | 56 to 146 | 59 to 158 | -1.61 | -3.83 | 0.06 | -0.03 | -0.06 | -0.01 | negligible | 0.01 | 0.012 |  |  |  |  |  |  |
| sex | share reading low | Female | Male | 4,390 | 4,096 |  |  |  |  |  |  |  |  |  |  |  |  | 0.001 | 52.12 | 48.58 | 3.53 | 1.48 | 5.63 | 0.00 |
| sex | share meter under 70 | Female | Male | 4,433 | 4,123 |  |  |  |  |  |  |  |  |  |  |  |  | 0.161 | 39.09 | 40.58 | -1.48 | -3.59 | 0.49 | 0.16 |
| sex | share outcome hospital or ER (model) | Female | Male | 8,362 | 7,994 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 74.42 | 70.69 | 3.73 | 2.35 | 5.02 | 0.00 |
| sex | share outcome hypoglycaemia (model) | Female | Male | 8,362 | 7,994 |  |  |  |  |  |  |  |  |  |  |  |  | 0.290 | 11.62 | 12.16 | -0.54 | -1.51 | 0.39 | 0.29 |
| sex | share FDA event type Death | Female | Male | 8,362 | 7,994 |  |  |  |  |  |  |  |  |  |  |  |  | 0.957 | 0.19 | 0.19 | 0.00 | -0.13 | 0.14 | 0.96 |

## g. Demographics: filled vs unfilled
| field | group | wrong_reading_reports | pairs | pct_with_pair | median_year | pct_brand_Abbott | pct_brand_Dexcom | pct_brand_Medtronic | pct_brand_Senseonics | pct_fda_death | pct_outcome_hospital_or_er | pct_outcome_none | pct_fda_hospitalization | pct_fingerstick_yes | pct_reporter_patient_or_family | pct_abbott_template | median_err_pct | q1_err_pct | q3_err_pct | pct_low | pct_meter_under_70 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| age | age filled | 19,462 | 10,732 | 55.1 | 2,024 | 22.6 | 71.4 | 3.4 | 2.5 | 0.1 | 71.6 | 10.7 | 23.1 | 75.6 | 7.5 | 2.3 | 30.8 | -66.1 | 167.9 | 46.7 | 43.1 |
| age | age not filled | 20,205 | 6,841 | 33.9 | 2,024 | 91.8 | 5.0 | 0.5 | 2.6 | 0.2 | 66.7 | 11.4 | 8.4 | 54.1 | 1.6 | 13.1 | -41.6 | -79.6 | 145.1 | 55.6 | 30.0 |
| sex | sex filled | 16,356 | 8,556 | 52.3 | 2,025 | 25.5 | 71.2 | 1.1 | 2.2 | 0.2 | 72.6 | 11.4 | 23.7 | 72.1 | 6.6 | 2.0 | -0.5 | -69.1 | 150.0 | 50.0 | 39.8 |
| sex | sex not filled | 23,311 | 9,017 | 38.7 | 2,023 | 80.5 | 14.0 | 2.5 | 2.8 | 0.2 | 66.7 | 10.9 | 10.0 | 59.4 | 3.1 | 11.9 | -11.8 | -75.8 | 170.6 | 50.3 | 36.3 |

## g. Demographics: filled vs unfilled, tests
| field | measure | n_a | n_b | median_a | median_b | iqr_a | iqr_b | median_diff_a_minus_b | median_diff_ci_low | median_diff_ci_high | cliffs_delta | cliffs_delta_ci_low | cliffs_delta_ci_high | effect_size_word | mann_whitney_p | p_text | share_a_pct | share_b_pct | risk_diff_points | risk_diff_ci_low | risk_diff_ci_high | chi_square_p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| age | error, % of meter: filled vs not filled | 10,732 | 6,841 | 30.79 | -41.58 | -66 to 168 | -80 to 145 | 72.37 | 63.75 | 78.95 | 0.12 | 0.10 | 0.14 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| age | share reading low: filled vs not filled | 10,648 | 6,813 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 47.09 | 55.82 | -8.73 | -10.16 | -7.19 | 0.00 |
| age | share FDA event type Death: filled vs not filled | 19,462 | 20,205 |  |  |  |  |  |  |  |  |  |  |  |  | 0.028 | 0.15 | 0.25 | -0.10 | -0.18 | -0.02 | 0.03 |
| age | share outcome hospital or ER (model): filled vs not filled | 19,462 | 20,205 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 71.61 | 66.71 | 4.91 | 4.00 | 5.81 | 0.00 |
| age | error, % of meter: filled vs not filled, Abbott only | 1,650 | 5,820 | -42.86 | -50.00 | -73 to 134 | -81 to 150 | 7.14 | 2.20 | 12.51 | 0.07 | 0.03 | 0.10 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| age | share FDA event type Death: filled vs not filled, Abbott only | 4,391 | 18,544 |  |  |  |  |  |  |  |  |  |  |  |  | 0.558 | 0.20 | 0.25 | -0.05 | -0.19 | 0.10 | 0.56 |
| age | error, % of meter: filled vs not filled, Dexcom only | 8,586 | 603 | 46.98 | 30.61 | -64 to 175 | -57 to 131 | 16.37 | 7.88 | 24.61 | 0.03 | -0.01 | 0.08 | negligible | 0.18 | 0.175 |  |  |  |  |  |  |
| age | share FDA event type Death: filled vs not filled, Dexcom only | 13,892 | 1,019 |  |  |  |  |  |  |  |  |  |  |  |  | 0.176 | 0.13 | 0.29 | -0.16 | -0.56 | 0.13 | 0.18 |
| sex | error, % of meter: filled vs not filled | 8,556 | 9,017 | -0.45 | -11.76 | -69 to 150 | -76 to 171 | 11.31 | -15.92 | 21.75 | 0.02 | 0.00 | 0.03 | negligible | 0.07 | 0.072 |  |  |  |  |  |  |
| sex | share reading low: filled vs not filled | 8,486 | 8,975 |  |  |  |  |  |  |  |  |  |  |  |  | 0.831 | 50.41 | 50.57 | -0.16 | -1.58 | 1.32 | 0.83 |
| sex | share FDA event type Death: filled vs not filled | 16,356 | 23,311 |  |  |  |  |  |  |  |  |  |  |  |  | 0.719 | 0.19 | 0.21 | -0.02 | -0.10 | 0.07 | 0.72 |
| sex | share outcome hospital or ER (model): filled vs not filled | 16,356 | 23,311 |  |  |  |  |  |  |  |  |  |  |  |  | < 0.001 | 72.60 | 66.67 | 5.93 | 5.03 | 6.90 | 0.00 |
| sex | error, % of meter: filled vs not filled, Abbott only | 1,225 | 6,245 | -47.28 | -46.74 | -74 to 77 | -81 to 160 | -0.54 | -6.13 | 3.75 | -0.01 | -0.05 | 0.02 | negligible | 0.42 | 0.416 |  |  |  |  |  |  |
| sex | share FDA event type Death: filled vs not filled, Abbott only | 4,169 | 18,766 |  |  |  |  |  |  |  |  |  |  |  |  | 0.682 | 0.22 | 0.25 | -0.03 | -0.19 | 0.14 | 0.68 |
| sex | error, % of meter: filled vs not filled, Dexcom only | 7,030 | 2,159 | 29.79 | 74.07 | -69 to 164 | -44 to 200 | -44.28 | -56.63 | -33.53 | -0.14 | -0.17 | -0.12 | negligible | 0.00 | < 0.001 |  |  |  |  |  |  |
| sex | share FDA event type Death: filled vs not filled, Dexcom only | 11,650 | 3,261 |  |  |  |  |  |  |  |  |  |  |  |  | 0.058 | 0.17 | 0.03 | 0.14 | 0.04 | 0.23 | 0.06 |
