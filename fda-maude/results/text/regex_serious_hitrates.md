# Regex hit rates

Input: `fda-maude/clean/serious.csv.gz`. Reports: 123607.

### By maker

| group | n | pair (both numbers) | pair incl. LOW/HIGH word | abbott_template | dexcom_bg | any sensor value | any meter value | display word | Parkes zone | wear day |
|---|---|---|---|---|---|---|---|---|---|---|
| Medtronic | 8721 | 5% | 5% | 0% | 5% | 5% | 73% | 0% | 0% | 0% |
| Other | 3235 | 16% | 16% | 0% | 16% | 20% | 23% | 0% | 0% | 1% |
| Abbott | 77868 | 7% | 7% | 5% | 3% | 10% | 12% | 0% | 6% | 7% |
| Dexcom | 33783 | 28% | 31% | 0% | 31% | 33% | 45% | 5% | 26% | 1% |

### By event type

| group | n | pair (both numbers) | pair incl. LOW/HIGH word | abbott_template | dexcom_bg | any sensor value | any meter value | display word | Parkes zone | wear day |
|---|---|---|---|---|---|---|---|---|---|---|
| Injury | 122984 | 13% | 14% | 3% | 11% | 16% | 26% | 1% | 11% | 5% |
| Death | 623 | 4% | 4% | 0% | 4% | 8% | 11% | 1% | 2% | 1% |

### By maker and event type

| group | n | pair (both numbers) | pair incl. LOW/HIGH word | abbott_template | dexcom_bg | any sensor value | any meter value | display word | Parkes zone | wear day |
|---|---|---|---|---|---|---|---|---|---|---|
| Medtronic / Injury | 8618 | 5% | 5% | 0% | 5% | 5% | 74% | 0% | 0% | 0% |
| Medtronic / Death | 103 | 2% | 2% | 0% | 2% | 4% | 10% | 0% | 0% | 0% |
| Other / Injury | 3230 | 16% | 16% | 0% | 16% | 20% | 23% | 0% | 0% | 1% |
| Abbott / Injury | 77706 | 7% | 7% | 5% | 3% | 10% | 12% | 0% | 6% | 7% |
| Dexcom / Injury | 33430 | 28% | 31% | 0% | 31% | 33% | 46% | 5% | 26% | 1% |
| Dexcom / Death | 353 | 3% | 3% | 0% | 3% | 8% | 8% | 2% | 1% | 1% |
| Other / Death | 5 | 0% | 0% | 0% | 0% | 0% | 20% | 0% | 0% | 0% |
| Abbott / Death | 162 | 7% | 7% | 1% | 6% | 12% | 17% | 0% | 4% | 2% |
