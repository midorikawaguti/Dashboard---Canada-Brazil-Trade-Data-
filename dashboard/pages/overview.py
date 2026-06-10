from dash import html, dcc, dash_table

from ..styles import (
    KPI_STYLE_ROW, KPI_STYLE_BOX, STYLE_CHART_ROW,
    STYLE_CHART_ITEM, BLUE_ACCENT, TEXT_GRAY, DARK_GREEN, WHITE,
    FONT_MAIN, TABLE_STYLE_TABLE, TABLE_STYLE_HEADER,
    TABLE_STYLE_CELL, TABLE_STYLE_DATA_CONDITIONAL,
    FIGURE_TITLE, FIGURE_DESCRIPTION,
    SECTION_TITLE, SECTION_DESCRIPTION
)


def layout():
    return html.Div([
        # ── Section 1: OVERVIEW ──────────────────────────────────────────────────────
        # ── Section title ──────────────────────────────────────────────────────
        html.Div(children=[
            html.H2('Overview', style=SECTION_TITLE),
            html.P([
            "This dashboard summarizes ",
            html.Strong("Canada's trade performance"),
            " and highlights ",
            html.Strong("imports, exports, trade growth"),
            ", ",
            html.Strong("top trading partners"),
            ", ",
            html.Strong("HS categories"),
            ", ",
            html.Strong("commodities"),
            ", provincial contributions, and market concentration."
        ], style=SECTION_DESCRIPTION),
        ]),

        # ── KPI cards ──────────────────────────────────────────────────────────
        html.Div(
            style=KPI_STYLE_ROW,
            children=[
                html.Div(style=KPI_STYLE_BOX, children=[
                    html.Div(id='total-export'),
                    html.P('Total Canada Export Value',
                           style={'color': TEXT_GRAY, 'fontSize': '14px'}),
                ]),
                html.Div(style=KPI_STYLE_BOX, children=[
                    html.Div(id='total-import'),
                    html.P('Total Canada Import Value',
                           style={'color': TEXT_GRAY, 'fontSize': '14px'}),
                ]),
                html.Div(style=KPI_STYLE_BOX, children=[
                    html.Div(id='trade-balance'),
                    html.P('Exports minus imports',
                           style={'color': TEXT_GRAY, 'fontSize': '14px'}),
                ]),
            ]
        ),

        # ── Row 1 — Monthly trade chart ────────────────────────────────────────
        html.Div(
            style=STYLE_CHART_ROW,
            children=[
                html.Div(
                    style=STYLE_CHART_ITEM,
                    children=[
                        html.H4('Trade Trend', style=FIGURE_TITLE),
                        html.P('Monthly exports and imports over time', style=FIGURE_DESCRIPTION),
                        dcc.Graph(id='monthly-trade'),
                    ]
                ),
            ]
        ),

        
        # # ── Section 2: PRODUCT ──────────────────────────────────────────────────────
        # # ── Section title ──────────────────────────────────────────────────────
        # html.Div(children=[
        #     html.H2('Product Performance', style=SECTION_TITLE),
        #     html.P('Total trade flow, balance and year-over-year trend', style=SECTION_DESCRIPTION),
        # ]),

        # # ── KPI cards ──────────────────────────────────────────────────────────
        # html.Div(
        #     style=KPI_STYLE_ROW,
        #     children=[
        #         html.Div(style=KPI_STYLE_BOX, children=[
        #             html.Div(id='top-HS2'),
        #             html.P(
        #                    style={'color': TEXT_GRAY, 'fontSize': '14px'}),
        #         ]),
        #         html.Div(style=KPI_STYLE_BOX, children=[
        #             html.Div(id='fastest-growing'),
        #             html.P(
        #                    style={'color': TEXT_GRAY, 'fontSize': '14px'}),
        #         ]),
        #         html.Div(style=KPI_STYLE_BOX, children=[
        #             html.Div(id='number-commodities'),
        #             html.P(
        #                    style={'color': TEXT_GRAY, 'fontSize': '14px'}),
        #         ]),
        #     ]
        # ),


        # # ── Row 2 — Top 10 chart + table ───────────────────────────────────────
        # html.Div(
        #     style=STYLE_CHART_ROW,
        #     children=[

        #         # html.Div(
        #         #     style={**STYLE_CHART_ITEM, 'flex': '1.2'},
        #         #     children=[
        #         #         html.H4('Top 10 Trading Partners', style=FIGURE_TITLE),
        #         #         html.P('Share of total Canada trade by country', style=FIGURE_DESCRIPTION),
        #         #         dcc.Graph(id='top-countries'),
        #         #     ]
        #         # ),
        #         # HS2 share chart
        #         html.Div(
        #             style=
        #                 STYLE_CHART_ITEM,
        #             children=[
        #                 html.H4('Trade Share by HS2 Category', style=FIGURE_TITLE),
        #                 html.P('% of total trade value', style=FIGURE_DESCRIPTION),
        #                 dcc.Graph(id='hs2-share-chart',
        #                           config={'displayModeBar': False}),
        #             ]
        #         ),

        #         html.Div(
        #             style={**STYLE_CHART_ITEM, 'flex': '0.8'},
        #             children=[
        #                 html.H4('Top 10 Trading Partners', style=FIGURE_TITLE),
        #                 html.P('Share of total Canada trade by country', style=FIGURE_DESCRIPTION),
        #                 dash_table.DataTable(
        #                     id='top-countries-table',
        #                     columns=[
        #                         {'name': '#',           'id': '#'},
        #                         {'name': 'Country',     'id': 'Country'},
        #                         {'name': 'Exports',     'id': 'Exports'},
        #                         {'name': 'Imports',     'id': 'Imports'},
        #                         {'name': 'Total Trade', 'id': 'Total Trade'},
        #                         {'name': 'Share %',     'id': 'Share %'},
        #                     ],
        #                     data=[],
        #                     style_table=TABLE_STYLE_TABLE,
        #                     style_header=TABLE_STYLE_HEADER,
        #                     style_cell=TABLE_STYLE_CELL,
        #                     style_data_conditional=TABLE_STYLE_DATA_CONDITIONAL,
        #                     page_size=10,
        #                 ),
        #             ]
        #         ),

        #     ]
        # ),

        # # ── Row 3 — Top 5 tables + HS2 share chart ────────────────────────────
        # html.Div(
        #     style={**STYLE_CHART_ROW, 'alignItems': 'flex-start'},
        #     children=[

        #         # Top 5 Exports table
        #         html.Div(
        #             style={**STYLE_CHART_ITEM, 'flex': '1'},
        #             children=[
        #                 html.H4('Top 5 Exports', style=FIGURE_TITLE),
        #                 html.P('Highest export commodities', style=FIGURE_DESCRIPTION),

        #                 dash_table.DataTable(
        #                     id='top5-export-table',
        #                     columns=[
        #                         {'name': 'Commodity', 'id': 'Commodity'},
        #                         {'name': 'Value',     'id': 'Value'},
        #                         {'name': 'YoY',       'id': 'YoY'},
        #                     ],
        #                     data=[],
        #                     style_table=TABLE_STYLE_TABLE,
        #                     style_header=TABLE_STYLE_HEADER,
        #                     style_cell=TABLE_STYLE_CELL,
        #                     style_data_conditional=[
        #                         *TABLE_STYLE_DATA_CONDITIONAL,

        #                         {
        #                             'if': {
        #                                 'filter_query': '{_yoy_val} > 0',
        #                                 'column_id': 'YoY'
        #                             },
        #                             'color': '#2d6a4f',
        #                             'fontWeight': 'bold'
        #                         },
        #                         {
        #                             'if': {
        #                                 'filter_query': '{_yoy_val} < 0',
        #                                 'column_id': 'YoY'
        #                             },
        #                             'color': '#C00000',
        #                             'fontWeight': 'bold'
        #                         },
        #                     ],
        #                     page_size=5,
        #                 ),
        #             ]
        #         ),

        #         html.Div(
        #             style={**STYLE_CHART_ITEM, 'flex': '1'},
        #             children=[
        #                 html.H4('Top 5 Imports', style=FIGURE_TITLE),
        #                 html.P('Highest import commodities', style=FIGURE_DESCRIPTION),

        #                 dash_table.DataTable(
        #                     id='top5-import-table',
        #                     columns=[
        #                         {'name': 'Commodity', 'id': 'Commodity'},
        #                         {'name': 'Value',     'id': 'Value'},
        #                         {'name': 'YoY',       'id': 'YoY'},
        #                     ],
        #                     data=[],
        #                     style_table=TABLE_STYLE_TABLE,
        #                     style_header=TABLE_STYLE_HEADER,
        #                     style_cell=TABLE_STYLE_CELL,
        #                     style_data_conditional=[
        #                         *TABLE_STYLE_DATA_CONDITIONAL,

        #                         {
        #                             'if': {
        #                                 'filter_query': '{_yoy_val} > 0',
        #                                 'column_id': 'YoY'
        #                             },
        #                             'color': '#2d6a4f',
        #                             'fontWeight': 'bold'
        #                         },
        #                         {
        #                             'if': {
        #                                 'filter_query': '{_yoy_val} < 0',
        #                                 'column_id': 'YoY'
        #                             },
        #                             'color': '#C00000',
        #                             'fontWeight': 'bold'
        #                         },
        #                     ],
        #                     page_size=5,
        #                 ),
        #             ]
        #         )

        #         # # HS2 share chart
        #         # html.Div(
        #         #     style=
        #         #         STYLE_CHART_ITEM,
        #         #     children=[
        #         #         html.H4('Trade Share by HS2 Category', style=FIGURE_TITLE),
        #         #         html.P('% of total trade value', style=FIGURE_DESCRIPTION),
        #         #         dcc.Graph(id='hs2-share-chart',
        #         #                   config={'displayModeBar': False}),
        #         #     ]
        #         # ),

        #     ]
        # ),

    ])  # ← end of return html.Div