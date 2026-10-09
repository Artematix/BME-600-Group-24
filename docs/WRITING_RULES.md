# Writing rules

These rules apply to EVERYTHING written in this repo: reports, plans, logs, summaries, agent prompts, code comments.
Why: the team comes from different backgrounds, not all with coding or statistics. Simple text is also cheaper for AI context and easier to search later. We turn it into academic language ourselves at the end.

## The rules

1. Very simple English. Anyone with no technical background must understand it.
2. Short sentences. About 15 words max. One idea per sentence.
3. Bullets and small tables, not paragraphs. Jot-note style is fine.
4. Big ideas first. Details after.
5. No academic prose. No padding. No "it is worth noting that".
6. No guessing presented as fact. If you guess, write "guess:" in front.
7. Define technical terms the first time. Example: "MARD = the sensor's average percent error".
8. Numbers go in tables or on their own line, not inside sentences.
9. Say what something means for the project, not just what it is.
10. Keep files short. Summaries under ~100 lines. Reports under ~200 lines. If longer, split or add a "detailed" version.

## Common terms (use these definitions)

| Term | Plain meaning |
|---|---|
| CGM | Continuous glucose monitor. A sensor under the skin that reads blood sugar every 5 minutes. |
| Fingerstick / BGM / reference glucose | A blood drop meter reading. We treat it as the "true" value. |
| mg/dL | Units for blood sugar. 70 = low. 70-180 = normal. 180+ = high. |
| Hypoglycaemia (hypo) | Low blood sugar, below 70 mg/dL. Dangerous. |
| Hyperglycaemia | High blood sugar, above 180 mg/dL. |
| Bias | Does the sensor read too high or too low on average? |
| MARD | Mean Absolute Relative Difference. The sensor's average percent error. Lower is better. |
| Error grid (Clarke / consensus) | A chart that sorts sensor errors into "harmless" vs "dangerous" zones. |
| HbA1c | A blood test for average blood sugar over ~3 months. |
| MAUDE | FDA's database of medical device problem reports. |
| Pair | One CGM reading matched to one fingerstick taken at the same time. |

## Example

Bad:
> The analysis demonstrates a statistically meaningful negative systematic deviation of CGM-derived glucose values relative to capillary reference measurements across euglycaemic and hyperglycaemic strata.

Good:
> The sensor reads too low in the normal and high ranges.
> - Normal range: 3-5% too low
> - High range: 3-5% too low
> This matches the Libre 3 recall problem.
