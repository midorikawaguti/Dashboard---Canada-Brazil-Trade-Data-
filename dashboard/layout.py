from dash import html, dcc

from .data import df, date_range_label, hs2_options_labeled, period_labels
from .styles import (
    DARK_GREEN, WHITE, LIGHT_GRAY, MID_GRAY,
    FONT_MAIN, FONT_BODY,
    STYLE_DROPDOWN_ROW, STYLE_DROPDOWN_CHILD, STYLE_DROPDOWN_LABEL,
    NAV_LINK_STYLE,
)

# from .pages.overview import layout as overview_layout
# from .pages.products import layout as product_layout
# from .pages.geography import layout as geography_layout



def create_layout():
    return html.Div(
        style={
            'fontFamily':      FONT_BODY,
            'backgroundColor': LIGHT_GRAY,
            'minHeight':       '100vh',
            'margin':          '0',
            'padding':         '0',
        },
        children=[

            # URL tracker (invisible — needed for page routing)
            dcc.Location(id='url', refresh=False),

            # ── Header ────────────────────────────────────────────────────────
            html.Div(
                style={
                    'backgroundColor': DARK_GREEN,
                    'padding':         '24px 32px',
                    'display':         'flex',
                    'justifyContent':  'space-between',
                    'alignItems':      'center',
                    'position':        'sticky',
                    'top':             '0',
                    'zIndex':          '1000',
                },
                children=[
                    html.Div([
                        html.H1('Canada Trade', style={
                            'margin':        '0',
                            'fontFamily':    FONT_MAIN,
                            'fontSize':      '36px',
                            'fontWeight':    'bold',
                            'color':         WHITE,
                            'letterSpacing': '0.5px',
                        }),
                        html.P(
                            f'Total trade flow, balance, and year-over-year trend · {date_range_label}',
                            style={
                                'margin':    '4px 2px 2px 2px',
                                'fontStyle': 'italic',
                                'fontSize':  '14px',
                                'color':     '#B2DFCC',
                            }
                        ),
                    ]),

                    # FCBB logo
                    html.Div(
                        style={'borderRadius': '4px', 'padding': '8px 12px'},
                        children=[
                            html.Img(src='/assets/P-Logo-FCBB.png', style={'height': '60px'}),
                        ]
                    ),
                ]
            ),


            # ── Navbar ────────────────────────────────────────────────────────
            html.Div(
                style={
                    'backgroundColor': WHITE,
                    'padding':         '0 32px',
                    'display':         'flex',
                    'gap':             '8px',
                    'borderBottom':    f'1px solid {MID_GRAY}',
                    'position':        'sticky',
                    'top':             '88px',
                    'zIndex':          '999',
                },
                children=[
                    dcc.Link('Overview',  href='/',          style=NAV_LINK_STYLE),
                    dcc.Link('Products',  href='/products',  style=NAV_LINK_STYLE),
                    dcc.Link('Geography', href='/geography', style=NAV_LINK_STYLE),
                ]
            ),

            # ── Filters ───────────────────────────────────────────────────────
            html.Div(
                style={
                    'backgroundColor': WHITE,
                    'padding':         '12px 32px 16px 32px',
                    'display':         'flex',
                    'flexDirection':   'column',   # stack rows vertically
                    'gap':             '12px',
                    'position':        'sticky',
                    'top':             '132px',
                    'zIndex':          '998',
                    'borderBottom':    f'1px solid {MID_GRAY}',
                },
                children=[

                    # ── Row 1 — Dropdowns ─────────────────────────────────────
                    html.Div(
                        style={
                            'display':  'flex',
                            'gap':      '12px',
                            'width':    '100%',
                            'flexWrap': 'wrap',
                        },
                        children=[

                            html.Div([
                                html.Label(style=STYLE_DROPDOWN_LABEL),
                                dcc.Dropdown(
                                    options=(
                                        [{'label': 'HS2 Codes', 'value': 'ALL'}] +
                                        hs2_options_labeled
                                    ),
                                    id='hs2-dropdown',
                                    value=['ALL'],
                                    multi=True,
                                    style={'border': 'none', 'fontSize': '13px'},
                                    className='slim-dropdown',
                                ),
                            ], style=STYLE_DROPDOWN_CHILD),

                            html.Div([
                                html.Label( style=STYLE_DROPDOWN_LABEL),
                                dcc.Dropdown(
                                    options=(
                                        [{'label': 'Provinces', 'value': 'ALL'}] +
                                        [{'label': str(p), 'value': p}
                                         for p in sorted(df['Province'].unique())]
                                    ),
                                    id='province-dropdown',
                                    value=['ALL'],
                                    multi=True,
                                    style={'border': 'none', 'fontSize': '13px'},
                                    className='slim-dropdown',
                                ),
                            ], style=STYLE_DROPDOWN_CHILD),

                            html.Div([
                                html.Label( style=STYLE_DROPDOWN_LABEL),
                                dcc.Dropdown(
                                    options=(
                                        [{'label': 'Countries', 'value': 'ALL'}] +
                                        [{'label': str(c), 'value': c}
                                         for c in sorted(df['Country'].unique())]
                                    ),
                                    id='country-dropdown',
                                    value=['ALL'],
                                    multi=True,
                                    style={'border': 'none', 'fontSize': '13px'},
                                    className='slim-dropdown',
                                ),
                            ], style=STYLE_DROPDOWN_CHILD),

                            html.Div([
                                html.Label( style=STYLE_DROPDOWN_LABEL),
                                dcc.Dropdown(
                                    options=(
                                        [{'label': 'Trade Type', 'value': 'ALL'}] +
                                        [{'label': str(c), 'value': c}
                                         for c in sorted(df['trade_type'].unique())]
                                    ),
                                    id='trade-type-dropdown',
                                    value=['ALL'],
                                    multi=True,
                                    style={'border': 'none', 'fontSize': '13px'},
                                    className='slim-dropdown',
                                ),
                            ], style=STYLE_DROPDOWN_CHILD),

                        ]
                    ),

                    # ── Row 2 — Period slider ──────────────────────────────────
                    html.Div(
                        style={'width': '100%', 'paddingBottom': '8px'},
                        children=[
                            html.Label(style=STYLE_DROPDOWN_LABEL),
                            dcc.RangeSlider(
                                id='period-slider',
                                min=0,
                                max=len(period_labels) - 1,
                                step=1,
                                value=[0, len(period_labels) - 1],
                                marks={
                                    i: {'label': label, 'style': {'fontSize': '11px'}}
                                    for i, label in enumerate(period_labels)
                                    if i % 3 == 0
                                },
                                tooltip=None,
                            ),
                        ]
                    ),
                
                    

                ]
            ),

            # ── Page content (swapped by routing callback) ────────────────────
            html.Div(id='page-content'),
            # overview_layout(),

            # product_layout(),

            # geography_layout(),

        ]


    )