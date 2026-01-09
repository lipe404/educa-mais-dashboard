import pandas as pd
import numpy as np
from datetime import timedelta, date
import logging
import math
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

logger = logging.getLogger(__name__)


def generate_forecast(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    algorithm: str,
    full_horizon_days: int,
) -> pd.DataFrame:
    """
    Generates a forecast DataFrame appended to the historical data using Prophet or Holt-Winters.

    This function applies advanced post-processing to the forecast, including:
    1.  **Optimistic Bias**: Lifts the forecast curve if the initial predicted values are lower
        than the recent historical average (last 30 days), ensuring the forecast doesn't
        start with an unrealistic drop.
    2.  **Sustainability Floor**: Enforces a minimum value (40% of recent average) to prevent
        the trend from crashing to zero in long horizons.
    3.  **Organic Noise**: Adds random Gaussian noise based on historical volatility (30% of std dev)
        to simulate natural day-to-day variations and avoid artificially smooth lines.

    Args:
        df (pd.DataFrame): The input dataframe containing historical data.
        date_col (str): The name of the column containing date values.
        value_col (str): The name of the column containing the target numeric values to forecast.
        algorithm (str): The algorithm to use. Options: 'Prophet' or 'Holt-Winters'.
        full_horizon_days (int): The number of days to forecast into the future.

    Returns:
        pd.DataFrame: A new DataFrame containing both historical data and the generated forecast.
                      It includes a 'Type' column distinguishing 'Histórico' from 'Previsão'.
                      For 'Previsão' rows, the 'value_col' contains the predicted values (adjusted).
    
    Raises:
        ImportError: If the selected algorithm library (prophet or statsmodels) is not installed.
    """
    # Prepare Base Data (Daily Aggregation)
    daily = df.groupby(df[date_col].dt.date)[value_col].sum().reset_index()
    daily[date_col] = pd.to_datetime(daily[date_col])
    daily = daily.sort_values(date_col)

    # Fill missing days with 0 to have a continuous time series
    idx = pd.date_range(daily[date_col].min(), daily[date_col].max())
    daily = daily.set_index(date_col).reindex(idx, fill_value=0).reset_index()
    daily = daily.rename(columns={"index": date_col})

    # Generate Future Dates
    last_date = daily[date_col].max()
    future_dates = [
        last_date + timedelta(days=x) for x in range(1, full_horizon_days + 1)
    ]
    future_df = pd.DataFrame({date_col: future_dates})

    forecast_values = []

    # ---------------------------------------------------------
    # ALGORITHMS
    # ---------------------------------------------------------

    if algorithm == C.ALGORITHM_PROPHET:
        if not PROPHET_AVAILABLE:
            raise ImportError(C.ERR_MSG_PROPHET_NOT_INSTALLED)

        # Prepare Data for Prophet (ds, y)
        p_df = daily.rename(columns={date_col: "ds", value_col: "y"})

        m = Prophet(daily_seasonality=True, yearly_seasonality=False)
        m.fit(p_df)

        future = m.make_future_dataframe(periods=full_horizon_days)
        forecast = m.predict(future)

        # Extract only future part
        forecast_values = forecast.tail(full_horizon_days)["yhat"].values

    elif algorithm == C.ALGORITHM_HOLT_WINTERS:
        if not STATSMODELS_AVAILABLE:
            raise ImportError(C.ERR_MSG_STATSMODELS_NOT_INSTALLED)

        # Ensure numeric type
        series = daily[value_col].astype(float)
        
        # Add small noise to avoid zero errors if needed, but usually not strict for add model
        # ExponentialSmoothing
        # Use simple 'add' trend/seasonal for robustness on small data
        model = ExponentialSmoothing(
            series, trend="add", seasonal=None, initialization_method="estimated"
        )
        fit = model.fit()
        forecast_values = fit.forecast(full_horizon_days).values

    else:
        # Default fallback (Naive average)
        avg_val = daily[value_col].mean()
        forecast_values = [avg_val] * full_horizon_days

    # ---------------------------------------------------------
    # POST-PROCESSING RULES
    # ---------------------------------------------------------
    
    # 1. Optimistic Bias:
    # If the forecast starts lower than the recent average (last 30 days), 
    # we lift it slightly to assume growth, not immediate crash.
    recent_avg = daily.tail(30)[value_col].mean()
    if pd.isna(recent_avg): 
        recent_avg = 0
        
    first_forecast = forecast_values[0] if len(forecast_values) > 0 else 0
    
    bias_percentage = 0.0
    if first_forecast < recent_avg and first_forecast > 0:
         # Calculate how much lower it is
         diff = (recent_avg - first_forecast) / first_forecast
         # Cap bias at 20% to avoid explosion
         bias_percentage = min(diff, 0.20)
    
    # Apply bias
    adjusted_forecast = [v * (1 + bias_percentage) for v in forecast_values]

    # 2. Sustainability Floor:
    # Ensure no value drops below 40% of the recent average (unless recent average is 0)
    floor = recent_avg * 0.4
    adjusted_forecast = [max(v, floor) for v in adjusted_forecast]

    # 3. Organic Noise:
    # Add random variation based on historical std dev
    hist_std = daily[value_col].std()
    if pd.isna(hist_std) or hist_std == 0:
        hist_std = recent_avg * 0.1 # Default 10% if no std
        
    # Generate noise for each day
    # Use fixed seed for reproducibility within same call if needed, but random is better for "organic" feel
    noise = np.random.normal(0, hist_std * 0.3, size=len(adjusted_forecast)) 
    
    final_values = []
    for val, n in zip(adjusted_forecast, noise):
        final_val = val + n
        # Ensure non-negative
        final_values.append(max(0, final_val))

    # Combine into DataFrame
    forecast_df = pd.DataFrame(
        {
            date_col: future_dates,
            value_col: final_values,
            "Type": C.UI_LABEL_FORECAST,
        }
    )

    daily["Type"] = C.UI_LABEL_HISTORY
    final_df = pd.concat([daily, forecast_df], ignore_index=True)

    return final_df

def run_backtest(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    algorithm: str,
    test_days: int = 30
) -> dict:
    """
    Runs a backtest by splitting data into train/test, training the model,
    and comparing forecasts against actuals.
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
        train_df, date_col, value_col, algorithm, test_days
    )
    
    # Extract forecast part
    forecast_only = forecast_result[forecast_result["Type"] == C.UI_LABEL_FORECAST].copy()
    
    # Align dates
    # generate_forecast generates dates starting from train_df.max() + 1 day
    # which matches test_df structure exactly.
    
    # Merge for comparison
    comparison = pd.merge(
        test_df[[date_col, value_col]], 
        forecast_only[[date_col, value_col]], 
        on=date_col, 
        how="inner",
        suffixes=("_actual", "_predicted")
    )
    
    # Calculate Metrics
    y_true = comparison[f"{value_col}_actual"]
    y_pred = comparison[f"{value_col}_predicted"]
    
    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred)**2))
    
    # MAPE (avoid div by zero)
    # Add epsilon or filter zeros
    non_zero = y_true != 0
    if non_zero.any():
        mape = np.mean(np.abs((y_true[non_zero] - y_pred[non_zero]) / y_true[non_zero])) * 100
    else:
        mape = 0.0
        
    return {
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "comparison_df": comparison,
        "train_last_date": train_df[date_col].max()
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
    future_only = forecast_df[forecast_df[C.COL_FORECAST_TYPE] == C.LABEL_FORECAST_TYPE_FORECAST]
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

    text += (
        f"{C.MSG_RECENT_TREND} {trend_desc} ({trend_pct:+.1f}%) {emoji}\n\n"
    )

    text += C.MSG_FORECAST_NEXT_DAYS.format(horizon_days=horizon_days)

    if is_currency:
        text += f"- {C.MSG_ESTIMATED_TOTAL} R$ {future_sum:,.2f}\n"
        text += f"- {C.MSG_EXPECTED_DAILY_AVG} R$ {future_daily_avg:,.2f}/dia\n\n"
    else:
        text += f"- {C.MSG_ESTIMATED_TOTAL} {int(future_sum)} {unit_label}\n"
        text += f"- {C.MSG_EXPECTED_DAILY_AVG} {future_daily_avg:.1f} {unit_label}/dia\n\n"

    if future_daily_avg > recent_avg * 1.05:
        text += f"{C.MSG_INSIGHT_PREFIX} {C.INSIGHT_POSITIVE}"
    elif future_daily_avg < recent_avg * 0.9:
        text += f"{C.MSG_INSIGHT_PREFIX} {C.INSIGHT_NEGATIVE}"
    else:
        text += f"{C.MSG_INSIGHT_PREFIX} {C.INSIGHT_NEUTRAL}"

    return text
