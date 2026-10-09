# Figure fixes, error grid, first simulation, README draft

Date: 2026-10-09 12:00
Who: manager + 3 agents
Asked by: Artemy

## Asked
- Prepare a clean public push. Fix figure 09. Add an error grid. Run a first decision-flip simulation. Rewrite README for the rubric. Show before pushing.

## Done
- analysis/explore_raw_data.py: bias now binned by average of CGM and reference (fixes the "reads high" artifact). Parkes error grid added (figure 11). Value labels, n= flags, units.
- analysis/bias_simulation.py (new): constant low bias 10/20/30%. Rules: CGM < 70 -> carbs, CGM > 200 -> insulin. Figure 12, simulation_stats.json, SIMULATION_RESULTS.md.
- README_DRAFT.md: rubric-driven README. Awaiting lead review.
- Public-repo cleanup: team-skill remarks reworded; draft feedback moved to docs/team-docs/ (gitignored); log trimmed.

## Key numbers
- Parkes zones, REPLACE-BG meter pairs: A 88.1%, B 10.9%, C+D+E 0.9%.
- Below 70 mg/dL, Dexcom G4 reads 5 to 11% low (average-binned).
- 10% low bias: median 6.5 false low alerts and 20.7 missed high alerts per person per day. 30%: 33.3 and 53.1.

## Decisions
- docs/team-docs/ and README_DRAFT.md are gitignored. Private.
- Thresholds 70 / 200 are a first choice from the lead's research description.

## Open questions / next
- Lead approves README and push list. Then push.
- Check Parkes zone borders against the paper.
