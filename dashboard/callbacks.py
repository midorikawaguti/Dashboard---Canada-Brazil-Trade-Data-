from dash import html, Input, Output, State

from .data import df, df_kpi, df_kpi_commodity, period_index
from .utils import (apply_filters, fmt_value, HS2_LABELS,
                    get_fastest_growing_hs2, get_top_hs2_share,
                    get_top_province, get_top_country)
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
    build_key_insights,
    build_export_destinations,
    build_import_origins,
)
from .styles import (KPI_STYLE_LABEL, KPI_STYLE_VALUE, KPI_TEXT_VALUE, KPI_NOTE,
                     RED, BLUE_ACCENT, GREEN_TREND, TEXT_GRAY, WHITE, DARK_GREEN)
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

    # ── Sidebar nav highlight ──────────────────────────────────────────────────
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
        active   = {**base, 'color': WHITE,   'backgroundColor': 'rgba(255,255,255,0.15)',
                    'borderLeft': '3px solid white'}
        inactive = {**base, 'color': '#B2DFCC', 'borderLeft': '3px solid transparent'}
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
    # OVERVIEW CALLBACKS
    # ══════════════════════════════════════════════════════════════════════════

    @app.callback(
        # KPIs
        Output('total-export',         'children'),
        Output('total-import',         'children'),
        Output('trade-balance',        'children'),
        #Output('overview-yoy',         'children'),
        Output('overview-top-partner', 'children'),
        Output('overview-top-province','children'),
        # Charts
        Output('monthly-trade',           'figure'),
        #Output('top-provinces-bar',       'figure'),
        Output('top-partners-bar',        'figure'),
        #Output('hs2-treemap',             'figure'),
        Output('province-balance-bar',    'figure'),
        #Output('key-insights-panel',      'children'),
        Output('province-small-multiples','figure'),
        #Output('top-countries-table',     'data'),
        #Output('top5-export-table',       'data'),
        #Output('top5-import-table',       'data'),
        # Inputs
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
        filtered_commodity = apply_filters(
            df_kpi_commodity, period_range, None,
            selected_province, selected_country,
            selected_trade_type, period_index=period_index
        )

        # ── KPIs ──────────────────────────────────────────────────────────────
        total_export  = filtered_kpi[filtered_kpi['trade_type'] == 'Export']['Value ($)'].sum()
        total_import  = filtered_kpi[filtered_kpi['trade_type'] == 'Import']['Value ($)'].sum()
        trade_balance = total_export - total_import
        balance_color = RED if trade_balance < 0 else BLUE_ACCENT

        kpi_export = [
            html.H2(fmt_value(total_export), style=KPI_STYLE_VALUE),
        ]
        kpi_import = [
            html.H2(fmt_value(total_import), style=KPI_STYLE_VALUE),
        ]
        kpi_balance = [
            html.H2(fmt_value(trade_balance),
                    style={**KPI_STYLE_VALUE, 'color': balance_color}),
        ]

        # # YoY
        # _, yoy_pct, yoy_note = get_fastest_growing_hs2(filtered_kpi, df_kpi)
        # if yoy_pct is not None:
        #     yoy_color = GREEN_TREND if yoy_pct >= 0 else RED
        #     yoy_str   = f'+{yoy_pct:.1f}%' if yoy_pct >= 0 else f'{yoy_pct:.1f}%'
        # else:
        #     yoy_color = TEXT_GRAY
        #     yoy_str   = 'N/A'
        # kpi_yoy = [
        #     html.H2(yoy_str, style={**KPI_STYLE_VALUE, 'color': yoy_color}),
        # ]

        # Top partner
        country_name, country_pct, _ = get_top_country(filtered_kpi)
        kpi_top_partner = [
            html.P(country_name[:20], style={**KPI_STYLE_VALUE, 'fontSize': '16px'}),
            html.P(f'{country_pct:.1f}% of trade', style=KPI_NOTE),
        ]

        # Top province
        province_name, province_pct, _ = get_top_province(filtered_kpi)
        kpi_top_province = [
            html.P(province_name[:20], style={**KPI_STYLE_VALUE, 'fontSize': '16px'}),
            html.P(f'{province_pct:.1f}% of trade', style=KPI_NOTE),
        ]

        # ── Key Insights ──────────────────────────────────────────────────────
        # hs2_top, hs2_pct, _ = get_top_hs2_share(filtered_kpi)
        # hs2_label = HS2_LABELS.get(str(hs2_top), str(hs2_top))

        # hs2_fastest, fastest_pct, fastest_note = get_fastest_growing_hs2(
        #     filtered_kpi, df_kpi
        # )
        # fastest_label = HS2_LABELS.get(str(hs2_fastest), str(hs2_fastest)) \
        #     if hs2_fastest else 'N/A'
        # fastest_str = (
        #     f'+{fastest_pct:.1f}%' if fastest_pct and fastest_pct >= 0
        #     else f'{fastest_pct:.1f}%' if fastest_pct else 'N/A'
        # )
        # fastest_color = GREEN_TREND if fastest_pct and fastest_pct >= 0 else RED

        # balance_label = 'Surplus' if trade_balance >= 0 else 'Deficit'

        # insights = html.Div(
        #     style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '10px'},
        #     children=[
        #         html.Div(style=INSIGHT_CARD_STYLE, children=[
        #             html.P('🌍 Largest Partner', style={'fontSize': '11px',
        #                    'color': TEXT_GRAY, 'margin': '0 0 4px 0'}),
        #             html.P(country_name[:22], style={'fontSize': '13px',
        #                    'fontWeight': 'bold', 'color': BLUE_ACCENT, 'margin': '0'}),
        #             html.P(f'{country_pct:.1f}% of total', style={'fontSize': '11px',
        #                    'color': TEXT_GRAY, 'margin': '2px 0 0 0'}),
        #         ]),
        #         html.Div(style=INSIGHT_CARD_STYLE, children=[
        #             html.P('📦 Largest HS2 Section', style={'fontSize': '11px',
        #                    'color': TEXT_GRAY, 'margin': '0 0 4px 0'}),
        #             html.P(hs2_label[:22], style={'fontSize': '13px',
        #                    'fontWeight': 'bold', 'color': BLUE_ACCENT, 'margin': '0'}),
        #             html.P(f'{hs2_pct:.1f}% of trade', style={'fontSize': '11px',
        #                    'color': TEXT_GRAY, 'margin': '2px 0 0 0'}),
        #         ]),
        #         html.Div(style=INSIGHT_CARD_STYLE, children=[
        #             html.P('📈 Fastest Growing', style={'fontSize': '11px',
        #                    'color': TEXT_GRAY, 'margin': '0 0 4px 0'}),
        #             html.P(fastest_label[:22], style={'fontSize': '13px',
        #                    'fontWeight': 'bold', 'color': BLUE_ACCENT, 'margin': '0'}),
        #             html.P(fastest_str, style={'fontSize': '13px',
        #                    'fontWeight': 'bold', 'color': fastest_color,
        #                    'margin': '2px 0 0 0'}),
        #         ]),
        #         html.Div(style=INSIGHT_CARD_STYLE, children=[
        #             html.P(f'⚖️ Trade {balance_label}', style={'fontSize': '11px',
        #                    'color': TEXT_GRAY, 'margin': '0 0 4px 0'}),
        #             html.P(fmt_value(abs(trade_balance)), style={
        #                    'fontSize': '13px', 'fontWeight': 'bold',
        #                    'color': balance_color, 'margin': '0'}),
        #             html.P('Exports minus imports', style={'fontSize': '11px',
        #                    'color': TEXT_GRAY, 'margin': '2px 0 0 0'}),
        #         ]),
        #     ]
        # )

        # ── Charts ────────────────────────────────────────────────────────────
        export_records, import_records = build_top5_tables(filtered, df_kpi_commodity)

        return (
            kpi_export,
            kpi_import,
            kpi_balance,
            #kpi_yoy,
            kpi_top_partner,
            kpi_top_province,
            build_monthly_chart(filtered),
            #build_top_provinces_bar(filtered_kpi),
            build_top_partners_bar(filtered_kpi),
            #build_hs2_treemap(filtered_kpi),
            build_province_balance_bar(filtered_kpi),
            #insights,
            build_province_small_multiples(filtered),
            #build_top_countries_table(filtered),
            #export_records,
            #import_records,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # PRODUCTS CALLBACKS
    # ══════════════════════════════════════════════════════════════════════════

    @app.callback(
        # KPIs
        Output('top-HS2',             'children'),
        Output('fastest-growing',     'children'),
        Output('number-commodities',  'children'),
        Output('products-avg-price',  'children'),
        # Charts
        Output('products-treemap',             'figure'),
        Output('hs2-share-chart-products',     'figure'),
        Output('top-commodity-table',          'data'),
        Output('top5-export-table-products',   'data'),
        Output('top5-import-table-products',   'data'),
        Output('products-export-destinations', 'figure'),
        Output('products-import-origins',      'figure'),
        # Inputs
        Input('period-slider',        'value'),
        Input('province-dropdown',    'value'),
        Input('country-dropdown',     'value'),
        Input('trade-type-dropdown',  'value'),
        Input('products-hs2-select',  'value'),
    )
    def update_products(period_range, selected_province, selected_country,
                        selected_trade_type, selected_hs2_drill):

        hs2_filter = [selected_hs2_drill] if selected_hs2_drill else None

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
        filtered_commodity = apply_filters(
            df_kpi_commodity, period_range, None,
            selected_province, selected_country,
            selected_trade_type, period_index=period_index
        )

        # ── KPIs ──────────────────────────────────────────────────────────────
        hs2_code, pct_top, note_top = get_top_hs2_share(filtered_kpi)
        clean_name = HS2_LABELS.get(str(hs2_code), str(hs2_code)) if hs2_code else 'N/A'
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
            fast_str   = 'N/A'
            fast_color = TEXT_GRAY
            fast_note  = note_fast or ''
        kpi_fastest = [
            html.P(fast_str, style={**KPI_STYLE_VALUE, 'color': fast_color}),
            html.P(fast_label[:28], style=KPI_TEXT_VALUE),
            html.P(fast_note, style=KPI_NOTE),
        ]

        n_commodities = filtered_commodity['Commodity'].nunique()
        kpi_commodities = [
            html.H2(f'{n_commodities:,}', style=KPI_STYLE_VALUE),
        ]

        price_df = filtered[
            (filtered['Quantity'] > 0) &
            (filtered['Unit of measure'] != 'Blank')
        ].copy()
        if not price_df.empty:
            price_df['ppu'] = price_df['Value ($)'] / price_df['Quantity']
            avg_price       = price_df['ppu'].median()
            kpi_price = [html.H2(f'{fmt_value(avg_price)}/unit', style=KPI_STYLE_VALUE)]
        else:
            kpi_price = [html.H2('N/A', style=KPI_STYLE_VALUE)]

        # ── Charts ────────────────────────────────────────────────────────────
        export_records, import_records = build_top5_tables(filtered, df_kpi_commodity)

        return (
            kpi_top_hs2,
            kpi_fastest,
            kpi_commodities,
            kpi_price,
            build_hs2_treemap(filtered_kpi),
            build_hs2_share_chart(filtered),
            build_top_commodity_table(filtered_commodity),
            export_records,
            import_records,
            build_export_destinations(filtered),
            build_import_origins(filtered),
        )