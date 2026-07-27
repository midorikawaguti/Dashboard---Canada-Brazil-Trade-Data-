import numpy as np
import pandas as pd
import calendar
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .utils import fmt_value, HS2_LABELS

# ── Internal helper ────────────────────────────────────────────────────────────
def _fmt(value):
    abs_val = abs(value)
    if abs_val >= 1_000_000_000:
        return f'${value/1_000_000_000:.1f}B'
    elif abs_val >= 1_000_000:
        return f'${value/1_000_000:.1f}M'
    elif abs_val >= 1_000:
        return f'${value/1_000:.1f}K'
    return f'${value:.1f}'

# ── Colour constants ───────────────────────────────────────────────────────────
EXPORT_COLOR = '#52B788'
IMPORT_COLOR = '#1A4731'
COLORS_10 = [
    '#264653', '#2A9D8F', '#52B788', '#84A59D', '#E9C46A',
    '#F4A261', '#E76F51', '#D62828', '#6D597A', '#457B9D',
]


# ══════════════════════════════════════════════════════════════════════════════
# TRADE TREND — diverging bar + balance line
# ══════════════════════════════════════════════════════════════════════════════
def build_monthly_chart(filtered_df):
    monthly = (
        filtered_df
        .groupby([
            filtered_df['Period'].dt.year.rename('year'),
            filtered_df['Period'].dt.month.rename('month'),
            'trade_type'
        ])['Value ($)']
        .sum()
        .reset_index()
    )

    pivot = monthly.pivot_table(
        index=['year', 'month'], columns='trade_type',
        values='Value ($)', aggfunc='sum'
    ).fillna(0).reset_index()
    pivot.columns.name = None
    pivot = pivot.rename(columns={'Export': 'exports', 'Import': 'imports'})

    if 'exports' not in pivot.columns:
        pivot['exports'] = 0
    if 'imports' not in pivot.columns:
        pivot['imports'] = 0

    pivot['balance'] = pivot['exports'] - pivot['imports']
    pivot = pivot.sort_values(['year', 'month']).reset_index(drop=True)
    pivot['label'] = pivot.apply(
        lambda r: f"{calendar.month_abbr[int(r['month'])]} {int(r['year'])}", axis=1
    )

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=pivot['label'], y=pivot['exports'],
        name='Exports', marker_color=EXPORT_COLOR,
    ))
    fig.add_trace(go.Bar(
        x=pivot['label'], y=-pivot['imports'],
        name='Imports', marker_color=IMPORT_COLOR,
    ))
    fig.add_trace(go.Scatter(
        x=pivot['label'], y=pivot['balance'] / 1e9,
        name='Balance', line=dict(color='black', width=2),
        marker=dict(size=4), yaxis='y2'
    ))

    max_val = max(pivot['exports'].max(), pivot['imports'].max())
    max_bal = pivot['balance'].abs().max() / 1e9
    tick_vals_both = np.linspace(-max_val, max_val, 9)

    fig.update_layout(
        barmode='overlay',
        yaxis=dict(
            title='Trade Value (CAD)',
            tickvals=tick_vals_both,
            ticktext=[fmt_value(abs(v)) for v in tick_vals_both],
            zeroline=True, zerolinecolor='black', zerolinewidth=1,
        ),
        yaxis2=dict(
            title='Balance (CAD $B)',
            overlaying='y', side='right',
            tickvals=np.linspace(-max_bal, max_bal, 9),
            ticktext=[fmt_value(abs(v) * 1e9) for v in np.linspace(-max_bal, max_bal, 9)],
        ),
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        template='plotly_white',
        margin=dict(t=40, b=40),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# TOP COMMODITIES TABLE
# ══════════════════════════════════════════════════════════════════════════════
def build_top_commodity_table(filtered_df):
    grouped = (
        filtered_df
        .groupby(['Commodity', 'trade_type'], observed=True)['Value ($)']
        .sum()
        .reset_index()
    )
    pivot = grouped.pivot_table(
        index='Commodity', columns='trade_type',
        values='Value ($)', aggfunc='sum'
    ).fillna(0).reset_index()
    pivot.columns.name = None

    if 'Export' not in pivot.columns:
        pivot['Export'] = 0
    if 'Import' not in pivot.columns:
        pivot['Import'] = 0

    pivot['Total'] = pivot['Export'] + pivot['Import']
    pivot = pivot.nlargest(10, 'Total').reset_index(drop=True)

    total_all = pivot['Total'].sum()
    pivot['Share %'] = (pivot['Total'] / total_all * 100).round(1)
    pivot['Rank'] = pivot.index + 1

    table_df = pd.DataFrame({
        '#':           pivot['Rank'],
        'Commodity':   pivot['Commodity'],
        'Exports':     pivot['Export'].apply(fmt_value),
        'Imports':     pivot['Import'].apply(fmt_value),
        'Total Trade': pivot['Total'].apply(fmt_value),
        'Share %':     pivot['Share %'].astype(str) + '%',
    })
    return table_df.to_dict('records')


# ══════════════════════════════════════════════════════════════════════════════
# TOP COUNTRIES TABLE
# ══════════════════════════════════════════════════════════════════════════════
def build_top_countries_table(filtered_df):
    grouped = (
        filtered_df
        .groupby(['Country', 'trade_type'], observed=True)['Value ($)']
        .sum()
        .reset_index()
    )
    pivot = grouped.pivot_table(
        index='Country', columns='trade_type',
        values='Value ($)', aggfunc='sum'
    ).fillna(0).reset_index()
    pivot.columns.name = None

    if 'Export' not in pivot.columns:
        pivot['Export'] = 0
    if 'Import' not in pivot.columns:
        pivot['Import'] = 0

    pivot['Total'] = pivot['Export'] + pivot['Import']
    pivot = pivot.nlargest(10, 'Total').reset_index(drop=True)

    total_all = pivot['Total'].sum()
    pivot['Share %'] = (pivot['Total'] / total_all * 100).round(1)
    pivot['Rank'] = pivot.index + 1

    table_df = pd.DataFrame({
        '#':           pivot['Rank'],
        'Country':     pivot['Country'],
        'Exports':     pivot['Export'].apply(fmt_value),
        'Imports':     pivot['Import'].apply(fmt_value),
        'Total Trade': pivot['Total'].apply(fmt_value),
        'Share %':     pivot['Share %'].astype(str) + '%',
    })
    return table_df.to_dict('records')


# ══════════════════════════════════════════════════════════════════════════════
# TOP 5 EXPORT/IMPORT TABLES with YoY
# ══════════════════════════════════════════════════════════════════════════════
def build_top5_tables(filtered_df, full_df):
    """
    Returns (export_records, import_records).
    YoY compares selected period vs same months one year prior using full_df.
    """
    current_periods = filtered_df[['Period']].drop_duplicates().copy()
    current_periods['year']      = current_periods['Period'].dt.year
    current_periods['month']     = current_periods['Period'].dt.month
    current_periods['prev_year'] = current_periods['year'] - 1

    full_df = full_df.copy()
    full_df['year']  = full_df['Period'].dt.year
    full_df['month'] = full_df['Period'].dt.month

    prev_rows = []
    for _, row in current_periods.iterrows():
        match = full_df[
            (full_df['year']  == row['prev_year']) &
            (full_df['month'] == row['month'])
        ]
        prev_rows.append(match)

    expected_count = len(current_periods)
    prior_df       = pd.concat(prev_rows) if prev_rows else pd.DataFrame()
    found_count    = prior_df[['year', 'month']].drop_duplicates().shape[0] \
                     if not prior_df.empty else 0
    has_prior_year = (found_count == expected_count)

    def get_top5(trade_type):
        sub = filtered_df[filtered_df['trade_type'] == trade_type]
        total = (
            sub.groupby('Commodity', observed=True)['Value ($)']
            .sum().nlargest(5).reset_index()
        )

        yoy_map = {}
        if has_prior_year and not prior_df.empty:
            curr_totals = sub.groupby('Commodity', observed=True)['Value ($)'].sum()
            prev_totals = prior_df[prior_df['trade_type'] == trade_type] \
                          .groupby('Commodity', observed=True)['Value ($)'].sum()
            for c in total['Commodity']:
                if c in curr_totals.index and c in prev_totals.index \
                        and prev_totals[c] > 0:
                    yoy_map[c] = (curr_totals[c] - prev_totals[c]) / prev_totals[c] * 100
                else:
                    yoy_map[c] = None

        records = []
        for _, row in total.iterrows():
            c   = row['Commodity']
            yoy = yoy_map.get(c)
            if yoy is None and not has_prior_year:
                yoy_str = 'N/A'
            elif yoy is None:
                yoy_str = 'N/A'
            elif yoy >= 0:
                yoy_str = f'+{yoy:.0f}%'
            else:
                yoy_str = f'{yoy:.0f}%'

            name = (str(c)[:60] + '...') if len(str(c)) > 60 else str(c)
            records.append({
                'Commodity': name,
                'Value':     fmt_value(row['Value ($)']),
                'YoY':       yoy_str,
                '_yoy_val':  yoy,
            })
        return records

    return get_top5('Export'), get_top5('Import')


# ══════════════════════════════════════════════════════════════════════════════
# HS2 SHARE HORIZONTAL BAR
# ══════════════════════════════════════════════════════════════════════════════
def build_hs2_share_chart(filtered_df):
    total_all = filtered_df['Value ($)'].sum()
    if total_all == 0:
        return go.Figure()

    hs2 = (
        filtered_df
        .groupby('HS2', observed=True)['Value ($)']
        .sum().reset_index()
    )
    hs2['share'] = (hs2['Value ($)'] / total_all * 100).round(1)
    hs2['label'] = hs2['HS2'].apply(lambda x: HS2_LABELS.get(str(x), str(x)))
    hs2 = hs2.nlargest(10, 'share').sort_values('share')

    fig = go.Figure(go.Bar(
        x=hs2['share'],
        y=hs2['label'],
        orientation='h',
        text=hs2['share'].apply(lambda x: f'{x}%'),
        textposition='outside',
        marker_color=COLORS_10[:len(hs2)],
        # Store HS2 code in customdata so click callback can read it
        customdata=hs2['HS2'].tolist(),
        hovertemplate='<b>%{y}</b><br>Share: %{x}%<br>Click to filter<extra></extra>',
    ))
    fig.update_layout(
        xaxis=dict(visible=False, range=[0, hs2['share'].max() * 1.20]),
        yaxis=dict(tickfont=dict(size=12)),
        margin=dict(l=0, r=60, t=10, b=10),
        template='plotly_white',
        showlegend=False,
        clickmode='event+select',
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# PROVINCE SMALL MULTIPLES (4 donuts)
# ══════════════════════════════════════════════════════════════════════════════
def build_province_small_multiples(filtered_df):
    top4 = (
        filtered_df
        .groupby('Province', observed=True)['Value ($)']
        .sum().nlargest(4).index.tolist()
    )
    if not top4:
        return go.Figure()

    while len(top4) < 4:
        top4.append(None)

    fig = make_subplots(
        rows=1, cols=4,
        specs=[[{'type': 'domain'}] * 4],
        subplot_titles=[p if p else '' for p in top4],
    )

    # Collect total values to add as centre annotations after layout
    totals = []

    for i, province in enumerate(top4):
        col = i + 1
        if province is None:
            fig.add_trace(go.Pie(
                values=[1], labels=['No data'],
                marker_colors=['#E0E0E0'],
                hole=0.6, showlegend=False, textinfo='none',
            ), row=1, col=col)
            totals.append(None)
            continue

        sub     = filtered_df[filtered_df['Province'] == province]
        split   = sub.groupby('trade_type', observed=True)['Value ($)'].sum()
        exports = split.get('Export', 0)
        imports = split.get('Import', 0)
        total   = exports + imports
        totals.append(total)

        fig.add_trace(go.Pie(
            values=[exports, imports],
            labels=['Exports', 'Imports'],
            marker_colors=[EXPORT_COLOR, IMPORT_COLOR],
            hole=0.55,
            showlegend=(i == 0),
            textinfo='percent',
            textfont=dict(size=11),
            hovertemplate=(
                '<b>%{label}</b><br>'
                'Value: %{value:.2s}<br>'
                'Share: %{percent}<extra></extra>'
            ),
        ), row=1, col=col)

    # Build layout first so subplot title annotations are already set
    fig.update_layout(
        template='plotly_white',
        margin=dict(t=40, b=20, l=0, r=0),
        height=300,
        legend=dict(orientation='h', yanchor='bottom', y=-0.15,
                    xanchor='center', x=0.5),
    )

    # Style subtitle annotations (province names) — these are auto-generated
    # by make_subplots and sit at y≈1.0 in paper coords
    for ann in fig.layout.annotations:
        ann.font = dict(size=12, color='#1F4E79', family='Arial')

    # Add total value annotations centred inside each donut hole
    # x midpoints read directly from Plotly domain computation:
    # subplot 1=0.1062, 2=0.3688, 3=0.6313, 4=0.8938
    # y midpoint is always 0.5 (full height domain)
    X_MIDS = [0.1062, 0.3688, 0.6313, 0.8938]

    for i, total in enumerate(totals):
        if total is None:
            continue
        fig.add_annotation(
            text=f'<b>{fmt_value(total)}</b>',
            x=X_MIDS[i],
            y=0.5,
            xref='paper',
            yref='paper',
            xanchor='center',
            yanchor='middle',
            showarrow=False,
            font=dict(size=12, color='#1A1A1A', family='Arial'),
        )

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# TOP 5 PROVINCES BAR
# ══════════════════════════════════════════════════════════════════════════════
def build_top_provinces_bar(filtered_kpi):
    top = (
        filtered_kpi
        .groupby('Province', observed=True)['Value ($)']
        .sum().nlargest(5).reset_index()
        .sort_values('Value ($)', ascending=True)
    )
    if top.empty:
        return go.Figure()

    tick_vals = np.linspace(0, top['Value ($)'].max(), 5)
    fig = go.Figure(go.Bar(
        y=top['Province'], x=top['Value ($)'],
        orientation='h', marker_color='#457B9D',
        text=[_fmt(v) for v in top['Value ($)']],
        textposition='outside',
        hovertemplate='%{y}<br>%{x:.2s}<extra></extra>',
    ))
    fig.update_layout(
        xaxis=dict(tickvals=tick_vals, ticktext=[_fmt(v) for v in tick_vals],
                   visible=False),
        yaxis=dict(tickfont=dict(size=11)),
        template='plotly_white',
        margin=dict(t=10, b=10, l=0, r=60),
        height=240,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# TOP 10 PARTNERS BAR
# ══════════════════════════════════════════════════════════════════════════════
def build_top_partners_bar(filtered_kpi):
    top = (
        filtered_kpi
        .groupby('Country', observed=True)['Value ($)']
        .sum().nlargest(10).reset_index()
        .sort_values('Value ($)', ascending=True)
    )
    if top.empty:
        return go.Figure()

    tick_vals = np.linspace(0, top['Value ($)'].max(), 5)
    fig = go.Figure(go.Bar(
        y=top['Country'], x=top['Value ($)'],
        orientation='h', marker_color='#2A9D8F',
        text=[_fmt(v) for v in top['Value ($)']],
        textposition='outside',
        hovertemplate='%{y}<br>%{x:.2s}<extra></extra>',
    ))
    fig.update_layout(
        xaxis=dict(
            tickvals=tick_vals,
            ticktext=[_fmt(v) for v in tick_vals],
            visible=False,
            range=[0, top['Value ($)'].max() * 1.1],  # extra space for labels
        ),
        yaxis=dict(tickfont=dict(size=11)),
        template='plotly_white',
        margin=dict(t=10, b=10, l=0, r=10),
        height=320,  # match province donut chart height
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# HS2 TREEMAP — two-level: Section → HS2
# ══════════════════════════════════════════════════════════════════════════════
def build_hs2_treemap(filtered_kpi, hs2_to_section=None, hs2_to_description=None):
    hs2 = (
        filtered_kpi
        .groupby('HS2', observed=True)['Value ($)']
        .sum().reset_index()
    )
    if hs2.empty:
        return go.Figure()

    hs2['hs2_str'] = hs2['HS2'].astype(str).str.zfill(2)

    if hs2_to_section and hs2_to_description:
        # Two-level treemap: Section → HS2
        hs2['section']     = hs2['hs2_str'].map(hs2_to_section).fillna('Other')
        hs2['description'] = hs2['hs2_str'].map(hs2_to_description).fillna(hs2['hs2_str'])

        section_totals = hs2.groupby('section')['Value ($)'].sum().reset_index()
        total = hs2['Value ($)'].sum()

        labels  = section_totals['section'].tolist() + hs2['description'].tolist()
        parents = [''] * len(section_totals) + hs2['section'].tolist()
        values  = section_totals['Value ($)'].tolist() + hs2['Value ($)'].tolist()
        pcts    = [round(v / total * 100, 1) for v in values]
    else:
        # Flat treemap fallback using HS2_LABELS
        hs2['label'] = hs2['hs2_str'].apply(lambda x: HS2_LABELS.get(x, x))
        total  = hs2['Value ($)'].sum()
        labels  = hs2['label'].tolist()
        parents = [''] * len(hs2)
        values  = hs2['Value ($)'].tolist()
        pcts    = [(v / total * 100) for v in values]

    fig = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        customdata=pcts,
        texttemplate='<b>%{label}</b><br>%{customdata:.1f}%',
        hovertemplate=(
            '<b>%{label}</b><br>'
            'Value: %{value:.2s}<br>'
            'Share: %{customdata:.1f}%<extra></extra>'
        ),
        marker=dict(colorscale='Teal', showscale=False),
        textfont=dict(size=11, color='white'),
        branchvalues='total',
    ))
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        height=260,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# TRADE BALANCE BY PROVINCE — diverging bar
# ══════════════════════════════════════════════════════════════════════════════
def build_province_balance_bar(filtered_kpi):
    exports = (
        filtered_kpi[filtered_kpi['trade_type'] == 'Export']
        .groupby('Province', observed=True)['Value ($)'].sum()
    )
    imports = (
        filtered_kpi[filtered_kpi['trade_type'] == 'Import']
        .groupby('Province', observed=True)['Value ($)'].sum()
    )
    balance = (exports - imports).dropna().sort_values(ascending=False).reset_index()
    balance.columns = ['Province', 'Balance']

    if balance.empty:
        return go.Figure()

    colors = ['#52B788' if v >= 0 else '#C00000' for v in balance['Balance']]

    fig = go.Figure(go.Bar(
        x=balance['Province'],
        y=balance['Balance'],
        marker_color=colors,
        text=[_fmt(v) for v in balance['Balance']],
        textposition='outside',
        hovertemplate='%{x}<br>Balance: %{y:.2s}<extra></extra>',
    ))
    fig.update_layout(
        xaxis=dict(tickfont=dict(size=10)),
        yaxis=dict(
            zeroline=True, zerolinecolor='black', zerolinewidth=1,
            tickformat='~s', tickprefix='$',
        ),
        template='plotly_white',
        margin=dict(t=20, b=20, l=40, r=20),
        height=280,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# EXPORT DESTINATIONS BAR
# ══════════════════════════════════════════════════════════════════════════════
def build_export_destinations(filtered_df):
    sub = filtered_df[filtered_df['trade_type'] == 'Export']
    if sub.empty:
        return go.Figure()

    top = (
        sub.groupby('Country', observed=True)['Value ($)']
        .sum().nlargest(10).reset_index()
        .sort_values('Value ($)', ascending=True)
    )
    tick_vals = np.linspace(0, top['Value ($)'].max(), 5)
    fig = go.Figure(go.Bar(
        y=top['Country'], x=top['Value ($)'],
        orientation='h', marker_color=EXPORT_COLOR,
        hovertemplate='%{y}<br>Exports: %{x:.2s}<extra></extra>',
    ))
    fig.update_layout(
        xaxis=dict(tickvals=tick_vals, ticktext=[_fmt(v) for v in tick_vals]),
        yaxis=dict(tickfont=dict(size=10)),
        template='plotly_white',
        margin=dict(t=10, b=20, l=0, r=20),
        height=300,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# IMPORT ORIGINS BAR
# ══════════════════════════════════════════════════════════════════════════════
def build_import_origins(filtered_df):
    sub = filtered_df[filtered_df['trade_type'] == 'Import']
    if sub.empty:
        return go.Figure()

    top = (
        sub.groupby('Country', observed=True)['Value ($)']
        .sum().nlargest(10).reset_index()
        .sort_values('Value ($)', ascending=True)
    )
    tick_vals = np.linspace(0, top['Value ($)'].max(), 5)
    fig = go.Figure(go.Bar(
        y=top['Country'], x=top['Value ($)'],
        orientation='h', marker_color=IMPORT_COLOR,
        hovertemplate='%{y}<br>Imports: %{x:.2s}<extra></extra>',
    ))
    fig.update_layout(
        xaxis=dict(tickvals=tick_vals, ticktext=[_fmt(v) for v in tick_vals]),
        yaxis=dict(tickfont=dict(size=10)),
        template='plotly_white',
        margin=dict(t=10, b=20, l=0, r=20),
        height=300,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# PLACEHOLDER (key insights built inline in callback)
# ══════════════════════════════════════════════════════════════════════════════
def build_key_insights(*args, **kwargs):
    return go.Figure()





"""
Commodity detail panel chart functions.

"""


EXPORT_COLOR = '#52B788'
IMPORT_COLOR = '#1A4731'


# ── Commodity KPIs ────────────────────────────────────────────────────────────
def get_commodity_kpis(filtered_df, full_df, commodity_name):
    """
    Returns dict of KPI values for a specific commodity.
    """
    sub = filtered_df[filtered_df['Commodity'] == commodity_name].copy()

    if sub.empty:
        return None

    total_value    = sub['Value ($)'].sum()
    total_quantity = sub['Quantity'].sum()
    unit           = sub['Unit of measure'].mode()[0] if not sub.empty else 'N/A'

    # Avg price per unit
    price_df = sub[(sub['Quantity'] > 0) & (sub['Unit of measure'] != 'Blank')].copy()
    if not price_df.empty:
        price_df['ppu'] = price_df['Value ($)'] / price_df['Quantity']
        avg_price = price_df['ppu'].median()
    else:
        avg_price = None

    # YoY avg price change — same period prior year
    current_periods = sub[['Period']].drop_duplicates().copy()
    current_periods['year']      = current_periods['Period'].dt.year
    current_periods['month']     = current_periods['Period'].dt.month
    current_periods['prev_year'] = current_periods['year'] - 1

    full_sub = full_df[
        (full_df['Commodity'] == commodity_name) &
        (full_df['Quantity'] > 0) &
        (full_df['Unit of measure'] != 'Blank')
    ].copy()
    full_sub['year']  = full_sub['Period'].dt.year
    full_sub['month'] = full_sub['Period'].dt.month
    full_sub['ppu']   = full_sub['Value ($)'] / full_sub['Quantity']

    prev_rows = []
    for _, row in current_periods.iterrows():
        match = full_sub[
            (full_sub['year']  == row['prev_year']) &
            (full_sub['month'] == row['month'])
        ]
        prev_rows.append(match)

    yoy_price = None
    if prev_rows:
        prev_df = pd.concat(prev_rows)
        expected = len(current_periods)
        found    = prev_df[['year', 'month']].drop_duplicates().shape[0] \
                   if not prev_df.empty else 0
        if found == expected and avg_price is not None and not prev_df.empty:
            prev_avg = prev_df['ppu'].median()
            if prev_avg > 0:
                yoy_price = (avg_price - prev_avg) / prev_avg * 100

    return {
        'total_value':    total_value,
        'total_quantity': total_quantity,
        'unit':           unit,
        'avg_price':      avg_price,
        'yoy_price':      yoy_price,
    }


# ── Price Distribution Histogram ──────────────────────────────────────────────
def build_price_histogram(filtered_df, commodity_name):
    sub = filtered_df[
        (filtered_df['Commodity'] == commodity_name) &
        (filtered_df['Quantity'] > 0) &
        (filtered_df['Unit of measure'] != 'Blank')
    ].copy()

    if sub.empty:
        return go.Figure()

    sub['ppu'] = sub['Value ($)'] / sub['Quantity']

    # Remove extreme outliers (top 1%) for readable histogram
    upper = sub['ppu'].quantile(0.99)
    sub   = sub[sub['ppu'] <= upper]

    fig = go.Figure(go.Histogram(
        x=sub['ppu'],
        nbinsx=30,
        marker_color='#2A9D8F',
        opacity=0.8,
    ))

    avg = sub['ppu'].median()
    fig.add_vline(
        x=avg,
        line_dash='dash',
        line_color='#C00000',
        annotation_text=f'Median: {_fmt(avg)}/unit',
        annotation_position='top right',
        annotation_font=dict(size=11, color='#C00000'),
    )

    fig.update_layout(
        xaxis=dict(title='Price per Unit (CAD)', tickprefix='$', tickformat=','),
        yaxis=dict(title='Frequency'),
        template='plotly_white',
        margin=dict(t=20, b=40, l=40, r=20),
        height=260,
        showlegend=False,
    )
    return fig


# ── Avg Price Over Time ───────────────────────────────────────────────────────
def build_price_over_time(filtered_df, commodity_name):
    sub = filtered_df[
        (filtered_df['Commodity'] == commodity_name) &
        (filtered_df['Quantity'] > 0) &
        (filtered_df['Unit of measure'] != 'Blank')
    ].copy()

    if sub.empty:
        return go.Figure()

    sub['ppu']   = sub['Value ($)'] / sub['Quantity']
    sub['year']  = sub['Period'].dt.year
    sub['month'] = sub['Period'].dt.month

    monthly = (
        sub.groupby(['year', 'month'])['ppu']
        .median().reset_index()
        .sort_values(['year', 'month'])
    )
    monthly['label'] = monthly.apply(
        lambda r: f"{calendar.month_abbr[int(r['month'])]} {int(r['year'])}", axis=1
    )

    fig = go.Figure(go.Scatter(
        x=monthly['label'],
        y=monthly['ppu'],
        mode='lines+markers',
        line=dict(color='#1A4731', width=2),
        marker=dict(size=5, color='#1A4731'),
        hovertemplate='%{x}<br>Avg Price: $%{y:,.0f}/unit<extra></extra>',
    ))

    fig.update_layout(
        xaxis=dict(tickangle=-30, tickfont=dict(size=10)),
        yaxis=dict(title='Avg Price/Unit (CAD)', tickprefix='$', tickformat=','),
        template='plotly_white',
        margin=dict(t=20, b=60, l=60, r=20),
        height=260,
    )
    return fig


# ── Seasonality Chart ─────────────────────────────────────────────────────────
def build_seasonality_chart(filtered_df, commodity_name):
    """
    Average trade value by calendar month across all years in the filtered range.
    Shows seasonal patterns.
    """
    sub = filtered_df[filtered_df['Commodity'] == commodity_name].copy()

    if sub.empty:
        return go.Figure()

    sub['month'] = sub['Period'].dt.month

    monthly_avg = (
        sub.groupby('month')['Value ($)']
        .mean().reset_index()
    )
    monthly_avg['label'] = monthly_avg['month'].apply(
        lambda m: calendar.month_abbr[int(m)]
    )

    # Colour bars by value — higher = darker
    max_val = monthly_avg['Value ($)'].max()
    colors  = [
        f'rgba(26, 71, 49, {0.4 + 0.6 * (v / max_val)})'
        for v in monthly_avg['Value ($)']
    ]

    tick_vals = np.linspace(0, max_val, 5)

    fig = go.Figure(go.Bar(
        x=monthly_avg['label'],
        y=monthly_avg['Value ($)'],
        marker_color=colors,
        hovertemplate='%{x}<br>Avg Value: %{y:.2s}<extra></extra>',
    ))
    fig.update_layout(
        xaxis=dict(tickfont=dict(size=11)),
        yaxis=dict(
            tickvals=tick_vals,
            ticktext=[_fmt(v) for v in tick_vals],
        ),
        template='plotly_white',
        margin=dict(t=10, b=20, l=60, r=20),
        height=260,
    )
    return fig


# ── Top Export Destinations for Commodity ─────────────────────────────────────
def build_commodity_export_destinations(filtered_df, commodity_name):
    sub = filtered_df[
        (filtered_df['Commodity'] == commodity_name) &
        (filtered_df['trade_type'] == 'Export')
    ]
    if sub.empty:
        return go.Figure()

    top = (
        sub.groupby('Country', observed=True)['Value ($)']
        .sum().nlargest(8).reset_index()
        .sort_values('Value ($)', ascending=True)
    )
    tick_vals = np.linspace(0, top['Value ($)'].max(), 5)

    fig = go.Figure(go.Bar(
        y=top['Country'], x=top['Value ($)'],
        orientation='h', marker_color=EXPORT_COLOR,
        text=[_fmt(v) for v in top['Value ($)']],
        textposition='outside',
        hovertemplate='%{y}<br>%{x:.2s}<extra></extra>',
    ))
    fig.update_layout(
        xaxis=dict(tickvals=tick_vals, ticktext=[_fmt(v) for v in tick_vals],
                   visible=False),
        yaxis=dict(tickfont=dict(size=10)),
        template='plotly_white',
        margin=dict(t=10, b=10, l=0, r=60),
        height=260,
    )
    return fig


# ── Top Import Origins for Commodity ──────────────────────────────────────────
def build_commodity_import_origins(filtered_df, commodity_name):
    sub = filtered_df[
        (filtered_df['Commodity'] == commodity_name) &
        (filtered_df['trade_type'] == 'Import')
    ]
    if sub.empty:
        fig = go.Figure()
        fig.add_annotation(
            text='No import data for this commodity<br>in the selected period and filters',
            x=0.5, y=0.5, xref='paper', yref='paper',
            showarrow=False, xanchor='center', yanchor='middle',
            font=dict(size=13, color='#999999'),
        )
        fig.update_layout(
            template='plotly_white', height=260,
            xaxis=dict(visible=False), yaxis=dict(visible=False)
        )
        return fig

    top = (
        sub.groupby('Country', observed=True)['Value ($)']
        .sum().nlargest(10).reset_index()
        .sort_values('Value ($)', ascending=True)
    )
    tick_vals = np.linspace(0, top['Value ($)'].max(), 5)

    fig = go.Figure(go.Bar(
        y=top['Country'], x=top['Value ($)'],
        orientation='h', marker_color=IMPORT_COLOR,
        text=[_fmt(v) for v in top['Value ($)']],
        textposition='outside',
        hovertemplate='%{y}<br>%{x:.2s}<extra></extra>',
    ))
    fig.update_layout(
        xaxis=dict(tickvals=tick_vals, ticktext=[_fmt(v) for v in tick_vals],
                   visible=False),
        yaxis=dict(tickfont=dict(size=10)),
        template='plotly_white',
        margin=dict(t=10, b=10, l=0, r=60),
        height=260,
    )
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# BUTTERFLY CHART — back-to-back horizontal bar by HS2 Section
# ══════════════════════════════════════════════════════════════════════════════
def build_butterfly_chart(filtered_kpi, hs2_to_section, selected_section=None):
    """
    Butterfly (back-to-back) horizontal bar chart.
    Imports go LEFT (negative x), Exports go RIGHT (positive x).
    Selected section is highlighted, others dimmed.
    Clicking a bar syncs to the section dropdown via callback.
    """
    hs2 = (
        filtered_kpi
        .groupby(['HS2', 'trade_type'], observed=True)['Value ($)']
        .sum().reset_index()
    )
    if hs2.empty:
        return go.Figure()

    hs2['hs2_str'] = hs2['HS2'].astype(str).str.zfill(2)
    hs2['section'] = hs2['hs2_str'].map(hs2_to_section).fillna('Other')

    section = (
        hs2.groupby(['section', 'trade_type'])['Value ($)']
        .sum().reset_index()
    )
    pivot = section.pivot_table(
        index='section', columns='trade_type',
        values='Value ($)', aggfunc='sum'
    ).fillna(0).reset_index()
    pivot.columns.name = None

    if 'Export' not in pivot.columns:
        pivot['Export'] = 0
    if 'Import' not in pivot.columns:
        pivot['Import'] = 0

    pivot['total']   = pivot['Export'] + pivot['Import']
    pivot['exp_pct'] = (pivot['Export'] / pivot['total'] * 100).round(1)
    pivot['imp_pct'] = (pivot['Import'] / pivot['total'] * 100).round(1)
    pivot = pivot.sort_values('total', ascending=True)

    total_all = pivot['total'].sum()
    total_exp = pivot['Export'].sum()
    total_imp = pivot['Import'].sum()
    balance   = total_exp - total_imp
    bal_str   = f'▲ {_fmt(abs(balance))} Surplus' \
                if balance >= 0 \
                else f'▼ {_fmt(abs(balance))} Deficit'
    bal_color = '#1A4731' if balance >= 0 else '#C00000'

    sections = pivot['section'].tolist()

    def imp_color(s):
        if selected_section is None:
            return '#2C5F8A'
        return '#2C5F8A' if s == selected_section else 'rgba(44,95,138,0.2)'

    def exp_color(s):
        if selected_section is None:
            return '#1A4731'
        return '#1A4731' if s == selected_section else 'rgba(26,71,49,0.2)'

    fig = go.Figure()

    # Imports — left side (negative x)
    fig.add_trace(go.Bar(
        y=sections,
        x=[-v for v in pivot['Import']],
        name='Imports',
        orientation='h',
        marker_color=[imp_color(s) for s in sections],
        text=[f'{_fmt(v)}  ({p}%)'
              for v, p in zip(pivot['Import'], pivot['imp_pct'])],
        textposition='outside',
        textfont=dict(size=10, color='#333333'),
        customdata=list(zip(
            [_fmt(v) for v in pivot['Import']],
            pivot['imp_pct'],
            sections,
        )),
        hovertemplate=(
            '<b>%{y}</b><br>'
            'Imports: %{customdata[0]}<br>'
            'Share of section: %{customdata[1]}%'
            '<extra></extra>'
        ),
    ))

    # Exports — right side (positive x)
    fig.add_trace(go.Bar(
        y=sections,
        x=pivot['Export'],
        name='Exports',
        orientation='h',
        marker_color=[exp_color(s) for s in sections],
        text=[f'{_fmt(v)}  ({p}%)'
              for v, p in zip(pivot['Export'], pivot['exp_pct'])],
        textposition='outside',
        textfont=dict(size=10, color='#333333'),
        customdata=list(zip(
            [_fmt(v) for v in pivot['Export']],
            pivot['exp_pct'],
            sections,
        )),
        hovertemplate=(
            '<b>%{y}</b><br>'
            'Exports: %{customdata[0]}<br>'
            'Share of section: %{customdata[1]}%'
            '<extra></extra>'
        ),
    ))

    max_val   = max(pivot['Export'].max(), pivot['Import'].max())
    tick_vals = list(np.linspace(-max_val*1.3, max_val*1.3, 9))
    tick_text = [_fmt(abs(v)) for v in tick_vals]

    fig.update_layout(
        barmode='overlay',
        xaxis=dict(
            tickvals=tick_vals,
            ticktext=tick_text,
            zeroline=True,
            zerolinecolor='#AAAAAA',
            zerolinewidth=1.5,
        ),
        yaxis=dict(tickfont=dict(size=11)),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.06,
            xanchor='center', x=0.5,
        ),
        template='plotly_white',
        annotations=[
            # Column headers
            dict(x=0.25, y=1.05, xref='paper', yref='paper',
                 showarrow=False, align='center',
                 text='<b>IMPORTS</b>',
                 font=dict(size=14, color='#2C5F8A')),
            dict(x=0.75, y=1.05, xref='paper', yref='paper',
                 showarrow=False, align='center',
                 text='<b>EXPORTS</b>',
                 font=dict(size=14, color='#1A4731')),
            # Footer summary
            dict(x=0.10, y=-0.18, xref='paper', yref='paper',
                 showarrow=False, align='center',
                 text=f'<b>Total Imports</b><br>'
                      f'<span style="font-size:15px"><b>{_fmt(total_imp)}</b></span><br>'
                      f'<span style="color:gray">({total_imp/total_all*100:.1f}%)</span>',
                 font=dict(size=11, color='#2C5F8A')),
            # dict(x=0.36, y=-0.18, xref='paper', yref='paper',
            #      showarrow=False, align='center',
            #      text=f'<b>Total Trade</b><br>'
            #           f'<span style="font-size:15px"><b>{_fmt(total_all)}</b></span><br>'
            #           f'<span style="color:gray">(100%)</span>',
            #      font=dict(size=11, color='#333333')),
            dict(x=0.5, y=-0.18, xref='paper', yref='paper',
                 showarrow=False, align='center',
                 text=f'<b>Total Exports</b><br>'
                      f'<span style="font-size:15px"><b>{_fmt(total_exp)}</b></span><br>'
                      f'<span style="color:gray">({total_exp/total_all*100:.1f}%)</span>',
                 font=dict(size=11, color='#1A4731')),
            dict(x=0.88, y=-0.18, xref='paper', yref='paper',
                 showarrow=False, align='center',
                 text=f'<b>Trade Balance</b><br>'
                      f'<span style="font-size:15px"><b>{bal_str}</b></span>',
                 font=dict(size=11, color=bal_color)),
        ],
        margin=dict(t=60, b=110, l=0, r=40),
        height=max(500, len(sections) * 30 + 180),
        clickmode='event+select',
    )
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# COMMODITY PROVINCE LINE CHART
# One line per province showing trade value over time for a specific commodity.
# Shows Export and/or Import depending on what data exists.
# ══════════════════════════════════════════════════════════════════════════════
def build_commodity_province_lines(filtered_df, commodity_name):
    """
    Line chart — one line per province — showing monthly trade value
    for a specific commodity. Separates Export and Import into subplots
    when both exist.
    """
    sub = filtered_df[filtered_df['Commodity'] == commodity_name].copy()
    if sub.empty:
        return go.Figure()

    has_exports = not sub[sub['trade_type'] == 'Export'].empty
    has_imports = not sub[sub['trade_type'] == 'Import'].empty

    types_to_show = []
    if has_exports:
        types_to_show.append('Export')
    if has_imports:
        types_to_show.append('Import')

    if not types_to_show:
        return go.Figure()

    cols      = len(types_to_show)
    subtitles = [f'{t}s by Province' for t in types_to_show]

    fig = make_subplots(
        rows=1, cols=cols,
        subplot_titles=subtitles,
        shared_yaxes=False,
    )

    PROVINCE_COLORS = [
        '#1A4731', '#2A9D8F', '#52B788', '#E9C46A', '#F4A261',
        '#E76F51', '#457B9D', '#264653', '#6D597A', '#D62828',
        '#2C5F8A', '#84A98C', '#84A59D',
    ]

    for col_idx, trade_type in enumerate(types_to_show):
        col = col_idx + 1
        sub_t = sub[sub['trade_type'] == trade_type].copy()

        # Monthly totals per province
        sub_t['year']  = sub_t['Period'].dt.year
        sub_t['month'] = sub_t['Period'].dt.month
        monthly = (
            sub_t.groupby(['year', 'month', 'Province'], observed=True)['Value ($)']
            .sum()
            .reset_index()
            .sort_values(['year', 'month'])
        )
        monthly['label'] = monthly.apply(
            lambda r: f"{calendar.month_abbr[int(r['month'])]} {int(r['year'])}",
            axis=1
        )

        # Top 8 provinces by total value to keep the chart readable
        top_provinces = (
            monthly.groupby('Province', observed=True)['Value ($)']
            .sum()
            .nlargest(8)
            .index.tolist()
        )

        for i, province in enumerate(top_provinces):
            prov_data = monthly[monthly['Province'] == province]
            fig.add_trace(go.Scatter(
                x=prov_data['label'],
                y=prov_data['Value ($)'],
                name=province,
                mode='lines+markers',
                line=dict(color=PROVINCE_COLORS[i % len(PROVINCE_COLORS)], width=2),
                marker=dict(size=4),
                legendgroup=province,
                showlegend=(col_idx == 0),  # only show legend once
                hovertemplate=(
                    f'<b>{province}</b><br>'
                    '%{x}<br>'
                    'Value: %{y:.2s}<extra></extra>'
                ),
            ), row=1, col=col)

        # Format y axis
        fig.update_yaxes(
            tickprefix='$',
            tickformat='~s',
            gridcolor='#F0F0F0',
            row=1, col=col,
        )
        fig.update_xaxes(
            tickangle=-30,
            tickfont=dict(size=9),
            row=1, col=col,
        )

    # Style subplot titles
    fig.update_layout(
        template='plotly_white',
        margin=dict(t=50, b=60, l=60, r=20),
        height=340,
        legend=dict(
            orientation='v',
            yanchor='middle', y=0.5,
            xanchor='left', x=1.01,
            font=dict(size=10),
            title=dict(text='Province', font=dict(size=11)),
        ),
        hovermode='x unified',
    )

    for ann in fig.layout.annotations:
        ann.font = dict(size=12, color='#1F4E79', family='Arial')

    return fig