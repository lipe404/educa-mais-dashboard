import pytest
import pandas as pd
import numpy as np
from services.data import parse_datetime_any, to_float_any, validate_columns, process_column

class TestDataService:
    def test_parse_datetime_any(self):
        # Valid dates
        assert parse_datetime_any("2023-01-01").date() == pd.Timestamp("2023-01-01").date()
        assert parse_datetime_any("01/01/2023").date() == pd.Timestamp("2023-01-01").date()
        
        # Invalid dates
        assert parse_datetime_any("not a date") is None
        assert parse_datetime_any(None) is None
        assert parse_datetime_any(float("nan")) is None

    def test_to_float_any(self):
        # Valid numbers
        assert to_float_any("100.50") == 100.50
        assert to_float_any("100,50") == 100.50
        assert to_float_any(100) == 100.0
        
        # Invalid numbers
        assert np.isnan(to_float_any("abc"))
        assert np.isnan(to_float_any(None))

    def test_validate_columns(self):
        df = pd.DataFrame({"A": [1], "B": [2]})
        assert validate_columns(df, ["A", "B"]) is True
        assert validate_columns(df, ["A", "C"]) is False

    def test_process_column(self):
        df = pd.DataFrame({"src": ["10,5", "20.0", "abc"]})
        
        # Test with conversion
        process_column(df, "src", "dest", to_float_any, 0.0)
        assert df["dest"].iloc[0] == 10.5
        assert df["dest"].iloc[1] == 20.0
        assert np.isnan(df["dest"].iloc[2])
        
        # Test with missing column and default
        process_column(df, "missing", "dest_missing", None, default="default")
        assert df["dest_missing"].iloc[0] == "default"
