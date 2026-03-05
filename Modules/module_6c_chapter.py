"""
MODULE 6c — Chapter-Level Price Drill-Down
============================================
INPUT  : Dataset/Normalised/prices_normalised.csv  (output of Module 6a)
USAGE  : python module_6c_chapter.py --chapter 08
         python module_6c_chapter.py --chapter fruit   (keyword search)
         python module_6c_chapter.py --list             (show all chapters)

Analyses one HS chapter at a time.  For each chapter:

  1. CHAPTER SUMMARY
       How many commodities, rows, flagged count, % flagged.
       Grouped by unit type (kg / litre / count / etc).

  2. COMMODITY OVERVIEW TABLE  (all commodities in the chapter)
       One row per commodity: n, median price, CV, outlier count, status.
       Status is one of:
         FLAGGED    — has outliers outside IQR × 3.0
         HIGH VAR   — CV > 1.0; too variable for reliable detection
         CLEAN      — no outliers found
         LOW DATA   — fewer than MIN_ROWS rows; skipped

  3. PER-COMMODITY DETAIL  (only for FLAGGED and CLEAN commodities)
       One ASCII box plot per commodity:
         min ──[  Q1 │ median │ Q3  ]──  max    (● = outlier)
       If the chapter has > MAX_DETAIL_ROWS commodities, this section
       is replaced by a compact table.

  4. SUBGROUP ANALYSIS  (for flagged commodities with enough data)
       Shows price breakdown by Country and by Season.
       Only runs when the subgroup has >= MIN_SUBGROUP rows.
       Explains whether a flagged row looks normal within its subgroup.

  5. FLAGGED ROWS DETAIL
       Full detail for every flagged row: commodity, period, country,
       raw qty, normalised qty, unit price, group median, fence, Z-score,
       and whether the row looks normal within its country or season subgroup.
"""

import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict

# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────
BASE_DIR        = Path.cwd().parent
NORMALISED_FILE = BASE_DIR / "Dataset" / "Normalised" / "prices_normalised.csv"

IQR_MULTIPLIER   = 3.0   # lenient; lower to 1.5 for more flags
MIN_ROWS         = 5     # minimum rows for any analysis
MIN_SUBGROUP     = 5     # minimum rows to split by country/season
MAX_CV           = 1.0   # commodities with CV > this are marked HIGH VAR
MAX_DETAIL_COMMS = 10    # if chapter has more than this, use table instead of per-commodity blocks
CHART_WIDTH      = 60    # width of ASCII box plot in characters

# HS chapter names (2-digit prefix -> description)
HS_CHAPTER_NAMES: dict[str, str] = {
    "01": "Live animals",
    "02": "Meat and edible meat offal",
    "03": "Fish and crustaceans",
    "04": "Dairy, eggs, honey",
    "05": "Other animal products",
    "06": "Live plants and cut flowers",
    "07": "Edible vegetables",
    "08": "Edible fruit and nuts",
    "09": "Coffee, tea, spices",
    "10": "Cereals",
    "11": "Milling products",
    "12": "Oil seeds and misc grains",
    "13": "Lac, gums, resins",
    "14": "Vegetable plaiting materials",
    "15": "Animal and vegetable fats",
    "16": "Prepared meat or fish",
    "17": "Sugars and confectionery",
    "18": "Cocoa and preparations",
    "19": "Preparations of cereals",
    "20": "Preparations of vegetables or fruit",
    "21": "Misc edible preparations",
    "22": "Beverages, spirits, vinegar",
    "23": "Animal feed and residues",
    "24": "Tobacco",
    "25": "Salt, sulphur, stone",
    "26": "Ores and ash",
    "27": "Mineral fuels and oils",
    "28": "Inorganic chemicals",
    "29": "Organic chemicals",
    "30": "Pharmaceutical products",
    "31": "Fertilisers",
    "32": "Dyes, paints, varnishes",
    "33": "Perfumes and cosmetics",
    "34": "Soap and waxes",
    "35": "Albuminoids and starches",
    "36": "Explosives and fireworks",
    "37": "Photographic goods",
    "38": "Misc chemical products",
    "39": "Plastics",
    "40": "Rubber",
    "41": "Raw hides and leather",
    "42": "Leather articles and bags",
    "43": "Furskins",
    "44": "Wood and articles of wood",
    "45": "Cork",
    "46": "Straw and basketwork",
    "47": "Pulp of wood",
    "48": "Paper and paperboard",
    "49": "Printed books and newspapers",
    "50": "Silk",
    "51": "Wool",
    "52": "Cotton",
    "53": "Other vegetable textile fibres",
    "54": "Man-made filaments",
    "55": "Man-made staple fibres",
    "56": "Wadding and felt",
    "57": "Carpets and floor coverings",
    "58": "Special woven fabrics",
    "59": "Impregnated textiles",
    "60": "Knitted or crocheted fabrics",
    "61": "Knitted or crocheted clothing",
    "62": "Not knitted clothing",
    "63": "Other made-up textile articles",
    "64": "Footwear",
    "65": "Headgear",
    "66": "Umbrellas and walking sticks",
    "67": "Feathers and artificial flowers",
    "68": "Stone, plaster and cement articles",
    "69": "Ceramic products",
    "70": "Glass and glassware",
    "71": "Precious stones and metals",
    "72": "Iron and steel",
    "73": "Articles of iron or steel",
    "74": "Copper",
    "75": "Nickel",
    "76": "Aluminium",
    "78": "Lead",
    "79": "Zinc",
    "80": "Tin",
    "81": "Other base metals",
    "82": "Tools and cutlery",
    "83": "Misc articles of base metal",
    "84": "Machinery and mechanical appliances",
    "85": "Electrical equipment",
    "86": "Railway locomotives",
    "87": "Vehicles",
    "88": "Aircraft and spacecraft",
    "89": "Ships and boats",
    "90": "Optical and medical instruments",
    "91": "Clocks and watches",
    "92": "Musical instruments",
    "93": "Arms and ammunition",
    "94": "Furniture and bedding",
    "95": "Toys and games",
    "96": "Misc manufactured articles",
    "97": "Works of art",
}

MONTH_TO_SEASON = {
    1:"Q1",2:"Q1",3:"Q1",4:"Q2",5:"Q2",6:"Q2",
    7:"Q3",8:"Q3",9:"Q3",10:"Q4",11:"Q4",12:"Q4",
}


# ──────────────────────────────────────────────────────────────
# LOAD
# ──────────────────────────────────────────────────────────────
def load_normalised(filepath: Path) -> pd.DataFrame:
    if not filepath.exists():
        raise FileNotFoundError(
            f"File not found: {filepath}\n"
            "Run Module 6a first to generate it."
        )
    df = pd.read_csv(filepath, dtype=str)
    for col in ["_unit_price", "_qty_normalised", "_month", "_year", "_conversion_factor"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "_hs_chapter" not in df.columns:
        df["_hs_chapter"] = df["Commodity"].fillna("").astype(str).str[:2]
    if "_season" not in df.columns:
        df["_season"] = df["_month"].map(MONTH_TO_SEASON).fillna("Unknown")
    return df


# ──────────────────────────────────────────────────────────────
# CHAPTER SELECTION
# ──────────────────────────────────────────────────────────────
def resolve_chapter(arg: str, df: pd.DataFrame) -> tuple[str, str]:
    """
    Accepts a 2-digit chapter number OR a keyword.
    Returns (chapter_code, chapter_name).
    """
    arg = arg.strip()

    # Exact 2-digit match
    if arg.isdigit():
        code = arg.zfill(2)
        if code in HS_CHAPTER_NAMES:
            return code, HS_CHAPTER_NAMES[code]
        # Chapter exists in data but not in our name table
        if code in df["_hs_chapter"].values:
            return code, f"Chapter {code}"
        raise ValueError(f"Chapter '{code}' not found in data.")

    # Keyword search in chapter names
    arg_lower = arg.lower()
    matches = [(k, v) for k, v in HS_CHAPTER_NAMES.items()
               if arg_lower in v.lower()]
    if not matches:
        raise ValueError(
            f"No chapter matching '{arg}'.\n"
            "Run with --list to see all available chapters."
        )
    if len(matches) > 1:
        options = "\n".join(f"  {k}: {v}" for k, v in matches)
        raise ValueError(
            f"Multiple chapters match '{arg}':\n{options}\n"
            "Use the 2-digit code to pick one."
        )
    return matches[0]


def list_chapters(df: pd.DataFrame) -> None:
    present = sorted(df["_hs_chapter"].dropna().unique())
    print("\nAvailable HS chapters in the normalised file:\n")
    for code in present:
        name = HS_CHAPTER_NAMES.get(code, "—")
        sub  = df[df["_hs_chapter"] == code]
        n_comms = sub["Commodity"].nunique()
        n_rows  = len(sub)
        print(f"  {code}  {name:<40}  {n_comms:>4} commodities  {n_rows:>6} rows")
    print()


# ──────────────────────────────────────────────────────────────
# STATS HELPERS
# ──────────────────────────────────────────────────────────────
def iqr_stats(prices: np.ndarray) -> dict:
    q1  = float(np.percentile(prices, 25))
    q3  = float(np.percentile(prices, 75))
    iqr = q3 - q1
    return {
        "min":    float(prices.min()),
        "max":    float(prices.max()),
        "q1":     q1,
        "q3":     q3,
        "median": float(np.median(prices)),
        "mean":   float(np.mean(prices)),
        "std":    float(np.std(prices, ddof=1)) if len(prices) > 1 else 0.0,
        "iqr":    iqr,
        "lo":     q1 - IQR_MULTIPLIER * iqr,
        "hi":     q3 + IQR_MULTIPLIER * iqr,
        "n":      len(prices),
    }


def cv(stats: dict) -> float:
    return stats["std"] / stats["mean"] if stats["mean"] > 0 else 0.0


def outlier_mask(prices: np.ndarray, stats: dict) -> np.ndarray:
    return (prices < stats["lo"]) | (prices > stats["hi"])


# ──────────────────────────────────────────────────────────────
# ASCII CHARTS
# ──────────────────────────────────────────────────────────────
HIST_WIDTH = 16   # characters for histogram
BOX_WIDTH  = 38   # characters for box plot

def ascii_hist(prices: np.ndarray, width: int = HIST_WIDTH) -> str:
    """
    Single-line Unicode block histogram using log-scale bins.
    Log scale handles skewed trade price distributions much better
    than linear — keeps the main cluster visible alongside outliers.
    """
    mn, mx = float(prices.min()), float(prices.max())
    if mn == mx or mn <= 0:
        return "█" * width
    bins   = np.exp(np.linspace(np.log(mn), np.log(mx), width + 1))
    counts, _ = np.histogram(prices, bins=bins)
    bars   = " ▁▂▃▄▅▆▇█"
    normed = counts / counts.max() if counts.max() > 0 else counts
    return "".join(bars[int(v * 8)] for v in normed)


def ascii_box(prices: np.ndarray, width: int = BOX_WIDTH,
              g_min: float | None = None, g_max: float | None = None) -> str:
    """
    Single-line box plot:  ──[  Q1 │ med │ Q3  ]──  ●
    g_min / g_max pin the scale across multiple commodities so they
    are visually comparable on the same axis.
    """
    lo_val = g_min if g_min is not None else float(prices.min())
    hi_val = g_max if g_max is not None else float(prices.max())
    span   = hi_val - lo_val or 1.0

    def sc(v: float) -> int:
        return max(0, min(width - 1, int((v - lo_val) / span * (width - 1))))

    q1  = float(np.percentile(prices, 25))
    q3  = float(np.percentile(prices, 75))
    med = float(np.median(prices))
    iqr = q3 - q1
    lo  = q1 - IQR_MULTIPLIER * iqr
    hi  = q3 + IQR_MULTIPLIER * iqr

    buf = [" "] * width
    for i in range(sc(max(lo, lo_val)), sc(q1)):          buf[i] = "─"
    for i in range(sc(q3) + 1, sc(min(hi, hi_val)) + 1): buf[i] = "─"
    buf[sc(q1)]  = "["
    buf[sc(q3)]  = "]"
    for i in range(sc(q1) + 1, sc(q3)):                  buf[i] = " "
    buf[sc(med)] = "│"

    outliers = prices[(prices < lo) | (prices > hi)]
    for p in outliers:
        buf[sc(p)] = "●"

    return "".join(buf)


def charts_sidebyside(prices: np.ndarray,
                      g_min: float | None = None,
                      g_max: float | None = None) -> str:
    """
    Returns:  HIST(16) ▕ BOX(38)
    Used for the compact one-line-per-commodity table.
    """
    h = ascii_hist(prices, HIST_WIDTH)
    b = ascii_box(prices, BOX_WIDTH, g_min, g_max)
    return f"{h} ▕ {b}"


# ──────────────────────────────────────────────────────────────
# OUTLIER DETECTION (per commodity, global IQR)
# ──────────────────────────────────────────────────────────────
def analyse_commodity(df_c: pd.DataFrame) -> dict:
    """
    Returns a result dict for one commodity.
    """
    prices = df_c["_unit_price"].dropna().values
    prices = prices[np.isfinite(prices) & (prices > 0)]

    if len(prices) < MIN_ROWS:
        return {"status": "LOW DATA", "n": len(prices)}

    st     = iqr_stats(prices)
    c_val  = cv(st)
    is_out = outlier_mask(prices, st)

    if c_val > MAX_CV and is_out.sum() == 0:
        status = "HIGH VAR"
    elif is_out.sum() > 0:
        status = "FLAGGED"
    else:
        status = "CLEAN"

    # Add outlier flag back to rows
    df_work = df_c[df_c["_unit_price"].notna()].copy()
    df_work = df_work[np.isfinite(df_work["_unit_price"]) & (df_work["_unit_price"] > 0)]
    df_work["_is_outlier"] = (
        (df_work["_unit_price"] < st["lo"]) | (df_work["_unit_price"] > st["hi"])
    )
    df_work["_outlier_dir"] = df_work.apply(
        lambda r: "HIGH" if r["_unit_price"] > st["hi"]
        else ("LOW" if r["_unit_price"] < st["lo"] else ""),
        axis=1
    )
    z_std = st["std"] if st["std"] > 0 else 1.0
    df_work["_z_score"] = (df_work["_unit_price"] - st["mean"]) / z_std

    return {
        "status":        status,
        "n":             st["n"],
        "stats":         st,
        "cv":            c_val,
        "n_outliers":    int(is_out.sum()),
        "pct_outliers":  round(is_out.sum() / len(prices) * 100, 1),
        "outlier_prices": df_work[df_work["_is_outlier"]]["_unit_price"].tolist(),
        "df_flagged":    df_work[df_work["_is_outlier"]].copy(),
        "df_all":        df_work,
    }


# ──────────────────────────────────────────────────────────────
# SUBGROUP ANALYSIS  (country / season breakdown for flagged rows)
# ──────────────────────────────────────────────────────────────
def subgroup_explanation(flagged_row: pd.Series, df_all: pd.DataFrame) -> str:
    """
    For one flagged row, checks whether its price looks normal within:
      - its Country subgroup
      - its Season subgroup
    Returns a short explanation string.
    """
    price   = flagged_row["_unit_price"]
    notes   = []

    for col, label in [("Country", "country"), ("_season", "season")]:
        val = flagged_row.get(col)
        if not val or pd.isna(val):
            continue
        sub = df_all[df_all[col] == val]["_unit_price"].dropna()
        sub = sub[np.isfinite(sub) & (sub > 0)]
        if len(sub) < MIN_SUBGROUP:
            notes.append(f"{label}: too few rows ({len(sub)}) to compare")
            continue
        st2 = iqr_stats(sub.values)
        if st2["lo"] <= price <= st2["hi"]:
            notes.append(f"normal within {label} ({val[:20]})")
        else:
            notes.append(f"outlier even within {label} ({val[:20]})")

    return "  |  ".join(notes) if notes else ""


# ──────────────────────────────────────────────────────────────
# SUBGROUP BREAKDOWN TABLE  (country prices for a commodity)
# ──────────────────────────────────────────────────────────────
def print_subgroup_table(df_all: pd.DataFrame, col: str, label: str, bu: str) -> None:
    groups = (
        df_all.groupby(col)["_unit_price"]
        .agg(n="count", median="median", min="min", max="max")
        .reset_index()
        .rename(columns={col: label})
        .sort_values("median", ascending=False)
    )
    groups = groups[groups["n"] >= MIN_SUBGROUP]
    if groups.empty:
        print(f"     No subgroups with >= {MIN_SUBGROUP} rows.")
        return
    print(f"     {label:<22} {'n':>4}  {'median $/'+bu:<14}  {'min':>10}  {'max':>10}")
    print("     " + "─" * 66)
    for _, r in groups.iterrows():
        print(f"     {str(r[label])[:22]:<22} {int(r['n']):>4}  "
              f"{r['median']:>12.4f}  {r['min']:>10.4f}  {r['max']:>10.4f}")


# ──────────────────────────────────────────────────────────────
# MAIN REPORT
# ──────────────────────────────────────────────────────────────
def run_chapter_report(df: pd.DataFrame, chapter: str, chapter_name: str) -> None:

    W  = 90
    S1 = "═" * W
    S2 = "─" * W
    S3 = "·" * W

    df_ch = df[df["_hs_chapter"] == chapter].copy()
    df_ch = df_ch[df_ch["_conversion_status"] == "OK"]
    df_ch = df_ch[df_ch["_unit_price"].notna()]
    df_ch = df_ch[np.isfinite(df_ch["_unit_price"]) & (df_ch["_unit_price"] > 0)]

    # ── HEADER ────────────────────────────────────────────────
    print("\n" + S1)
    print(f"  CHAPTER {chapter}  —  {chapter_name.upper()}")
    print(S1)

    if df_ch.empty:
        print("\n  No rows with valid unit prices for this chapter.\n")
        return

    # ── SECTION 1: CHAPTER SUMMARY ────────────────────────────
    all_comms   = df_ch["Commodity"].unique()
    n_comms     = len(all_comms)
    n_rows      = len(df_ch)
    n_countries = df_ch["Country"].nunique()
    n_seasons   = df_ch["_season"].nunique()

    # Unit breakdown
    unit_counts = df_ch["_base_unit"].value_counts()

    print(f"\n  {n_comms} commodities  •  {n_rows} rows with valid price  "
          f"•  {n_countries} destination countries")
    print(f"  Units: " +
          "  |  ".join(f"{bu}: {cnt} rows" for bu, cnt in unit_counts.items()))
    print(f"  Seasons in data: {sorted(df_ch['_season'].unique())}")
    print()

    # ── SECTION 2: COMMODITY OVERVIEW TABLE ───────────────────
    print(S2)
    print("  COMMODITY OVERVIEW")
    print(S2)
    print()

    results = {}
    for commodity in sorted(all_comms):
        df_c = df_ch[df_ch["Commodity"] == commodity].copy()
        results[commodity] = analyse_commodity(df_c)

    # Summary counts
    status_counts = defaultdict(int)
    for r in results.values():
        status_counts[r["status"]] += 1
    total_flagged = sum(r.get("n_outliers", 0) for r in results.values())
    total_valid   = sum(r.get("n", 0) for r in results.values())
    pct_flagged   = round(total_flagged / total_valid * 100, 1) if total_valid else 0

    print(f"  {'Status':<12} {'Count':>6}    Description")
    print("  " + "─" * 60)
    for st, cnt in sorted(status_counts.items()):
        desc = {
            "FLAGGED":  "commodities with price outliers",
            "CLEAN":    "commodities with no outliers detected",
            "HIGH VAR": f"commodities with CV > {MAX_CV} (too variable for reliable detection)",
            "LOW DATA": f"commodities with < {MIN_ROWS} valid rows (skipped)",
        }.get(st, "")
        print(f"  {st:<12} {cnt:>6}    {desc}")

    print()
    print(f"  Total valid rows : {total_valid:,}")
    print(f"  Total flagged    : {total_flagged:,}  ({pct_flagged}% of valid rows)")
    print()

    # Commodity table
    short_name = lambda c: (c.split(" - ", 1)[1] if " - " in c else c)[:45]
    bu_for     = lambda c: (
        df_ch[df_ch["Commodity"] == c]["_base_unit"].mode()[0]
        if not df_ch[df_ch["Commodity"] == c]["_base_unit"].mode().empty else "?"
    )

    print(f"  {'Commodity':<47} {'unit':>6} {'n':>5}  {'median':>10}  {'CV':>6}  "
          f"{'flags':>6}  {'status'}")
    print("  " + "─" * W)

    for commodity in sorted(all_comms, key=lambda c: results[c]["status"]):
        r  = results[commodity]
        bu = bu_for(commodity)
        sn = short_name(commodity)

        if r["status"] == "LOW DATA":
            print(f"  {sn:<47} {bu:>6} {r['n']:>5}  {'—':>10}  {'—':>6}  "
                  f"{'—':>6}  LOW DATA")
            continue

        st  = r["stats"]
        med = f"{st['median']:.4f}"
        c_v = f"{r['cv']:.2f}"
        fl  = str(r["n_outliers"]) if r["n_outliers"] > 0 else "—"
        pct = f" ({r['pct_outliers']}%)" if r["n_outliers"] > 0 else ""

        marker = " ◄" if r["status"] == "FLAGGED" else ""
        print(f"  {sn:<47} {bu:>6} {r['n']:>5}  {med:>10}  {c_v:>6}  "
              f"{fl+pct:>6}  {r['status']}{marker}")

    print()

    # ── SECTION 3: PER-COMMODITY DETAIL ───────────────────────
    detail_comms = [c for c in all_comms
                    if results[c]["status"] in ("FLAGGED", "CLEAN")]

    if not detail_comms:
        print(S3)
        print("  No commodities with enough data to show detail.")
        print(S3)
    elif len(all_comms) > MAX_DETAIL_COMMS:
        # Compact one-line-per-commodity table with HIST ▕ BOX
        print(S2)
        print("  PRICE DISTRIBUTIONS")
        print(f"  Name (43 chars)                            "
              f"HIST (log bins) ▕ BOX [Q1│med│Q3] ● outlier")
        print(f"  {'─'*43}  {'─'*HIST_WIDTH} ▕ {'─'*BOX_WIDTH}")
        print()

        # Global price range for comparable box plot scale
        all_prices = np.concatenate([
            results[c]["df_all"]["_unit_price"].values
            for c in detail_comms if "df_all" in results[c]
        ])
        all_prices = all_prices[np.isfinite(all_prices) & (all_prices > 0)]
        g_min = float(all_prices.min()) if len(all_prices) else 0
        g_max = float(all_prices.max()) if len(all_prices) else 1

        for commodity in sorted(detail_comms,
                                 key=lambda c: -results[c].get("n_outliers", 0)):
            r  = results[commodity]
            bu = bu_for(commodity)
            sn = short_name(commodity)
            prices = r["df_all"]["_unit_price"].values
            prices = prices[np.isfinite(prices) & (prices > 0)]

            chart = charts_sidebyside(prices, g_min, g_max)
            flag  = (f"  ● {r['n_outliers']} flag{'s' if r['n_outliers']>1 else ''}"
                     if r["n_outliers"] > 0 else "")
            print(f"  {sn[:43]:<43}  {chart}{flag}")

        print()
        print(f"  Box scale: min={g_min:.4f}  max={g_max:.4f}   $/{bu}")
        print(f"  Hist scale: log bins per commodity (each histogram is self-scaled)")
        print()

    else:
        # Full per-commodity blocks with HIST + BOX side by side
        print(S2)
        print("  PER-COMMODITY ANALYSIS")
        print(S2)

        for commodity in sorted(detail_comms,
                                 key=lambda c: -results[c].get("n_outliers", 0)):
            r      = results[commodity]
            st     = r["stats"]
            bu     = bu_for(commodity)
            sn     = short_name(commodity)
            df_all = r["df_all"]
            prices = df_all["_unit_price"].values
            prices = prices[np.isfinite(prices) & (prices > 0)]

            print()
            print(f"  ┌─ {sn}")
            print(f"  │  n={st['n']}  median={st['median']:.4f} $/{bu}  "
                  f"CV={r['cv']:.2f}  "
                  f"fences=[{st['lo']:.4f} … {st['hi']:.4f}]  "
                  f"outliers={r['n_outliers']}")

            # HIST and BOX side by side on one line
            h = ascii_hist(prices, HIST_WIDTH)
            b = ascii_box(prices, BOX_WIDTH)
            print(f"  │  {h} ▕ {b}")

            # Axis labels: min and max aligned under each chart
            mn_s = f"{st['min']:.3f}"
            mx_s = f"{st['max']:.3f}"
            hist_axis = f"{mn_s:<{HIST_WIDTH}}"
            box_axis_pad = BOX_WIDTH - len(mn_s) - len(mx_s)
            box_axis  = f"{mn_s}{' ' * max(0, box_axis_pad)}{mx_s}"
            print(f"  │  {hist_axis} ▕ {box_axis}   $/{bu}")
            print("  │")

            # Country breakdown (if enough data)
            country_groups = df_all.groupby("Country").size()
            has_country_data = (country_groups >= MIN_SUBGROUP).sum() >= 2
            if has_country_data:
                print(f"  │  By country  (groups with >= {MIN_SUBGROUP} rows):")
                print_subgroup_table(df_all, "Country", "Country", bu)
                print("  │")

            # Season breakdown (if enough data)
            season_groups = df_all.groupby("_season").size()
            has_season_data = (season_groups >= MIN_SUBGROUP).sum() >= 2
            if has_season_data:
                print(f"  │  By season  (groups with >= {MIN_SUBGROUP} rows):")
                print_subgroup_table(df_all, "_season", "Season", bu)
                print("  │")

            if r["n_outliers"] == 0:
                print(f"  └─ CLEAN — no outliers detected")
            else:
                print(f"  └─ {r['n_outliers']} FLAGGED row{'s' if r['n_outliers']>1 else ''}")

    # ── SECTION 4: FLAGGED ROWS DETAIL ────────────────────────
    flagged_list = [r["df_flagged"] for r in results.values()
                    if r.get("n_outliers", 0) > 0 and "df_flagged" in r]

    if not flagged_list:
        print(S3)
        print("  No flagged rows in this chapter.")
        print(S3 + "\n")
        return

    all_flagged = pd.concat(flagged_list, ignore_index=True)

    if all_flagged.empty:
        print(S3)
        print("  No flagged rows in this chapter.")
        print(S3 + "\n")
        return

    all_flagged_merged = all_flagged.merge(
        df_ch[["Commodity","Country","Province","State","Period","_season",
               "_qty_normalised","_base_unit","Quantity","Unit of measure",
               "Value ($)"]].drop_duplicates(),
        on="Commodity", how="left", suffixes=("", "_orig")
    ) if "Country" not in all_flagged.columns else all_flagged

    print(S2)
    print(f"  FLAGGED ROWS — {len(all_flagged)} total")
    print(S2)
    print()

    display_cols = [c for c in [
        "Commodity", "Period", "_season", "Country", "Province",
        "Quantity", "Unit of measure", "_qty_normalised", "_base_unit",
        "Value ($)", "_unit_price", "_z_score", "_outlier_dir",
    ] if c in all_flagged.columns]

    for _, row in all_flagged.sort_values("_z_score", key=abs, ascending=False).iterrows():
        commodity = row.get("Commodity", "?")
        sn        = short_name(commodity)
        bu        = row.get("_base_unit", "?")
        price     = row.get("_unit_price")
        z         = row.get("_z_score")
        direction = "OVERPRICED" if row.get("_outlier_dir") == "HIGH" else "UNDERPRICED"
        r_stats   = results.get(commodity, {}).get("stats", {})
        df_all    = results.get(commodity, {}).get("df_all", pd.DataFrame())

        print(f"  ● {direction}  |z|={abs(z):.2f}")
        print(f"    {sn}")
        print(f"    Period   : {row.get('Period','?')}  ({row.get('_season','?')})")
        print(f"    Country  : {row.get('Country','?')}")
        print(f"    Qty      : {row.get('Quantity','?')} [{row.get('Unit of measure','?')}]")
        if pd.notna(price):
            print(f"    Price    : {price:.4f} $/{bu}  "
                  f"(group median={r_stats.get('median',float('nan')):.4f}  "
                  f"fence=[{r_stats.get('lo',float('nan')):.4f} … "
                  f"{r_stats.get('hi',float('nan')):.4f}])")
        # Subgroup explanation
        if not df_all.empty:
            expl = subgroup_explanation(row, df_all)
            if expl:
                print(f"    Context  : {expl}")
        print()

    print(S1 + "\n")


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Module 6c — Chapter-level price drill-down report"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--chapter", "-c",
                       help="HS chapter to analyse: 2-digit number (e.g. 08) or keyword (e.g. fruit)")
    group.add_argument("--list", "-l", action="store_true",
                       help="List all available HS chapters and exit")
    parser.add_argument("--file", "-f", default=str(NORMALISED_FILE),
                        help=f"Path to normalised CSV (default: {NORMALISED_FILE})")
    args = parser.parse_args()

    filepath = Path(args.file)
    print(f"\nLoading: {filepath}")
    try:
        df = load_normalised(filepath)
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    print(f"Loaded {len(df):,} rows.\n")

    if args.list:
        list_chapters(df)
        sys.exit(0)

    try:
        chapter, chapter_name = resolve_chapter(args.chapter, df)
    except ValueError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    run_chapter_report(df, chapter, chapter_name)


if __name__ == "__main__":
    main()
