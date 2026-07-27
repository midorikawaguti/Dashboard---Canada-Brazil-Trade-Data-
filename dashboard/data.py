import pandas as pd
from .utils import HS2_LABELS

# ── Load ───────────────────────────────────────────────────────────────────────
df = pd.read_parquet("Dataset/Dataset.parquet", engine="pyarrow")

# Ensure category dtypes
for col in ['Commodity', 'Province', 'Country', 'trade_type']:
    if col in df.columns and df[col].dtype.name != 'category':
        df[col] = df[col].astype('category')

df['Year']  = df['Period'].dt.year
df['Month'] = df['Period'].dt.month
df['HS2']   = df['Commodity'].astype(str).str[:2].astype('category')

# ── Pre-aggregated KPI summary (HS2 level — lightweight) ──────────────────────
# Drops Commodity column → much smaller groupby
df_kpi = (
    df.groupby(
        ['Period', 'HS2', 'Province', 'Country', 'trade_type'],
        observed=True
    )['Value ($)'].sum()
    .reset_index()
)

# ── df_kpi_commodity removed — computed on demand in callbacks ─────────────────
# Previously this was a groupby on Commodity (~50k unique values × 12M rows)
# which caused OOM. Callbacks that need it filter df directly.
df_kpi_commodity = df_kpi   # alias — keeps callbacks that reference it working

# ── HS2 Section mapping ────────────────────────────────────────────────────────
hs2_sections       = pd.read_csv("Dataset/HS2_Sections_With_Descriptions.csv")
hs2_sections['HS2_Code'] = hs2_sections['HS2_Code'].astype(str).str.zfill(2)
hs2_to_section     = dict(zip(hs2_sections['HS2_Code'], hs2_sections['Section']))
hs2_to_description = dict(zip(hs2_sections['HS2_Code'], hs2_sections['HS2_Description']))

# ── Dropdown option lists ──────────────────────────────────────────────────────
year_options     = sorted(df['Year'].unique().tolist())
province_options = sorted(df['Province'].cat.categories.tolist())
country_options  = sorted(df['Country'].cat.categories.tolist())
date_range_label = (
    f"{df['Period'].min().strftime('%b %Y')} – "
    f"{df['Period'].max().strftime('%b %Y')}"
)

hs2_options = sorted(df['HS2'].cat.categories.tolist())
hs2_options_labeled = [
    {'label': f"{code} – {HS2_LABELS.get(code, 'Other')}", 'value': code}
    for code in hs2_options
]

# ── Period slider ──────────────────────────────────────────────────────────────
periods       = sorted(df['Period'].dt.to_period('M').unique())
period_labels = [p.strftime('%b %Y') for p in periods]
period_index  = {i: p for i, p in enumerate(periods)}

default_start_index = next(
    (i for i, p in period_index.items() if str(p) == '2025-01'),
    0
)