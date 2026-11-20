# Regex hit rates

Input: `fda-maude/data/sample_narratives.jsonl`. Reports: 287.

### By maker

| group | n | pair (both numbers) | pair incl. LOW/HIGH word | abbott_template | dexcom_bg | any sensor value | any meter value | display word | Parkes zone | wear day |
|---|---|---|---|---|---|---|---|---|---|---|
| Abbott | 100 | 58% | 58% | 57% | 1% | 59% | 60% | 0% | 57% | 52% |
| Dexcom | 100 | 16% | 20% | 0% | 20% | 19% | 30% | 4% | 27% | 0% |
| Medtronic | 87 | 3% | 3% | 0% | 3% | 5% | 16% | 0% | 0% | 0% |

### By event type

| group | n | pair (both numbers) | pair incl. LOW/HIGH word | abbott_template | dexcom_bg | any sensor value | any meter value | display word | Parkes zone | wear day |
|---|---|---|---|---|---|---|---|---|---|---|
| Malfunction | 150 | 32% | 32% | 32% | 0% | 33% | 32% | 0% | 41% | 31% |
| Injury | 134 | 22% | 25% | 7% | 18% | 25% | 42% | 3% | 17% | 4% |
| Death | 3 | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |

### By maker and event type

| group | n | pair (both numbers) | pair incl. LOW/HIGH word | abbott_template | dexcom_bg | any sensor value | any meter value | display word | Parkes zone | wear day |
|---|---|---|---|---|---|---|---|---|---|---|
| Abbott / Malfunction | 50 | 96% | 96% | 96% | 0% | 98% | 96% | 0% | 98% | 94% |
| Abbott / Injury | 49 | 20% | 20% | 18% | 2% | 20% | 24% | 0% | 16% | 10% |
| Abbott / Death | 1 | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| Dexcom / Malfunction | 50 | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 24% | 0% |
| Dexcom / Injury | 50 | 32% | 40% | 0% | 40% | 38% | 60% | 8% | 30% | 0% |
| Medtronic / Malfunction | 50 | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
| Medtronic / Injury | 35 | 9% | 9% | 0% | 9% | 11% | 40% | 0% | 0% | 0% |
| Medtronic / Death | 2 | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% |
