def prediction(stock, n_days):
    import yfinance as yf
    import pandas as pd
    import numpy as np
    from sklearn.model_selection import train_test_split, GridSearchCV
    from sklearn.svm import SVR
    from datetime import date, timedelta
    import plotly.graph_objs as go

    df = yf.download(stock, period='60d')
    df.reset_index(inplace=True)
    df['Day'] = df.index

    X = [[i] for i in range(len(df))]
    Y = df[['Close']]

    x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.1, shuffle=False)

    gsc = GridSearchCV(
        estimator=SVR(kernel='rbf'),
        param_grid={
            'C': [0.001, 0.01, 0.1, 1, 100, 1000],
            'epsilon': [0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5, 10, 50, 100, 150, 1000],
            'gamma': [0.0001, 0.001, 0.005, 0.1, 1, 3, 5, 8, 40, 100, 1000]
        },
        cv=5,
        scoring='neg_mean_absolute_error',
        verbose=0,
        n_jobs=-1
    )

    y_train = y_train.values.ravel()
    grid_result = gsc.fit(x_train, y_train)
    best_params = grid_result.best_params_
    best_svr = SVR(kernel='rbf', C=best_params["C"], epsilon=best_params["epsilon"], gamma=best_params["gamma"])

    best_svr.fit(x_train, y_train)

    last_index = x_test[-1][0]
    output_days = [[last_index + i + 1] for i in range(1, n_days)]

    dates = [date.today() + timedelta(days=i) for i in range(1, n_days)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=best_svr.predict(output_days),
        mode='lines+markers',
        name='Predicted Close Price'
    ))
    fig.update_layout(
        title=f"Predicted Close Price for Next {n_days - 1} Days",
        xaxis_title="Date",
        yaxis_title="Close Price"
    )

    return fig
