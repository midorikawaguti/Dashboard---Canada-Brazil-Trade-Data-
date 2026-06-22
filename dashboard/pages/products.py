from dash import html, dcc, dash_table

from ..styles import (
    KPI_STYLE_ROW, KPI_STYLE_BOX, KPI_STYLE_VALUE,
    KPI_TEXT_VALUE, KPI_NOTE,
    STYLE_CHART_ROW, STYLE_CHART_ITEM,
    TEXT_GRAY, WHITE,
    TABLE_STYLE_TABLE, TABLE_STYLE_HEADER,
    TABLE_STYLE_CELL, TABLE_STYLE_DATA_CONDITIONAL,
    FIGURE_TITLE, FIGURE_DESCRIPTION,
    SECTION_TITLE, SECTION_DESCRIPTION,
    BLUE_ACCENT,
)
from ..data import hs2_to_section


def layout():
    return html.Div(
        style={'padding': '20px 24px'},
        children=[

            # ── Page title ─────────────────────────────────────────────────────
            html.H2('Products', style={**SECTION_TITLE, 'margin': '0 0 4px 0'}),
            html.P(
                'Explore trade by HS2 section and commodity — value, volume, pricing and market share',
                style={**SECTION_DESCRIPTION, 'margin': '0 0 16px 0'}
            ),

            # ══════════════════════════════════════════════════════════════════
            # LEVEL 1 — Section selector (synced with treemap)
            # ══════════════════════════════════════════════════════════════════
            html.Div(
                style={
                    'backgroundColor': WHITE,
                    'borderRadius':    '8px',
                    'padding':         '10px 16px',
                    'marginBottom':    '16px',
                    'boxShadow':       '0 1px 4px rgba(0,0,0,0.06)',
                    'display':         'flex',
                    'alignItems':      'center',
                    'gap':             '12px',
                },
                children=[
                    html.Span('1️⃣  Select Section:',
                              style={'fontSize': '13px', 'color': TEXT_GRAY,
                                     'whiteSpace': 'nowrap', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='products-section-select',
                        options=[{'label': s, 'value': s}
                                 for s in sorted(set(hs2_to_section.values()))],
                        value=None,
                        placeholder='All sections — or click treemap to drill down…',
                        multi=False,
                        clearable=True,
                        style={'flex': '1', 'fontSize': '13px', 'border': 'none'},
                        className='slim-dropdown',
                    ),
                ]
            ),

            # ══════════════════════════════════════════════════════════════════
            # KPI ROW — updates when section selected
            # ══════════════════════════════════════════════════════════════════
            html.Div(
                style={**KPI_STYLE_ROW, 'margin': '0 0 20px 0'},
                children=[
                    html.Div(style=KPI_STYLE_BOX, children=[
                        html.Div(id='top-HS2'),
                        html.P('Top HS2 Category',
                               style={'color': TEXT_GRAY, 'fontSize': '12px',
                                      'margin': '4px 0 0 0'}),
                    ]),
                    html.Div(style=KPI_STYLE_BOX, children=[
                        html.Div(id='fastest-growing'),
                        html.P('Fastest Growing HS2',
                               style={'color': TEXT_GRAY, 'fontSize': '12px',
                                      'margin': '4px 0 0 0'}),
                    ]),
                    html.Div(style=KPI_STYLE_BOX, children=[
                        html.Div(id='number-commodities'),
                        html.P('Unique Commodities',
                               style={'color': TEXT_GRAY, 'fontSize': '12px',
                                      'margin': '4px 0 0 0'}),
                    ]),
                    # html.Div(style=KPI_STYLE_BOX, children=[
                    #     html.Div(id='products-avg-price'),
                    #     html.P('Avg Price per Unit',
                    #            style={'color': TEXT_GRAY, 'fontSize': '12px',
                    #                   'margin': '4px 0 0 0'}),
                    # ]),
                ]
            ),

            # ══════════════════════════════════════════════════════════════════
            # ROW 1 — Treemap (Section level) + HS2 Share bar
            # ══════════════════════════════════════════════════════════════════
            html.Div(
                style={**STYLE_CHART_ROW, 'margin': '0 0 16px 0'},
                children=[

                    html.Div(
                        style={**STYLE_CHART_ITEM, 'flex': '1'},
                        children=[
                            html.H4('Trade Composition by Section', style=FIGURE_TITLE),
                            html.P(
                                'Shows HS2 Sections — click a section or use dropdown above to filter',
                                style=FIGURE_DESCRIPTION
                            ),
                            dcc.Graph(
                                id='products-treemap',
                                config={'displayModeBar': False},
                            ),
                        ]
                    ),

                    # html.Div(
                    #     style={**STYLE_CHART_ITEM, 'flex': '1'},
                    #     children=[
                    #         html.H4('HS2 Share of Total Trade', style=FIGURE_TITLE),
                    #         html.P(
                    #             'HS2 codes within selected section — % of total value',
                    #             style=FIGURE_DESCRIPTION
                    #         ),
                    #         dcc.Graph(
                    #             id='hs2-share-chart-products',
                    #             config={'displayModeBar': False},
                    #         ),
                    #     ]
                    # ),

                ]
            ),


            # ══════════════════════════════════════════════════════════════════
            # ROW 1 — Treemap (Section level) + HS2 Share bar
            # ══════════════════════════════════════════════════════════════════
            html.Div(
                style={**STYLE_CHART_ROW, 'margin': '0 0 16px 0'},
                children=[

                    # html.Div(
                    #     style={**STYLE_CHART_ITEM, 'flex': '1'},
                    #     children=[
                    #         html.H4('Trade Composition by Section', style=FIGURE_TITLE),
                    #         html.P(
                    #             'Shows HS2 Sections — click a section or use dropdown above to filter',
                    #             style=FIGURE_DESCRIPTION
                    #         ),
                    #         dcc.Graph(
                    #             id='products-treemap',
                    #             config={'displayModeBar': False},
                    #         ),
                    #     ]
                    # ),

                    html.Div(
                        style={**STYLE_CHART_ITEM, 'flex': '1'},
                        children=[
                            html.H4('HS2 Share of Total Trade', style=FIGURE_TITLE),
                            html.P(
                                'HS2 codes within selected section — % of total value',
                                style=FIGURE_DESCRIPTION
                            ),
                            dcc.Graph(
                                id='hs2-share-chart-products',
                                config={'displayModeBar': False},
                            ),
                        ]
                    ),

                ]
            ),
            # ══════════════════════════════════════════════════════════════════
            # LEVEL 2 — HS2 code selector (filtered to selected section)
            # ══════════════════════════════════════════════════════════════════
            html.Div(
                style={
                    'backgroundColor': WHITE,
                    'borderRadius':    '8px',
                    'padding':         '10px 16px',
                    'marginBottom':    '16px',
                    'boxShadow':       '0 1px 4px rgba(0,0,0,0.06)',
                    'display':         'flex',
                    'alignItems':      'center',
                    'gap':             '12px',
                },
                children=[
                    html.Span('2️⃣  Select HS2 Code:',
                              style={'fontSize': '13px', 'color': TEXT_GRAY,
                                     'whiteSpace': 'nowrap', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='products-hs2-select',
                        options=[],   # populated by callback based on section
                        value=None,
                        placeholder='Select a section first, then pick an HS2 code…',
                        multi=False,
                        clearable=True,
                        style={'flex': '1', 'fontSize': '13px', 'border': 'none'},
                        className='slim-dropdown',
                    ),
                ]
            ),

            # ══════════════════════════════════════════════════════════════════
            # ROW 2 — Top 10 commodities + Top 5 Export/Import tables
            # ══════════════════════════════════════════════════════════════════
            html.Div(
                style={**STYLE_CHART_ROW, 'alignItems': 'flex-start',
                       'margin': '0 0 16px 0'},
                children=[

                    # html.Div(
                    #     style={**STYLE_CHART_ITEM, 'flex': '1.2'},
                    #     children=[
                    #         html.H4('Top 10 Commodities', style=FIGURE_TITLE),
                    #         html.P('By total trade value with share %',
                    #                style=FIGURE_DESCRIPTION),
                    #         dash_table.DataTable(
                    #             id='top-commodity-table',
                    #             columns=[
                    #                 {'name': '#',           'id': '#'},
                    #                 {'name': 'Commodity',   'id': 'Commodity'},
                    #                 {'name': 'Exports',     'id': 'Exports'},
                    #                 {'name': 'Imports',     'id': 'Imports'},
                    #                 {'name': 'Total Trade', 'id': 'Total Trade'},
                    #                 {'name': 'Share %',     'id': 'Share %'},
                    #             ],
                    #             data=[],
                    #             style_table=TABLE_STYLE_TABLE,
                    #             style_header=TABLE_STYLE_HEADER,
                    #             style_cell={**TABLE_STYLE_CELL,
                    #                         'fontSize': '12px', 'padding': '6px 8px'},
                    #             style_cell_conditional=[
                    #                 {'if': {'column_id': '#'},
                    #                  'width': '5%', 'textAlign': 'center'},
                    #                 {'if': {'column_id': 'Commodity'},
                    #                  'width': '40%', 'textAlign': 'left',
                    #                  'paddingLeft': '8px'},
                    #             ],
                    #             style_data_conditional=TABLE_STYLE_DATA_CONDITIONAL,
                    #             page_size=10,
                    #         ),
                    #     ]
                    # ),

                    html.Div(
                        style={**STYLE_CHART_ITEM, 'flex': '0.9'},
                        children=[
                            html.H4('Top 5 Export Commodities', style=FIGURE_TITLE),
                            html.P('YoY vs same period prior year',
                                   style=FIGURE_DESCRIPTION),
                            dash_table.DataTable(
                                id='top5-export-table-products',
                                columns=[
                                    {'name': 'Commodity', 'id': 'Commodity'},
                                    {'name': 'Value',     'id': 'Value'},
                                    {'name': 'YoY',       'id': 'YoY'},
                                ],
                                data=[],
                                style_table={'border': 'none'},
                                style_header={
                                    **TABLE_STYLE_HEADER,
                                    'backgroundColor': WHITE,
                                    'color': TEXT_GRAY,
                                    'fontSize': '11px',
                                },
                                style_cell={**TABLE_STYLE_CELL,
                                            'fontSize': '12px', 'padding': '6px 8px'},
                                style_cell_conditional=[
                                    {'if': {'column_id': 'Commodity'},
                                     'width': '60%', 'textAlign': 'left',
                                     'paddingLeft': '8px'},
                                    {'if': {'column_id': 'Value'},
                                     'width': '25%', 'textAlign': 'right'},
                                    {'if': {'column_id': 'YoY'},
                                     'width': '15%', 'textAlign': 'center'},
                                ],
                                style_data_conditional=[
                                    {'if': {'row_index': 'odd'},
                                     'backgroundColor': '#F5F8FC'},
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
                        style={**STYLE_CHART_ITEM, 'flex': '0.9'},
                        children=[
                            html.H4('Top 5 Import Commodities', style=FIGURE_TITLE),
                            html.P('YoY vs same period prior year',
                                   style=FIGURE_DESCRIPTION),
                            dash_table.DataTable(
                                id='top5-import-table-products',
                                columns=[
                                    {'name': 'Commodity', 'id': 'Commodity'},
                                    {'name': 'Value',     'id': 'Value'},
                                    {'name': 'YoY',       'id': 'YoY'},
                                ],
                                data=[],
                                style_table={'border': 'none'},
                                style_header={
                                    **TABLE_STYLE_HEADER,
                                    'backgroundColor': WHITE,
                                    'color': TEXT_GRAY,
                                    'fontSize': '11px',
                                },
                                style_cell={**TABLE_STYLE_CELL,
                                            'fontSize': '12px', 'padding': '6px 8px'},
                                style_cell_conditional=[
                                    {'if': {'column_id': 'Commodity'},
                                     'width': '60%', 'textAlign': 'left',
                                     'paddingLeft': '8px'},
                                    {'if': {'column_id': 'Value'},
                                     'width': '25%', 'textAlign': 'right'},
                                    {'if': {'column_id': 'YoY'},
                                     'width': '15%', 'textAlign': 'center'},
                                ],
                                style_data_conditional=[
                                    {'if': {'row_index': 'odd'},
                                     'backgroundColor': '#F5F8FC'},
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

            # ══════════════════════════════════════════════════════════════════
            # ROW 3 — Export destinations + Import origins
            # ══════════════════════════════════════════════════════════════════
            html.Div(
                style={**STYLE_CHART_ROW, 'margin': '0 0 16px 0'},
                children=[
                    html.Div(
                        style={**STYLE_CHART_ITEM, 'flex': '1'},
                        children=[
                            html.H4('Top Export Destinations', style=FIGURE_TITLE),
                            html.P('Top 10 countries buying Canadian exports',
                                   style=FIGURE_DESCRIPTION),
                            dcc.Graph(id='products-export-destinations',
                                      config={'displayModeBar': False}),
                        ]
                    ),
                    html.Div(
                        style={**STYLE_CHART_ITEM, 'flex': '1'},
                        children=[
                            html.H4('Top Import Origins', style=FIGURE_TITLE),
                            html.P('Top 10 countries supplying Canadian imports',
                                   style=FIGURE_DESCRIPTION),
                            dcc.Graph(id='products-import-origins',
                                      config={'displayModeBar': False}),
                        ]
                    ),
                ]
            ),

            # ══════════════════════════════════════════════════════════════════
            # LEVEL 3 — Commodity selector + detail panel
            # ══════════════════════════════════════════════════════════════════
            html.Div(
                style={
                    'backgroundColor': WHITE,
                    'borderRadius':    '8px',
                    'padding':         '10px 16px',
                    'margin':          '0 0 4px 0',
                    'boxShadow':       '0 1px 4px rgba(0,0,0,0.06)',
                    'display':         'flex',
                    'alignItems':      'center',
                    'gap':             '12px',
                },
                children=[
                    html.Span('3️⃣  Select Commodity for details:',
                              style={'fontSize': '13px', 'color': TEXT_GRAY,
                                     'whiteSpace': 'nowrap', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='products-commodity-select',
                        options=[],   # populated by callback
                        value=None,
                        placeholder='Select an HS2 code first, then pick a commodity…',
                        multi=False,
                        clearable=True,
                        style={'flex': '1', 'fontSize': '13px', 'border': 'none'},
                        className='slim-dropdown',
                    ),
                ]
            ),

            # Detail panel — hidden until commodity selected
            html.Div(id='commodity-detail-panel'),

        ]
    )