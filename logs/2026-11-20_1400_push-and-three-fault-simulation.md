# Push and three-fault simulation

Date: 2026-11-20 14:00
Who: manager (fixes, push, status edits) + 1 agent (simulation)
Asked by: Artemy

## Asked
- Fix the three pre-push items and push.
- Run the three-fault simulation with the suggested defaults. Light checking only.

## Done
- `.gitignore`: the two per-participant tables (`analysis/participant_metrics.csv`, `analysis/simulation_v2_participants.csv`) and all `llm_serious500_*` pilot outputs stay local.
- `README.md`: text step no longer "pending"; the 287-report set is "labelled by one AI reviewer", not "hand-labelled".
- Pushed commit `0baa650` to `origin/main` (266 files). First tries failed with HTTP 408 on a slow connection.
- New, not pushed yet: `analysis/simulation_three_faults.py`, `simulation_three_faults_stats.json`, `simulation_three_faults_lookup.csv`, `SIMULATION_THREE_FAULTS.md`, figures 36 and 37.
- Status lines updated: `docs/PROJECT_OVERVIEW.md`, `analysis/FINDINGS.md`, `analysis/REPRODUCIBILITY.md`, `README.md`.

## Result (one 6-hour episode, median person, 226 participants)
| Fault | Size from FDA tables | Main effect |
|---|---|---|
| False low (true 70 to 250) | -69.4 % | 20.3 unneeded sugar treatments; 0.52 U insulin not given; 83 min over 180 not shown as high |
| Hidden low (true under 54) | +163.6 % | 33.7 min truly under 54 with sensor at 70 or above; 0.48 under-54 alerts not shown |
| Floor-pinned (true over 250) | shows 39 mg/dL | 8.2 unneeded sugar treatments; 1.29 U insulin not given; 115 min over 180 not shown as high |

## Decisions
- Episodes 2, 6, 12 h. Sugar rule: 15 g when the sensor shows under 70, at most once per 15 min. Constant bias (-20, -40, -66 %) kept as reference rows.
- Per-participant tables are kept out of the public repo. Data-use terms were not checked; leaving them out is the safe choice.
- Checking was light by request: three sanity checks (all passed) and one look at each figure. No independent number check.

## Open questions / next
- Sugar counts are an upper bound: the rule repeats every 15 min and glucose does not respond to the sugar.
- Fault sizes use the nearest group in the FDA tables, not the exact glucose bands. Exact values would need the per-report file.
- The three hidden-low sizes give the same result (no true reading is under 39, so every size lifts it to 70 or above).
- Second push for the simulation files waits for Artemy's word.
- Still not built: the four sharing pieces for the team (agents died in the 2026-11-10 network outage).
