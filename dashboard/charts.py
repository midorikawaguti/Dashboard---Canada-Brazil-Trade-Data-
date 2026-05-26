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
# def build_top_products(filtered_df): ...
# def build_province_map(filtered_df): ...
# def build_country_breakdown(filtered_df): ...

def build_top_countries(filtered_df):
    top_countries = (
        filtered_df
        .groupby(['Country', 'trade_type'], observed=True)['Value ($)']
        .sum()
        .reset_index()
    )
    top10 = (
        top_countries.groupby('Country', observed=True)['Value ($)']
        .sum()
        .nlargest(10)
        .reset_index()
    )
    top_countries = top_countries[top_countries['Country'].isin(top10['Country'])]
    top_countries = top_countries.sort_values('Value ($)', ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=top_countries[top_countries['trade_type'] == 'Export']['Value ($)'],
        y=top_countries[top_countries['trade_type'] == 'Export']['Country'],
        name='Exports',
        orientation='h',
        marker_color='#458098',
    ))
    fig.add_trace(go.Bar(
        x=top_countries[top_countries['trade_type'] == 'Import']['Value ($)'],
        y=top_countries[top_countries['trade_type'] == 'Import']['Country'],
        name='Imports',
        orientation='h',
        marker_color='#183662',
    ))

    tick_vals = np.linspace(0, top_countries['Value ($)'].max(), 5)

    fig.update_layout(
        barmode='group',
        title='Top 10 Countries by Trade Value',
        xaxis=dict(
            title='Trade Value (CAD)',
            tickvals=tick_vals,
            ticktext=[fmt_value(v) for v in tick_vals],
        ),
        yaxis=dict(title=''),
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        template='plotly_white',
        margin=dict(t=60, b=40),
        height=400,
    )
    return fig

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