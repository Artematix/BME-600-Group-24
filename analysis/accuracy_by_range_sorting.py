"""
accuracy_by_range_sorting.py - sensor accuracy by glucose range under three ways of sorting the pairs
(BMEN 600 Group 24).

Why
  accuracy_v2.py sorts every sensor-meter pair into a glucose range by the AVERAGE of the two values.
  Published studies usually sort by the meter (the reference) alone. The choice changes the picture a lot
  at low glucose. This script gives all three sortings for the paper's headline pair set.

Words
  CGM / sensor = continuous glucose monitor, a skin sensor that reads glucose every 5 minutes.
  meter        = fingerstick blood glucose meter, the reference.
  pair         = one sensor value with the meter value taken at the same moment (within 5 minutes).
  error        = sensor minus meter. In % it is divided by the meter value.
  MARD         = mean absolute relative difference: the average size of the error in % of the meter value,
                 ignoring direction.
  bias         = the average error with its direction kept. Negative = the sensor reads too low.
  95 % CI      = from a bootstrap: participants are re-drawn at random 1,000 times and every value is redone.

Pair set
  Set B of accuracy_v2.py: verified fingerstick pairs of all 226 participants, inside the study window.
  Built with the same code (preprocess.py and its cache). Expected: 168,990 pairs.
  These are the plain matched pairs. No delay (lag) correction.

Method
  Every number comes from accuracy_v2.range_block and accuracy_v2.Booter, unchanged. Same seed (600), same
  1,000 draws, same range edges (accuracy_v2.bin5). Only the value that picks the range changes:
    by_meter    the meter value alone
    by_sensor   the sensor value alone
    by_average  the average of the two (must reproduce accuracy_v2_stats.json)
  The script stops if the pair count is not 168,990 or if by_average does not reproduce the known MARD values.

Usage (from the repo root; plain `python -B`, a few seconds when the cache exists)
  python -B analysis/accuracy_by_range_sorting.py "Uncommitted Data/Raw Data Dump" analysis
  Argument 1 = raw data folder (only read if the cache is missing), argument 2 = output folder,
  argument 3 (optional) = cache folder.

Output (aggregates only; no per-participant rows)
  <outdir>/accuracy_by_range_sorting_stats.json   every number quoted in ACCURACY_BY_RANGE_SORTING.md
  The tables of the memo are also printed at the end of the run.
"""
import json
import os
import sys
import time

if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
    print(__doc__.strip())
    sys.exit(0)

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import preprocess as pp      # noqa: E402  (shared loading, cleaning and cache)
import accuracy_v2 as av     # noqa: E402  (bin5, range_block, Booter, SEED, N_BOOT: reused unchanged)

EXPECTED_PAIRS = 168990
EXPECTED_PEOPLE = 226
EXPECTED_AVG_MARD = {"<54": 19.6, "54-69": 16.9, "70-180": 14.2, "181-250": 11.4, ">250": 10.3}   # % (task brief)
BINS = av.BIN5
RANGE_WORDS = {"<54": "under 54", "54-69": "54 to 69", "70-180": "70 to 180", "181-250": "181 to 250", ">250": "over 250"}
SORTINGS = [  # key, column that picks the range, plain name
    ("by_meter", "ref", "the meter value alone"),
    ("by_sensor", "cgm", "the sensor value alone"),
    ("by_average", "avg", "the average of sensor and meter"),
]


def load_set_b(root, cache_dir):
    """Set B exactly as accuracy_v2.main builds it: meter pairs, in the study window, verified fingerstick."""
    pm = pp.build_pairs(root, cache_dir)["meter"]
    return pm[pm.in_study_window.to_numpy() & pm.is_verified_fingerstick.to_numpy()]


def direction(x):
    return "too low" if x < 0 else "too high"


def contrast(bt, values, bins, lab_a, lab_b):
    """Mean of `values` in range a against range b: difference and ratio, with a participant-bootstrap 95 % CI.

    Uses the same resampling weights as Booter.ratio (bt.W), so it matches the per-range intervals.
    """
    values = np.asarray(values, float)
    ma, mb = (bins == lab_a).astype(float), (bins == lab_b).astype(float)
    na, da, nb, db = bt._sums(values * ma), bt._sums(ma), bt._sums(values * mb), bt._sums(mb)
    pa, pb = na.sum() / da.sum(), nb.sum() / db.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        ba, bb = (bt.W @ na) / (bt.W @ da), (bt.W @ nb) / (bt.W @ db)
    ok = np.isfinite(ba) & np.isfinite(bb)
    d_lo, d_hi = np.percentile(ba[ok] - bb[ok], [2.5, 97.5])
    r_lo, r_hi = np.percentile(ba[ok] / bb[ok], [2.5, 97.5])
    return {"range_a": lab_a, "range_b": lab_b, "value_a": pa, "value_b": pb,
            "difference_a_minus_b": {"value": pa - pb, "ci_low": d_lo, "ci_high": d_hi},
            "ratio_a_over_b": {"value": pa / pb, "ci_low": r_lo, "ci_high": r_hi},
            "draws_used": int(ok.sum())}


def compare_with_v2(outdir, by_avg, by_cgm):
    """Compare by_average and by_sensor with accuracy_v2_stats.json (Set B), value and interval, to 4 decimals."""
    path = os.path.join(outdir, "accuracy_v2_stats.json")
    if not os.path.isfile(path):
        return {"file_found": False}
    with open(path, encoding="utf-8") as f:
        old = json.load(f)["sets"]["B"]
    worst = 0.0
    for new, key in ((by_avg, "by_avg_range"), (by_cgm, "by_cgm_range")):
        for lab in BINS:
            for met in ("bias_mgdl", "bias_pct", "mard_pct"):
                for fld in ("value", "ci_low", "ci_high"):
                    worst = max(worst, abs(new[lab][met][fld] - old[key][lab][met][fld]))
            for fld in ("n_pairs", "n_participants"):
                worst = max(worst, abs(new[lab][fld] - old[key][lab][fld]))
    return {"file_found": True, "largest_absolute_difference": f"{worst:.1e}", "identical_to_4_decimals": bool(worst < 1e-4),
            "note": "accuracy_v2_stats.json stores 4 decimals, so a difference up to 0.00005 is rounding only",
            "compared":"Set B by_avg_range and by_cgm_range: pairs, participants, MARD, bias in % and in mg/dL, each with its 95 % interval"}


def words_dir(stat, unit):
    """'5.2 % too low' style text for a bias statistic."""
    return f"{abs(stat['value']):.1f} {unit} {direction(stat['value'])}"


def words_ci(stat):
    """95 % interval of a bias in words, without minus signs."""
    lo, hi = stat["ci_low"], stat["ci_high"]
    if lo < 0 and hi < 0:
        return f"{abs(hi):.1f} to {abs(lo):.1f}"
    if lo >= 0 and hi >= 0:
        return f"{lo:.1f} to {hi:.1f}"
    return f"{abs(lo):.1f} too low to {hi:.1f} too high"


def table_md(rows):
    L = ["| Range (mg/dL) | Pairs | People | MARD, % of meter value (95 % interval) | Average direction, % of meter value (95 % interval) | Same in mg/dL |",
         "|---|---|---|---|---|---|"]
    for lab in BINS:
        r = rows[lab]
        m = r["mard_pct"]
        L.append(f"| {RANGE_WORDS[lab]} | {r['n_pairs']:,} | {r['n_participants']} | {m['value']:.1f} ({m['ci_low']:.1f} to {m['ci_high']:.1f}) | "
                 f"{words_dir(r['bias_pct'], '%')} ({words_ci(r['bias_pct'])}) | {words_dir(r['bias_mgdl'], 'mg/dL')} |")
    return "\n".join(L)


def main(root, outdir, cache_dir=pp.DEFAULT_CACHE):
    t0 = time.time()
    df = load_set_b(root, cache_dir)
    n_pairs, n_people = len(df), int(df.PtID.nunique())
    print(f"Set B: {n_pairs:,} pairs, {n_people} participants")
    if n_pairs != EXPECTED_PAIRS or n_people != EXPECTED_PEOPLE:
        sys.exit(f"STOP: expected {EXPECTED_PAIRS:,} pairs from {EXPECTED_PEOPLE} participants, found {n_pairs:,} from {n_people}. "
                 "The cache or the inclusion rule differs from accuracy_v2.py.")

    bt = av.Booter(df.PtID.to_numpy())                     # seed av.SEED, av.N_BOOT draws: the same weights as accuracy_v2 Set B
    ones = np.ones(n_pairs)
    err, rel, arel = df.err.to_numpy(float), df.rel_err_pct.to_numpy(float), df.abs_rel_err_pct.to_numpy(float)
    overall = {"n_pairs": n_pairs, "n_participants": n_people, "mard_pct": bt.ratio(arel, ones),
               "bias_pct": bt.ratio(rel, ones), "bias_mgdl": bt.ratio(err, ones)}

    bins, sortings = {}, {}
    for key, col, name in SORTINGS:
        bins[key] = av.bin5(df[col])
        rows = av.range_block(bt, df, bins[key], BINS)
        for lab in BINS:
            rows[lab]["direction_pct"] = direction(rows[lab]["bias_pct"]["value"])
            rows[lab]["direction_mgdl"] = direction(rows[lab]["bias_mgdl"]["value"])     # can differ from the % direction, see the memo
            rows[lab]["share_of_all_pairs_pct"] = rows[lab]["n_pairs"] / n_pairs * 100
        sortings[key] = {"sorted_by": name, "ranges": rows}

    # Check 2: the average sorting must reproduce the known MARD values
    got = {lab: round(sortings["by_average"]["ranges"][lab]["mard_pct"]["value"], 1) for lab in BINS}
    if got != EXPECTED_AVG_MARD:
        sys.exit(f"STOP: sorting by the average gives MARD {got}, expected {EXPECTED_AVG_MARD}.")
    v2 = compare_with_v2(outdir, sortings["by_average"]["ranges"], sortings["by_sensor"]["ranges"])
    if v2.get("file_found") and not v2["identical_to_4_decimals"]:
        sys.exit(f"STOP: numbers differ from accuracy_v2_stats.json (largest difference {v2['largest_absolute_difference']}).")
    print("checks passed: pair count; MARD by average; match with accuracy_v2_stats.json:",
          f"largest difference {v2['largest_absolute_difference']}" if v2.get("file_found") else "file not found, skipped")

    # What holds under every sorting
    CONTRASTS = {"mard_lowest_range_vs_70_180": ("<54", "70-180"), "mard_under_54_vs_54_69": ("<54", "54-69"),
                 "mard_54_69_vs_70_180": ("54-69", "70-180"), "mard_lowest_range_vs_over_250": ("<54", ">250"),
                 "mard_181_250_vs_70_180": ("181-250", "70-180"), "mard_over_250_vs_70_180": (">250", "70-180")}
    holds = {name: {key: contrast(bt, arel, bins[key], a, b) for key, _, _ in SORTINGS} for name, (a, b) in CONTRASTS.items()}
    mard = {key: {lab: sortings[key]["ranges"][lab]["mard_pct"]["value"] for lab in BINS} for key, _, _ in SORTINGS}
    bias = {key: {lab: sortings[key]["ranges"][lab]["bias_pct"]["value"] for lab in BINS} for key, _, _ in SORTINGS}
    holds["range_with_largest_mard"] = {key: max(BINS, key=lambda b: mard[key][b]) for key in mard}
    holds["range_with_smallest_mard"] = {key: min(BINS, key=lambda b: mard[key][b]) for key in mard}
    holds["mard_falls_at_every_step_from_low_to_high"] = {key: bool(all(mard[key][BINS[i]] > mard[key][BINS[i + 1]] for i in range(4))) for key in mard}
    holds["mard_falls_from_under_54_to_54_69_to_70_180"] = {key: bool(mard[key]["<54"] > mard[key]["54-69"] > mard[key]["70-180"]) for key in mard}
    holds["mard_spread_across_sortings_pct_points"] = {lab: {"min": min(mard[k][lab] for k in mard), "max": max(mard[k][lab] for k in mard)} for lab in BINS}
    holds["direction_by_range"] = {lab: {key: direction(bias[key][lab]) for key in bias} for lab in BINS}
    holds["direction_same_under_all_three"] = {lab: bool(len({direction(bias[key][lab]) for key in bias}) == 1) for lab in BINS}
    holds["bias_spread_across_sortings_pct"] = {lab: {"min": min(bias[k][lab] for k in bias), "max": max(bias[k][lab] for k in bias)} for lab in BINS}

    # How many pairs sit in a different range under the meter sorting and the sensor sorting (counts only)
    ct = pd.crosstab(pd.Categorical(bins["by_meter"], BINS), pd.Categorical(bins["by_sensor"], BINS), dropna=False)
    cross = {m: {s: int(ct.loc[m, s]) for s in BINS} for m in BINS}
    same = {lab: cross[lab][lab] for lab in BINS}
    agreement = {
        "pairs_in_same_range_by_meter_and_by_sensor": int(sum(same.values())),
        "share_of_all_pairs_pct": sum(same.values()) / n_pairs * 100,
        "of_pairs_with_meter_in_range_share_with_sensor_in_same_range_pct": {lab: same[lab] / max(1, sum(cross[lab].values())) * 100 for lab in BINS},
        "of_pairs_with_sensor_in_range_share_with_meter_in_same_range_pct": {lab: same[lab] / max(1, sum(cross[m][lab] for m in BINS)) * 100 for lab in BINS},
    }

    stats = {
        "generated": time.strftime("%Y-%m-%d %H:%M"), "script": "analysis/accuracy_by_range_sorting.py",
        "seed": av.SEED, "n_boot": av.N_BOOT, "cache_version": pp.CACHE_VERSION,
        "pair_set": "accuracy_v2.py Set B: verified fingerstick pairs (meter-log reference, not used for calibration), in the study window, "
                    "all participants and phases. Plain matched pairs, no delay correction.",
        "definitions": {
            "error": "sensor minus meter",
            "mard_pct": "mean of |sensor - meter| / meter x 100 over the pairs in the range",
            "bias_pct": "mean of (sensor - meter) / meter x 100 over the pairs in the range; negative = sensor reads too low",
            "bias_mgdl": "mean of (sensor - meter) in mg/dL over the pairs in the range",
            "within_20_20_pct": "share of pairs within 20 mg/dL (meter under 100 mg/dL) or within 20 % (meter 100 or above); from range_block, not used in the memo",
            "ci": "95 % interval, 2.5th to 97.5th percentile of a bootstrap that re-draws participants (accuracy_v2.Booter)",
            "ranges": "<54; 54-69; 70-180 (70 <= v <= 180); 181-250 (180 < v <= 250); >250 mg/dL (accuracy_v2.bin5)",
            "low_n": "true when the range has fewer than 50 pairs or fewer than 10 participants",
        },
        "checks": {"n_pairs": n_pairs, "n_pairs_expected": EXPECTED_PAIRS, "n_participants": n_people,
                   "mard_by_average_rounded": got, "mard_by_average_expected": EXPECTED_AVG_MARD, "mard_by_average_reproduced": True,
                   "match_with_accuracy_v2_stats_json": v2},
        "overall": overall,
        "sortings": sortings,
        "what_holds": holds,
        "meter_range_vs_sensor_range": {"pairs_rows_meter_columns_sensor": cross, "agreement": agreement},
        "runtime_s": round(time.time() - t0, 1),
    }
    path = os.path.join(outdir, "accuracy_by_range_sorting_stats.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(av.clean(stats), f, indent=1)
    print("wrote", path)

    # Tables for the memo
    o = overall
    print(f"\nAll pairs: {n_pairs:,} pairs, {n_people} people, MARD {o['mard_pct']['value']:.1f} % "
          f"({o['mard_pct']['ci_low']:.1f} to {o['mard_pct']['ci_high']:.1f}), {words_dir(o['bias_pct'], '%')} ({words_ci(o['bias_pct'])}), "
          f"{words_dir(o['bias_mgdl'], 'mg/dL')}")
    for key, _, name in SORTINGS:
        print(f"\n### Sorted by {name}\n")
        print(table_md(sortings[key]["ranges"]))
    print("\nMARD of one range against another (ratio, difference in % of meter value, 95 % interval):")
    for block in CONTRASTS:
        for key, _, _ in SORTINGS:
            c = holds[block][key]
            r, d = c["ratio_a_over_b"], c["difference_a_minus_b"]
            print(f"  {block:32s} {key:11s} {c['value_a']:.1f} vs {c['value_b']:.1f}: x{r['value']:.2f} ({r['ci_low']:.2f} to {r['ci_high']:.2f}), "
                  f"diff {d['value']:.1f} ({d['ci_low']:.1f} to {d['ci_high']:.1f})")
    for k in ("range_with_largest_mard", "range_with_smallest_mard", "mard_falls_at_every_step_from_low_to_high",
              "mard_falls_from_under_54_to_54_69_to_70_180", "direction_same_under_all_three"):
        print(f"  {k}: {holds[k]}")
    print("  MARD spread across sortings:", {lab: (round(x["min"], 1), round(x["max"], 1)) for lab, x in holds["mard_spread_across_sortings_pct_points"].items()})
    print("\nMeter range (rows) by sensor range (columns), pairs:")
    print(ct.to_string())
    print({k: (round(x, 1) if isinstance(x, float) else x) for k, x in agreement.items() if not isinstance(x, dict)})
    for k in ("of_pairs_with_meter_in_range_share_with_sensor_in_same_range_pct", "of_pairs_with_sensor_in_range_share_with_meter_in_same_range_pct"):
        print(" ", k, {lab: round(x, 1) for lab, x in agreement[k].items()})
    print(f"done in {time.time() - t0:.1f} s")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit('usage: python -B analysis/accuracy_by_range_sorting.py "Uncommitted Data/Raw Data Dump" analysis [cache folder]')
    main(sys.argv[1], sys.argv[2], *(sys.argv[3:4]))
