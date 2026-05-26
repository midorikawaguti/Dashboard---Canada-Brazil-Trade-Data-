from dash import html, dcc

from ..styles import BLUE_ACCENT, TEXT_GRAY, FONT_MAIN, STYLE_CHART_ROW, STYLE_CHART_ITEM


def layout():
    return html.Div([

        # ── Section title ──────────────────────────────────────────────────────
        html.Div(children=[
            html.H2('Products', style={
                'margin':        '20px',
                'fontFamily':    FONT_MAIN,
                'fontSize':      '28px',
                'fontWeight':    'bold',
                'color':         BLUE_ACCENT,
                'letterSpacing': '0.5px',
            }),
            html.P('Top traded commodities and HS code breakdown', style={
                'margin':    '6px 6px 4px 22px',
                'fontStyle': 'italic',
                'fontSize':  '16px',
            }),
        ]),

        # ── Charts row — add chart ids here as you build them ─────────────────
        html.Div([
            # html.Div(dcc.Graph(id='top-products'),    style=STYLE_CHART_ITEM),
            # html.Div(dcc.Graph(id='hs-breakdown'),    style=STYLE_CHART_ITEM),
            html.P('Charts coming soon.',
                   style={'color': TEXT_GRAY, 'margin': '40px', 'fontSize': '16px'}),
        ], style=STYLE_CHART_ROW),

    ])
