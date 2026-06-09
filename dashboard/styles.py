# ── Colours ────────────────────────────────────────────────────────────────────
DARK_GREEN   = '#1A4731'
MEDIUM_GREEN = '#2D6A4F'
BLUE_ACCENT  = '#1F4E79'
BLUE_MEDIUM  = '#366A9B'
LIGHT_GRAY   = '#F5F5F5'
MID_GRAY     = '#E0E0E0'
TEXT_DARK    = '#1A1A1A'
TEXT_GRAY    = '#555555'
WHITE        = '#FFFFFF'
RED          = '#C00000'
GREEN_TREND  = '#65CC90'

# ── Fonts ──────────────────────────────────────────────────────────────────────
FONT_MAIN = "'Arial', 'Times New Roman', serif"
FONT_BODY = "'Helvetica Neue', 'Helvetica', Arial, sans-serif"

# ── Component styles ───────────────────────────────────────────────────────────
HEADER_BOX_STYLE={'fontFamily':      FONT_BODY,
            'backgroundColor': LIGHT_GRAY,
            'minHeight':       '90vh',
            'margin':          '0',
            'padding':         '0'
}

HEADER_STYLE={
                    'backgroundColor': DARK_GREEN,
                    'padding':         '20px 28px',
                    'display':         'flex',
                    'justifyContent':  'space-between',
                    'alignItems':      'center',
                    'position':        'sticky',    
                    'top':             '0',         
                    'zIndex':          '1000',      
                }

HEADER_TITLE ={
                'margin':        '20px',
                'fontFamily':    FONT_MAIN,
                'fontSize':      '36px',
                'fontWeight':    'bold',
                'color':         WHITE,
                'letterSpacing': '0.5px',
}


KPI_STYLE_ROW = {
    'display':  'flex',
    'gap':      '8px',
    'margin':   '8px 16px',
    'width':    'auto',
    'flexWrap': 'wrap',
}

KPI_STYLE_BOX = {
    'flex':            '1',
    'backgroundColor': WHITE,
    'borderRadius':    '10px',
    'padding':         '6px',
    'textAlign':       'center',
    'boxShadow':       '0 2px 8px rgba(0,0,0,0.08)',
}

KPI_STYLE_LABEL = {
    'margin':     '0',
    'fontSize':   '16px',
    'fontWeight': 'bold',
    'color':      BLUE_MEDIUM,
}

KPI_STYLE_VALUE = {
    'margin':   '4px 0 0 0',
    'fontSize': '24px',
    'color':    BLUE_ACCENT,
    'fontWeight': 'bold'
}

KPI_TEXT_VALUE = {
    'fontSize': '13px', 
    'color': TEXT_GRAY,
    'margin': '4px 0 2px 0',
}

KPI_NOTE= {
    'fontSize': '12px', 
    'color': TEXT_GRAY,
    'fontStyle': 'italic', 
    'margin': '4px 0 0 0'
}

STYLE_CHART_ROW = {
    'display':  'flex',
    'gap':      '10px',
    'margin':   '20px',
    'width':    'auto',
    'flexWrap': 'wrap',
}

STYLE_CHART_ITEM = {
    'flex':     '1',
    'minWidth': '0',
    'backgroundColor': WHITE,
    'borderRadius':    '10px',
    'padding':         '16px',
    'boxShadow':       '0 2px 8px rgba(0,0,0,0.08)'
}

STYLE_DROPDOWN_LABEL = {
    'fontWeight': 'bold',
    'color':      BLUE_MEDIUM,
}

STYLE_DROPDOWN_CHILD = {
    'flex':            '1',
    'minWidth':        '150px',
    'backgroundColor': WHITE,
    'borderRadius':    '5px',
    'boxShadow':       '0 2px 8px rgba(0,0,0,0.08)',
}

STYLE_DROPDOWN_ROW = {
    'display':  'flex',
    'gap':      '12px',
    'margin':   '16px 32px',
    'width':    'auto',
    'flexWrap': 'wrap',
}

NAV_LINK_STYLE = {
    'padding':        '12px 16px',
    'textDecoration': 'none',
    'color':          TEXT_GRAY,
    'fontSize':       '14px',
    'fontWeight':     '500',
    'borderBottom':   '3px solid transparent',
}

NAV_LINK_ACTIVE_STYLE = {
    **NAV_LINK_STYLE,
    'color':       BLUE_ACCENT,
    'borderBottom': f'3px solid {BLUE_ACCENT}',
}

# ── DataTable styles ───────────────────────────────────────────────────────────
TABLE_STYLE_TABLE = {
    'overflowX':    'auto',
    'borderRadius': '10px',
    'boxShadow':    '0 2px 8px rgba(0,0,0,0.08)',
}

TABLE_STYLE_HEADER = {
    'backgroundColor': BLUE_ACCENT,
    'color':           WHITE,
    'fontWeight':      'bold',
    'fontSize':        '13px',
    'textAlign':       'center',
    'border':          'none',
    'padding':         '10px',
}

TABLE_STYLE_CELL = {
    'textAlign':       'center',
    'fontSize':        '13px',
    'padding':         '10px',
    'fontFamily':      FONT_BODY,
    'border':          'none',
    'backgroundColor': WHITE,
}

TABLE_STYLE_DATA_CONDITIONAL = [
    {
        'if': {'row_index': 'odd'},
        'backgroundColor': '#F5F8FC',
    },
    {
        'if': {'column_id': 'Share %'},
        'color':      BLUE_ACCENT,
        'fontWeight': 'bold',
    },
    {
        'if': {'column_id': 'Country'},
        'textAlign':   'left',
        'paddingLeft': '16px',
    },
]


FIGURE_TITLE={
            'margin':     '0 0 8px 0',
            'color':      BLUE_ACCENT,
            'fontFamily': FONT_MAIN,
            'fontSize':   '18px',
            'fontWeight': 'bold',
        }

FIGURE_DESCRIPTION = {
            'margin':     '0 0 12px 0',
            'color':      TEXT_GRAY,
            'fontSize':   '12px',
            'fontStyle':  'italic',
        }

SECTION_TITLE = {
                'margin':        '20px',
                'fontFamily':    FONT_MAIN,
                'fontSize':      '28px',
                'fontWeight':    'bold',
                'color':         BLUE_ACCENT,
                'letterSpacing': '0.5px',
            }
SECTION_DESCRIPTION = {
                'margin':    '6px 6px 4px 22px',
                'fontStyle': 'italic',
                'fontSize':  '16px',
            }