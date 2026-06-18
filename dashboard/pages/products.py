from dash import html, dcc, dash_table

from ..styles import (
    KPI_STYLE_ROW, KPI_STYLE_BOX, STYLE_CHART_ROW,
    STYLE_CHART_ITEM, BLUE_ACCENT, TEXT_GRAY, WHITE,
    FONT_MAIN, TABLE_STYLE_TABLE, TABLE_STYLE_HEADER,
    TABLE_STYLE_CELL, TABLE_STYLE_DATA_CONDITIONAL,
    FIGURE_TITLE, FIGURE_DESCRIPTION,
    SECTION_TITLE, SECTION_DESCRIPTION
)


def layout():
    return html.Div([

        # ── Section title ──────────────────────────────────────────────────────
        html.Div(children=[
            html.H2('Product Performance', style=SECTION_TITLE),
            html.P('Top traded commodities, HS2 breakdown and growth analysis',
                   style=SECTION_DESCRIPTION),
        ]),

        # ── KPI Row — Product KPIs ─────────────────────────────────────────────
        html.Div(
            style=KPI_STYLE_ROW,
            children=[
                html.Div(style=KPI_STYLE_BOX, children=[
                    html.Div(id='top-HS2'),
                    html.P('Top HS2 category by trade value',
                           style={'color': TEXT_GRAY, 'fontSize': '14px'}),
                ]),
                html.Div(style=KPI_STYLE_BOX, children=[
                    html.Div(id='fastest-growing'),
                    html.P('Fastest growing HS2 vs prior year',
                           style={'color': TEXT_GRAY, 'fontSize': '14px'}),
                ]),
                html.Div(style=KPI_STYLE_BOX, children=[
                    html.Div(id='number-commodities'),
                    html.P('Total unique commodities traded',
                           style={'color': TEXT_GRAY, 'fontSize': '14px'}),
                ]),
            ]
        ),

        # ── Row 1 — HS2 share chart + Top commodities table ───────────────────
        html.Div(
            style=STYLE_CHART_ROW,
            children=[

                html.Div(
                    style=STYLE_CHART_ITEM,
                    children=[
                        html.H4('Trade Share by HS2 Category', style=FIGURE_TITLE),
                        html.P('% of total trade value', style=FIGURE_DESCRIPTION),
                        dcc.Graph(id='hs2-share-chart-products',
                                  config={'displayModeBar': False}),
                    ]
                ),

                html.Div(
                    style={**STYLE_CHART_ITEM, 'flex': '0.8'},
                    children=[
                        html.H4('Top 10 Trading Commodities', style=FIGURE_TITLE),
                        html.P('Share of total Canada trade by commodity',
                               style=FIGURE_DESCRIPTION),
                        dash_table.DataTable(
                            id='top-commodity-table',
                            columns=[
                                {'name': '#',           'id': '#'},
                                {'name': 'Commodity',   'id': 'Commodity'},
                                {'name': 'Exports',     'id': 'Exports'},
                                {'name': 'Imports',     'id': 'Imports'},
                                {'name': 'Total Trade', 'id': 'Total Trade'},
                                {'name': 'Share %',     'id': 'Share %'},
                            ],
                            data=[],
                            style_table=TABLE_STYLE_TABLE,
                            style_header=TABLE_STYLE_HEADER,
                            style_cell=TABLE_STYLE_CELL,
                            style_data_conditional=TABLE_STYLE_DATA_CONDITIONAL,
                            page_size=10,
                        ),
                    ]
                ),

            ]
        ),

        # ── Row 2 — Top 5 Export/Import tables ────────────────────────────────
        html.Div(
            style={**STYLE_CHART_ROW, 'alignItems': 'flex-start'},
            children=[

                html.Div(
                    style={**STYLE_CHART_ITEM, 'flex': '1'},
                    children=[
                        html.H4('Top 5 Exports', style=FIGURE_TITLE),
                        html.P('Highest export commodities', style=FIGURE_DESCRIPTION),
                        dash_table.DataTable(
                            id='top5-export-table-products',
                            columns=[
                                {'name': 'Commodity', 'id': 'Commodity'},
                                {'name': 'Value',     'id': 'Value'},
                                {'name': 'YoY',       'id': 'YoY'},
                            ],
                            data=[],
                            style_table=TABLE_STYLE_TABLE,
                            style_header=TABLE_STYLE_HEADER,
                            style_cell=TABLE_STYLE_CELL,
                            style_data_conditional=[
                                *TABLE_STYLE_DATA_CONDITIONAL,
                                {'if': {'filter_query': '{_yoy_val} > 0',
                                        'column_id': 'YoY'},
                                 'color': '#2d6a4f', 'fontWeight': 'bold'},
                                {'if': {'filter_query': '{_yoy_val} < 0',
                                        'column_id': 'YoY'},
                                 'color': '#C00000', 'fontWeight': 'bold'},
                            ],
                            page_size=5,
                        ),
                    ]
                ),

                html.Div(
                    style={**STYLE_CHART_ITEM, 'flex': '1'},
                    children=[
                        html.H4('Top 5 Imports', style=FIGURE_TITLE),
                        html.P('Highest import commodities', style=FIGURE_DESCRIPTION),
                        dash_table.DataTable(
                            id='top5-import-table-products',
                            columns=[
                                {'name': 'Commodity', 'id': 'Commodity'},
                                {'name': 'Value',     'id': 'Value'},
                                {'name': 'YoY',       'id': 'YoY'},
                            ],
                            data=[],
                            style_table=TABLE_STYLE_TABLE,
                            style_header=TABLE_STYLE_HEADER,
                            style_cell=TABLE_STYLE_CELL,
                            style_data_conditional=[
                                *TABLE_STYLE_DATA_CONDITIONAL,
                                {'if': {'filter_query': '{_yoy_val} > 0',
                                        'column_id': 'YoY'},
                                 'color': '#2d6a4f', 'fontWeight': 'bold'},
                                {'if': {'filter_query': '{_yoy_val} < 0',
                                        'column_id': 'YoY'},
                                 'color': '#C00000', 'fontWeight': 'bold'},
                            ],
                            page_size=5,
                        ),
                    ]
                ),

            ]
        ),

    ])