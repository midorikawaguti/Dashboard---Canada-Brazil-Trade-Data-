import dash

from dashboard.layout import create_layout
from dashboard.callbacks import register_callbacks

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.layout = create_layout()
register_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True, port=8050)
