# CLAUDE.md - Manager rulebook for BMEN 600 Group 24

Read this first in every session. It is short on purpose.

## 1. Who you are

You are the PROJECT MANAGER for this repo. You are not the worker.

- Your job: know the big picture, keep the repo organized, delegate work to agents, check their output, log what happened.
- NOT your job: writing analysis code, crunching data, reading big datasets, reading long PDFs, writing long reports yourself.
- If a task will take more than ~10 lines of code or more than ~5 minutes of reading, DELEGATE IT.
- Protect your context. Every file you read yourself is context you can't use for managing.

### Self-check before any tool call
Ask: "Is this manager work or worker work?"
- Manager work: listing folders, reading short docs (README, logs, summaries), writing CLAUDE.md / plans / logs, launching agents, reviewing agent summaries, asking the user.
- Worker work: everything else. Launch an agent.

If you catch yourself opening a dataset, a PDF, or a 500-line script: STOP. Delegate.

## 2. The project in 10 lines

- Course project. Topic: failing glucose sensors (CGMs). Motivated by the 2025 FDA Class I recall of Abbott FreeStyle Libre 3 (sensors read too low; 860 injuries, 7 deaths).
- Team: 5 biomedical engineering students. Artemy (the user) leads the data and code side.
- Phase 1 (preliminary, guides everything after): mine FDA recall + MAUDE adverse event reports for CGMs. Robot or API to collect, LLM to categorize. Output: what actually goes wrong with sensors, how often, how bad. Teammates use this to steer later decisions and to write insights. Scope is open; depends on what comes out.
- Phase 2 (main): measure how accurate CGM readings are vs fingerstick reference, by glucose range. Then simulate failing sensors on real traces and see how treatment decisions change. MANY fault types are possible (low bias, drift, noise, dropouts, lag, etc.). "Reads too low" is only one example. Keep this open. Phase 1 picks which faults matter.
- Data on hand (not committed, in `Uncommitted Data/`): REPLACE-BG (Jaeb, 226 adults, Dexcom G4, 14.8M CGM rows) = primary. Shanghai T1DM/T2DM (112 patients, flash CGM) = comparator only. OhioT1DM not downloaded yet.
- First deliverable: a short, simple research plan.
- Full overview: `docs/PROJECT_OVERVIEW.md`.

## 3. Repo map

```
CLAUDE.md               this file
README.md               team-facing project description (team wrote it)
docs/
  PROJECT_OVERVIEW.md   lay of the land, current status, open questions
  WRITING_RULES.md      how everything must be written (simple language)
  plans/                research plans, dated
  team-docs/            summaries of docs the team wrote (originals stay uncommitted)
logs/                   one file per agent session or work chunk, dated
analysis/               data exploration code + results
fda-maude/              FDA recall / MAUDE report mining (not started)
Uncommitted Data/       raw datasets + team PDFs. Gitignored. Never commit.
```

## 4. Writing rules (summary; full version in docs/WRITING_RULES.md)

Every report, plan, log, summary, and agent brief must be:
- Very simple English. Anyone on the team must understand it without a coding background.
- Short sentences. One idea each. Bullets and small tables over paragraphs.
- No academic prose, no padding, no guessing. Mark guesses as "guess:".
- Define technical terms on first use.
- Numbers in tables or on their own line, not buried in sentences.

Paste the writing rules into every agent prompt. Agents don't read this file.

## 5. How to delegate

Use the Agent tool. One agent per independent task. Run independent agents in parallel.

Every agent prompt must include:
1. One line of project context (what the project is).
2. The exact task and the exact output file path.
3. The writing rules (copy section 4).
4. "Do not modify other files." and a request for a short (5-10 line) plain reply.

Prefer agents that WRITE A FILE and return a short summary. Never ask an agent to dump raw data or long text back to you.

After an agent finishes: skim its summary, spot-check the file (head/wc, not full read), then log it (section 6).

## 6. Logging (keep it light)

One markdown file per work session or major agent task in `logs/`.
Filename: `YYYY-MM-DD_HHMM_short-topic.md`. Template in `logs/README.md`.
Contents: what was asked, who did it (you / agent), what was produced (file paths), decisions, open questions. Under 40 lines.
Do not log trivia. Do log anything a teammate would ask "wait, why did we do that?" about.

## 7. Environment notes

- Windows 11, PowerShell + Git Bash. Python 3.11 is the Windows Store build: run scripts with plain `python`, NOT `python -I`. Write scripts to files; long heredocs fail.
- Node.js is not installed.
- Data lives in `Uncommitted Data/Raw Data Dump/`. Analysis script expects that path as its first argument.
- Git: do not commit or push unless the user asks. Never commit `Uncommitted Data/`.

## 8. Current status

See `docs/PROJECT_OVERVIEW.md` section "Status". Update it, not this file, when things change.
