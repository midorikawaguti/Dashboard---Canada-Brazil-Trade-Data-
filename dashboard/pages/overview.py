from dash import html, dcc, dash_table

from ..styles import (
    KPI_STYLE_ROW, KPI_STYLE_BOX, KPI_STYLE_LABEL, KPI_STYLE_VALUE,
    KPI_TEXT_VALUE, KPI_NOTE,
    STYLE_CHART_ROW, STYLE_CHART_ITEM,
    BLUE_ACCENT, TEXT_GRAY, DARK_GREEN, WHITE, RED, LIGHT_GRAY,
    FONT_MAIN, FONT_BODY,
    TABLE_STYLE_TABLE, TABLE_STYLE_HEADER,
    TABLE_STYLE_CELL, TABLE_STYLE_DATA_CONDITIONAL,
    FIGURE_TITLE, FIGURE_DESCRIPTION,
    SECTION_TITLE, SECTION_DESCRIPTION,
)

INSIGHT_CARD = {
    'flex':            '1',
    'backgroundColor': WHITE,
    'borderRadius':    '8px',
    'padding':         '14px 16px',
    'boxShadow':       '0 1px 4px rgba(0,0,0,0.07)',
    'minWidth':        '140px',
}


def layout():
    return html.Div(
        style={'padding': '20px 24px'},
        children=[

            # ── Page title ─────────────────────────────────────────────────────
            html.H2('Overview', style={**SECTION_TITLE, 'margin': '0 0 4px 0'}),
            html.P(
                'Canada trade flow summary — exports, imports, balance, top partners and provinces',
                style={**SECTION_DESCRIPTION, 'margin': '0 0 20px 0'}
            ),

            # ══════════════════════════════════════════════════════════════════
            # KPI ROW
            # ══════════════════════════════════════════════════════════════════
            html.Div(
                style={**KPI_STYLE_ROW, 'margin': '0 0 20px 0'},
                children=[
                    html.Div(style=KPI_STYLE_BOX, children=[
                        html.Div(id='total-export'),
                        html.P('Total Exports',
                               style={'color': TEXT_GRAY, 'fontSize': '12px',
                                      'margin': '4px 0 0 0'}),
                    ]),
                    html.Div(style=KPI_STYLE_BOX, children=[
                        html.Div(id='total-import'),
                        html.P('Total Imports',
                               style={'color': TEXT_GRAY, 'fontSize': '12px',
                                      'margin': '4px 0 0 0'}),
                    ]),
                    html.Div(style=KPI_STYLE_BOX, children=[
                        html.Div(id='trade-balance'),
                        html.P('Trade Balance',
                               style={'color': TEXT_GRAY, 'fontSize': '12px',
                                      'margin': '4px 0 0 0'}),
                    ]),
                    # html.Div(style=KPI_STYLE_BOX, children=[
                    #     html.Div(id='overview-yoy'),
                    #     html.P('YoY Growth',
                    #            style={'color': TEXT_GRAY, 'fontSize': '12px',
                    #                   'margin': '4px 0 0 0'}),
                    # ]),
                    html.Div(style=KPI_STYLE_BOX, children=[
                        html.Div(id='overview-top-partner'),
                        html.P('Top Trade Partner',
                               style={'color': TEXT_GRAY, 'fontSize': '12px',
                                      'margin': '4px 0 0 0'}),
                    ]),
                    html.Div(style=KPI_STYLE_BOX, children=[
                        html.Div(id='overview-top-province'),
                        html.P('Top Province',
                               style={'color': TEXT_GRAY, 'fontSize': '12px',
                                      'margin': '4px 0 0 0'}),
                    ]),
                ]
            ),

            # ══════════════════════════════════════════════════════════════════
            # ROW 1 — Trade Trend + Top 5 Provinces + Top 5 Partners 
            # ══════════════════════════════════════════════════════════════════
            html.Div(
                style={**STYLE_CHART_ROW, 'margin': '0 0 16px 0'},
                children=[

                    # Trade trend (diverging bar)
                    html.Div(
                        style={**STYLE_CHART_ITEM, 'flex': '1.4'},
                        children=[
                            html.H4('Trade Value Over Time', style=FIGURE_TITLE),
                            html.P('Monthly exports and imports',
                                   style=FIGURE_DESCRIPTION),
                            dcc.Graph(id='monthly-trade',
                                      config={'displayModeBar': False}),
                        ]
                    ),

                ]
            ),

            # ══════════════════════════════════════════════════════════════════
            # ROW 2 — Trade Balance by Province + Key Insights
            # ══════════════════════════════════════════════════════════════════
            html.Div(
                style={**STYLE_CHART_ROW, 'margin': '0 0 16px 0'},
                children=[

                    # Trade balance by province diverging bar
                    html.Div(
                        style={**STYLE_CHART_ITEM, 'flex': '1.5'},
                        children=[
                            html.H4('Trade Balance by Province', style=FIGURE_TITLE),
                            html.P('Exports minus imports per province',
                                   style=FIGURE_DESCRIPTION),
                            dcc.Graph(id='province-balance-bar',
                                      config={'displayModeBar': False}),
                        ]
                    ),

                ]
            ),

            # ══════════════════════════════════════════════════════════════════
            # ROW 3 — Province small multiples 
            # ══════════════════════════════════════════════════════════════════
            html.Div(
                style={**STYLE_CHART_ROW, 'margin': '0 0 16px 0'},
                children=[
                    html.Div(
                        style=STYLE_CHART_ITEM,
                        children=[
                            html.H4('Export vs Import by Province', style=FIGURE_TITLE),
                            html.P('Top 4 provinces — share of export and import value',
                                   style=FIGURE_DESCRIPTION),
                            dcc.Graph(id='province-small-multiples',
                                      config={'displayModeBar': False}),
                        ]
                    ),
                ]
            ),

            # ══════════════════════════════════════════════════════════════════
            # ROW 4 — Trade Balance by Province + Key Insights
            # ══════════════════════════════════════════════════════════════════

            html.Div(
                style={**STYLE_CHART_ROW, 'margin': '0 0 16px 0'},
                children=[

            # Top 5 partners bar
                    html.Div(
                        style={**STYLE_CHART_ITEM, 'flex': '0.9'},
                        children=[
                            html.H4('Top 10 Trading Partners', style=FIGURE_TITLE),
                            html.P('By total trade value', style=FIGURE_DESCRIPTION),
                            dcc.Graph(id='top-partners-bar',
                                        config={'displayModeBar': False}),
                        ]
                    ),

                ]
            ),
            # ══════════════════════════════════════════════════════════════════
            # ROW 4 — Top countries table + Top 5 Export/Import tables
            # ══════════════════════════════════════════════════════════════════
            # html.Div(
            #     style={**STYLE_CHART_ROW,'margin': '0 0 16px 0'},
            #     children=[

            #         html.Div(
            #             style={**STYLE_CHART_ITEM, 'flex': '0.9'},
            #             children=[
            #                 html.H4('Top 10 Trading Partners', style=FIGURE_TITLE),
            #                 html.P('Ranked by total trade value with share %',
            #                        style=FIGURE_DESCRIPTION),
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

            #         html.Div(
            #             style={**STYLE_CHART_ITEM, 'flex': '0.9'},
            #             children=[
            #                 html.H4('Top 5 Export Commodities', style=FIGURE_TITLE),
            #                 html.P('YoY vs same period prior year',
            #                        style=FIGURE_DESCRIPTION),
            #                 dash_table.DataTable(
            #                     id='top5-export-table',
            #                     columns=[
            #                         {'name': 'Commodity', 'id': 'Commodity'},
            #                         {'name': 'Value',     'id': 'Value'},
            #                         {'name': 'YoY',       'id': 'YoY'},
            #                     ],
            #                     data=[],
            #                     style_table={'border': 'none'},
            #                     style_header={
            #                         **TABLE_STYLE_HEADER,
            #                         'backgroundColor': WHITE,
            #                         'color': TEXT_GRAY,
            #                         'fontSize': '11px',
            #                     },
            #                     style_cell={**TABLE_STYLE_CELL,
            #                                 'fontSize': '12px', 'padding': '6px 8px'},
            #                     style_cell_conditional=[
            #                         {'if': {'column_id': 'Commodity'},
            #                          'width': '60%', 'textAlign': 'left',
            #                          'paddingLeft': '8px'},
            #                         {'if': {'column_id': 'Value'},
            #                          'width': '25%', 'textAlign': 'right'},
            #                         {'if': {'column_id': 'YoY'},
            #                          'width': '15%', 'textAlign': 'center'},
            #                     ],
            #                     style_data_conditional=[
            #                         {'if': {'row_index': 'odd'},
            #                          'backgroundColor': '#F5F8FC'},
            #                         {'if': {'filter_query': '{_yoy_val} > 0',
            #                                 'column_id': 'YoY'},
            #                          'color': '#2d6a4f', 'fontWeight': 'bold'},
            #                         {'if': {'filter_query': '{_yoy_val} < 0',
            #                                 'column_id': 'YoY'},
            #                          'color': '#C00000', 'fontWeight': 'bold'},
            #                     ],
            #                     page_size=5,
            #                 ),
            #             ]
            #         ),

            #         html.Div(
            #             style={**STYLE_CHART_ITEM, 'flex': '0.9'},
            #             children=[
            #                 html.H4('Top 5 Import Commodities', style=FIGURE_TITLE),
            #                 html.P('YoY vs same period prior year',
            #                        style=FIGURE_DESCRIPTION),
            #                 dash_table.DataTable(
            #                     id='top5-import-table',
            #                     columns=[
            #                         {'name': 'Commodity', 'id': 'Commodity'},
            #                         {'name': 'Value',     'id': 'Value'},
            #                         {'name': 'YoY',       'id': 'YoY'},
            #                     ],
            #                     data=[],
            #                     style_table={'border': 'none'},
            #                     style_header={
            #                         **TABLE_STYLE_HEADER,
            #                         'backgroundColor': WHITE,
            #                         'color': TEXT_GRAY,
            #                         'fontSize': '11px',
            #                     },
            #                     style_cell={**TABLE_STYLE_CELL,
            #                                 'fontSize': '12px', 'padding': '6px 8px'},
            #                     style_cell_conditional=[
            #                         {'if': {'column_id': 'Commodity'},
            #                          'width': '60%', 'textAlign': 'left',
            #                          'paddingLeft': '8px'},
            #                         {'if': {'column_id': 'Value'},
            #                          'width': '25%', 'textAlign': 'right'},
            #                         {'if': {'column_id': 'YoY'},
            #                          'width': '15%', 'textAlign': 'center'},
            #                     ],
            #                     style_data_conditional=[
            #                         {'if': {'row_index': 'odd'},
            #                          'backgroundColor': '#F5F8FC'},
            #                         {'if': {'filter_query': '{_yoy_val} > 0',
            #                                 'column_id': 'YoY'},
            #                          'color': '#2d6a4f', 'fontWeight': 'bold'},
            #                         {'if': {'filter_query': '{_yoy_val} < 0',
            #                                 'column_id': 'YoY'},
            #                          'color': '#C00000', 'fontWeight': 'bold'},
            #                     ],
            #                     page_size=5,
            #                 ),
            #             ]
            #         ),

            #     ]
            # ),

            # ══════════════════════════════════════════════════════════════════
            # ROW 2 — Trade Balance by Province + Key Insights
            # ══════════════════════════════════════════════════════════════════
            # html.Div(
            #     style={**STYLE_CHART_ROW, 'margin': '0 0 16px 0'},
            #     children=[

            #         # Key Insights panel
            #         html.Div(
            #             style={**STYLE_CHART_ITEM, 'flex': '1'},
            #             children=[
            #                 html.H4('🔍  Key Insights', style=FIGURE_TITLE),
            #                 html.P('Derived from selected period and filters',
            #                        style=FIGURE_DESCRIPTION),
            #                 html.Div(
            #                     id='key-insights-panel',
            #                     style={
            #                         'display':        'flex',
            #                         'flexWrap':       'wrap',
            #                         'gap':            '10px',
            #                         'marginTop':      '8px',
            #                     },
            #                 ),
            #             ]
            #         ),

            #     ]
            # ),

        ]
    )