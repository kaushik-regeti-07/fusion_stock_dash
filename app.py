
import dash
from dash import dcc, html, Input, Output, State
from datetime import datetime as dt
import pandas as pd
import yfinance as yf
import plotly.express as px

from model import predict_prices  # ML model import

# Initialize Dash app and server
app = dash.Dash(__name__)
server = app.server

# Web layout
app.layout = html.Div(className='container', children=[

    # Left Section: User Inputs
    html.Div(className='inputs', children=[
        html.P("Welcome to the Stock Dash App!", className="start"),

        html.Div([
            html.Label("Enter Stock Code:"),
            dcc.Input(id="stock-code", type="text", placeholder="e.g., AAPL", className="input-box")
        ]),

        html.Div([
            html.Label("Select Date Range:"),
            dcc.DatePickerRange(
                id='date-picker-range',
                start_date=dt(2022, 1, 1),
                end_date=dt.now().date()
            )
        ]),

        html.Div([
            html.Button("Get Stock Price", id='stock-button', n_clicks=0, className="btn"),
            html.Button("Get Indicators", id='indicator-button', n_clicks=0, className="btn"),
            html.Label("Number of Days to Forecast:"),
            dcc.Input(id="forecast-days", type="number", min=1, placeholder="e.g., 10", className="input-box"),
            html.Button("Forecast", id='forecast-button', n_clicks=0, className="btn")
        ])
    ]),

    # Right Section: Display Content
    html.Div(className='content', children=[
        html.Div(className='header', children=[
            html.Img(id="logo"),
            html.H1(id="company-name")
        ]),

        html.Div(id="description", className="description_ticker"),

        html.Div(id="graphs-content"),        # Stock Price Plot
        html.Div(id="main-content"),          # Indicator Plot
        html.Div(id="forecast-content")       # Forecast Plot
    ])
])

# --- Callback to update company info ---
@app.callback(
    [Output("description", "children"),
     Output("logo", "src"),
     Output("company-name", "children")],
    Input("stock-button", "n_clicks"),
    State("stock-code", "value")
)
def update_company_info(n_clicks, code):
    if not code:
        return "Please enter a stock code.", "", ""
    try:
        ticker = yf.Ticker(code)
        info = ticker.info
        return info.get("longBusinessSummary", "N/A"), info.get("logo_url", ""), info.get("shortName", "N/A")
    except Exception as e:
        return "Failed to fetch data. Try a valid stock code.", "", ""

# --- Callback to update stock price plot ---
@app.callback(
    Output("graphs-content", "children"),
    Input("stock-button", "n_clicks"),
    State("stock-code", "value"),
    State("date-picker-range", "start_date"),
    State("date-picker-range", "end_date")
)
def update_stock_graph(n_clicks, code, start, end):
    if not code or not start or not end:
        return html.P("Please provide stock code and date range.")
    try:
        df = yf.download(code, start=start, end=end)
        df.reset_index(inplace=True)
        fig = get_stock_price_fig(df)
        return dcc.Graph(figure=fig)
    except Exception:
        return html.P("Error retrieving stock data.")

def get_stock_price_fig(df):
    fig = px.line(
        df,
        x="Date",
        y=["Open", "Close"],
        title="Opening and Closing Price vs Date"
    )
    return fig

# --- Callback to update indicator (EMA) plot ---
@app.callback(
    Output("main-content", "children"),
    Input("indicator-button", "n_clicks"),
    State("stock-code", "value"),
    State("date-picker-range", "start_date"),
    State("date-picker-range", "end_date")
)
def update_ema_graph(n_clicks, code, start, end):
    if not code or not start or not end:
        return html.P("Please provide stock code and date range.")
    try:
        df = yf.download(code, start=start, end=end)
        df.reset_index(inplace=True)
        fig = get_more(df)
        return dcc.Graph(figure=fig)
    except Exception:
        return html.P("Error retrieving indicator data.")

def get_more(df):
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    fig = px.line(df, x="Date", y="EMA_20", title="Exponential Moving Average (EMA 20) vs Date")
    return fig

# --- Callback to forecast stock prices ---
@app.callback(
    Output("forecast-content", "children"),
    Input("forecast-button", "n_clicks"),
    State("stock-code", "value"),
    State("forecast-days", "value")
)
def forecast_prices(n_clicks, code, days):
    if not code or not days:
        return html.P("Please enter stock code and number of days.")
    
    dates, preds, err = predict_prices(code, days)
    if err:
        return html.P(err)

    df = pd.DataFrame({"Date": dates, "Predicted Close": preds})
    fig = px.line(df, x="Date", y="Predicted Close", title="Forecasted Closing Prices")

    return dcc.Graph(figure=fig)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

