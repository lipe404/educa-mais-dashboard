import pandas as pd
import numpy as np
from datetime import timedelta, date
import logging
import math

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
    Generates a forecast DataFrame appended to the historical data.
    Only supports Prophet and Holt-Winters with Optimistic Bias.
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

    if algorithm == "Prophet (Facebook AI)":
        if not PROPHET_AVAILABLE:
            raise ImportError("Biblioteca Prophet não instalada.")

        # Prepare Data for Prophet (ds, y)
        p_df = daily.rename(columns={date_col: "ds", value_col: "y"})

        m = Prophet(daily_seasonality=True, yearly_seasonality=False)
        m.fit(p_df)

        future = m.make_future_dataframe(periods=full_horizon_days)
        forecast = m.predict(future)

        # Extract only future part
        forecast_values = forecast.tail(full_horizon_days)["yhat"].values

    elif algorithm == "Holt-Winters (Sazonal)":
        if not STATSMODELS_AVAILABLE:
            raise ImportError("Biblioteca statsmodels não instalada.")

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

    # Final cleanup: Ensure no negatives
    forecast_values = np.maximum(forecast_values, 0)

    future_df[value_col] = forecast_values
    future_df["Type"] = "Previsão"

    # Combine
    daily["Type"] = "Histórico"
    if "days_from_start" in daily.columns:
        daily = daily.drop(columns=["days_from_start"])

    final_df = pd.concat([daily, future_df], ignore_index=True)
    return final_df


def generate_smart_insights(
    df: pd.DataFrame, date_col: str, value_col: str, forecast_df: pd.DataFrame
) -> str:
    """
    Generates text analysis of the historical and forecast data.
    """
    # 1. Historical Analysis
    daily = df.groupby(df[date_col].dt.date)[value_col].sum().sort_index()
    if len(daily) < 14:
        return "Dados insuficientes para análise detalhada (mínimo 2 semanas)."

    recent_avg = daily.tail(7).mean()
    prev_avg = daily.iloc[-14:-7].mean()

    trend_pct = 0
    if prev_avg > 0:
        trend_pct = ((recent_avg - prev_avg) / prev_avg) * 100

    # 2. Forecast Analysis
    future_only = forecast_df[forecast_df["Type"] == "Previsão"]
    future_sum = future_only[value_col].sum()
    future_daily_avg = future_only[value_col].mean()

    horizon_days = len(future_only)

    # 3. Construct Text
    text = f"### 🧠 Análise Inteligente\n\n"

    # Trend
    if trend_pct > 5:
        emoji = "🚀"
        trend_desc = "Crescimento acelerado"
    elif trend_pct < -5:
        emoji = "⚠️"
        trend_desc = "Desaceleração recente"
    else:
        emoji = "⚖️"
        trend_desc = "Estabilidade"

    text += (
        f"**Tendência Recente (7 dias):** {trend_desc} ({trend_pct:+.1f}%) {emoji}\n\n"
    )

    text += f"**Previsão para os próximos {horizon_days} dias:**\n"
    text += f"- **Total estimado:** {int(future_sum)} novos contratos\n"
    text += f"- **Média diária esperada:** {future_daily_avg:.1f} contratos/dia\n\n"

    if future_daily_avg > recent_avg * 1.05:
        text += "> **Insight:** O modelo (ajustado com otimismo) prevê uma performance sólida para o período."
    elif future_daily_avg < recent_avg * 0.9:
        text += "> **Insight:** O modelo prevê uma leve queda. Verifique campanhas ou sazonalidade."
    else:
        text += "> **Insight:** A previsão indica manutenção do ritmo atual de vendas."

    return text
