"""
Deep demographics check for BMEN 600 Group 24: does WHO the person is predict sensor error?

Extension of analysis/subgroups.py (first pass). Unit of analysis = the participant
(REPLACE-BG, 226 adults, Dexcom G4; verified fingerstick pairs). Shanghai (Abbott flash CGM,
in-patients) is the small comparator.

What it does, in order:
  1. Inventory of every participant-level variable in both cohorts (fill rate, counts, testable or not).
  2. A pre-registered test list, then the tests:
     a. univariate: every predictor x 7 outcomes (MARD, low-range MARD, bias, low-range bias,
        missed-low rate, false-low rate, within 20/20)
     b. interactions: pairwise regressions with an interaction term + simple 2x2 median tables
     c. study site: per-site table, ICC, permutation test, mixed model with a site random effect
     d. flexible models (random forest, gradient boosting, ridge) with repeated cross-validation:
        demographics only vs glucose pattern only vs both; grouped permutation importance
     e. mediation: demographic -> glucose pattern (CV, time below 70) -> MARD
     f. worst-quartile check: the 25 % of people with the worst MARD vs the rest
     g. Shanghai: same questions, same honest limits
     Benjamini-Hochberg over the whole pre-registered REPLACE-BG list (one family) and a second
     family for Shanghai.
  3. Figures 29-32 and demographics_deep_stats.json.

Run from the repo root (needs the preprocess cache and participant_metrics from subgroups.py;
about 2-3 minutes):
    python analysis/demographics_deep.py "Uncommitted Data/Raw Data Dump" analysis

Outputs (under the second argument, default analysis/):
    demographics_deep_stats.json
    figures/29_cohort_demographics.png
    figures/30_demographic_interactions.png
    figures/31_site_effects.png
    figures/32_demographics_vs_glucose_pattern.png
Markdown tables for the memo are printed to stdout.

Terms. MARD = mean absolute relative difference (average sensor error in % of the fingerstick).
Bias = mean signed error in % (negative = sensor reads low). Missed low = fingerstick below 70
but sensor 70 or more. False low = sensor below 70 but fingerstick 70 or more. CV = glucose
SD / mean (how much glucose swings). ICC = intraclass correlation (share of the spread that
sits between sites). BH = Benjamini-Hochberg false-discovery-rate correction.
"""
import json
import os
import re
import sys
import time
import warnings

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import RepeatedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preprocess as pp  # shared loaders + parquet cache (analysis/preprocess.py)

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
    print(__doc__.strip())
    sys.exit(0)

ROOT = sys.argv[1] if len(sys.argv) > 1 else pp.DEFAULT_ROOT
OUT = sys.argv[2] if len(sys.argv) > 2 else "analysis"
CACHE = sys.argv[3] if len(sys.argv) > 3 else pp.DEFAULT_CACHE
FIG = os.path.join(OUT, "figures")

SEED = 600                 # same seed as subgroups.py
N_BOOT = 2000              # bootstrap resamples for CIs
N_BOOT_MED = 1000          # bootstrap resamples for mediation
N_PERM = 2000              # permutations for the site ICC test
MIN_GROUP = 10             # fewer people than this in a group = "not testable"
MIN_LOW_PAIRS = 20         # pairs needed for a per-person low-range rate
MIN_SHANGHAI_PAIRS = 10
LOW_VARIANCE_SHARE = 0.90  # largest category above this share = "low variance" flag
CV_FOLDS, CV_REPEATS = 5, 10
PERM_REPEATS, PERM_SPLITS = 5, 25   # grouped permutation importance: 5 permutations on the first 25 splits (5 repeats x 5 folds)
ALPHA = 0.05

RNG = np.random.default_rng(SEED)
T0 = time.time()
STATS = {}
FAMILY = []                # every pre-registered REPLACE-BG p-value: (block, outcome, variable, label, p, dict to write p_bh into)
FAMILY_SH = []             # the same for Shanghai

OUTCOMES = [("mard", "MARD (%)"), ("low_mard", "Low-range MARD (%)"), ("bias_pct", "Bias (%)"), ("low_bias_pct", "Low-range bias (%)"),
            ("missed_low_rate", "Missed-low rate (%)"), ("false_low_rate", "False-low rate (%)"), ("pct_within_20_20", "Within 20/20 (%)")]
OUTCOME_LABEL = dict(OUTCOMES)


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


# --------------------------------------------------------------------------
# Chart styling (same palette as subgroups.py)
# --------------------------------------------------------------------------
C_BLUE, C_ORANGE, C_AQUA = "#2a78d6", "#eb6834", "#1baf7a"
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"], "font.size": 9,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titleweight": "semibold", "axes.titlesize": 10, "axes.titlelocation": "left",
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.axisbelow": True, "legend.frameon": False, "legend.fontsize": 9,
    "lines.linewidth": 1.5, "savefig.dpi": 150, "savefig.bbox": "tight",
})


def save(fig, name):
    path = os.path.join(FIG, name)
    fig.savefig(path)
    plt.close(fig)
    log("wrote", path)


# --------------------------------------------------------------------------
# Small statistics helpers (same definitions as subgroups.py)
# --------------------------------------------------------------------------
def q(x, p):
    return float(np.nanpercentile(np.asarray(x, float), p))


def describe(x):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) == 0:
        return {"n": 0, "median": None, "q1": None, "q3": None, "mean": None}
    return {"n": int(len(x)), "median": float(np.median(x)), "q1": q(x, 25), "q3": q(x, 75), "mean": float(x.mean())}


def boot_diff(ref, grp, stat=np.median):
    """Group minus reference (median by default) with a bootstrap 95 % CI."""
    a, b = np.asarray(ref, float), np.asarray(grp, float)
    ia = RNG.integers(0, len(a), (N_BOOT, len(a)))
    ib = RNG.integers(0, len(b), (N_BOOT, len(b)))
    d = stat(b[ib], axis=1) - stat(a[ia], axis=1)
    return float(stat(b) - stat(a)), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def spearman_ci(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    if len(x) < MIN_GROUP:
        return {"n": int(len(x)), "rho": None, "ci_low": None, "ci_high": None, "p": None}
    rho, p = stats.spearmanr(x, y)
    idx = RNG.integers(0, len(x), (N_BOOT, len(x)))
    rx = stats.rankdata(x[idx], axis=1)
    ry = stats.rankdata(y[idx], axis=1)
    rx = rx - rx.mean(axis=1, keepdims=True)
    ry = ry - ry.mean(axis=1, keepdims=True)
    r = (rx * ry).sum(axis=1) / np.sqrt((rx ** 2).sum(axis=1) * (ry ** 2).sum(axis=1))
    return {"n": int(len(x)), "rho": float(rho), "ci_low": float(np.nanpercentile(r, 2.5)),
            "ci_high": float(np.nanpercentile(r, 97.5)), "p": float(p)}


def detectable_diff(a, b):
    """Smallest difference in means detectable with 80 % power (2.8 x pooled SD x sqrt(1/n1 + 1/n2))."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    sd = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return float(2.8 * sd * np.sqrt(1 / len(a) + 1 / len(b)))


def bh(pvals):
    p = np.asarray(pvals, float)
    out = np.full(len(p), np.nan)
    ok = ~np.isnan(p)
    if ok.sum() > 0:
        out[ok] = multipletests(p[ok], method="fdr_bh")[1]
    return out


def register(block, outcome, variable, label, res, family=FAMILY):
    """Add one pre-registered p-value to the BH family. p_bh is written into `res` at the end."""
    p = res.get("p")
    family.append({"block": block, "outcome": outcome, "variable": variable, "label": label,
                   "p": float(p) if p is not None and not np.isnan(p) else np.nan, "ref": res})


def finish_family(family, name):
    """BH over the whole family, plus BH within each block and within (block, outcome). Returns a summary."""
    p = np.array([f["p"] for f in family], float)
    adj_all = bh(p)
    blocks = np.array([f["block"] for f in family])
    bo = np.array([f["block"] + "|" + str(f["outcome"]) for f in family])
    adj_block, adj_bo = np.full(len(p), np.nan), np.full(len(p), np.nan)
    for b in np.unique(blocks):
        m = blocks == b
        adj_block[m] = bh(p[m])
    for b in np.unique(bo):
        m = bo == b
        adj_bo[m] = bh(p[m])
    for f, a1, a2, a3 in zip(family, adj_all, adj_block, adj_bo):
        f["ref"]["p_bh"] = None if np.isnan(a1) else float(a1)
        f["ref"]["p_bh_block"] = None if np.isnan(a2) else float(a2)
        f["ref"]["p_bh_block_outcome"] = None if np.isnan(a3) else float(a3)
        f["ref"]["bh_significant"] = bool(not np.isnan(a1) and a1 < ALPHA)
    ok = ~np.isnan(p)
    passed = [{"block": f["block"], "outcome": f["outcome"], "variable": f["variable"], "label": f["label"], "p": f["p"], "p_bh": float(a)}
              for f, a in zip(family, adj_all) if not np.isnan(a) and a < ALPHA]
    passed_block = [{"block": f["block"], "outcome": f["outcome"], "variable": f["variable"], "label": f["label"], "p": f["p"], "p_bh_block": float(a)}
                    for f, a in zip(family, adj_block) if not np.isnan(a) and a < ALPHA]
    out = {"family": name, "n_tests": int(ok.sum()), "n_raw_p_below_0_05": int((p[ok] < ALPHA).sum()),
           "expected_by_chance_at_0_05": float(ok.sum() * ALPHA), "n_pass_bh_whole_list": len(passed),
           "n_pass_bh_within_block": len(passed_block), "smallest_p_bh": float(np.nanmin(adj_all)) if ok.any() else None,
           "passed_whole_list": passed, "passed_within_block": passed_block,
           "tests_per_block": {b: int((blocks == b)[ok].sum()) for b in np.unique(blocks)}}
    return out


def group_test(df, var, outcome, label, reference=None, order=None):
    """Compare a per-participant outcome between the groups of one variable (Mann-Whitney / Kruskal-Wallis),
    with each group contrasted to the reference as a difference in medians with a bootstrap CI."""
    d = df[[var, outcome]].dropna()
    if order is None:
        order = list(d[var].cat.categories) if isinstance(d[var].dtype, pd.CategoricalDtype) else sorted(d[var].unique())
    counts = d[var].value_counts()
    groups = [{"group": str(g), "n": int(counts.get(g, 0)), **{k: v for k, v in describe(d.loc[d[var] == g, outcome]).items() if k != "n"}}
              for g in order if counts.get(g, 0) > 0]
    keep = [g for g in order if counts.get(g, 0) >= MIN_GROUP]
    small = [{"group": str(g), "n": int(counts.get(g, 0))} for g in order if 0 < counts.get(g, 0) < MIN_GROUP]
    res = {"variable": var, "label": label, "outcome": outcome, "n": int(len(d)), "groups": groups, "excluded_small_groups": small,
           "testable": len(keep) >= 2, "test": None, "p": None, "reference": None, "contrasts": [], "max_abs_diff_median": None}
    if not res["testable"]:
        res["reason"] = f"fewer than 2 groups with at least {MIN_GROUP} people"
        return res
    ref = reference if reference in keep else keep[0]
    samples = [d.loc[d[var] == g, outcome].values for g in keep]
    if len(keep) == 2:
        res["test"] = "Mann-Whitney U"
        res["p"] = float(stats.mannwhitneyu(samples[0], samples[1], alternative="two-sided").pvalue)
    else:
        res["test"] = "Kruskal-Wallis"
        res["p"] = float(stats.kruskal(*samples).pvalue)
    res["reference"] = str(ref)
    a = d.loc[d[var] == ref, outcome].values
    for g in keep:
        if g == ref:
            continue
        b = d.loc[d[var] == g, outcome].values
        est, lo, hi = boot_diff(a, b)
        res["contrasts"].append({"group": str(g), "vs": str(ref), "n": int(len(b)), "n_ref": int(len(a)), "diff_median": est,
                                 "ci_low": lo, "ci_high": hi, "detectable_diff_means": detectable_diff(a, b)})
    res["max_abs_diff_median"] = float(max(abs(c["diff_median"]) for c in res["contrasts"]))
    return res


def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return None if np.isnan(o) else round(float(o), 4)
    if isinstance(o, (pd.Timestamp,)):
        return str(o)
    return o


def fmt_p(p):
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return "n.t."
    return "<0.001" if p < 0.001 else f"{p:.3f}" if p < 0.01 else f"{p:.2f}"


# --------------------------------------------------------------------------
# Data: participant metrics (from subgroups.py), extra outcomes, extra predictors
# --------------------------------------------------------------------------
def read_raw(name):
    return pd.read_csv(os.path.join(pp.rb_dir(ROOT), name), sep="|", low_memory=False)


def load_metrics():
    """Per-participant metrics computed by subgroups.py (parquet in the cache, else the CSV)."""
    p = os.path.join(CACHE, "participant_metrics.parquet")
    if os.path.isfile(p):
        return pd.read_parquet(p)
    c = os.path.join(OUT, "participant_metrics.csv")
    if not os.path.isfile(c):
        sys.exit("participant_metrics not found: run analysis/subgroups.py first")
    return pd.read_csv(c)


def extra_outcomes(pairs):
    """Per person, on verified fingerstick pairs: missed-low rate (meter < 70, CGM >= 70; share of meter-low pairs)
    and false-low rate (CGM < 70, meter >= 70; share of CGM-low pairs). NaN when fewer than MIN_LOW_PAIRS pairs."""
    v = pairs["verified"]
    ml = v[v.ref < 70].groupby("PtID").agg(n_meter_low=("cgm", "size"), missed_low_rate=("cgm", lambda c: float((c >= 70).mean() * 100)))
    fl = v[v.cgm < 70].groupby("PtID").agg(n_cgm_low=("ref", "size"), false_low_rate=("ref", lambda r: float((r >= 70).mean() * 100)))
    out = pd.concat([ml, fl], axis=1).reset_index()
    out.loc[out.n_meter_low.fillna(0) < MIN_LOW_PAIRS, "missed_low_rate"] = np.nan
    out.loc[out.n_cgm_low.fillna(0) < MIN_LOW_PAIRS, "false_low_rate"] = np.nan
    STATS["extra_outcomes"] = {"pooled_missed_low_pct": float((v[v.ref < 70].cgm >= 70).mean() * 100),
                               "pooled_false_low_pct": float((v[v.cgm < 70].ref >= 70).mean() * 100),
                               "people_with_missed_low_rate": int(out.missed_low_rate.notna().sum()),
                               "people_with_false_low_rate": int(out.false_low_rate.notna().sum())}
    return out


def extra_predictors():
    """Participant-level variables not in the cached participants table: hypoglycaemia-awareness questionnaire,
    hypoglycaemia-fear and diabetes-technology questionnaire scores at screening, medication counts and flags,
    extra medical-condition flags, insulin type."""
    hu = read_raw("HQuestHypoUnaware.txt").drop_duplicates("PtID").set_index("PtID")
    e = pd.DataFrame(index=hu.index)
    e["hypo_awareness"] = pd.Categorical(np.where(hu.LowBGSympCat.str.startswith("Always"), "Always", "Sometimes"), ["Always", "Sometimes"])
    e["lost_symptoms"] = pd.Categorical(hu.LowBGLostSymp.astype(str), ["No", "Yes"])
    e["mod_hypo_6mo"] = pd.Categorical(np.where(hu.ModHypoEpPast6Mon == "Never", "Never", "Any"), ["Never", "Any"])
    freq_map = {"Never": "0-3 times", "1 to 3 times": "0-3 times", "1 time/week": "1 per week", "2 to 3 times/week": "2-3 per week",
                "4 to 5 times/week": "4+ per week", "Almost daily": "4+ per week"}
    e["lows_with_symptoms_freq"] = pd.Categorical(hu.Bel70PastMonWSymp.map(freq_map), ["0-3 times", "1 per week", "2-3 per week", "4+ per week"])
    e["lows_with_symptoms_score"] = hu.Bel70PastMonWSymp.map({"Never": 0, "1 to 3 times": 1, "1 time/week": 2, "2 to 3 times/week": 3, "4 to 5 times/week": 4, "Almost daily": 5}).astype(float)
    e["lows_without_symptoms"] = pd.Categorical(np.where(hu.Bel70PastMonNoSymp == "Never", "Never", "Any"), ["Never", "Any"])
    e["symptom_threshold"] = pd.Categorical(hu.FeelSympLowBG.astype(str), ["60-69 mg/dL", "50-59 mg/dL"])
    e["symptom_extent"] = pd.Categorical(np.where(hu.ExtentSympLowBG == "Always", "Always", "Often or sometimes"), ["Always", "Often or sometimes"])
    # Hypoglycaemia fear survey at screening: 23 items, 0-4 each; 13 "worry" items, 10 behaviour items.
    hf = read_raw("HQuestHypoFear.txt")
    hf = hf[hf.Visit == "Screening Visit"].drop_duplicates("PtID").set_index("PtID")
    items = [c for c in hf.columns if c not in ("RecID", "SiteID", "Visit", "QuestNotDone")]
    vals = hf[items].apply(pd.to_numeric, errors="coerce")
    e["hypo_fear_total"] = vals.sum(axis=1, min_count=1)
    e["hypo_fear_worry"] = vals[[c for c in items if c.startswith("Worry")]].sum(axis=1, min_count=1)
    e["hypo_fear_behaviour"] = vals[[c for c in items if not c.startswith("Worry")]].sum(axis=1, min_count=1)
    # Diabetes technology questionnaire at screening: 30 "now" items, 1-5 each (total only; direction not interpreted).
    dt = read_raw("HQuestDiabTech.txt")
    dt = dt[dt.Visit == "Screening Visit"].drop_duplicates("PtID").set_index("PtID")
    now = [c for c in dt.columns if c.endswith("Now")]
    e["diabtech_total"] = dt[now].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=1)
    # Medications: count, statin, acetaminophen-containing (a known G4 interferent).
    md = read_raw("HMedication.txt")
    drug = md.DrugName.astype(str).str.lower()
    e["n_medications"] = md.groupby("PtID").size().reindex(e.index).fillna(0)
    e["statin"] = e.index.isin(md[drug.str.contains("statin|lipitor|crestor|zocor|pravachol|lescol|livalo|mevacor|vytorin", regex=True)].PtID)
    e["acetaminophen"] = e.index.isin(md[drug.str.contains("acetaminophen|tylenol|paracetamol|norco|vicodin|percocet|excedrin", regex=True)].PtID)
    # Medical conditions: extra flags beyond the six in the participants table.
    mc = read_raw("HMedicalCondition.txt").rename(columns={"PtId": "PtID"})
    low = mc.MedCond.astype(str).str.lower()
    for name, pat in [("comorb_neuropathy", "neuropathy"), ("comorb_gastroparesis", "gastroparesis"),
                      ("comorb_nephropathy", "nephropathy|albuminuria|kidney disease|renal"), ("comorb_anxiety", "anxiety"),
                      ("comorb_thyroid_any", "thyroid|hashimoto|graves"),
                      ("comorb_any_dm_complication", "retinopathy|neuropathy|nephropathy|albuminuria|gastroparesis")]:
        e[name] = e.index.isin(mc[low.str.contains(pat, regex=True)].PtID)
    # Insulin in the pump.
    ins = read_raw("HInsulin.txt")
    names = ins.groupby("PtID").InsName.apply(lambda s: set(s.dropna()))
    def ins_type(s):
        s = set(s) if isinstance(s, set) else set()
        if s == {"Novolog (Aspart)"}:
            return "Aspart (Novolog)"
        if s == {"Humalog (Lispro)"}:
            return "Lispro (Humalog)"
        return "Other or more than one"
    e["insulin_type"] = pd.Categorical(names.reindex(e.index).map(ins_type), ["Aspart (Novolog)", "Lispro (Humalog)", "Other or more than one"])
    e["n_injection_route_rows"] = int((ins.InsRoute == "Injection").sum())
    return e.reset_index()


def pump_family(s):
    if not isinstance(s, str) or s.strip() in ("", "None"):
        return np.nan
    fams = set()
    for tok in s.split(";"):
        t = tok.strip()
        if t == "multiple":
            fams.add("multiple")
        elif "Paradigm" in t or "MiniMed" in t:
            fams.add("Medtronic")
        elif "OmniPod" in t:
            fams.add("OmniPod")
        elif "Animas" in t or "Ping" in t:
            fams.add("Animas")
        elif "Tandem" in t:
            fams.add("Tandem")
        else:
            fams.add("Unknown code")
    if "multiple" in fams or len(fams) > 1:
        return "Multiple pumps"
    return fams.pop()


def add_covariates(ppl):
    """Grouped and 0/1 versions of every predictor (same cut points as subgroups.py where they exist)."""
    d = ppl.copy()
    d["sex"] = pd.Categorical(d.sex.astype(str), ["F", "M"])
    d["arm"] = pd.Categorical(d.arm.astype(str), ["CGM Only", "CGM+BGM"])
    d["male"] = (d.sex == "M").astype(int)
    d["arm_cgm_bgm"] = (d.arm == "CGM+BGM").astype(int)
    d["age_group"] = pd.cut(d.age, [0, 34, 50, 200], labels=["<35", "35-50", ">50"])
    d["bmi_group"] = pd.cut(d.bmi, [0, 25, 30, 100], right=False, labels=["<25", "25-30", "30+"])
    h = d.hba1c_screening
    d["hba1c_group"] = pd.Categorical(np.select([h < 7, h <= 8, h > 8], ["<7", "7-8", ">8"], default=""), ["<7", "7-8", ">8"])
    d["duration_group"] = pd.qcut(d.diabetes_duration_yrs.rank(method="first"), 3, labels=["shortest third", "middle third", "longest third"])
    d["hba1c_change"] = d.hba1c_week26 - d.hba1c_randomisation
    edu = d.education.astype(str)
    d["education_group"] = pd.Categorical(np.select(
        [edu.isin(["High school graduate/diploma/GED", "Some college but no degree", "Associate Degree"]), edu == "Bachelor's Degree",
         edu.isin(["Master's Degree", "Professional Degree", "Doctorate Degree"])], ["No bachelor's", "Bachelor's", "Graduate degree"], default=""),
        ["No bachelor's", "Bachelor's", "Graduate degree"])
    d["education_years"] = edu.map({"High school graduate/diploma/GED": 12, "Some college but no degree": 13, "Associate Degree": 14,
                                    "Bachelor's Degree": 16, "Master's Degree": 18, "Professional Degree": 19, "Doctorate Degree": 20})
    inc = d.income.astype(str)
    d["income_group"] = pd.Categorical(np.select(
        [inc.isin(["Less than $25,000", "$25,000 - $35,000", "$35,000 - less than $50,000"]),
         inc.isin(["$50,000 - less than $75,000", "$75,000 - less than $100,000"]), inc == "$100,000 - less than $200,000", inc == "$200,000 or more"],
        ["<$50k", "$50k-<$100k", "$100k-<$200k", "$200k+"], default=""), ["<$50k", "$50k-<$100k", "$100k-<$200k", "$200k+"])
    d["income_ordinal"] = d.income_group.cat.codes.replace(-1, np.nan).astype(float)
    d["income_answered"] = pd.Categorical(np.where(d.income_not_answered, "no", "yes"), ["no", "yes"])
    d["race_group"] = pd.Categorical(np.where(d.race.astype(str) == "White", "White", "Not White or unknown"), ["White", "Not White or unknown"])
    eth = d.ethnicity.astype(str)
    d["ethnicity_group"] = pd.Categorical(eth.where(eth != "Unknown/not reported", None), ["Not Hispanic or Latino", "Hispanic or Latino"])
    for c in ["insurance_private", "insurance_medicare", "insurance_medicaid", "insurance_other", "insurance_none",
              "comorb_hyperlipidemia", "comorb_hypertension", "comorb_hypothyroidism", "comorb_depression", "comorb_retinopathy", "comorb_obesity",
              "comorb_neuropathy", "comorb_gastroparesis", "comorb_nephropathy", "comorb_anxiety", "comorb_thyroid_any", "comorb_any_dm_complication",
              "statin", "acetaminophen", "other_glucose_lowering_med"]:
        d[c + "_yn"] = pd.Categorical(np.where(d[c].astype(bool), "yes", "no"), ["no", "yes"])
        d[c + "_01"] = d[c].astype(bool).astype(int)
    d["site_str"] = pd.Categorical(d.site.astype(str), [str(s) for s in sorted(d.site.unique())])
    d["cgm_use_status"] = pd.Categorical(d.cgm_use_status.astype(str), ["Never", "In past, but not current", "Current"])
    d["prior_cgm_current"] = (d.cgm_use_status == "Current").astype(int)
    dev = d.cgm_use_device.astype(str).where(d.cgm_use_device.notna(), None)
    d["cgm_use_device"] = pd.Categorical(dev, ["Dexcom", "Medtronic"])
    dur = d.cgm_use_duration.astype(str)
    d["cgm_use_years"] = pd.Categorical(np.select([dur.isin(["< 6 months", "6 months - < 1 year"]), dur.isin(["1 - < 2 years", "2 - < 5 years"]), dur == ">= 5 years"],
                                                  ["<1 year", "1-<5 years", "5+ years"], default=""), ["<1 year", "1-<5 years", "5+ years"])
    d["pump_family"] = pd.Categorical(d.pump_models.map(pump_family), ["Medtronic", "OmniPod", "Animas", "Tandem", "Unknown code", "Multiple pumps"])
    d["cgm_receiver"] = pd.Categorical(np.where(d.cgm_models.astype(str) == "G4Receiver", "G4 receiver only", "Also Share or G5 receiver"),
                                       ["G4 receiver only", "Also Share or G5 receiver"])
    d["status"] = pd.Categorical(d.status.astype(str), ["Completed", "Dropped"])
    d["severe_hypo_history"] = pd.Categorical(np.where(d.severe_hypo_most_recent.astype(str) == "Never", "never", "yes (>12 months ago)"), ["never", "yes (>12 months ago)"])
    d["dka_history"] = pd.Categorical(np.where(d.dka_most_recent.astype(str) == "Never", "never", "yes (ever)"), ["never", "yes (ever)"])
    d["initial_study_cgm"] = pd.Categorical(d.initial_study_cgm.astype(str), ["Blinded", "Standard"])
    d["impaired_awareness"] = (d.hypo_awareness == "Sometimes").astype(int)
    d["blinded_runin"] = (d.initial_study_cgm == "Blinded").astype(int)
    return d


# Predictor registry: (column, label, kind, family). kind = "cat" (group test) or "cont" (Spearman).
PREDICTORS = [
    ("sex", "Sex", "cat", "demographic"), ("age", "Age (years)", "cont", "demographic"), ("age_group", "Age group", "cat", "demographic"),
    ("race_group", "Race", "cat", "demographic"), ("ethnicity_group", "Ethnicity", "cat", "demographic"),
    ("education_group", "Education", "cat", "socio-economic"), ("education_years", "Education (years, coded)", "cont", "socio-economic"),
    ("income_group", "Income (answered only)", "cat", "socio-economic"), ("income_answered", "Answered the income question", "cat", "socio-economic"),
    ("insurance_private_yn", "Private insurance", "cat", "socio-economic"), ("insurance_medicare_yn", "Medicare", "cat", "socio-economic"),
    ("insurance_medicaid_yn", "Medicaid", "cat", "socio-economic"), ("insurance_other_yn", "Other insurance", "cat", "socio-economic"),
    ("insurance_none_yn", "No insurance", "cat", "socio-economic"),
    ("bmi", "BMI (kg/m2)", "cont", "body"), ("bmi_group", "BMI group", "cat", "body"), ("weight_kg", "Weight (kg)", "cont", "body"), ("height_cm", "Height (cm)", "cont", "body"),
    ("hba1c_screening", "HbA1c at screening (%)", "cont", "diabetes"), ("hba1c_group", "HbA1c group", "cat", "diabetes"),
    ("hba1c_change", "HbA1c change, randomisation to week 26 (%)", "cont", "diabetes"),
    ("diabetes_duration_yrs", "Diabetes duration (years)", "cont", "diabetes"), ("duration_group", "Diabetes duration tertile", "cat", "diabetes"),
    ("diagnosis_age", "Age at diagnosis (years)", "cont", "diabetes"), ("fingersticks_per_day", "Fingersticks per day at screening", "cont", "diabetes"),
    ("severe_hypo_history", "Severe hypoglycaemia history", "cat", "diabetes"), ("dka_history", "DKA history", "cat", "diabetes"),
    ("other_glucose_lowering_med_yn", "Non-insulin glucose-lowering drug", "cat", "diabetes"), ("insulin_type", "Insulin in the pump", "cat", "diabetes"),
    ("hypo_awareness", "Symptoms when glucose is low", "cat", "hypo awareness"), ("lost_symptoms", "Has lost some low-glucose symptoms", "cat", "hypo awareness"),
    ("mod_hypo_6mo", "Moderate hypo needing help, past 6 months", "cat", "hypo awareness"),
    ("lows_with_symptoms_freq", "Lows with symptoms, past month", "cat", "hypo awareness"), ("lows_with_symptoms_score", "Lows with symptoms, past month (0-5 score)", "cont", "hypo awareness"),
    ("lows_without_symptoms", "Lows without symptoms, past month", "cat", "hypo awareness"), ("symptom_threshold", "Glucose where symptoms start", "cat", "hypo awareness"),
    ("symptom_extent", "How often symptoms appear when low", "cat", "hypo awareness"),
    ("hypo_fear_total", "Hypoglycaemia fear score (23 items)", "cont", "psychosocial"), ("hypo_fear_worry", "Hypoglycaemia fear: worry items", "cont", "psychosocial"),
    ("hypo_fear_behaviour", "Hypoglycaemia fear: behaviour items", "cont", "psychosocial"), ("diabtech_total", "Diabetes technology questionnaire (30 items)", "cont", "psychosocial"),
    ("n_comorbidities", "Number of listed conditions", "cont", "health"), ("n_medications", "Number of listed medications", "cont", "health"),
    ("comorb_hyperlipidemia_yn", "Hyperlipidaemia", "cat", "health"), ("comorb_hypertension_yn", "Hypertension", "cat", "health"),
    ("comorb_hypothyroidism_yn", "Hypothyroidism", "cat", "health"), ("comorb_thyroid_any_yn", "Any thyroid condition", "cat", "health"),
    ("comorb_depression_yn", "Depression", "cat", "health"), ("comorb_anxiety_yn", "Anxiety", "cat", "health"),
    ("comorb_retinopathy_yn", "Retinopathy", "cat", "health"), ("comorb_neuropathy_yn", "Neuropathy", "cat", "health"),
    ("comorb_nephropathy_yn", "Kidney disease or albuminuria", "cat", "health"), ("comorb_gastroparesis_yn", "Gastroparesis", "cat", "health"),
    ("comorb_any_dm_complication_yn", "Any diabetes complication listed", "cat", "health"), ("comorb_obesity_yn", "Obesity listed as a condition", "cat", "health"),
    ("statin_yn", "Takes a statin", "cat", "health"), ("acetaminophen_yn", "Acetaminophen-containing drug listed", "cat", "health"),
    ("arm", "Study arm", "cat", "trial"), ("site_str", "Clinic site", "cat", "trial"), ("initial_study_cgm", "Run-in CGM type", "cat", "trial"),
    ("randomisation_day", "Run-in length (days to randomisation)", "cont", "trial"), ("status", "Completion status", "cat", "trial"),
    ("cgm_days_in_window", "Days of CGM data", "cont", "trial"),
    ("cgm_use_status", "Prior CGM use", "cat", "device"), ("cgm_use_device", "CGM brand (current users)", "cat", "device"),
    ("cgm_use_years", "Years of CGM use (current users)", "cat", "device"), ("pump_family", "Pump family", "cat", "device"),
    ("cgm_receiver", "CGM receiver model", "cat", "device"),
]
GLUCOSE_PATTERN = [("cv_pct", "Glucose CV (%)"), ("pct_below_70", "% time below 70 mg/dL"), ("mean_glucose", "Mean glucose (mg/dL)"),
                   ("pct_above_180", "% time above 180 mg/dL"), ("sd_glucose", "Glucose SD (mg/dL)"), ("pct_pairs_low", "% of own pairs below 70"),
                   ("pct_pairs_fast", "% of own pairs fast-changing"), ("pairs_per_day", "Fingerstick pairs per day")]


def inventory_rows(d, preds, min_group=MIN_GROUP):
    """One row per variable: fill rate, counts or quartiles, testable flag and low-variance flag."""
    rows = []
    for col, label, kind, fam in preds:
        s = d[col]
        n = len(s)
        fill = float(s.notna().mean() * 100)
        row = {"variable": col, "label": label, "kind": kind, "family": fam, "n": n, "fill_pct": fill, "n_missing": int(s.isna().sum())}
        if kind == "cat":
            vc = s.value_counts()
            vc = vc[vc > 0]
            row["levels"] = [{"level": str(k), "n": int(v), "pct_of_cohort": float(v / n * 100)} for k, v in vc.items()]
            big = float(vc.max() / vc.sum()) if vc.sum() else 1.0
            testable_levels = int((vc >= min_group).sum())
            row["largest_share_pct"] = big * 100
            row["testable"] = testable_levels >= 2
            row["low_variance"] = big >= LOW_VARIANCE_SHARE
            if not row["testable"]:
                row["why_not"] = f"only {testable_levels} level(s) with at least {min_group} people"
        else:
            x = pd.to_numeric(s, errors="coerce")
            row.update({"median": float(x.median()) if x.notna().any() else None, "q1": float(x.quantile(0.25)) if x.notna().any() else None,
                        "q3": float(x.quantile(0.75)) if x.notna().any() else None, "min": float(x.min()) if x.notna().any() else None,
                        "max": float(x.max()) if x.notna().any() else None, "n_distinct": int(x.nunique())})
            row["testable"] = bool(x.notna().sum() >= 2 * min_group and x.nunique() >= 5)
            row["low_variance"] = bool(x.nunique() < 5)
            if not row["testable"]:
                row["why_not"] = "fewer than 5 distinct values or too few people"
        rows.append(row)
    return rows


# --------------------------------------------------------------------------
# a. Univariate
# --------------------------------------------------------------------------
def univariate(d, preds, outcomes, block, family=FAMILY):
    """Every testable predictor x every outcome. Categorical: group_test. Continuous: Spearman."""
    out = {o: [] for o, _ in outcomes}
    inv = {r["variable"]: r for r in inventory_rows(d, preds)}
    for col, label, kind, fam in preds:
        for o, _ in outcomes:
            if kind == "cat":
                r = group_test(d, col, o, label)
                r["kind"] = "cat"
            else:
                r = {"variable": col, "label": label, "outcome": o, "kind": "cont", "test": "Spearman", **spearman_ci(d[col], d[o])}
                r["testable"] = r["p"] is not None and inv[col]["testable"]
                if not inv[col]["testable"]:
                    r["p"] = None
            r["family"] = fam
            r["low_variance"] = inv[col]["low_variance"]
            if r.get("testable"):
                register(block, o, col, label, r, family)
            out[o].append(r)
    return out


# --------------------------------------------------------------------------
# b. Interactions
# --------------------------------------------------------------------------
# main variables for the pairwise interaction grid: column, short label, continuous?, (low level name, high level name)
MAIN_VARS = {"age": ("Age", True, None), "male": ("Sex", False, ("female", "male")), "bmi": ("BMI", True, None),
             "hba1c_screening": ("HbA1c", True, None), "diabetes_duration_yrs": ("Duration", True, None),
             "arm_cgm_bgm": ("Arm", False, ("CGM-only", "CGM+BGM")), "prior_cgm_current": ("Prior CGM", False, ("not a current CGM user", "current CGM user")),
             "impaired_awareness": ("Hypo awareness", False, ("always has symptoms", "sometimes has symptoms"))}
INTERACTION_PAIRS = [("age", "male"), ("age", "bmi"), ("age", "hba1c_screening"), ("age", "diabetes_duration_yrs"), ("age", "arm_cgm_bgm"),
                     ("male", "bmi"), ("male", "hba1c_screening"), ("male", "diabetes_duration_yrs"), ("male", "arm_cgm_bgm"),
                     ("bmi", "hba1c_screening"), ("bmi", "diabetes_duration_yrs"), ("bmi", "arm_cgm_bgm"),
                     ("hba1c_screening", "diabetes_duration_yrs"), ("hba1c_screening", "arm_cgm_bgm"), ("diabetes_duration_yrs", "arm_cgm_bgm"),
                     ("prior_cgm_current", "arm_cgm_bgm"), ("impaired_awareness", "hba1c_screening"), ("impaired_awareness", "age")]


def split_labels(sub, v):
    """High/low split of one variable for the 2x2 table: median for continuous, the two levels for binary."""
    name, cont, levels = MAIN_VARS[v]
    if cont:
        med = float(sub[v].median())
        hi = sub[v] >= med
        return hi, f"{name} < {med:g}", f"{name} >= {med:g}"
    hi = sub[v] == 1
    return hi, levels[0], levels[1]


def interaction_test(d, a, b, outcome):
    """OLS outcome ~ a + b + a:b (continuous terms centred; HC3 errors); interaction p; a 2x2 table of medians
    (split at the median for continuous variables) with a bootstrap CI for the difference of differences."""
    sub = d[[a, b, outcome]].dropna().copy()
    hi_a, la0, la1 = split_labels(sub, a)
    hi_b, lb0, lb1 = split_labels(sub, b)
    fit_d = sub.copy()
    for v in (a, b):
        fit_d[v] = fit_d[v].astype(float)
        if MAIN_VARS[v][1]:
            fit_d[v] = fit_d[v] - fit_d[v].mean()
    fit = smf.ols(f"{outcome} ~ {a} * {b}", data=fit_d).fit(cov_type="HC3")
    term = f"{a}:{b}"
    ci = fit.conf_int()
    cells = {}
    arrs = {}
    for ia, (ma, la) in enumerate([(~hi_a, la0), (hi_a, la1)]):
        for ib, (mb, lb) in enumerate([(~hi_b, lb0), (hi_b, lb1)]):
            v = sub.loc[ma & mb, outcome].values
            arrs[(ia, ib)] = v
            cells[f"{ia}{ib}"] = {"a_level": la, "b_level": lb, "n": int(len(v)), "median": float(np.median(v)) if len(v) else None}
    # difference of differences: (high a, high b) - (high a, low b) minus (low a, high b) - (low a, low b)
    ok = all(len(v) >= MIN_GROUP for v in arrs.values())
    dod = None
    if ok:
        def stat(idx):
            m = {k: np.median(v[i], axis=-1) for (k, v), i in zip(arrs.items(), idx)}
            return (m[(1, 1)] - m[(1, 0)]) - (m[(0, 1)] - m[(0, 0)])
        est = float(stat([np.arange(len(v)) for v in arrs.values()]))
        boots = stat([RNG.integers(0, len(v), (N_BOOT, len(v))) for v in arrs.values()])
        dod = {"estimate": est, "ci_low": float(np.percentile(boots, 2.5)), "ci_high": float(np.percentile(boots, 97.5))}
    return {"a": a, "b": b, "a_label": MAIN_VARS[a][0], "b_label": MAIN_VARS[b][0], "outcome": outcome, "n": int(fit.nobs),
            "interaction_coef": float(fit.params[term]), "ci_low": float(ci.loc[term, 0]), "ci_high": float(ci.loc[term, 1]),
            "p": float(fit.pvalues[term]), "r2_with_interaction": float(fit.rsquared),
            "main_effects_p": {a: float(fit.pvalues[a]), b: float(fit.pvalues[b])},
            "table_2x2": cells, "difference_of_differences": dod, "testable": True,
            "note": "coef = change in the slope (or difference) of a per unit of b; 2x2 cells = median outcome; continuous variables split at their median"}


def site_arm_interaction(d, outcome, n_perm=1000):
    """outcome ~ site x arm. F-test of the site:arm block (full vs site + arm), plus a permutation p
    (arm labels shuffled within each site, so every site keeps its own arm counts). A robust-error Wald test
    is NOT used: several site-arm cells hold 1-3 people, which makes HC3 errors explode."""
    sub = d[["site_str", "arm_cgm_bgm", outcome]].dropna().copy()
    sub["site_str"] = sub.site_str.astype(str)
    y = sub[outcome].values.astype(float)
    S = pd.get_dummies(sub.site_str).values.astype(float)
    sites = sub.site_str.values
    arm0 = sub.arm_cgm_bgm.values.astype(float)

    def fstat(arm):
        Xr = np.c_[S, arm]
        Xf = np.c_[S, S * arm[:, None]]
        rr = y - Xr @ np.linalg.lstsq(Xr, y, rcond=None)[0]
        rf = y - Xf @ np.linalg.lstsq(Xf, y, rcond=None)[0]
        df1 = np.linalg.matrix_rank(Xf) - np.linalg.matrix_rank(Xr)
        df2 = len(y) - np.linalg.matrix_rank(Xf)
        if df1 <= 0 or df2 <= 0:
            return np.nan, df1, df2, (rr ** 2).sum(), (rf ** 2).sum()
        return float((((rr ** 2).sum() - (rf ** 2).sum()) / df1) / ((rf ** 2).sum() / df2)), int(df1), int(df2), (rr ** 2).sum(), (rf ** 2).sum()

    f_obs, df1, df2, rss_r, rss_f = fstat(arm0)
    p_f = float(1 - stats.f.cdf(f_obs, df1, df2)) if not np.isnan(f_obs) else np.nan
    perm = []
    for _ in range(n_perm):
        arm = arm0.copy()
        for s in np.unique(sites):
            ix = np.where(sites == s)[0]
            arm[ix] = arm0[ix][RNG.permutation(len(ix))]
        perm.append(fstat(arm)[0])
    perm = np.array(perm, float)
    p_perm = float(np.nanmean(perm >= f_obs)) if not np.isnan(f_obs) else np.nan
    per = sub.groupby(["site_str", "arm_cgm_bgm"])[outcome].agg(["size", "median"]).reset_index()
    tab = {}
    for s, g in per.groupby("site_str"):
        tab[s] = {("CGM+BGM" if int(r.arm_cgm_bgm) else "CGM-only"): {"n": int(r["size"]), "median": float(r["median"])} for _, r in g.iterrows()}
    return {"a": "site", "b": "arm", "a_label": "Site", "b_label": "Arm", "outcome": outcome, "n": int(len(y)), "F": f_obs, "df": [df1, df2],
            "p_f_test": p_f, "p": p_perm, "n_perm": n_perm, "n_interaction_terms": int(df1), "r2_gain_from_interaction": float((rss_r - rss_f) / ((y - y.mean()) ** 2).sum()),
            "test": "F-test of the site x arm block; p = permutation p (arm shuffled within site)", "per_site_per_arm_median": tab, "testable": True}


# --------------------------------------------------------------------------
# c. Site effects
# --------------------------------------------------------------------------
def icc1(y, g):
    """One-way random-effects ICC(1): share of the variance that sits between groups (0 = none, negative = less than chance)."""
    df = pd.DataFrame({"y": np.asarray(y, float), "g": np.asarray(g)}).dropna()
    grp = df.groupby("g").y
    k, N = grp.ngroups, len(df)
    if k < 2 or N <= k:
        return np.nan
    n_i = grp.size().values.astype(float)
    grand = df.y.mean()
    msb = (n_i * (grp.mean().values - grand) ** 2).sum() / (k - 1)
    msw = ((df.y - grp.transform("mean")) ** 2).sum() / (N - k)
    k0 = (N - (n_i ** 2).sum() / N) / (k - 1)
    return float((msb - msw) / (msb + (k0 - 1) * msw))


def site_analysis(d, outcome):
    """Per-site table, Kruskal-Wallis (sites with 10+), ICC with permutation p and bootstrap CI, mixed model ICC."""
    sub = d[["site", outcome]].dropna()
    y, g = sub[outcome].values, sub.site.values
    obs = icc1(y, g)
    perm = np.array([icc1(y, RNG.permutation(g)) for _ in range(N_PERM)])
    p_perm = float((perm >= obs).mean()) if not np.isnan(obs) else None
    boots = []
    for _ in range(N_BOOT // 2):
        idx = RNG.integers(0, len(y), len(y))
        boots.append(icc1(y[idx], g[idx]))
    boots = np.array(boots, float)
    res = {"outcome": outcome, "n": int(len(y)), "n_sites": int(sub.site.nunique()), "icc1": obs,
           "icc1_ci_low": float(np.nanpercentile(boots, 2.5)), "icc1_ci_high": float(np.nanpercentile(boots, 97.5)),
           "icc1_permutation_p": p_perm, "icc1_permutation_null_95th": float(np.nanpercentile(perm, 95))}
    try:
        mm = sm.MixedLM(sub[outcome].values, np.ones((len(sub), 1)), groups=sub.site.values).fit(reml=True)
        vs, ve = float(np.asarray(mm.cov_re)[0, 0]), float(mm.scale)
        res["mixed_model"] = {"site_variance": vs, "residual_variance": ve, "icc": vs / (vs + ve), "site_sd": float(np.sqrt(vs)), "residual_sd": float(np.sqrt(ve))}
    except Exception as e:
        res["mixed_model"] = {"error": str(e)}
    return res


def site_mixed_with_covariates(d):
    """MARD ~ six pre-specified terms + CV + % time below 70, random intercept per site. Does site variance survive?"""
    cols = ["mard", "age", "male", "bmi", "hba1c_screening", "diabetes_duration_yrs", "arm_cgm_bgm", "cv_pct", "pct_below_70", "site"]
    sub = d[cols].dropna()
    out = {}
    for name, terms in [("intercept_only", []), ("six_terms", ["age", "male", "bmi", "hba1c_screening", "diabetes_duration_yrs", "arm_cgm_bgm"]),
                        ("six_terms_plus_glucose_pattern", ["age", "male", "bmi", "hba1c_screening", "diabetes_duration_yrs", "arm_cgm_bgm", "cv_pct", "pct_below_70"])]:
        try:
            X = sm.add_constant(sub[terms].astype(float)) if terms else np.ones((len(sub), 1))
            mm = sm.MixedLM(sub.mard.values, X, groups=sub.site.values).fit(reml=True)
            vs, ve = float(np.asarray(mm.cov_re)[0, 0]), float(mm.scale)
            fixed = []
            if terms:
                ci = mm.conf_int()
                for t in terms:
                    fixed.append({"term": t, "coef": float(mm.params[t]), "ci_low": float(ci.loc[t, 0]), "ci_high": float(ci.loc[t, 1]), "p": float(mm.pvalues[t])})
            out[name] = {"n": int(len(sub)), "site_variance": vs, "residual_variance": ve, "icc": vs / (vs + ve), "fixed_effects": fixed}
        except Exception as e:
            out[name] = {"error": str(e)}
    return out


# --------------------------------------------------------------------------
# d. Flexible models
# --------------------------------------------------------------------------
def feature_frames(d):
    """Numeric feature tables. DEMO = every demographic / clinical / device / trial variable (one-hot for categories).
    GLUC = the three glucose-pattern variables named in the brief. Returns (X_demo, X_gluc, groups)."""
    X = pd.DataFrame(index=d.index)
    groups = {}
    def add(name, s):
        X[name] = pd.to_numeric(s, errors="coerce").astype(float)
        groups.setdefault(name, []).append(name)
    for c in ["age", "bmi", "weight_kg", "height_cm", "hba1c_screening", "hba1c_change", "diabetes_duration_yrs", "diagnosis_age", "fingersticks_per_day",
              "education_years", "income_ordinal", "n_comorbidities", "n_medications", "hypo_fear_total", "hypo_fear_worry", "hypo_fear_behaviour",
              "diabtech_total", "lows_with_symptoms_score", "randomisation_day", "cgm_days_in_window", "male", "arm_cgm_bgm", "prior_cgm_current",
              "impaired_awareness", "blinded_runin"]:
        add(c, d[c])
    for c in ["insurance_private", "insurance_medicare", "insurance_medicaid", "insurance_other", "insurance_none", "comorb_hyperlipidemia", "comorb_hypertension",
              "comorb_hypothyroidism", "comorb_depression", "comorb_retinopathy", "comorb_obesity", "comorb_neuropathy", "comorb_gastroparesis", "comorb_nephropathy",
              "comorb_anxiety", "comorb_thyroid_any", "comorb_any_dm_complication", "statin", "acetaminophen", "other_glucose_lowering_med"]:
        add(c, d[c + "_01"])
    add("income_not_answered", d.income_not_answered.astype(int))
    add("race_not_white", (d.race_group == "Not White or unknown").astype(int))
    add("hispanic", (d.ethnicity_group == "Hispanic or Latino").astype(int))
    add("dropped", (d.status == "Dropped").astype(int))
    add("severe_hypo_ever", (d.severe_hypo_history != "never").astype(int))
    add("dka_ever", (d.dka_history != "never").astype(int))
    add("lost_symptoms", (d.lost_symptoms == "Yes").astype(int))
    add("mod_hypo_6mo", (d.mod_hypo_6mo == "Any").astype(int))
    add("lows_without_symptoms", (d.lows_without_symptoms == "Any").astype(int))
    add("symptom_threshold_50s", (d.symptom_threshold == "50-59 mg/dL").astype(int))
    add("symptoms_not_always", (d.symptom_extent != "Always").astype(int))
    add("cgm_receiver_share_or_g5", (d.cgm_receiver != "G4 receiver only").astype(int))
    for col, gname in [("site_str", "site"), ("cgm_use_status", "prior_cgm_status"), ("cgm_use_device", "cgm_brand"), ("cgm_use_years", "cgm_years"),
                       ("pump_family", "pump_family"), ("insulin_type", "insulin_type"), ("education_group", "education_group")]:
        dummies = pd.get_dummies(d[col].astype(str), prefix=gname, dummy_na=False)
        for c in dummies.columns:
            if c.endswith("_nan") or c.endswith("_None"):
                continue
            X[c] = dummies[c].astype(float)
            groups.setdefault(gname, []).append(c)
    X_gluc = d[["cv_pct", "pct_below_70", "mean_glucose"]].astype(float)
    return X, X_gluc, groups


def model_factories():
    imp = lambda: SimpleImputer(strategy="median", add_indicator=True)
    return {
        "random_forest": lambda: make_pipeline(imp(), RandomForestRegressor(n_estimators=300, min_samples_leaf=5, max_features=0.33, random_state=SEED, n_jobs=-1)),
        "gradient_boosting": lambda: make_pipeline(imp(), HistGradientBoostingRegressor(max_depth=2, learning_rate=0.03, max_iter=300, min_samples_leaf=15,
                                                                                         l2_regularization=1.0, early_stopping=True, validation_fraction=0.2,
                                                                                         n_iter_no_change=15, random_state=SEED)),
        "ridge": lambda: make_pipeline(imp(), StandardScaler(), RidgeCV(alphas=np.logspace(-2, 4, 25))),
    }


def oof_r2(X, y, factory, splits):
    """Out-of-fold R squared per repeat (1 - SSE / SST over the held-out predictions of that repeat)."""
    X, y = np.asarray(X, float), np.asarray(y, float)
    per_repeat = []
    for rep in range(CV_REPEATS):
        pred = np.full(len(y), np.nan)
        for tr, te in splits[rep * CV_FOLDS:(rep + 1) * CV_FOLDS]:
            m = factory().fit(X[tr], y[tr])
            pred[te] = m.predict(X[te])
        per_repeat.append(1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum())
    per_repeat = np.array(per_repeat)
    return {"r2_mean": float(per_repeat.mean()), "r2_min": float(per_repeat.min()), "r2_max": float(per_repeat.max()), "r2_per_repeat": per_repeat.tolist(),
            "rmse": float(np.sqrt(((y - pred) ** 2).mean()))}


def grouped_permutation_importance(X, y, factory, splits, groups):
    """Held-out permutation importance by variable group: drop in out-of-fold R squared when the group's columns are
    shuffled together in the test folds (mean over PERM_REPEATS permutations and PERM_SPLITS splits)."""
    Xv, y = np.asarray(X, float), np.asarray(y, float)
    cols = list(X.columns)
    sst = ((y - y.mean()) ** 2).sum()
    gnames = [g for g in groups if any(c in cols for c in groups[g])]
    gidx = {g: [cols.index(c) for c in groups[g] if c in cols] for g in gnames}
    base_sse, perm_sse = 0.0, {g: 0.0 for g in gnames}
    for tr, te in splits[:PERM_SPLITS]:
        m = factory().fit(Xv[tr], y[tr])
        Xt, yt = Xv[te], y[te]
        base_sse += ((yt - m.predict(Xt)) ** 2).sum()
        perms = [RNG.permutation(len(te)) for _ in range(PERM_REPEATS)]
        stack = []
        for g in gnames:
            for pidx in perms:
                Xp = Xt.copy()
                Xp[:, gidx[g]] = Xt[pidx][:, gidx[g]]
                stack.append(Xp)
        pred = m.predict(np.vstack(stack)).reshape(len(gnames), PERM_REPEATS, len(te))   # one predict call per split
        sse = ((yt[None, None, :] - pred) ** 2).sum(axis=2).mean(axis=1)
        for g, v in zip(gnames, sse):
            perm_sse[g] += float(v)
    n_rep = PERM_SPLITS / CV_FOLDS
    base_r2 = 1 - base_sse / (sst * n_rep)
    out = {g: {"r2_drop": float((perm_sse[g] - base_sse) / (sst * n_rep)), "n_columns": len(gidx[g])} for g in gnames}
    return {"base_oof_r2": float(base_r2), "by_group": dict(sorted(out.items(), key=lambda kv: -kv[1]["r2_drop"]))}


def flexible_models(d, outcome):
    """Compare DEMO vs GLUC vs DEMO+GLUC feature sets with three model types, same folds."""
    X_demo, X_gluc, groups = feature_frames(d)
    ok = d[outcome].notna().values
    y = d.loc[ok, outcome].values
    sets = {"demographics_only": X_demo[ok], "glucose_pattern_only": X_gluc[ok], "demographics_plus_glucose_pattern": pd.concat([X_demo[ok], X_gluc[ok]], axis=1)}
    rkf = RepeatedKFold(n_splits=CV_FOLDS, n_repeats=CV_REPEATS, random_state=SEED)
    splits = list(rkf.split(y))
    res = {"outcome": outcome, "n": int(len(y)), "n_demographic_columns": int(X_demo.shape[1]), "n_glucose_columns": int(X_gluc.shape[1]),
           "cv": f"{CV_FOLDS}-fold, {CV_REPEATS} repeats, same folds for every model and feature set", "results": {}}
    for mname, fac in model_factories().items():
        res["results"][mname] = {}
        for sname, X in sets.items():
            res["results"][mname][sname] = oof_r2(X, y, fac, splits)
            log(f"  {outcome} {mname} {sname}: OOF R2 {res['results'][mname][sname]['r2_mean']:.3f}")
        a = np.array(res["results"][mname]["demographics_plus_glucose_pattern"]["r2_per_repeat"])
        b = np.array(res["results"][mname]["glucose_pattern_only"]["r2_per_repeat"])
        res["results"][mname]["added_r2_demographics_on_top_of_glucose"] = {"mean": float((a - b).mean()), "min": float((a - b).min()), "max": float((a - b).max())}
    if outcome == "mard":
        Xb = sets["demographics_plus_glucose_pattern"]
        g_all = {**{k: v for k, v in groups.items()}, "cv_pct": ["cv_pct"], "pct_below_70": ["pct_below_70"], "mean_glucose": ["mean_glucose"]}
        res["permutation_importance_random_forest"] = grouped_permutation_importance(Xb, y, model_factories()["random_forest"], splits, g_all)
        blocks = {"ALL demographics together": list(X_demo.columns), "ALL glucose pattern together": list(X_gluc.columns)}
        res["block_permutation_random_forest"] = grouped_permutation_importance(Xb, y, model_factories()["random_forest"], splits, blocks)
        res["block_permutation_gradient_boosting"] = grouped_permutation_importance(Xb, y, model_factories()["gradient_boosting"], splits, blocks)
    return res


# --------------------------------------------------------------------------
# e. Mediation
# --------------------------------------------------------------------------
def mediation(d, x, mediators=("cv_pct", "pct_below_70"), y="mard"):
    """Demographic x -> mediators (CV, % time below 70) -> y. All variables standardised (SD units).
    a_j = effect of x on mediator j; b_j = effect of mediator j on y holding x and the other mediator;
    indirect_j = a_j * b_j; direct = effect of x on y holding the mediators; total = effect of x on y alone.
    Bootstrap CIs (participants resampled)."""
    cols = [x] + list(mediators) + [y]
    sub = d[cols].dropna().astype(float)
    Z = ((sub - sub.mean()) / sub.std(ddof=1)).values
    n, k = Z.shape[0], len(mediators)
    def fit(Zb):
        one = np.ones((len(Zb), 1))
        Xx = np.c_[one, Zb[:, 0]]
        a = np.array([np.linalg.lstsq(Xx, Zb[:, 1 + j], rcond=None)[0][1] for j in range(k)])
        Xf = np.c_[one, Zb[:, :1 + k]]
        cf = np.linalg.lstsq(Xf, Zb[:, -1], rcond=None)[0]
        direct, b = cf[1], cf[2:]
        total = np.linalg.lstsq(Xx, Zb[:, -1], rcond=None)[0][1]
        ind = a * b
        return np.r_[a, b, ind, ind.sum(), direct, total]
    est = fit(Z)
    boots = np.array([fit(Z[RNG.integers(0, n, n)]) for _ in range(N_BOOT_MED)])
    lo, hi = np.percentile(boots, 2.5, axis=0), np.percentile(boots, 97.5, axis=0)
    names = [f"a_{m}" for m in mediators] + [f"b_{m}" for m in mediators] + [f"indirect_via_{m}" for m in mediators] + ["indirect_total", "direct", "total"]
    out = {"x": x, "y": y, "mediators": list(mediators), "n": int(n), "units": "SD of each variable",
           "paths": {nm: {"estimate": float(e), "ci_low": float(l), "ci_high": float(h)} for nm, e, l, h in zip(names, est, lo, hi)}}
    tot = est[-1]
    out["proportion_mediated"] = float(est[-3] / tot) if abs(tot) > 0.05 else None
    out["chain_present"] = bool(all(not (l <= 0 <= h) for l, h in [(lo[i], hi[i]) for i in range(2 * k, 3 * k)][:1]) or
                               all(not (l <= 0 <= h) for l, h in [(lo[i], hi[i]) for i in range(2 * k, 3 * k)][1:]))
    return out


# --------------------------------------------------------------------------
# f. Worst quartile
# --------------------------------------------------------------------------
def worst_quartile(d, outcome, preds, extra_cont, block, family=FAMILY):
    """The 25 % with the worst outcome vs the rest: medians or shares in each group, p-values, standardised difference."""
    thr = float(d[outcome].quantile(0.75))
    w = d[outcome] >= thr
    rows = []
    for col, label, kind, fam in preds + [(c, l, "cont", "glucose pattern") for c, l in extra_cont]:
        s = d[col]
        r = {"variable": col, "label": label, "kind": kind, "family": fam}
        if kind == "cont":
            a, b = pd.to_numeric(s[~w], errors="coerce").dropna(), pd.to_numeric(s[w], errors="coerce").dropna()
            r.update({"rest_median": float(a.median()), "worst_median": float(b.median()), "n_rest": int(len(a)), "n_worst": int(len(b))})
            if len(a) >= MIN_GROUP and len(b) >= MIN_GROUP and s.nunique() >= 5:
                r["p"] = float(stats.mannwhitneyu(a, b, alternative="two-sided").pvalue)
                sd = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
                r["standardised_diff"] = float((b.mean() - a.mean()) / sd) if sd > 0 else None
                r["testable"] = True
            else:
                r["testable"] = False
        else:
            levels = [l for l in (s.cat.categories if isinstance(s.dtype, pd.CategoricalDtype) else sorted(s.dropna().unique()))]
            tab = pd.crosstab(s, w).reindex(levels).fillna(0)
            r["levels"] = [{"level": str(l), "n_rest": int(tab.loc[l, False]) if False in tab.columns else 0, "n_worst": int(tab.loc[l, True]) if True in tab.columns else 0,
                            "pct_rest": float(tab.loc[l, False] / tab[False].sum() * 100) if False in tab.columns and tab[False].sum() else None,
                            "pct_worst": float(tab.loc[l, True] / tab[True].sum() * 100) if True in tab.columns and tab[True].sum() else None} for l in levels]
            tab2 = tab.loc[tab.sum(axis=1) >= MIN_GROUP]
            if tab2.shape[0] >= 2 and tab2.shape[1] == 2:
                if tab2.shape[0] == 2:
                    r["p"] = float(stats.fisher_exact(tab2.values)[1])
                    r["test"] = "Fisher exact"
                else:
                    r["p"] = float(stats.chi2_contingency(tab2.values)[1])
                    r["test"] = "chi-square"
                r["testable"] = True
            else:
                r["testable"] = False
        if r.get("testable"):
            register(block, outcome, col, label, r, family)
        rows.append(r)
    return {"outcome": outcome, "threshold": thr, "n_worst": int(w.sum()), "n_rest": int((~w).sum()), "rows": rows}


# --------------------------------------------------------------------------
# Ad hoc follow-up: sex and low-range bias (the one univariate result that passes BH)
# --------------------------------------------------------------------------
def fit_ols(df, outcome, terms):
    """OLS with HC3 errors; terms = list of (column, label). Returns n, R2 and per-term coef, CI, p."""
    cols = [c for c, _ in terms]
    sub = df[[outcome] + cols].dropna()
    fit = sm.OLS(sub[outcome].astype(float), sm.add_constant(sub[cols].astype(float))).fit(cov_type="HC3")
    ci = fit.conf_int()
    return {"outcome": outcome, "n": int(fit.nobs), "r2": float(fit.rsquared),
            "terms": [{"term": c, "label": l, "coef": float(fit.params[c]), "ci_low": float(ci.loc[c, 0]), "ci_high": float(ci.loc[c, 1]), "p": float(fit.pvalues[c])} for c, l in terms]}


def sex_followup(d, pairs):
    """Is the sex difference in low-range bias real, where does it live, and does anything explain it?
    Per-person bias by glucose range and in calibration pairs; adjusted models; a selection check (how low the
    fingersticks were); the same for the missed-low rate."""
    v = pairs["verified"]
    cal = pairs["calibration"]
    cal = cal[cal.in_study_window]

    def per_person(df, mask, name):
        g = df[mask].groupby("PtID").agg(n=("rel_err_pct", "size"), bias=("rel_err_pct", "mean"), err_mgdl=("err", "mean"), ref_mean=("ref", "mean"), cgm_mean=("cgm", "mean"))
        g.loc[g.n < MIN_LOW_PAIRS, ["bias", "err_mgdl"]] = np.nan
        return g.rename(columns=lambda c: f"{name}_{c}")

    blocks = [("lt54", "below 54 mg/dL", v, v.avg < 54), ("b54_69", "54-69 mg/dL", v, (v.avg >= 54) & (v.avg < 70)), ("low", "below 70 mg/dL", v, v.avg < 70),
              ("mid", "70-180 mg/dL", v, (v.avg >= 70) & (v.avg <= 180)), ("high", "above 180 mg/dL", v, v.avg > 180),
              ("cal_low", "calibration pairs below 70 mg/dL", cal, cal.avg < 70), ("cal_all", "calibration pairs, all", cal, cal.avg > 0),
              ("day1_low", "below 70 mg/dL, sensor day 1", v, (v.avg < 70) & (v.wear_day == 1)), ("day2plus_low", "below 70 mg/dL, sensor day 2+", v, (v.avg < 70) & (v.wear_day >= 2))]
    f = d[["PtID", "sex", "male", "age", "bmi", "weight_kg", "hba1c_screening", "diabetes_duration_yrs", "arm_cgm_bgm", "cv_pct", "pct_below_70", "pct_pairs_low",
           "low_bias_pct", "low_mard", "missed_low_rate", "false_low_rate", "fingersticks_per_day", "impaired_awareness"]].copy()
    f = f.merge(pd.concat([per_person(df, mask, name) for name, _, df, mask in blocks], axis=1).reset_index(), on="PtID", how="left")
    out = {"note": "ad hoc follow-up of a pre-registered result; not part of the BH family", "by_range": {}}
    for name, lab, _, _ in blocks:
        r = group_test(f, "sex", f"{name}_bias", f"Bias, {lab}")
        r["median_err_mgdl_by_sex"] = {s: describe(f.loc[f.sex == s, f"{name}_err_mgdl"]) for s in ["F", "M"]}
        out["by_range"][name] = r
    base = [("male", "Male vs female"), ("age", "Age (per year)"), ("bmi", "BMI (per kg/m2)"), ("hba1c_screening", "HbA1c (per 1 %)"),
            ("diabetes_duration_yrs", "Duration (per year)"), ("arm_cgm_bgm", "CGM+BGM vs CGM-only"), ("cv_pct", "CV (per 1 %)"), ("pct_below_70", "% time below 70 (per 1 %)")]
    out["adjusted_low_bias"] = fit_ols(f, "low_bias_pct", base)
    out["adjusted_low_bias_plus_weight"] = fit_ols(f, "low_bias_pct", base + [("weight_kg", "Weight (per kg)")])
    out["adjusted_low_bias_plus_lowpair_depth"] = fit_ols(f, "low_bias_pct", base + [("low_ref_mean", "Mean fingerstick of the person's low pairs (per mg/dL)")])
    out["adjusted_missed_low"] = fit_ols(f, "missed_low_rate", base)
    out["unadjusted_missed_low"] = fit_ols(f, "missed_low_rate", [("male", "Male vs female")])
    out["unadjusted_low_bias"] = fit_ols(f, "low_bias_pct", [("male", "Male vs female")])
    out["selection_check"] = {"mean_fingerstick_of_low_pairs_by_sex": {s: describe(f.loc[f.sex == s, "low_ref_mean"]) for s in ["F", "M"]},
                              "n_low_pairs_by_sex": {s: describe(f.loc[f.sex == s, "low_n"]) for s in ["F", "M"]},
                              "pct_time_below_70_by_sex": {s: describe(f.loc[f.sex == s, "pct_below_70"]) for s in ["F", "M"]},
                              "pct_pairs_low_by_sex": {s: describe(f.loc[f.sex == s, "pct_pairs_low"]) for s in ["F", "M"]},
                              "bmi_by_sex": {s: describe(f.loc[f.sex == s, "bmi"]) for s in ["F", "M"]},
                              "weight_by_sex": {s: describe(f.loc[f.sex == s, "weight_kg"]) for s in ["F", "M"]}}
    out["sex_x_arm_low_bias"] = {a: group_test(f[f.arm_cgm_bgm == k], "sex", "low_bias_pct", f"Sex, {a}") for a, k in [("CGM-only arm", 0), ("CGM+BGM arm", 1)]}
    out["within_sex_spearman_bias_vs_weight"] = {s: spearman_ci(f.loc[f.sex == s, "weight_kg"], f.loc[f.sex == s, "low_bias_pct"]) for s in ["F", "M"]}
    out["pooled_low_pairs"] = {}
    vm = v[v.avg < 70].merge(d[["PtID", "sex"]], on="PtID")
    for s in ["F", "M"]:
        g = vm[vm.sex == s]
        out["pooled_low_pairs"][s] = {"pairs": int(len(g)), "people": int(g.PtID.nunique()), "bias_pct": float(g.rel_err_pct.mean()), "median_err_mgdl": float(g.err.median()),
                                      "pct_cgm_reads_low_by_10_or_more": float((g.err <= -10).mean() * 100), "pct_cgm_reads_high_by_10_or_more": float((g.err >= 10).mean() * 100)}
    return out


def medications_followup(d):
    """Number of listed medications vs MARD (rho -0.24): tertile medians, links to age and glucose pattern, adjusted models."""
    f = d.copy()
    f["log_mard"] = np.log(f.mard)
    tert = pd.qcut(f.n_medications.rank(method="first"), 3, labels=["fewest third", "middle third", "most third"])
    f["med_tertile"] = tert
    cuts = [float(f.n_medications.quantile(1 / 3)), float(f.n_medications.quantile(2 / 3))]
    out = {"note": "ad hoc follow-up; not part of the BH family", "tertile_cut_points": cuts,
           "by_tertile": group_test(f, "med_tertile", "mard", "Medication count tertile"),
           "rho_with_age": spearman_ci(f.n_medications, f.age), "rho_with_cv": spearman_ci(f.n_medications, f.cv_pct),
           "rho_with_pct_below_70": spearman_ci(f.n_medications, f.pct_below_70), "rho_with_n_comorbidities": spearman_ci(f.n_medications, f.n_comorbidities),
           "rho_with_mard": spearman_ci(f.n_medications, f.mard), "rho_with_cal_mard": spearman_ci(f.n_medications, f.cal_mard),
           "rho_with_low_mard": spearman_ci(f.n_medications, f.low_mard), "rho_with_mid_mard": spearman_ci(f.n_medications, f.mid_mard)}
    base = [("n_medications", "Medications (per drug listed)")]
    adj = [("age", "Age (per year)"), ("cv_pct", "CV (per 1 %)"), ("pct_below_70", "% time below 70 (per 1 %)")]
    out["unadjusted"] = fit_ols(f, "mard", base)
    out["adjusted_age_cv_tbr"] = fit_ols(f, "mard", base + adj)
    out["adjusted_plus_conditions"] = fit_ols(f, "mard", base + adj + [("n_comorbidities", "Conditions (per condition listed)")])
    out["log_mard_adjusted"] = fit_ols(f, "log_mard", base + adj)
    out["cal_mard_adjusted"] = fit_ols(f, "cal_mard", base + adj)
    return out


# --------------------------------------------------------------------------
# g. Shanghai comparator
# --------------------------------------------------------------------------
SH_PREDICTORS = [
    ("type", "Diabetes type", "cat", "diabetes"), ("sex", "Sex", "cat", "demographic"), ("age", "Age (years)", "cont", "demographic"),
    ("age_group", "Age tertile", "cat", "demographic"), ("bmi", "BMI (kg/m2)", "cont", "body"), ("hba1c_pct", "HbA1c (%)", "cont", "diabetes"),
    ("hba1c_group", "HbA1c tertile", "cat", "diabetes"), ("duration_yrs", "Diabetes duration (years)", "cont", "diabetes"),
    ("smoker", "Smoking history (any pack-years)", "cat", "lifestyle"), ("drinker", "Alcohol drinker", "cat", "lifestyle"),
    ("macro_any", "Any macrovascular complication", "cat", "health"), ("micro_any", "Any microvascular complication", "cat", "health"),
    ("comorb_any", "Any listed comorbidity", "cat", "health"), ("hypo_recorded", "Hypoglycaemia recorded (yes/no column)", "cat", "diabetes"),
    ("on_insulin", "On insulin", "cat", "diabetes"), ("agent_class", "Glucose-lowering treatment", "cat", "diabetes"),
    ("egfr", "eGFR (kidney function)", "cont", "health"), ("fasting_cpeptide", "Fasting C-peptide (nmol/L)", "cont", "diabetes"),
    ("fpg", "Fasting plasma glucose (mg/dL)", "cont", "diabetes"), ("pack_years", "Smoking pack-years", "cont", "lifestyle"),
]
SH_OUTCOMES = [("mard", "MARD (%)"), ("bias_pct", "Bias (%)"), ("pct_within_20_20", "Within 20/20 (%)")]


def within_20_20(err, ref):
    err, ref = np.asarray(err, float), np.asarray(ref, float)
    return np.where(ref < 100, np.abs(err) <= 20, np.abs(err) / ref <= 0.20)


def shanghai_table(pairs):
    """One row per Shanghai patient (first summary row), with per-patient accuracy for those with 10+ pairs."""
    sh = pp.load_shanghai(ROOT, CACHE)
    pt = sh["patients"].copy()
    pt["group"] = pt.group.astype(str)
    pt["pid"] = pt.pid.astype(str)
    pt = pt.sort_values(["group", "pid", "visit"]).drop_duplicates(["group", "pid"]).reset_index(drop=True)
    s = pd.DataFrame({"group": pt.group, "pid": pt.pid})
    s["type"] = pd.Categorical(pt.group, ["T1DM", "T2DM"])
    s["sex"] = pd.Categorical(pt.sex.astype(str), ["F", "M"])
    s["age"] = pt["Age (years)"]
    s["bmi"] = pt["BMI (kg/m2)"]
    s["hba1c_pct"] = pt.hba1c_pct
    s["duration_yrs"] = pt["Duration of Diabetes (years)"]
    s["pack_years"] = pt["Smoking History (pack year)"]
    s["smoker"] = pd.Categorical(np.where(pt["Smoking History (pack year)"].fillna(0) > 0, "yes", "no"), ["no", "yes"])
    s["drinker"] = pd.Categorical(np.where(pt["Alcohol Drinking History (drinker/non-drinker)"].astype(str).str.strip() == "drinker", "yes", "no"), ["no", "yes"])
    def any_flag(col):
        v = pt[col].astype(str).str.strip().str.lower()
        return pd.Categorical(np.where(v.isin(["none", "nan", "", "/"]), "no", "yes"), ["no", "yes"])
    s["macro_any"] = any_flag("Diabetic Macrovascular Complications")
    s["micro_any"] = any_flag("Diabetic Microvascular Complications")
    s["comorb_any"] = any_flag("Comorbidities")
    s["acute_any"] = any_flag("Acute Diabetic Complications")
    s["hypo_recorded"] = pd.Categorical(pt["Hypoglycemia (yes/no)"].astype(str).str.strip().str.lower().map({"yes": "yes", "no": "no"}), ["no", "yes"])
    s["on_insulin"] = pd.Categorical(np.where(pt.on_insulin.astype(bool), "yes", "no"), ["no", "yes"])
    agents = pt["Hypoglycemic Agents"].astype(str).str.lower()
    oral = agents.str.contains("metformin|gliptin|glipt|acarbose|voglibose|glimepiride|gliclazide|glipizide|glibenclamide|repaglinide|nateglinide|pioglitazone|"
                               "flozin|glutide|exenatide|liraglutide|semaglutide|dulaglutide|tide$", regex=True)
    insulin = pt.on_insulin.astype(bool)
    s["agent_class"] = pd.Categorical(np.select([insulin & oral, insulin & ~oral, ~insulin & oral], ["insulin + oral/GLP-1", "insulin only", "oral/GLP-1 only"], default="none listed"),
                                      ["insulin only", "insulin + oral/GLP-1", "oral/GLP-1 only", "none listed"])
    s["egfr"] = pt["Estimated Glomerular Filtration Rate (ml/min/1.73m2)"]
    s["fasting_cpeptide"] = pt["Fasting C-peptide (nmol/L)"]
    s["fpg"] = pt["Fasting Plasma Glucose (mg/dl)"]
    a1, a2 = s.age.quantile([1 / 3, 2 / 3])
    s["age_group"] = pd.cut(s.age, [0, a1, a2, 200], labels=[f"<={a1:.0f}", f"{a1:.0f}-{a2:.0f}", f">{a2:.0f}"])
    h1, h2 = s.hba1c_pct.quantile([1 / 3, 2 / 3])
    s["hba1c_group"] = pd.cut(s.hba1c_pct, [0, h1, h2, 30], labels=[f"<={h1:.1f}", f"{h1:.1f}-{h2:.1f}", f">{h2:.1f}"])
    sp = pairs["shanghai"].copy()
    sp["group"] = sp.group.astype(str)
    sp["pid"] = sp.pid.astype(str)
    sp["w2020"] = within_20_20(sp.err, sp.ref)
    per = sp.groupby(["group", "pid"]).agg(n_pairs=("abs_rel_err_pct", "size"), mard=("abs_rel_err_pct", "mean"), bias_pct=("rel_err_pct", "mean"),
                                           pct_within_20_20=("w2020", lambda v: float(v.mean() * 100)),
                                           n_meter_low=("ref", lambda r: int((r < 70).sum()))).reset_index()
    s = s.merge(per, on=["group", "pid"], how="left")
    s["has_pairs"] = s.n_pairs.notna()
    for c in ["mard", "bias_pct", "pct_within_20_20"]:
        s.loc[s.n_pairs.fillna(0) < MIN_SHANGHAI_PAIRS, c] = np.nan
    pooled_low = sp[sp.ref < 70]
    STATS["shanghai_pooled_low"] = {"pairs_meter_below_70": int(len(pooled_low)), "patients_with_such_pairs": int(pooled_low.pid.nunique()),
                                    "missed_low_pct_pooled": float((pooled_low.cgm >= 70).mean() * 100) if len(pooled_low) else None,
                                    "by_type": {g: {"pairs": int(len(v)), "missed_low_pct": float((v.cgm >= 70).mean() * 100)} for g, v in pooled_low.groupby("group")},
                                    "note": "too few low fingersticks per patient for a per-patient missed-low rate; pooled only"}
    return s


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------
def hist_panel(ax, x, title, xlabel, color=C_BLUE, bins=20):
    x = np.asarray(pd.to_numeric(x, errors="coerce").dropna(), float)
    ax.hist(x, bins=bins, color=color, alpha=0.85, edgecolor=SURFACE, linewidth=0.5)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.text(0.98, 0.95, f"n = {len(x)}\nmedian {np.median(x):.1f}\nIQR {q(x, 25):.1f}-{q(x, 75):.1f}", transform=ax.transAxes, ha="right", va="top", fontsize=8, color=INK2)


def bar_panel(ax, items, title, color=C_BLUE):
    """Horizontal bars of cohort shares. items: list of (label, pct)."""
    labels = [i[0] for i in items][::-1]
    vals = [i[1] for i in items][::-1]
    ax.barh(range(len(vals)), vals, color=color, alpha=0.85, height=0.7)
    for i, v in enumerate(vals):
        ax.text(v + 1, i, f"{v:.0f} %", va="center", fontsize=7.5, color=INK2)
    ax.set_yticks(range(len(vals)))
    ax.set_yticklabels(labels, fontsize=7.5)
    ax.set_xlim(0, 115)
    ax.grid(False, axis="y")
    ax.grid(True, axis="x")
    ax.set_title(title)
    ax.set_xlabel("% of cohort")


def fig29(d, s):
    fig, axes = plt.subplots(2, 5, figsize=(14, 6.4), gridspec_kw={"width_ratios": [1, 1, 1, 1, 1.6]})
    r = axes[0]
    hist_panel(r[0], d.age, "REPLACE-BG: age", "years")
    hist_panel(r[1], d.bmi, "BMI", "kg/m2")
    hist_panel(r[2], d.hba1c_screening, "HbA1c at screening", "%")
    hist_panel(r[3], d.diabetes_duration_yrs, "Diabetes duration", "years")
    n = len(d)
    items = [("Female", (d.sex == "F").mean() * 100), ("White", (d.race_group == "White").mean() * 100), ("Hispanic or Latino", (d.ethnicity_group == "Hispanic or Latino").mean() * 100),
             ("Bachelor's or higher", d.education_group.isin(["Bachelor's", "Graduate degree"]).mean() * 100), ("Income $100k+ (of answered)", d.income_group.isin(["$100k-<$200k", "$200k+"]).sum() / d.income_group.notna().sum() * 100),
             ("Private insurance", d.insurance_private.mean() * 100), ("On an insulin pump", d.pump_user.mean() * 100), ("Current CGM user", (d.cgm_use_status == "Current").mean() * 100),
             ("Always feels lows", (d.hypo_awareness == "Always").mean() * 100), ("Severe hypo ever", (d.severe_hypo_history != "never").mean() * 100),
             ("CGM-only arm", (d.arm == "CGM Only").mean() * 100)]
    bar_panel(r[4], items, f"REPLACE-BG: who is in it (n = {n})")
    r = axes[1]
    hist_panel(r[0], s.age, "Shanghai: age", "years", color=C_ORANGE)
    hist_panel(r[1], s.bmi, "BMI", "kg/m2", color=C_ORANGE)
    hist_panel(r[2], s.hba1c_pct, "HbA1c", "%", color=C_ORANGE)
    hist_panel(r[3], s.duration_yrs, "Diabetes duration", "years", color=C_ORANGE)
    items = [("Type 2 diabetes", (s.type == "T2DM").mean() * 100), ("Female", (s.sex == "F").mean() * 100), ("On insulin", (s.on_insulin == "yes").mean() * 100),
             ("Any macrovascular complication", (s.macro_any == "yes").mean() * 100), ("Any microvascular complication", (s.micro_any == "yes").mean() * 100),
             ("Any other condition listed", (s.comorb_any == "yes").mean() * 100), ("Hypoglycaemia recorded", (s.hypo_recorded == "yes").mean() * 100),
             ("Smoking history", (s.smoker == "yes").mean() * 100), ("Alcohol drinker", (s.drinker == "yes").mean() * 100),
             (f"Has {MIN_SHANGHAI_PAIRS}+ fingerstick pairs", s.mard.notna().mean() * 100)]
    bar_panel(r[4], items, f"Shanghai: who is in it (n = {len(s)})", color=C_ORANGE)
    fig.suptitle("The two cohorts. REPLACE-BG: adults with type 1 diabetes on pumps, mostly White, well-educated, HbA1c near 7 %. Shanghai: older in-patients, mostly type 2.",
                 x=0.01, ha="left", fontsize=10, fontweight="semibold", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    save(fig, "29_cohort_demographics.png")


def fig30(inter_mard, choices):
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.6), gridspec_kw={"hspace": 0.5, "wspace": 0.5})
    vals = []
    for key in choices:
        for c in inter_mard[key]["table_2x2"].values():
            if c["median"] is not None:
                vals.append(c["median"])
    vmin, vmax = min(vals), max(vals)
    for ax, key in zip(axes.ravel(), choices):
        r = inter_mard[key]
        t = r["table_2x2"]
        grid = np.array([[t["00"]["median"], t["01"]["median"]], [t["10"]["median"], t["11"]["median"]]], float)
        im = ax.imshow(grid, cmap="Blues", vmin=vmin - 0.5, vmax=vmax + 0.5, aspect="auto")
        for i in range(2):
            for j in range(2):
                c = t[f"{i}{j}"]
                ax.text(j, i, f"{c['median']:.1f} %\nn = {c['n']}", ha="center", va="center", fontsize=9, color=INK if grid[i, j] < (vmin + vmax) / 2 + 0.6 else "white")
        ax.set_xticks([0, 1])
        ax.set_xticklabels([t["00"]["b_level"], t["01"]["b_level"]], fontsize=8)
        ax.set_yticks([0, 1])
        ax.set_yticklabels([t["00"]["a_level"], t["10"]["a_level"]], fontsize=8)
        ax.grid(False)
        dod = r["difference_of_differences"]
        dtxt = f"DoD {dod['estimate']:+.1f} (CI {dod['ci_low']:+.1f} to {dod['ci_high']:+.1f})" if dod else "DoD not estimable"
        ax.set_title(f"{r['a_label']} x {r['b_label']}: p {fmt_p(r['p'])}, BH p {fmt_p(r.get('p_bh'))}\n{dtxt}", fontsize=8.5)
        for sp in ax.spines.values():
            sp.set_visible(False)
    cb = fig.colorbar(im, ax=axes.ravel().tolist(), fraction=0.02, pad=0.02)
    cb.set_label("median per-person MARD (%)")
    n_pass = sum(1 for r in inter_mard.values() if r.get("bh_significant"))
    tail = "None passed the multiple-testing correction." if n_pass == 0 else f"{n_pass} passed the multiple-testing correction."
    fig.suptitle("Do two traits together predict error? Cell = median MARD of people in that combination. DoD = difference of differences\n"
                 f"(how much the effect of one trait changes with the other); 0 = no interaction. {tail}",
                 x=0.01, ha="left", fontsize=10, fontweight="semibold", color=INK)
    save(fig, "30_demographic_interactions.png")


def fig31(d, site_res, site_cv):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.4), gridspec_kw={"width_ratios": [1.5, 1]})
    per = d.groupby("site").agg(n=("mard", "size"), med=("mard", "median"), tbr=("pct_below_70", "median"), cv=("cv_pct", "median")).sort_values("med")
    order = list(per.index)
    for i, s in enumerate(order):
        v = d.loc[d.site == s, "mard"].values
        ax1.scatter(np.full(len(v), i) + RNG.uniform(-0.18, 0.18, len(v)), v, s=11, color=C_BLUE, alpha=0.5, edgecolor=SURFACE, linewidth=0.3)
        ax1.plot([i - 0.3, i + 0.3], [per.loc[s, "med"]] * 2, color=INK, lw=2)
    ax1.axhline(d.mard.median(), color=C_ORANGE, lw=1, ls="--")
    ax1.text(-0.45, d.mard.median() - 0.9, f"all sites: median {d.mard.median():.1f} %", ha="left", fontsize=8, color=C_ORANGE)
    ax1.set_xticks(range(len(order)))
    ax1.set_xticklabels([f"site {s}\nn={per.loc[s, 'n']}" for s in order], fontsize=7.5)
    ax1.set_ylabel("per-person MARD (%)")
    ax1.set_ylim(5, 25)
    r = site_res
    ax1.set_title(f"MARD by clinic site (sorted). Site medians span {per.med.min():.1f}-{per.med.max():.1f} %. ICC = {r['icc1']:.3f} "
                  f"(CI {r['icc1_ci_low']:.2f} to {r['icc1_ci_high']:.2f}), permutation p = {fmt_p(r['icc1_permutation_p'])}", fontsize=9)
    ax1.text(0.01, 0.97, "two people above 25 % are off the chart", transform=ax1.transAxes, fontsize=7.5, color=MUTED, va="top")
    ax2.scatter(per.tbr, per.med, s=per.n * 4, color=C_BLUE, alpha=0.7, edgecolor=SURFACE)
    for s, row in per.iterrows():
        ax2.annotate(str(s), (row.tbr, row.med), textcoords="offset points", xytext=(4, 3), fontsize=7.5, color=INK2)
    rho = stats.spearmanr(per.tbr, per.med)
    ax2.set_xlabel("site median % time below 70 mg/dL")
    ax2.set_ylabel("site median MARD (%)")
    ax2.set_title(f"Site MARD vs site time-low (Spearman rho {rho.statistic:+.2f}, p = {fmt_p(rho.pvalue)}); bubble = n", fontsize=9)
    fig.suptitle(f"Location: how much of the sensor-error spread sits between the 14 clinics? ICC for % time below 70: {site_cv['icc1']:.3f}.",
                 x=0.01, ha="left", fontsize=10, fontweight="semibold", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save(fig, "31_site_effects.png")


def fig32(path_rows, flex):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.8), gridspec_kw={"width_ratios": [1.25, 1]})
    n = len(path_rows)
    ys = np.arange(n)[::-1]
    for y, r in zip(ys, path_rows):
        for j, (key, col, mk) in enumerate([("cv", C_BLUE, "o"), ("tbr", C_ORANGE, "s"), ("mard", MUTED, "D")]):
            s = r[key]
            off = (1 - j) * 0.24
            ax1.plot([s["ci_low"], s["ci_high"]], [y + off, y + off], color=col, lw=1.3)
            ax1.plot(s["rho"], y + off, marker=mk, color=col, ms=5, markeredgecolor=SURFACE, markeredgewidth=0.5)
    ax1.axvline(0, color=AXIS, lw=1)
    ax1.set_yticks(ys)
    ax1.set_yticklabels([r["label"] for r in path_rows], fontsize=8)
    ax1.set_xlabel("Spearman rho with 95 % CI")
    ax1.grid(False, axis="y")
    ax1.grid(True, axis="x")
    for col, mk, lab in [(C_BLUE, "o", "with glucose CV"), (C_ORANGE, "s", "with % time below 70"), (MUTED, "D", "with MARD (the outcome)")]:
        ax1.plot([], [], marker=mk, color=col, ls="-", label=lab)
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=8)
    ax1.set_title("Which traits go with a swingy or often-low glucose pattern?", fontsize=9.5)
    sets = [("demographics_only", "Demographics\nonly"), ("glucose_pattern_only", "Glucose pattern\nonly (CV, time<70, mean)"), ("demographics_plus_glucose_pattern", "Both")]
    models = [("random_forest", "random forest", C_BLUE), ("gradient_boosting", "gradient boosting", C_ORANGE), ("ridge", "ridge (linear)", C_AQUA)]
    w = 0.26
    for j, (m, mlab, col) in enumerate(models):
        for i, (sname, slab) in enumerate(sets):
            r = flex["results"][m][sname]
            x = i + (j - 1) * w
            ax2.bar(x, r["r2_mean"], width=w, color=col, alpha=0.85, label=mlab if i == 0 else None)
            ax2.plot([x, x], [r["r2_min"], r["r2_max"]], color=INK, lw=1)
    ax2.axhline(0, color=AXIS, lw=1)
    ax2.set_xticks(range(len(sets)))
    ax2.set_xticklabels([s[1] for s in sets], fontsize=8)
    ax2.set_ylabel("out-of-fold R squared (share of MARD spread predicted)")
    ax2.legend(fontsize=8, loc="upper left")
    ax2.set_title(f"How well can we predict a person's MARD? ({CV_FOLDS}-fold CV x {CV_REPEATS} repeats; bar = mean, line = range)", fontsize=9.5)
    fig.suptitle("Demographics vs glucose pattern. Left: traits that predict the glucose pattern. Right: prediction of MARD from each set of variables.",
                 x=0.01, ha="left", fontsize=10, fontweight="semibold", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save(fig, "32_demographics_vs_glucose_pattern.png")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def preregistration(inv, inv_sh):
    testable = [r["label"] for r in inv if r["testable"]]
    not_testable = [f"{r['label']} ({r.get('why_not', '')})" for r in inv if not r["testable"]]
    return {
        "written_before_running": "yes: this dict is built from the registry and the inventory before any test runs",
        "unit": "participant (REPLACE-BG n = 226; Shanghai patients with 10+ pairs)",
        "outcomes": [{"column": o, "label": l} for o, l in OUTCOMES],
        "predictors_tested": testable, "predictors_described_only": not_testable,
        "blocks": {
            "a_univariate": "every testable predictor x every outcome; categorical: Mann-Whitney (2 groups) or Kruskal-Wallis (3+), groups under 10 people dropped; "
                            "continuous: Spearman rho with bootstrap CI",
            "b_interactions": f"{len(INTERACTION_PAIRS)} pairs x 7 outcomes: OLS outcome ~ a + b + a:b (HC3 errors), p of the a:b term; "
                              "plus site x arm (F-test of the site:arm block with a within-site permutation p); 2x2 median tables split at the median for continuous variables",
            "c_site": "per-site medians; Kruskal-Wallis over sites with 10+ people (in block a); ICC(1) with permutation p and bootstrap CI for MARD, "
                      "low-range MARD, missed-low rate, CV and % time below 70; mixed model with a site random intercept, with and without covariates",
            "d_flexible": f"random forest, gradient boosting and ridge; {CV_FOLDS}-fold CV x {CV_REPEATS} repeats; feature sets: demographics only, "
                          "glucose pattern only (CV, % time below 70, mean glucose), both; outcomes MARD, low-range MARD, missed-low rate; "
                          "grouped permutation importance on held-out folds (not in the BH family: no p-values)",
            "e_mediation": "x -> (CV, % time below 70) -> MARD, standardised, product of coefficients, bootstrap CIs; for age, sex, BMI, HbA1c, duration, arm, "
                           "prior CGM use, impaired awareness, hypo fear, fingersticks per day, number of conditions, education years (descriptive, not in the BH family)",
            "f_worst_quartile": "worst 25 % of MARD vs the rest: Mann-Whitney / Fisher / chi-square for every predictor and the glucose-pattern variables",
            "g_shanghai": f"univariate tests on {len(SH_PREDICTORS)} predictors x 3 outcomes (MARD, bias, within 20/20); own BH family; "
                          "no interactions or flexible models (n too small); no site variable exists in the Shanghai files",
        },
        "multiple_testing": "Benjamini-Hochberg over all p-values in blocks a, b, c (Kruskal-Wallis by site is in a) and f together: one family. "
                            "Shanghai is a second family. p_bh within each block is also stored (secondary).",
        "effect_size_rule": "a result that passes BH but moves the median by under 1 MARD point (or rho under 0.2) is 'statistically detectable, too small to matter'",
        "shanghai_predictors": [l for _, l, _, _ in SH_PREDICTORS],
    }


def main():
    pp.check_raw_data(ROOT)
    os.makedirs(FIG, exist_ok=True)
    STATS["run"] = {"seed": SEED, "n_boot": N_BOOT, "n_boot_mediation": N_BOOT_MED, "n_perm": N_PERM, "min_group": MIN_GROUP, "min_low_pairs": MIN_LOW_PAIRS,
                    "cv_folds": CV_FOLDS, "cv_repeats": CV_REPEATS, "cache_version": pp.CACHE_VERSION, "date": "2026-11-06"}
    ppl = pp.load_participants(ROOT, CACHE)
    pairs = pp.build_pairs(ROOT, CACHE)
    m = load_metrics()
    log(f"participants {len(ppl)}, metrics {len(m)} rows, verified pairs {len(pairs['verified']):,}")
    extra_o = extra_outcomes(pairs)
    extra_p = extra_predictors()
    d = add_covariates(ppl.merge(extra_p, on="PtID", how="left")).merge(m, on="PtID", how="left").merge(extra_o, on="PtID", how="left")
    STATS["outcome_summary"] = {o: describe(d[o]) for o, _ in OUTCOMES}
    STATS["outcome_correlations"] = {f"{a}_vs_{b}": spearman_ci(d[a], d[b]) for a, b in
                                     [("mard", "missed_low_rate"), ("mard", "false_low_rate"), ("low_mard", "missed_low_rate"), ("missed_low_rate", "false_low_rate"),
                                      ("mard", "pct_within_20_20"), ("bias_pct", "missed_low_rate"), ("low_bias_pct", "missed_low_rate")]}

    # 1. Inventory
    s = shanghai_table(pairs)
    inv = inventory_rows(d, PREDICTORS)
    inv_sh = inventory_rows(s[s.mard.notna()], SH_PREDICTORS)
    inv_sh_all = inventory_rows(s, SH_PREDICTORS)
    STATS["inventory"] = {"replace_bg": inv, "shanghai_with_pairs": inv_sh, "shanghai_all": inv_sh_all,
                          "replace_bg_no_variance": ["pump vs injections: all 226 on a pump (3 injection rows in HInsulin, all pump users too)",
                                                     "severe hypoglycaemia in the past 12 months: 0 of 226 (an exclusion criterion)",
                                                     "DKA in the past 12 months: 2 of 226", "CGM model: all Dexcom G4 (23 also had a Share receiver, 1 a G5)"],
                          "shanghai_missing": ["no hospital or site column in the Shanghai files", "no race, education, income or insurance", "no run-in or arm"]}
    STATS["preregistration"] = preregistration(inv, inv_sh)
    log("inventory done")

    # 2a. Univariate
    STATS["univariate"] = univariate(d, PREDICTORS, OUTCOMES, "a_univariate")
    log("univariate done")

    # 2b. Interactions
    inter = {o: {} for o, _ in OUTCOMES}
    for o, _ in OUTCOMES:
        for a, b in INTERACTION_PAIRS:
            r = interaction_test(d, a, b, o)
            inter[o][f"{a}|{b}"] = r
            register("b_interactions", o, f"{a}:{b}", f"{MAIN_VARS[a][0]} x {MAIN_VARS[b][0]}", r)
        r = site_arm_interaction(d, o)
        inter[o]["site|arm"] = r
        register("b_interactions", o, "site:arm", "Site x Arm", r)
    STATS["interactions"] = inter
    log("interactions done")

    # 2c. Site
    site = {o: site_analysis(d, o) for o in ["mard", "low_mard", "missed_low_rate", "false_low_rate", "bias_pct", "cv_pct", "pct_below_70", "mean_glucose"]}
    per_site = d.groupby("site").agg(n=("mard", "size"), mard_median=("mard", "median"), mard_q1=("mard", lambda v: v.quantile(0.25)), mard_q3=("mard", lambda v: v.quantile(0.75)),
                                     low_mard_median=("low_mard", "median"), missed_low_median=("missed_low_rate", "median"), cv_median=("cv_pct", "median"),
                                     tbr_median=("pct_below_70", "median"), age_median=("age", "median"), hba1c_median=("hba1c_screening", "median"),
                                     pct_cgm_bgm=("arm_cgm_bgm", lambda v: v.mean() * 100), pct_female=("male", lambda v: (1 - v.mean()) * 100)).reset_index()
    STATS["site"] = {"per_site": per_site.to_dict(orient="records"), "icc": site, "mixed_models_mard": site_mixed_with_covariates(d),
                     "site_vs_glucose_pattern": {"rho_site_median_mard_vs_site_median_tbr": spearman_ci(per_site.tbr_median, per_site.mard_median),
                                                 "rho_site_median_mard_vs_site_median_cv": spearman_ci(per_site.cv_median, per_site.mard_median)}}
    log("site done")

    # 2d. Flexible models (log MARD added because two people above 30 % dominate the raw-MARD variance)
    d["log_mard"] = np.log(d.mard)
    STATS["flexible_models"] = {o: flexible_models(d, o) for o in ["mard", "log_mard", "low_mard", "missed_low_rate"]}
    log("flexible models done")

    # Follow-up on the one univariate result expected to pass BH (sex and low-range bias): labelled ad hoc.
    STATS["followup_sex_low_bias"] = sex_followup(d, pairs)
    log("sex follow-up done")

    # 2e. Mediation
    med_x = [("age", "Age"), ("male", "Male"), ("bmi", "BMI"), ("hba1c_screening", "HbA1c"), ("diabetes_duration_yrs", "Diabetes duration"), ("arm_cgm_bgm", "CGM+BGM arm"),
             ("prior_cgm_current", "Current CGM user"), ("impaired_awareness", "Impaired hypo awareness"), ("hypo_fear_total", "Hypo fear score"),
             ("fingersticks_per_day", "Fingersticks per day"), ("n_comorbidities", "Number of conditions"), ("education_years", "Education years"),
             ("lows_with_symptoms_score", "Self-reported lows per month"), ("hypo_fear_behaviour", "Hypo fear: behaviour")]
    STATS["mediation"] = {x: {"label": lab, **mediation(d, x)} for x, lab in med_x}
    STATS["mediation_low_mard"] = {x: {"label": lab, **mediation(d, x, y="low_mard")} for x, lab in med_x[:8]}
    path_rows = [{"variable": x, "label": lab, "cv": spearman_ci(d[x], d.cv_pct), "tbr": spearman_ci(d[x], d.pct_below_70), "mard": spearman_ci(d[x], d.mard)} for x, lab in med_x]
    STATS["demographics_vs_glucose_pattern"] = path_rows
    log("mediation done")

    # 2f. Worst quartile
    STATS["worst_quartile"] = {o: worst_quartile(d, o, PREDICTORS, GLUCOSE_PATTERN, "f_worst_quartile") for o in ["mard", "missed_low_rate"]}
    log("worst quartile done")

    # 2g. Shanghai
    sh_tests = univariate(s, SH_PREDICTORS, SH_OUTCOMES, "g_shanghai", family=FAMILY_SH)
    STATS["shanghai"] = {"patients_total": int(len(s)), "patients_with_pairs": int(s.has_pairs.sum()), "patients_with_min_pairs": int(s.mard.notna().sum()),
                         "min_pairs": MIN_SHANGHAI_PAIRS, "outcome_summary": {o: describe(s[o]) for o, _ in SH_OUTCOMES},
                         "by_type": {t: {o: describe(s.loc[s.type == t, o]) for o, _ in SH_OUTCOMES} for t in ["T1DM", "T2DM"]},
                         "univariate": sh_tests, "site": "no hospital or site column exists in the Shanghai files; location cannot be tested",
                         "not_done": "interactions and flexible models: n = 76 is too small (a 2x2 split leaves cells under 20)"}
    log("shanghai done")

    # Ad hoc follow-up of the second-smallest univariate p (number of medications vs MARD): does it survive adjustment?
    STATS["followup_n_medications"] = medications_followup(d)

    # BH over the families
    STATS["bh_summary"] = {"replace_bg": finish_family(FAMILY, "REPLACE-BG pre-registered list"), "shanghai": finish_family(FAMILY_SH, "Shanghai list")}
    log("BH done:", STATS["bh_summary"]["replace_bg"]["n_tests"], "tests;", STATS["bh_summary"]["replace_bg"]["n_pass_bh_whole_list"], "pass")

    # Figures
    fig29(d, s)
    fig30(inter["mard"], ["age|male", "bmi|hba1c_screening", "age|hba1c_screening", "male|hba1c_screening", "age|diabetes_duration_yrs", "prior_cgm_current|arm_cgm_bgm"])
    fig31(d, site["mard"], site["pct_below_70"])
    fig32(path_rows, STATS["flexible_models"]["mard"])

    STATS["run"]["runtime_s"] = round(time.time() - T0, 1)
    with open(os.path.join(OUT, "demographics_deep_stats.json"), "w", encoding="utf-8") as f:
        json.dump(clean(STATS), f, indent=1)
    log("wrote", os.path.join(OUT, "demographics_deep_stats.json"))
    print_tables(d, s)


# --------------------------------------------------------------------------
# Markdown tables for the memo
# --------------------------------------------------------------------------
def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def f1(v, nd=1, sign=False):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "-"
    return f"{v:+.{nd}f}" if sign else f"{v:.{nd}f}"


def print_tables(d, s):
    print("\n\n######## INVENTORY REPLACE-BG")
    rows = []
    for r in STATS["inventory"]["replace_bg"]:
        if r["kind"] == "cat":
            desc = "; ".join(f"{l['level']} {l['n']}" for l in r["levels"])
        else:
            desc = f"median {f1(r['median'])} (IQR {f1(r['q1'])}-{f1(r['q3'])}), range {f1(r['min'])}-{f1(r['max'])}"
        flag = ("testable" if r["testable"] else "NOT testable: " + r.get("why_not", "")) + ("; low variance" if r["low_variance"] else "")
        rows.append([r["label"], r["family"], f"{r['fill_pct']:.0f} %", desc, flag])
    print(md_table(["Variable", "Group", "Filled", "Values (n)", "Status"], rows))
    print("\n######## INVENTORY SHANGHAI (patients with 10+ pairs)")
    rows = []
    for r in STATS["inventory"]["shanghai_with_pairs"]:
        desc = "; ".join(f"{l['level']} {l['n']}" for l in r["levels"]) if r["kind"] == "cat" else f"median {f1(r['median'])} (IQR {f1(r['q1'])}-{f1(r['q3'])}), range {f1(r['min'])}-{f1(r['max'])}"
        flag = ("testable" if r["testable"] else "NOT testable: " + r.get("why_not", "")) + ("; low variance" if r["low_variance"] else "")
        rows.append([r["label"], f"{r['fill_pct']:.0f} %", desc, flag])
    print(md_table(["Variable", "Filled", "Values (n)", "Status"], rows))
    print("\n######## OUTCOMES")
    print(md_table(["Outcome", "n", "Median", "IQR"], [[l, v["n"], f1(v["median"]), f"{f1(v['q1'])} to {f1(v['q3'])}"] for (o, l), v in zip(OUTCOMES, STATS["outcome_summary"].values())]))
    print(json.dumps(clean(STATS["extra_outcomes"])), json.dumps(clean(STATS["outcome_correlations"])))
    print("\n######## BH SUMMARY")
    print(json.dumps(clean(STATS["bh_summary"]), indent=1))
    print("\n######## UNIVARIATE MATRIX (cell: effect; raw p; BH p over the whole list). cat effect = largest |difference in medians| vs reference; cont effect = rho")
    rows = []
    for i, (col, label, kind, fam) in enumerate(PREDICTORS):
        cells = []
        for o, _ in OUTCOMES:
            r = STATS["univariate"][o][i]
            if not r.get("testable"):
                cells.append("n.t.")
            elif kind == "cat":
                cells.append(f"{f1(r['max_abs_diff_median'])}; {fmt_p(r['p'])}; {fmt_p(r.get('p_bh'))}")
            else:
                cells.append(f"{f1(r['rho'], 2, True)}; {fmt_p(r['p'])}; {fmt_p(r.get('p_bh'))}")
        rows.append([label] + cells)
    print(md_table(["Predictor"] + [l for _, l in OUTCOMES], rows))
    print("\n######## UNIVARIATE DETAIL for MARD and low MARD and missed-low (groups: median, n)")
    for o in ["mard", "low_mard", "missed_low_rate", "bias_pct", "low_bias_pct", "false_low_rate", "pct_within_20_20"]:
        print(f"\n--- {o}")
        for r in STATS["univariate"][o]:
            if r["kind"] == "cat":
                gs = "; ".join(f"{g['group']} {f1(g['median'])} (n {g['n']})" for g in r["groups"] if g["median"] is not None)
                cs = "; ".join(f"{c['group']} vs {c['vs']}: {f1(c['diff_median'], 1, True)} (CI {f1(c['ci_low'], 1, True)} to {f1(c['ci_high'], 1, True)}; detectable {f1(c['detectable_diff_means'])})" for c in r["contrasts"])
                print(f"{r['label']} | {gs} | {cs} | p {fmt_p(r['p'])} | BH {fmt_p(r.get('p_bh'))} | {'testable' if r['testable'] else 'n.t. ' + str(r.get('excluded_small_groups'))}")
            else:
                print(f"{r['label']} | rho {f1(r['rho'], 2, True)} (CI {f1(r['ci_low'], 2, True)} to {f1(r['ci_high'], 2, True)}) n {r['n']} | p {fmt_p(r['p'])} | BH {fmt_p(r.get('p_bh'))}")
    print("\n######## INTERACTIONS")
    for o, _ in OUTCOMES:
        print(f"\n--- {o}")
        for k, r in STATS["interactions"][o].items():
            if k == "site|arm":
                print(f"Site x Arm | F {f1(r['F'], 2)} df {r['df']} | F-test p {fmt_p(r['p_f_test'])} | permutation p {fmt_p(r['p'])} | BH {fmt_p(r.get('p_bh'))} | R2 gain {f1(r['r2_gain_from_interaction'], 3)}")
                continue
            t = r["table_2x2"]
            dod = r["difference_of_differences"]
            cells = " / ".join(f"{t[k2]['a_level']} & {t[k2]['b_level']}: {f1(t[k2]['median'])} (n {t[k2]['n']})" for k2 in ["00", "01", "10", "11"])
            print(f"{r['a_label']} x {r['b_label']} | coef {f1(r['interaction_coef'], 3, True)} | p {fmt_p(r['p'])} | BH {fmt_p(r.get('p_bh'))} | "
                  f"DoD {f1(dod['estimate'], 1, True) if dod else '-'} (CI {f1(dod['ci_low'], 1, True) if dod else '-'} to {f1(dod['ci_high'], 1, True) if dod else '-'}) | {cells}")
    print("\n######## SITE")
    print(md_table(["Site", "n", "MARD median (IQR)", "Low MARD", "Missed-low", "CV", "% time <70", "Age", "HbA1c", "% CGM+BGM", "% female"],
                   [[r["site"], r["n"], f"{f1(r['mard_median'])} ({f1(r['mard_q1'])}-{f1(r['mard_q3'])})", f1(r["low_mard_median"]), f1(r["missed_low_median"]), f1(r["cv_median"]),
                     f1(r["tbr_median"]), f1(r["age_median"], 0), f1(r["hba1c_median"]), f1(r["pct_cgm_bgm"], 0), f1(r["pct_female"], 0)] for r in STATS["site"]["per_site"]]))
    for o, r in STATS["site"]["icc"].items():
        mm = r.get("mixed_model", {})
        print(f"ICC {o}: {f1(r['icc1'], 3)} (CI {f1(r['icc1_ci_low'], 3)} to {f1(r['icc1_ci_high'], 3)}), perm p {fmt_p(r['icc1_permutation_p'])}, null 95th {f1(r['icc1_permutation_null_95th'], 3)}; "
              f"mixed-model ICC {f1(mm.get('icc'), 3)} site SD {f1(mm.get('site_sd'), 2)} resid SD {f1(mm.get('residual_sd'), 2)}")
    print(json.dumps(clean(STATS["site"]["mixed_models_mard"]), indent=0))
    print(json.dumps(clean(STATS["site"]["site_vs_glucose_pattern"])))
    print("\n######## FLEXIBLE MODELS")
    for o, fr in STATS["flexible_models"].items():
        print(f"\n--- {o} (n {fr['n']}; {fr['n_demographic_columns']} demographic columns)")
        rows = []
        for mname, res in fr["results"].items():
            rows.append([mname] + [f"{f1(res[s]['r2_mean'], 3)} ({f1(res[s]['r2_min'], 2)} to {f1(res[s]['r2_max'], 2)})" for s in ["demographics_only", "glucose_pattern_only", "demographics_plus_glucose_pattern"]]
                        + [f"{f1(res['added_r2_demographics_on_top_of_glucose']['mean'], 3, True)} ({f1(res['added_r2_demographics_on_top_of_glucose']['min'], 2, True)} to {f1(res['added_r2_demographics_on_top_of_glucose']['max'], 2, True)})"])
        print(md_table(["Model", "Demographics only", "Glucose pattern only", "Both", "Added by demographics"], rows))
        if "permutation_importance_random_forest" in fr:
            pi = fr["permutation_importance_random_forest"]
            print(f"base OOF R2 {f1(pi['base_oof_r2'], 3)}; top groups by held-out R2 drop:")
            for g, v in list(pi["by_group"].items())[:20]:
                print(f"   {g:32s} {f1(v['r2_drop'], 3, True)}  ({v['n_columns']} cols)")
            for k in ["block_permutation_random_forest", "block_permutation_gradient_boosting"]:
                print(k, json.dumps(clean(fr[k]["by_group"])))
    print("\n######## SEX FOLLOW-UP")
    fu = STATS["followup_sex_low_bias"]
    for name, r in fu["by_range"].items():
        gs = "; ".join(f"{g['group']} {f1(g['median'])} (n {g['n']})" for g in r["groups"] if g["median"] is not None)
        cs = "; ".join(f"M vs F {f1(c['diff_median'], 1, True)} (CI {f1(c['ci_low'], 1, True)} to {f1(c['ci_high'], 1, True)})" for c in r["contrasts"])
        mg = "; ".join(f"{s} median err {f1(v['median'])} mg/dL" for s, v in r["median_err_mgdl_by_sex"].items())
        print(f"{r['label']} | {gs} | {cs} | p {fmt_p(r['p'])} | {mg}")
    for k in ["unadjusted_low_bias", "adjusted_low_bias", "adjusted_low_bias_plus_weight", "adjusted_low_bias_plus_lowpair_depth", "unadjusted_missed_low", "adjusted_missed_low"]:
        mdl = fu[k]
        print(f"-- {k}: n {mdl['n']} R2 {f1(mdl['r2'], 3)}")
        for t in mdl["terms"]:
            print(f"   {t['label']:50s} {f1(t['coef'], 3, True)} (CI {f1(t['ci_low'], 3, True)} to {f1(t['ci_high'], 3, True)}) p {fmt_p(t['p'])}")
    print(json.dumps(clean(fu["selection_check"]), indent=0))
    for a, r in fu["sex_x_arm_low_bias"].items():
        cs = "; ".join(f"M vs F {f1(c['diff_median'], 1, True)} (CI {f1(c['ci_low'], 1, True)} to {f1(c['ci_high'], 1, True)})" for c in r["contrasts"])
        print(f"{a}: {cs} p {fmt_p(r['p'])}")
    print("within-sex weight vs low bias:", json.dumps(clean(fu["within_sex_spearman_bias_vs_weight"])))
    print("pooled low pairs:", json.dumps(clean(fu["pooled_low_pairs"])))
    print("\n######## MEDICATIONS FOLLOW-UP")
    mf = STATS["followup_n_medications"]
    t = mf["by_tertile"]
    print("cuts", mf["tertile_cut_points"], "; ".join(f"{g['group']} {f1(g['median'])} (n {g['n']})" for g in t["groups"]),
          "|", "; ".join(f"{c['group']}: {f1(c['diff_median'], 1, True)} (CI {f1(c['ci_low'], 1, True)} to {f1(c['ci_high'], 1, True)})" for c in t["contrasts"]), "p", fmt_p(t["p"]))
    for k in ["rho_with_age", "rho_with_cv", "rho_with_pct_below_70", "rho_with_n_comorbidities", "rho_with_mard", "rho_with_cal_mard", "rho_with_low_mard", "rho_with_mid_mard"]:
        r = mf[k]
        print(f"   {k:28s} rho {f1(r['rho'], 2, True)} (CI {f1(r['ci_low'], 2, True)} to {f1(r['ci_high'], 2, True)}) p {fmt_p(r['p'])} n {r['n']}")
    for k in ["unadjusted", "adjusted_age_cv_tbr", "adjusted_plus_conditions", "log_mard_adjusted", "cal_mard_adjusted"]:
        mdl = mf[k]
        print(f"-- {k}: n {mdl['n']} R2 {f1(mdl['r2'], 3)}")
        for t in mdl["terms"]:
            print(f"   {t['label']:40s} {f1(t['coef'], 3, True)} (CI {f1(t['ci_low'], 3, True)} to {f1(t['ci_high'], 3, True)}) p {fmt_p(t['p'])}")
    print("\n######## MEDIATION (SD units)")
    for key in ["mediation", "mediation_low_mard"]:
        print("---", key)
        rows = []
        for x, r in STATS[key].items():
            p = r["paths"]
            def c(nm):
                return f"{f1(p[nm]['estimate'], 2, True)} ({f1(p[nm]['ci_low'], 2, True)} to {f1(p[nm]['ci_high'], 2, True)})"
            rows.append([r["label"], c("a_cv_pct"), c("a_pct_below_70"), c("b_cv_pct"), c("b_pct_below_70"), c("indirect_total"), c("direct"), c("total"),
                         f1(r["proportion_mediated"], 2) if r["proportion_mediated"] is not None else "-"])
        print(md_table(["Trait", "a: trait->CV", "a: trait->time<70", "b: CV->MARD", "b: time<70->MARD", "Indirect (total)", "Direct", "Total", "Share mediated"], rows))
    print("\n######## WORST QUARTILE")
    for o, wq in STATS["worst_quartile"].items():
        print(f"\n--- {o}: threshold {f1(wq['threshold'])}, worst n {wq['n_worst']}, rest n {wq['n_rest']}")
        for r in wq["rows"]:
            if r["kind"] == "cont":
                print(f"{r['label']} | rest {f1(r['rest_median'])} vs worst {f1(r['worst_median'])} | std diff {f1(r.get('standardised_diff'), 2, True)} | p {fmt_p(r.get('p'))} | BH {fmt_p(r.get('p_bh'))}")
            else:
                lv = "; ".join(f"{l['level']}: {f1(l['pct_rest'], 0)} % vs {f1(l['pct_worst'], 0)} %" for l in r["levels"])
                print(f"{r['label']} | {lv} | p {fmt_p(r.get('p'))} | BH {fmt_p(r.get('p_bh'))}")
    print("\n######## SHANGHAI")
    S = STATS["shanghai"]
    print({k: S[k] for k in ["patients_total", "patients_with_pairs", "patients_with_min_pairs"]}, json.dumps(clean(S["outcome_summary"])), json.dumps(clean(S["by_type"])))
    print(json.dumps(clean(STATS["shanghai_pooled_low"])))
    for o, _ in SH_OUTCOMES:
        print(f"\n--- {o}")
        for r in S["univariate"][o]:
            if r["kind"] == "cat":
                gs = "; ".join(f"{g['group']} {f1(g['median'])} (n {g['n']})" for g in r["groups"] if g["median"] is not None)
                cs = "; ".join(f"{c['group']} vs {c['vs']}: {f1(c['diff_median'], 1, True)} (CI {f1(c['ci_low'], 1, True)} to {f1(c['ci_high'], 1, True)}; detectable {f1(c['detectable_diff_means'])})" for c in r["contrasts"])
                print(f"{r['label']} | {gs} | {cs} | p {fmt_p(r['p'])} | BH {fmt_p(r.get('p_bh'))} | {'testable' if r['testable'] else 'n.t. ' + str(r.get('excluded_small_groups'))}")
            else:
                print(f"{r['label']} | rho {f1(r['rho'], 2, True)} (CI {f1(r['ci_low'], 2, True)} to {f1(r['ci_high'], 2, True)}) n {r['n']} | p {fmt_p(r['p'])} | BH {fmt_p(r.get('p_bh'))}")
    print(f"\nruntime {STATS['run']['runtime_s']} s")


if __name__ == "__main__":
    main()
