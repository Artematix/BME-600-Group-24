#!/usr/bin/env python
"""
build_run_set.py : builds the set of reports the text pipeline runs on (Phase 1, BMEN 600 Group 24).

Two parts
(a) Serious tier: every Death or Injury report in clean/serious.csv.gz that has text and was received
    at least --months months before the FDA snapshot date (texts arrive late).
(b) Malfunction sample: a stratified random sample of Malfunction reports drawn locally from
    clean/full.parquet. Strata = product code x year received. Each stratum gets a share of --sample-size
    in proportion to its size; a stratum with at least --min-per-stratum reports gets at least that many;
    smaller strata are taken whole. Simple random sampling inside each stratum, fixed seed.
    Weight = stratum size / stratum sample size, so weighted counts scale to all malfunction reports
    in the frame. The frame is limited to the same received-date cutoff as (a), so every sampled report
    can have text.

Outputs
  clean/sample_local.parquet   the malfunction sample, all columns + stratum, sel_prob, weight, weight_norm
  clean/run_set.csv.gz         (a) + (b) with text, one row per report, columns the extractors expect
  results/text/RUN_SET.md      the definition and the counts (small, goes in git)

Usage
  python fda-maude/scripts/build_run_set.py --clean fda-maude/clean --results fda-maude/results/text
      [--snapshot 2026-10-21] [--months 3] [--sample-size 5000] [--min-per-stratum 25] [--seed 20261019]
"""

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

TEXT_COLS = ["mdr_report_key", "report_number", "date_received", "date_of_event", "event_type", "product_code",
             "brand_name", "manufacturer", "product_problems", "patient_problems", "patient_outcome",
             "event_text", "mfr_narrative"]
H10_MIN_CHARS = 20   # a manufacturer narrative this short is only a redaction mark like "(B)(4)."


def log(msg, t0):
    print(f"[{time.time() - t0:7.1f}s] {msg}", flush=True)


def has_text(df):
    """True when the event text is non-empty or the manufacturer narrative is longer than H10_MIN_CHARS."""
    d5 = df["event_text"].fillna("").str.strip().ne("")
    h10 = df["mfr_narrative"].fillna("").str.strip().str.len() > H10_MIN_CHARS
    return d5 | h10


def maker_label(manufacturer, brand):
    """Abbott / Dexcom / Medtronic / Other from manufacturer and brand strings (same words as extract_regex)."""
    s = (str(manufacturer) + " " + str(brand)).upper()
    if "ABBOTT" in s or "LIBRE" in s:
        return "Abbott"
    if "DEXCOM" in s:
        return "Dexcom"
    if any(w in s for w in ("MEDTRONIC", "MINIMED", "GUARDIAN", "SIMPLERA", "ENLITE")):
        return "Medtronic"
    return "Other"


def serious_set(clean, cutoff, t0):
    """Part (a): serious reports with text, received on or before the cutoff."""
    s = pd.read_csv(clean / "serious.csv.gz", dtype=str, usecols=TEXT_COLS)
    log(f"serious.csv.gz: {len(s):,} rows", t0)
    s = s[s["event_type"].isin(["Death", "Injury"])]
    dr = pd.to_datetime(s["date_received"], format="%Y%m%d", errors="coerce")
    old = dr <= cutoff
    txt = has_text(s)
    counts = {"serious_rows": len(s), "received_by_cutoff": int(old.sum()), "with_text": int(txt.sum()),
              "eligible": int((old & txt).sum()), "dropped_too_recent": int((~old).sum()),
              "dropped_no_text_old": int((old & ~txt).sum())}
    out = s[old & txt].copy()
    out["tier"] = "serious"
    out["stratum"] = ""
    out["sel_prob"] = 1.0
    out["weight"] = 1.0
    log(f"serious eligible: {len(out):,} (too recent {counts['dropped_too_recent']:,}, no text {counts['dropped_no_text_old']:,})", t0)
    return out, counts


def allocate(sizes, total, min_per):
    """Sample size per stratum: proportional share of total, at least min_per when the stratum has min_per
    or more reports, the whole stratum when it is smaller."""
    N = sizes.sum()
    alloc = {}
    for h, Nh in sizes.items():
        share = int(round(total * Nh / N))
        if Nh >= min_per:
            alloc[h] = min(Nh, max(min_per, share))
        else:
            alloc[h] = int(Nh)
    return pd.Series(alloc)


def sample_set(clean, cutoff, size, min_per, seed, t0):
    """Part (b): stratified simple random sample of Malfunction reports from full.parquet."""
    pf = pq.ParquetFile(clean / "full.parquet")
    frame = pf.read(columns=["mdr_report_key", "event_type", "product_code", "date_received"]).to_pandas()
    log(f"full.parquet: {len(frame):,} rows read (4 columns)", t0)
    frame = frame[frame["event_type"] == "Malfunction"].copy()
    n_malf_all = len(frame)
    dr = pd.to_datetime(frame["date_received"], format="%Y%m%d", errors="coerce")
    frame = frame[dr <= cutoff].copy()
    frame["year"] = frame["date_received"].str[:4]
    frame["stratum"] = frame["product_code"].fillna("") + "_" + frame["year"].fillna("")
    sizes = frame.groupby("stratum").size().sort_index()
    alloc = allocate(sizes, size, min_per)
    log(f"malfunction frame: {len(frame):,} of {n_malf_all:,} (received by cutoff); {len(sizes)} strata; planned sample {int(alloc.sum()):,}", t0)

    rng = np.random.default_rng(seed)
    picks = []
    frame = frame.sort_values(["stratum", "mdr_report_key"]).reset_index(drop=True)
    for h in sizes.index:                      # sorted order -> same draws every run
        idx = frame.index[frame["stratum"] == h].to_numpy()
        n_h = int(alloc[h])
        chosen = rng.choice(idx, size=n_h, replace=False) if n_h < len(idx) else idx
        picks.append(pd.DataFrame({"mdr_report_key": frame.loc[chosen, "mdr_report_key"].to_numpy(), "stratum": h,
                                   "stratum_size": int(sizes[h]), "stratum_sample": n_h}))
    picks = pd.concat(picks, ignore_index=True)
    picks["sel_prob"] = picks["stratum_sample"] / picks["stratum_size"]
    picks["weight"] = picks["stratum_size"] / picks["stratum_sample"]
    picks["weight_norm"] = picks["weight"]      # simple random sampling: weights already sum to the stratum size
    log(f"drawn {len(picks):,} reports; weights sum {picks['weight'].sum():,.0f} = frame size", t0)

    # all columns for the sampled rows, read row group by row group
    keys = set(picks["mdr_report_key"])
    parts = []
    for i in range(pf.metadata.num_row_groups):
        tbl = pf.read_row_group(i).to_pandas()
        parts.append(tbl[tbl["mdr_report_key"].isin(keys)])
    full = pd.concat(parts, ignore_index=True)
    full = full.merge(picks[["mdr_report_key", "stratum", "stratum_size", "stratum_sample", "sel_prob", "weight", "weight_norm"]], on="mdr_report_key", how="inner")
    full["has_text"] = has_text(full)
    log(f"sample rows with all columns: {len(full):,}; with text {int(full['has_text'].sum()):,}", t0)
    counts = {"malfunction_all": n_malf_all, "malfunction_frame": len(frame), "n_strata": len(sizes),
              "strata_taken_whole": int((alloc >= sizes).sum()), "sample_drawn": len(picks),
              "sample_with_text": int(full["has_text"].sum()), "min_weight": float(picks["weight"].min()),
              "max_weight": float(picks["weight"].max()), "seed": seed}
    return full, sizes, alloc, counts


def df_md(df):
    """Small markdown table from a DataFrame (the index becomes the first column)."""
    d = df.reset_index()
    header = "| " + " | ".join(str(c) for c in d.columns) + " |"
    sep = "|" + "---|" * len(d.columns)
    rows = ["| " + " | ".join(f"{v:,}" if isinstance(v, (int, np.integer)) else str(v) for v in r) + " |" for r in d.itertuples(index=False)]
    return chr(10).join([header, sep] + rows)


def write_md(path, args, cutoff, s_counts, m_counts, run, sizes, alloc, sample):
    """RUN_SET.md: definition, counts, and how the local sample differs from the API sample."""
    by_maker = run.groupby(["tier", "maker"]).size().unstack(fill_value=0)
    by_maker["All"] = by_maker.sum(axis=1)
    strata = pd.DataFrame({"reports": sizes, "sampled": alloc}).reset_index().rename(columns={"index": "stratum"})
    strata["code"] = strata["stratum"].str.split("_").str[0]
    by_code = strata.groupby("code")[["reports", "sampled"]].sum().sort_values("reports", ascending=False)
    txt_by_maker = sample.groupby(sample.apply(lambda r: maker_label(r["manufacturer"], r["brand_name"]), axis=1))["has_text"].agg(["size", "mean"]).rename_axis("maker")

    L = ["# Run set for the text pipeline", "",
         f"Built {time.strftime('%Y-%m-%d')} by `scripts/build_run_set.py`. FDA snapshot {args.snapshot}; cutoff for text = received on or before {cutoff.date()} ({args.months} months before the snapshot).",
         "Words: tier = part of the data (serious = death + injury reports; sample = random malfunction reports). Stratum = group of reports (product code x year received). Weight = how many malfunction reports one sampled report stands for.", "",
         "## 1. Definition", "",
         "| Part | Rule |", "|---|---|",
         f"| (a) serious | event_type Death or Injury; received on or before {cutoff.date()}; has text (event text non-empty, or manufacturer narrative longer than {H10_MIN_CHARS} characters) |",
         f"| (b) sample | Malfunction reports received on or before {cutoff.date()}; strata = product code x year; target {args.sample_size:,}; at least {args.min_per_stratum} per stratum when the stratum has that many, smaller strata taken whole; simple random sampling, seed {args.seed} |",
         "| run set | (a) + (b) rows that have text. Order in the file: sample first (by key), then serious in random order (seed 20261019), so a partial run is a random subset |", "",
         "## 2. Counts", "",
         "| Step | Reports |", "|---|---|",
         f"| serious rows (Death + Injury) | {s_counts['serious_rows']:,} |",
         f"| received on or before cutoff | {s_counts['received_by_cutoff']:,} |",
         f"| dropped: too recent | {s_counts['dropped_too_recent']:,} |",
         f"| dropped: no text | {s_counts['dropped_no_text_old']:,} |",
         f"| (a) serious eligible | {s_counts['eligible']:,} |",
         f"| malfunction reports, all | {m_counts['malfunction_all']:,} |",
         f"| malfunction frame (received by cutoff) | {m_counts['malfunction_frame']:,} |",
         f"| strata (taken whole) | {m_counts['n_strata']} ({m_counts['strata_taken_whole']}) |",
         f"| (b) sample drawn | {m_counts['sample_drawn']:,} |",
         f"| (b) sample with text | {m_counts['sample_with_text']:,} |",
         f"| weight range | {m_counts['min_weight']:.1f} to {m_counts['max_weight']:.1f} |",
         f"| **run set (a + b with text)** | **{len(run):,}** |", "",
         "Run set by tier and maker:", "", df_md(by_maker), "",
         "Sample text availability by maker (share with text):", "",
         df_md(txt_by_maker.rename(columns={"size": "sampled", "mean": "with text"}).assign(**{"with text": lambda d: (d["with text"] * 100).round(0).astype(int).astype(str) + "%"})), "",
         "Sample allocation by product code (frame reports and sampled):", "", df_md(by_code), "",
         "## 3. How this sample differs from the earlier API-drawn sample (tier 3, 5,193 reports)", "",
         "- Same strata (product code x year), same target (5,000), same minimum (25), same seed (20261019).",
         "- Drawn locally from the full table, so it is a simple random sample inside each stratum. The API sample used clusters of up to 10 neighbouring reports on busy days, with a selection probability per report. Here every report in a stratum has the same chance, so `weight` = stratum size / sampled, and `weight_norm` equals `weight`.",
         f"- Frame limited to reports received on or before {cutoff.date()} so that every sampled report can have text. The API sample included reports up to the 2026-10-07 snapshot.",
         "- The FDA data are the 2026-10-21 snapshot (bulk files), not the 2026-10-07 API snapshot. Counts differ a little.",
         "- Different reports are picked (different method), so results are not row-for-row comparable with the API sample. Weighted totals should agree within sampling error.", "",
         "## 4. Files", "",
         "| File | Rows | In git? |", "|---|---|---|",
         f"| `clean/sample_local.parquet` | {len(sample):,} | no (rebuild with the script) |",
         f"| `clean/run_set.csv.gz` | {len(run):,} | no |",
         "| `results/text/RUN_SET.md` | this file | yes |", ""]
    path.write_text("\n".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Build the text-pipeline run set: serious reports with text + a local weighted malfunction sample.")
    ap.add_argument("--clean", default="fda-maude/clean")
    ap.add_argument("--results", default="fda-maude/results/text")
    ap.add_argument("--snapshot", default="2026-10-21", help="FDA data snapshot date (DATA_NOTES.md)")
    ap.add_argument("--months", type=int, default=3, help="texts arrive late: only reports at least this old")
    ap.add_argument("--sample-size", type=int, default=5000)
    ap.add_argument("--min-per-stratum", type=int, default=25)
    ap.add_argument("--seed", type=int, default=20261019)
    args = ap.parse_args()

    t0 = time.time()
    clean, results = Path(args.clean), Path(args.results)
    results.mkdir(parents=True, exist_ok=True)
    cutoff = pd.Timestamp(args.snapshot) - pd.DateOffset(months=args.months)
    log(f"cutoff: received on or before {cutoff.date()}", t0)

    serious, s_counts = serious_set(clean, cutoff, t0)
    sample, sizes, alloc, m_counts = sample_set(clean, cutoff, args.sample_size, args.min_per_stratum, args.seed, t0)
    sample.to_parquet(clean / "sample_local.parquet", index=False)
    log(f"wrote {clean / 'sample_local.parquet'}", t0)

    smp = sample[sample["has_text"]][TEXT_COLS + ["stratum", "sel_prob", "weight"]].copy()
    smp["tier"] = "sample"
    smp = smp.sort_values("mdr_report_key")
    rng = np.random.default_rng(20261019)
    serious = serious.iloc[rng.permutation(len(serious))]
    cols = TEXT_COLS + ["tier", "stratum", "sel_prob", "weight"]
    run = pd.concat([smp[cols], serious[cols]], ignore_index=True)
    run["split"] = run["tier"]
    run["maker"] = [maker_label(m, b) for m, b in zip(run["manufacturer"], run["brand_name"])]
    assert run["mdr_report_key"].is_unique, "duplicate keys in the run set"
    run.to_csv(clean / "run_set.csv.gz", index=False, compression="gzip")
    log(f"wrote {clean / 'run_set.csv.gz'}: {len(run):,} rows (sample {len(smp):,} + serious {len(serious):,})", t0)

    write_md(results / "RUN_SET.md", args, cutoff, s_counts, m_counts, run, sizes, alloc, sample)
    log(f"wrote {results / 'RUN_SET.md'}; done", t0)


if __name__ == "__main__":
    main()
