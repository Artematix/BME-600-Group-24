# Kickoff: full Phase 2 analysis and Phase 1 text step

Date: 2026-10-26 10:00
Who: manager + agents (running)
Asked by: Artemy

## Asked
- Track A: complete the preprocessing pipeline, bring methods up to current standards (not overdone), expand the analysis (demographics etc.), fish for a main finding, connect to the submitted plan.
- Track B: process the MAUDE texts with a cheap, explainable LLM-type method. Explore options, draft methods, iterate, run if simple. Use the GPU. Write down the reasoning at each step.

## Found at start
- Pulled 2 upstream commits (Oct 14, Oct 23): Phase 1 structured pull done on another machine (3.38M reports; 123,607 serious; 5,193 weighted sample). Final project due Dec 4.
- Raw/clean MAUDE files are not on this machine. No OPENFDA_API_KEY here.
- GPU: RTX 5080 16 GB. torch + CUDA work. Ollama installed. No vLLM on Windows.
- My stash of two tiny edits conflicted with the upstream overview. Took the upstream version.

## Done so far
- analysis/METHODOLOGY.md and fda-maude/METHODOLOGY.md: research logs with the reasoning (entry 1 each).
- Agents launched: methods standards review; submitted-plan summary; MAUDE re-pull/flatten; text-method options; preprocessing audit + shared module.

## Progress 2026-10-27 03:15
- Done: METHODS_REVIEW.md (12 'do these' items; calibration pairs contaminate the headline MARD; v1 simulation measures the glucose distribution, not the sensor). Midterm-plan summary (promised methods list = contract). OPTIONS.md (Abbott texts are templated: values, Parkes zone, wear day; Dexcom serious = prose; chosen pipeline = codes -> regex -> local LLM form -> gold set).
- Launched: extraction pilot on GPU (Ollama qwen2.5:7b-instruct, JSON schema) and gold-set labelling (287 reports by careful reading).
- All four workers hit the session rate limit at about 00:15 and were resumed at 03:15. Partial work was on disk: preprocess.py, MAUDE clean tables (full + serious), regex and prompt files, gold labels through batch 10.

## Decisions
- Text step scope: serious subset + weighted sample, not all 3.4M. Regex on everything later.
- Fishing rules for subgroups: participant as unit, pre-specified vs exploratory lists, BH correction, min 10 per group, CIs.

## Open questions / next
- User: copy fda-maude/raw and clean from the other machine, or set the API key here.
- After agents: expanded analysis agents; text pilot on GPU.
