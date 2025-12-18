import pytest
import pandas as pd
import numpy as np
import constants as C
from forecasting import generate_forecast

class TestForecasting:
    def test_optimistic_bias(self):
        # Create synthetic historical data (last 30 days stable at 100)
        dates = pd.date_range(end=pd.Timestamp.today(), periods=60)
        df = pd.DataFrame({
            "date": dates,
            "value": [100] * 60
        })
        
        # We use a mock algorithm name to trigger the fallback (zeros)
        # This ensures the raw forecast is 0, which is < recent history (100)
        # The optimistic bias should kick in.
        
        forecast_df = generate_forecast(
            df=df,
            date_col="date",
            value_col="value",
            algorithm="UNKNOWN_ALGO",
            full_horizon_days=30
        )
        
        future_forecast = forecast_df[forecast_df["Type"] == "Previsão"]["value"]
        
        # Recent average is 100.
        # Target mean is 100 * 1.05 = 105.
        # Raw forecast is 0.
        # Lift should be roughly 105.
        # Since history is constant, std dev is 0, so noise is 0.
        
        assert np.allclose(future_forecast.mean(), 105.0, atol=1.0)
        assert future_forecast.min() > 100.0

    def test_forecast_structure(self):
        dates = pd.date_range(start="2023-01-01", periods=10)
        df = pd.DataFrame({
            "date": dates,
            "value": np.random.rand(10) * 100
        })
        
        forecast_df = generate_forecast(
            df=df,
            date_col="date",
            value_col="value",
            algorithm="UNKNOWN_ALGO",
            full_horizon_days=5
        )
        
        # Check columns
        assert "date" in forecast_df.columns
        assert "value" in forecast_df.columns
        assert "Type" in forecast_df.columns
        
        # Check rows count (10 historical + 5 forecast)
        # Note: The code fills missing days in history, so if input is continuous 10 days, output history is 10 days.
        assert len(forecast_df) == 15
        assert len(forecast_df[forecast_df["Type"] == "Previsão"]) == 5
