from dash import html, Input, Output

from .data import df, df_kpi, period_index
from .utils import apply_filters, fmt_value
from .charts import build_monthly_chart, build_top_countries_table, build_top5_tables, build_hs2_share_chart
from .styles import KPI_STYLE_LABEL, KPI_STYLE_VALUE, RED, BLUE_ACCENT
from .pages import overview, products, geography



def register_callbacks(app):

    # ── Routing ───────────────────────────────────────────────────────────────
    @app.callback(
        Output('page-content', 'children'),
        Input('url', 'pathname')
    )
    def render_page(pathname):
        if pathname == '/products':
            return products.layout()
        elif pathname == '/geography':
            return geography.layout()
        else:
            return overview.layout()   # default → Overview

    # ── Enforce ALL when dropdowns are empty ──────────────────────────────────
    @app.callback(
        
        Output('hs2-dropdown', 'value'),
        Output('province-dropdown',  'value'),
        Output('country-dropdown',   'value'),
      
        Input('hs2-dropdown',  'value'),
        Input('province-dropdown',   'value'),
        Input('country-dropdown',    'value'),
        prevent_initial_call=True,
    )
    def enforce_all( hs2, province, country):
        def fix(selected):
            if not selected:
                return ['ALL']
            if len(selected) > 1 and 'ALL' in selected:
                return [v for v in selected if v != 'ALL']
            return selected

        return fix(hs2), fix(province), fix(country)

    # ── Overview: KPI cards ───────────────────────────────────────────────────
    @app.callback(
        Output('total-export',  'children'),
        Output('total-import',  'children'),
        Output('trade-balance', 'children'),


        Input('period-slider', 'value'),
        Input('hs2-dropdown', 'value'),
        Input('province-dropdown', 'value'),
        Input('country-dropdown',  'value'),
    )
    def update_metrics(period_range, selected_hs2, selected_province, selected_country):
        filtered = apply_filters(df_kpi, period_range, selected_hs2,
                                 selected_province, selected_country,
                                 period_index=period_index)

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

    # ── Overview: Charts ──────────────────────────────────────────────────────
    @app.callback(
        Output('monthly-trade',  'figure'),
        #Output('top-countries',  'figure'),
        Output('top-countries-table', 'data'),
        Output('top5-export-table',   'data'),     
        Output('top5-import-table',   'data'),     
        Output('hs2-share-chart',     'figure'),

        Input('period-slider',      'value'),
        Input('hs2-dropdown', 'value'),
        Input('province-dropdown',  'value'),
        Input('country-dropdown',   'value'),
    )
    def update_charts(period_range, selected_hs2, selected_province, selected_country):
        print('period_range:', period_range)
        # Charts need the full df (Period column for month grouping)
        filtered = apply_filters(df, period_range, selected_hs2,
                                 selected_province, selected_country,
                                 period_index=period_index)

        export_records, import_records = build_top5_tables(filtered)
        
        return (build_monthly_chart(filtered), 
                #build_top_countries(filtered), 
                build_top_countries_table(filtered),
                export_records,                        
                import_records,                        
                build_hs2_share_chart(filtered) )      

    # ── Products callbacks (add here as you build the Products page) ──────────
    # @app.callback(
    #     Output('top-products', 'figure'),
    #     Input('year-dropdown', 'value'), ...
    # )
    # def update_products(...): ...

    # ── Geography callbacks (add here as you build the Geography page) ────────
    # @app.callback(
    #     Output('province-map', 'figure'),
    #     Input('year-dropdown', 'value'), ...
    # )
    # def update_geography(...): ...
