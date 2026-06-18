from dash import html, Input, Output

from .data import df, df_kpi, period_index, df_kpi_commodity
from .utils import (apply_filters, fmt_value, HS2_LABELS,
                    get_fastest_growing_hs2, get_top_hs2_share,
                    get_top_province, get_top_country)
from .charts import (build_monthly_chart, build_top_countries_table,
                     build_top5_tables, build_hs2_share_chart,
                     build_top_commodity_table, build_province_small_multiples)
from .styles import (KPI_STYLE_LABEL, KPI_STYLE_VALUE, RED, BLUE_ACCENT,
                     GREEN_TREND, TEXT_GRAY, KPI_TEXT_VALUE, KPI_NOTE)
from .pages import overview, products, geography


def register_callbacks(app):

    # ── Routing ───────────────────────────────────────────────────────────────
    @app.callback(
        Output('page-content', 'children'),
        Input('url', 'pathname')
    )
    def render_page(pathname):
        print('pathname:', pathname)
        if pathname == '/products':
            return products.layout()
        elif pathname == '/geography':
            return geography.layout()
        else:
            return overview.layout()

    # ── Enforce ALL ───────────────────────────────────────────────────────────
    @app.callback(
        Output('hs2-dropdown',        'value'),
        Output('province-dropdown',   'value'),
        Output('country-dropdown',    'value'),
        Output('trade-type-dropdown', 'value'),
        Input('hs2-dropdown',         'value'),
        Input('province-dropdown',    'value'),
        Input('country-dropdown',     'value'),
        Input('trade-type-dropdown',  'value'),
        prevent_initial_call=True,
    )
    def enforce_all(hs2, province, country, trade_type):
        def fix(selected):
            if not selected:
                return ['ALL']
            if len(selected) > 1 and 'ALL' in selected:
                return [v for v in selected if v != 'ALL']
            return selected
        return fix(hs2), fix(province), fix(country), fix(trade_type)

    # ── Overview KPIs ─────────────────────────────────────────────────────────
    @app.callback(
        Output('total-export',   'children'),
        Output('total-import',   'children'),
        Output('trade-balance',  'children'),
        Input('period-slider',        'value'),
        Input('hs2-dropdown',         'value'),
        Input('province-dropdown',    'value'),
        Input('country-dropdown',     'value'),
        Input('trade-type-dropdown',  'value'),
    )
    def update_overview_kpis(period_range, selected_hs2, selected_province,
                             selected_country, selected_trade_type):
        filtered = apply_filters(df_kpi, period_range, selected_hs2,
                                 selected_province, selected_country,
                                 period_index=period_index,
                                 selected_trade_type=selected_trade_type)

        total_export  = filtered[filtered['trade_type'] == 'Export']['Value ($)'].sum()
        total_import  = filtered[filtered['trade_type'] == 'Import']['Value ($)'].sum()
        trade_balance = total_export - total_import
        balance_color = RED if trade_balance < 0 else BLUE_ACCENT

        kpi_export = [
            html.P('Total Exports', style=KPI_STYLE_LABEL),
            html.H2(fmt_value(total_export), style=KPI_STYLE_VALUE),
        ]
        kpi_import = [
            html.P('Total Imports', style=KPI_STYLE_LABEL),
            html.H2(fmt_value(total_import), style=KPI_STYLE_VALUE),
        ]
        kpi_balance = [
            html.P('Trade Balance', style=KPI_STYLE_LABEL),
            html.H2(fmt_value(trade_balance),
                    style={**KPI_STYLE_VALUE, 'color': balance_color}),
        ]
        return kpi_export, kpi_import, kpi_balance

    # ── Overview Charts ───────────────────────────────────────────────────────
    @app.callback(
        Output('monthly-trade',       'figure'),
        Output('top-countries-table', 'data'),
        Output('top5-export-table',   'data'),
        Output('top5-import-table',   'data'),
        Output('hs2-share-chart',     'figure'),
        Input('period-slider',        'value'),
        Input('hs2-dropdown',         'value'),
        Input('province-dropdown',    'value'),
        Input('country-dropdown',     'value'),
        Input('trade-type-dropdown',  'value'),
    )
    def update_overview_charts(period_range, selected_hs2, selected_province,
                               selected_country, selected_trade_type):
        filtered = apply_filters(df, period_range, selected_hs2,
                                 selected_province, selected_country,
                                 period_index=period_index,
                                 selected_trade_type=selected_trade_type)
        export_records, import_records = build_top5_tables(filtered, df_kpi_commodity)
        return (
            build_monthly_chart(filtered),
            build_top_countries_table(filtered),
            export_records,
            import_records,
            build_hs2_share_chart(filtered),
        )

    # ── Products KPIs ─────────────────────────────────────────────────────────
    @app.callback(
        Output('top-HS2',            'children'),
        Output('fastest-growing',    'children'),
        Output('number-commodities', 'children'),
        Input('period-slider',        'value'),
        Input('hs2-dropdown',         'value'),
        Input('province-dropdown',    'value'),
        Input('country-dropdown',     'value'),
        Input('trade-type-dropdown',  'value'),
    )
    def update_products_kpis(period_range, selected_hs2, selected_province,
                             selected_country, selected_trade_type):
        filtered = apply_filters(df_kpi, period_range, selected_hs2,
                                 selected_province, selected_country,
                                 period_index=period_index,
                                 selected_trade_type=selected_trade_type)
        filtered_commodity = apply_filters(df_kpi_commodity, period_range, None,
                                           selected_province, selected_country,
                                           period_index=period_index,
                                           selected_trade_type=selected_trade_type)

        # Top HS2
        hs2_code, pct, note = get_top_hs2_share(filtered)
        clean_name = HS2_LABELS.get(str(hs2_code), str(hs2_code))
        kpi_top_hs2 = [
            html.P('Top HS2 Category', style=KPI_STYLE_LABEL),
            html.P(clean_name, style=KPI_TEXT_VALUE),
            html.P(f'{pct:.1f}%', style=KPI_STYLE_VALUE),
            html.P(note, style=KPI_NOTE),
        ]

        # Fastest growing HS2
        hs2_code, pct, note = get_fastest_growing_hs2(filtered, df_kpi)
        clean_name = HS2_LABELS.get(str(hs2_code), str(hs2_code)) if hs2_code else 'N/A'
        if pct is not None:
            yoy_str   = f'+{pct:.1f}%' if pct >= 0 else f'{pct:.1f}%'
            yoy_color = GREEN_TREND if pct >= 0 else RED
            note_str  = '% vs same period prior year'
        else:
            yoy_str   = 'N/A'
            yoy_color = TEXT_GRAY
            note_str  = note or ''
        kpi_fast_hs2 = [
            html.P('Fastest Growing HS2', style=KPI_STYLE_LABEL),
            html.P(clean_name, style=KPI_TEXT_VALUE),
            html.P(yoy_str, style={**KPI_STYLE_VALUE, 'color': yoy_color}),
            html.P(note_str, style=KPI_NOTE),
        ]

        # Number of commodities
        number_commodities = filtered_commodity['Commodity'].nunique()
        kpi_number_commodities = [
            html.P('Number of Commodities', style=KPI_STYLE_LABEL),
            html.H2(f'{number_commodities:,}', style=KPI_STYLE_VALUE),
            html.P('Total unique commodities traded', style=KPI_NOTE),
        ]

        return kpi_top_hs2, kpi_fast_hs2, kpi_number_commodities

    # ── Products Charts ───────────────────────────────────────────────────────
    @app.callback(
        Output('hs2-share-chart-products',    'figure'),
        Output('top-commodity-table',         'data'),
        Output('top5-export-table-products',  'data'),
        Output('top5-import-table-products',  'data'),
        Input('period-slider',        'value'),
        Input('hs2-dropdown',         'value'),
        Input('province-dropdown',    'value'),
        Input('country-dropdown',     'value'),
        Input('trade-type-dropdown',  'value'),
    )
    def update_products_charts(period_range, selected_hs2, selected_province,
                               selected_country, selected_trade_type):
        filtered = apply_filters(df, period_range, selected_hs2,
                                 selected_province, selected_country,
                                 period_index=period_index,
                                 selected_trade_type=selected_trade_type)
        filtered_commodity = apply_filters(df_kpi_commodity, period_range, None,
                                           selected_province, selected_country,
                                           period_index=period_index,
                                           selected_trade_type=selected_trade_type)
        export_records, import_records = build_top5_tables(filtered, df_kpi_commodity)
        return (
            build_hs2_share_chart(filtered),
            build_top_commodity_table(filtered_commodity),
            export_records,
            import_records,
        )

    # ── Geography KPIs ────────────────────────────────────────────────────────
    @app.callback(
        Output('top-province',    'children'),
        Output('top-country',     'children'),
        Output('number-countries','children'),
        Input('period-slider',        'value'),
        Input('hs2-dropdown',         'value'),
        Input('province-dropdown',    'value'),
        Input('country-dropdown',     'value'),
        Input('trade-type-dropdown',  'value'),
    )
    def update_geography_kpis(period_range, selected_hs2, selected_province,
                              selected_country, selected_trade_type):
        filtered = apply_filters(df_kpi, period_range, selected_hs2,
                                 selected_province, selected_country,
                                 period_index=period_index,
                                 selected_trade_type=selected_trade_type)
        filtered_commodity = apply_filters(df_kpi_commodity, period_range, None,
                                           selected_province, selected_country,
                                           period_index=period_index,
                                           selected_trade_type=selected_trade_type)

        province_name, pct, note = get_top_province(filtered)
        kpi_top_province = [
            html.P('Top Province', style=KPI_STYLE_LABEL),
            html.P(province_name, style=KPI_TEXT_VALUE),
            html.P(f'{pct:.1f}%', style=KPI_STYLE_VALUE),
            html.P(note, style=KPI_NOTE),
        ]

        country_name, pct, note = get_top_country(filtered)
        kpi_top_country = [
            html.P('Top Country', style=KPI_STYLE_LABEL),
            html.P(country_name, style=KPI_TEXT_VALUE),
            html.P(f'{pct:.1f}%', style=KPI_STYLE_VALUE),
            html.P(note, style=KPI_NOTE),
        ]

        number_countries = filtered_commodity['Country'].nunique()
        kpi_number_country = [
            html.P('Number of Countries', style=KPI_STYLE_LABEL),
            html.H2(f'{number_countries:,}', style=KPI_STYLE_VALUE),
            html.P('Total unique countries', style=KPI_NOTE),
        ]

        return kpi_top_province, kpi_top_country, kpi_number_country

    # ── Geography Charts ──────────────────────────────────────────────────────
    @app.callback(
        Output('province-small-multiples', 'figure'),
        Output('hs2-share-chart-geo',      'figure'),
        Output('top-countries-table-geo',  'data'),
        Input('period-slider',        'value'),
        Input('hs2-dropdown',         'value'),
        Input('province-dropdown',    'value'),
        Input('country-dropdown',     'value'),
        Input('trade-type-dropdown',  'value'),
    )
    def update_geography_charts(period_range, selected_hs2, selected_province,
                                selected_country, selected_trade_type):
        filtered = apply_filters(df, period_range, selected_hs2,
                                 selected_province, selected_country,
                                 period_index=period_index,
                                 selected_trade_type=selected_trade_type)
        return (
            build_province_small_multiples(filtered),
            build_hs2_share_chart(filtered),
            build_top_countries_table(filtered),
        )