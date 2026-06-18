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
            html.H2('Geographic Insights', style=SECTION_TITLE),
            html.P('Trade flows by province and country', style=SECTION_DESCRIPTION),
        ]),

        # ── KPI Row — Geography KPIs ───────────────────────────────────────────
        html.Div(
            style=KPI_STYLE_ROW,
            children=[
                html.Div(style=KPI_STYLE_BOX, children=[
                    html.Div(id='top-province'),
                    html.P('Top province by trade value',
                           style={'color': TEXT_GRAY, 'fontSize': '14px'}),
                ]),
                html.Div(style=KPI_STYLE_BOX, children=[
                    html.Div(id='top-country'),
                    html.P('Top country by trade value',
                           style={'color': TEXT_GRAY, 'fontSize': '14px'}),
                ]),
                html.Div(style=KPI_STYLE_BOX, children=[
                    html.Div(id='number-countries'),
                    html.P('Total unique countries traded with',
                           style={'color': TEXT_GRAY, 'fontSize': '14px'}),
                ]),
            ]
        ),

        # ── Row 1 — Province small multiples ──────────────────────────────────
        html.Div(
            style=STYLE_CHART_ROW,
            children=[
                html.Div(
                    style=STYLE_CHART_ITEM,
                    children=[
                        html.H4('Export vs Import by Province', style=FIGURE_TITLE),
                        html.P('Top 4 provinces by total trade value',
                               style=FIGURE_DESCRIPTION),
                        dcc.Graph(id='province-small-multiples',
                                  config={'displayModeBar': False}),
                    ]
                ),
            ]
        ),

        # ── Row 2 — HS2 share + Top countries table ────────────────────────────
        html.Div(
            style=STYLE_CHART_ROW,
            children=[

                html.Div(
                    style=STYLE_CHART_ITEM,
                    children=[
                        html.H4('Trade Share by HS2 Category', style=FIGURE_TITLE),
                        html.P('% of total trade value', style=FIGURE_DESCRIPTION),
                        dcc.Graph(id='hs2-share-chart-geo',
                                  config={'displayModeBar': False}),
                    ]
                ),

                html.Div(
                    style={**STYLE_CHART_ITEM, 'flex': '0.8'},
                    children=[
                        html.H4('Top 10 Trading Partners', style=FIGURE_TITLE),
                        html.P('Share of total Canada trade by country',
                               style=FIGURE_DESCRIPTION),
                        dash_table.DataTable(
                            id='top-countries-table-geo',
                            columns=[
                                {'name': '#',           'id': '#'},
                                {'name': 'Country',     'id': 'Country'},
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

    ])