import dash
from dash import dcc, html
from datetime import datetime as dt
import yfinance as yf
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.express as px
from model import prediction

def get_stock_price_fig(df):
    fig = px.line(df, x="Date", y=["Close", "Open"], title="Closing and Opening Price vs Date")
    return fig

def get_more(df):
    df['EWA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    fig = px.scatter(df, x="Date", y="EWA_20", title="Exponential Moving Average vs Date")
    fig.update_traces(mode='lines+markers')
    return fig

app = dash.Dash(__name__, external_stylesheets=[
    "https://fonts.googleapis.com/css2?family=Roboto&display=swap"
])
server = app.server

# 🎨 Define themes
light_theme = {
    "backgroundColor": "#ffffff",
    "color": "#000000",
    "backgroundImage": "url('https://www.transparenttextures.com/patterns/paper-fibers.png')"
}

dark_theme = {
    "backgroundColor": "#111111",
    "color": "#eeeeee",
    "backgroundImage": "url('https://www.transparenttextures.com/patterns/diamond-upholstery.png')"
}

# ✅ NEW description styles per theme
light_description = {
    "color": "#000000",
    "backgroundColor": "#ffffff",
    "padding": "10px",
    "borderRadius": "10px"
}

dark_description = {
    "color": "#ffffff",
    "backgroundColor": "#222222",
    "padding": "10px",
    "borderRadius": "10px"
}

app.layout = html.Div([
    dcc.Store(id='theme-store', data='light'),
    html.Div([
        html.Button("Toggle Theme", id='toggle-theme', n_clicks=0, style={"margin": "10px"}),
        html.P("Welcome to the Stock Dash App!", className="start"),
        html.Div([
            html.P("Input stock code: "),
            html.Div([
                dcc.Input(id="dropdown_tickers", type="text"),
                html.Button("Submit", id='submit'),
            ], className="form")
        ], className="input-place"),
        html.Div([
            dcc.DatePickerRange(
                id='my-date-picker-range',
                min_date_allowed=dt(1995, 8, 5),
                max_date_allowed=dt.now(),
                initial_visible_month=dt.now(),
                end_date=dt.now().date()
            ),
        ], className="date"),
        html.Div([
            html.Button("Stock Price", className="stock-btn", id="stock"),
            html.Button("Indicators", className="indicators-btn", id="indicators"),
            dcc.Input(id="n_days", type="text", placeholder="number of days"),
            html.Button("Forecast", className="forecast-btn", id="forecast")
        ], className="buttons"),
    ], className="nav", id="nav-container"),

    html.Div([
        html.Div([
            html.Img(id="logo"),
            html.P(id="ticker")
        ], className="header"),
        html.Div(id="description", className="description_ticker"),
        html.Div([], id="graphs-content"),
        html.Div([], id="main-content"),
        html.Div([], id="forecast-content")
    ], className="content"),
], className="container", id="main-container")

# 🔥 Callback to toggle theme
@app.callback(
    Output("theme-store", "data"),
    [Input("toggle-theme", "n_clicks")],
    [State("theme-store", "data")]
)
def toggle_theme(n_clicks, current_theme):
    if n_clicks is None:
        raise PreventUpdate
    return "dark" if current_theme == "light" else "light"

# ✅ Updated callback to apply description background too
@app.callback(
    Output("main-container", "style"),
    Output("nav-container", "style"),
    Output("description", "style"),
    [Input("theme-store", "data")]
)
def update_theme(theme):
    if theme == "dark":
        return dark_theme, dark_theme, dark_description
    return light_theme, light_theme, light_description

# 🟢 Other callbacks unchanged
@app.callback([
    Output("description", "children"),
    Output("logo", "src"),
    Output("ticker", "children"),
    Output("stock", "n_clicks"),
    Output("indicators", "n_clicks"),
    Output("forecast", "n_clicks")
], [Input("submit", "n_clicks")], [State("dropdown_tickers", "value")])
def update_data(n, val):
    if n is None:
        return ("Hey there! Please enter a legitimate stock code to get details.",
                "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg",
                "Stonks", None, None, None)
    if val is None:
        raise PreventUpdate
    ticker = yf.Ticker(val)
    inf = ticker.info
    logo_url = inf.get('logo_url', 'https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg')
    short_name = inf.get('shortName', 'Unknown Company')
    long_summary = inf.get('longBusinessSummary', 'No summary available')
    return long_summary, logo_url, short_name, None, None, None

@app.callback([Output("graphs-content", "children")],
              [Input("stock", "n_clicks"),
               Input('my-date-picker-range', 'start_date'),
               Input('my-date-picker-range', 'end_date')],
              [State("dropdown_tickers", "value")])
def stock_price(n, start_date, end_date, val):
    if n is None or val is None:
        return [""]
    if start_date is not None:
        df = yf.download(val, str(start_date), str(end_date))
    else:
        df = yf.download(val)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.reset_index(inplace=True)
    fig = get_stock_price_fig(df)
    return [dcc.Graph(figure=fig)]

@app.callback([Output("main-content", "children")],
              [Input("indicators", "n_clicks"),
               Input('my-date-picker-range', 'start_date'),
               Input('my-date-picker-range', 'end_date')],
              [State("dropdown_tickers", "value")])
def indicators(n, start_date, end_date, val):
    if n is None or val is None:
        return [""]
    if start_date is None:
        df_more = yf.download(val)
    else:
        df_more = yf.download(val, str(start_date), str(end_date))
    if isinstance(df_more.columns, pd.MultiIndex):
        df_more.columns = df_more.columns.get_level_values(0)
    df_more.reset_index(inplace=True)
    fig = get_more(df_more)
    return [dcc.Graph(figure=fig)]

@app.callback([Output("forecast-content", "children")],
              [Input("forecast", "n_clicks")],
              [State("n_days", "value"),
               State("dropdown_tickers", "value")])
def forecast(n, n_days, val):
    if n is None or val is None:
        return [""]
    fig = prediction(val, int(n_days) + 1)
    return [dcc.Graph(figure=fig)]

if __name__ == '__main__':
    app.run(debug=True)
