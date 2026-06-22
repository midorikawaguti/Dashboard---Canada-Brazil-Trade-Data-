from dash import html, dcc

from .data import df, date_range_label, period_labels
from .styles import (
    DARK_GREEN, WHITE, LIGHT_GRAY, MID_GRAY,
    FONT_BODY,
)

SIDEBAR_WIDTH  = '220px'
CONTENT_MARGIN = '220px'


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

            dcc.Location(id='url', refresh=False),

            # ── LEFT SIDEBAR ──────────────────────────────────────────────────
            html.Div(
                style={
                    'position':        'fixed',
                    'top':             '0',
                    'left':            '0',
                    'bottom':          '0',
                    'width':           SIDEBAR_WIDTH,
                    'backgroundColor': DARK_GREEN,
                    'display':         'flex',
                    'flexDirection':   'column',
                    'zIndex':          '1100',
                    'overflowY':       'auto',
                },
                children=[

                    # ── Logo + title ───────────────────────────────────────────
                    html.Div(
                        style={
                            'padding':      '24px 16px 20px 16px',
                            'borderBottom': '1px solid rgba(255,255,255,0.1)',
                            'textAlign':    'center',
                        },
                        children=[
                            html.Img(
                                src='/assets/P-Logo-FCBB.png',
                                style={'height': '48px', 'marginBottom': '10px'}
                            ),
                            html.Div('Canada Trade Portfolio', style={
                                'color':         WHITE,
                                'fontSize':      '13px',
                                'fontWeight':    'bold',
                                'letterSpacing': '0.5px',
                            }),
                            html.Div('Dashboard', style={
                                'color':    '#B2DFCC',
                                'fontSize': '11px',
                            }),
                        ]
                    ),

                    # ── Nav links ──────────────────────────────────────────────
                    html.Div(
                        style={'padding': '16px 0', 'flex': '1'},
                        children=[

                            dcc.Link(
                                href='/',
                                style={'textDecoration': 'none'},
                                children=html.Div(
                                    id='nav-overview',
                                    style={
                                        'display':      'flex',
                                        'alignItems':   'center',
                                        'gap':          '10px',
                                        'padding':      '12px 20px',
                                        'color':        WHITE,
                                        'fontSize':     '14px',
                                        'cursor':       'pointer',
                                        'borderLeft':   '3px solid transparent',
                                    },
                                    children=[
                                        html.Span('🏠', style={'fontSize': '16px'}),
                                        html.Span('Overview'),
                                    ]
                                )
                            ),

                            dcc.Link(
                                href='/products',
                                style={'textDecoration': 'none'},
                                children=html.Div(
                                    id='nav-products',
                                    style={
                                        'display':    'flex',
                                        'alignItems': 'center',
                                        'gap':        '10px',
                                        'padding':    '12px 20px',
                                        'color':      '#B2DFCC',
                                        'fontSize':   '14px',
                                        'cursor':     'pointer',
                                        'borderLeft': '3px solid transparent',
                                    },
                                    children=[
                                        html.Span('📦', style={'fontSize': '16px'}),
                                        html.Span('Products'),
                                    ]
                                )
                            ),

                        ]
                    ),

                    # ── Data as of ─────────────────────────────────────────────
                    html.Div(
                        style={
                            'padding':   '16px',
                            'borderTop': '1px solid rgba(255,255,255,0.1)',
                            'color':     '#B2DFCC',
                            'fontSize':  '11px',
                            'textAlign': 'center',
                        },
                        children=[
                            html.Div('Data as of'),
                            html.Div(
                                date_range_label,
                                style={'fontWeight': 'bold', 'color': WHITE,
                                       'fontSize': '12px'}
                            ),
                        ]
                    ),

                ]
            ),

            # ── MAIN CONTENT AREA ─────────────────────────────────────────────
            html.Div(
                style={
                    'marginLeft':    CONTENT_MARGIN,
                    'minHeight':     '100vh',
                    'display':       'flex',
                    'flexDirection': 'column',
                },
                children=[

                    # ── TOP FILTER BAR ─────────────────────────────────────────
                    html.Div(
                        style={
                            'backgroundColor': WHITE,
                            'padding':         '10px 24px',
                            'display':         'flex',
                            'gap':             '12px',
                            'alignItems':      'center',
                            'flexWrap':        'wrap',
                            'borderBottom':    f'1px solid {MID_GRAY}',
                            'position':        'sticky',
                            'top':             '0',
                            'zIndex':          '1000',
                            'boxShadow':       '0 1px 4px rgba(0,0,0,0.06)',
                        },
                        children=[

                            # Province
                            html.Div([
                                dcc.Dropdown(
                                    id='province-dropdown',
                                    options=(
                                        [{'label': 'All Provinces', 'value': 'ALL'}] +
                                        [{'label': p, 'value': p}
                                         for p in sorted(df['Province'].unique())]
                                    ),
                                    value=['ALL'],
                                    multi=True,
                                    placeholder='Province',
                                    style={'border': 'none', 'fontSize': '13px',
                                           'minWidth': '160px'},
                                    className='slim-dropdown',
                                ),
                            ]),

                            # Country
                            html.Div([
                                dcc.Dropdown(
                                    id='country-dropdown',
                                    options=(
                                        [{'label': 'All Countries', 'value': 'ALL'}] +
                                        [{'label': c, 'value': c}
                                         for c in sorted(df['Country'].unique())]
                                    ),
                                    value=['ALL'],
                                    multi=True,
                                    placeholder='Partner Country',
                                    style={'border': 'none', 'fontSize': '13px',
                                           'minWidth': '160px'},
                                    className='slim-dropdown',
                                ),
                            ]),

                            # Trade Type
                            html.Div([
                                dcc.Dropdown(
                                    id='trade-type-dropdown',
                                    options=(
                                        [{'label': 'All Trade Types', 'value': 'ALL'}] +
                                        [{'label': t, 'value': t}
                                         for t in sorted(df['trade_type'].unique())]
                                    ),
                                    value=['ALL'],
                                    multi=True,
                                    placeholder='Trade Type',
                                    style={'border': 'none', 'fontSize': '13px',
                                           'minWidth': '140px'},
                                    className='slim-dropdown',
                                ),
                            ]),

                            # Period slider
                            html.Div(
                                style={
                                    'flex':        '1',
                                    'minWidth':    '260px',
                                    'paddingTop':  '6px',
                                },
                                children=[
                                    dcc.RangeSlider(
                                        id='period-slider',
                                        min=0,
                                        max=len(period_labels) - 1,
                                        step=1,
                                        value=[0, len(period_labels) - 1],
                                        marks={
                                            i: {'label': label,
                                                'style': {'fontSize': '10px'}}
                                            for i, label in enumerate(period_labels)
                                            if i % 4 == 0
                                        },
                                        tooltip=None,
                                    ),
                                ]
                            ),

                        ]
                    ),

                    # ── PAGE CONTENT (swapped by routing callback) ─────────────
                    html.Div(id='page-content', style={'flex': '1'}),

                ]
            ),

        ]
    )