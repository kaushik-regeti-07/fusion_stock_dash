import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.svm import SVR
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
from datetime import timedelta

def predict_prices(ticker_symbol, days=10):
    try:
        df = yf.download(ticker_symbol, period="60d")
        if df.empty:
            return [], [], "No data available for prediction."

        df = df.reset_index()
        df["Day"] = np.arange(len(df))

        # Prepare features and labels
        X = df[["Day"]].values
        y = df["Close"].values

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, shuffle=False)

        # Hyperparameter tuning
        param_grid = {"C": [1, 10], "epsilon": [0.1, 0.5], "gamma": ["scale", "auto"]}
        grid = GridSearchCV(SVR(kernel='rbf'), param_grid, cv=3)
        grid.fit(X_train, y_train)

        # Predict future
        model = grid.best_estimator_
        future_days = np.arange(len(df), len(df) + days).reshape(-1, 1)
        future_preds = model.predict(future_days)

        # Prepare dates for plotting
        last_date = df["Date"].iloc[-1]
        future_dates = [last_date + timedelta(days=i + 1) for i in range(days)]

        return future_dates, future_preds.tolist(), None

    except Exception as e:
        return [], [], f"Error: {str(e)}"

