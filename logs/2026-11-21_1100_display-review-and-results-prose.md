# Paper: display items reworked, Results written and checked

Date: 2026-11-21
Who: manager (Results prose, Table 1, Table S1, captions, outline) + 5 agents (Figures 2 and 4, new Figure 5, rubric check, number check, Methods facts)
Asked by: Artemy

## Asked
- Artemy reviewed the seven display items and the voice sample. His points:
  - Table 1 a little too wordy. Figures 2 and 4 carry too much text.
  - Table 2 is confusing. A table is the wrong form. Illustrate it, take space if needed.
  - Table 3: "What we did" must be natural language, fewer semicolons and colons. It can go to supplementary material.
  - Voice: Version A (example first). No semicolons.
  - Confirmed: the three wording changes, 32 recall events, "comparison device" counts as the meter.
- Then: continue.

## Done
- `docs/paper/PAPER.md`: first prose version of the Results. 20 paragraphs, about 2,480 words, plus four captions (about 470 words).
- `docs/paper/CHECKS_RESULTS_PROSE.md`: agent check of about 165 numbers in that text. 4 errors and 13 loose spots, all fixed the same day.
- Figures 2 and 4 rebuilt with little text inside. Figure 5 (`fig5_three_faults`) replaces Table 2. Its numbers are in `tables/tableS2_three_faults.md`.
- `tables/table1_data_sources.md`: three rows, about 210 words (was 320). `tables/tableS1_analyses.md`: the old Table 3 in full sentences.
- `docs/paper/METHODS_FACTS.md`: the facts for the Methods section with sources, and five flags.
- `docs/paper/OUTLINE.md`: voice section, two new number rules, cut list, corrections, gaps G11, G14, G15.

## Decisions
- Corrected by the number check:
  - Malfunction-only pairs are about 6 in 10 false lows, not "nearly all". The three faults cover about 6 in 10 pairs in each group.
  - The sex gap changes no dose, but it does shift low alerts a little. The text said "no alert".
  - Fast-changing glucose (the sensor's delay) moves accuracy more than the first day of wear. It is now named in Results 3.5 and in Table S1 row 10.
  - "Meter 178, sensor 63" is two medians, not one real pair. Reworded.
- Dropped from the text: "the reports agree on day 1". Only Abbott reports show it, Dexcom reports do not.
- Glucose-range sorting is explained in Results 3.2, next to its numbers.
- Table 1 has three rows, to match "three data sources" in the text and in Figure 1.

## Open questions / next
- Length. Results with its figures is about 5 pages. The rubric suggests about 2, and the whole paper may be 10. Measure at the first document build (G11).
- The rubric does not mention supplements. Artemy to decide where Tables S1 and S2 go (G14).
- Message line 4 and the 3.5 heading do not name fast-changing glucose. Artemy to decide.
- Next: Artemy reads the Results. Then Methods, Discussion, Introduction, Abstract.
- Nothing committed or pushed.
