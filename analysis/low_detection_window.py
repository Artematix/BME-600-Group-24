"""
low_detection_window.py - how many true lows does the sensor show, when "shown" is counted the way
published clinic studies count it? (BMEN 600 Group 24)

Why
  Our paper says: 31 % of true lows (meter under 70 mg/dL) were not shown as low by the sensor.
  That number compares one fingerstick with ONE sensor reading (the matched one).
  Published clinic studies count a low as detected if the sensor was under the threshold at ANY time in a
  window around the reference reading (15 minutes before or after; some use 30).
  This script counts our lows both ways, so the two numbers can be compared like for like.

Words
  sensor (CGM) = continuous glucose monitor, a skin sensor that stores one reading every 5 minutes.
  meter        = fingerstick blood glucose meter. Its value is the reference here.
  pair         = one meter value with the nearest sensor reading within 5 minutes (the "matched reading").
  true low     = a pair whose meter value is under the meter threshold (70 or 54 mg/dL).
  shown        = the sensor is under the sensor threshold (70 or 54 mg/dL) under the rule in use.
  not shown    = a true low that is not shown. This is the share the paper quotes.
  sensor low   = a pair whose matched sensor reading is under 70 mg/dL.
  signal gap   = no sensor reading at all in the window. Counted on its own, never as "not shown".
  95 % CI      = confidence interval, the range the true value most likely sits in. Here it comes from a
                 bootstrap: the participants are re-drawn at random 2,000 times (fixed seed) and every share
                 is counted again.

Pair sets (built exactly as in accuracy_v2.py, through preprocess.py and the cache)
  all 226 = verified fingerstick pairs, study window, all participants (accuracy_v2 Set B).
  arm     = the same pairs, CGM+BGM arm, randomised phase only (accuracy_v2 Set A, 77 people). A check.

Rules for "shown" (the fingerstick time is the centre of every window; the ends of a window count)
  matched    the matched reading only. This is the existing number.
  within 15  any sensor reading from 15 minutes before to 15 minutes after the fingerstick.
  within 30  the same with 30 minutes.
  before 15  any reading from 15 minutes before up to the fingerstick time.
  after 15   any reading from the fingerstick time up to 15 minutes after.
  The windows use the full 5-minute sensor trace from the cache (repeated time stamps dropped, as in the pairs).

Counts made
  1. For each true low: shown or not shown, under each rule. Three cases: meter under 70 with sensor
     threshold 70; meter under 54 with sensor threshold 70; meter under 54 with sensor threshold 54.
  2. The mirror: for each sensor low (matched reading under 70), was the meter 70 or above (not
     confirmed), and was it 80 or above (a softer check).
  3. Signal gaps: true lows with no sensor reading in a window; and verified fingersticks that never
     became a pair because no sensor reading lay within 5 minutes.
  4. Every share: 95 % CI, and the per-participant median with quartiles for people with at least 10 events.

Usage (from the repo root; plain `python`, a few seconds once the cache exists)
  python analysis/low_detection_window.py "Uncommitted Data/Raw Data Dump" analysis
  Argument 1 = raw data folder, argument 2 = output folder, argument 3 (optional) = cache folder.

Output (aggregates only; no per-participant files)
  <outdir>/low_detection_window_stats.json     every number quoted in LOW_DETECTION_WINDOW.md
  The results table of the memo is also printed at the end of the run.
"""
import json
import os
import sys
import time

if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
    print(__doc__.strip())
    sys.exit(0)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np
import pandas as pd
import preprocess as pp          # shared cache: the verified pair set, the meter table and the sensor trace
import accuracy_v2 as av2        # the participant bootstrap (Booter) and the JSON cleaner

T0 = time.time()
SEED = av2.SEED                  # 600, the seed accuracy_v2.py uses
N_BOOT = 2000                    # bootstrap resamples (participants drawn with replacement)
MIN_EVENTS = 10                  # a person enters the per-participant summary with at least this many events
MIRROR_CUTS = [70, 80]           # sensor lows: meter at or above 70 = not confirmed; at or above 80 = softer check
EXPECT = {"all_226": (168990, 226), "arm_77": (33467, 77)}         # pairs and people, from ACCURACY_V2.md; the script stops on any other count
V2_SET = {"all_226": "B", "arm_77": "A"}                            # the same sets in accuracy_v2_stats.json
V2_STATS = os.path.join(HERE, "accuracy_v2_stats.json")             # source of the numbers in ACCURACY_V2.md
SET_LABELS = {"all_226": "All 226 participants: verified fingerstick pairs, study window, run-in and randomised phase",
              "arm_77": "Check: CGM+BGM arm, randomised phase"}
PUBLISHED = {"low_alert_detection_pct_low": 86, "low_alert_detection_pct_high": 91, "threshold_mgdl": 70,     # not computed here
             "source": "docs/paper/OUTLINE.md, point D2 (b), and the task brief; published clinic studies, not re-checked in this script"}

# The three cases: key, meter threshold, sensor threshold (mg/dL).
CASES = [("meter_under_70_sensor_under_70", 70, 70),
         ("meter_under_54_sensor_under_70", 54, 70),
         ("meter_under_54_sensor_under_54", 54, 54)]
# The five rules: key, plain label, seconds before the fingerstick, seconds after it (None = the matched reading only).
RULES = [("matched", "matched reading only", None, None),
         ("within_15", "any reading within 15 min before or after", 900, 900),
         ("within_30", "any reading within 30 min before or after", 1800, 1800),
         ("before_15", "any reading in the 15 min before", 900, 0),
         ("after_15", "any reading in the 15 min after", 0, 900)]
STRIDE, OFFSET = 10 ** 10, 10 ** 9   # used to give every sensor reading one sortable number (see Trace)


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


# --------------------------------------------------------------------------
# The sensor trace, set up for window look-ups
# --------------------------------------------------------------------------
class Trace:
    """The full 5-minute sensor trace of every participant.

    Every reading gets one number: participant number x STRIDE + time in seconds. The readings are sorted
    by that number, so "all readings of this person between two times" is one slice of the array."""

    def __init__(self, cgm):
        t = cgm.t.to_numpy("int64")
        if np.abs(t).max() >= OFFSET - 3600:
            sys.exit("STOP: a sensor time is outside the range this script expects.")
        key = cgm.PtID.to_numpy("int64") * STRIDE + t + OFFSET
        order = np.argsort(key, kind="stable")
        self.key = key[order]
        self.glucose = cgm.glucose.to_numpy(float)[order]

    def _slices(self, ptid, t, before_s, after_s):
        base = np.asarray(ptid, "int64") * STRIDE + np.asarray(t, "int64") + OFFSET
        return np.searchsorted(self.key, base - before_s, "left"), np.searchsorted(self.key, base + after_s, "right")

    def count(self, ptid, t, before_s, after_s):
        """Number of readings from before_s seconds before t to after_s seconds after t (ends included)."""
        lo, hi = self._slices(ptid, t, before_s, after_s)
        return hi - lo

    def lowest(self, ptid, t, before_s, after_s):
        """Lowest sensor value in the same window (NaN when the window holds no reading), and the number of readings."""
        lo, hi = self._slices(ptid, t, before_s, after_s)
        low = np.full(len(lo), np.nan)
        for i in np.flatnonzero(hi > lo):
            low[i] = self.glucose[lo[i]:hi[i]].min()
        return low, hi - lo


# --------------------------------------------------------------------------
# Data: pairs, fingersticks that never became a pair, and the checks asked for
# --------------------------------------------------------------------------
def load_events(root, cache):
    """One row per verified fingerstick in the study window. Pairs first, then fingersticks without a pair.

    Columns: PtID, t (fingerstick time, seconds), ref (meter), cgm (matched sensor reading; NaN without a
    pair), is_pair, in_arm (CGM+BGM arm and randomised phase = accuracy_v2 Set A)."""
    pairs = pp.build_pairs(root, cache)
    part = pp.load_participants(root, cache)[["PtID", "arm", "randomisation_day"]]
    b = pairs["verified"][["PtID", "t", "day", "ref", "cgm"]]               # the headline pair set (accuracy_v2 Set B)
    cgm = pp.load_cgm(root, cache)[["PtID", "t", "glucose"]]                # repeated time stamps already dropped
    cgm = cgm[cgm.glucose.notna()]
    trace = Trace(cgm)
    log(f"sensor trace: {len(cgm):,} readings from {cgm.PtID.nunique()} people")
    n_trace = int(len(cgm))
    del cgm

    # Verified fingersticks with no sensor reading within 5 minutes never became a pair. Find them with the pair rules.
    bgm = pp.load_bgm(root, cache)
    v = bgm[bgm.is_verified_fingerstick & bgm.in_study_window & ~bgm.value_out_of_range]
    v = v[["PtID", "t", "day", "value"]].rename(columns={"value": "ref"})
    near = trace.count(v.PtID.to_numpy(), v.t.to_numpy(), pp.METER_PAIR_TOL_S, pp.METER_PAIR_TOL_S)
    recount = {"verified_fingersticks": int(len(v)), "with_a_reading_within_5_min": int((near > 0).sum()), "pairs_in_cache": int(len(b)),
               "ok": bool(int((near > 0).sum()) == len(b))}
    if not recount["ok"]:
        sys.exit(f"STOP: {recount['with_a_reading_within_5_min']:,} verified fingersticks have a sensor reading within 5 minutes, "
                 f"but the cache holds {len(b):,} pairs. The trace and the pair set do not agree.")
    u = v[near == 0]
    ev = pd.DataFrame({c: np.concatenate([b[c].to_numpy(), u[c].to_numpy()]) for c in ("PtID", "t", "day", "ref")})
    ev["cgm"] = np.concatenate([b.cgm.to_numpy(float), np.full(len(u), np.nan)])
    ev["is_pair"] = np.arange(len(ev)) < len(b)
    ev = ev.merge(part, on="PtID", how="left")
    ev["in_arm"] = (ev.arm.astype(str) == "CGM+BGM") & (ev.day >= ev.randomisation_day)      # same rule as accuracy_v2.py
    return ev, trace, {"sensor_readings_in_trace": n_trace, "pair_recount": recount}


def point_in_time_check(found):
    """Compare the matched-reading counts with accuracy_v2_stats.json (the source of ACCURACY_V2.md). Stop on any difference."""
    if not os.path.isfile(V2_STATS):
        sys.exit(f"STOP: {V2_STATS} is missing, so the matched-reading numbers cannot be checked.")
    with open(V2_STATS, encoding="utf-8") as f:
        v2 = json.load(f)
    out, bad = {}, []
    for skey, f_ in found.items():
        s = v2["sets"][V2_SET[skey]]
        c70 = s["misclassification"]["hypo_detection"]["70"]["counts"]
        c54 = s["misclassification"]["hypo_detection"]["54"]["counts"]
        expected = {"pairs": s["definition_counts"]["n_pairs"], "participants": s["definition_counts"]["n_participants"],
                    "true_lows_meter_under_70": c70["TP"] + c70["FN"], "not_shown_at_70": c70["FN"],
                    "sensor_lows_under_70": c70["TP"] + c70["FP"], "not_confirmed_at_70": c70["FP"],
                    "true_lows_meter_under_54": c54["TP"] + c54["FN"], "not_shown_at_54": c54["FN"]}
        if (f_["pairs"], f_["participants"]) != EXPECT[skey]:
            bad.append(f"{skey}: expected {EXPECT[skey][0]:,} pairs from {EXPECT[skey][1]} people, this script has {f_['pairs']:,} from {f_['participants']}")
        rows = {k: {"accuracy_v2": int(expected[k]), "here": int(f_[k]), "ok": bool(int(expected[k]) == int(f_[k]))} for k in expected}
        rows["not_shown_at_70_pct"] = {"accuracy_v2": s["misclassification"]["70_180"]["rates"]["missed_low_pct"]["value"],
                                       "here": 100.0 * f_["not_shown_at_70"] / f_["true_lows_meter_under_70"]}
        rows["not_confirmed_at_70_pct"] = {"accuracy_v2": 100.0 - s["misclassification"]["hypo_detection"]["70"]["ppv_pct"]["value"],
                                           "here": 100.0 * f_["not_confirmed_at_70"] / f_["sensor_lows_under_70"]}
        for k in ("not_shown_at_70_pct", "not_confirmed_at_70_pct"):
            rows[k]["ok"] = bool(abs(rows[k]["accuracy_v2"] - rows[k]["here"]) < 0.001)
        bad += [f"{skey}: {k}: accuracy_v2 has {r['accuracy_v2']}, this script has {r['here']}" for k, r in rows.items() if not r["ok"]]
        out[skey] = rows
    if bad:
        sys.exit("STOP: the matched-reading numbers do not match ACCURACY_V2.md.\n  " + "\n  ".join(bad))
    return out


# --------------------------------------------------------------------------
# Shares with a CI and a per-participant summary
# --------------------------------------------------------------------------
def share(bt, yes, base):
    """Share of `base` events that are `yes`, in %: value, 95 % CI, counts, and the per-participant summary."""
    yes, base = yes.astype(float), base.astype(float)
    r = bt.ratio(yes * 100.0, base)
    n_yes, n_base = bt._sums(yes), bt._sums(base)                 # per participant
    keep = n_base >= MIN_EVENTS
    q1, med, q3 = np.percentile(n_yes[keep] / n_base[keep] * 100.0, [25, 50, 75]) if keep.any() else (np.nan,) * 3
    return {"counted": int(base.sum()), "yes": int(yes.sum()), "participants": int(r["n_participants"]),
            "share_pct": {"value": r["value"], "ci_low": r["ci_low"], "ci_high": r["ci_high"]},
            "opposite_share_pct": {"value": 100.0 - r["value"], "ci_low": 100.0 - r["ci_high"], "ci_high": 100.0 - r["ci_low"]},
            "per_participant": {"min_events": MIN_EVENTS, "participants": int(keep.sum()), "median_pct": float(med), "q1_pct": float(q1), "q3_pct": float(q3)}}


def analyse(ev, trace, label):
    """Every count for one set of events (pairs plus the fingersticks without a pair of the same people)."""
    n = len(ev)
    bt = av2.Booter(ev.PtID.to_numpy(), seed=SEED, n_boot=N_BOOT)
    ref, cgm, is_pair = ev.ref.to_numpy(float), ev.cgm.to_numpy(float), ev.is_pair.to_numpy(bool)
    n_people = int(ev.PtID[is_pair].nunique())
    if bt.P != n_people:
        sys.exit(f"STOP: {bt.P - n_people} people have fingersticks but no pair in set '{label}'.")

    # Lowest sensor value and number of readings in every window, for every meter value under 70 (this covers under 54).
    low = ref < 70
    ptid, t = ev.PtID.to_numpy()[low], ev.t.to_numpy()[low]
    lowest, count = {"matched": cgm}, {"matched": is_pair.astype(int)}
    for rkey, _, before_s, after_s in RULES[1:]:
        lowest[rkey], count[rkey] = np.full(n, np.nan), np.zeros(n, dtype=int)
        lowest[rkey][low], count[rkey][low] = trace.lowest(ptid, t, before_s, after_s)
    # Checks on the window logic, on the pairs: the matched reading lies inside the 15-minute window, the 15-minute
    # window lies inside the 30-minute one, and "before" plus "after" together are the 15-minute window.
    pl = low & is_pair
    ok = bool(np.all(lowest["within_15"][pl] <= cgm[pl]) and np.all(lowest["within_30"][pl] <= lowest["within_15"][pl])
              and np.all(np.fmin(lowest["before_15"][pl], lowest["after_15"][pl]) == lowest["within_15"][pl]))
    if not ok:
        sys.exit(f"STOP: the window logic check failed in set '{label}'.")

    cases = {}
    for ckey, m_thr, s_thr in CASES:
        true_low = is_pair & (ref < m_thr)
        rules = {}
        for rkey, rlabel, before_s, after_s in RULES:
            has = true_low & (count[rkey] > 0)                    # a sensor reading exists in the window
            not_shown = has & ~(lowest[rkey] < s_thr)
            row = share(bt, not_shown, has)
            rules[rkey] = {"rule": rlabel, "true_lows": int(true_low.sum()), "no_reading_in_window": int((true_low & (count[rkey] == 0)).sum()),
                           "counted": row["counted"], "not_shown": row["yes"], "shown": row["counted"] - row["yes"], "participants": row["participants"],
                           "not_shown_pct": row["share_pct"], "shown_pct": row["opposite_share_pct"],
                           "per_participant_not_shown_pct": row["per_participant"],
                           "readings_in_window_median": float(np.median(count[rkey][has]))}
        cases[ckey] = {"meter_threshold_mgdl": m_thr, "sensor_threshold_mgdl": s_thr, "true_lows": int(true_low.sum()),
                       "participants_with_a_true_low": bt.n_part(true_low), "rules": rules}

    # The mirror: sensor lows (matched reading under 70) that the meter did not confirm.
    sensor_low = is_pair & (cgm < 70)
    mirror = {"sensor_threshold_mgdl": 70, "sensor_lows": int(sensor_low.sum()), "participants_with_a_sensor_low": bt.n_part(sensor_low)}
    for cut in MIRROR_CUTS:
        row = share(bt, sensor_low & (ref >= cut), sensor_low)
        mirror[f"meter_{cut}_or_above"] = {"rule": f"meter {cut} mg/dL or above", "counted": row["counted"], "not_confirmed": row["yes"],
                                           "confirmed": row["counted"] - row["yes"], "participants": row["participants"],
                                           "not_confirmed_pct": row["share_pct"], "confirmed_pct": row["opposite_share_pct"],
                                           "per_participant_not_confirmed_pct": row["per_participant"]}

    # Signal gaps: verified fingersticks under the threshold that never became a pair, and whether a wider window holds a reading.
    gaps = {"verified_fingersticks": int(n), "pairs": int(is_pair.sum()), "not_paired_no_reading_within_5_min": int((~is_pair).sum()),
            "not_paired_pct_of_fingersticks": float((~is_pair).mean() * 100.0)}
    for m_thr in (70, 54):
        m_low = ref < m_thr
        d = {"verified_fingerstick_lows": int(m_low.sum()), "pairs": int((m_low & is_pair).sum()), "not_paired": int((m_low & ~is_pair).sum())}
        d["not_paired_pct_of_lows"] = 100.0 * d["not_paired"] / d["verified_fingerstick_lows"]
        for rkey in ("within_15", "within_30"):
            d[f"not_paired_with_a_reading_{rkey}"] = int((m_low & ~is_pair & (count[rkey] > 0)).sum())
            d[f"not_paired_no_reading_{rkey}"] = int((m_low & ~is_pair & (count[rkey] == 0)).sum())
        gaps[f"meter_under_{m_thr}"] = d
    # Check on the pair rule: the same shares when those unpaired lows are added (every low with a reading in the window).
    added = {}
    for ckey, m_thr, s_thr in CASES:
        added[ckey] = {}
        for rkey in ("within_15", "within_30"):
            has = (ref < m_thr) & (count[rkey] > 0)
            row = share(bt, has & ~(lowest[rkey] < s_thr), has)
            added[ckey][rkey] = {"counted": row["counted"], "of_which_not_paired": int((has & ~is_pair).sum()), "not_shown": row["yes"],
                                 "not_shown_pct": row["share_pct"], "shown_pct": row["opposite_share_pct"]}
    gaps["with_unpaired_lows_added"] = added

    found = {"pairs": int(is_pair.sum()), "participants": n_people,
             "true_lows_meter_under_70": cases[CASES[0][0]]["rules"]["matched"]["counted"], "not_shown_at_70": cases[CASES[0][0]]["rules"]["matched"]["not_shown"],
             "sensor_lows_under_70": mirror["meter_70_or_above"]["counted"], "not_confirmed_at_70": mirror["meter_70_or_above"]["not_confirmed"],
             "true_lows_meter_under_54": cases[CASES[2][0]]["rules"]["matched"]["counted"], "not_shown_at_54": cases[CASES[2][0]]["rules"]["matched"]["not_shown"]}
    return {"label": label, "n_pairs": int(is_pair.sum()), "n_participants": n_people, "true_lows": cases, "sensor_lows": mirror, "signal_gaps": gaps}, found


# --------------------------------------------------------------------------
# The results table of the memo, built from the stats
# --------------------------------------------------------------------------
def ci(s):
    return f"{s['value']:.1f} ({s['ci_low']:.1f} to {s['ci_high']:.1f})"


def per_person(p):
    if not p["participants"]:
        return "n/a, 0"
    return f"{p['median_pct']:.1f} ({p['q1_pct']:.1f} to {p['q3_pct']:.1f}), {p['participants']}"


def table_markdown(stats):
    sets = [stats["sets"]["all_226"], stats["sets"]["arm_77"]]
    L = ["| Row | Events and rule | All 226: events counted (no reading in the window) | All 226: share, % (95 % CI) | All 226: per person, median (quartiles), people | "
         "Arm: events counted (no reading) | Arm: share, % (95 % CI) | Arm: per person, median (quartiles), people |",
         "|---|---|---|---|---|---|---|---|"]
    i = 0
    for ckey, m_thr, s_thr in CASES:
        for rkey, rlabel, _, _ in RULES:
            i += 1
            cells = []
            for s in sets:
                r = s["true_lows"][ckey]["rules"][rkey]
                cells += [f"{r['counted']:,} ({r['no_reading_in_window']:,})", ci(r["not_shown_pct"]), per_person(r["per_participant_not_shown_pct"])]
            L.append(f"| {i} | Meter under {m_thr}, sensor threshold {s_thr}: {rlabel} | " + " | ".join(cells) + " |")
    for cut in MIRROR_CUTS:
        i += 1
        cells = []
        for s in sets:
            r = s["sensor_lows"][f"meter_{cut}_or_above"]
            cells += [f"{r['counted']:,} (0)", ci(r["not_confirmed_pct"]), per_person(r["per_participant_not_confirmed_pct"])]
        L.append(f"| {i} | Sensor low (matched reading under 70): meter {cut} or above | " + " | ".join(cells) + " |")
    return "\n".join(L)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main(root, outdir, cache):
    ev, trace, info = load_events(root, cache)
    sets, found = {}, {}
    for skey, mask in (("all_226", np.ones(len(ev), bool)), ("arm_77", ev.in_arm.to_numpy(bool))):
        sets[skey], found[skey] = analyse(ev[mask].reset_index(drop=True), trace, SET_LABELS[skey])
        log(f"{skey}: {sets[skey]['n_pairs']:,} pairs from {sets[skey]['n_participants']} people")
    checks = {"matched_reading_vs_accuracy_v2": point_in_time_check(found), "pair_recount": info["pair_recount"],
              "window_logic": "passed: the matched reading lies inside the 15-minute window, the 15-minute window inside the 30-minute one, "
                              "and the before and after windows together equal the 15-minute window"}
    stats = {
        "generated": time.strftime("%Y-%m-%d %H:%M"), "seed": SEED, "n_boot": N_BOOT, "cache_version": pp.CACHE_VERSION,
        "definitions": {
            "pair": f"a verified fingerstick with the nearest sensor reading within {pp.METER_PAIR_TOL_S // 60} minutes (the matched reading); preprocess.verified_pairs()",
            "true_low": "a pair whose meter value is under the meter threshold (70 or 54 mg/dL)",
            "shown": "the sensor is under the sensor threshold under the rule in use; not shown = a true low that is not shown",
            "rules": {k: lab for k, lab, _, _ in RULES},
            "window": "seconds from the fingerstick time on the meter clock; both ends count; a reading at the exact fingerstick second is in the before and in the after window",
            "trace": "every sensor reading in the cache (5-minute steps), repeated time stamps dropped, all days",
            "no_reading_in_window": "true lows with no sensor reading in the window (signal gap); left out of 'counted', never counted as not shown",
            "sensor_low": "a pair whose matched sensor reading is under 70 mg/dL; not confirmed = the meter value is at or above the cut (70, or 80 as a softer check)",
            "ci": f"95 % CI = 2.5th to 97.5th percentile of {N_BOOT:,} bootstrap resamples of participants (seed {SEED})",
            "per_participant": f"median and quartiles of each person's own share, for people with at least {MIN_EVENTS} counted events",
            "signal_gaps": "verified fingersticks in the study window with no sensor reading within 5 minutes never became a pair; they are outside every row of the table",
            "with_unpaired_lows_added": "check: the 15- and 30-minute shares when every verified fingerstick low with a reading in the window is counted, paired or not",
        },
        "published_for_context": PUBLISHED,
        "sensor_readings_in_trace": info["sensor_readings_in_trace"],
        "checks": checks, "sets": sets,
    }
    stats = av2.clean(stats)
    stats["runtime_s"] = round(time.time() - T0, 1)
    path = os.path.join(outdir, "low_detection_window_stats.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=1)
    log("wrote", path)
    print("\n" + table_markdown(stats) + "\n")
    log("done in", stats["runtime_s"], "s")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit('usage: python analysis/low_detection_window.py "Uncommitted Data/Raw Data Dump" analysis [cache folder]')
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else pp.DEFAULT_CACHE)
