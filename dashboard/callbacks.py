from dash import html, dcc, Input, Output, State, ctx

from .data import df, df_kpi, df_kpi_commodity, period_index, \
                  hs2_to_section, hs2_to_description
from .utils import (apply_filters, fmt_value, HS2_LABELS,
                    get_fastest_growing_hs2, get_top_hs2_share,
                    get_top_province, get_top_country,
                    get_hs2_codes_for_section)
from .charts import (
    build_monthly_chart,
    build_top_countries_table,
    build_top5_tables,
    build_hs2_share_chart,
    build_top_commodity_table,
    build_province_small_multiples,
    build_top_provinces_bar,
    build_top_partners_bar,
    build_hs2_treemap,
    build_province_balance_bar,
    build_export_destinations,
    build_import_origins,
    get_commodity_kpis,
    build_price_histogram,
    build_price_over_time,
    build_seasonality_chart,
    build_commodity_export_destinations,
    build_commodity_import_origins,
    build_butterfly_chart
)
from .styles import (
    KPI_STYLE_VALUE, KPI_TEXT_VALUE, KPI_NOTE,
    KPI_STYLE_BOX, KPI_STYLE_ROW,
    STYLE_CHART_ROW, STYLE_CHART_ITEM,
    FIGURE_TITLE, FIGURE_DESCRIPTION,
    RED, BLUE_ACCENT, GREEN_TREND, TEXT_GRAY, WHITE, DARK_GREEN,
)
from .pages import overview, products


INSIGHT_CARD_STYLE = {
    'flex':            '1',
    'backgroundColor': '#F0F7F4',
    'borderRadius':    '8px',
    'padding':         '12px 14px',
    'minWidth':        '130px',
    'borderLeft':      f'3px solid {DARK_GREEN}',
}


def register_callbacks(app):

    # ── Routing ───────────────────────────────────────────────────────────────
    @app.callback(
        Output('page-content', 'children'),
        Input('url', 'pathname')
    )
    def render_page(pathname):
        if pathname == '/products':
            return products.layout()
        else:
            return overview.layout()

    # ── Sidebar nav highlight ─────────────────────────────────────────────────
    @app.callback(
        Output('nav-overview', 'style'),
        Output('nav-products', 'style'),
        Input('url', 'pathname')
    )
    def highlight_nav(pathname):
        base = {
            'display': 'flex', 'alignItems': 'center', 'gap': '10px',
            'padding': '12px 20px', 'fontSize': '14px', 'cursor': 'pointer',
        }
        active   = {**base, 'color': WHITE,
                    'backgroundColor': 'rgba(255,255,255,0.15)',
                    'borderLeft': '3px solid white'}
        inactive = {**base, 'color': '#B2DFCC',
                    'borderLeft': '3px solid transparent'}
        if pathname == '/products':
            return inactive, active
        return active, inactive

    # ── Enforce ALL ───────────────────────────────────────────────────────────
    @app.callback(
        Output('province-dropdown',   'value'),
        Output('country-dropdown',    'value'),
        Output('trade-type-dropdown', 'value'),
        Input('province-dropdown',    'value'),
        Input('country-dropdown',     'value'),
        Input('trade-type-dropdown',  'value'),
        prevent_initial_call=True,
    )
    def enforce_all(province, country, trade_type):
        def fix(selected):
            if not selected:
                return ['ALL']
            if len(selected) > 1 and 'ALL' in selected:
                return [v for v in selected if v != 'ALL']
            return selected
        return fix(province), fix(country), fix(trade_type)

    # ══════════════════════════════════════════════════════════════════════════
    # OVERVIEW CALLBACK
    # ══════════════════════════════════════════════════════════════════════════
    @app.callback(
        Output('total-export',          'children'),
        Output('total-import',          'children'),
        Output('trade-balance',         'children'),
        Output('overview-top-partner',  'children'),
        Output('overview-top-province', 'children'),
        Output('monthly-trade',            'figure'),
        Output('top-partners-bar',         'figure'),
        Output('province-balance-bar',     'figure'),
        Output('province-small-multiples', 'figure'),
        Input('period-slider',        'value'),
        Input('province-dropdown',    'value'),
        Input('country-dropdown',     'value'),
        Input('trade-type-dropdown',  'value'),
    )
    def update_overview(period_range, selected_province,
                        selected_country, selected_trade_type):

        filtered = apply_filters(
            df, period_range, None,
            selected_province, selected_country,
            selected_trade_type, period_index=period_index
        )
        filtered_kpi = apply_filters(
            df_kpi, period_range, None,
            selected_province, selected_country,
            selected_trade_type, period_index=period_index
        )

        total_export  = filtered_kpi[filtered_kpi['trade_type'] == 'Export']['Value ($)'].sum()
        total_import  = filtered_kpi[filtered_kpi['trade_type'] == 'Import']['Value ($)'].sum()
        trade_balance = total_export - total_import
        balance_color = RED if trade_balance < 0 else BLUE_ACCENT

        kpi_export  = [html.H2(fmt_value(total_export),  style=KPI_STYLE_VALUE)]
        kpi_import  = [html.H2(fmt_value(total_import),  style=KPI_STYLE_VALUE)]
        kpi_balance = [html.H2(fmt_value(trade_balance),
                               style={**KPI_STYLE_VALUE, 'color': balance_color})]

        country_name, country_pct, _ = get_top_country(filtered_kpi)
        kpi_top_partner = [
            html.P(str(country_name)[:20],
                   style={**KPI_STYLE_VALUE, 'fontSize': '16px'}),
            html.P(f'{country_pct:.1f}% of trade', style=KPI_NOTE),
        ]

        province_name, province_pct, _ = get_top_province(filtered_kpi)
        kpi_top_province = [
            html.P(str(province_name)[:20],
                   style={**KPI_STYLE_VALUE, 'fontSize': '16px'}),
            html.P(f'{province_pct:.1f}% of trade', style=KPI_NOTE),
        ]

        return (
            kpi_export,
            kpi_import,
            kpi_balance,
            kpi_top_partner,
            kpi_top_province,
            build_monthly_chart(filtered),
            build_top_partners_bar(filtered_kpi),
            build_province_balance_bar(filtered_kpi),
            build_province_small_multiples(filtered),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # PRODUCTS — LEVEL 1: Section synced with butterfly chart click
    # ══════════════════════════════════════════════════════════════════════════
    @app.callback(
        Output('products-section-select', 'value'),
        Input('products-butterfly',       'clickData'),
        Input('products-section-select',  'value'),
        prevent_initial_call=True,
    )
    def sync_butterfly_to_section(click_data, current_section):
        if ctx.triggered_id == 'products-section-select':
            return current_section
        if click_data:
            point           = click_data['points'][0]
            clicked_section = point.get('y')
            if clicked_section:
                if clicked_section == current_section:
                    return None
                return clicked_section
        return current_section

    # ── Sync HS2 share chart click → HS2 dropdown ─────────────────────────────
    @app.callback(
        Output('products-hs2-select', 'value', allow_duplicate=True),
        Input('hs2-share-chart-products', 'clickData'),
        Input('products-hs2-select',      'value'),
        prevent_initial_call=True,
    )
    def sync_hs2_chart_to_dropdown(click_data, current_hs2):
        if ctx.triggered_id == 'products-hs2-select':
            return current_hs2
        if click_data:
            clicked_hs2 = click_data['points'][0].get('customdata')
            if clicked_hs2:
                if str(clicked_hs2) == str(current_hs2):
                    return None
                return clicked_hs2
        return current_hs2

    # ══════════════════════════════════════════════════════════════════════════
    # PRODUCTS — LEVEL 2: HS2 dropdown OPTIONS only (not value)
    # ══════════════════════════════════════════════════════════════════════════
    @app.callback(
        Output('products-hs2-select', 'options'),
        Input('products-section-select', 'value'),
        Input('period-slider',           'value'),
        Input('province-dropdown',       'value'),
        Input('trade-type-dropdown',     'value'),
    )
    def update_hs2_options(selected_section, period_range,
                           selected_province, selected_trade_type):
        hs2_filter = get_hs2_codes_for_section(selected_section, hs2_to_section)

        filtered = apply_filters(
            df_kpi, period_range, hs2_filter,
            selected_province, None,
            selected_trade_type, period_index=period_index
        )

        if filtered.empty:
            return []

        available_hs2 = filtered['HS2'].unique().tolist()
        return [
            {'label': f"{code} – {HS2_LABELS.get(str(code), str(code))}",
             'value': code}
            for code in sorted(available_hs2)
        ]

    # ── Reset HS2 value ONLY when section changes ─────────────────────────────
    @app.callback(
        Output('products-hs2-select', 'value'),
        Input('products-section-select', 'value'),
        prevent_initial_call=True,
    )
    def reset_hs2_on_section_change(selected_section):
        """Clear HS2 selection only when section changes."""
        return None

    # ══════════════════════════════════════════════════════════════════════════
    # PRODUCTS — Main charts/KPIs
    # ══════════════════════════════════════════════════════════════════════════
    @app.callback(
        Output('top-HS2',                      'children'),
        Output('fastest-growing',              'children'),
        Output('number-commodities',           'children'),
        Output('products-butterfly',           'figure'),
        Output('hs2-share-chart-products',     'figure'),
        Output('top5-export-table-products',   'data'),
        Output('top5-import-table-products',   'data'),
        Output('products-export-destinations', 'figure'),
        Output('products-import-origins',      'figure'),
        Input('period-slider',           'value'),
        Input('province-dropdown',       'value'),
        Input('country-dropdown',        'value'),
        Input('trade-type-dropdown',     'value'),
        Input('products-section-select', 'value'),
        Input('products-hs2-select',     'value'),
    )
    def update_products(period_range, selected_province, selected_country,
                        selected_trade_type, selected_section, selected_hs2):

        section_hs2_filter = get_hs2_codes_for_section(selected_section, hs2_to_section)

        if selected_hs2:
            hs2_filter = [selected_hs2]
        else:
            hs2_filter = section_hs2_filter

        filtered = apply_filters(
            df, period_range, hs2_filter,
            selected_province, selected_country,
            selected_trade_type, period_index=period_index
        )
        filtered_kpi = apply_filters(
            df_kpi, period_range, hs2_filter,
            selected_province, selected_country,
            selected_trade_type, period_index=period_index
        )
        filtered_for_commodity = apply_filters(
            df, period_range, hs2_filter,
            selected_province, selected_country,
            selected_trade_type, period_index=period_index
        )
        filtered_commodity = (
            filtered_for_commodity
            .groupby(['Period', 'Commodity', 'Province', 'Country', 'trade_type'],
                     observed=True)['Value ($)']
            .sum()
            .reset_index()
        )

        # ── KPIs ──────────────────────────────────────────────────────────────
        hs2_code, pct_top, _ = get_top_hs2_share(filtered_kpi)
        clean_name = HS2_LABELS.get(str(hs2_code), str(hs2_code)) \
                     if hs2_code else 'N/A'
        kpi_top_hs2 = [
            html.P(clean_name[:28], style={**KPI_STYLE_VALUE, 'fontSize': '14px'}),
            html.P(f'{pct_top:.1f}% of total trade', style=KPI_NOTE),
        ]

        hs2_fast, pct_fast, note_fast = get_fastest_growing_hs2(filtered_kpi, df_kpi)
        fast_label = HS2_LABELS.get(str(hs2_fast), str(hs2_fast)) if hs2_fast else 'N/A'
        if pct_fast is not None:
            fast_str   = f'+{pct_fast:.1f}%' if pct_fast >= 0 else f'{pct_fast:.1f}%'
            fast_color = GREEN_TREND if pct_fast >= 0 else RED
            fast_note  = '% vs same period prior year'
        else:
            fast_str, fast_color, fast_note = 'N/A', TEXT_GRAY, note_fast or ''
        kpi_fastest = [
            html.P(fast_str, style={**KPI_STYLE_VALUE, 'color': fast_color}),
            html.P(fast_label[:28], style=KPI_TEXT_VALUE),
            html.P(fast_note, style=KPI_NOTE),
        ]

        n_commodities = filtered_commodity['Commodity'].nunique()
        kpi_commodities = [html.H2(f'{n_commodities:,}', style=KPI_STYLE_VALUE)]

        # ── Charts ────────────────────────────────────────────────────────────
        filtered_kpi_sections = apply_filters(
            df_kpi, period_range, section_hs2_filter,
            selected_province, selected_country,
            selected_trade_type, period_index=period_index
        )

        export_records, import_records = build_top5_tables(
            filtered_for_commodity, df_kpi_commodity
        )

        return (
            kpi_top_hs2,
            kpi_fastest,
            kpi_commodities,
            build_butterfly_chart(
                filtered_kpi_sections,
                hs2_to_section,
                selected_section=selected_section
            ),
            build_hs2_share_chart(filtered_kpi),
            export_records,
            import_records,
            build_export_destinations(filtered),
            build_import_origins(filtered),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # PRODUCTS — LEVEL 3: Commodity dropdown OPTIONS only (not value)
    # Updates the list but never touches the selected value
    # ══════════════════════════════════════════════════════════════════════════
    @app.callback(
        Output('products-commodity-select', 'options'),
        Input('period-slider',           'value'),
        Input('province-dropdown',       'value'),
        Input('trade-type-dropdown',     'value'),
        Input('products-hs2-select',     'value'),
        Input('products-section-select', 'value'),
    )
    def update_commodity_options(period_range, selected_province,
                                 selected_trade_type, selected_hs2,
                                 selected_section):
        if selected_hs2:
            hs2_filter = [selected_hs2]
        else:
            hs2_filter = get_hs2_codes_for_section(selected_section, hs2_to_section)

        filtered_raw = apply_filters(
            df, period_range, hs2_filter,
            selected_province, None,
            selected_trade_type, period_index=period_index
        )
        filtered = (
            filtered_raw
            .groupby(['Period', 'Commodity', 'Province', 'Country', 'trade_type'],
                     observed=True)['Value ($)']
            .sum()
            .reset_index()
        )

        if filtered.empty:
            return []

        top_commodities = (
            filtered
            .groupby('Commodity', observed=True)['Value ($)']
            .sum()
            .nlargest(200)
            .index.tolist()
        )
        return [{'label': str(c)[:60], 'value': c}
                for c in sorted(top_commodities)]

    # ── Reset commodity value ONLY when section or HS2 changes ────────────────
    @app.callback(
        Output('products-commodity-select', 'value'),
        Input('products-section-select', 'value'),
        Input('products-hs2-select',     'value'),
        prevent_initial_call=True,
    )
    def reset_commodity_on_drill_change(selected_section, selected_hs2):
        """Clear commodity selection only when the drill-down level above changes."""
        return None

    # ══════════════════════════════════════════════════════════════════════════
    # PRODUCTS — LEVEL 3: Commodity detail panel
    # ══════════════════════════════════════════════════════════════════════════
    @app.callback(
        Output('commodity-detail-panel', 'children'),
        Input('products-commodity-select', 'value'),
        Input('period-slider',             'value'),
        Input('province-dropdown',         'value'),
        Input('trade-type-dropdown',       'value'),
    )
    def update_commodity_detail(selected_commodity, period_range,
                                selected_province, selected_trade_type):

        if not selected_commodity:
            return html.Div()

        filtered = apply_filters(
            df, period_range, None,
            selected_province, None,
            selected_trade_type, period_index=period_index
        )

        kpis = get_commodity_kpis(filtered, df, selected_commodity)

        if not kpis:
            return html.Div(
                html.P('No data available for this commodity.',
                       style={'color': TEXT_GRAY, 'padding': '20px'}),
            )

        short_name = str(selected_commodity)[:80] + '...' \
                     if len(str(selected_commodity)) > 80 \
                     else str(selected_commodity)

        # ── Determine what data is available ──────────────────────────────────
        sub         = filtered[filtered['Commodity'] == selected_commodity]
        has_exports = not sub[sub['trade_type'] == 'Export'].empty
        has_imports = not sub[sub['trade_type'] == 'Import'].empty
        has_price   = kpis['avg_price'] is not None

        # ── Trade direction banner ─────────────────────────────────────────────
        if has_exports and has_imports:
            dir_text  = '✅  Both Export and Import data available'
            dir_color = '#1A4731'
            dir_bg    = '#E8F5E9'
        elif has_exports:
            dir_text  = 'ℹ️  Export data only — no import records for this commodity in the selected period'
            dir_color = '#1F4E79'
            dir_bg    = '#E3F0FA'
        elif has_imports:
            dir_text  = 'ℹ️  Import data only — no export records for this commodity in the selected period'
            dir_color = '#1F4E79'
            dir_bg    = '#E3F0FA'
        else:
            dir_text  = '⚠️  No trade data found'
            dir_color = '#C00000'
            dir_bg    = '#FFF0F0'

        # ── KPI tiles ─────────────────────────────────────────────────────────
        avg_price_str = fmt_value(kpis['avg_price']) + '/unit' if has_price else None

        if has_price and kpis['yoy_price'] is not None:
            yoy_str   = f'+{kpis["yoy_price"]:.1f}%' if kpis['yoy_price'] >= 0 \
                        else f'{kpis["yoy_price"]:.1f}%'
            yoy_color = GREEN_TREND if kpis['yoy_price'] >= 0 else RED
        else:
            yoy_str, yoy_color = None, TEXT_GRAY

        kpi_tiles = [
            html.Div(style=KPI_STYLE_BOX, children=[
                html.H2(fmt_value(kpis['total_value']), style=KPI_STYLE_VALUE),
                html.P('Total Trade Value',
                       style={'color': TEXT_GRAY, 'fontSize': '12px',
                              'margin': '4px 0 0 0'}),
            ]),
            html.Div(style=KPI_STYLE_BOX, children=[
                html.H2(f'{kpis["total_quantity"]:,.0f}', style=KPI_STYLE_VALUE),
                html.P(f'Total Quantity ({kpis["unit"]})',
                       style={'color': TEXT_GRAY, 'fontSize': '12px',
                              'margin': '4px 0 0 0'}),
            ]),
        ]
        if has_price:
            kpi_tiles.append(html.Div(style=KPI_STYLE_BOX, children=[
                html.H2(avg_price_str, style=KPI_STYLE_VALUE),
                html.P('Avg Price per Unit',
                       style={'color': TEXT_GRAY, 'fontSize': '12px',
                              'margin': '4px 0 0 0'}),
            ]))
            if yoy_str:
                kpi_tiles.append(html.Div(style=KPI_STYLE_BOX, children=[
                    html.H2(yoy_str, style={**KPI_STYLE_VALUE, 'color': yoy_color}),
                    html.P('YoY Price Change',
                           style={'color': TEXT_GRAY, 'fontSize': '12px',
                                  'margin': '4px 0 0 0'}),
                    html.P('vs same period prior year',
                           style={'color': TEXT_GRAY, 'fontSize': '10px',
                                  'fontStyle': 'italic', 'margin': '2px 0 0 0'}),
                ]))
        else:
            kpi_tiles.append(html.Div(
                style={**KPI_STYLE_BOX, 'borderLeft': '3px solid #FFAA00',
                       'backgroundColor': '#FFFBF0'}, children=[
                html.P('⚠️  Price data unavailable',
                       style={'color': '#AA6600', 'fontSize': '12px',
                              'fontWeight': 'bold', 'margin': '0 0 4px 0'}),
                html.P('Quantity = 0 for all records — price per unit cannot be computed',
                       style={'color': TEXT_GRAY, 'fontSize': '11px', 'margin': '0'}),
            ]))

        # ── Price charts row ───────────────────────────────────────────────────
        if has_price:
            price_row = html.Div(
                style={**STYLE_CHART_ROW, 'margin': '0 0 16px 0'},
                children=[
                    html.Div(style={**STYLE_CHART_ITEM, 'flex': '1'}, children=[
                        html.H4('Price Distribution', style=FIGURE_TITLE),
                        html.P('Frequency of price per unit', style=FIGURE_DESCRIPTION),
                        dcc.Graph(figure=build_price_histogram(filtered, selected_commodity),
                                  config={'displayModeBar': False}),
                    ]),
                    html.Div(style={**STYLE_CHART_ITEM, 'flex': '1'}, children=[
                        html.H4('Avg Price Over Time', style=FIGURE_TITLE),
                        html.P('Monthly median price per unit', style=FIGURE_DESCRIPTION),
                        dcc.Graph(figure=build_price_over_time(filtered, selected_commodity),
                                  config={'displayModeBar': False}),
                    ]),
                    html.Div(style={**STYLE_CHART_ITEM, 'flex': '1'}, children=[
                        html.H4('Seasonality', style=FIGURE_TITLE),
                        html.P('Avg monthly trade value across years',
                               style=FIGURE_DESCRIPTION),
                        dcc.Graph(figure=build_seasonality_chart(filtered, selected_commodity),
                                  config={'displayModeBar': False}),
                    ]),
                ]
            )
        else:
            price_row = html.Div(
                style={'backgroundColor': '#FFFBF0', 'borderRadius': '8px',
                       'padding': '14px 18px', 'margin': '0 0 16px 0',
                       'border': '1px solid #FFDD99'},
                children=[
                    html.P('⚠️  Price charts not available',
                           style={'color': '#AA6600', 'fontWeight': 'bold',
                                  'margin': '0 0 4px 0', 'fontSize': '13px'}),
                    html.P('Price distribution, avg price over time and seasonality '
                           'require Quantity > 0 to compute price per unit. '
                           'All records for this commodity have Quantity = 0.',
                           style={'color': TEXT_GRAY, 'fontSize': '12px', 'margin': '0'}),
                ]
            )

        # ── Destinations — only show available directions ──────────────────────
        dest_children = []
        if has_exports:
            dest_children.append(html.Div(style={**STYLE_CHART_ITEM, 'flex': '1'}, children=[
                html.H4('Top Export Destinations', style=FIGURE_TITLE),
                html.P('Countries buying this commodity from Canada',
                       style=FIGURE_DESCRIPTION),
                dcc.Graph(figure=build_commodity_export_destinations(
                              filtered, selected_commodity),
                          config={'displayModeBar': False}),
            ]))
        if has_imports:
            dest_children.append(html.Div(style={**STYLE_CHART_ITEM, 'flex': '1'}, children=[
                html.H4('Top Import Origins', style=FIGURE_TITLE),
                html.P('Countries supplying this commodity to Canada',
                       style=FIGURE_DESCRIPTION),
                dcc.Graph(figure=build_commodity_import_origins(
                              filtered, selected_commodity),
                          config={'displayModeBar': False}),
            ]))
        dest_row = html.Div(
            style={**STYLE_CHART_ROW, 'margin': '0 0 16px 0'},
            children=dest_children
        )

        # ── Data quality stats ─────────────────────────────────────────────────
        total_r     = len(sub)
        valid_r     = len(sub[sub['Quantity'] > 0])
        zero_r      = total_r - valid_r
        blank_u     = len(sub[sub['Unit of measure'] == 'Blank']) \
                      if 'Unit of measure' in sub.columns else 0
        countries_n = sub['Country'].nunique() \
                      if 'Country' in sub.columns else 0

        data_quality = html.Div(
            id='data-quality-panel',
            style={'display': 'none'},
            children=[
                html.Hr(style={'margin': '16px 0', 'borderColor': '#E0E0E0'}),
                html.H4('📊  Data Quality',
                        style={'color': BLUE_ACCENT, 'fontSize': '14px',
                               'margin': '0 0 12px 0'}),
                html.Div(style={'display': 'flex', 'gap': '12px', 'flexWrap': 'wrap'},
                         children=[
                    html.Div(style={**KPI_STYLE_BOX, 'minWidth': '130px'}, children=[
                        html.H3(f'{total_r:,}',
                                style={**KPI_STYLE_VALUE, 'fontSize': '22px'}),
                        html.P('Total Rows',
                               style={'color': TEXT_GRAY, 'fontSize': '11px',
                                      'margin': '4px 0 0 0'}),
                    ]),
                    html.Div(style={**KPI_STYLE_BOX, 'minWidth': '130px',
                                    'borderLeft': f'3px solid {"#1A4731" if valid_r == total_r else "#FFAA00"}'}, children=[
                        html.H3(f'{valid_r:,}',
                                style={**KPI_STYLE_VALUE, 'fontSize': '22px',
                                       'color': '#1A4731' if valid_r == total_r else '#AA6600'}),
                        html.P(f'Valid Rows ({valid_r/total_r*100:.0f}% of total)' if total_r > 0 else 'Valid Rows',
                               style={'color': TEXT_GRAY, 'fontSize': '11px',
                                      'margin': '4px 0 0 0'}),
                        html.P('Qty > 0, price computable',
                               style={'color': TEXT_GRAY, 'fontSize': '10px',
                                      'fontStyle': 'italic', 'margin': '2px 0 0 0'}),
                    ]),
                    # Zero quantity — only show if there are any
                    *([html.Div(style={**KPI_STYLE_BOX, 'minWidth': '130px',
                                       'borderLeft': '3px solid #C00000'}, children=[
                        html.H3(f'{zero_r:,}',
                                style={**KPI_STYLE_VALUE, 'fontSize': '22px',
                                       'color': '#C00000'}),
                        html.P('Zero Quantity',
                               style={'color': TEXT_GRAY, 'fontSize': '11px',
                                      'margin': '4px 0 0 0'}),
                        html.P('Cannot compute price/unit',
                               style={'color': TEXT_GRAY, 'fontSize': '10px',
                                      'fontStyle': 'italic', 'margin': '2px 0 0 0'}),
                    ])] if zero_r > 0 else []),
                    # Blank unit — only show if there are any
                    *([html.Div(style={**KPI_STYLE_BOX, 'minWidth': '130px'}, children=[
                        html.H3(f'{blank_u:,}',
                                style={**KPI_STYLE_VALUE, 'fontSize': '22px'}),
                        html.P('Blank Unit',
                               style={'color': TEXT_GRAY, 'fontSize': '11px',
                                      'margin': '4px 0 0 0'}),
                        html.P('No unit of measure',
                               style={'color': TEXT_GRAY, 'fontSize': '10px',
                                      'fontStyle': 'italic', 'margin': '2px 0 0 0'}),
                    ])] if blank_u > 0 else []),
                    html.Div(style={**KPI_STYLE_BOX, 'minWidth': '130px'}, children=[
                        html.H3(f'{countries_n:,}',
                                style={**KPI_STYLE_VALUE, 'fontSize': '22px',
                                       'color': BLUE_ACCENT}),
                        html.P('Countries',
                               style={'color': TEXT_GRAY, 'fontSize': '11px',
                                      'margin': '4px 0 0 0'}),
                    ]),
                ])
            ]
        )

        return html.Div(
            style={
                'backgroundColor': WHITE, 'borderRadius': '10px',
                'padding': '20px 24px', 'marginTop': '16px',
                'boxShadow': '0 1px 4px rgba(0,0,0,0.07)',
                'borderLeft': f'4px solid {BLUE_ACCENT}',
            },
            children=[

                # Title row + data quality toggle button
                html.Div(style={'display': 'flex', 'justifyContent': 'space-between',
                                'alignItems': 'flex-start', 'marginBottom': '12px'},
                         children=[
                    html.Div(children=[
                        html.H4(f'🔬  {short_name}',
                                style={'margin': '0 0 4px 0', 'color': BLUE_ACCENT,
                                       'fontSize': '15px', 'fontWeight': 'bold'}),
                        html.P('Price distribution, trend, seasonality and trade partners',
                               style={'margin': '0', 'color': TEXT_GRAY,
                                      'fontSize': '12px', 'fontStyle': 'italic'}),
                    ]),
                    html.Button('📊  Data Quality', id='data-quality-toggle',
                                n_clicks=0,
                                style={'backgroundColor': WHITE,
                                       'border': f'1px solid {BLUE_ACCENT}',
                                       'borderRadius': '6px', 'color': BLUE_ACCENT,
                                       'cursor': 'pointer', 'fontSize': '12px',
                                       'fontWeight': 'bold', 'padding': '6px 14px'}),
                ]),

                # Trade direction banner
                html.Div(style={'backgroundColor': dir_bg,
                                'border': f'1px solid {dir_color}',
                                'borderRadius': '6px', 'padding': '8px 14px',
                                'marginBottom': '16px', 'fontSize': '13px',
                                'color': dir_color, 'fontWeight': '500'},
                         children=dir_text),

                # KPI tiles
                html.Div(style={**KPI_STYLE_ROW, 'margin': '0 0 20px 0'},
                         children=kpi_tiles),

                # Price charts or warning
                price_row,

                # Export/Import destinations
                dest_row,

                # Data quality panel (toggle)
                data_quality,
            ]
        )

    # ── Data quality panel toggle ─────────────────────────────────────────────
    @app.callback(
        Output('data-quality-panel', 'style'),
        Output('data-quality-toggle', 'children'),
        Output('data-quality-toggle', 'style'),
        Input('data-quality-toggle', 'n_clicks'),
        prevent_initial_call=True,
    )
    def toggle_data_quality(n_clicks):
        if n_clicks and n_clicks % 2 == 1:
            return (
                {'display': 'block'},
                '📊  Hide Data Quality',
                {'backgroundColor': BLUE_ACCENT, 'border': f'1px solid {BLUE_ACCENT}',
                 'borderRadius': '6px', 'color': WHITE, 'cursor': 'pointer',
                 'fontSize': '12px', 'fontWeight': 'bold', 'padding': '6px 14px'},
            )
        else:
            return (
                {'display': 'none'},
                '📊  Data Quality',
                {'backgroundColor': WHITE, 'border': f'1px solid {BLUE_ACCENT}',
                 'borderRadius': '6px', 'color': BLUE_ACCENT, 'cursor': 'pointer',
                 'fontSize': '12px', 'fontWeight': 'bold', 'padding': '6px 14px'},
            )