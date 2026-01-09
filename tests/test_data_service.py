import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from io import StringIO
import constants as C
from services import data as data_service

class TestDataService:
    # --- Helper Function Tests ---
    
    def test_parse_datetime_any_valid(self):
        assert data_service.parse_datetime_any("2023-01-01") == pd.Timestamp("2023-01-01")
        assert data_service.parse_datetime_any("01/01/2023") == pd.Timestamp("2023-01-01")
        assert data_service.parse_datetime_any("2023-01-01 12:00:00") == pd.Timestamp("2023-01-01 12:00:00")

    def test_parse_datetime_any_invalid(self):
        assert data_service.parse_datetime_any("invalid-date") is None
        assert data_service.parse_datetime_any(None) is None
        assert data_service.parse_datetime_any(np.nan) is None

    def test_to_float_any_valid(self):
        assert data_service.to_float_any("100.50") == 100.50
        assert data_service.to_float_any("100,50") == 100.50
        assert data_service.to_float_any(100) == 100.0

    def test_to_float_any_invalid(self):
        assert np.isnan(data_service.to_float_any("abc"))
        assert np.isnan(data_service.to_float_any(None))

    def test_validate_columns_success(self):
        df = pd.DataFrame({"A": [1], "B": [2]})
        assert data_service.validate_columns(df, ["A", "B"]) is True

    @patch("streamlit.error")
    def test_validate_columns_failure(self, mock_st_error):
        df = pd.DataFrame({"A": [1]})
        assert data_service.validate_columns(df, ["A", "B"]) is False
        mock_st_error.assert_called_once()

    def test_process_column_existing(self):
        df = pd.DataFrame({"src": [1, 2]})
        data_service.process_column(df, "src", "dest", lambda x: x * 2)
        assert "dest" in df.columns
        assert df["dest"].tolist() == [2, 4]

    def test_process_column_missing_default(self):
        df = pd.DataFrame({"other": [1]})
        data_service.process_column(df, "src", "dest", default=0)
        assert "dest" in df.columns
        assert df["dest"].tolist() == [0]

    # --- Data Loading Tests ---

    @patch("services.data.requests.get")
    def test_load_sheet_success(self, mock_get):
        csv_content = "col1,col2\nval1,val2"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = csv_content
        mock_get.return_value = mock_response

        df = data_service.load_sheet("dummy_id", "dummy_sheet")
        assert not df.empty
        assert len(df) == 1
        assert df.iloc[0]["col1"] == "val1"

    @patch("services.data.requests.get")
    def test_load_sheet_failure(self, mock_get):
        mock_get.side_effect = Exception("Network Error")
        
        # We also need to patch st.error since load_sheet calls it
        with patch("streamlit.error") as mock_st_error:
            df = data_service.load_sheet("dummy_id_fail", "dummy_sheet_fail")
            assert df.empty
            mock_st_error.assert_called()

    @patch("services.data.load_sheet")
    def test_get_dados_processing(self, mock_load_sheet):
        # Create a sample raw dataframe mimicking Google Sheets output
        # Ensure Partner Name is the first key/column
        raw_data = {
            "Partner Name": ["Partner A"], # 1st column
            C.COL_SRC_TIMESTAMP: ["01/01/2023"],
            C.COL_SRC_STATUS: [" Assinado "],
            C.COL_SRC_CAPTADOR: [" João "],
            C.COL_SRC_STATE: [" sp "],
            C.COL_SRC_CITY: [" São Paulo "],
        }
        mock_df = pd.DataFrame(raw_data)
        # Ensure column order matches insertion order (for safe iloc usage in test)
        cols = ["Partner Name", C.COL_SRC_TIMESTAMP, C.COL_SRC_STATUS, C.COL_SRC_CAPTADOR, C.COL_SRC_STATE, C.COL_SRC_CITY]
        mock_df = mock_df[cols]
        
        mock_load_sheet.return_value = mock_df

        df = data_service.get_dados("dummy_id")
        
        assert not df.empty
        assert df.iloc[0][C.COL_INT_STATUS] == "ASSINADO"
        assert df.iloc[0][C.COL_INT_STATE] == "SP"
        assert df.iloc[0][C.COL_INT_CITY] == "São Paulo"
        assert df.iloc[0][C.COL_INT_PARTNER] == "Partner A"
        assert C.COL_INT_REGION in df.columns # Check region mapping

    @patch("services.data.load_sheet")
    def test_get_faturamento_processing(self, mock_load_sheet):
        raw_data = {
            "Partner Name": ["Partner A"], # 1st column
            C.COL_SRC_VALOR: ["1000,50"],
            C.COL_SRC_COMISSAO: ["10,0"], # 10%
            C.COL_SRC_DATA: ["01/01/2023"],
        }
        mock_df = pd.DataFrame(raw_data)
        cols = ["Partner Name", C.COL_SRC_VALOR, C.COL_SRC_COMISSAO, C.COL_SRC_DATA]
        mock_df = mock_df[cols]
        
        mock_load_sheet.return_value = mock_df

        df = data_service.get_faturamento("dummy_id")
        
        assert not df.empty
        assert df.iloc[0][C.COL_INT_VALOR] == 1000.50
        assert df.iloc[0][C.COL_INT_COMISSAO] == 0.10
