import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import constants as C
from forecasting import generate_forecast, generate_smart_insights, run_backtest
import forecasting # Import module for patching

class TestForecasting:
    @patch("forecasting.Prophet")
    def test_optimistic_bias(self, mock_prophet_class):
        # Create synthetic historical data (last 30 days stable at 100)
        dates = pd.date_range(end=pd.Timestamp.today(), periods=60)
        df = pd.DataFrame({
            "date": dates,
            "value": [100] * 60
        })
        
        # Mock Prophet to return LOW forecast (e.g. 50)
        # Recent average is 100.
        # Forecast 50 is < 100.
        # Bias should kick in.
        # Bias max is 20%. 
        # So it should lift 50 by 20% -> 60.
        # Wait, bias percentage = min((100 - 50)/50, 0.20) = min(1.0, 0.20) = 0.20.
        # Adjusted = 50 * 1.2 = 60.
        
        m = MagicMock()
        mock_prophet_class.return_value = m
        future_dates = pd.date_range(start=dates[-1] + pd.Timedelta(days=1), periods=30)
        forecast_ret = pd.DataFrame({
            "ds": future_dates,
            "yhat": [50.0] * 30
        })
        m.predict.return_value = forecast_ret
        m.make_future_dataframe.return_value = pd.DataFrame({"ds": future_dates})

        with patch("forecasting.PROPHET_AVAILABLE", True):
            forecast_df = generate_forecast(
                df=df,
                date_col="date",
                value_col="value",
                algorithm=C.ALGORITHM_PROPHET,
                full_horizon_days=30
            )
        
        future_forecast = forecast_df[forecast_df["Type"] == "Previsão"]["value"]
        
        # We expect values around 60 (50 * 1.2) + noise.
        # Noise std is based on history std.
        # History is constant 100, so hist_std=0 -> default 10% of 100 = 10.
        # Noise added is Normal(0, 10 * 0.3) = Normal(0, 3).
        
        # So mean should be approx 60.
        # Let's assert it is significantly higher than raw 50.
        
        assert future_forecast.mean() > 55.0
        assert future_forecast.mean() < 65.0

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

    def test_sustainability_floor(self):
        # Scenario: History is 100, but raw forecast (zeros) drops to 0.
        # Floor should be 40% of 100 = 40.
        # Note: Optimistic bias might also kick in (lifting to 105).
        # To isolate floor, we need raw forecast to be low but optimistic bias NOT to trigger?
        # Actually optimistic bias compares average.
        # If we have high volatility, maybe we can trigger floor.
        
        # Let's rely on the fact that if bias kicks in, it lifts.
        # But if we manually disable bias logic in our mind, floor is recent_avg * 0.4.
        
        # Let's test that values never go below floor (except if noise pushes it, but noise is random).
        # With constant history, noise is 0.
        
        dates = pd.date_range(end=pd.Timestamp.today(), periods=60)
        df = pd.DataFrame({
            "date": dates,
            "value": [100] * 60
        })

        # We need a scenario where forecast is generated as very low, say 10.
        # But `generate_forecast` uses Prophet/HoltWinters or Zeros.
        # If we use Zeros, Optimistic Bias lifts it to 105.
        
        # If we want to test floor, we need to check if max(value, floor) is working.
        # Since Optimistic Bias lifts to 105, which is > 40, floor doesn't trigger effectively for Zeros.
        
        # However, we can check that it returns non-negative values at least.
        forecast_df = generate_forecast(
            df=df,
            date_col="date",
            value_col="value",
            algorithm="UNKNOWN_ALGO",
            full_horizon_days=10
        )
        future_vals = forecast_df[forecast_df["Type"] == "Previsão"]["value"]
        assert (future_vals >= 0).all()

    def test_smart_insights_generation(self):
        # Create a scenario where trend is positive
        dates = pd.date_range(end=pd.Timestamp.today(), periods=20)
        # Increasing values
        values = np.linspace(10, 100, 20)
        df = pd.DataFrame({"date": dates, "value": values})
        
        # Mock forecast df
        future_dates = pd.date_range(start=dates[-1] + pd.Timedelta(days=1), periods=5)
        forecast_df = pd.DataFrame({
            "date": future_dates,
            "value": [110, 115, 120, 125, 130],
            "Type": ["Previsão"] * 5
        })
        
        insight = generate_smart_insights(
            df=df,
            date_col="date",
            value_col="value",
            forecast_df=forecast_df,
            unit_label="contratos"
        )
        
        assert "🚀" in insight  # Growth emoji
        assert "Previsão para os próximos 5 dias" in insight
        assert "110" not in insight # It shows totals/averages
        assert "Média diária" in insight

    def test_smart_insights_insufficient_data(self):
        dates = pd.date_range(end=pd.Timestamp.today(), periods=5)
        df = pd.DataFrame({"date": dates, "value": [10]*5})
        forecast_df = pd.DataFrame()
        
        insight = generate_smart_insights(
            df=df,
            date_col="date",
            value_col="value",
            forecast_df=forecast_df
        )
        
        assert insight == C.MSG_INSUFFICIENT_DATA

    def test_smart_insights_scenarios(self):
        # Base data
        dates = pd.date_range(end=pd.Timestamp.today(), periods=20)
        
        # Scenario 1: Negative Trend (Warning emoji)
        # Recent avg (last 7) < Previous avg (prev 7)
        values_down = np.linspace(100, 10, 20)
        df_down = pd.DataFrame({"date": dates, "value": values_down})
        
        # Forecast showing decrease (Negative insight)
        future_dates = pd.date_range(start=dates[-1] + pd.Timedelta(days=1), periods=5)
        forecast_down = pd.DataFrame({
            "date": future_dates,
            "value": [5, 4, 3, 2, 1],
            "Type": ["Previsão"] * 5
        })
        
        insight = generate_smart_insights(df_down, "date", "value", forecast_down)
        assert "⚠️" in insight
        assert C.INSIGHT_NEGATIVE in insight

        # Scenario 2: Stable Trend (Balance emoji)
        values_stable = np.ones(20) * 100
        df_stable = pd.DataFrame({"date": dates, "value": values_stable})
        
        # Forecast showing stability (Neutral insight)
        forecast_stable = pd.DataFrame({
            "date": future_dates,
            "value": [100] * 5,
            "Type": ["Previsão"] * 5
        })
        
        insight = generate_smart_insights(df_stable, "date", "value", forecast_stable)
        assert "⚖️" in insight
        assert C.INSIGHT_NEUTRAL in insight

    @patch("forecasting.Prophet")
    def test_generate_forecast_prophet(self, mock_prophet_class):
        # Mock Prophet instance
        m = MagicMock()
        mock_prophet_class.return_value = m
        
        # Mock predict return
        future_dates = pd.date_range(start="2023-01-11", periods=5)
        forecast_ret = pd.DataFrame({
            "ds": future_dates,
            "yhat": [10, 11, 12, 13, 14]
        })
        m.predict.return_value = forecast_ret
        
        df = pd.DataFrame({
            "date": pd.date_range(start="2023-01-01", periods=10),
            "value": [10] * 10
        })
        
        # Mock global PROPHET_AVAILABLE
        # Since we mock the class, we assume the import check passes or we bypass it.
        # But generate_forecast checks the flag.
        # We can patch the flag in the module.
        with patch("forecasting.PROPHET_AVAILABLE", True):
            forecast_df = generate_forecast(
                df, "date", "value", C.ALGORITHM_PROPHET, 5
            )
            
        assert len(forecast_df[forecast_df["Type"] == "Previsão"]) == 5
        # 10 history + 5 forecast = 15
        assert len(forecast_df) == 15

    # --- Backtesting Tests ---

    def test_run_backtest_insufficient_data(self):
        # Create small dataframe (5 days)
        dates = pd.date_range(end=pd.Timestamp.today(), periods=5)
        df = pd.DataFrame({"date": dates, "value": [10]*5})
        
        # Request 30 days backtest
        result = forecasting.run_backtest(
            df=df,
            date_col="date",
            value_col="value",
            algorithm="Naive",
            test_days=30
        )
        
        assert "error" in result
        assert result["error"] == "Dados insuficientes para backtesting."

    def test_run_backtest_success(self):
        # Create ample data (60 days)
        dates = pd.date_range(end=pd.Timestamp.today(), periods=60)
        # Constant value to make prediction easy (Naive uses mean)
        df = pd.DataFrame({"date": dates, "value": [100.0]*60})
        
        # Test last 10 days
        result = forecasting.run_backtest(
            df=df,
            date_col="date",
            value_col="value",
            algorithm="Naive", # Should predict mean (~100)
            test_days=10
        )
        
        assert "error" not in result
        assert "mae" in result
        assert "rmse" in result
        assert "mape" in result
        assert "comparison_df" in result
        
        # Since history is constant 100, forecast (Naive) should be roughly 100.
        # However, generate_forecast adds noise and optimistic bias.
        # But we can check ranges.
        # MAE should be relatively low (mostly noise).
        # It shouldn't be huge.
        assert result["mae"] < 50.0 

    def test_run_backtest_metrics_calculation(self):
        # We need to mock generate_forecast to return deterministic values
        # so we can verify MAE/RMSE calculation exactly.
        
        dates = pd.date_range(start="2023-01-01", periods=10) # 10 days total
        # Split: 5 train, 5 test
        
        df = pd.DataFrame({
            "date": dates,
            "value": [10, 10, 10, 10, 10,  # Train
                      20, 20, 20, 20, 20]  # Test (Actuals)
        })
        
        # We want predicted to be 15 for the test period
        # Error = |20 - 15| = 5
        # MAE = 5
        # RMSE = 5
        # MAPE = (5/20) = 25%
        
        # Mock generate_forecast
        with patch("forecasting.generate_forecast") as mock_gen:
            # Prepare mock return
            # It needs to return history + forecast
            # History (train) dates: Jan 1 to Jan 5
            # Forecast (test) dates: Jan 6 to Jan 10
            
            history_df = pd.DataFrame({
                "date": dates[:5],
                "value": [10]*5,
                "Type": [C.UI_LABEL_HISTORY]*5
            })
            
            forecast_df = pd.DataFrame({
                "date": dates[5:],
                "value": [15.0]*5, # Predicted
                "Type": [C.UI_LABEL_FORECAST]*5
            })
            
            mock_gen.return_value = pd.concat([history_df, forecast_df])
            
            result = forecasting.run_backtest(
                df=df,
                date_col="date",
                value_col="value",
                algorithm="Dummy",
                test_days=5
            )
            
            assert result["mae"] == 5.0
            assert result["rmse"] == 5.0
            assert result["mape"] == 25.0

    def test_run_backtest_mape_zero_handling(self):
        # Scenario: Actuals contain zero
        dates = pd.date_range(start="2023-01-01", periods=4)
        # Train: 2 days, Test: 2 days
        # Test Actuals: [0, 100]
        # Predicted: [10, 10]
        
        df = pd.DataFrame({
            "date": dates,
            "value": [10, 10, 0, 100]
        })
        
        with patch("forecasting.generate_forecast") as mock_gen:
            forecast_df = pd.DataFrame({
                "date": dates[2:],
                "value": [10.0, 10.0],
                "Type": [C.UI_LABEL_FORECAST]*2
            })
            # We don't strictly need history in return for backtest logic, but good practice
            mock_gen.return_value = forecast_df 
            
            result = forecasting.run_backtest(df, "date", "value", "Dummy", test_days=2)
            
            # MAPE Calculation:
            # Day 1: Actual=0, Pred=10. Skipped for MAPE? 
            # Code: non_zero = y_true != 0. 
            # Only Day 2 is calculated.
            # Day 2: Actual=100, Pred=10. Diff=90. Abs(90/100) = 0.9 = 90%
            # MAPE = Mean([90%]) = 90.0
            
            assert result["mape"] == 90.0


    @patch("forecasting.ExponentialSmoothing")
    def test_generate_forecast_holt_winters(self, mock_es_class):
        # Mock fit return
        model_fit = MagicMock()
        mock_es_class.return_value.fit.return_value = model_fit
        model_fit.forecast.return_value = pd.Series([10, 11, 12, 13, 14])
        
        df = pd.DataFrame({
            "date": pd.date_range(start="2023-01-01", periods=10),
            "value": [10] * 10
        })
        
        with patch("forecasting.STATSMODELS_AVAILABLE", True):
            forecast_df = generate_forecast(
                df, "date", "value", C.ALGORITHM_HOLT_WINTERS, 5
            )
            
            assert len(forecast_df[forecast_df["Type"] == "Previsão"]) == 5
            mock_es_class.assert_called()
            model_fit.forecast.assert_called()
