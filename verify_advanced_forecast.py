import pandas as pd
import forecasting
from datetime import datetime
import numpy as np


def test_advanced_forecast():
    try:
        from prophet import Prophet

        print("✅ Prophet is installed.")
    except ImportError:
        print("❌ Prophet NOT installed.")

    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        print("✅ Statsmodels is installed.")
    except ImportError:
        print("❌ Statsmodels NOT installed.")

    # Create seasonal data (sine wave)
    dates = pd.date_range(start="2023-01-01", periods=100)
    values = [10 + 5 * np.sin(i / 7) + i / 10 for i in range(100)]  # Seasonal + Trend
    df = pd.DataFrame({"Date": dates, "Value": values})

    # Test Prophet
    print("\nTesting Prophet...")
    if forecasting.PROPHET_AVAILABLE:
        try:
            forecast = forecasting.generate_forecast(
                df, "Date", "Value", "Prophet (Facebook AI)", 14
            )
            future = forecast[forecast["Type"] == "Previsão"]
            if len(future) == 14:
                print("✅ Prophet generated 14 days forecast.")
            else:
                print(f"❌ Prophet generated {len(future)} days (Expected 14).")
        except Exception as e:
            print(f"❌ Prophet Error: {e}")
    else:
        print("Skipping Prophet test (not available).")

    # Test Holt-Winters
    print("\nTesting Holt-Winters...")
    if forecasting.STATSMODELS_AVAILABLE:
        try:
            forecast = forecasting.generate_forecast(
                df, "Date", "Value", "Holt-Winters (Sazonal)", 14
            )
            future = forecast[forecast["Type"] == "Previsão"]
            if len(future) == 14:
                print("✅ Holt-Winters generated 14 days forecast.")
            else:
                print(f"❌ Holt-Winters generated {len(future)} days (Expected 14).")
        except Exception as e:
            print(f"❌ Holt-Winters Error: {e}")

    # Test Insights
    print("\nTesting Insights...")
    dummy_forecast = df.copy()  # Just for shape
    dummy_forecast["Type"] = "Previsão"
    insights = forecasting.generate_smart_insights(df, "Date", "Value", dummy_forecast)
    if "Análise Inteligente" in insights:
        print("✅ Insights generated.")
    else:
        print("❌ Insights failed.")


if __name__ == "__main__":
    test_advanced_forecast()
