"""
COMMODITY EXPLORER
==================
Interactive script to analyse any commodity from prices_normalised.csv.
Generates a self-contained HTML report with:
  - Validity breakdown (valid vs blank/zero rows)
  - Unit-of-measure distribution
  - Log-IQR histogram with fences highlighted
  - Outlier detail table
  - Full row listing

Usage:
  python commodity_explorer.py
  python commodity_explorer.py --input /path/to/prices_normalised.csv
  python commodity_explorer.py --input /path/to/file.csv --output /path/to/reports/
  python commodity_explorer.py --commodity "8421.21.00"   # partial match, skip selector
"""

import argparse, json, math, sys, textwrap, webbrowser
from pathlib import Path

import numpy as np
import pandas as pd

# ── CONFIG ────────────────────────────────────────────────────────────────────
BASE_DIR   = Path.cwd()
INPUT_FILE = BASE_DIR / "Dataset" / "Normalised" / "prices_normalised.csv"
OUTPUT_DIR = BASE_DIR / "Dataset" / "Reports"
LOG_IQR_MULT = 1.5
MIN_ROWS     = 5           # minimum valid rows to compute fences


# ── LOAD ──────────────────────────────────────────────────────────────────────
def load(path: Path) -> pd.DataFrame:
    print(f"  Loading {path.name} ...", end=" ", flush=True)
    df = pd.read_csv(path, low_memory=False)
    print(f"{len(df):,} rows")
    return df


# ── COMMODITY SELECTOR ────────────────────────────────────────────────────────
def choose_commodity(df: pd.DataFrame, query: str = "") -> str:
    """
    Interactive fuzzy search.  Keeps asking until the user picks exactly one.
    If `query` is provided (from --commodity flag) skip the prompt loop.
    """
    commodities = sorted(df["Commodity"].dropna().unique())

    if query:
        hits = [c for c in commodities if query.lower() in c.lower()]
        if len(hits) == 1:
            return hits[0]
        if len(hits) == 0:
            print(f"\n  No commodity matches '{query}'.")
            query = ""
        else:
            print(f"\n  '{query}' matches {len(hits)} commodities — entering selector.")
            query = ""

    while True:
        print("\n" + "─" * 65)
        print("  COMMODITY SELECTOR")
        print("  Type part of the HS code or description to search.")
        print("  Examples:  8421   /   coffee   /   lithium   /   polyethylene")
        print("─" * 65)
        term = input("  Search: ").strip()
        if not term:
            continue

        hits = [c for c in commodities if term.lower() in c.lower()]

        if len(hits) == 0:
            print(f"  No matches for '{term}'. Try a shorter or different term.")
            continue

        if len(hits) > 50:
            print(f"  {len(hits)} matches — too many to list. Refine your search.")
            continue

        print(f"\n  {len(hits)} match{'es' if len(hits)>1 else ''}:\n")
        for i, c in enumerate(hits, 1):
            # Wrap long names neatly
            label = textwrap.shorten(c, width=80, placeholder="…")
            print(f"  [{i:>3}] {label}")

        if len(hits) == 1:
            confirm = input("\n  Press Enter to select, or 'n' to search again: ").strip().lower()
            if confirm != "n":
                return hits[0]
            continue

        print()
        choice = input("  Enter number (or press Enter to search again): ").strip()
        if not choice:
            continue
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(hits):
                return hits[idx]
            print("  Out of range.")
        except ValueError:
            print("  Please enter a number.")


# ── COMPUTE STATS ─────────────────────────────────────────────────────────────
def compute(df: pd.DataFrame, commodity: str) -> dict:
    sub = df[df["Commodity"] == commodity].copy()

    # ── Validity classification ───────────────────────────────────────────────
    def classify(row):
        if row["_conversion_status"] == "BLANK_UNIT":
            return "blank_unit"
        if row["_conversion_status"] == "ZERO_QTY":
            return "zero_qty"
        if pd.isna(row["_unit_price"]) or row["_unit_price"] <= 0:
            return "no_price"
        if pd.isna(row["Value ($)"]) or row["Value ($)"] <= 0:
            return "no_value"
        return "valid"

    sub["_validity"] = sub.apply(classify, axis=1)
    valid = sub[sub["_validity"] == "valid"].copy()

    # ── Summary counts ────────────────────────────────────────────────────────
    total       = len(sub)
    n_valid     = len(valid)
    n_blank     = (sub["_validity"] == "blank_unit").sum()
    n_zero_qty  = (sub["_validity"] == "zero_qty").sum()
    n_no_price  = (sub["_validity"] == "no_price").sum()
    n_no_value  = (sub["_validity"] == "no_value").sum()

    # ── Unit of measure breakdown (all rows) ──────────────────────────────────
    uom_counts = (sub["Unit of measure"]
                  .fillna("Unknown")
                  .value_counts()
                  .reset_index()
                  .rename(columns={"index": "uom", "Unit of measure": "uom", "count": "n"}))
    uom_counts.columns = ["uom", "n"]
    uom_list = uom_counts.to_dict("records")

    base_unit_counts = (sub["_base_unit"]
                        .fillna("—")
                        .value_counts()
                        .reset_index()
                        .rename(columns={"index": "base_unit", "_base_unit": "base_unit", "count": "n"}))
    base_unit_counts.columns = ["base_unit", "n"]
    base_unit_list = base_unit_counts.to_dict("records")

    # ── Price stats (valid rows only) ─────────────────────────────────────────
    if n_valid < 2:
        # Not enough data — return minimal structure
        return {
            "commodity": commodity,
            "total": total, "n_valid": n_valid, "n_blank": n_blank,
            "n_zero_qty": n_zero_qty, "n_no_price": n_no_price, "n_no_value": n_no_value,
            "uom": uom_list, "base_units": base_unit_list,
            "sufficient": False, "stats": {}, "hist": [], "outliers": [], "rows": []
        }

    prices = valid["_unit_price"]

    q1   = prices.quantile(0.25)
    q3   = prices.quantile(0.75)
    iqr  = q3 - q1
    med  = prices.median()
    mean = prices.mean()
    std  = prices.std()
    cv   = std / med if med > 0 else None

    # Log-IQR fences
    lp   = np.log10(prices.clip(lower=1e-9))
    lq1  = lp.quantile(0.25)
    lq3  = lp.quantile(0.75)
    liqr = lq3 - lq1
    lo   = float(10 ** (lq1 - LOG_IQR_MULT * liqr))
    hi   = float(10 ** (lq3 + LOG_IQR_MULT * liqr))
    lmed = float(10 ** lp.median())
    lstd = float(lp.std())

    sufficient = n_valid >= MIN_ROWS

    # Outlier flags
    valid = valid.copy()
    valid["_log_price"] = lp.values
    valid["_log_z"]     = ((lp - lp.median()) / lstd).round(3) if lstd > 0 else 0.0
    valid["_outlier"]   = (prices < lo) | (prices > hi)
    valid["_direction"] = np.where(prices < lo, "LOW", np.where(prices > hi, "HIGH", ""))
    valid["_severity"]  = np.where(
        valid["_outlier"],
        np.where(valid["_log_z"].abs() >= 3, "CRITICAL",
        np.where(valid["_log_z"].abs() >= 2, "HIGH", "MEDIUM")),
        "")
    if not sufficient:
        valid["_outlier"]  = False
        valid["_severity"] = ""

    n_outlier   = int(valid["_outlier"].sum())
    n_out_low   = int((valid["_direction"] == "LOW").sum())
    n_out_high  = int((valid["_direction"] == "HIGH").sum())
    total_value = float(valid["Value ($)"].sum())

    # ── Country breakdown ─────────────────────────────────────────────────────
    ctry = (valid.groupby("Country", dropna=False)
            .agg(n=("_unit_price","count"),
                 med_price=("_unit_price","median"),
                 total_val=("Value ($)","sum"),
                 n_out=("_outlier","sum"))
            .reset_index()
            .sort_values("n", ascending=False))
    ctry["med_price"] = ctry["med_price"].round(2)
    ctry["total_val"] = ctry["total_val"].round(0)
    country_list = ctry.to_dict("records")

    # ── Histogram (log-spaced bins) ───────────────────────────────────────────
    pmin = prices.min()
    pmax = prices.max()
    if pmin <= 0:
        pmin = prices[prices > 0].min() if (prices > 0).any() else 0.01
    bin_edges = np.logspace(
        math.log10(max(pmin * 0.85, 1e-6)),
        math.log10(pmax * 1.15),
        30
    )
    hist_data = []
    for i in range(len(bin_edges) - 1):
        mask   = (prices >= bin_edges[i]) & (prices < bin_edges[i + 1])
        n_bin  = int(mask.sum())
        n_low  = int((mask & (valid["_direction"] == "LOW")).sum())
        n_high = int((mask & (valid["_direction"] == "HIGH")).sum())
        hist_data.append({
            "x0":     round(float(bin_edges[i]), 4),
            "x1":     round(float(bin_edges[i + 1]), 4),
            "xmid":   round(float((bin_edges[i] + bin_edges[i + 1]) / 2), 4),
            "n":      n_bin,
            "n_low":  n_low,
            "n_high": n_high,
        })

    # ── All valid rows for the row table ─────────────────────────────────────
    keep_cols = [
        "Period", "Country", "Province", "Quantity",
        "Unit of measure", "_base_unit", "_unit_price",
        "Value ($)", "_conversion_status",
        "_outlier", "_direction", "_severity", "_log_z"
    ]
    keep_cols = [c for c in keep_cols if c in valid.columns]
    rows_df = valid[keep_cols].copy()
    rows_df = rows_df.sort_values("_unit_price", ascending=False).reset_index(drop=True)

    def safe(v):
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        if isinstance(v, (np.integer,)):   return int(v)
        if isinstance(v, (np.floating,)):  return float(v)
        if isinstance(v, (np.bool_,)):     return bool(v)
        return v

    rows_list = [
        {k: safe(v) for k, v in row.items()}
        for row in rows_df.to_dict("records")
    ]

    # Outliers only (for the detail section)
    outlier_rows = [r for r in rows_list if r.get("_outlier")]

    stats = {
        "n_valid": n_valid, "n_countries": int(valid["Country"].nunique()),
        "min": round(float(prices.min()), 4),
        "max": round(float(prices.max()), 2),
        "median": round(float(med), 2),
        "mean": round(float(mean), 2),
        "std": round(float(std), 2),
        "cv": round(float(cv), 2) if cv else None,
        "q1": round(float(q1), 2), "q3": round(float(q3), 2),
        "iqr": round(float(iqr), 2),
        "lo": round(lo, 4), "hi": round(hi, 2),
        "lmed": round(lmed, 2), "lstd": round(lstd, 4),
        "log_iqr_mult": LOG_IQR_MULT,
        "n_outlier": n_outlier, "n_out_low": n_out_low, "n_out_high": n_out_high,
        "pct_outlier": round(n_outlier / n_valid * 100, 1) if n_valid > 0 else 0,
        "total_value": round(total_value, 0),
        "sufficient": sufficient,
    }

    return {
        "commodity": commodity,
        "total": total, "n_valid": n_valid, "n_blank": n_blank,
        "n_zero_qty": n_zero_qty, "n_no_price": n_no_price, "n_no_value": n_no_value,
        "uom": uom_list, "base_units": base_unit_list,
        "sufficient": sufficient,
        "stats": stats,
        "hist": hist_data,
        "outliers": outlier_rows,
        "countries": country_list,
        "rows": rows_list,
    }


# ── HTML TEMPLATE ─────────────────────────────────────────────────────────────
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%%TITLE%%</title>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@300;400;500;600;700&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&display=swap" rel="stylesheet">
<style>
:root {
  --bg:      #f4f1ec;
  --bg2:     #ede9e2;
  --bg3:     #e4dfd6;
  --ink:     #1c1812;
  --ink2:    #5c5448;
  --ink3:    #9a9080;
  --border:  rgba(92,84,72,0.15);
  --border2: rgba(92,84,72,0.25);
  --red:     #c0311e;
  --red-bg:  rgba(192,49,30,0.08);
  --amber:   #b85c00;
  --amb-bg:  rgba(184,92,0,0.09);
  --green:   #2a6e3f;
  --grn-bg:  rgba(42,110,63,0.08);
  --blue:    #1a4f9e;
  --blu-bg:  rgba(26,79,158,0.08);
  --teal:    #0e7a6a;
  --tel-bg:  rgba(14,122,106,0.08);
  --bar-clean: rgba(26,79,158,0.55);
  --bar-low:   #0e7a6a;
  --bar-high:  #b85c00;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:'DM Mono',monospace;font-size:12.5px;line-height:1.65;min-height:100vh}

/* ── HEADER ── */
.hdr{padding:48px 56px 40px;border-bottom:2px solid var(--ink);position:relative;overflow:hidden}
.hdr::after{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;
  background:repeating-linear-gradient(90deg,var(--ink) 0,var(--ink) 8px,transparent 8px,transparent 16px)}
.hdr-label{font-size:9.5px;letter-spacing:.28em;text-transform:uppercase;color:var(--ink3);margin-bottom:12px}
.hdr-title{font-family:'Bricolage Grotesque',sans-serif;font-size:28px;font-weight:700;
  color:var(--ink);line-height:1.2;max-width:820px;margin-bottom:10px}
.hdr-hs{font-family:'Bricolage Grotesque',sans-serif;font-size:13px;font-weight:300;
  color:var(--ink2);letter-spacing:.04em}
.hdr-meta{margin-top:14px;font-size:11px;color:var(--ink3);display:flex;gap:24px;flex-wrap:wrap}
.hdr-meta span{color:var(--ink2)}

/* ── PAGE ── */
.page{max-width:1140px;margin:0 auto;padding:0 56px 80px}
.section{margin-top:48px;animation:up .45s ease both}
.section:nth-child(2){animation-delay:.04s}.section:nth-child(3){animation-delay:.08s}
.section:nth-child(4){animation-delay:.12s}.section:nth-child(5){animation-delay:.16s}
.section:nth-child(6){animation-delay:.20s}.section:nth-child(7){animation-delay:.24s}
@keyframes up{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}

.eyebrow{font-size:9px;letter-spacing:.28em;text-transform:uppercase;color:var(--ink3);
  margin-bottom:16px;display:flex;align-items:center;gap:12px}
.eyebrow::after{content:'';flex:1;height:1px;background:var(--border2)}

/* ── KPI ROW ── */
.kpi-row{display:grid;grid-template-columns:repeat(7,1fr);gap:1px;background:var(--border2);border:1px solid var(--border2)}
.kpi{background:var(--bg);padding:16px 14px 13px;text-align:center}
.kpi-v{font-family:'Bricolage Grotesque',sans-serif;font-size:21px;font-weight:700;
  color:var(--ink);letter-spacing:-.02em;line-height:1.1}
.kpi-v.red{color:var(--red)}.kpi-v.amber{color:var(--amber)}.kpi-v.green{color:var(--green)}.kpi-v.blue{color:var(--blue)}
.kpi-l{font-size:8.5px;color:var(--ink3);text-transform:uppercase;letter-spacing:.12em;margin-top:4px}

/* ── VALIDITY STRIP ── */
.validity-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:1px;background:var(--border);border:1px solid var(--border)}
.validity-card{background:var(--bg2);padding:14px 16px}
.vc-count{font-family:'Bricolage Grotesque',sans-serif;font-size:20px;font-weight:600;line-height:1.1}
.vc-label{font-size:9px;text-transform:uppercase;letter-spacing:.12em;color:var(--ink3);margin-top:3px}
.vc-sub{font-size:10.5px;color:var(--ink3);margin-top:4px}
.vc-bar{height:3px;margin-top:8px;border-radius:2px}

/* ── UOM TABLE ── */
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.panel{background:var(--bg2);border:1px solid var(--border)}
.panel-hdr{padding:11px 16px;border-bottom:1px solid var(--border);font-size:9px;
  letter-spacing:.18em;text-transform:uppercase;color:var(--ink3)}
.uom-row{display:flex;justify-content:space-between;align-items:center;
  padding:8px 16px;border-bottom:1px solid rgba(92,84,72,.06);font-size:11.5px}
.uom-row:last-child{border-bottom:none}
.uom-bar-bg{height:3px;background:var(--bg3);margin-top:4px;border-radius:2px}
.uom-bar-fill{height:100%;background:var(--blue);border-radius:2px;opacity:.5}

/* ── CALLOUT ── */
.callout{padding:16px 20px;border-left:3px solid;font-size:12.5px;line-height:1.75;margin:16px 0}
.callout.blue{border-color:var(--blue);background:var(--blu-bg)}
.callout.amber{border-color:var(--amber);background:var(--amb-bg)}
.callout.green{border-color:var(--green);background:var(--grn-bg)}
.callout.red{border-color:var(--red);background:var(--red-bg)}
.callout.teal{border-color:var(--teal);background:var(--tel-bg)}
.callout strong{color:var(--ink);font-weight:500}
.hl-red{color:var(--red);font-weight:500}.hl-amb{color:var(--amber);font-weight:500}
.hl-grn{color:var(--green);font-weight:500}.hl-blu{color:var(--blue);font-weight:500}
.hl-tel{color:var(--teal);font-weight:500}

/* ── STATS PANELS ── */
.stats-two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.stat-row{display:flex;justify-content:space-between;align-items:baseline;
  padding:6px 16px;border-bottom:1px solid rgba(92,84,72,.06);font-size:11.5px}
.stat-row:last-child{border-bottom:none}
.stat-key{color:var(--ink3)}.stat-val{color:var(--ink);font-weight:500}
.stat-val.red{color:var(--red)}.stat-val.amb{color:var(--amber)}.stat-val.grn{color:var(--green)}.stat-val.blu{color:var(--blue)}

/* ── HISTOGRAM ── */
.chart-wrap{background:var(--bg2);border:1px solid var(--border);padding:24px 28px 20px}
.chart-title{font-family:'Bricolage Grotesque',sans-serif;font-size:13px;font-weight:600;color:var(--ink);margin-bottom:2px}
.chart-sub{font-size:11px;color:var(--ink3);margin-bottom:20px}
#histogram{width:100%;height:260px;position:relative;display:flex;align-items:flex-end;gap:1.5px}
.bar-wrap{flex:1;display:flex;flex-direction:column;justify-content:flex-end;height:100%;cursor:pointer}
.bar-fill{width:100%;border-radius:1px 1px 0 0;transition:opacity .15s}
.bar-wrap:hover .bar-fill{opacity:.65}
.bar-clean{background:var(--bar-clean)}
.bar-low{background:var(--bar-low);box-shadow:0 0 5px rgba(14,122,106,.3)}
.bar-high{background:var(--bar-high);box-shadow:0 0 5px rgba(184,92,0,.3)}
.bar-mixed-low{background:linear-gradient(to top,var(--bar-low) 40%,var(--bar-clean) 100%)}
.bar-mixed-high{background:linear-gradient(to top,var(--bar-high) 40%,var(--bar-clean) 100%)}
.chart-overlay{position:absolute;top:0;bottom:0;left:0;right:0;pointer-events:none}
.vline{position:absolute;top:0;bottom:0}
.vline-median{border-left:2px solid var(--blue);opacity:.75}
.vline-lo{border-left:2px dashed var(--teal);opacity:.85}
.vline-hi{border-left:2px dashed var(--amber);opacity:.85}
.vlabel{position:absolute;top:7px;font-size:8px;letter-spacing:.05em;white-space:nowrap;
  padding:2px 5px;border-radius:2px}
.vlabel-med{background:var(--blu-bg);color:var(--blue);border:1px solid rgba(26,79,158,.25)}
.vlabel-lo{background:var(--tel-bg);color:var(--teal);border:1px solid rgba(14,122,106,.25)}
.vlabel-hi{background:var(--amb-bg);color:var(--amber);border:1px solid rgba(184,92,0,.25)}
.x-axis{display:flex;gap:1.5px;margin-top:5px}
.x-tick{flex:1;text-align:center;font-size:8px;color:var(--ink3);overflow:hidden;white-space:nowrap}
.chart-legend{display:flex;gap:20px;margin-top:14px;flex-wrap:wrap}
.leg-item{display:flex;align-items:center;gap:7px;font-size:10.5px;color:var(--ink3)}
.leg-sw{width:12px;height:8px;border-radius:1px}

/* ── TOOLTIP ── */
#tip{position:fixed;background:var(--ink);color:#f0ede8;padding:9px 13px;font-size:11px;
  pointer-events:none;z-index:200;display:none;min-width:140px;box-shadow:0 6px 24px rgba(0,0,0,.3)}
#tip .tr{font-size:9.5px;color:#8a8070;margin-bottom:3px}
#tip .tc{font-size:13px;font-weight:500}

/* ── OUTLIER TABLE ── */
.outlier-wrap{background:var(--bg2);border:1px solid var(--border);overflow:hidden}
.outlier-hdr{padding:13px 18px;border-bottom:1px solid var(--border);
  display:flex;justify-content:space-between;align-items:center}
.outlier-hdr-title{font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink3)}
.badge{font-size:9px;padding:2px 9px;letter-spacing:.06em}
.badge-out{background:var(--amb-bg);color:var(--amber);border:1px solid rgba(184,92,0,.3)}
.badge-low{background:var(--tel-bg);color:var(--teal);border:1px solid rgba(14,122,106,.3)}
.badge-ok{background:var(--grn-bg);color:var(--green);border:1px solid rgba(42,110,63,.3)}

table{width:100%;border-collapse:collapse}
th{font-size:8.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink3);
  padding:9px 14px;text-align:left;font-weight:400;border-bottom:1px solid var(--border);white-space:nowrap}
td{font-size:11.5px;padding:10px 14px;border-bottom:1px solid rgba(92,84,72,.06);color:var(--ink);vertical-align:middle}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover td{background:rgba(92,84,72,.04)}
tr.row-high td{background:rgba(184,92,0,.04)!important}
tr.row-high td:first-child{border-left:2px solid var(--amber)}
tr.row-low  td{background:rgba(14,122,106,.04)!important}
tr.row-low  td:first-child{border-left:2px solid var(--teal)}

.pill{display:inline-block;font-size:8.5px;padding:2px 7px;letter-spacing:.06em;border-radius:2px}
.pill-crit{background:var(--red-bg);color:var(--red);border:1px solid rgba(192,49,30,.3)}
.pill-high{background:var(--amb-bg);color:var(--amber);border:1px solid rgba(184,92,0,.3)}
.pill-med{background:rgba(184,92,0,.06);color:var(--amber);border:1px solid rgba(184,92,0,.2)}
.pill-low{background:var(--tel-bg);color:var(--teal);border:1px solid rgba(14,122,106,.3)}
.pill-clean{background:var(--grn-bg);color:var(--green);border:1px solid rgba(42,110,63,.25)}

.z-bar{height:3px;border-radius:2px;margin-top:4px;max-width:120px}

/* ── COUNTRY BREAKDOWN ── */
.ctry-table-wrap{background:var(--bg2);border:1px solid var(--border);overflow:hidden}
.ctry-hdr{padding:13px 18px;border-bottom:1px solid var(--border);
  display:grid;grid-template-columns:1fr auto;align-items:center}
.ctry-hdr-title{font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink3)}
.ctry-hdr-meta{font-size:10.5px;color:var(--ink3)}
.ctry-bar-bg{height:4px;background:var(--bg3);border-radius:2px;margin-top:5px;width:100%}
.ctry-bar-fill{height:100%;border-radius:2px;background:var(--blue);opacity:.45}
.ctry-bar-out{background:var(--amber);opacity:.7}
.ctry-rank{font-family:'Bricolage Grotesque',sans-serif;font-size:11px;font-weight:300;
  color:var(--ink3);width:22px;text-align:right;flex-shrink:0}

.toggle-btn{background:none;border:1px solid var(--border2);color:var(--ink3);
  font-family:'DM Mono',monospace;font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;
  padding:6px 14px;cursor:pointer;transition:all .2s}
.toggle-btn:hover{border-color:var(--ink);color:var(--ink)}
.scrollable{display:none;max-height:480px;overflow-y:auto}
.scrollable::-webkit-scrollbar{width:5px}
.scrollable::-webkit-scrollbar-thumb{background:var(--bg3);border-radius:3px}
</style>
</head>
<body>
<div id="tip"><div class="tr"></div><div class="tc"></div></div>

<div class="hdr">
  <div class="hdr-label">Commodity Analysis &nbsp;·&nbsp; Log-IQR ×%%MULT%% &nbsp;·&nbsp; prices_normalised.csv</div>
  <div class="hdr-title">%%DESC%%</div>
  <div class="hdr-hs">HS %%HSCODE%%</div>
  <div class="hdr-meta">
    Base unit: <span>%%BASEUNIT%%</span> &nbsp;·&nbsp;
    Unit Price: <span>CAD per %%BASEUNIT%%</span> &nbsp;·&nbsp;
    Source: <span>%%SOURCE%%</span>
  </div>
</div>

<div class="page">

<!-- KPI -->
<div class="section">
  <div class="eyebrow">At a glance</div>
  <div class="kpi-row" id="kpi-row"></div>
</div>

<!-- VALIDITY -->
<div class="section">
  <div class="eyebrow">Row validity breakdown</div>
  <div class="validity-grid" id="validity-grid"></div>
  <div id="validity-note" style="margin-top:10px"></div>
</div>

<!-- UOM -->
<div class="section">
  <div class="eyebrow">Unit of measure distribution</div>
  <div class="two-col">
    <div class="panel">
      <div class="panel-hdr">Reported unit of measure (all rows)</div>
      <div id="uom-list"></div>
    </div>
    <div class="panel">
      <div class="panel-hdr">Normalised base unit (valid rows only)</div>
      <div id="base-unit-list"></div>
    </div>
  </div>
</div>

<!-- STATS -->
<div class="section">
  <div class="eyebrow">Price statistics — valid rows only</div>
  <div id="stats-section"></div>
</div>

<!-- HISTOGRAM -->
<div class="section">
  <div class="eyebrow">Unit price histogram</div>
  <div class="chart-wrap">
    <div class="chart-title">Distribution of unit prices — log scale</div>
    <div class="chart-sub" id="chart-sub"></div>
    <div id="histogram"></div>
    <div class="x-axis" id="x-axis"></div>
    <div class="chart-legend" id="chart-legend"></div>
  </div>
</div>

<!-- OUTLIERS -->
<div class="section" id="outlier-section">
  <div class="eyebrow">Flagged rows</div>
  <div id="outlier-content"></div>
</div>

<!-- COUNTRY BREAKDOWN -->
<div class="section">
  <div class="eyebrow">Country breakdown — top 15 by row count</div>
  <div id="country-breakdown"></div>
</div>

<!-- ALL ROWS -->
<div class="section">
  <div class="eyebrow">All valid rows</div>
  <div class="outlier-wrap">
    <div class="outlier-hdr">
      <div class="outlier-hdr-title">All <span id="all-rows-count"></span> valid rows — sorted by unit price desc — amber border = high outlier · teal border = low outlier</div>
      <button class="toggle-btn" id="toggle-all">Show ↓</button>
    </div>
    <div class="scrollable" id="all-rows-scroll">
      <table>
        <thead><tr>
          <th>Country</th><th>Province</th><th>Period</th>
          <th>Qty</th><th>Base Unit</th>
          <th>Unit Price</th><th>Total Value</th>
          <th>Log z</th><th>Status</th>
        </tr></thead>
        <tbody id="all-rows-body"></tbody>
      </table>
    </div>
  </div>
</div>

</div><!-- /page -->
<script>
const DATA = %%DATA%%;

// ── helpers ───────────────────────────────────────────────────────────────────
const fmtP  = v => v == null ? '—' : (v >= 1000 ? '$' + v.toLocaleString('en-CA',{maximumFractionDigits:0}) : '$' + v.toLocaleString('en-CA',{minimumFractionDigits:2,maximumFractionDigits:4}));
const fmtV  = v => v == null ? '—' : (v >= 1e6 ? '$'+(v/1e6).toFixed(1)+'M' : v >= 1e3 ? '$'+(v/1e3).toFixed(0)+'K' : '$'+v.toFixed(0));
const fmtN  = v => v == null ? '—' : v.toLocaleString('en-CA');
const pct   = (n,d) => d > 0 ? (n/d*100).toFixed(1)+'%' : '0%';

const S = DATA.stats;
const tip = document.getElementById('tip');
function showTip(e, range, body) {
  tip.style.display = 'block';
  tip.querySelector('.tr').textContent = range;
  tip.querySelector('.tc').innerHTML = body;
}
document.addEventListener('mousemove', e => {
  if (tip.style.display==='block'){tip.style.left=(e.clientX+14)+'px';tip.style.top=(e.clientY-36)+'px'}
});
document.addEventListener('mouseleave', () => tip.style.display='none');

// ── KPI ───────────────────────────────────────────────────────────────────────
(function(){
  const items = [
    {v: fmtN(DATA.total),    l:'Total rows',         cls:''},
    {v: fmtN(DATA.n_valid),  l:'Valid rows',         cls:'green'},
    {v: fmtN(DATA.n_blank),  l:'Blank unit',         cls: DATA.n_blank>0?'amber':''},
    {v: S.n_countries != null ? fmtN(S.n_countries):'—', l:'Countries', cls:'blue'},
    {v: S.median != null ? fmtP(S.median) : '—',    l:'Median price',   cls:''},
    {v: S.cv != null ? S.cv.toFixed(2) : '—',       l:'CV (spread)',    cls: S.cv && S.cv>2?'red':''},
    {v: S.n_outlier != null ? fmtN(S.n_outlier):'—',l:'Outliers',       cls: S.n_outlier>0?'amber':'green'},
  ];
  const row = document.getElementById('kpi-row');
  items.forEach(it => {
    row.innerHTML += `<div class="kpi"><div class="kpi-v ${it.cls}">${it.v}</div><div class="kpi-l">${it.l}</div></div>`;
  });
})();

// ── VALIDITY ─────────────────────────────────────────────────────────────────
(function(){
  const tot = DATA.total;
  const cards = [
    {count: DATA.n_valid,    label:'Valid rows',    sub:'unit price computed',     color:'#2a6e3f', light:'var(--grn-bg)'},
    {count: DATA.n_blank,    label:'Blank unit',    sub:'no unit of measure',      color:'#b85c00', light:'var(--amb-bg)'},
    {count: DATA.n_zero_qty, label:'Zero quantity', sub:'qty=0, cannot compute',   color:'#b85c00', light:'var(--amb-bg)'},
    {count: DATA.n_no_price, label:'No price',      sub:'unit price missing/zero', color:'#9a9080', light:'var(--bg3)'},
    {count: DATA.n_no_value, label:'No value',      sub:'export value missing',    color:'#9a9080', light:'var(--bg3)'},
  ];
  const grid = document.getElementById('validity-grid');
  cards.forEach(c => {
    const w = tot > 0 ? Math.round(c.count/tot*100) : 0;
    grid.innerHTML += `<div class="validity-card" style="background:${c.light}">
      <div class="vc-count" style="color:${c.color}">${fmtN(c.count)}</div>
      <div class="vc-label">${c.label}</div>
      <div class="vc-sub">${pct(c.count,tot)} of total</div>
      <div class="vc-sub">${c.sub}</div>
      <div class="vc-bar" style="background:${c.color};opacity:.4;width:${w}%"></div>
    </div>`;
  });
  const note = document.getElementById('validity-note');
  const pctValid = tot > 0 ? (DATA.n_valid/tot*100).toFixed(0) : 0;
  const pctBlank = tot > 0 ? (DATA.n_blank/tot*100).toFixed(0) : 0;
  if (DATA.n_blank > 0) {
    note.innerHTML = `<div class="callout amber"><strong>${pctBlank}% of rows have a blank unit of measure</strong> — these cannot have a unit price calculated and are excluded from all statistics. They are real export transactions (the value is reported) but the quantity unit was not provided in the source data.</div>`;
  } else {
    note.innerHTML = `<div class="callout green"><strong>${pctValid}% of rows are valid</strong> — all have a computable unit price and are included in statistics.</div>`;
  }
})();

// ── UOM ───────────────────────────────────────────────────────────────────────
(function(){
  function buildList(containerId, items, totalKey) {
    const el = document.getElementById(containerId);
    const maxN = Math.max(...items.map(i => i.n));
    items.forEach(i => {
      const w = maxN > 0 ? Math.round(i.n/maxN*80) : 0;
      const key = i.uom || i.base_unit || '—';
      el.innerHTML += `<div class="uom-row">
        <div>
          <div style="color:var(--ink)">${key}</div>
          <div class="uom-bar-bg" style="width:100px"><div class="uom-bar-fill" style="width:${w}%"></div></div>
        </div>
        <div style="color:var(--ink2);text-align:right">${fmtN(i.n)}<br><span style="color:var(--ink3);font-size:10px">${pct(i.n, DATA.total)}</span></div>
      </div>`;
    });
  }
  buildList('uom-list', DATA.uom, DATA.total);
  buildList('base-unit-list', DATA.base_units, DATA.n_valid);
})();

// ── STATS ─────────────────────────────────────────────────────────────────────
(function(){
  const el = document.getElementById('stats-section');
  if (!DATA.sufficient) {
    el.innerHTML = `<div class="callout amber"><strong>Insufficient data.</strong> Only ${DATA.n_valid} valid rows — need at least ${DATA.stats.log_iqr_mult != null ? 5 : 5} to compute fences. Statistics shown below are indicative only.</div>`;
  }
  if (!S.median) { el.innerHTML += '<div class="callout amber">No valid price data available.</div>'; return; }

  const cvClass = S.cv > 5 ? 'red' : S.cv > 1 ? 'amb' : 'grn';
  const lo_note = S.lo < 1 ? ` <span style="color:var(--teal);font-size:10px">(catches sub-$1 prices)</span>` : '';

  el.innerHTML = `
  <div class="stats-two">
    <div class="panel">
      <div class="panel-hdr">Central tendency &amp; spread</div>
      <div class="stat-row"><span class="stat-key">Min price</span><span class="stat-val">${fmtP(S.min)}</span></div>
      <div class="stat-row"><span class="stat-key">Max price</span><span class="stat-val red">${fmtP(S.max)}</span></div>
      <div class="stat-row"><span class="stat-key">Median (Q2)</span><span class="stat-val blu">${fmtP(S.median)}</span></div>
      <div class="stat-row"><span class="stat-key">Mean</span><span class="stat-val">${fmtP(S.mean)}</span></div>
      <div class="stat-row"><span class="stat-key">Std deviation</span><span class="stat-val">${fmtP(S.std)}</span></div>
      <div class="stat-row"><span class="stat-key">CV (std ÷ median)</span><span class="stat-val ${cvClass}">${S.cv != null ? S.cv.toFixed(2) : '—'}</span></div>
      <div class="stat-row"><span class="stat-key">Total export value</span><span class="stat-val grn">${fmtV(S.total_value)}</span></div>
      <div class="stat-row"><span class="stat-key">Countries</span><span class="stat-val">${fmtN(S.n_countries)}</span></div>
    </div>
    <div class="panel">
      <div class="panel-hdr">Log-IQR fences (×${DATA.stats.log_iqr_mult})</div>
      <div class="stat-row"><span class="stat-key">Q1 (25th pct)</span><span class="stat-val">${fmtP(S.q1)}</span></div>
      <div class="stat-row"><span class="stat-key">Q3 (75th pct)</span><span class="stat-val">${fmtP(S.q3)}</span></div>
      <div class="stat-row"><span class="stat-key">Raw IQR</span><span class="stat-val">${fmtP(S.iqr)}</span></div>
      <div class="stat-row"><span class="stat-key">Log-IQR (log units)</span><span class="stat-val">${S.lstd != null ? ((Math.log10(S.q3)-Math.log10(S.q1))).toFixed(4) : '—'}</span></div>
      <div class="stat-row"><span class="stat-key">Lower fence${lo_note}</span><span class="stat-val" style="color:var(--teal)">${fmtP(S.lo)}</span></div>
      <div class="stat-row"><span class="stat-key">Upper fence</span><span class="stat-val amb">${fmtP(S.hi)}</span></div>
      <div class="stat-row"><span class="stat-key">Outliers (total)</span><span class="stat-val ${S.n_outlier>0?'amb':''}">${fmtN(S.n_outlier)} (${S.pct_outlier}%)</span></div>
      <div class="stat-row"><span class="stat-key">LOW flags / HIGH flags</span><span class="stat-val">${fmtN(S.n_out_low)} / ${fmtN(S.n_out_high)}</span></div>
    </div>
  </div>`;
})();

// ── HISTOGRAM ────────────────────────────────────────────────────────────────
(function(){
  const hist = DATA.hist;
  if (!hist || hist.length === 0) return;
  const container = document.getElementById('histogram');
  const xAxis     = document.getElementById('x-axis');
  const sub       = document.getElementById('chart-sub');

  sub.textContent = `${DATA.n_valid} valid rows · lower fence ${fmtP(S.lo)} · upper fence ${fmtP(S.hi)} · median ${fmtP(S.median)}`;

  const maxN  = Math.max(...hist.map(b => b.n));
  const xMin  = Math.log10(Math.max(hist[0].x0, 1e-9));
  const xMax  = Math.log10(hist[hist.length-1].x1);
  const logPct = v => Math.max(0, Math.min(100, (Math.log10(Math.max(v,1e-9)) - xMin) / (xMax - xMin) * 100));

  hist.forEach((b, i) => {
    const wrap = document.createElement('div');
    wrap.className = 'bar-wrap';
    if (b.n > 0) {
      const fill = document.createElement('div');
      const h = Math.max(Math.round(b.n/maxN*100), 2);
      fill.style.height = h + '%';
      fill.className = 'bar-fill ' + (
        b.n_low > 0 && b.n_low === b.n   ? 'bar-low' :
        b.n_high > 0 && b.n_high === b.n ? 'bar-high' :
        b.n_low > 0                       ? 'bar-mixed-low' :
        b.n_high > 0                      ? 'bar-mixed-high' : 'bar-clean');
      wrap.appendChild(fill);

      wrap.addEventListener('mouseenter', e => {
        const lo = b.n_low  > 0 ? ` <span style="color:#0e7a6a">↓${b.n_low} LOW</span>` : '';
        const hi = b.n_high > 0 ? ` <span style="color:#b85c00">↑${b.n_high} HIGH</span>` : '';
        showTip(e, `${fmtP(b.x0)} – ${fmtP(b.x1)}`, `${b.n} row${b.n!==1?'s':''}${lo}${hi}`);
      });
      wrap.addEventListener('mouseleave', () => tip.style.display='none');
    }
    container.appendChild(wrap);

    const tick = document.createElement('div');
    tick.className = 'x-tick';
    if (i % 5 === 0 || i === hist.length-1) {
      tick.textContent = b.xmid >= 1e6 ? '$'+(b.xmid/1e6).toFixed(0)+'M' :
                         b.xmid >= 1e3 ? '$'+(b.xmid/1e3).toFixed(0)+'k' :
                         b.xmid >= 1   ? '$'+Math.round(b.xmid) : '$'+b.xmid.toFixed(2);
    }
    xAxis.appendChild(tick);
  });

  // Overlay lines
  requestAnimationFrame(() => {
    container.style.position = 'relative';
    const ov = document.createElement('div');
    ov.className = 'chart-overlay';

    const addLine = (price, cls, lblCls, text, side='right') => {
      const p = logPct(price);
      if (p <= 0 || p >= 100) return;
      const line = document.createElement('div');
      line.className = `vline ${cls}`;
      line.style.left = p + '%';
      const lbl = document.createElement('div');
      lbl.className = `vlabel ${lblCls}`;
      lbl.textContent = text;
      if (side === 'left') lbl.style.left  = (p + 0.4) + '%';
      else                 lbl.style.right = (100 - p + 0.4) + '%';
      line.appendChild(lbl);
      ov.appendChild(line);
    };

    if (S.lo) addLine(S.lo,     'vline-lo', 'vlabel-lo', `LO ${fmtP(S.lo)}`,    'left');
    if (S.hi) addLine(S.hi,     'vline-hi', 'vlabel-hi', `HI ${fmtP(S.hi)}`);
    if (S.median) addLine(S.median, 'vline-median', 'vlabel-med', `MED ${fmtP(S.median)}`, 'left');

    container.appendChild(ov);
  });

  // Legend
  const leg = document.getElementById('chart-legend');
  leg.innerHTML = `
    <div class="leg-item"><div class="leg-sw" style="background:var(--bar-clean)"></div>Clean</div>
    <div class="leg-item"><div class="leg-sw" style="background:var(--bar-low)"></div>LOW flag</div>
    <div class="leg-item"><div class="leg-sw" style="background:var(--bar-high)"></div>HIGH flag</div>
    <div class="leg-item"><div class="leg-sw" style="width:2px;height:12px;border-radius:0;background:var(--blue)"></div>Median</div>
    <div class="leg-item"><div class="leg-sw" style="width:2px;height:12px;border-radius:0;background:var(--teal);opacity:.8"></div>Lower fence</div>
    <div class="leg-item"><div class="leg-sw" style="width:2px;height:12px;border-radius:0;background:var(--amber);opacity:.8"></div>Upper fence</div>`;
})();

// ── OUTLIER TABLE ─────────────────────────────────────────────────────────────
(function(){
  const el = document.getElementById('outlier-content');
  if (!DATA.sufficient) {
    el.innerHTML = `<div class="callout amber">Not enough valid rows (${DATA.n_valid}) to compute fences — no outliers flagged.</div>`;
    return;
  }
  if (DATA.outliers.length === 0) {
    el.innerHTML = `<div class="callout green"><strong>No outliers flagged.</strong> All ${DATA.n_valid} valid rows fall within the log-IQR fences (${fmtP(S.lo)} – ${fmtP(S.hi)}).</div>`;
    return;
  }
  const maxZ = Math.max(...DATA.outliers.map(r => Math.abs(r._log_z||0)));
  el.innerHTML = `
  <div class="outlier-wrap">
    <div class="outlier-hdr">
      <div class="outlier-hdr-title">${DATA.outliers.length} flagged row${DATA.outliers.length!==1?'s':''} · ${S.n_out_low} LOW · ${S.n_out_high} HIGH</div>
      <div style="display:flex;gap:8px">
        ${S.n_out_low  > 0 ? `<span class="badge badge-low">↓ ${S.n_out_low} LOW</span>` : ''}
        ${S.n_out_high > 0 ? `<span class="badge badge-out">↑ ${S.n_out_high} HIGH</span>` : ''}
      </div>
    </div>
    <table>
      <thead><tr>
        <th>Severity</th><th>Direction</th><th>Country</th><th>Province</th>
        <th>Period</th><th>Qty</th><th>Base Unit</th>
        <th>Unit Price</th><th>vs Median</th><th>Total Value</th><th>Log z</th>
      </tr></thead>
      <tbody id="outlier-tbody"></tbody>
    </table>
  </div>`;

  const tbody = document.getElementById('outlier-tbody');
  DATA.outliers.forEach(r => {
    const sev = r._severity;
    const dir = r._direction;
    const sevPill = sev==='CRITICAL' ? `<span class="pill pill-crit">CRITICAL</span>` :
                    sev==='HIGH'     ? `<span class="pill pill-high">HIGH</span>` :
                                       `<span class="pill pill-med">MEDIUM</span>`;
    const dirPill = dir==='LOW' ? `<span class="pill pill-low">↓ LOW</span>` :
                                   `<span class="pill pill-high">↑ HIGH</span>`;
    const ratio = S.median > 0 && r._unit_price ? (r._unit_price / S.median).toFixed(2) + '×' : '—';
    const z = r._log_z != null ? r._log_z.toFixed(3) : '—';
    const zW = maxZ > 0 ? Math.round(Math.abs(r._log_z||0)/maxZ*100) : 0;
    const zColor = dir==='LOW' ? 'var(--teal)' : 'var(--amber)';
    const tr = document.createElement('tr');
    tr.className = dir==='LOW' ? 'row-low' : 'row-high';
    tr.innerHTML = `
      <td>${sevPill}</td>
      <td>${dirPill}</td>
      <td><strong>${r.Country||'—'}</strong></td>
      <td style="color:var(--ink2)">${r.Province||'—'}</td>
      <td style="color:var(--ink2)">${r.Period||'—'}</td>
      <td style="color:var(--ink2)">${r.Quantity != null ? r.Quantity.toLocaleString('en-CA') : '—'}</td>
      <td style="color:var(--ink2)">${r._base_unit||'—'}</td>
      <td><strong>${fmtP(r._unit_price)}</strong></td>
      <td style="color:${dir==='LOW'?'var(--teal)':'var(--amber)'}">${ratio}</td>
      <td style="color:var(--ink2)">${fmtV(r['Value ($)'])}</td>
      <td>
        <div style="color:${zColor}">${z}σ</div>
        <div class="z-bar" style="width:${zW}px;background:${zColor}"></div>
      </td>`;
    tbody.appendChild(tr);
  });
})();

// ── COUNTRY BREAKDOWN ────────────────────────────────────────────────────────
(function(){
  const el = document.getElementById('country-breakdown');
  if (!DATA.countries || DATA.countries.length === 0) {
    el.innerHTML = '<div class="callout amber">No country data available.</div>';
    return;
  }

  const top15   = DATA.countries.slice(0, 15);
  const maxN    = Math.max(...top15.map(c => c.n));
  const maxVal  = Math.max(...top15.map(c => c.total_val));
  const total   = DATA.n_valid;
  const nMore   = DATA.countries.length - top15.length;

  let html = `
  <div class="ctry-table-wrap">
    <div class="ctry-hdr">
      <div class="ctry-hdr-title">${top15.length} of ${DATA.countries.length} countries shown · sorted by row count</div>
      <div class="ctry-hdr-meta">${fmtN(total)} total valid rows · ${fmtN(DATA.countries.length)} countries</div>
    </div>
    <table>
      <thead><tr>
        <th style="width:24px">#</th>
        <th>Country</th>
        <th>Rows</th>
        <th>Share of valid</th>
        <th>Median price</th>
        <th>vs Commodity median</th>
        <th>Total value</th>
        <th>Outliers</th>
      </tr></thead>
      <tbody>`;

  top15.forEach((c, i) => {
    const rowBarW   = maxN > 0 ? Math.round(c.n / maxN * 120) : 0;
    const shareW    = total > 0 ? Math.round(c.n / total * 120) : 0;
    const sharePct  = total > 0 ? (c.n / total * 100).toFixed(1) + '%' : '—';
    const hasOut    = c.n_out > 0;

    // Price deviation from commodity median
    let devHtml = '—';
    if (S.median && c.med_price) {
      const ratio = c.med_price / S.median;
      const sign  = ratio >= 1 ? '+' : '';
      const pctDev = ((ratio - 1) * 100).toFixed(0);
      const color = ratio > 1.5 ? 'var(--amber)' : ratio < 0.5 ? 'var(--teal)' : 'var(--ink2)';
      devHtml = `<span style="color:${color}">${sign}${pctDev}%</span>`;
    }

    // Value bar colour — if country has outliers, show mix
    const barClass = hasOut ? 'ctry-bar-fill ctry-bar-out' : 'ctry-bar-fill';

    html += `<tr>
      <td class="ctry-rank">${i + 1}</td>
      <td><strong>${c.Country || '—'}</strong>
          ${hasOut ? `<br><span style="font-size:9.5px;color:var(--amber)">⚠ ${c.n_out} outlier${c.n_out>1?'s':''}</span>` : ''}
      </td>
      <td>
        <div style="font-weight:500">${fmtN(c.n)}</div>
        <div class="ctry-bar-bg" style="width:${rowBarW}px"><div class="${barClass}" style="width:100%"></div></div>
      </td>
      <td>
        <div style="color:var(--ink2)">${sharePct}</div>
        <div class="ctry-bar-bg" style="width:${shareW}px"><div class="ctry-bar-fill" style="width:100%"></div></div>
      </td>
      <td style="color:var(--ink)">${fmtP(c.med_price)}</td>
      <td>${devHtml}</td>
      <td style="color:var(--ink2)">${fmtV(c.total_val)}</td>
      <td>${hasOut
        ? `<span class="pill pill-high">${c.n_out} flagged</span>`
        : `<span class="pill pill-clean">clean</span>`}
      </td>
    </tr>`;
  });

  html += `</tbody></table>`;
  if (nMore > 0) {
    html += `<div style="padding:10px 18px;font-size:10.5px;color:var(--ink3);border-top:1px solid var(--border)">
      + ${nMore} more countr${nMore===1?'y':'ies'} not shown (all with fewer rows than the 15th entry above)
    </div>`;
  }
  html += `</div>`;
  el.innerHTML = html;
})();


(function(){
  document.getElementById('all-rows-count').textContent = fmtN(DATA.rows.length);
  const tbody = document.getElementById('all-rows-body');
  DATA.rows.forEach(r => {
    const tr = document.createElement('tr');
    if (r._direction==='LOW')  tr.className = 'row-low';
    if (r._direction==='HIGH') tr.className = 'row-high';
    const statusHtml = r._outlier
      ? (r._direction==='LOW' ? `<span class="pill pill-low">LOW</span>` : `<span class="pill pill-high">HIGH</span>`)
      : `<span class="pill pill-clean">clean</span>`;
    tr.innerHTML = `
      <td>${r.Country||'—'}</td>
      <td style="color:var(--ink2);font-size:11px">${r.Province||'—'}</td>
      <td style="color:var(--ink2)">${r.Period||'—'}</td>
      <td style="color:var(--ink2)">${r.Quantity != null ? r.Quantity.toLocaleString('en-CA') : '—'}</td>
      <td style="color:var(--ink2)">${r._base_unit||'—'}</td>
      <td style="color:${r._outlier?(r._direction==='LOW'?'var(--teal)':'var(--amber)'):'var(--ink)'};font-weight:${r._outlier?'500':'400'}">${fmtP(r._unit_price)}</td>
      <td style="color:var(--ink2)">${fmtV(r['Value ($)'])}</td>
      <td style="color:var(--ink2);font-size:11px">${r._log_z != null ? r._log_z.toFixed(3)+'σ' : '—'}</td>
      <td>${statusHtml}</td>`;
    tbody.appendChild(tr);
  });

  document.getElementById('toggle-all').addEventListener('click', function(){
    const sc = document.getElementById('all-rows-scroll');
    const open = sc.style.display==='block';
    sc.style.display = open ? 'none' : 'block';
    this.textContent = open ? 'Show ↓' : 'Hide ↑';
  });
})();
</script>
</body>
</html>
"""


# ── RENDER HTML ───────────────────────────────────────────────────────────────
def render(data: dict, output_dir: Path) -> Path:
    commodity = data["commodity"]
    hs_code   = commodity.split(" - ")[0].strip() if " - " in commodity else commodity[:12]
    desc_raw  = commodity.split(" - ", 1)[1].strip() if " - " in commodity else commodity

    # Sentence-case the description
    desc = desc_raw[0].upper() + desc_raw[1:] if desc_raw else desc_raw

    base_units = [b["base_unit"] for b in data.get("base_units", []) if b["base_unit"] != "—"]
    base_unit  = base_units[0] if base_units else "unit"
    source     = "prices_normalised.csv"

    html = HTML_TEMPLATE
    html = html.replace("%%TITLE%%",    f"HS {hs_code} — Commodity Analysis")
    html = html.replace("%%DESC%%",     desc)
    html = html.replace("%%HSCODE%%",   hs_code)
    html = html.replace("%%BASEUNIT%%", base_unit)
    html = html.replace("%%SOURCE%%",   source)
    html = html.replace("%%MULT%%",     str(LOG_IQR_MULT))
    class _Enc(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, (np.integer,)):  return int(o)
            if isinstance(o, (np.floating,)): return float(o)
            if isinstance(o, (np.bool_,)):    return bool(o)
            if isinstance(o, (np.ndarray,)):  return o.tolist()
            return super().default(o)
    html = html.replace("%%DATA%%",     json.dumps(data, cls=_Enc, ensure_ascii=False))

    safe_name = hs_code.replace(".", "_").replace("/", "_")
    out_path  = output_dir / f"commodity_{safe_name}.html"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Generate a commodity analysis HTML report from prices_normalised.csv"
    )
    parser.add_argument("--input",     type=Path, default=INPUT_FILE,
                        help="Path to prices_normalised.csv")
    parser.add_argument("--output",    type=Path, default=OUTPUT_DIR,
                        help="Directory for the HTML report")
    parser.add_argument("--commodity", type=str, default="",
                        help="Partial commodity name/HS code to pre-select (skips interactive prompt if unique match)")
    parser.add_argument("--no-open",   action="store_true",
                        help="Don't automatically open the report in a browser")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"\n  ERROR: File not found: {args.input}")
        sys.exit(1)

    print("\n" + "=" * 65)
    print("  COMMODITY EXPLORER")
    print("=" * 65)

    df        = load(args.input)
    commodity = choose_commodity(df, args.commodity)

    print(f"\n  Selected: {commodity[:75]}{'…' if len(commodity)>75 else ''}")
    print("  Computing stats...", end=" ", flush=True)
    data      = compute(df, commodity)
    print("done")

    print("  Rendering HTML...", end=" ", flush=True)
    out_path  = render(data, args.output)
    print("done")

    print(f"\n  ✓ Report saved: {out_path}")
    print(f"    Valid rows   : {data['n_valid']:,} of {data['total']:,}")
    if data["stats"]:
        S = data["stats"]
        print(f"    Median price : {S.get('median','—')}")
        print(f"    Fences       : ${S.get('lo','—')} – ${S.get('hi','—')}")
        print(f"    Outliers     : {S.get('n_outlier',0)} ({S.get('pct_outlier',0)}%)")
    print()

    if not args.no_open:
        webbrowser.open(out_path.as_uri())

    return out_path


if __name__ == "__main__":
    main()
