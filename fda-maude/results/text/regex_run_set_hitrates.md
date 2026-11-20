# Regex hit rates

Input: `fda-maude/clean/run_set.csv.gz` (the run set: 118,462 serious + 6,137 sampled malfunction reports). Reports: 124599.

### By maker

| group | n | pair (both numbers) | pair incl. LOW/HIGH word | abbott_template | dexcom_bg | any sensor value | any meter value | display word | Parkes zone | wear day |
|---|---|---|---|---|---|---|---|---|---|---|
| Dexcom | 36619 | 25% | 27% | 0% | 27% | 29% | 40% | 4% | 24% | 1% |
| Medtronic | 9067 | 4% | 4% | 0% | 4% | 5% | 70% | 0% | 0% | 0% |
| Other | 3413 | 15% | 15% | 0% | 15% | 19% | 22% | 0% | 0% | 1% |
| Abbott | 75500 | 7% | 7% | 4% | 3% | 10% | 12% | 0% | 6% | 7% |

### By event type

| group | n | pair (both numbers) | pair incl. LOW/HIGH word | abbott_template | dexcom_bg | any sensor value | any meter value | display word | Parkes zone | wear day |
|---|---|---|---|---|---|---|---|---|---|---|
| Malfunction | 6137 | 5% | 5% | 4% | 1% | 5% | 6% | 0% | 16% | 4% |
| Injury | 117862 | 13% | 13% | 3% | 11% | 16% | 26% | 1% | 11% | 5% |
| Death | 600 | 4% | 4% | 0% | 4% | 8% | 11% | 1% | 2% | 1% |

### By maker and event type

| group | n | pair (both numbers) | pair incl. LOW/HIGH word | abbott_template | dexcom_bg | any sensor value | any meter value | display word | Parkes zone | wear day |
|---|---|---|---|---|---|---|---|---|---|---|
| Dexcom / Malfunction | 4574 | 1% | 1% | 0% | 1% | 1% | 1% | 0% | 8% | 0% |
| Medtronic / Malfunction | 407 | 6% | 6% | 0% | 6% | 6% | 9% | 0% | 0% | 0% |
| Other / Malfunction | 313 | 4% | 4% | 0% | 4% | 4% | 4% | 0% | 0% | 1% |
| Abbott / Malfunction | 843 | 27% | 27% | 27% | 0% | 28% | 30% | 0% | 75% | 25% |
| Abbott / Injury | 74512 | 7% | 7% | 4% | 3% | 10% | 12% | 0% | 6% | 7% |
| Dexcom / Injury | 31698 | 28% | 31% | 0% | 31% | 33% | 46% | 5% | 26% | 1% |
| Medtronic / Injury | 8557 | 4% | 4% | 0% | 4% | 5% | 74% | 0% | 0% | 0% |
| Other / Injury | 3095 | 17% | 17% | 0% | 17% | 21% | 23% | 0% | 0% | 1% |
| Dexcom / Death | 347 | 3% | 3% | 0% | 3% | 7% | 8% | 2% | 1% | 1% |
| Other / Death | 5 | 0% | 0% | 0% | 0% | 0% | 20% | 0% | 0% | 0% |
| Medtronic / Death | 103 | 2% | 2% | 0% | 2% | 4% | 10% | 0% | 0% | 0% |
| Abbott / Death | 145 | 8% | 8% | 1% | 7% | 13% | 18% | 0% | 5% | 2% |
