import pandas as pd
from .utils import HS2_LABELS

# ── Load ───────────────────────────────────────────────────────────────────────
df = pd.read_parquet("Dataset/Dataset.parquet", engine="pyarrow")

for col in ['Commodity', 'Province', 'Country', 'trade_type']:
    df[col] = df[col].astype('category')

df['Year']  = df['Period'].dt.year
df['Month'] = df['Period'].dt.month
df['HS2'] = df['Commodity'].astype(str).str[:2]
df['HS2'] = df['HS2'].astype('category')


# ── Pre-aggregated summary for KPIs (faster filtering) ────────────────────────
df_kpi = df.groupby(
    ['Period', 'HS2', 'Province', 'Country', 'trade_type'],
    observed=True
)['Value ($)'].sum().reset_index()

# ── Dropdown option lists ──────────────────────────────────────────────────────
year_options      = sorted(df['Year'].unique().tolist())

province_options  = sorted(df['Province'].cat.categories.tolist())
country_options   = sorted(df['Country'].cat.categories.tolist())
date_range_label  = f"{df['Period'].min().strftime('%b %Y')} – {df['Period'].max().strftime('%b %Y')}"

hs2_options = sorted(df['HS2'].cat.categories.tolist())
hs2_options_labeled = [
    {'label': f"{code} – {HS2_LABELS.get(code, 'Other')}", 'value': code}
    for code in hs2_options
]

# ── Period slider ──────────────────────────────────────────────────────
periods = sorted(df['Period'].dt.to_period('M').unique())
period_labels = [p.strftime('%b %Y') for p in periods]  # ['Jan 2024', 'Feb 2024', ...]
period_index  = {i: p for i, p in enumerate(periods)}   # {0: Period('2024-01'), ...}