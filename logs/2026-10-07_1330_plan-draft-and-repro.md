# Research plan draft 1 + reproducibility check

Date: 2026-10-07 13:30
Who: manager + 2 agents
Asked by: Artemy

## Asked
- Reframe: FDA mining = Phase 1 (preliminary, guides later). Fault simulation stays open, many fault types.
- Draft the research plan. Check the analysis script still runs. Pick figures for Preliminary Results.
- Do not commit.

## Done
- CLAUDE.md, docs/PROJECT_OVERVIEW.md, fda-maude/README.md: reframed to Phase 1 / Phase 2.
- Agent: docs/plans/2026-10-07_research-plan.md (219 lines). Follows the 6 graded sections. Fault types listed as an open table.
- Agent: analysis/REPRODUCIBILITY.md + analysis/requirements.txt. Script runs from new data path in 31 s. Outputs byte-identical across two runs.
- Manager: removed last line of explore_raw_data.py (printed JSON with Chinese text, crashed on Windows when redirected). Files were saved before the crash, so no results change.

## Decisions
- Recommended report figures: 09_accuracy_by_range (main), 08_cgm_vs_reference_scatter (second). Both need caption/label fixes before use.
- Phase 2 waits on Phase 1 for fault choice, but team should pick a fallback fault set now.

## Open questions / next
- Team must confirm research question (README version) and fix the 18 draft problems listed in the plan.
- Treatment rules to simulate: thresholds vs real pump events vs both.
- Possibly build an error-grid figure that shows decision flips. Needs new code.
- Nothing committed.
