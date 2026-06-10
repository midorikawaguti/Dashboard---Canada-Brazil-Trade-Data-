import numpy as np
import pandas as pd
import calendar
import plotly.graph_objects as go

from .utils import fmt_value


# ── Chart 1 — Monthly Trade (grouped bars) ────────────────────────────────────
# def build_monthly_chart(filtered_df):
#     monthly = (
#         filtered_df
#         .groupby([
#             filtered_df['Period'].dt.year.rename('year'),
#             filtered_df['Period'].dt.month.rename('month'),
#             'trade_type'
#         ])['Value ($)']
#         .sum()
#         .reset_index()
#     )

#     pivot = monthly.pivot_table(
#         index=['year', 'month'], columns='trade_type',
#         values='Value ($)', aggfunc='sum'
#     ).fillna(0).reset_index()
#     pivot.columns.name = None
#     pivot = pivot.rename(columns={'Export': 'exports', 'Import': 'imports'})
#     pivot['balance'] = pivot['exports'] - pivot['imports']
#     pivot = pivot.sort_values(['year', 'month']).reset_index(drop=True)
#     pivot['label'] = pivot.apply(
#         lambda r: f"{calendar.month_abbr[int(r['month'])]} {int(r['year'])}", axis=1
#     )

#     fig = go.Figure()

#     fig.add_trace(go.Bar(
#         x=pivot['label'], y=pivot['exports'],
#         name='Exports', marker_color='#458098'
#     ))
#     fig.add_trace(go.Bar(
#         x=pivot['label'], y=pivot['imports'],
#         name='Imports', marker_color='#183662'
#     ))
#     fig.add_trace(go.Scatter(
#         x=pivot['label'], y=pivot['balance'] / 1e9,
#         name='Balance', line=dict(color='black', width=2),
#         marker=dict(size=4), yaxis='y2'
#     ))

#     tick_vals = np.linspace(0, pivot['exports'].max(), 6)

#     fig.update_layout(
#         barmode='group',
#         yaxis=dict(
#             title='Trade Value (CAD)',
#             tickvals=tick_vals,
#             ticktext=[fmt_value(v) for v in tick_vals],
#         ),
#         yaxis2=dict(
#             title='Balance (CAD $B)',
#             overlaying='y',
#             side='right',
#         ),
#         legend=dict(orientation='h', yanchor='bottom', y=1.02),
#         template='plotly_white',
#         margin=dict(t=40, b=40),
#     )
#     return fig


# ── Chart 2 — Monthly Trade (diverging bars) ──────────────────────────────────
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
        name='Exports', marker_color='#65CC90'
    ))
    fig.add_trace(go.Bar(
        x=pivot['label'], y=-pivot['imports'],
        name='Imports', marker_color='#1A4731'
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
            zeroline=True,
            zerolinecolor='black',
            zerolinewidth=1,
        ),
        yaxis2=dict(
            title='Balance (CAD $B)',
            overlaying='y',
            side='right',
            tickvals=np.linspace(-max_bal, max_bal, 9),
            ticktext=[fmt_value(abs(v) * 1e9) for v in np.linspace(-max_bal, max_bal, 9)],
        ),
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        template='plotly_white',
        margin=dict(t=40, b=40),
    )
    return fig


# ── Add new chart functions below as you build new pages ──────────────────────

# def build_top_countries(filtered_df):
#     top_countries = (
#         filtered_df
#         .groupby(['Country', 'trade_type'], observed=True)['Value ($)']
#         .sum()
#         .reset_index()
#     )
#     top10 = (
#         top_countries.groupby('Country', observed=True)['Value ($)']
#         .sum()
#         .nlargest(10)
#         .reset_index()
#     )
#     top_countries = top_countries[top_countries['Country'].isin(top10['Country'])]
#     top_countries = top_countries.sort_values('Value ($)', ascending=True)

#     fig = go.Figure()

#     fig.add_trace(go.Bar(
#         x=top_countries[top_countries['trade_type'] == 'Export']['Value ($)'],
#         y=top_countries[top_countries['trade_type'] == 'Export']['Country'],
#         name='Exports',
#         orientation='h',
#         marker_color='#458098',
#     ))
#     fig.add_trace(go.Bar(
#         x=top_countries[top_countries['trade_type'] == 'Import']['Value ($)'],
#         y=top_countries[top_countries['trade_type'] == 'Import']['Country'],
#         name='Imports',
#         orientation='h',
#         marker_color='#183662',
#     ))

#     tick_vals = np.linspace(0, top_countries['Value ($)'].max(), 5)

#     fig.update_layout(
#         barmode='group',
#         title='Top 10 Countries by Trade Value',
#         xaxis=dict(
#             title='Trade Value (CAD)',
#             tickvals=tick_vals,
#             ticktext=[fmt_value(v) for v in tick_vals],
#         ),
#         yaxis=dict(title=''),
#         legend=dict(orientation='h', yanchor='bottom', y=1.02),
#         template='plotly_white',
#         margin=dict(t=60, b=40),
#         height=400,
#     )
#     return fig
# ── Table 1  — Top Commodity Share ──────────────────────────────────
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

    # Handle case where Export or Import column might be missing after filtering
    if 'Export' not in pivot.columns:
        pivot['Export'] = 0
    if 'Import' not in pivot.columns:
        pivot['Import'] = 0

    pivot['Total'] = pivot['Export'] + pivot['Import']
    pivot = pivot.nlargest(10, 'Total').reset_index(drop=True)

    total_all = pivot['Total'].sum()
    pivot['Share %'] = (pivot['Total'] / total_all * 100).round(1)
    pivot['Rank'] = pivot.index + 1

    # Format for display
    table_df = pd.DataFrame({
        '#':          pivot['Rank'],
        'Commodity':    pivot['Commodity'],
        'Exports':    pivot['Export'].apply(fmt_value),
        'Imports':    pivot['Import'].apply(fmt_value),
        'Total Trade': pivot['Total'].apply(fmt_value),
        'Share %':    pivot['Share %'].astype(str) + '%',
    })

    return table_df.to_dict('records')

# ── Table 1  — Top Countries Share ──────────────────────────────────
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

    # Handle case where Export or Import column might be missing after filtering
    if 'Export' not in pivot.columns:
        pivot['Export'] = 0
    if 'Import' not in pivot.columns:
        pivot['Import'] = 0

    pivot['Total'] = pivot['Export'] + pivot['Import']
    pivot = pivot.nlargest(10, 'Total').reset_index(drop=True)

    total_all = pivot['Total'].sum()
    pivot['Share %'] = (pivot['Total'] / total_all * 100).round(1)
    pivot['Rank'] = pivot.index + 1

    # Format for display
    table_df = pd.DataFrame({
        '#':          pivot['Rank'],
        'Country':    pivot['Country'],
        'Exports':    pivot['Export'].apply(fmt_value),
        'Imports':    pivot['Import'].apply(fmt_value),
        'Total Trade': pivot['Total'].apply(fmt_value),
        'Share %':    pivot['Share %'].astype(str) + '%',
    })

    return table_df.to_dict('records')

# ── Chart  ─────────────────────────────────
def build_top5_tables(filtered_df, full_df):
    """
    Returns (export_records, import_records) for the two mini tables.
    YoY compares selected period vs same period 1 year prior.
    full_df is used to look up prior year data outside the filtered range.
    """

    # Get exact year-month pairs in current selection
    current_periods = (
        filtered_df[['Period']]
        .drop_duplicates()
        .copy()
    )
    current_periods['year']      = current_periods['Period'].dt.year
    current_periods['month']     = current_periods['Period'].dt.month
    current_periods['prev_year'] = current_periods['year'] - 1

    # Check if all months have prior year data in full_df
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
    found_count    = prior_df[['year', 'month']].drop_duplicates().shape[0] if not prior_df.empty else 0
    has_prior_year = found_count == expected_count   # all months matched

# ── Chart  ─────────────────────────────────
    def get_top5(trade_type):
        sub = filtered_df[filtered_df['trade_type'] == trade_type]

        total = (
            sub.groupby('Commodity', observed=True)['Value ($)']
            .sum()
            .nlargest(5)
            .reset_index()
        )

        yoy_map = {}

        if has_prior_year:
            # Current period totals per commodity
            curr = (
                sub.groupby('Commodity', observed=True)['Value ($)']
                .sum()
            )

            # Prior period totals per commodity
            prior_sub = prior_df[prior_df['trade_type'] == trade_type]
            prev = (
                prior_sub.groupby('Commodity', observed=True)['Value ($)']
                .sum()
            )

            for c in total['Commodity']:
                if c in curr.index and c in prev.index and prev[c] != 0:
                    yoy_map[c] = ((curr[c] - prev[c]) / prev[c] * 100)
                else:
                    yoy_map[c] = None

        records = []
        for _, row in total.iterrows():
            yoy     = yoy_map.get(row['Commodity'])
            if yoy is None and not has_prior_year:
                yoy_str = 'N/A'       # no prior year data at all
            elif yoy is None:
                yoy_str = 'N/A'       # commodity not found in prior year
            elif yoy >= 0:
                yoy_str = f'+{yoy:.0f}%'
            else:
                yoy_str = f'{yoy:.0f}%'

            name = str(row['Commodity'])[:60] + '...' if len(str(row['Commodity'])) > 20 else str(row['Commodity'])
            records.append({
                'Commodity': name,
                'Value':     fmt_value(row['Value ($)']),
                'YoY':       yoy_str,
                '_yoy_val':  yoy,
            })
        return records

    return get_top5('Export'), get_top5('Import')

# ── Chart  ──────────────────────────────────
def build_hs2_share_chart(filtered_df):
    """Horizontal bar chart of % share by HS2 category."""
    from .utils import HS2_LABELS

    total_all = filtered_df['Value ($)'].sum()
    if total_all == 0:
        return go.Figure()

    hs2 = (
        filtered_df
        .groupby('HS2', observed=True)['Value ($)']
        .sum()
        .reset_index()
    )
    hs2['share'] = (hs2['Value ($)'] / total_all * 100).round(1)
    hs2['label'] = hs2['HS2'].apply(lambda x: HS2_LABELS.get(str(x), str(x)))
    hs2 = hs2.nlargest(10, 'share').sort_values('share')

    # Colour scale — greens to oranges
    colors = [
    "#264653",  # deep blue-green
    "#2A9D8F",  # teal
    "#52B788",  # soft green
    "#84A59D",  # sage
    "#E9C46A",  # warm yellow
    "#F4A261",  # sand orange
    "#E76F51",  # coral
    "#D62828",  # muted red
    "#6D597A",  # dusty purple
    "#457B9D",  # steel blue
]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=hs2['share'],
        y=hs2['label'],
        orientation='h',
        text=hs2['share'].apply(lambda x: f'{x}%'),
        textposition='outside',
        marker_color=colors[:len(hs2)],
    ))

    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(tickfont=dict(size=12)),
        margin=dict(l=0, r=0, t=10, b=10),
        template='plotly_white',
        showlegend=False,
    )
    return fig