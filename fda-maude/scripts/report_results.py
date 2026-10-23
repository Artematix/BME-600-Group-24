"""Turn finished MAUDE + recall pull data into report-ready tables, figures, and a markdown summary.

Inputs (read only):
  fda-maude/results/counts/*.csv          counts for ALL CGM reports (tier 1)
  fda-maude/results/recalls_cgm.csv       recall records
  fda-maude/results/recall_harm_manual.csv
  fda-maude/clean/serious.csv.gz          death + injury reports (tier 2)

Outputs:
  fda-maude/results/report/report_results.md
  fda-maude/results/report/tables/*.csv
  fda-maude/results/report/figures/*.png

Run:  py -3.11 fda-maude/scripts/report_results.py [path/to/serious.csv.gz] [--only-f-summary]
  --only-f-summary   rewrite only tables/f_libre3_summary.csv, then stop
  --help, -h         show this text
No API calls. The malfunction sample (clean/sample.csv.gz) and the full pull
(clean/full.csv.gz) are finished but not used here. Counts already cover all reports.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = Path(__file__).resolve().parents[1]          # fda-maude/
RES = ROOT / "results"
CNT = RES / "counts"
OUT = RES / "report"
TAB = OUT / "tables"
FIG = OUT / "figures"
# --only-f-summary: rewrite ONLY tables/f_libre3_summary.csv (no figures, no other tables, no .md), then stop.
ONLY_F = "--only-f-summary" in sys.argv[1:]
_ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
SERIOUS = Path(_ARGS[0]) if _ARGS else ROOT / "clean" / "serious.csv.gz"
if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
    print(__doc__)
    sys.exit(0)
if not SERIOUS.is_file():
    sys.exit(f"Missing input: {SERIOUS} (death + injury reports, about 32 MB, gitignored). "
             "Copy fda-maude/clean/serious.csv.gz from the old machine, or rebuild it with the robot "
             "(maude_robot.py counts, serious, clean). See fda-maude/README.md.")
TAB.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

PULL_DATE = "2026-10-19"
FDA_DATA_DATE = "2026-10-07"

# ---------------------------------------------------------------- style
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
GRAY = "#9a9893"
MFR_COLOR = {"Dexcom": BLUE, "Abbott": ORANGE, "Medtronic": AQUA, "Senseonics": YELLOW, "Other / unknown": GRAY}
MFR_ORDER = ["Dexcom", "Abbott", "Medtronic", "Senseonics", "Other / unknown"]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.labelsize": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "legend.frameon": False, "figure.dpi": 100, "savefig.dpi": 300, "savefig.bbox": "tight",
})


def save(fig, name):
    if ONLY_F:
        plt.close(fig)
        return
    fig.savefig(FIG / name, facecolor="white")
    plt.close(fig)


def wtab(df, name):
    if ONLY_F and name != "f_libre3_summary.csv":
        return df
    df.to_csv(TAB / name, index=False)
    return df


def md_table(df, fmt_int=True):
    cols = list(df.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (int, np.integer)) and fmt_int:
                cells.append(f"{v:,}")
            elif isinstance(v, (float, np.floating)):
                cells.append("" if pd.isna(v) else (f"{v:,.0f}" if float(v).is_integer() and abs(v) > 100 else f"{v:,.1f}"))
            else:
                cells.append("" if pd.isna(v) else str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------- brand cleaning
def classify(brand, code="", mfr=""):
    """Return (manufacturer, product family) from messy brand / manufacturer text."""
    b = str(brand or "").upper()
    m = str(mfr or "").upper()
    if "STELO" in b:
        return "Dexcom", "Dexcom Stelo"
    if "LINGO" in b:
        return "Abbott", "Abbott Lingo"
    if "INSTINCT" in b:
        return "Medtronic", "Medtronic Instinct (made by Abbott)"
    if "SIMPLERA" in b or "SIM SYNC" in b:
        return "Medtronic", "Medtronic Simplera"
    if "EVERSENSE" in b:
        return "Senseonics", "Senseonics Eversense"
    if re.search(r"LIBRE\s*3", b):
        return "Abbott", "Abbott Libre 3 / 3 Plus"
    if re.search(r"LIBRE\s*2", b):
        return "Abbott", "Abbott Libre 2 / 2 Plus"
    if "LIBRE" in b or "NAVIGATOR" in b:
        if any(k in b for k in ("LIBRELINK", "APP", "NAVIGATOR", "SELECT")):
            return "Abbott", "Abbott other (Navigator, apps)"
        return "Abbott", "Abbott Libre 14-day / original"
    medtronic_tokens = ("MMT", "GST", "GRDN", "GUARDIAN", "ENLITE", "MINILINK", "MINIMED", "PARADIGM",
                        "PRDGM", "CARELINK", "IPRO", "GS3", "SOF-SENSOR", "MEDTRONIC", "CGM MODULE")
    is_dex = "DEXCOM" in b
    if not is_dex and any(t in b for t in medtronic_tokens):
        return "Medtronic", "Medtronic Guardian and older"
    if is_dex or re.search(r"\bG[4-7]|G4PLAT|SEVEN (PLUS )?CONTINUOUS", b):
        if re.search(r"G7", b):
            return "Dexcom", "Dexcom G7"
        if re.search(r"G6", b):
            return "Dexcom", "Dexcom G6"
        if re.search(r"G5", b):
            return "Dexcom", "Dexcom G5"
        if re.search(r"G4", b):
            return "Dexcom", "Dexcom G4"
        return "Dexcom", "Dexcom other (Seven, ONE, apps)"
    # fall back on manufacturer field (serious reports only have it)
    if "DEXCOM" in m:
        return "Dexcom", "Dexcom other (Seven, ONE, apps)"
    if "ABBOTT" in m:
        return "Abbott", "Abbott other (Navigator, apps)"
    if "MEDTRONIC" in m:
        return "Medtronic", "Medtronic Guardian and older"
    if "SENSEONICS" in m:
        return "Senseonics", "Senseonics Eversense"
    return "Other / unknown", "Other / unknown"


FAMILY_ORDER = ["Dexcom G4", "Dexcom G5", "Dexcom G6", "Dexcom G7", "Dexcom Stelo", "Dexcom other (Seven, ONE, apps)",
                "Abbott Libre 14-day / original", "Abbott Libre 2 / 2 Plus", "Abbott Libre 3 / 3 Plus", "Abbott Lingo",
                "Abbott other (Navigator, apps)", "Medtronic Guardian and older", "Medtronic Simplera",
                "Medtronic Instinct (made by Abbott)", "Senseonics Eversense", "Other / unknown"]

# ---------------------------------------------------------------- problem families
PROBLEM_FAMILY = {
    "Wrong readings (accuracy)": [
        "Incorrect, Inadequate or Imprecise Result or Readings", "Low Readings", "High Readings", "Imprecision",
        "Invalid Sensing", "Incorrect Or Inadequate Test Results", "High Test Results", "Low Test Results",
        "Incorrect Measurement", "False Reading From Device Non-Compliance", "Calibration Problem",
        "Calibration Error", "Failure to Calibrate", "Unexpected Therapeutic Results", "False Positive Result",
        "False Negative Result"],
    "Signal loss / connection": [
        "Wireless Communication Problem", "Communication or Transmission Problem", "Connection Problem",
        "Application Network Problem", "Loss of Data", "Intermittent Communication Failure"],
    "No readings / sensor stopped": [
        "No Device Output", "Unable to Obtain Readings", "Premature End-of-Life Indicator", "Failure to Sense",
        "Device Inoperable", "Failure to Power Up", "Unexpected Shutdown", "Inappropriate or Unexpected Reset",
        "Device Stops Intermittently", "Output Problem", "Device Sensing Problem", "Failure to Read Input Signal",
        "Loss of Power", "Therapeutic or Diagnostic Output Failure", "Failure of Device to Self-Test",
        "Intermittent Loss of Power", "Device Fails to Read"],
    "Falls off / insertion / applicator": [
        "Detachment of Device or Device Component", "Detachment Of Device Component", "Retraction Problem",
        "Unintended Ejection", "Difficult to Remove", "Loss of or Failure to Bond", "Difficult to Insert",
        "Activation, Positioning or Separation Problem", "Failure to Fire", "Activation Problem",
        "Difficult or Delayed Activation", "Activation Failure", "Self-Activation or Keying",
        "Physical Resistance/Sticking", "Sticking", "Device, or device fragments remain in patient",
        "Patient-Device Incompatibility", "Patient Device Interaction Problem", "Migration or Expulsion of Device",
        "Positioning Problem", "Insufficient Adhesion"],
    "Alarms": [
        "Device Alarm System", "No Audible Alarm", "Defective Alarm", "Low Audible Alarm", "Alarm Not Visible",
        "Delayed Alarm", "False Alarm", "Alarm, Audible"],
    "App, software, display": [
        "Unintended Application Program Shut Down", "Device Displays Incorrect Message",
        "Display or Visual Feedback Problem", "Operating System Version or Upgrade Problem",
        "Application Program Freezes or Fails to Launch", "Computer Software Problem", "Application Program Problem",
        "No Display/Image", "Poor Quality Image", "Image Display Error/Artifact", "Data Problem",
        "Date/Time-Related Software Problem",
        "Application Interface Becomes Non-Functional Or Program Exits Abnormally", "Application Security Problem",
        "Software Installation Problem", "Problem with Software Installation"],
    "Hardware, battery, packaging": [
        "Break", "Battery Problem", "Component Missing", "Low Battery", "Overheating of Device", "Crack",
        "Structural Problem", "Bent", "Moisture Damage", "Material Twisted/Bent", "Premature Discharge of Battery",
        "Fracture", "Unintended Electrical Shock", "Material Integrity Problem", "Material Separation",
        "Moisture or Humidity Problem", "Power Problem", "Mechanical Problem", "Defective Component",
        "Electrical /Electronic Property Problem", "Delivered as Unsterile Product", "Packaging Problem",
        "Fluid/Blood Leak", "Charging Problem", "Smoking", "Sparking", "Fire", "Burst Container or Vessel"],
}
FAM_ORDER = list(PROBLEM_FAMILY) + ["Unclear / other"]
P2F = {p: f for f, ps in PROBLEM_FAMILY.items() for p in ps}
ACCURACY_TERMS = ["Incorrect, Inadequate or Imprecise Result or Readings", "Low Readings", "High Readings", "Imprecision"]


def fam(p):
    return P2F.get(p, "Unclear / other")


# ---------------------------------------------------------------- load
code_tot = pd.read_csv(CNT / "code_totals.csv")
brand = pd.read_csv(CNT / "brand_name.csv")
probs = pd.read_csv(CNT / "product_problems.csv")
month_rec = pd.read_csv(CNT / "reports_by_month_received.csv")
month_evt = pd.read_csv(CNT / "reports_by_month_event_date.csv")
age_c = pd.read_csv(CNT / "patient_age.csv", keep_default_na=False)
sex_c = pd.read_csv(CNT / "patient_sex.csv", keep_default_na=False)
outc_c = pd.read_csv(CNT / "patient_outcome.csv", keep_default_na=False)
recalls = pd.read_csv(RES / "recalls_cgm.csv")
harm = pd.read_csv(RES / "recall_harm_manual.csv")

S = pd.read_csv(SERIOUS, low_memory=False)
S["date_received"] = pd.to_datetime(S["date_received"].astype(str), format="%Y%m%d", errors="coerce")
S["date_of_event"] = pd.to_datetime(S["date_of_event"].astype("Int64").astype(str), format="%Y%m%d", errors="coerce")
mf = [classify(b, c, m) for b, c, m in zip(S.brand_name, S.product_code, S.manufacturer)]
S["mfr"] = [x[0] for x in mf]
S["family"] = [x[1] for x in mf]
S["problem_list"] = S["product_problems"].fillna("").apply(lambda s: [p.strip() for p in s.split(";") if p.strip()])

TOTAL_REPORTS = 3_382_071
TOTAL_DEATHS = int(code_tot.deaths.sum())
TOTAL_INJ = int(code_tot.injuries.sum())
N_SER = len(S)
md = []  # markdown lines

# ================================================================ a. scope
scope = pd.DataFrame([
    ("Sources", "FDA MAUDE (device problem reports) via openFDA; FDA recall database"),
    ("CGM product codes", f"{len(code_tot)} codes: " + ", ".join(code_tot.product_code)),
    ("Reports received", f"{code_tot.first_received.min()} to {code_tot.last_received.max()}"),
    ("All CGM reports", f"{TOTAL_REPORTS:,}"),
    ("Death + injury reports downloaded", f"{N_SER:,} unique"),
    ("Recall events", f"{recalls.recall_event_id.nunique()} ({len(recalls)} recall records)"),
    ("Pull date", PULL_DATE),
    ("FDA data last updated", FDA_DATA_DATE),
], columns=["Item", "Value"])
wtab(scope, "a_scope.csv")
md += ["# CGM problem reports and recalls: results for the report",
       f"Made by `fda-maude/scripts/report_results.py` on {PULL_DATE}. Tables: `tables/`. Figures: `figures/`.",
       "- **CGM** = continuous glucose monitor (a sensor worn on the body that reads glucose every few minutes).",
       "- **MAUDE** = FDA database of reports about medical device problems. Report counts are NOT failure rates.",
       "- **Serious reports** = reports filed as a death or an injury.", "",
       "## a. Scope",
       f"- Sources: FDA MAUDE (via openFDA) and FDA recall database. {len(code_tot)} CGM product codes (FDA device-type labels).",
       f"- Reports received {code_tot.first_received.min()} to {code_tot.last_received.max()}. Pulled {PULL_DATE}. FDA data last updated {FDA_DATA_DATE}.",
       f"- All CGM reports: {TOTAL_REPORTS:,}",
       f"- Death + injury reports downloaded: {N_SER:,}",
       "- Not used here: the malfunction sample and the full pull (both finished; counts already cover all reports). Full scope: `tables/a_scope.csv`.", ""]

# ================================================================ b. manufacturer
brand["mfr"], brand["family"] = zip(*[classify(b, c) for b, c in zip(brand.brand_name, brand.product_code)])
all_fam = brand.groupby("family").reports.sum()
ser_fam = S.groupby(["family", "event_type"]).size().unstack(fill_value=0)
fam_tab = pd.DataFrame({"Product family": FAMILY_ORDER})
fam_tab["Manufacturer"] = fam_tab["Product family"].map(lambda f: next((m for m in MFR_ORDER if f.startswith(m.split(" ")[0])), "Other / unknown"))
fam_tab.loc[fam_tab["Product family"].str.startswith("Senseonics"), "Manufacturer"] = "Senseonics"
fam_tab["All reports"] = fam_tab["Product family"].map(all_fam).fillna(0).astype(int)
fam_tab["Deaths"] = fam_tab["Product family"].map(ser_fam.get("Death", pd.Series(dtype=int))).fillna(0).astype(int)
fam_tab["Injuries"] = fam_tab["Product family"].map(ser_fam.get("Injury", pd.Series(dtype=int))).fillna(0).astype(int)
fam_tab["Malfunction (and other)"] = (fam_tab["All reports"] - fam_tab["Deaths"] - fam_tab["Injuries"]).clip(lower=0)
fam_tab["Injuries per 100 reports"] = (100 * fam_tab["Injuries"] / fam_tab["All reports"].replace(0, np.nan)).round(1)
# 'other' rows pick up serious reports matched only by the manufacturer field (not possible for counts), so
# their ratio is not comparable; tiny families are too small to compare.
unreliable = fam_tab["Product family"].str.contains("other|Other") | (fam_tab["All reports"] < 1000)
fam_tab.loc[unreliable, "Injuries per 100 reports"] = np.nan
fam_tab = fam_tab[["Manufacturer", "Product family", "All reports", "Deaths", "Injuries", "Malfunction (and other)", "Injuries per 100 reports"]]
wtab(fam_tab, "b_reports_by_product_family.csv")
mfr_tab = fam_tab.groupby("Manufacturer", sort=False)[["All reports", "Deaths", "Injuries", "Malfunction (and other)"]].sum().reset_index()
mfr_tab["Share of all reports %"] = (100 * mfr_tab["All reports"] / mfr_tab["All reports"].sum()).round(1)
mfr_tab["Share of injury reports %"] = (100 * mfr_tab["Injuries"] / mfr_tab["Injuries"].sum()).round(1)
wtab(mfr_tab, "b_reports_by_manufacturer.csv")
code_tab = code_tot[["product_code", "reports", "deaths", "injuries", "malfunctions", "first_received", "last_received"]]
wtab(code_tab, "b_reports_by_product_code.csv")
md += ["## b. Reports by manufacturer",
       "We grouped 2,600+ messy brand spellings by keyword. Totals: FDA brand counts. Deaths and injuries: downloaded serious reports. All families: `tables/b_reports_by_product_family.csv`.", "",
       md_table(mfr_tab), "", md_table(fam_tab[fam_tab["All reports"] >= 100000].drop(columns=["Manufacturer"])), "",
       "What it means:",
       f"- Dexcom has the most reports overall. Abbott has the most injury reports.",
       "- Injuries per 100 reports (share of a product's reports that are injuries, NOT a rate per sensor): Abbott Libre about 7 to 14; Dexcom G5/G6/G7 about 1 to 2.",
       "- guess: part of this gap is how each company files reports (what it labels 'injury'), not only the sensors.", ""]

# ================================================================ c. per year
mr = month_rec.copy()
mr["year"] = mr.month.str[:4].astype(int)
yr = mr.pivot_table(index="year", columns="event_type", values="reports", aggfunc="sum", fill_value=0)
yr = yr.reindex(columns=["All", "Death", "Injury", "Malfunction"], fill_value=0)
yr_tab = yr.reset_index().rename(columns={"year": "Year received", "All": "All reports", "Death": "Deaths",
                                          "Injury": "Injuries", "Malfunction": "Malfunctions"})
early = yr_tab[yr_tab["Year received"] < 2021].drop(columns="Year received").sum()
yr_md = pd.concat([pd.DataFrame([{"Year received": "before 2021", **early.to_dict()}]),
                   yr_tab[yr_tab["Year received"] >= 2021].astype({"Year received": str})], ignore_index=True)
yr_md.loc[yr_md["Year received"] == "2026", "Year received"] = "2026 (Jan-Sep)"
wtab(yr_tab, "c_reports_per_year.csv")
ser_year = S.groupby([S.date_received.dt.year, "mfr"]).size().unstack(fill_value=0).reindex(columns=MFR_ORDER, fill_value=0)
ser_year.index.name = "Year received"
wtab(ser_year.reset_index(), "c_serious_reports_per_year_by_manufacturer.csv")

fig, axes = plt.subplots(2, 1, figsize=(8, 7.2), sharex=True, gridspec_kw={"hspace": 0.35})
years = list(range(2012, 2027))
a = yr_tab.set_index("Year received").reindex(years, fill_value=0)
ax = axes[0]
bars = ax.bar(years, a["All reports"] / 1000, color=BLUE, width=0.75)
bars[-1].set_alpha(0.55)
for x, v in zip(years, a["All reports"] / 1000):
    if v >= 100:
        ax.text(x, v + 12, f"{v:,.0f}k", ha="center", va="bottom", fontsize=8, color=INK2)
ax.set_title("All CGM problem reports per year", loc="left")
ax.set_ylabel("Reports (thousands)")
ax.grid(axis="x", visible=False)
ax.set_ylim(0, a["All reports"].max() / 1000 * 1.15)
ax = axes[1]
bottom = np.zeros(len(years))
sy = ser_year.reindex(years, fill_value=0)
for m in MFR_ORDER:
    v = sy[m].values / 1000
    ax.bar(years, v, bottom=bottom, color=MFR_COLOR[m], width=0.75, edgecolor="white", linewidth=0.8, label=m)
    bottom += v
ax.set_title("Death + injury reports per year, by manufacturer", loc="left")
ax.set_ylabel("Reports (thousands)")
ax.grid(axis="x", visible=False)
ax.set_xlabel("Year FDA received the report  (2026 = January to September only)")
ax.set_xticks(years)
ax.set_xticklabels([str(y) for y in years], rotation=0, fontsize=8.5)
ax.legend(ncol=5, loc="upper left", fontsize=8.5, bbox_to_anchor=(0, 1.0))
ax.set_ylim(0, bottom.max() * 1.25)
save(fig, "fig1_reports_per_year.png")

md += ["## c. Reports per year",
       "By the year FDA received the report (not the year the problem happened). Every year: `tables/c_reports_per_year.csv`.", "",
       md_table(yr_md.drop(columns=["Malfunctions"])), "", "![Reports per year](figures/fig1_reports_per_year.png)", "",
       "What it means:",
       "- From 2018 on, Abbott products have the most death + injury reports every year.",
       f"- Dexcom death + injury reports grew fast: {int(ser_year.loc[2022, 'Dexcom']):,} in 2022 to {int(ser_year.loc[2025, 'Dexcom']):,} in 2025.", ""]

# ================================================================ d. problem types
pr = probs.copy()
pr["Family"] = pr.product_problem.map(fam)
overall = pr.groupby("product_problem").reports.sum().sort_values(ascending=False).reset_index()
overall["Family"] = overall.product_problem.map(fam)
overall["% of all reports (mentions)"] = (100 * overall.reports / TOTAL_REPORTS).round(1)
overall.columns = ["Problem (FDA term)", "Reports", "Family", "% of all reports"]
wtab(overall, "d_problem_terms_all_reports.csv")
mapping = overall[["Family", "Problem (FDA term)", "Reports"]].sort_values(["Family", "Reports"], ascending=[True, False])
wtab(mapping, "d_problem_family_mapping.csv")

fam_all = pr.groupby("Family").reports.sum().reindex(FAM_ORDER, fill_value=0)
fam_all_tab = pd.DataFrame({"Problem family": FAM_ORDER, "Problem mentions": fam_all.values.astype(int)})
fam_all_tab["Mentions per 100 reports"] = (100 * fam_all_tab["Problem mentions"] / TOTAL_REPORTS).round(1)
wtab(fam_all_tab, "d_problem_families_all_reports.csv")

# by product code (manufacturer not available in counts problem table)
main5 = ["QBJ", "PQF", "MDS", "QLG", "PZE"]
pc = pr.assign(code=np.where(pr.product_code.isin(main5), pr.product_code, "8 small codes"))
fam_code = pc.pivot_table(index="Family", columns="code", values="reports", aggfunc="sum", fill_value=0).reindex(FAM_ORDER, fill_value=0)
rep_code = code_tot.assign(code=np.where(code_tot.product_code.isin(main5), code_tot.product_code, "8 small codes")).groupby("code").reports.sum()
fam_code_pct = (100 * fam_code / rep_code).round(1)[main5 + ["8 small codes"]]
fam_code_pct.columns = [f"{c} ({MAIN})" for c, MAIN in zip(fam_code_pct.columns,
                        ["Dexcom G6/G7, Libre 2 Plus/3", "Dexcom G5, Medtronic", "older Dexcom/Medtronic",
                         "Libre 2/3", "Libre 14-day", "Eversense, Stelo, etc."])]
wtab(fam_code_pct.reset_index().rename(columns={"Family": "Problem family"}), "d_problem_families_by_product_code_per100.csv")
top_code = (pc.sort_values("reports", ascending=False).groupby("code").head(5)
            .assign(pct=lambda d: (100 * d.reports / d.code.map(rep_code)).round(1))
            [["code", "product_problem", "reports", "pct"]])
top_code.columns = ["Product code", "Problem (FDA term)", "Reports", "% of code's reports"]
wtab(top_code, "d_top5_problems_by_product_code.csv")

# serious: exact share of reports with >=1 term in a family, by manufacturer
S["families"] = S.problem_list.apply(lambda ps: sorted({fam(p) for p in ps}) if ps else ["Unclear / other"])
big3 = ["Dexcom", "Abbott", "Medtronic"]
rows = []
for f in FAM_ORDER:
    has = S.families.apply(lambda fs: f in fs)
    r = {"Problem family": f, "All serious %": round(100 * has.mean(), 1)}
    for m in big3 + ["Senseonics"]:
        sel = S.mfr == m
        r[f"{m} %"] = round(100 * has[sel].mean(), 1)
    rows.append(r)
fam_ser = pd.DataFrame(rows)
wtab(fam_ser, "d_problem_families_serious_by_manufacturer_pct.csv")
top_mfr = (S[["mfr", "problem_list"]].explode("problem_list").dropna().groupby(["mfr", "problem_list"]).size()
           .rename("Reports").reset_index().sort_values("Reports", ascending=False).groupby("mfr").head(5))
top_mfr["% of manufacturer's serious reports"] = (100 * top_mfr.Reports / top_mfr.mfr.map(S.mfr.value_counts())).round(1)
top_mfr = top_mfr.rename(columns={"mfr": "Manufacturer", "problem_list": "Problem (FDA term)"})
top_mfr["_o"] = top_mfr.Manufacturer.map({m: i for i, m in enumerate(MFR_ORDER)})
top_mfr = top_mfr.sort_values(["_o", "Reports"], ascending=[True, False]).drop(columns="_o")
wtab(top_mfr, "d_top5_problems_serious_by_manufacturer.csv")

acc_all = int(pr[pr.product_problem.isin(ACCURACY_TERMS)].reports.sum())

# figure 2
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1, 1.25], "wspace": 0.08})
ax = axes[0]
order = FAM_ORDER[::-1]
vals = fam_all.reindex(order) / TOTAL_REPORTS * 100
colors = [RED if f.startswith("Wrong") else BLUE for f in order]
ax.barh(order, vals, color=colors, height=0.65)
for y, v in enumerate(vals):
    ax.text(v + 0.8, y, f"{v:.0f}", va="center", fontsize=8.5, color=INK2)
ax.set_title("A. All reports (3.38 million)", loc="left", fontsize=11)
ax.set_xlabel("Problem mentions per 100 reports")
ax.grid(axis="y", visible=False)
ax.set_xlim(0, vals.max() * 1.18)
ax = axes[1]
h = 0.26
fs = fam_ser.set_index("Problem family").reindex(order)
yy = np.arange(len(order))
for i, m in enumerate(big3):
    ax.barh(yy + (1 - i) * h, fs[f"{m} %"], height=h, color=MFR_COLOR[m], label=m, edgecolor="white", linewidth=0.6)
ax.set_yticks(yy)
ax.set_yticklabels([])
ax.set_title("B. Death + injury reports, by manufacturer", loc="left", fontsize=11)
ax.set_xlabel("% of serious reports with at least one problem in the family")
ax.grid(axis="y", visible=False)
ax.legend(loc="center right", fontsize=9)
fig.suptitle("What goes wrong: FDA problem terms grouped into plain families", x=0.02, ha="left", fontsize=12.5, fontweight="bold", y=1.02)
save(fig, "fig2_problem_families.png")

short_terms = {f: ", ".join(mapping[mapping.Family == f].sort_values("Reports", ascending=False)["Problem (FDA term)"].head(3)
                             .str.replace("Incorrect, Inadequate or Imprecise Result or Readings", "Incorrect...Readings", regex=False))
               for f in FAM_ORDER[:-1]}
short_terms["Unclear / other"] = "Device Operates Differently Than Expected, Use of Device Problem, Adverse Event Without..."
comb = pd.DataFrame({"Problem family": FAM_ORDER, "Main FDA terms": [short_terms[f] for f in FAM_ORDER]})
comb["All reports: mentions per 100"] = fam_all_tab["Mentions per 100 reports"].values
for c in ["All serious %", "Dexcom %", "Abbott %", "Medtronic %"]:
    comb[f"Serious: {c}"] = fam_ser[c].values
wtab(comb, "d_problem_families_summary.csv")

md += ["## d. Problem types",
       "Each report lists one or more FDA 'problem terms' (fixed labels). Top 5 terms over all reports:", "",
       md_table(overall.head(5)), "",
       "We grouped the 391 terms into 8 plain families (full mapping: `tables/d_problem_family_mapping.csv`).",
       "All reports: one report can list several terms, so 'mentions per 100' is an upper limit on the share of reports. Serious reports: exact % of reports.", "",
       md_table(comb), "",
       "![Problem families](figures/fig2_problem_families.png)", "",
       "What it means:",
       f"- All reports: signal loss is the biggest family, wrong readings second. Death + injury reports: wrong readings is the top family ({fam_ser.iloc[0]['All serious %']}%).",
       "- Abbott serious reports often pair 'Unable to Obtain Readings' with 'Device Displays Incorrect Message' (sensor error message). So 'App, software, display' is high for Abbott.",
       "- Problem counts per manufacturer for ALL reports are not possible: FDA counts split only by product code, and codes mix brands. Per-code tables: `tables/d_top5_problems_by_product_code.csv`.", ""]

# ================================================================ e. serious reports
def norm_outcome(o):
    o = o.strip()
    return {"O": "Other", "H": "Hospitalization", "R": "Required Intervention", "L": "Life Threatening",
            "S": "Disability", "D": "Death", "C": "Congenital Anomaly"}.get(o, o)

S["outcomes"] = S.patient_outcome.fillna("").apply(lambda s: sorted({norm_outcome(o) for o in s.split(";") if o.strip()}))
oc = S[["mfr", "outcomes"]].explode("outcomes")
oc["outcomes"] = oc.outcomes.fillna("(blank)")
outc_tab = oc.groupby(["outcomes", "mfr"]).size().unstack(fill_value=0).reindex(columns=MFR_ORDER, fill_value=0)
outc_tab["All serious"] = S.outcomes.explode().fillna("(blank)").value_counts().reindex(outc_tab.index).fillna(0).astype(int)
outc_tab = outc_tab.sort_values("All serious", ascending=False)
outc_tab["% of serious reports"] = (100 * outc_tab["All serious"] / N_SER).round(1)
outc_tab = outc_tab.reset_index().rename(columns={"outcomes": "Patient outcome"})
outc_tab = outc_tab[["Patient outcome", "All serious", "% of serious reports"] + MFR_ORDER]
wtab(outc_tab, "e_patient_outcomes_serious_by_manufacturer.csv")
top_ser_prob = (S.problem_list.explode().dropna().value_counts().head(10).rename_axis("Problem (FDA term)").reset_index(name="Reports"))
top_ser_prob["% of serious reports"] = (100 * top_ser_prob.Reports / N_SER).round(1)
top_ser_prob["Family"] = top_ser_prob["Problem (FDA term)"].map(fam)
wtab(top_ser_prob, "e_top_problems_serious.csv")
pp = S.patient_problems.fillna("").apply(lambda s: sorted({p.strip() for p in s.split(";") if p.strip()}))
top_pat = pp.explode().dropna().value_counts().head(10).rename_axis("Patient problem (FDA term)").reset_index(name="Reports")
top_pat["% of serious reports"] = (100 * top_pat.Reports / N_SER).round(1)
wtab(top_pat, "e_top_patient_problems_serious.csv")
ser_by_mfr = S.groupby(["mfr", "event_type"]).size().unstack(fill_value=0).reindex(MFR_ORDER, fill_value=0).reset_index()
ser_by_mfr.columns.name = None
ser_by_mfr = ser_by_mfr.rename(columns={"mfr": "Manufacturer"})
wtab(ser_by_mfr, "e_serious_by_manufacturer.csv")
md += ["## e. Death + injury reports",
       f"{N_SER:,} reports ({int((S.event_type == 'Death').sum()):,} deaths, {int((S.event_type == 'Injury').sum()):,} injuries). Patient outcomes (a report can have several); manufacturer columns = number of reports:", "",
       md_table(outc_tab.drop(columns=["Other / unknown"])[outc_tab["Patient outcome"].isin(["Required Intervention", "Other", "Hospitalization", "Life Threatening", "Death"])]), "",
       "What it means:",
       "- Most serious reports say the person 'required intervention' (needed treatment to prevent harm).",
       "- Companies fill this field differently. Abbott mostly uses 'Required Intervention'. Dexcom mostly uses 'Other'. Compare manufacturers with care.",
       "- A death report does not mean the device caused the death. It means someone reported a death while using it.",
       "- Top patient problem terms (% of serious reports; full list in `tables/e_top_patient_problems_serious.csv`):",
       *[f"  - {r[0]}: {r[2]}%" for r in top_pat.head(3).itertuples(index=False)],
       ""]

# ================================================================ f. Libre 3 timeline
L3 = S[S.family == "Abbott Libre 3 / 3 Plus"]
start, end = pd.Timestamp("2022-01-01"), pd.Timestamp("2026-09-30")
rec_m = L3.date_received.dt.to_period("M").value_counts().sort_index()
evt_m = L3.date_of_event.dt.to_period("M").value_counts().sort_index()
idx = pd.period_range("2022-01", "2026-09", freq="M")
l3 = pd.DataFrame({"Month": idx.astype(str), "By date received": rec_m.reindex(idx, fill_value=0).values,
                   "By date of event": evt_m.reindex(idx, fill_value=0).values})
wtab(l3, "f_libre3_serious_reports_per_month.csv")

me = month_evt.copy()
me = me[me.month >= "2023-01"]
mrr = month_rec[(month_rec.event_type == "All") & (month_rec.month >= "2023-01")]
q = []
for c in ["QBJ", "QLG"]:
    a_ = mrr[mrr.product_code == c].set_index("month").reports.rename(f"{c} received")
    b_ = me[me.product_code == c].set_index("month").reports.rename(f"{c} event date")
    q += [a_, b_]
qtab = pd.concat(q, axis=1).fillna(0).astype(int).sort_index().reset_index().rename(columns={"index": "Month", "month": "Month"})
wtab(qtab, "f_QBJ_QLG_all_reports_per_month.csv")

low = S[S.problem_list.apply(lambda ps: "Low Readings" in ps)]
low_m = low.groupby([low.date_received.dt.to_period("M"), "mfr"]).size().unstack(fill_value=0)
idx2 = pd.period_range("2020-01", "2026-09", freq="M")
low_m = low_m.reindex(idx2, fill_value=0).reindex(columns=MFR_ORDER, fill_value=0)
low_tab = low_m.copy()
low_tab.index = low_tab.index.astype(str)
low_tab.index.name = "Month received"
wtab(low_tab.reset_index(), "f_low_readings_serious_per_month_by_manufacturer.csv")

RECALL_MARKS = [(pd.Timestamp("2024-07-24"), "Jul 2024 recall\n(Libre 3 reads too HIGH)"),
                (pd.Timestamp("2025-11-24"), "Nov 24 2025 recall starts\n(Libre 3 reads too LOW)"),
                (pd.Timestamp("2026-01-14"), "Jan 14 2026\nFDA posts recall")]

fig, ax = plt.subplots(figsize=(10, 4.8))
x = idx.to_timestamp() + pd.Timedelta(days=14)
ax.plot(x, l3["By date received"], color=BLUE, lw=2, label="By date FDA received the report")
ax.plot(x, l3["By date of event"], color=ORANGE, lw=2, label="By date the problem happened")
ymax = max(l3["By date received"].max(), l3["By date of event"].max())
for i, (d, t) in enumerate(RECALL_MARKS):
    ax.axvline(d, color=INK2, lw=1, ls="--")
    right = i == 2
    ax.text(d + pd.Timedelta(days=8 if right else -8), ymax * 1.12, t,
            ha="left" if right else "right", va="top", fontsize=8, color=INK2)
ax.text(x[-1] + pd.Timedelta(days=10), l3["By date received"].iloc[-1], "received", color=BLUE, fontsize=8.5, va="center")
ax.text(x[-1] + pd.Timedelta(days=10), l3["By date of event"].iloc[-1], "event", color=ORANGE, fontsize=8.5, va="center")
ax.set_ylim(0, ymax * 1.15)
ax.set_title("FreeStyle Libre 3 / 3 Plus: death + injury reports per month", loc="left")
ax.set_ylabel("Reports per month")
ax.set_xlabel("Month")
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.legend(loc="upper left", fontsize=9)
ax.text(0, -0.2, "Note: September 2026 is incomplete. Recent months of 'date the problem happened' fill in as late reports arrive.",
        transform=ax.transAxes, fontsize=8, color=MUTED)
save(fig, "fig3_libre3_timeline.png")

fig, ax = plt.subplots(figsize=(10, 4.4))
x2 = idx2.to_timestamp() + pd.Timedelta(days=14)
for m in ["Dexcom", "Abbott", "Medtronic"]:
    ax.plot(x2, low_m[m], color=MFR_COLOR[m], lw=2, label=m)
    ax.text(x2[-1] + pd.Timedelta(days=12), low_m[m].iloc[-1], m, color=MFR_COLOR[m], fontsize=9, va="center")
ylm = low_m[["Dexcom", "Abbott", "Medtronic"]].values.max()
for d, t in RECALL_MARKS[1:2]:
    ax.axvline(d, color=INK2, lw=1, ls="--")
    ax.text(d - pd.Timedelta(days=10), ylm * 1.02, t, ha="right", va="top", fontsize=8, color=INK2)
ax.set_title("Death + injury reports with the problem term 'Low Readings', per month", loc="left")
ax.set_ylabel("Reports per month")
ax.set_xlabel("Month FDA received the report")
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.legend(loc="upper left", fontsize=9, frameon=True, facecolor="white", edgecolor="#cccccc", framealpha=1)
save(fig, "fig4_low_readings_monthly.png")

l3_tot = len(L3)
l3_recent = L3[L3.date_received >= "2025-11-24"]
l3_low = L3.problem_list.apply(lambda ps: "Low Readings" in ps)
peak = l3.loc[l3["By date received"].idxmax()]
peak_e = l3.loc[l3["By date of event"].idxmax()]
l3_low_recent = l3_recent[l3_recent.problem_list.apply(lambda ps: "Low Readings" in ps)]


def death_inj(df, label):
    """Count Death / Injury in a group; print a check that they add up to the group total."""
    d, i = int((df.event_type == "Death").sum()), int((df.event_type == "Injury").sum())
    other = df.event_type[~df.event_type.isin(["Death", "Injury"])].value_counts(dropna=False)
    msg = "OK" if d + i == len(df) else f"MISMATCH, other event_type values: {other.to_dict()}"
    print(f"check {label}: deaths {d:,} + injuries {i:,} = {d + i:,} vs total {len(df):,} -> {msg}")
    return d, i


d_all, i_all = death_inj(L3, "all time")
d_rec, i_rec = death_inj(l3_recent, "received on/after Nov 24 2025")
d_low, i_low = death_inj(L3[l3_low], "Low Readings (all time)")
d_lr, i_lr = death_inj(l3_low_recent, "received on/after Nov 24 2025 AND Low Readings")
lib_tab = pd.DataFrame([
    ("Libre 3 / 3 Plus serious reports (all time)", l3_tot),
    ("    deaths (all time)", d_all),
    ("    injuries (all time)", i_all),
    ("  of these, received on or after Nov 24 2025", len(l3_recent)),
    ("    deaths (received on or after Nov 24 2025)", d_rec),
    ("    injuries (received on or after Nov 24 2025)", i_rec),
    ("  of these, with problem term 'Low Readings'", int(l3_low.sum())),
    ("    deaths ('Low Readings', all time)", d_low),
    ("    injuries ('Low Readings', all time)", i_low),
    ("  received on or after Nov 24 2025 AND 'Low Readings'", len(l3_low_recent)),
    ("    deaths (on or after Nov 24 2025 AND 'Low Readings')", d_lr),
    ("    injuries (on or after Nov 24 2025 AND 'Low Readings')", i_lr),
    ("Peak month by date received", f"{peak['Month']} ({peak['By date received']:,})"),
    ("Peak month by date of event", f"{peak_e['Month']} ({peak_e['By date of event']:,})"),
], columns=["Item", "Value"])
wtab(lib_tab, "f_libre3_summary.csv")
if ONLY_F:
    print(lib_tab.to_string(index=False))
    print("--only-f-summary: wrote", TAB / "f_libre3_summary.csv", "and stopped.")
    sys.exit(0)
md += ["## f. Libre 3 and the recall timeline",
       "Libre 3 / 3 Plus death + injury reports (found by brand name) per month, by date FDA received them and by date the problem happened.", "",
       md_table(lib_tab), "",
       f"- Deaths + injuries add up to the row above each pair. The {int(l3_low.sum()):,} 'Low Readings' row counts ALL time, "
       f"not only after Nov 24 2025. The after-Nov-24 'Low Readings' count is the {len(l3_low_recent):,} row.", "",
       "![Libre 3 timeline](figures/fig3_libre3_timeline.png)", "",
       "![Low Readings per month](figures/fig4_low_readings_monthly.png)", "",
       "What it means:",
       "- Look at both lines. A jump 'by date received' with no jump 'by date of event' means late reports, not new problems.",
       "- Libre 3 reports peak around both Class I recalls (Jul 2024, Nov 2025), by both dates. guess: recall news also makes people report more.",
       "- Dexcom almost never used the term 'Low Readings' before mid-2025, then about 100-200 per month. guess: a change in how Dexcom codes reports, not a sudden new fault.",
       "- Not possible from our counts (no API calls made): monthly ALL reports for Libre 3 alone (FDA monthly counts are by product code, which mixes brands), and monthly 'Low Readings' for ALL reports. Both figures use serious reports only. Monthly ALL reports for codes QBJ and QLG: `tables/f_QBJ_QLG_all_reports_per_month.csv`.", ""]

# ================================================================ g. recalls
PLAIN = {  # short plain-words reason + product, written by hand from the FDA reason text
    50202: ("FreeStyle Navigator receiver", "Set to wrong glucose units (mmol/L instead of mg/dL)"),
    52635: ("FreeStyle Navigator system", "Housing may crack and let in moisture; possible wrong readings"),
    68888: ("Guardian REAL-Time monitor", "Manufacturing issue; may not be water resistant"),
    71816: ("Guardian REAL-Time system", "Finnish translation error in low-glucose alert setting"),
    73412: ("Dexcom G4 PLATINUM receiver", "Alarm may not sound"),
    74955: ("CareLink iPro software", "Time stamp error"),
    81656: ("Guardian Connect app (iOS)", "Phone may close the app silently; alerts missed"),
    85091: ("Guardian Connect app + transmitter", "iOS 12 drains transmitter battery early"),
    84290: ("Dexcom receiver", "Software: receiver stuck on start screen; no readings"),
    83896: ("Eversense sensor", "Sensors stopped working early"),
    84436: ("Dexcom G6 iOS app", "Low alarm may not sound with Alert Schedule"),
    84891: ("Dexcom G4/G5/G6 systems", "Drug hydroxyurea makes readings falsely high"),
    86081: ("Guardian Connect app (iOS)", "App stopped uploading data"),
    87476: ("Medtronic Guardian sensors", "Drug hydroxyurea makes readings falsely high"),
    87787: ("FreeStyle Libre kits (Cardinal Health)", "Exposed to cold in shipping; possible wrong readings"),
    91260: ("Guardian 4 apps", "App logs out; care partners miss alerts"),
    93393: ("FreeStyle Libre 3 app (Android 13)", "Long signal loss; alarms missed"),
    91756: ("FreeStyle Libre readers", "Reader battery may swell, overheat, or catch fire"),
    92708: ("FreeStyle Libre 2 readers", "'Incompatible sensor' message blocks new sensor"),
    93675: ("Medtronic Guardian 4 sensor", "Sensing layer thickness out of spec; wrong or no readings"),
    95047: ("FreeStyle Libre 3 sensors", "Readings falsely HIGH"),
    96091: ("Dexcom G6 receiver", "High/low alarms may not sound"),
    96684: ("Dexcom G7 iOS app", "App shows an old (stale) reading; alerts missed"),
    96745: ("Medtronic Simplera sensor", "Cap label may not stick; sterility and infection risk"),
    96743: ("Dexcom G6/ONE receivers", "Speaker fault; audible alarms missed"),
    97262: ("Dexcom G7 / ONE+ apps", "App software fault; alerts or readings missed"),
    97607: ("Dexcom G6 Android app", "App closes unexpectedly; no readings or alarms"),
    97873: ("Medtronic CareLink Clinic software", "Wrong data on 24-hour glucose graph"),
    97896: ("Unapproved CGM (Get Tested Intl.)", "Sold without FDA clearance"),
    98049: ("FreeStyle Libre 3 / 3 Plus sensors", "Readings falsely LOW (carbon build-up in sensor)"),
    98639: ("Dexcom G7 / ONE+ iOS apps", "Delayed readings; app may show old values"),
    98968: ("Dexcom G7 sensors (stolen scrap)", "Stolen scrap sensors resold; may be unsterile or inaccurate"),
}


RTYPE = {}  # plain recall type, by hand from the reason text
for _i in (52635, 84891, 87476, 87787, 93675, 95047, 98049, 50202):
    RTYPE[_i] = "Wrong readings"
for _i in (73412, 84436, 96091, 96743):
    RTYPE[_i] = "Missed alarms (receiver/app)"
for _i in (71816, 74955, 81656, 85091, 84290, 86081, 91260, 93393, 92708, 96684, 97262, 97607, 97873, 98639):
    RTYPE[_i] = "Software / app (no or late readings, data)"
for _i in (68888, 91756, 83896):
    RTYPE[_i] = "Hardware / sensor stops"
for _i in (96745, 97896, 98968):
    RTYPE[_i] = "Sterility / unapproved / stolen"


def qnum(s):
    mm = re.search(r"\d[\d,]*", str(s))
    return int(mm.group(0).replace(",", "")) if mm else np.nan


def short_firm(f):
    f = str(f).upper()
    for k, v in [("ABBOTT", "Abbott"), ("DEXCOM", "Dexcom"), ("MEDTRONIC", "Medtronic"), ("SENSEONICS", "Senseonics"),
                 ("CARDINAL", "Cardinal Health"), ("GET TESTED", "Get Tested Intl.")]:
        if k in f:
            return v
    return f.title()


recalls["q"] = recalls.quantity_in_commerce.apply(qnum)
ev = recalls.groupby("recall_event_id").agg(
    initiated=("date_initiated", "min"), posted=("date_posted", "min"), cls=("recall_class", "first"),
    firm=("firm", "first"), records=("recall_number", "size"), qty=("q", "sum"), status=("recall_status", "first")).reset_index()
ev["cls"] = ev.cls.fillna("No class (old)")
ev["Firm"] = ev.firm.apply(short_firm)
ev["Product"] = ev.recall_event_id.map(lambda i: PLAIN.get(i, ("?", "?"))[0])
ev["Reason (plain words)"] = ev.recall_event_id.map(lambda i: PLAIN.get(i, ("?", "?"))[1])
ev["Type"] = ev.recall_event_id.map(RTYPE).fillna("?")
ev = ev.sort_values("initiated")
ev["Quantity (approx.)"] = ev.qty.apply(lambda v: "" if pd.isna(v) or v == 0 else f"{int(v):,}")
rec_tab = ev[["initiated", "Firm", "Product", "cls", "Type", "Reason (plain words)", "Quantity (approx.)", "records"]].rename(
    columns={"initiated": "Date started", "cls": "Class", "records": "FDA records"})
wtab(rec_tab, "g_recall_events.csv")
by_class = ev.cls.value_counts().rename_axis("Class").reset_index(name="Recall events")
wtab(by_class, "g_recalls_by_class.csv")
by_firm = ev.pivot_table(index="Firm", columns="cls", values="recall_event_id", aggfunc="count", fill_value=0)
by_firm["Total"] = by_firm.sum(axis=1)
by_firm = by_firm.sort_values("Total", ascending=False).reset_index()
by_firm.columns.name = None
wtab(by_firm, "g_recalls_by_firm.csv")
by_type = ev.pivot_table(index="Type", columns="cls", values="recall_event_id", aggfunc="count", fill_value=0)
by_type["Total"] = by_type.sum(axis=1)
by_type = by_type.sort_values("Total", ascending=False).reset_index()
by_type.columns.name = None
wtab(by_type, "g_recalls_by_type.csv")
n_c1 = int((ev.cls == "Class I").sum())
n_c1_recent = int(((ev.cls == "Class I") & (ev.initiated >= "2023-01-01")).sum())

fig, ax = plt.subplots(figsize=(10, 4.4))
firms = ["Dexcom", "Abbott", "Medtronic", "Senseonics", "Cardinal Health", "Get Tested Intl."]
ev["date"] = pd.to_datetime(ev.initiated)
style = {"Class I": dict(marker="D", s=70, color=RED, edgecolor="white", zorder=4),
         "Class II": dict(marker="o", s=45, color=BLUE, edgecolor="white", zorder=3),
         "No class (old)": dict(marker="o", s=45, facecolor="white", edgecolor=GRAY, zorder=3)}
for c, st in style.items():
    d = ev[ev.cls == c]
    ax.scatter(d.date, d.Firm.map({f: len(firms) - i for i, f in enumerate(firms)}), label=c, linewidths=1.2, **st)
for _, r in ev[ev.cls == "Class I"].iterrows():
    y = len(firms) - firms.index(r.Firm)
    lab, off, ha = {73412: ("G4 receiver alarm", 0.3, "center"), 91756: ("reader battery", 0.3, "center"),
                    95047: ("Libre 3 reads high", -0.32, "center"), 96743: ("receiver speaker", -0.32, "right"),
                    97262: ("G7 app", 0.3, "center"), 97607: ("G6 app", -0.32, "left"),
                    98049: ("Libre 3 reads low", 0.3, "center")}[r.recall_event_id]
    ax.text(r.date, y + off, lab, fontsize=7.5, ha=ha, va="center", color=INK2)
ax.set_yticks(range(len(firms), 0, -1))
ax.set_yticklabels(firms)
ax.set_ylim(0.4, len(firms) + 0.7)
ax.set_xlabel("Date the recall started")
ax.set_title("CGM recall events over time (32 events)", loc="left")
ax.legend(loc="lower left", fontsize=9, ncol=1)
ax.set_xlim(pd.Timestamp("2008-01-01"), pd.Timestamp("2027-06-30"))
ax.grid(axis="y", visible=False)
save(fig, "fig5_recalls_timeline.png")

md += ["## g. Recalls",
       "A recall event = one FDA action (it can have several records, one per product model).",
       "- **Class I** = most serious (use may cause serious injury or death).",
       "- **Class II** = use may cause temporary or reversible harm.", "",
       "Recall events by firm (3 more firms have 1 each; `tables/g_recalls_by_firm.csv`):",
       *[f"- {r.Firm}: {r.Total} ({r._2} Class I)" for r in by_firm.head(3).itertuples()],
       "",
       "Recall type (our plain grouping of the FDA reason; `g_recalls_by_type.csv`):",
       *[f"- {r.Type}: {r.Total} ({r._2} Class I)" for r in by_type.itertuples()], "",
       "The 7 Class I recalls (all 32: `tables/g_recall_events.csv`). Quantity = sum of numbers in the FDA records; units differ; rough size only.", "",
       md_table(rec_tab[rec_tab.Class == "Class I"].drop(columns=["FDA records", "Class", "Type"])), "",
       "![Recall timeline](figures/fig5_recalls_timeline.png)", "",
       "What it means:",
       f"- Nov 2025 Libre 3 recall: FDA lists {int(harm.injuries.iloc[0]):,} injuries and {int(harm.deaths.iloc[0])} deaths (as of {harm.as_of_date.iloc[0]}). Other recalls: harm numbers not typed in yet.",
       f"- {n_c1_recent} of the {n_c1} Class I recalls started in 2023 or later.",
       "- Wrong-reading recalls: 2 for the drug hydroxyurea (falsely high), 2 for Libre 3 (high in 2024, low in 2025), plus cold exposure, a Guardian 4 sensing-layer defect, and 2 old Navigator recalls.",
       ""]

# ================================================================ h. demographics
MISSING = {"", "NA", "UNKNOWN", "UNK", "NI", "ASKU", "UNK YR"}


def age_years(s):
    s = str(s).strip().upper()
    mm = re.fullmatch(r"(-?[\d.]+)\s*(YR|MO|WK|DA)?", s)
    if not mm:
        return np.nan
    v = float(mm.group(1))
    unit = mm.group(2) or "YR"
    v = v / {"YR": 1, "MO": 12, "WK": 52, "DA": 365}[unit]
    return v if 0 <= v <= 110 else np.nan


BINS = [0, 18, 30, 45, 65, 75, 200]
BLAB = ["0-17", "18-29", "30-44", "45-64", "65-74", "75+"]
age_c["years"] = age_c.patient_age.apply(age_years)
age_all = age_c.dropna(subset=["years"]).assign(bin=lambda d: pd.cut(d.years, BINS, right=False, labels=BLAB)).groupby("bin", observed=False).reports.sum()
S["age_years"] = S.patient_age.apply(age_years)
age_ser = pd.cut(S.age_years.dropna(), BINS, right=False, labels=BLAB).value_counts().reindex(BLAB)
age_tab = pd.DataFrame({"Age group (years)": BLAB, "All reports": age_all.values.astype(int),
                        "All reports %": (100 * age_all / age_all.sum()).round(1).values,
                        "Serious reports": age_ser.values.astype(int),
                        "Serious reports %": (100 * age_ser / age_ser.sum()).round(1).values})
wtab(age_tab, "h_age_groups.csv")


def sex_norm(v):
    v = str(v).strip()
    return v if v in ("Female", "Male", "Prefer Not To Disclose") else "Missing"


sex_all = sex_c.assign(s=sex_c.patient_sex.apply(sex_norm)).groupby("s").reports.sum()
sex_ser = S.patient_sex.apply(sex_norm).value_counts()
sex_tab = pd.DataFrame({"Sex": ["Female", "Male", "Prefer Not To Disclose", "Missing"]})
sex_tab["All reports"] = sex_tab.Sex.map(sex_all).fillna(0).astype(int)
sex_tab["All reports %"] = (100 * sex_tab["All reports"] / sex_tab["All reports"].sum()).round(1)
sex_tab["Serious reports"] = sex_tab.Sex.map(sex_ser).fillna(0).astype(int)
sex_tab["Serious reports %"] = (100 * sex_tab["Serious reports"] / N_SER).round(1)
wtab(sex_tab, "h_sex.csv")
age_fill_all = 100 * age_all.sum() / TOTAL_REPORTS
age_fill_ser = 100 * S.age_years.notna().mean()
known = sex_tab[sex_tab.Sex.isin(["Female", "Male"])]
fill = pd.DataFrame([
    ("Age (usable number)", round(age_fill_all, 1), round(age_fill_ser, 1)),
    ("Sex (female or male)", round(100 * known["All reports"].sum() / sex_tab["All reports"].sum(), 1),
     round(100 * known["Serious reports"].sum() / N_SER, 1)),
], columns=["Field", "All reports: % filled", "Serious reports: % filled"])
wtab(fill, "h_fill_rates.csv")
med_all = np.repeat(age_c.dropna(subset=["years"]).years.values, age_c.dropna(subset=["years"]).reports.values)
med_all = float(np.median(med_all))
med_ser = float(S.age_years.median())
sx = sex_tab.set_index("Sex")
demo = pd.DataFrame([
    ("Age filled in (%)", round(age_fill_all, 1), round(age_fill_ser, 1)),
    ("Median age (years)", round(med_all), round(med_ser)),
    ("Under 18 (% of known age)", age_tab["All reports %"].iloc[0], age_tab["Serious reports %"].iloc[0]),
    ("Female (% of all)", sx.loc["Female", "All reports %"], sx.loc["Female", "Serious reports %"]),
    ("Male (% of all)", sx.loc["Male", "All reports %"], sx.loc["Male", "Serious reports %"]),
    ("Sex missing (% of all)", sx.loc["Missing", "All reports %"], sx.loc["Missing", "Serious reports %"]),
], columns=["Measure", "All reports", "Serious reports"])
wtab(demo, "h_demographics_summary.csv")

fig, ax = plt.subplots(figsize=(8, 4.2))
xx = np.arange(len(BLAB))
w = 0.38
ax.bar(xx - w / 2, age_tab["All reports %"], w, color=BLUE, label="All reports", edgecolor="white")
ax.bar(xx + w / 2, age_tab["Serious reports %"], w, color=ORANGE, label="Death + injury reports", edgecolor="white")
for i in range(len(BLAB)):
    ax.text(xx[i] - w / 2, age_tab["All reports %"][i] + 0.6, f"{age_tab['All reports %'][i]:.0f}", ha="center", fontsize=8, color=INK2)
    ax.text(xx[i] + w / 2, age_tab["Serious reports %"][i] + 0.6, f"{age_tab['Serious reports %'][i]:.0f}", ha="center", fontsize=8, color=INK2)
ax.set_xticks(xx)
ax.set_xticklabels(BLAB)
ax.set_xlabel("Patient age group (years)")
ax.grid(axis="x", visible=False)
ax.set_ylabel("% of reports with a known age")
ax.set_title("Age of patients in CGM problem reports", loc="left")
ax.legend(loc="upper left", fontsize=9)
ax.text(0, -0.2, f"Age is filled in for {age_fill_all:.0f}% of all reports and {age_fill_ser:.0f}% of death + injury reports.",
        transform=ax.transAxes, fontsize=8, color=MUTED)
save(fig, "fig6_age_groups.png")

md += ["## h. Demographics",
       md_table(demo), "", "![Age groups](figures/fig6_age_groups.png)", "",
       "What it means:",
       "- The age mix is about the same in all and serious reports. About 1 in 6 reports with a known age is for a child.",
       "- More than half of reports have no sex recorded. Race and ethnicity are almost always blank (under 3%), so we do not report them. Tables: `h_age_groups.csv`, `h_sex.csv`.", ""]

# ================================================================ i. keyword signals
KW = {
    "Low reading words (e.g. 'low reading', 'falsely low', 'lower than')":
        r"LOW(ER)? (GLUCOSE |SENSOR |CGM )?(READING|RESULT|VALUE)S?|FALSE(LY)? LOW|READ(S|ING)? (TOO )?LOW|LOWER THAN",
    "High reading words (e.g. 'high reading', 'falsely high')":
        r"HIGH(ER)? (GLUCOSE |SENSOR |CGM )?(READING|RESULT|VALUE)S?|FALSE(LY)? HIGH|READ(S|ING)? (TOO )?HIGH|HIGHER THAN",
    "Fingerstick / meter mentioned": r"FINGER ?STICK|FINGER ?PRICK|BLOOD GLUCOSE METER|\bBGM\b|GLUCOMETER|\bSMBG\b|METER READING",
    "Inaccuracy words ('inaccura', 'discrepan', 'did not match')": r"INACCURA|DISCREPAN|DID NOT MATCH|MISMATCH",
    "Hypoglycemia / low blood sugar": r"HYPOGLYC|LOW BLOOD SUGAR",
    "Emergency care (ambulance, emergency room, 911)": r"EMERGENCY|AMBULANCE|PARAMEDIC|\bEMS\b|\b911\b",
    "Skin reaction (skin reaction, rash, itch, allergy, infection)": r"SKIN REACTION|RASH|REDNESS|ITCH|ALLERG|IRRITAT|BLISTER|INFECTION",
    "Sensor fell off / adhesive": r"FELL OFF|FALLING OFF|CAME OFF|ADHESI|DETACH",
}
txt = S.event_text.fillna("").str.upper()
kw_rows = []
hits = {}
for k, rx in KW.items():
    h_ = txt.str.contains(rx.replace("(", "(?:"), regex=True)
    hits[k] = h_
    r = {"Keyword group": k, "Serious reports": int(h_.sum()), "% of serious": round(100 * h_.mean(), 1)}
    for m in big3:
        r[f"{m} %"] = round(100 * h_[S.mfr == m].mean(), 1)
    kw_rows.append(r)
combo = hits[list(KW)[0]] & hits[list(KW)[2]]
kw_rows.append({"Keyword group": "Low reading words AND fingerstick/meter", "Serious reports": int(combo.sum()),
                "% of serious": round(100 * combo.mean(), 1), **{f"{m} %": round(100 * combo[S.mfr == m].mean(), 1) for m in big3}})
kw = pd.DataFrame(kw_rows)
wtab(kw, "i_keyword_signals_serious.csv")
md += ["## i. Keyword signals in serious reports (keyword counts, NOT AI labels)",
       "Simple word patterns in the event text. Misses other wordings; can wrongly match (e.g. 'no low readings'). More groups: `tables/i_keyword_signals_serious.csv`.", "",
       md_table(kw.iloc[[0, 1, 2, 8]]), "",
       "What it means:",
       "- Each company writes reports from its own template. Dexcom texts often say 'an inaccuracy between the CGM and ...'. So differences between manufacturers partly reflect wording, not events.",
       "- Low reading words appear in more Abbott serious reports than Dexcom ones. This fits the Libre 3 'reads too low' recall, but is not proof.", ""]

# ================================================================ j. caveats
md += ["## j. Caveats (read before using any number)",
       "| Caveat | Why it matters |", "|---|---|",
       "| Voluntary reporting | Many problems are never reported. Some are reported many times. |",
       "| Counts, not rates | No count of sensors used. A brand with more users gets more reports. Never call these rates or risk. |",
       "| Date received vs date of event | Reports can arrive months or years late. Jumps by date received can be backlogs. |",
       "| Duplicates | The same event can be reported by the patient and by the maker. 65 double-coded serious reports were removed; others may remain. |",
       "| Brand-name cleaning | We grouped 2,600+ brand spellings by keyword. A few may be in the wrong family. MDS brand list was cut at 999 spellings (about 170 reports lost). |",
       "| Product codes mix brands | QBJ holds Dexcom G6/G7 and Libre 2 Plus/3. So all-report problem and monthly counts cannot be split by brand. |",
       "| Missing demographics | Age is missing in about 1 in 4 reports, sex in about half. Race and ethnicity almost always missing. |",
       ""]

(OUT / "report_results.md").write_text("\n".join(md).replace("\n\n## ", "\n## ").rstrip() + "\n", encoding="utf-8")
print("lines in md:", len(md), "->", OUT / "report_results.md")
print(mfr_tab.to_string())
print(fam_ser.to_string())
print(lib_tab.to_string())
print(kw.to_string())
