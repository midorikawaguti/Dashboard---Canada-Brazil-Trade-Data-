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
    """
    Horizontal grouped bar showing Export and Import value for each HS2 code,
    with % share labels. Used on the Products page to show HS2 breakdown
    within a selected section.
    """
    if filtered_df.empty:
        return go.Figure()

    grouped = (
        filtered_df
        .groupby(['HS2', 'trade_type'], observed=True)['Value ($)']
        .sum().reset_index()
    )
    if grouped.empty:
        return go.Figure()

    # Top 10 HS2 by total
    top10 = (
        grouped.groupby('HS2', observed=True)['Value ($)']
        .sum().nlargest(10).index.tolist()
    )
    grouped = grouped[grouped['HS2'].isin(top10)].copy()
    total_all = grouped['Value ($)'].sum()
    grouped['label'] = grouped['HS2'].apply(
        lambda x: HS2_LABELS.get(str(x), str(x))
    )

    order = (
        grouped.groupby('label')['Value ($)'].sum()
        .sort_values(ascending=True).index.tolist()
    )

    exports = grouped[grouped['trade_type'] == 'Export'].set_index('label')
    imports = grouped[grouped['trade_type'] == 'Import'].set_index('label')

    exp_vals = [exports['Value ($)'].get(l, 0) for l in order]
    imp_vals = [imports['Value ($)'].get(l, 0) for l in order]
    exp_pcts = [round(v / total_all * 100, 1) if total_all > 0 else 0
                for v in exp_vals]
    imp_pcts = [round(v / total_all * 100, 1) if total_all > 0 else 0
                for v in imp_vals]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=order, x=exp_vals, name='Exports',
        orientation='h', marker_color=EXPORT_COLOR,
        text=[f'{p}%' for p in exp_pcts],
        textposition='outside',
        hovertemplate='%{y}<br>Exports: %{x:.2s} (%{text})<extra></extra>',
    ))
    fig.add_trace(go.Bar(
        y=order, x=imp_vals, name='Imports',
        orientation='h', marker_color=IMPORT_COLOR,
        text=[f'{p}%' for p in imp_pcts],
        textposition='outside',
        hovertemplate='%{y}<br>Imports: %{x:.2s} (%{text})<extra></extra>',
    ))

    max_val = max(max(exp_vals, default=0), max(imp_vals, default=0))
    tick_vals = np.linspace(0, max_val, 5) if max_val > 0 else [0]

    fig.update_layout(
        barmode='group',
        xaxis=dict(
            tickvals=tick_vals,
            ticktext=[_fmt(v) for v in tick_vals],
        ),
        yaxis=dict(tickfont=dict(size=10)),
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        margin=dict(l=0, r=80, t=30, b=10),
        template='plotly_white',
        height=320,
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
    """
    Two-level treemap: Section (parent) → HS2 description (child).
    Top level always shows Sections. Clicking a Section reveals its HS2 codes.
    When hs2_to_section/description not provided, falls back to flat HS2 view.
    """
    hs2 = (
        filtered_kpi
        .groupby('HS2', observed=True)['Value ($)']
        .sum().reset_index()
    )
    if hs2.empty:
        return go.Figure()

    hs2['hs2_str'] = hs2['HS2'].astype(str).str.zfill(2)

    if hs2_to_section and hs2_to_description:
        hs2['section']     = hs2['hs2_str'].map(hs2_to_section).fillna('Other')
        hs2['description'] = hs2['hs2_str'].map(hs2_to_description).fillna(hs2['hs2_str'])

        section_totals = hs2.groupby('section')['Value ($)'].sum().reset_index()
        total = hs2['Value ($)'].sum()

        # Section level (parents = '') + HS2 level (parents = section name)
        labels  = section_totals['section'].tolist() + hs2['description'].tolist()
        parents = [''] * len(section_totals) + hs2['section'].tolist()
        values  = section_totals['Value ($)'].tolist() + hs2['Value ($)'].tolist()
        ids     = section_totals['section'].tolist() + \
                  (hs2['section'] + ' / ' + hs2['description']).tolist()
        pcts    = [round(v / total * 100, 1) for v in values]

        # Colour sections distinctly
        section_colors = [
            '#264653','#2A9D8F','#52B788','#84A59D','#E9C46A',
            '#F4A261','#E76F51','#D62828','#6D597A','#457B9D',
            '#1A4731','#A8DADC','#457B9D','#E63946','#F1FAEE',
            '#A8C4E0','#2B2D42','#8D99AE',
        ]
        section_list   = section_totals['section'].tolist()
        section_color_map = {s: section_colors[i % len(section_colors)]
                             for i, s in enumerate(section_list)}

        marker_colors = [section_color_map.get(s, '#457B9D')
                         for s in section_list] + \
                        [section_color_map.get(s, '#457B9D')
                         for s in hs2['section'].tolist()]
    else:
        hs2['label'] = hs2['hs2_str'].apply(lambda x: HS2_LABELS.get(x, x))
        total   = hs2['Value ($)'].sum()
        labels  = hs2['label'].tolist()
        ids     = hs2['label'].tolist()
        parents = [''] * len(hs2)
        values  = hs2['Value ($)'].tolist()
        pcts    = [round(v / total * 100, 1) for v in values]
        marker_colors = COLORS_10[:len(hs2)]

    fig = go.Figure(go.Treemap(
        ids=ids,
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
        marker=dict(colors=marker_colors, showscale=False),
        textfont=dict(size=11, color='white'),
        branchvalues='total',
        maxdepth=1,   # start at Section level — click to expand
    ))
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        height=300,
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
        return go.Figure()

    top = (
        sub.groupby('Country', observed=True)['Value ($)']
        .sum().nlargest(8).reset_index()
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