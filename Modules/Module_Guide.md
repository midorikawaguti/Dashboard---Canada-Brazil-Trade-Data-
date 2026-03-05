# Module Guide — Canadian Export Data Analysis

## Overview

The modules run in two phases:

**Phase 1 — Data Quality (Modules 1–5)**
Check that the raw CSV files are clean and trustworthy before any analysis.
These all read directly from `Dataset/Exports/`.

**Phase 2 — Price Analysis (Modules 6a, 6b, 6c)**
Normalise units, detect price anomalies, and drill into specific product categories.
These read from `Dataset/Normalised/` (created by Module 6a).

---

## How to Run

Open Terminal, navigate to your project folder, then run in order:

```bash
cd /Users/midorikawaguti/DevProject/Dashboard-BR-CA

# Phase 1 — run any or all of these
jupyter notebook   # then open each .ipynb file and run it

# Phase 2
python3 module_6a_normalise.py        # must run first
python3 module_6b_outliers.py         # optional
python3 module_6c_chapter.py --list   # then pick a chapter
python3 module_6c_chapter.py --chapter 22
```

---

## Module 1 — Schema Validation

**What it checks:** Do all 146 CSV files have the right columns in the right format?

**Specifically:**
- Are all 8 expected columns present? (`Period`, `Commodity`, `Province`, `Country`, `State`, `Value ($)`, `Quantity`, `Unit of measure`)
- Are there any unexpected extra columns?
- Can `Period` be parsed as a date?
- Can `Value ($)` and `Quantity` be parsed as numbers?

**How to interpret the output:**

| Status | Meaning |
|--------|---------|
| ✅ OK | No problems found |
| ⚠️ WARN | Minor issue — worth checking but not blocking |
| ❌ FAIL | Serious problem — files may not load correctly in later modules |

If you see a FAIL on column names, check whether Statistics Canada changed the file format in a specific month. The detail column will tell you exactly which columns are missing or renamed.

**What to do with failures:** Note which files are affected. You may need to rename columns or check if a file was downloaded incorrectly.

---

## Module 2 — Missing Values

**What it checks:** Are there blank cells in the key columns across all files?

**Specifically checks for missing values in:**
- `Period` — if blank, the row has no date and can't be placed in time
- `Commodity` — if blank, the row has no product and is unusable
- `Province` — if blank, origin is unknown
- `Country` — if blank, destination is unknown

**How to interpret the output:**

The module prints a count and percentage of missing values per column, plus example rows showing which files and records are affected.

- A small number of missing `State` values is normal — not all exports go to a US state (e.g. exports to Germany have no state).
- Missing `Commodity` or `Period` is a real problem — those rows cannot be used in any downstream analysis.
- The examples section shows you the actual rows so you can judge whether it's a systematic file issue or a one-off.

**What to do with failures:** Missing values in `Commodity` or `Period` should be investigated. Check if a specific file has formatting issues.

---

## Module 3 — Duplicate Detection

**What it checks:** Are there duplicate rows that would inflate counts and values?

A duplicate is defined as two rows with identical values in all five key columns: `Period`, `Commodity`, `Province`, `Country`, `State`.

**How to interpret the output:**

The module tells you how many exact duplicate rows exist and shows examples. For trade data, a true duplicate almost certainly means the same file was loaded twice, or a row was accidentally repeated.

- If duplicates are found in the same `_source_file`, the file itself has repeated rows.
- If duplicates appear across two different `_source_file` values, a monthly file may have been included twice in your dataset folder.

**What to do with failures:** Check the `_source_file` column in the examples. If it's the same file twice, the source file has an error. If it's two different files, check whether you have overlapping monthly files (e.g. both a provisional and a revised version of the same month).

---

## Module 4 — Value & Quantity Consistency

**What it checks:** Are the numbers in `Value ($)` and `Quantity` sensible?

**Specifically:**
- **Negative values** — export values and quantities should never be negative
- **Zero values** — zero quantity with a non-zero value is suspicious; flagged as a warning
- **Invalid dates** — `Period` values that can't be parsed
- **Future dates** — records dated beyond today

**How to interpret the output:**

| Finding | What it means |
|---------|--------------|
| Negative `Value ($)` | Likely a data entry error or a correction/reversal entry |
| Negative `Quantity` | Same — should not occur in export data |
| Zero `Quantity` with Value > 0 | Statistics Canada uses "Blank" unit for some HS codes — these are expected and handled in Module 6a |
| Future dates | File may have been mis-dated or contain projected data |

**What to do with failures:** Negative values are worth flagging for manual review. Zero quantity rows with a value are normal if the unit is "Blank" — Module 6a handles these correctly and gives them a `BLANK_UNIT` status rather than treating them as errors.

---

## Module 5 — Unit of Measure Consistency

**What it checks:** Does each commodity always use the same unit, or does it switch between units across different records?

For example, hydrogen (HS 2804.10.00) appears in both `Weight in kilograms` and `Volume in cubic metres` depending on how it was shipped. This is a real data issue because you can't compare prices if the units differ.

**How to interpret the output:**

The module reports how many commodities have more than one unit of measure, and shows a breakdown of how many rows use each unit.

- **9 commodities with multiple units (0.16%)** — as shown in your output, this is a small but real issue.
- The breakdown table shows which unit is dominant (more rows) vs minor (fewer rows).
- Some are physically meaningful: radioactive elements measured in both megabecquerels and gigabecquerels is not a problem — Module 6a converts both to GBq.
- Others like hydrogen in kg vs cubic metres represent genuinely different ways of measuring the same product — prices per kg and prices per cubic metre are not comparable.

**What to do with findings:** Module 6a already handles this — it converts all weight units to kg and all volume units to litres. After normalisation, a cross-dimension check tells you which commodities still appear in multiple physical dimensions (weight AND volume). Those are the ones to watch in Module 6c.

---

## Module 6a — Unit Conversion & Price Normalisation

**What it does:** Converts all quantities to a common base unit and computes a unit price for every row.

**Conversions applied:**
- All weight units → **kg** (grams, metric tonnes, carats all converted)
- All volume units → **litre** (cubic metres, litres of pure alcohol all converted)
- All count units → **count** (dozens × 12, gross × 144, etc.)
- Area → **m²**, Length → **m**, Energy → **MWh**

**Output file:** `Dataset/Normalised/prices_normalised.csv`

**How to interpret the output:**

The summary printed to the screen shows:

| Status | Meaning |
|--------|---------|
| OK | Unit price successfully computed |
| BLANK_UNIT | Statistics Canada did not record a quantity for this HS code — normal, not an error |
| EXCLUDED (radioactivity) | Radioactive materials — excluded from price analysis |
| WARN — unknown unit | A unit label not in the conversion table — needs to be added |
| WARN — zero/negative qty | Quantity is zero or negative after conversion |

The **verification table** (Section 4) is the most important thing to read. It shows 3 example rows per unit type. Check that the normalised quantity and unit price look correct — for example, 1 metric tonne at $1,000 should produce the same $/kg as 1,000 kg at $1,000. If something looks wrong here, stop and check before running later modules.

**You need to run this once.** After that, Modules 6b and 6c read the saved CSV directly — you don't need to re-run 6a unless you add new monthly files.

---

## Module 6b — Outlier Detection

**What it does:** Flags rows where the unit price looks anomalous compared to other records of the same commodity.

**Method:**
- Groups rows by `(Commodity × Season)` — if the group has ≥ 8 rows
- Falls back to global `(Commodity)` if fewer than 8 rows in that season
- Uses IQR × 3.0 to set fences (lenient — only catches genuine extremes)
- Escalates severity using Z-score

**Output file:** `Dataset/Normalised/outliers_flagged.csv`

**How to interpret severity:**

| Severity | Z-score | Meaning |
|----------|---------|---------|
| MEDIUM | outside IQR fence | Unusual but could be legitimate |
| HIGH | \|z\| ≥ 3.0 | Very unusual — worth investigating |
| CRITICAL | \|z\| ≥ 4.0 | Extreme — very likely a data error or exceptional event |

**The seasonal risk tag** marks commodities in HS chapters 01–16, 22, and 27 (food, agriculture, fish, fuel). A MEDIUM flag on strawberries in December is more explainable than the same flag on steel in July — the seasonal risk tag reminds you to consider that before escalating.

**What to do with this file:** Don't treat every flag as an error. The purpose is to surface rows that deserve a second look. A CRITICAL flag on a pharmaceutical product exported to one country at 10× the median price might be a legitimate transfer price — or it might be a data entry error with an extra zero.

---

## Module 6c — Chapter Drill-Down Report

**What it does:** Lets you explore one HS chapter at a time with a full breakdown of commodities, price distributions, and flagged rows.

**How to run:**
```bash
python3 module_6c_chapter.py --list              # see all chapters
python3 module_6c_chapter.py --chapter 22        # by number
python3 module_6c_chapter.py --chapter beverages # by keyword
python3 module_6c_chapter.py --chapter 22 | less # scroll through output
```

**The four sections of the report:**

**1. Chapter Summary**
One-line overview: how many commodities, rows, countries, and what units are used.

**2. Commodity Overview Table**
Every commodity in the chapter, one row each. The columns to focus on:

| Column | What it tells you |
|--------|------------------|
| `n` | How many rows — low n means statistics are unreliable |
| `median` | The typical unit price for this commodity |
| `CV` | Coefficient of variation — how spread out prices are. CV < 0.5 = tight (reliable outlier detection). CV > 1.0 = very variable (flags may be noise) |
| `flags` | Number of flagged rows and % of total |
| `status` | FLAGGED / CLEAN / HIGH VAR / LOW DATA |

**3. Price Distributions**
Each commodity gets two charts side by side:

```
Non-alcoholic beer   ▂ ▁█ ▁ ▂      ▁▂ ▕ │]─ ●●     ● 3 flags
```

- **Left side (HIST):** histogram using log-scale bins — shows where most prices cluster and whether there are outliers far from the main group
- **Right side (BOX):** box plot — `[` is the 25th percentile, `│` is the median, `]` is the 75th percentile, `─` are the whiskers, `●` are flagged outliers
- All box plots share the same scale across the chapter so you can compare price levels between commodities

**4. Flagged Rows Detail**
Every flagged row with full context:
- The price, the group median, and the IQR fences
- The `Context` line is key — it tells you whether the price is also unusual within its country or season subgroup:
  - `outlier even within country (United States)` — flag is robust, worth investigating
  - `normal within country (United States)` — this country simply pays more; may not be an error

---

## Recommended Workflow

```
Run Module 1  →  Are the files loading correctly?
Run Module 2  →  Any columns with too many blanks?
Run Module 3  →  Any duplicate files accidentally included?
Run Module 4  →  Any negative or impossible values?
Run Module 5  →  Any commodities with inconsistent units?
                     ↓ (fix any critical issues found above)
Run Module 6a →  Normalise units, verify the conversion table
Run Module 6c →  Pick chapters of interest and drill in
                 Focus on FLAGGED rows with low CV and high |z|
                 Use the Context line to judge each flag
```

Module 6b is optional — its `outliers_flagged.csv` output is not used by Module 6c. It's useful if you want a single flat file of all flagged rows across all chapters for further analysis in Excel or another tool.
