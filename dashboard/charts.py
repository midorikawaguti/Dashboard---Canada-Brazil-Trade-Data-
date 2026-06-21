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
    ))
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(tickfont=dict(size=12)),
        margin=dict(l=0, r=60, t=10, b=10),
        template='plotly_white',
        showlegend=False,
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

    for i, province in enumerate(top4):
        col = i + 1
        if province is None:
            fig.add_trace(go.Pie(
                values=[1], labels=['No data'],
                marker_colors=['#E0E0E0'],
                hole=0.6, showlegend=False, textinfo='none',
            ), row=1, col=col)
            continue

        sub    = filtered_df[filtered_df['Province'] == province]
        split  = sub.groupby('trade_type', observed=True)['Value ($)'].sum()
        exports = split.get('Export', 0)
        imports = split.get('Import', 0)
        total   = exports + imports

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

        fig.add_annotation(
            text=f'<b>{fmt_value(total)}</b>',
            x=0.125 + i * 0.25, y=0.5,
            showarrow=False,
            font=dict(size=11, color='#1A1A1A'),
            xref='paper', yref='paper',
        )

    fig.update_layout(
        template='plotly_white',
        margin=dict(t=40, b=20, l=0, r=0),
        height=280,
        legend=dict(orientation='h', yanchor='bottom', y=-0.15,
                    xanchor='center', x=0.5),
        annotations=[
            {**a, 'font': dict(size=13, color='#1F4E79', family='Arial')}
            if a.get('text') else a
            for a in fig.to_dict()['layout'].get('annotations', [])
        ],
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
        xaxis=dict(tickvals=tick_vals, ticktext=[_fmt(v) for v in tick_vals],
                   visible=False),
        yaxis=dict(tickfont=dict(size=11)),
        template='plotly_white',
        margin=dict(t=10, b=10, l=0, r=60),
        height=240,
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

