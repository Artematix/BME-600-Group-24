# Run set for the text pipeline

Built 2026-10-30 by `scripts/build_run_set.py`. FDA snapshot 2026-10-21; cutoff for text = received on or before 2026-07-21 (3 months before the snapshot).
Words: tier = part of the data (serious = death + injury reports; sample = random malfunction reports). Stratum = group of reports (product code x year received). Weight = how many malfunction reports one sampled report stands for.

## 1. Definition

| Part | Rule |
|---|---|
| (a) serious | event_type Death or Injury; received on or before 2026-07-21; has text (event text non-empty, or manufacturer narrative longer than 20 characters) |
| (b) sample | Malfunction reports received on or before 2026-07-21; strata = product code x year; target 5,000; at least 25 per stratum when the stratum has that many, smaller strata taken whole; simple random sampling, seed 20261019 |
| run set | (a) + (b) rows that have text. Order in the file: sample first (by key), then serious in random order (seed 20261019), so a partial run is a random subset |

## 2. Counts

| Step | Reports |
|---|---|
| serious rows (Death + Injury) | 123,607 |
| received on or before cutoff | 118,472 |
| dropped: too recent | 5,135 |
| dropped: no text | 10 |
| (a) serious eligible | 118,462 |
| malfunction reports, all | 3,257,570 |
| malfunction frame (received by cutoff) | 2,936,278 |
| strata (taken whole) | 95 (19) |
| (b) sample drawn | 6,168 |
| (b) sample with text | 6,137 |
| weight range | 1.0 to 594.3 |
| **run set (a + b with text)** | **124,599** |

Run set by tier and maker:

| tier | Abbott | Dexcom | Medtronic | Other | All |
|---|---|---|---|---|---|
| sample | 843 | 4,574 | 407 | 313 | 6,137 |
| serious | 74,657 | 32,045 | 8,660 | 3,100 | 118,462 |

Sample text availability by maker (share with text):

| maker | sampled | with text |
|---|---|---|
| Abbott | 861 | 98% |
| Dexcom | 4,585 | 100% |
| Medtronic | 407 | 100% |
| Other | 315 | 99% |

Sample allocation by product code (frame reports and sampled):

| code | reports | sampled |
|---|---|---|
| QBJ | 2,117,302 | 3,606 |
| PQF | 321,884 | 613 |
| MDS | 267,424 | 730 |
| QLG | 120,077 | 227 |
| PZE | 98,928 | 314 |
| SFI | 3,368 | 50 |
| SBA | 2,381 | 59 |
| SAF | 2,333 | 75 |
| QHJ | 1,179 | 129 |
| QDK | 601 | 162 |
| QCD | 566 | 104 |
| QII | 234 | 98 |
| SBH | 1 | 1 |

## 3. How this sample differs from the earlier API-drawn sample (tier 3, 5,193 reports)

- Same strata (product code x year), same target (5,000), same minimum (25), same seed (20261019).
- Drawn locally from the full table, so it is a simple random sample inside each stratum. The API sample used clusters of up to 10 neighbouring reports on busy days, with a selection probability per report. Here every report in a stratum has the same chance, so `weight` = stratum size / sampled, and `weight_norm` equals `weight`.
- Frame limited to reports received on or before 2026-07-21 so that every sampled report can have text. The API sample included reports up to the 2026-10-07 snapshot.
- The FDA data are the 2026-10-21 snapshot (bulk files), not the 2026-10-07 API snapshot. Counts differ a little.
- Different reports are picked (different method), so results are not row-for-row comparable with the API sample. Weighted totals should agree within sampling error.

## 4. Files

| File | Rows | In git? |
|---|---|---|
| `clean/sample_local.parquet` | 6,168 | no (rebuild with the script) |
| `clean/run_set.csv.gz` | 124,599 | no |
| `results/text/RUN_SET.md` | this file | yes |
