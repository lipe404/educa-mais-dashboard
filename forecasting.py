import pandas as pd
import numpy as np
from datetime import timedelta, date
import logging
import math
from typing import Optional
import constants as C

try:
    from prophet import Prophet

    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

logger = logging.getLogger(__name__)


def _create_features(df: pd.DataFrame, date_col: str, value_col: str, lags: list = None) -> pd.DataFrame:
    """
    Creates time series features for XGBoost (lags, rolling windows, date parts).

    Args:
        df (pd.DataFrame): The input dataframe containing historical data.
        date_col (str): The name of the column containing date values.
        value_col (str): The name of the column containing the target numeric values.
        lags (list, optional): List of lag periods to generate features for. 
                               Defaults to [1, 7, 14, 30].

    Returns:
        pd.DataFrame: A new DataFrame with additional columns for the generated features.
    """
    df = df.copy()
    if lags is None:
        lags = [1, 7, 14, 30]

    # Date features
    df["day_of_week"] = df[date_col].dt.dayofweek
    df["day_of_month"] = df[date_col].dt.day
    df["month"] = df[date_col].dt.month
    df["is_weekend"] = df["day_of_week"].apply(lambda x: 1 if x >= 5 else 0)

    # Lag features
    for lag in lags:
        df[f"lag_{lag}"] = df[value_col].shift(lag)

    # Rolling mean features
    for window in [7, 30]:
        df[f"rolling_mean_{window}"] = df[value_col].rolling(window=window).mean()

    return df


def _prepare_daily_series(df: pd.DataFrame, date_col: str, value_col: str) -> pd.DataFrame:
    """Aggregate input rows into a continuous daily time series."""
    base = df[[date_col, value_col]].copy()
    base[date_col] = pd.to_datetime(base[date_col], errors="coerce")
    base[value_col] = pd.to_numeric(base[value_col], errors="coerce").fillna(0)
    base = base.dropna(subset=[date_col])

    if base.empty:
        raise ValueError("Dados insuficientes para gerar previsao.")

    daily = base.groupby(base[date_col].dt.date)[value_col].sum().reset_index()
    daily[date_col] = pd.to_datetime(daily[date_col])
    daily = daily.sort_values(date_col)

    idx = pd.date_range(daily[date_col].min(), daily[date_col].max())
    daily = daily.set_index(date_col).reindex(idx, fill_value=0).reset_index()
    return daily.rename(columns={"index": date_col})


def _build_forecast_frame(
    daily: pd.DataFrame,
    future_dates: list,
    forecast_values,
    date_col: str,
    value_col: str,
) -> pd.DataFrame:
    """Combine historical daily data and future forecast values in the UI shape."""
    forecast_df = pd.DataFrame(
        {
            date_col: future_dates,
            value_col: np.asarray(forecast_values, dtype=float),
            C.COL_FORECAST_TYPE: C.UI_LABEL_FORECAST,
        }
    )

    history_df = daily.copy()
    history_df[C.COL_FORECAST_TYPE] = C.UI_LABEL_HISTORY
    return pd.concat([history_df, forecast_df], ignore_index=True)


def _run_model_forecast(
    daily: pd.DataFrame,
    date_col: str,
    value_col: str,
    algorithm: str,
    full_horizon_days: int,
) -> np.ndarray:
    """Return only the raw values predicted by the selected model."""
    last_date = daily[date_col].max()

    if algorithm == C.ALGORITHM_PROPHET:
        if not PROPHET_AVAILABLE:
            raise ImportError(C.ERR_MSG_PROPHET_NOT_INSTALLED)

        p_df = daily.rename(columns={date_col: "ds", value_col: "y"})
        model = Prophet(daily_seasonality=True, yearly_seasonality=False)
        model.fit(p_df)

        future = model.make_future_dataframe(periods=full_horizon_days)
        forecast = model.predict(future)
        return forecast.tail(full_horizon_days)["yhat"].to_numpy(dtype=float)

    if algorithm == C.ALGORITHM_HOLT_WINTERS:
        if not STATSMODELS_AVAILABLE:
            raise ImportError(C.ERR_MSG_STATSMODELS_NOT_INSTALLED)

        series = daily[value_col].astype(float)
        model = ExponentialSmoothing(
            series, trend="add", seasonal=None, initialization_method="estimated"
        )
        fit = model.fit()
        return np.asarray(fit.forecast(full_horizon_days).values, dtype=float)

    if algorithm == C.ALGORITHM_XGBOOST:
        if not XGBOOST_AVAILABLE:
            raise ImportError("Biblioteca xgboost nao instalada.")

        train_df = _create_features(daily, date_col, value_col).dropna()
        features = [c for c in train_df.columns if c not in [date_col, value_col, C.COL_FORECAST_TYPE]]
        X_train = train_df[features]
        y_train = train_df[value_col]

        model = xgb.XGBRegressor(
            objective="reg:squarederror", n_estimators=1000, learning_rate=0.05
        )
        model.fit(X_train, y_train)

        current_history = daily.copy()
        preds = []
        for i in range(full_horizon_days):
            next_date = last_date + timedelta(days=i + 1)
            new_row = pd.DataFrame({date_col: [next_date], value_col: [0]})
            temp_df = pd.concat([current_history, new_row], ignore_index=True)
            df_with_features = _create_features(temp_df, date_col, value_col)
            row_to_predict = df_with_features.iloc[[-1]][features]

            pred_val = max(0, model.predict(row_to_predict)[0])
            preds.append(pred_val)

            temp_df.iloc[-1, temp_df.columns.get_loc(value_col)] = pred_val
            current_history = temp_df

        return np.asarray(preds, dtype=float)

    avg_val = daily[value_col].mean()
    return np.asarray([avg_val] * full_horizon_days, dtype=float)


def apply_commercial_postprocessing(
    forecast_values,
    daily_history: pd.DataFrame,
    value_col: str,
    random_seed: Optional[int] = None,
) -> np.ndarray:
    """
    Apply business adjustments over raw model output.

    Adjustments are intentionally kept separate from model prediction:
    optimistic lift, sustainability floor, and optional deterministic noise.
    """
    forecast_values = np.asarray(forecast_values, dtype=float)
    if len(forecast_values) == 0:
        return forecast_values

    recent_avg = daily_history.tail(30)[value_col].mean()
    if pd.isna(recent_avg):
        recent_avg = 0

    first_forecast = forecast_values[0]
    bias_percentage = 0.0
    if first_forecast < recent_avg and first_forecast > 0:
        diff = (recent_avg - first_forecast) / first_forecast
        bias_percentage = min(diff, 0.20)

    adjusted_forecast = forecast_values * (1 + bias_percentage)

    floor = recent_avg * 0.4
    adjusted_forecast = np.maximum(adjusted_forecast, floor)

    hist_std = daily_history[value_col].std()
    if pd.isna(hist_std) or hist_std == 0:
        hist_std = recent_avg * 0.1

    if random_seed is None:
        noise = np.random.normal(0, hist_std * 0.3, size=len(adjusted_forecast))
    else:
        rng = np.random.default_rng(int(random_seed))
        noise = rng.normal(0, hist_std * 0.3, size=len(adjusted_forecast))

    return np.maximum(adjusted_forecast + noise, 0)


def generate_raw_model_forecast(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    algorithm: str,
    full_horizon_days: int,
) -> pd.DataFrame:
    """Generate a forecast using only raw model output, with no commercial adjustments."""
    daily = _prepare_daily_series(df, date_col, value_col)
    last_date = daily[date_col].max()
    future_dates = [last_date + timedelta(days=x) for x in range(1, full_horizon_days + 1)]
    raw_values = _run_model_forecast(daily, date_col, value_col, algorithm, full_horizon_days)
    return _build_forecast_frame(daily, future_dates, raw_values, date_col, value_col)


def generate_forecast(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    algorithm: str,
    full_horizon_days: int,
    forecast_mode: str = C.FORECAST_MODE_ADJUSTED,
    random_seed: Optional[int] = None,
) -> pd.DataFrame:
    """
    Generate a forecast DataFrame appended to historical daily data.

    Raw model prediction and commercial post-processing are separate steps. The
    default remains the adjusted commercial forecast to preserve existing UI
    behavior. Use C.FORECAST_MODE_RAW to inspect the model output directly.
    """
    daily = _prepare_daily_series(df, date_col, value_col)
    last_date = daily[date_col].max()
    future_dates = [last_date + timedelta(days=x) for x in range(1, full_horizon_days + 1)]

    raw_values = _run_model_forecast(daily, date_col, value_col, algorithm, full_horizon_days)
    if forecast_mode == C.FORECAST_MODE_RAW:
        forecast_values = raw_values
    else:
        forecast_values = apply_commercial_postprocessing(
            raw_values,
            daily,
            value_col,
            random_seed=random_seed,
        )

    return _build_forecast_frame(daily, future_dates, forecast_values, date_col, value_col)


def run_backtest(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    algorithm: str,
    test_days: int = 30,
    forecast_mode: str = C.FORECAST_MODE_ADJUSTED,
    random_seed: Optional[int] = None,
) -> dict:
    """
    Runs a backtest by splitting data into train/test, training the model,
    and comparing forecasts against actuals.

    Args:
        df (pd.DataFrame): The input dataframe containing historical data.
        date_col (str): The name of the column containing date values.
        value_col (str): The name of the column containing the target numeric values.
        algorithm (str): The algorithm to use for forecasting (e.g., 'Prophet', 'Holt-Winters').
        test_days (int, optional): The number of days to hold out for testing. Defaults to 30.
        forecast_mode (str, optional): Raw model forecast or commercially adjusted forecast.
        random_seed (int, optional): Seed for deterministic commercial noise.

    Returns:
        dict: A dictionary containing performance metrics:
            - 'mae' (float): Mean Absolute Error.
            - 'rmse' (float): Root Mean Squared Error.
            - 'mape' (float): Mean Absolute Percentage Error.
            - 'comparison_df' (pd.DataFrame): DataFrame comparing actual vs predicted values.
            - 'train_last_date' (pd.Timestamp): The last date used in the training set.
            - 'error' (str, optional): Error message if backtesting fails (e.g., insufficient data).
    """
    # Prepare Data
    daily = df.groupby(df[date_col].dt.date)[value_col].sum().reset_index()
    daily[date_col] = pd.to_datetime(daily[date_col])
    daily = daily.sort_values(date_col)

    # Fill missing days
    idx = pd.date_range(daily[date_col].min(), daily[date_col].max())
    daily = daily.set_index(date_col).reindex(idx, fill_value=0).reset_index()
    daily = daily.rename(columns={"index": date_col})

    if len(daily) <= test_days:
        return {"error": "Dados insuficientes para backtesting."}

    # Split Train/Test
    train_df = daily.iloc[:-test_days].copy()
    test_df = daily.iloc[-test_days:].copy()

    # Forecast
    # We reuse generate_forecast logic but need to strip the "post-processing"
    # if we want raw model accuracy, OR keep it if we want to test OUR pipeline.
    # Let's keep the pipeline to test "what user sees".

    # We need to adapt generate_forecast to accept a DF and return just values or DF
    # But generate_forecast expects raw transaction data usually?
    # No, it expects a DF with date_col and value_col.
    # train_df is already aggregated. generate_forecast re-aggregates.
    # That's fine, re-aggregating aggregated data is idempotent (sum of sums).

    forecast_result = generate_forecast(
        train_df,
        date_col,
        value_col,
        algorithm,
        test_days,
        forecast_mode=forecast_mode,
        random_seed=random_seed,
    )

    # Extract forecast part
    forecast_only = forecast_result[
        forecast_result["Type"] == C.UI_LABEL_FORECAST
    ].copy()

    # Align dates
    # generate_forecast generates dates starting from train_df.max() + 1 day
    # which matches test_df structure exactly.

    # Merge for comparison
    comparison = pd.merge(
        test_df[[date_col, value_col]],
        forecast_only[[date_col, value_col]],
        on=date_col,
        how="inner",
        suffixes=("_actual", "_predicted"),
    )

    # Calculate Metrics
    y_true = comparison[f"{value_col}_actual"]
    y_pred = comparison[f"{value_col}_predicted"]

    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))

    # MAPE (avoid div by zero)
    # Add epsilon or filter zeros
    non_zero = y_true != 0
    if non_zero.any():
        mape = (
            np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero]))
            * 100
        )
    else:
        mape = 0.0

    return {
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "comparison_df": comparison,
        "train_last_date": train_df[date_col].max(),
    }


def generate_smart_insights(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    forecast_df: pd.DataFrame,
    unit_label: str = C.LABEL_NEW_CONTRACTS,
    is_currency: bool = False,
) -> str:
    """
    Generates a natural language summary and analysis of the historical and forecast data.

    It calculates:
    - **Recent Trend**: Compares the last 7 days vs the previous 7 days to determine if the
      metric is growing, slowing down, or stable.
    - **Forecast Totals**: Sums up the predicted values for the full horizon.
    - **Daily Average**: Calculates the expected daily run rate.
    - **Strategic Insight**: Compares the forecast daily average with the recent history to
      give a qualitative assessment (Positive, Negative, or Neutral).

    Args:
        df (pd.DataFrame): Historical data.
        date_col (str): Date column name.
        value_col (str): Value column name.
        forecast_df (pd.DataFrame): The output from `generate_forecast`.
        unit_label (str, optional): Label for the unit (e.g., "novos contratos"). Defaults to C.LABEL_NEW_CONTRACTS.
        is_currency (bool, optional): If True, formats values as currency (R$). Defaults to False.

    Returns:
        str: A formatted string with emojis and insights ready for display in Streamlit.
    """
    # 1. Historical Analysis
    daily = df.groupby(df[date_col].dt.date)[value_col].sum().sort_index()
    if len(daily) < 14:
        return C.MSG_INSUFFICIENT_DATA

    recent_avg = daily.tail(7).mean()
    prev_avg = daily.iloc[-14:-7].mean()

    trend_pct = 0
    if prev_avg > 0:
        trend_pct = ((recent_avg - prev_avg) / prev_avg) * 100

    # 2. Forecast Analysis
    future_only = forecast_df[
        forecast_df[C.COL_FORECAST_TYPE] == C.LABEL_FORECAST_TYPE_FORECAST
    ]
    future_sum = future_only[value_col].sum()
    future_daily_avg = future_only[value_col].mean()

    horizon_days = len(future_only)

    # 3. Construct Text
    text = C.MSG_SMART_ANALYSIS_TITLE

    # Trend
    if trend_pct > 5:
        emoji = "🚀"
        trend_desc = C.INSIGHT_GROWTH
    elif trend_pct < -5:
        emoji = "⚠️"
        trend_desc = C.INSIGHT_SLOWDOWN
    else:
        emoji = "⚖️"
        trend_desc = C.INSIGHT_STABLE

    text += f"{C.MSG_RECENT_TREND} {trend_desc} ({trend_pct:+.1f}%) {emoji}\n\n"

    text += C.MSG_FORECAST_NEXT_DAYS.format(horizon_days=horizon_days)

    if is_currency:
        text += f"- {C.MSG_ESTIMATED_TOTAL} R$ {future_sum:,.2f}\n"
        text += f"- {C.MSG_EXPECTED_DAILY_AVG} R$ {future_daily_avg:,.2f}/dia\n\n"
    else:
        text += f"- {C.MSG_ESTIMATED_TOTAL} {int(future_sum)} {unit_label}\n"
        text += (
            f"- {C.MSG_EXPECTED_DAILY_AVG} {future_daily_avg:.1f} {unit_label}/dia\n\n"
        )

    if future_daily_avg > recent_avg * 1.05:
        text += f"{C.MSG_INSIGHT_PREFIX} {C.INSIGHT_POSITIVE}"
    elif future_daily_avg < recent_avg * 0.9:
        text += f"{C.MSG_INSIGHT_PREFIX} {C.INSIGHT_NEGATIVE}"
    else:
        text += f"{C.MSG_INSIGHT_PREFIX} {C.INSIGHT_NEUTRAL}"

    return text
