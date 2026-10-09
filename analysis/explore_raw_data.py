"""
Exploratory analysis of the raw data dump for BMEN 600 Group 24.

Datasets
  1. REPLACE-BG (Jaeb Center / T1D Exchange) - pipe-delimited tables in
     "Uncommitted Data/Raw Data Dump/Replace-BG Dataset/Data Tables"
  2. Shanghai T1DM / T2DM (Zhao et al., Figshare) - one Excel file per
     patient-visit plus two summary workbooks in "Uncommitted Data/Raw Data Dump/Shanghai"

Usage (from the repo root)
  python analysis/explore_raw_data.py "Uncommitted Data/Raw Data Dump" analysis

Outputs
  analysis/figures/*.png         figures referenced by RESULTS.md
  analysis/summary_stats.json    every number quoted in RESULTS.md
  stdout                         a readable log of the same numbers
"""
import glob
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.patches
import matplotlib.pyplot as plt

ROOT = sys.argv[1] if len(sys.argv) > 1 else "Raw Data Dump"
OUT = sys.argv[2] if len(sys.argv) > 2 else "analysis"
FIG = os.path.join(OUT, "figures")
os.makedirs(FIG, exist_ok=True)

RB = os.path.join(ROOT, "Replace-BG Dataset", "Data Tables")
SH = os.path.join(ROOT, "Shanghai")

STATS = {}
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:6.1f}s]", *a, flush=True)


# --------------------------------------------------------------------------
# Chart styling (dataviz reference palette, light surface)
# --------------------------------------------------------------------------
C_BLUE, C_ORANGE, C_AQUA = "#2a78d6", "#eb6834", "#1baf7a"   # categorical slots 1-3
RAMP = ["#86b6ef", "#2a78d6", "#104281"]                      # ordinal blue ramp
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
    "font.size": 10,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titleweight": "semibold", "axes.titlesize": 11, "axes.titlelocation": "left",
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.axisbelow": True, "legend.frameon": False, "legend.fontsize": 9,
    "lines.linewidth": 2, "savefig.dpi": 150, "savefig.bbox": "tight",
})


def save(fig, name):
    path = os.path.join(FIG, name)
    fig.savefig(path)
    plt.close(fig)
    log("wrote", path)


def hbar(ax, labels, values, color=C_BLUE, title="", fmt="{:,.0f}"):
    y = np.arange(len(labels))
    ax.barh(y, values, color=color, height=0.62)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_title(title)
    xmax = max(values) if len(values) else 1
    for yi, v in zip(y, values):
        ax.text(v + xmax * 0.015, yi, fmt.format(v), va="center", fontsize=8.5, color=INK2)
    ax.set_xlim(0, xmax * 1.18)


# --------------------------------------------------------------------------
# Glucose range helpers
# --------------------------------------------------------------------------
RANGE_EDGES = [0, 54, 70, 180, 250, 10_000]
RANGE_LABELS = ["<54", "54-69", "70-180", "181-250", ">250"]


def glucose_range(v):
    return pd.cut(v, RANGE_EDGES, labels=RANGE_LABELS, right=False)


def accuracy_table(cgm, ref):
    """Per-range bias and MARD of CGM relative to reference (both mg/dL)."""
    df = pd.DataFrame({"cgm": np.asarray(cgm, float), "ref": np.asarray(ref, float)}).dropna()
    df["err"] = df.cgm - df.ref
    df["rel"] = df.err / df.ref * 100
    df["range"] = glucose_range(df.ref)
    rows = []
    for lab, g in df.groupby("range", observed=False):
        n = len(g)
        rows.append({
            "range": lab, "n": int(n),
            "mean_bias_mgdl": float(g.err.mean()) if n else np.nan,
            "mean_rel_bias_pct": float(g.rel.mean()) if n else np.nan,
            "mard_pct": float(g.rel.abs().mean()) if n else np.nan,
            "within_20pct_or_20mgdl": float(((g.err.abs() <= 20) | (g.rel.abs() <= 20)).mean() * 100) if n else np.nan,
            "pct_cgm_reads_low": float((g.err < 0).mean() * 100) if n else np.nan,
        })
    # same statistics binned by the CGM value instead of the reference (regression-to-the-mean check)
    by_cgm = []
    for lab, g in df.groupby(glucose_range(df.cgm), observed=False):
        n = len(g)
        by_cgm.append({"cgm_range": lab, "n": int(n),
                       "mean_rel_bias_pct": float(g.rel.mean()) if n else np.nan,
                       "mard_pct": float(g.rel.abs().mean()) if n else np.nan,
                       "pct_cgm_reads_low": float((g.err < 0).mean() * 100) if n else np.nan})
    # binned by the AVERAGE of CGM and reference (Bland-Altman style). This grouping is not
    # pulled towards either device's noise, so the low-range bias is not a regression-to-the-mean artefact.
    by_avg = []
    for lab, g in df.groupby(glucose_range((df.cgm + df.ref) / 2), observed=False):
        n = len(g)
        by_avg.append({"avg_range": lab, "n": int(n),
                       "mean_bias_mgdl": float(g.err.mean()) if n else np.nan,
                       "mean_rel_bias_pct": float(g.rel.mean()) if n else np.nan,
                       "mard_pct": float(g.rel.abs().mean()) if n else np.nan,
                       "pct_cgm_reads_low": float((g.err < 0).mean() * 100) if n else np.nan})
    overall = {
        "by_cgm_range": by_cgm,
        "by_avg_range": by_avg,
        "range": "all", "n": int(len(df)),
        "mean_bias_mgdl": float(df.err.mean()), "mean_rel_bias_pct": float(df.rel.mean()),
        "mard_pct": float(df.rel.abs().mean()),
        "within_20pct_or_20mgdl": float(((df.err.abs() <= 20) | (df.rel.abs() <= 20)).mean() * 100),
        "pct_cgm_reads_low": float((df.err < 0).mean() * 100),
    }
    return pd.DataFrame(rows), overall, df


def clarke_zones(ref, cgm):
    """Clarke error grid zone share (%) for (reference, CGM) pairs in mg/dL."""
    ref = np.asarray(ref, float)
    cgm = np.asarray(cgm, float)
    z = np.full(len(ref), "B", dtype="<U1")
    a = ((cgm <= 70) & (ref <= 70)) | (np.abs(cgm - ref) <= 0.2 * ref)
    e = ((ref <= 70) & (cgm >= 180)) | ((ref >= 180) & (cgm <= 70))
    c = ((ref >= 130) & (ref <= 180) & (cgm <= (7 / 5) * ref - 182)) | ((ref >= 70) & (cgm >= ref + 110))
    d = ((ref <= 70) & (cgm >= 70) & (cgm <= 180)) | ((ref >= 240) & (cgm >= 70) & (cgm <= 180))
    z[d] = "D"
    z[c] = "C"
    z[e] = "E"
    z[a] = "A"
    s = pd.Series(z).value_counts(normalize=True).reindex(list("ABCDE"), fill_value=0) * 100
    return s.round(2).to_dict()


# Parkes (consensus) error grid, type 1 diabetes version. Zone boundaries are the polylines
# published by Pfutzner et al. 2013 (J Diabetes Sci Technol 7:1275), in (reference, CGM) mg/dL.
# A point exactly on a boundary belongs to the lower-risk zone.
PARKES_T1 = {
    "upper": {  # CGM reads higher than reference; (x = reference, y = CGM); beyond last x the line is vertical
        "B": ([0, 30, 140, 280, 430], [50, 50, 170, 380, 550]),
        "C": ([0, 30, 50, 70, 260], [60, 60, 80, 110, 550]),
        "D": ([0, 25, 50, 80, 125], [100, 100, 125, 215, 550]),
        "E": ([0, 35, 50], [150, 155, 550]),
    },
    "lower": {  # CGM reads lower than reference; left of first x the line is vertical (zone does not exist there)
        "B": ([50, 170, 385, 550], [30, 145, 300, 450]),
        "C": ([120, 260, 550], [30, 130, 250]),
        "D": ([250, 550], [40, 150]),
    },
}


def parkes_zone_labels(ref, cgm):
    """Parkes consensus error grid zone (A-E) for each (reference, CGM) pair in mg/dL."""
    ref = np.asarray(ref, float)
    cgm = np.asarray(cgm, float)
    z = np.full(len(ref), "A", dtype="<U1")
    for zone in "BCDE":                      # higher-risk zones overwrite lower ones
        xs, ys = PARKES_T1["upper"][zone]
        z[cgm > np.interp(ref, xs, ys, right=np.inf)] = zone
    for zone in "BCD":
        xs, ys = PARKES_T1["lower"][zone]
        z[cgm < np.interp(ref, xs, ys, left=-np.inf)] = zone
    return z


def parkes_zones(ref, cgm):
    """Parkes consensus error grid zone share (%) for (reference, CGM) pairs in mg/dL."""
    s = pd.Series(parkes_zone_labels(ref, cgm)).value_counts(normalize=True).reindex(list("ABCDE"), fill_value=0) * 100
    return s.round(2).to_dict()


def rounded(dct):
    out = {}
    for k, v in dct.items():
        if isinstance(v, float):
            out[k] = round(v, 2)
        elif isinstance(v, list):
            out[k] = [{kk: (round(vv, 2) if isinstance(vv, float) else vv) for kk, vv in r.items()} for r in v]
        else:
            out[k] = v
    return out


# ==========================================================================
# 1. REPLACE-BG participant-level tables
# ==========================================================================
log("Loading REPLACE-BG participant tables")
roster = pd.read_csv(os.path.join(RB, "HPtRoster.txt"), sep="|")
screen = pd.read_csv(os.path.join(RB, "HScreening.txt"), sep="|")
hba1c = pd.read_csv(os.path.join(RB, "HLocalHbA1c.txt"), sep="|")
uploads = pd.read_csv(os.path.join(RB, "HDeviceUploads.txt"), sep="|")
medcond = pd.read_csv(os.path.join(RB, "HMedicalCondition.txt"), sep="|")

ppl = roster.merge(screen, on=["PtID", "SiteID"], how="left")
ppl["BMI"] = ppl.Weight / (ppl.Height / 100) ** 2
ppl["DiabDurationYrs"] = ppl.AgeAsOfEnrollDt - ppl.DiagAge

rb = STATS["replace_bg"] = {}
rb["n_participants"] = int(len(roster))
rb["n_sites"] = int(roster.SiteID.nunique())
rb["status"] = roster.PtStatus.value_counts().to_dict()
rb["treatment_group"] = roster.TrtGroup.value_counts().to_dict()
rb["age"] = ppl.AgeAsOfEnrollDt.describe().round(1).to_dict()
rb["age_bands"] = pd.cut(ppl.AgeAsOfEnrollDt, [18, 25, 35, 45, 55, 65, 80], right=False).value_counts().sort_index().astype(int).rename(str).to_dict()
rb["sex"] = ppl.Gender.value_counts().to_dict()
rb["race"] = ppl.Race.value_counts().to_dict()
rb["ethnicity"] = ppl.Ethnicity.value_counts().to_dict()
rb["education"] = ppl.EduLevel.fillna("Not answered").value_counts().to_dict()
rb["income"] = ppl.AnnualInc.fillna("Not answered/unknown").value_counts().to_dict()
rb["insurance_private_pct"] = float(ppl.InsPrivate.notna().mean() * 100)
rb["diag_age"] = ppl.DiagAge.describe().round(1).to_dict()
rb["diab_duration_yrs"] = ppl.DiabDurationYrs.describe().round(1).to_dict()
rb["bmi"] = ppl.BMI.describe().round(1).to_dict()
rb["bmi_ge_30_pct"] = float((ppl.BMI >= 30).mean() * 100)
rb["cgm_use_status"] = ppl.CGMUseStatus.value_counts().to_dict()
rb["cgm_use_device"] = ppl.CGMUseDevice.fillna("n/a (never used)").value_counts().to_dict()
rb["severe_hypo_history"] = ppl.SHMostRec.value_counts().to_dict()
rb["dka_history"] = ppl.DKAMostRec.value_counts().to_dict()
rb["fingersticks_per_day"] = ppl.Fingerstick7DayAve.describe().round(1).to_dict()
rb["screening_missing_counts"] = {c: int(v) for c, v in screen.isna().sum().items() if v > 0}

rb["hba1c_by_visit"] = hba1c.groupby("Visit").HbA1cTestRes.describe().round(2).loc[
    ["Screening Visit", "Randomization", "Week 13 Visit", "Week 26 Visit"]].to_dict("index")
rb["hba1c_missing_rows"] = int(hba1c.HbA1cTestRes.isna().sum())
hba1c_screen = hba1c[hba1c.Visit == "Screening Visit"].HbA1cTestRes

dev = uploads.drop_duplicates(["PtId", "DeviceManufact", "DeviceModel", "DeviceType"])
rb["cgm_models"] = dev[dev.DeviceType == "cgm"].DeviceModel.value_counts().to_dict()
rb["bgm_models"] = dev[dev.DeviceType.str.contains("bgm")].DeviceModel.value_counts().to_dict()
rb["pump_participants"] = int(dev[dev.DeviceType.str.contains("pump")].PtId.nunique())
rb["top_comorbidities"] = medcond[medcond.MedCond != "Type I diabetes mellitus"].MedCond.value_counts().head(8).to_dict()
log("REPLACE-BG participants:", rb["n_participants"], rb["sex"], rb["race"])

# ==========================================================================
# 2. REPLACE-BG device data (CGM, calibrations, BGM)
# ==========================================================================
log("Loading HDeviceCGM.txt (837 MB) ...")
cgm_all = pd.read_csv(
    os.path.join(RB, "HDeviceCGM.txt"), sep="|",
    usecols=["PtID", "DeviceDtTmDaysFromEnroll", "DeviceTm", "RecordType", "GlucoseValue"],
    dtype={"PtID": "int32", "DeviceDtTmDaysFromEnroll": "int32", "RecordType": "category", "GlucoseValue": "float32"},
)
tm = cgm_all.DeviceTm.str.split(":", expand=True).astype("int32")
cgm_all["t"] = (cgm_all.DeviceDtTmDaysFromEnroll.astype("int64") * 86400
                + tm[0] * 3600 + tm[1] * 60 + tm[2])
cgm_all.drop(columns=["DeviceTm"], inplace=True)
del tm
log("rows:", len(cgm_all), cgm_all.RecordType.value_counts().to_dict())

cgm = cgm_all[cgm_all.RecordType == "CGM"].drop(columns="RecordType").copy()
cal = cgm_all[cgm_all.RecordType == "Calibration"].drop(columns="RecordType").copy()
del cgm_all

d = rb["cgm_device_data"] = {}
d["n_cgm_readings"] = int(len(cgm))
d["n_calibration_records"] = int(len(cal))
d["cgm_glucose_missing"] = int(cgm.GlucoseValue.isna().sum())
d["cgm_min"] = float(cgm.GlucoseValue.min())
d["cgm_max"] = float(cgm.GlucoseValue.max())
d["cgm_pct_at_floor_39"] = float((cgm.GlucoseValue <= 39).mean() * 100)
d["cgm_pct_at_ceiling_401"] = float((cgm.GlucoseValue >= 401).mean() * 100)
d["cgm_glucose_describe"] = cgm.GlucoseValue.describe().round(1).to_dict()
rng = glucose_range(cgm.GlucoseValue).value_counts(normalize=True).sort_index() * 100
d["cgm_pct_by_range"] = rng.round(2).to_dict()
d["time_in_range"] = {"<70": float(rng["<54"] + rng["54-69"]), "70-180": float(rng["70-180"]),
                      ">180": float(rng["181-250"] + rng[">250"])}

cgm["day"] = cgm.t // 86400
per_pt = cgm.groupby("PtID").agg(n=("GlucoseValue", "size"), days=("day", "nunique"),
                                 first_day=("day", "min"), last_day=("day", "max"))
per_pt["span_days"] = per_pt.last_day - per_pt.first_day + 1
per_pt["readings_per_day"] = per_pt.n / per_pt.days
per_pt["coverage_pct"] = per_pt.n / (per_pt.span_days * 288) * 100
d["participants_with_cgm"] = int(len(per_pt))
d["days_with_cgm_per_pt"] = per_pt.days.describe().round(1).to_dict()
d["span_days_per_pt"] = per_pt.span_days.describe().round(1).to_dict()
d["readings_per_day_per_pt"] = per_pt.readings_per_day.describe().round(1).to_dict()
d["coverage_pct_of_288_per_day"] = per_pt.coverage_pct.describe().round(1).to_dict()
d["days_before_enrollment_min"] = int(cgm.DeviceDtTmDaysFromEnroll.min())
d["days_after_enrollment_max"] = int(cgm.DeviceDtTmDaysFromEnroll.max())
d["pct_readings_pre_enrollment"] = float((cgm.DeviceDtTmDaysFromEnroll < 0).mean() * 100)
d["participants_with_readings_before_day_minus_30"] = int(cgm[cgm.DeviceDtTmDaysFromEnroll < -30].PtID.nunique())
d["pct_readings_before_day_minus_30"] = float((cgm.DeviceDtTmDaysFromEnroll < -30).mean() * 100)
d["duplicate_pt_timestamp_rows"] = int(cgm.duplicated(["PtID", "t"]).sum())
cgm.sort_values(["PtID", "t"], inplace=True)
dt = cgm.groupby("PtID").t.diff()
d["interval_median_s"] = float(dt.median())
d["pct_intervals_gt_10min"] = float((dt > 600).mean() * 100)
d["pct_intervals_gt_1h"] = float((dt > 3600).mean() * 100)
del dt
log("CGM per-participant coverage done")

# --- pair calibrations (fingerstick entered in receiver) with preceding CGM
REF_MIN, REF_MAX = 20, 600          # outside this the reference value is a meter code or unit error, not a glucose
cal = cal.dropna(subset=["GlucoseValue"])
p_pre = {"n_calibrations_with_value": int(len(cal)),
         "n_calibrations_outside_20_600": int(((cal.GlucoseValue < REF_MIN) | (cal.GlucoseValue >= REF_MAX)).sum())}
cal = cal[(cal.GlucoseValue >= REF_MIN) & (cal.GlucoseValue < REF_MAX)].sort_values("t")
cgm_sorted = cgm[["PtID", "t", "GlucoseValue"]].sort_values("t").rename(columns={"GlucoseValue": "cgm"})
pairs_cal = pd.merge_asof(cal.rename(columns={"GlucoseValue": "ref"}), cgm_sorted,
                          on="t", by="PtID", direction="backward", tolerance=600)
pairs_cal = pairs_cal.dropna(subset=["cgm"])
tab_cal, ov_cal, df_cal = accuracy_table(pairs_cal.cgm, pairs_cal.ref)
p = rb["pairs_calibration_vs_cgm"] = {}
p["method"] = "Calibration record matched to most recent CGM reading of same participant within 10 min before it"
p.update(p_pre)
p["n_pairs"] = int(len(pairs_cal))
p["participants_in_pairs"] = int(pairs_cal.PtID.nunique())
p["by_range"] = tab_cal.round(2).to_dict("records")
p["overall"] = rounded(ov_cal)
p["clarke_pct"] = clarke_zones(df_cal.ref, df_cal.cgm)
p["parkes_pct"] = parkes_zones(df_cal.ref, df_cal.cgm)
p["n_ref_below_70"] = int((df_cal.ref < 70).sum())
p["n_ref_below_54"] = int((df_cal.ref < 54).sum())
pt_mard = df_cal.assign(PtID=pairs_cal.PtID.values).groupby("PtID").rel.apply(lambda s: s.abs().mean())
p["per_participant_mard"] = pt_mard.describe().round(2).to_dict()
log("calibration pairs:", p["n_pairs"], "MARD", round(ov_cal["mard_pct"], 2))

# --- pair meter (BGM) readings with nearest CGM reading (±5 min)
log("Loading HDeviceBGM.txt")
bgm = pd.read_csv(os.path.join(RB, "HDeviceBGM.txt"), sep="|",
                  usecols=["PtID", "DeviceDtTmDaysFromEnroll", "DeviceTm", "RecordType", "RecordSubType", "GlucoseValue"])
b = rb["bgm_device_data"] = {}
b["n_rows"] = int(len(bgm))
b["record_types"] = bgm.RecordType.value_counts().to_dict()
b["bgm_subtypes"] = bgm[bgm.RecordType == "BGM"].RecordSubType.fillna("(blank)").value_counts().to_dict()
bgm = bgm[bgm.RecordType == "BGM"].copy()
bgm["PtID"] = bgm.PtID.astype("int32")
tm = bgm.DeviceTm.str.split(":", expand=True).astype(int)
bgm["t"] = bgm.DeviceDtTmDaysFromEnroll.astype("int64") * 86400 + tm[0] * 3600 + tm[1] * 60 + tm[2]
b["bgm_glucose_describe"] = bgm.GlucoseValue.describe().round(1).to_dict()
b["bgm_n_below_20_mgdl"] = int((bgm.GlucoseValue < 20).sum())        # implausible; likely mmol/L entries or LO codes
b["bgm_n_ge_600_mgdl"] = int((bgm.GlucoseValue >= 600).sum())        # meter HI code
b["bgm_pct_by_range"] = (glucose_range(bgm.GlucoseValue).value_counts(normalize=True).sort_index() * 100).round(2).to_dict()
b["bgm_per_pt_per_cgm_day"] = (bgm.groupby("PtID").size() / per_pt.days.reindex(bgm.PtID.unique())).describe().round(1).to_dict()
bgm = bgm[(bgm.GlucoseValue >= REF_MIN) & (bgm.GlucoseValue < REF_MAX)].sort_values("t")
pairs_bgm = pd.merge_asof(bgm.rename(columns={"GlucoseValue": "ref"})[["PtID", "t", "ref"]], cgm_sorted,
                          on="t", by="PtID", direction="nearest", tolerance=300).dropna(subset=["cgm"])
tab_bgm, ov_bgm, df_bgm = accuracy_table(pairs_bgm.cgm, pairs_bgm.ref)
p = rb["pairs_bgm_vs_cgm"] = {}
p["method"] = "Meter reading matched to nearest CGM reading of same participant within ±5 min (separate device clocks)"
p["n_pairs"] = int(len(pairs_bgm))
p["pct_of_bgm_matched"] = float(len(pairs_bgm) / len(bgm) * 100)
p["by_range"] = tab_bgm.round(2).to_dict("records")
p["overall"] = rounded(ov_bgm)
p["clarke_pct"] = clarke_zones(df_bgm.ref, df_bgm.cgm)
p["parkes_pct"] = parkes_zones(df_bgm.ref, df_bgm.cgm)
p["n_ref_below_70"] = int((df_bgm.ref < 70).sum())
p["n_ref_below_54"] = int((df_bgm.ref < 54).sum())
log("BGM pairs:", p["n_pairs"], "MARD", round(ov_bgm["mard_pct"], 2))

# ==========================================================================
# 3. Shanghai summary workbooks
# ==========================================================================
log("Loading Shanghai summary workbooks")
MISSING_TOKENS = {"/", "", "nan", "NaN", "none", "None", "NA"}


def load_summary(name):
    path = glob.glob(os.path.join(SH, "*", name))[0]
    df = pd.read_excel(path)
    df.columns = [" ".join(c.split()) for c in df.columns]      # collapse double spaces / trailing spaces
    df = df.rename(columns={"Duration of diabetes (years)": "Duration of Diabetes (years)",
                            "2-hour Postprandial insulin (pmol/L)": "2-hour Postprandial Insulin (pmol/L)"})
    df["pid"] = df["Patient Number"].astype(str).str.split("_").str[0]
    df["sex"] = df["Gender (Female=1, Male=2)"].map({1: "F", 2: "M"})
    df["hba1c_pct"] = pd.to_numeric(df["HbA1c (mmol/mol)"], errors="coerce") / 10.929 + 2.15   # IFCC -> NGSP
    df["on_insulin"] = df["Hypoglycemic Agents"].astype(str).str.contains(
        "insulin|humulin|novolin|gansulin|lantus|degludec|glargine|aspart|lispro|detemir", case=False)
    return df


def summary_stats(df):
    s = {}
    s["n_records"] = int(len(df))
    s["n_patients"] = int(df.pid.nunique())
    s["visits_per_patient"] = df.pid.value_counts().value_counts().sort_index().rename(str).to_dict()
    first = df.drop_duplicates("pid")           # demographic stats on first visit per patient
    s["sex"] = first.sex.value_counts().to_dict()
    age = pd.to_numeric(first["Age (years)"], errors="coerce")
    s["age"] = age.describe().round(1).to_dict()
    s["age_bands"] = pd.cut(age, [18, 25, 35, 45, 55, 65, 100], right=False).value_counts().sort_index().astype(int).rename(str).to_dict()
    s["bmi"] = pd.to_numeric(first["BMI (kg/m2)"], errors="coerce").describe().round(1).to_dict()
    s["duration_yrs"] = pd.to_numeric(first["Duration of Diabetes (years)"], errors="coerce").describe().round(1).to_dict()
    s["hba1c_pct"] = first.hba1c_pct.describe().round(2).to_dict()
    s["on_insulin_pct"] = float(first.on_insulin.mean() * 100)
    s["hypoglycemia_flag"] = df["Hypoglycemia (yes/no)"].astype(str).str.strip().str.lower().value_counts().to_dict()
    s["acute_complications"] = df["Acute Diabetic Complications"].astype(str).str.strip().value_counts().to_dict()
    s["alcohol"] = first["Alcohol Drinking History (drinker/non-drinker)"].astype(str).str.strip().value_counts().to_dict()
    miss = df.drop(columns=["pid", "sex", "hba1c_pct", "on_insulin"]).astype(str).apply(lambda c: c.str.strip().isin(MISSING_TOKENS)).sum()
    s["missing_counts"] = {k: int(v) for k, v in miss.items() if v > 0}
    return s


t1 = load_summary("Shanghai_T1DM_Summary.xlsx")
t2 = load_summary("Shanghai_T2DM_Summary.xlsx")
STATS["shanghai_t1dm"] = summary_stats(t1)
STATS["shanghai_t2dm"] = summary_stats(t2)
log("Shanghai T1DM", STATS["shanghai_t1dm"]["n_patients"], "patients; T2DM", STATS["shanghai_t2dm"]["n_patients"])

# ==========================================================================
# 4. Shanghai per-patient CGM files
# ==========================================================================
log("Loading Shanghai per-patient CGM files")
STANDARD_COLS = {"Date", "CGM (mg / dl)", "CBG (mg / dl)", "Blood Ketone (mmol / L)", "Dietary intake", "饮食",
                 "Insulin dose - s.c.", "Non-insulin hypoglycemic agents", "CSII - bolus insulin (Novolin R, IU)",
                 "CSII - basal insulin (Novolin R, IU / H)", "Insulin dose - i.v."}


def find_col(cols, prefix):
    for c in cols:
        if str(c).strip().lower().startswith(prefix):
            return c
    return None


sh_files = []
for grp in ["Shanghai_T1DM", "Shanghai_T2DM"]:
    for f in sorted(glob.glob(os.path.join(SH, "*", grp, "*.xls*"))):
        if os.path.basename(f).startswith("~$"):
            continue
        df = pd.read_excel(f)
        cols = list(df.columns)
        c_date, c_cgm, c_cbg = find_col(cols, "date"), find_col(cols, "cgm"), find_col(cols, "cbg")
        odd = [c for c in cols if c not in STANDARD_COLS]
        ts = pd.to_datetime(df[c_date], errors="coerce")
        g = pd.to_numeric(df[c_cgm], errors="coerce")
        cbg = pd.to_numeric(df[c_cbg], errors="coerce") if c_cbg else pd.Series(np.nan, index=df.index)
        unit_fix = False
        if g.max() < 35:                      # file reported in mmol/L
            g = g * 18.0
            unit_fix = True
        if c_cbg and cbg.notna().any() and cbg.max() < 35:
            cbg = cbg * 18.0
        interval = ts.diff().dt.total_seconds().median()
        sh_files.append({
            "group": grp.replace("Shanghai_", ""), "file": os.path.basename(f),
            "pid": os.path.basename(f).split("_")[0],
            "rows": len(df), "n_cgm": int(g.notna().sum()), "n_cbg": int(cbg.notna().sum()),
            "n_cbg_lt70": int((cbg < 70).sum()), "n_cbg_lt54": int((cbg < 54).sum()),
            "days": float((ts.max() - ts.min()).total_seconds() / 86400) if ts.notna().any() else np.nan,
            "interval_min": interval / 60 if pd.notna(interval) else np.nan,
            "cgm_mean": float(g.mean()), "pct_lt70": float((g < 70).mean() * 100),
            "pct_in_range": float(((g >= 70) & (g <= 180)).mean() * 100), "pct_gt180": float((g > 180).mean() * 100),
            "nonstandard_columns": odd, "unit_converted": unit_fix,
            "cgm_values": g.dropna().to_numpy(), "pairs": pd.DataFrame({"cgm": g, "ref": cbg}).dropna(),
        })
shf = pd.DataFrame(sh_files)
sh = STATS["shanghai_cgm_files"] = {}
sh["n_files"] = int(len(shf))
sh["files_by_group"] = shf.group.value_counts().to_dict()
sh["patients_by_group"] = shf.groupby("group").pid.nunique().to_dict()
sh["total_cgm_readings"] = int(shf.n_cgm.sum())
sh["total_cbg_readings"] = int(shf.n_cbg.sum())
sh["files_with_zero_cbg"] = int((shf.n_cbg == 0).sum())
sh["cbg_per_file"] = shf.n_cbg.describe().round(1).to_dict()
sh["days_per_file"] = shf.days.describe().round(1).to_dict()
sh["interval_min_mode"] = float(shf.interval_min.mode().iloc[0])
sh["files_with_nonstandard_columns"] = {r.file: r.nonstandard_columns for r in shf.itertuples() if r.nonstandard_columns}
sh["files_unit_converted_from_mmol"] = shf[shf.unit_converted].file.tolist()
for grp in ["T1DM", "T2DM"]:
    vals = np.concatenate(shf[shf.group == grp].cgm_values.tolist())
    rng = glucose_range(pd.Series(vals)).value_counts(normalize=True).sort_index() * 100
    sh[f"{grp}_cgm_describe"] = pd.Series(vals).describe().round(1).to_dict()
    sh[f"{grp}_cgm_pct_by_range"] = rng.round(2).to_dict()
    sh[f"{grp}_time_in_range"] = {"<70": float(rng["<54"] + rng["54-69"]), "70-180": float(rng["70-180"]), ">180": float(rng["181-250"] + rng[">250"])}
    sh[f"{grp}_cgm_min"] = float(vals.min())
    sh[f"{grp}_cgm_max"] = float(vals.max())
sh_pairs = pd.concat([r.pairs.assign(group=r.group, pid=r.pid) for r in shf.itertuples()], ignore_index=True)
tab_sh, ov_sh, df_sh = accuracy_table(sh_pairs.cgm, sh_pairs.ref)
p = sh["pairs_cbg_vs_cgm"] = {}
p["method"] = "Capillary blood glucose (CBG) recorded on the same 15-min CGM row"
p["n_pairs"] = int(len(sh_pairs))
p["n_pairs_by_group"] = sh_pairs.group.value_counts().to_dict()
p["by_range"] = tab_sh.round(2).to_dict("records")
p["overall"] = rounded(ov_sh)
p["clarke_pct"] = clarke_zones(df_sh.ref, df_sh.cgm)
p["parkes_pct"] = parkes_zones(df_sh.ref, df_sh.cgm)
p["n_ref_below_70"] = int((df_sh.ref < 70).sum())
p["n_ref_below_54"] = int((df_sh.ref < 54).sum())
for grp in ["T1DM", "T2DM"]:
    sub = sh_pairs[sh_pairs.group == grp]
    _, ov, _ = accuracy_table(sub.cgm, sub.ref)
    p[f"overall_{grp}"] = rounded(ov)
log("Shanghai CBG pairs:", p["n_pairs"], "MARD", round(ov_sh["mard_pct"], 2))

# ==========================================================================
# 5. Figures
# ==========================================================================
log("Drawing figures")
t1_first, t2_first = t1.drop_duplicates("pid"), t2.drop_duplicates("pid")

# F1 age distribution, small multiples
fig, axes = plt.subplots(1, 3, figsize=(11, 3.4), sharex=True)
bins = np.arange(15, 100, 5)
for ax, (lab, vals, col) in zip(axes, [
        (f"REPLACE-BG (n={len(ppl)})", ppl.AgeAsOfEnrollDt, C_BLUE),
        (f"Shanghai T1DM (n={len(t1_first)})", pd.to_numeric(t1_first["Age (years)"]), C_ORANGE),
        (f"Shanghai T2DM (n={len(t2_first)})", pd.to_numeric(t2_first["Age (years)"]), C_AQUA)]):
    ax.hist(vals, bins=bins, color=col, rwidth=0.9)
    ax.set_title(lab)
    ax.axvline(vals.median(), color=INK2, lw=1, ls=":")
    ax.text(vals.median() + 1, ax.get_ylim()[1] * 0.92, f"median {vals.median():.0f}", fontsize=8.5, color=INK2)
    ax.set_xlabel("Age (years)")
axes[0].set_ylabel("Participants")
fig.suptitle("Age at enrolment: REPLACE-BG is a working-age cohort, Shanghai is older", x=0.01, ha="left", fontsize=12, fontweight="semibold", color=INK)
fig.tight_layout()
save(fig, "01_age_distribution.png")

# F2 REPLACE-BG demographics
fig, axes = plt.subplots(2, 2, figsize=(11, 7))
sx = ppl.Gender.map({"M": "Male", "F": "Female"}).value_counts()
hbar(axes[0, 0], sx.index, sx.values, title="Sex")
rc = ppl.Race.value_counts()
hbar(axes[0, 1], rc.index, rc.values, title="Race")
ed_order = ["High school graduate/diploma/GED", "Some college but no degree", "Associate Degree", "Bachelor's Degree", "Master's Degree", "Professional Degree", "Doctorate Degree"]
ed = ppl.EduLevel.value_counts().reindex(ed_order).fillna(0)
hbar(axes[1, 0], [e.replace("graduate/diploma/GED", "grad / GED") for e in ed.index], ed.values,
     title=f"Highest education ({int(ppl.EduLevel.isna().sum())} not answered)")
inc_order = ["Less than $25,000", "$25,000 - $35,000", "$35,000 - less than $50,000", "$50,000 - less than $75,000",
             "$75,000 - less than $100,000", "$100,000 - less than $200,000", "$200,000 or more"]
inc = ppl.AnnualInc.value_counts().reindex(inc_order).fillna(0)
hbar(axes[1, 1], [i.replace(" - less than ", " to <").replace(",000", "k").replace("$", r"\$") for i in inc.index], inc.values,
     title=f"Annual household income ({int(ppl.AnnualInc.isna().sum())} not answered)")
fig.suptitle("REPLACE-BG participants (n=226): sex-balanced, overwhelmingly White, highly educated and affluent", x=0.01, ha="left", fontsize=12, fontweight="semibold", color=INK)
fig.tight_layout()
save(fig, "02_replacebg_demographics.png")

# F3 HbA1c
fig, ax = plt.subplots(figsize=(9, 3.8))
data = [hba1c_screen.dropna(), t1_first.hba1c_pct.dropna(), t2_first.hba1c_pct.dropna()]
labels = [f"REPLACE-BG screening\n(n={len(data[0])})", f"Shanghai T1DM\n(n={len(data[1])})", f"Shanghai T2DM\n(n={len(data[2])})"]
rngs = np.random.default_rng(0)
for i, (v, c) in enumerate(zip(data, [C_BLUE, C_ORANGE, C_AQUA])):
    ax.scatter(v, i + rngs.uniform(-0.18, 0.18, len(v)), s=18, color=c, alpha=0.55, edgecolor=SURFACE, linewidth=0.6)
    ax.plot([v.median(), v.median()], [i - 0.3, i + 0.3], color=INK, lw=2)
    ax.text(v.median(), i + 0.36, f"median {v.median():.1f}%", ha="center", fontsize=8.5, color=INK2)
ax.set_yticks(range(3), labels)
ax.invert_yaxis()
ax.grid(axis="y", visible=False); ax.grid(axis="x", visible=True)
ax.set_xlabel("HbA1c (%)   [Shanghai converted from mmol/mol: % = mmol/mol / 10.929 + 2.15]")
ax.set_title("Glycaemic control: REPLACE-BG enrolled HbA1c ≤ 9%; Shanghai in-patients run far higher")
fig.tight_layout()
save(fig, "03_hba1c_distribution.png")

# F4 Missing data in Shanghai summary workbooks
cols_lab = ["Fasting Plasma Glucose (mg/dl)", "2-hour Postprandial Plasma Glucose (mg/dl)", "Fasting C-peptide (nmol/L)",
            "2-hour Postprandial C-peptide (nmol/L)", "Fasting Insulin (pmol/L)", "2-hour Postprandial Insulin (pmol/L)",
            "HbA1c (mmol/mol)", "Glycated Albumin (%)", "Total Cholesterol (mmol/L)", "Triglyceride (mmol/L)",
            "Creatinine (umol/L)", "Estimated Glomerular Filtration Rate (ml/min/1.73m2)", "Uric Acid (mmol/L)", "Blood Urea Nitrogen (mmol/L)"]
m1 = pd.Series({c: STATS["shanghai_t1dm"]["missing_counts"].get(c, 0) / len(t1) * 100 for c in cols_lab})
m2 = pd.Series({c: STATS["shanghai_t2dm"]["missing_counts"].get(c, 0) / len(t2) * 100 for c in cols_lab})
fig, ax = plt.subplots(figsize=(9.5, 5.5))
y = np.arange(len(cols_lab)); hgt = 0.38
ax.barh(y - hgt / 2 - 0.02, m1.values, height=hgt, color=C_ORANGE, label=f"T1DM summary ({len(t1)} records)")
ax.barh(y + hgt / 2 + 0.02, m2.values, height=hgt, color=C_AQUA, label=f"T2DM summary ({len(t2)} records)")
short = [c.split(" (")[0].replace("Estimated Glomerular Filtration Rate", "eGFR") for c in cols_lab]
ax.set_yticks(y, short); ax.invert_yaxis()
ax.grid(axis="y", visible=False); ax.grid(axis="x", visible=True)
ax.set_xlabel("Records with value missing (recorded as '/')  (%)")
ax.legend(loc="lower right")
for yi, v in zip(y + hgt / 2 + 0.02, m2.values):
    ax.text(v + 0.6, yi, f"{v:.0f}%", va="center", fontsize=8, color=INK2)
ax.set_title("Shanghai summary workbooks: lab values are often missing, especially 2-h postprandial and insulin assays")
fig.tight_layout()
save(fig, "04_shanghai_missing_labs.png")

# F5 CGM glucose distributions
fig, ax = plt.subplots(figsize=(10, 4))
bins = np.arange(36, 410, 9)          # 9 mg/dL = 5 x 1.8, avoids aliasing on the Shanghai mmol/L-derived values
vals_t1 = np.concatenate(shf[shf.group == "T1DM"].cgm_values.tolist())
vals_t2 = np.concatenate(shf[shf.group == "T2DM"].cgm_values.tolist())
for v, c, lab in [(cgm.GlucoseValue.to_numpy(), C_BLUE, f"REPLACE-BG, Dexcom G4 ({len(cgm)/1e6:.1f} M readings)"),
                  (vals_t1, C_ORANGE, f"Shanghai T1DM ({len(vals_t1):,} readings)"),
                  (vals_t2, C_AQUA, f"Shanghai T2DM ({len(vals_t2):,} readings)")]:
    hist, edges = np.histogram(v, bins=bins, density=True)
    ax.plot((edges[:-1] + edges[1:]) / 2, hist * 100, color=c, label=lab)
ymax = ax.get_ylim()[1]
for x in (70, 180):
    ax.axvline(x, color=AXIS, lw=1)
    ax.text(x + 2, ymax * 0.97, f"{x} mg/dL", fontsize=8, color=MUTED, va="top")
ax.set_xlabel("CGM glucose (mg/dL)"); ax.set_ylabel("Share of readings per mg/dL (%)")
ax.legend(loc="upper right")
ax.set_title("CGM glucose distribution: readings below 70 mg/dL are the thin left tail in every cohort")
fig.tight_layout()
save(fig, "05_cgm_glucose_distribution.png")

# F6 time-in-range stacked bars (ordinal ramp)
tir = pd.DataFrame({"REPLACE-BG": d["time_in_range"], "Shanghai T1DM": sh["T1DM_time_in_range"],
                    "Shanghai T2DM": sh["T2DM_time_in_range"]}).T[["<70", "70-180", ">180"]]
fig, ax = plt.subplots(figsize=(8, 3.2))
left = np.zeros(len(tir))
for lab, col in zip(tir.columns, RAMP):
    ax.barh(tir.index, tir[lab], left=left, color=col, height=0.55, label=f"{lab} mg/dL", edgecolor=SURFACE, linewidth=2)
    for i, (l0, v) in enumerate(zip(left, tir[lab])):
        if v > 4:
            ax.text(l0 + v / 2, i, f"{v:.1f}%", ha="center", va="center", fontsize=8.5, color=INK if col == RAMP[0] else SURFACE)
    left += tir[lab].values
ax.invert_yaxis(); ax.set_xlim(0, 100); ax.grid(visible=False)
ax.set_xlabel("Share of CGM readings (%)")
ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.25))
ax.set_title("Time in range from CGM: readings below 70 mg/dL are a few percent in every cohort")
fig.tight_layout()
save(fig, "06_time_in_range.png")

# F7 CGM coverage
fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.4))
axes[0].hist(per_pt.days, bins=np.arange(0, 320, 15), color=C_BLUE, rwidth=0.9)
axes[0].set_title("REPLACE-BG: days with ≥1 CGM reading"); axes[0].set_xlabel("Days per participant"); axes[0].set_ylabel("Participants")
axes[1].hist(per_pt.readings_per_day, bins=np.arange(100, 300, 10), color=C_BLUE, rwidth=0.9)
axes[1].axvline(288, color=INK2, lw=1, ls=":")
axes[1].text(284, axes[1].get_ylim()[1] * 0.55, "288 = full day\nat 5 min", ha="right", fontsize=8, color=INK2)
axes[1].set_title("REPLACE-BG: readings per CGM day"); axes[1].set_xlabel("Readings / day")
axes[2].hist([shf[shf.group == "T1DM"].days, shf[shf.group == "T2DM"].days], bins=np.arange(0, 16, 1),
             color=[C_ORANGE, C_AQUA], label=["T1DM", "T2DM"], rwidth=0.9)
axes[2].set_title("Shanghai: days of CGM per patient file"); axes[2].set_xlabel("Days"); axes[2].legend()
fig.tight_layout()
save(fig, "07_cgm_coverage.png")

# F8 CGM vs reference scatter (one series per panel)
fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.4))
panels = [(df_cal, C_BLUE, f"REPLACE-BG: receiver calibrations\n(n={len(df_cal):,} pairs, MARD {ov_cal['mard_pct']:.1f}%)"),
          (df_bgm, C_BLUE, f"REPLACE-BG: meter readings ±5 min\n(n={len(df_bgm):,} pairs, MARD {ov_bgm['mard_pct']:.1f}%)"),
          (df_sh, C_ORANGE, f"Shanghai: CBG on CGM row\n(n={len(df_sh):,} pairs, MARD {ov_sh['mard_pct']:.1f}%)")]
for ax, (df_, c, title) in zip(axes, panels):
    samp = df_.sample(min(len(df_), 40_000), random_state=0)
    ax.scatter(samp.ref, samp.cgm, s=3, color=c, alpha=0.15, linewidths=0)
    ax.plot([0, 420], [0, 420], color=INK2, lw=1)
    ax.plot([0, 420], [0, 420 * 0.8], color=AXIS, lw=1, ls=":"); ax.plot([0, 420], [0, 420 * 1.2], color=AXIS, lw=1, ls=":")
    for x in (70, 180):
        ax.axvline(x, color=GRID, lw=1); ax.axhline(x, color=GRID, lw=1)
    ax.set_xlim(20, 420); ax.set_ylim(20, 420); ax.set_aspect("equal")
    ax.set_xlabel("Reference fingerstick glucose (mg/dL)"); ax.set_title(title, fontsize=9.5)
    ax.grid(visible=False)
axes[0].set_ylabel("CGM glucose (mg/dL)")
axes[2].text(300, 60, "dotted: ±20%", fontsize=8, color=MUTED)
fig.suptitle("CGM versus reference glucose: pairs cluster on the identity line, scatter widens at the low end", x=0.01, y=0.995, ha="left", fontsize=12, fontweight="semibold", color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.93))
save(fig, "08_cgm_vs_reference_scatter.png")

# F9 accuracy by range: pairs (by reference range), bias (by AVERAGE of CGM and reference), MARD (by reference range)
# Bias is binned by the average of the two readings (Bland-Altman style) so the low bins are not biased by
# selecting low reference values (regression to the mean, see RESULTS.md pitfall 1).
SMALL_N = 50


def bar_with_labels(ax, xs, vals, ns, color, fmt, label=None):
    """Bars plus a value label on each bar. Bars with fewer than SMALL_N pairs are hatched and get an n= label."""
    bars = ax.bar(xs, vals, width=w, color=color, label=label)
    for bar, xi, v, n in zip(bars, xs, vals, ns):
        if n < SMALL_N:
            bar.set_hatch("////"); bar.set_edgecolor(SURFACE); bar.set_linewidth(0)
        if np.isnan(v):
            continue
        txt = fmt.format(v) + (f" (n={n})" if n < SMALL_N else "")
        ax.text(xi, v, txt, ha="center", va="bottom" if v >= 0 else "top", rotation=90, fontsize=7.5, color=INK2)


def pad_ylim(ax, lo, hi, frac=0.42):
    span = max(hi - min(lo, 0), 1)
    ax.set_ylim(min(lo, 0) - (frac * span if lo < 0 else 0), max(hi, 0) + (frac * span if hi > 0 else 0))


fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.4))
x = np.arange(len(RANGE_LABELS)); w = 0.26
avg_cal, avg_bgm, avg_sh = (pd.DataFrame(o["by_avg_range"]) for o in (ov_cal, ov_bgm, ov_sh))
series = [("REPLACE-BG calibrations", tab_cal, avg_cal, C_BLUE),
          ("REPLACE-BG meter ±5 min", tab_bgm, avg_bgm, RAMP[0]),
          ("Shanghai CBG", tab_sh, avg_sh, C_ORANGE)]
lo1 = hi1 = hi2 = 0
for i, (lab, tab, avg, c) in enumerate(series):
    off = (i - 1) * (w + 0.02)
    bars = axes[0].bar(x + off, tab.n.clip(lower=0.5), width=w, color=c, label=lab)
    for bar, xi, n in zip(bars, x + off, tab.n):
        if n < SMALL_N:
            bar.set_hatch("////"); bar.set_edgecolor(SURFACE); bar.set_linewidth(0)
        axes[0].text(xi, max(n, 0.5) * 1.2, f"{n:,}", ha="center", fontsize=7.5, color=INK2, rotation=90, va="bottom")
    bar_with_labels(axes[1], x + off, avg.mean_rel_bias_pct.values, avg.n.values, c, "{:+.1f}")
    bar_with_labels(axes[2], x + off, tab.mard_pct.values, tab.n.values, c, "{:.1f}")
    lo1, hi1 = min(lo1, avg.mean_rel_bias_pct.min()), max(hi1, avg.mean_rel_bias_pct.max())
    hi2 = max(hi2, tab.mard_pct.max())
axes[0].set_yscale("log"); axes[0].set_ylim(0.5, 5e7)
axes[0].set_title("Number of paired readings"); axes[0].set_ylabel("Pairs (count, log scale)")
axes[1].axhline(0, color=AXIS, lw=1); pad_ylim(axes[1], lo1, hi1)
axes[1].set_title("Mean relative bias, CGM minus reference"); axes[1].set_ylabel("Bias (%)")
pad_ylim(axes[2], 0, hi2)
axes[2].set_title("Mean absolute relative difference (MARD)"); axes[2].set_ylabel("MARD (%)")
for ax in axes:
    ax.set_xticks(x, RANGE_LABELS)
axes[0].set_xlabel("Reference glucose range (mg/dL)")
axes[1].set_xlabel("Average of CGM and reference (mg/dL)")
axes[2].set_xlabel("Reference glucose range (mg/dL)")
handles, labels_ = axes[0].get_legend_handles_labels()
handles.append(matplotlib.patches.Patch(facecolor=MUTED, hatch="////", edgecolor=SURFACE, linewidth=0, label=f"hatched = fewer than {SMALL_N} pairs"))
fig.legend(handles=handles, loc="upper left", ncol=4, fontsize=9, bbox_to_anchor=(0.01, 0.935))
fig.suptitle("Accuracy by glucose range: error is largest below 70 mg/dL, where pairs are fewest", x=0.01, y=0.995, ha="left", fontsize=12, fontweight="semibold", color=INK)
fig.text(0.01, 0.845, "Bias is grouped by the average of CGM and reference, so the low bins are not biased by picking low reference values. "
         "MARD is grouped by reference value; this inflates MARD a little in the lowest bins.", fontsize=8.5, color=INK2)
fig.tight_layout(rect=(0, 0, 1, 0.835))
save(fig, "09_accuracy_by_range.png")

# F10 per-participant MARD (REPLACE-BG calibrations)
fig, ax = plt.subplots(figsize=(8, 3.2))
ax.hist(pt_mard, bins=np.arange(4, 30, 1), color=C_BLUE, rwidth=0.9)
ax.axvline(pt_mard.median(), color=INK2, lw=1, ls=":")
ax.text(pt_mard.median() + 0.2, ax.get_ylim()[1] * 0.9, f"median {pt_mard.median():.1f}%", fontsize=8.5, color=INK2)
ax.set_xlabel("Per-participant MARD vs calibration fingersticks (%)"); ax.set_ylabel("Participants")
ax.set_title("REPLACE-BG: sensor accuracy varies substantially between participants")
fig.tight_layout()
save(fig, "10_per_participant_mard.png")

# F11 Parkes (consensus) error grid: where each pair falls in zones A-E
def draw_parkes(ax, df_, color, title, zones_pct, n_plot=40_000):
    samp = df_.sample(min(len(df_), n_plot), random_state=0)
    ax.scatter(samp.ref, samp.cgm, s=3, color=color, alpha=0.18, linewidths=0)
    ax.plot([0, 550], [0, 550], color=AXIS, lw=0.8, ls=":")
    for side in ("upper", "lower"):
        for xs, ys in PARKES_T1[side].values():
            ax.plot(xs, ys, color=INK2, lw=0.9)
    box = dict(boxstyle="round,pad=0.15", fc=SURFACE, ec="none", alpha=0.9)
    for z, (xx, yy) in {"A": (360, 320), "B": (150, 200), "C": (110, 250), "D": (55, 250), "E": (18, 250)}.items():
        ax.text(xx, yy, z, fontsize=10, fontweight="bold", color=INK, ha="center", va="center", bbox=box)
    for z, (xx, yy) in {"B": (300, 180), "C": (300, 90), "D": (380, 35)}.items():
        ax.text(xx, yy, z, fontsize=10, fontweight="bold", color=INK, ha="center", va="center", bbox=box)
    pct = "\n".join(f"{z}  {zones_pct[z]:5.1f} %" for z in "ABCDE")
    ax.text(0.03, 0.97, pct, transform=ax.transAxes, ha="left", va="top", fontsize=9, color=INK, family="monospace",
            bbox=dict(boxstyle="round,pad=0.35", fc=SURFACE, ec=GRID, lw=1))
    ax.set_xlim(0, 420); ax.set_ylim(0, 420); ax.set_aspect("equal")
    ax.set_xticks(range(0, 421, 70)); ax.set_yticks(range(0, 421, 70))
    ax.set_xlabel("Reference fingerstick glucose (mg/dL)"); ax.set_title(title, fontsize=10)
    ax.grid(visible=False)


pk_bgm, pk_sh = rb["pairs_bgm_vs_cgm"]["parkes_pct"], sh["pairs_cbg_vs_cgm"]["parkes_pct"]
fig, axes = plt.subplots(1, 2, figsize=(8.2, 4.5))
draw_parkes(axes[0], df_bgm, C_BLUE, f"REPLACE-BG meter pairs (n={len(df_bgm):,})", pk_bgm)
draw_parkes(axes[1], df_sh, C_ORANGE, f"Shanghai CBG pairs (n={len(df_sh):,})", pk_sh)
axes[0].set_ylabel("CGM glucose (mg/dL)")
fig.suptitle(f"Consensus (Parkes) error grid: {pk_bgm['A'] + pk_bgm['B']:.1f} % of REPLACE-BG pairs in zones A or B",
             x=0.01, y=0.995, ha="left", fontsize=12, fontweight="semibold", color=INK)
fig.text(0.01, 0.905, "A = accurate. B = small error, no harm. C, D, E = error could change treatment. "
         "Dots: random 40,000 pairs per panel. Zone % uses all pairs. Axes cut at 420 mg/dL.", fontsize=8.5, color=INK2)
fig.tight_layout(rect=(0, 0, 1, 0.88))
save(fig, "11_parkes_error_grid.png")

# ==========================================================================
# 6. Dump stats
# ==========================================================================
def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if np.isnan(o) else round(float(o), 3)
    if isinstance(o, pd.Interval):
        return str(o)
    return o


with open(os.path.join(OUT, "summary_stats.json"), "w", encoding="utf-8") as f:
    json.dump(clean(STATS), f, indent=2, ensure_ascii=False)
log("wrote summary_stats.json")
