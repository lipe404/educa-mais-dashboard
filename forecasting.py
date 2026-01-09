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

        # Add small constant to avoid zero issues if multiplicative
        series = daily[value_col] + 1e-6

        # Fit (Triple Exponential Smoothing)
        # We assume weekly seasonality (7 days)
        model = ExponentialSmoothing(
            series,
            seasonal_periods=7,
            trend="add",
            seasonal="add",
            initialization_method="estimated",
        ).fit()

        forecast_values = model.forecast(full_horizon_days).values

    else:
        # Default/Fallback
        forecast_values = np.zeros(full_horizon_days)

    # ---------------------------------------------------------
    # OPTIMISTIC BIAS CORRECTION
    # ---------------------------------------------------------
    # Check if forecast average is below recent history average.
    # If so, lift the curve to at least match recent history + 5%.

    recent_history = daily[value_col].tail(30)  # Last 30 days
    if not recent_history.empty and len(forecast_values) > 0:
        recent_avg = recent_history.mean()

        # Compare with the start of the forecast (max 30 days) to align trend entry
        validation_len = min(len(forecast_values), 30)
        forecast_start_avg = np.mean(forecast_values[:validation_len])

        # If the model's starting point is lower than recent history, lift it.
        # We apply a constant offset so the *start* matches recent history + small optimism.
        if forecast_start_avg < recent_avg:
            # Target is recent_avg + 5% boost
            target_mean = recent_avg * 1.05
            lift = target_mean - forecast_start_avg

            # Apply lift
            forecast_values = forecast_values + lift

    # ---------------------------------------------------------
    # SUSTAINABILITY & ORGANIC VARIABILITY (FIXES)
    # ---------------------------------------------------------

    # 1. Sustainability Floor: Prevent trend to zero in long horizons.
    if recent_avg > 0:
        # Floor = 40% of recent average. usage: max(forecast, floor).
        floor = recent_avg * 0.4
        forecast_values = np.maximum(forecast_values, floor)

    # 2. Organic Noise: Break rigid repeating patterns.
    if len(recent_history) > 1:
        # Use 30% of historical std dev as noise scale.
        noise_scale = recent_history.std() * 0.3
        # Generate noise
        noise = np.random.normal(0, noise_scale, size=len(forecast_values))
        forecast_values = forecast_values + noise

    # Final cleanup: Ensure no negatives
    forecast_values = np.maximum(forecast_values, 0)

    future_df[value_col] = forecast_values
    future_df[C.COL_FORECAST_TYPE] = C.LABEL_FORECAST_TYPE_FORECAST

    # Combine
    daily[C.COL_FORECAST_TYPE] = C.LABEL_FORECAST_TYPE_HISTORY
    if "days_from_start" in daily.columns:
        daily = daily.drop(columns=["days_from_start"])

    final_df = pd.concat([daily, future_df], ignore_index=True)
    return final_df


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
