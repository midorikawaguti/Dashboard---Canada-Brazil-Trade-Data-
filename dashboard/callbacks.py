from dash import html, dcc, Input, Output

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
    # PRODUCTS — LEVEL 1: Section selection synced with treemap click
    # ══════════════════════════════════════════════════════════════════════════
    @app.callback(
        Output('products-section-select', 'value'),
        Input('products-treemap', 'clickData'),
        prevent_initial_call=True,
    )
    def sync_treemap_to_dropdown(click_data):
        """When user clicks a section in the treemap, update the section dropdown."""
        if not click_data:
            return None
        clicked_label = click_data['points'][0].get('label', None)
        # Only accept section-level clicks (parents are empty string)
        parent = click_data['points'][0].get('parent', None)
        if parent == '':
            return clicked_label
        # If clicked on HS2 child, return its parent section
        return parent if parent else None

    # ══════════════════════════════════════════════════════════════════════════
    # PRODUCTS — LEVEL 2: HS2 dropdown options based on selected section
    # ══════════════════════════════════════════════════════════════════════════
    @app.callback(
        Output('products-hs2-select', 'options'),
        Output('products-hs2-select', 'value'),
        Input('products-section-select', 'value'),
        Input('period-slider',           'value'),
        Input('province-dropdown',       'value'),
        Input('trade-type-dropdown',     'value'),
    )
    def update_hs2_options(selected_section, period_range,
                           selected_province, selected_trade_type):
        """Populate HS2 dropdown with codes that belong to the selected section."""
        hs2_filter = get_hs2_codes_for_section(selected_section, hs2_to_section)

        filtered = apply_filters(
            df_kpi, period_range, hs2_filter,
            selected_province, None,
            selected_trade_type, period_index=period_index
        )

        if filtered.empty:
            return [], None

        # Get HS2 codes present in filtered data
        available_hs2 = filtered['HS2'].unique().tolist()

        options = [
            {'label': f"{code} – {HS2_LABELS.get(str(code), str(code))}",
             'value': code}
            for code in sorted(available_hs2)
        ]
        return options, None   # reset HS2 selection when section changes

    # ══════════════════════════════════════════════════════════════════════════
    # PRODUCTS — Main charts/KPIs (update on section OR hs2 selection)
    # ══════════════════════════════════════════════════════════════════════════
    @app.callback(
        # KPIs
        Output('top-HS2',            'children'),
        Output('fastest-growing',    'children'),
        Output('number-commodities', 'children'),
        #Output('products-avg-price', 'children'),
        # Charts
        Output('products-treemap',             'figure'),
        Output('hs2-share-chart-products',     'figure'),
        #Output('top-commodity-table',          'data'),
        Output('top5-export-table-products',   'data'),
        Output('top5-import-table-products',   'data'),
        Output('products-export-destinations', 'figure'),
        Output('products-import-origins',      'figure'),
        # Inputs — global filters
        Input('period-slider',           'value'),
        Input('province-dropdown',       'value'),
        Input('country-dropdown',        'value'),
        Input('trade-type-dropdown',     'value'),
        # Inputs — page-specific
        Input('products-section-select', 'value'),  # Level 1
        Input('products-hs2-select',     'value'),  # Level 2
    )
    def update_products(period_range, selected_province, selected_country,
                        selected_trade_type, selected_section, selected_hs2):

        # Level 1: filter by section → list of HS2 codes
        section_hs2_filter = get_hs2_codes_for_section(selected_section, hs2_to_section)

        # Level 2: if specific HS2 selected, filter further to just that code
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
        # Filter full df by hs2_filter (has HS2 column), then re-aggregate
        # to commodity level — df_kpi_commodity has no HS2 column
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
            html.P(clean_name[:28],
                   style={**KPI_STYLE_VALUE, 'fontSize': '14px'}),
            html.P(f'{pct_top:.1f}% of total trade', style=KPI_NOTE),
        ]

        hs2_fast, pct_fast, note_fast = get_fastest_growing_hs2(
            filtered_kpi, df_kpi
        )
        fast_label = HS2_LABELS.get(str(hs2_fast), str(hs2_fast)) \
                     if hs2_fast else 'N/A'
        if pct_fast is not None:
            fast_str   = f'+{pct_fast:.1f}%' if pct_fast >= 0 else f'{pct_fast:.1f}%'
            fast_color = GREEN_TREND if pct_fast >= 0 else RED
            fast_note  = '% vs same period prior year'
        else:
            fast_str, fast_color, fast_note = 'N/A', TEXT_GRAY, note_fast or ''
        kpi_fastest = [
            html.P(fast_str,
                   style={**KPI_STYLE_VALUE, 'color': fast_color}),
            html.P(fast_label[:28], style=KPI_TEXT_VALUE),
            html.P(fast_note, style=KPI_NOTE),
        ]

        n_commodities = filtered_commodity['Commodity'].nunique()
        kpi_commodities = [html.H2(f'{n_commodities:,}', style=KPI_STYLE_VALUE)]

        price_df = filtered[
            (filtered['Quantity'] > 0) &
            (filtered['Unit of measure'] != 'Blank')
        ].copy()
        if not price_df.empty:
            price_df['ppu'] = price_df['Value ($)'] / price_df['Quantity']
            avg_price = price_df['ppu'].median()
            kpi_price = [html.H2(f'{fmt_value(avg_price)}/unit',
                                 style=KPI_STYLE_VALUE)]
        else:
            kpi_price = [html.H2('N/A', style=KPI_STYLE_VALUE)]

        # ── Charts ────────────────────────────────────────────────────────────
        # Treemap always shows Section level (ignores hs2_filter)
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
            #kpi_price,
            build_hs2_treemap(filtered_kpi_sections,
                              hs2_to_section, hs2_to_description),
            build_hs2_share_chart(filtered_kpi),
            #build_top_commodity_table(filtered_commodity),
            export_records,
            import_records,
            build_export_destinations(filtered),
            build_import_origins(filtered),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # PRODUCTS — LEVEL 3: Commodity dropdown options
    # ══════════════════════════════════════════════════════════════════════════
    @app.callback(
        Output('products-commodity-select', 'options'),
        Output('products-commodity-select', 'value'),
        Input('period-slider',          'value'),
        Input('province-dropdown',      'value'),
        Input('trade-type-dropdown',    'value'),
        Input('products-hs2-select',    'value'),   # Level 2
        Input('products-section-select','value'),   # Level 1 fallback
    )
    def update_commodity_options(period_range, selected_province,
                                 selected_trade_type, selected_hs2,
                                 selected_section):
        # Use HS2 filter if selected, else use section filter
        if selected_hs2:
            hs2_filter = [selected_hs2]
        else:
            hs2_filter = get_hs2_codes_for_section(selected_section, hs2_to_section)

        # Filter df (has HS2 column), then re-aggregate to commodity level
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
            return [], None

        top_commodities = (
            filtered
            .groupby('Commodity', observed=True)['Value ($)']
            .sum()
            .nlargest(200)
            .index.tolist()
        )
        options = [{'label': str(c)[:60], 'value': c}
                   for c in sorted(top_commodities)]
        return options, None

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

        avg_price_str = fmt_value(kpis['avg_price']) + '/unit' \
                        if kpis['avg_price'] else 'N/A'

        if kpis['yoy_price'] is not None:
            yoy_str   = f'+{kpis["yoy_price"]:.1f}%' \
                        if kpis['yoy_price'] >= 0 \
                        else f'{kpis["yoy_price"]:.1f}%'
            yoy_color = GREEN_TREND if kpis['yoy_price'] >= 0 else RED
        else:
            yoy_str, yoy_color = 'N/A', TEXT_GRAY

        short_name = str(selected_commodity)[:80] + '...' \
                     if len(str(selected_commodity)) > 80 \
                     else str(selected_commodity)

        return html.Div(
            style={
                'backgroundColor': WHITE,
                'borderRadius':    '10px',
                'padding':         '20px 24px',
                'marginTop':       '16px',
                'boxShadow':       '0 1px 4px rgba(0,0,0,0.07)',
                'borderLeft':      f'4px solid {BLUE_ACCENT}',
            },
            children=[

                # Panel title
                html.Div(style={'marginBottom': '16px'}, children=[
                    html.H4(f'🔬  {short_name}',
                            style={'margin': '0 0 4px 0', 'color': BLUE_ACCENT,
                                   'fontSize': '15px', 'fontWeight': 'bold'}),
                    html.P('Price distribution, trend, seasonality and trade partners',
                           style={'margin': '0', 'color': TEXT_GRAY,
                                  'fontSize': '12px', 'fontStyle': 'italic'}),
                ]),

                # KPI row
                html.Div(
                    style={**KPI_STYLE_ROW, 'margin': '0 0 20px 0'},
                    children=[
                        html.Div(style=KPI_STYLE_BOX, children=[
                            html.H2(fmt_value(kpis['total_value']),
                                    style=KPI_STYLE_VALUE),
                            html.P('Total Trade Value',
                                   style={'color': TEXT_GRAY, 'fontSize': '12px',
                                          'margin': '4px 0 0 0'}),
                        ]),
                        html.Div(style=KPI_STYLE_BOX, children=[
                            html.H2(f'{kpis["total_quantity"]:,.0f}',
                                    style=KPI_STYLE_VALUE),
                            html.P(f'Total Quantity ({kpis["unit"]})',
                                   style={'color': TEXT_GRAY, 'fontSize': '12px',
                                          'margin': '4px 0 0 0'}),
                        ]),
                        html.Div(style=KPI_STYLE_BOX, children=[
                            html.H2(avg_price_str, style=KPI_STYLE_VALUE),
                            html.P('Avg Price per Unit',
                                   style={'color': TEXT_GRAY, 'fontSize': '12px',
                                          'margin': '4px 0 0 0'}),
                        ]),
                        html.Div(style=KPI_STYLE_BOX, children=[
                            html.H2(yoy_str,
                                    style={**KPI_STYLE_VALUE, 'color': yoy_color}),
                            html.P('YoY Price Change',
                                   style={'color': TEXT_GRAY, 'fontSize': '12px',
                                          'margin': '4px 0 0 0'}),
                            html.P('vs same period prior year',
                                   style={'color': TEXT_GRAY, 'fontSize': '10px',
                                          'fontStyle': 'italic',
                                          'margin': '2px 0 0 0'}),
                        ]),
                    ]
                ),

                # Row 1: Histogram + Price over time + Seasonality
                html.Div(
                    style={**STYLE_CHART_ROW, 'margin': '0 0 16px 0'},
                    children=[
                        html.Div(style={**STYLE_CHART_ITEM, 'flex': '1'}, children=[
                            html.H4('Price Distribution', style=FIGURE_TITLE),
                            html.P('Frequency of price per unit',
                                   style=FIGURE_DESCRIPTION),
                            dcc.Graph(
                                figure=build_price_histogram(filtered,
                                                             selected_commodity),
                                config={'displayModeBar': False}
                            ),
                        ]),
                        html.Div(style={**STYLE_CHART_ITEM, 'flex': '1'}, children=[
                            html.H4('Avg Price Over Time', style=FIGURE_TITLE),
                            html.P('Monthly median price per unit',
                                   style=FIGURE_DESCRIPTION),
                            dcc.Graph(
                                figure=build_price_over_time(filtered,
                                                             selected_commodity),
                                config={'displayModeBar': False}
                            ),
                        ]),
                        html.Div(style={**STYLE_CHART_ITEM, 'flex': '1'}, children=[
                            html.H4('Seasonality', style=FIGURE_TITLE),
                            html.P('Avg monthly trade value across years',
                                   style=FIGURE_DESCRIPTION),
                            dcc.Graph(
                                figure=build_seasonality_chart(filtered,
                                                               selected_commodity),
                                config={'displayModeBar': False}
                            ),
                        ]),
                    ]
                ),

                # Row 2: Export destinations + Import origins
                html.Div(
                    style={**STYLE_CHART_ROW, 'margin': '0'},
                    children=[
                        html.Div(style={**STYLE_CHART_ITEM, 'flex': '1'}, children=[
                            html.H4('Top Export Destinations', style=FIGURE_TITLE),
                            html.P('Countries buying this commodity from Canada',
                                   style=FIGURE_DESCRIPTION),
                            dcc.Graph(
                                figure=build_commodity_export_destinations(
                                    filtered, selected_commodity),
                                config={'displayModeBar': False}
                            ),
                        ]),
                        html.Div(style={**STYLE_CHART_ITEM, 'flex': '1'}, children=[
                            html.H4('Top Import Origins', style=FIGURE_TITLE),
                            html.P('Countries supplying this commodity to Canada',
                                   style=FIGURE_DESCRIPTION),
                            dcc.Graph(
                                figure=build_commodity_import_origins(
                                    filtered, selected_commodity),
                                config={'displayModeBar': False}
                            ),
                        ]),
                    ]
                ),

            ]
        )