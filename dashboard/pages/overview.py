from dash import html, dcc, dash_table

from ..styles import (
    KPI_STYLE_ROW, KPI_STYLE_BOX, STYLE_CHART_ROW,
    STYLE_CHART_ITEM, BLUE_ACCENT, TEXT_GRAY,
    FONT_MAIN,TABLE_STYLE_TABLE, TABLE_STYLE_HEADER,       
    TABLE_STYLE_CELL, TABLE_STYLE_DATA_CONDITIONAL,
)


def layout():
    return html.Div([

        # ── Section title ──────────────────────────────────────────────────────
        html.Div(children=[
            html.H2('Overview', style={
                'margin':        '20px',
                'fontFamily':    FONT_MAIN,
                'fontSize':      '28px',
                'fontWeight':    'bold',
                'color':         BLUE_ACCENT,
                'letterSpacing': '0.5px',
            }),
            html.P('Total trade flow, balance and year-over-year trend', style={
                'margin':    '6px 6px 4px 22px',
                'fontStyle': 'italic',
                'fontSize':  '16px',
            }),
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


         # ── Charts row 1 ───────────────────────────────────────────────────
        html.Div(
            html.Div(dcc.Graph(id='monthly-trade'), style=STYLE_CHART_ITEM),
         style=STYLE_CHART_ROW),

                # ── Charts row 2 — Top 10 chart + table ───────────────────────────
        html.Div([
            html.Div(dcc.Graph(id='top-countries'), style={**STYLE_CHART_ITEM, 'flex': '1.2'}),
            html.Div(
                style={**STYLE_CHART_ITEM, 'flex': '0.8'},
                children=[
                    # ── Table title ───────────────────────────────
                    html.H4('Top 10 Trading Partners', style={
                        'margin':     '0 0 8px 0',
                        'color':      BLUE_ACCENT,
                        'fontFamily': FONT_MAIN,
                        'fontSize':   '16px',
                        'fontWeight': 'bold',
                    }),
                    html.P('Share of total Canada trade by country', style={
                        'margin':     '0 0 12px 0',
                        'color':      TEXT_GRAY,
                        'fontSize':   '12px',
                        'fontStyle':  'italic',
                    }),
                    # ── Table ─────────────────────────────────────
                    dash_table.DataTable(
                        id='top-countries-table',
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
                    )
                ]
            ),
        ], style=STYLE_CHART_ROW),


        # ── Charts row 3 ───────────────────────────────────────────────────
        html.Div(
            html.Div(dcc.Graph(id='monthly-trade-2'), style=STYLE_CHART_ITEM),
         style=STYLE_CHART_ROW),

    ])
