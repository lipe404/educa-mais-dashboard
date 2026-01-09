
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import constants as C
from services import data as data_service

class TestDataServiceExpanded:
    # --- Helper Function Edge Cases ---

    def test_parse_datetime_any_edge_cases(self):
        # Mixed formats
        assert data_service.parse_datetime_any("2023/01/01") == pd.Timestamp("2023-01-01")
        assert data_service.parse_datetime_any("01-01-2023") == pd.Timestamp("2023-01-01")
        
        # Non-string inputs that are convertible
        assert data_service.parse_datetime_any(20230101) is not None # parser might handle this or fail depending on implementation details, but let's check basic robustness
        
        # Empty strings
        assert data_service.parse_datetime_any("") is None
        assert data_service.parse_datetime_any("   ") is None

    def test_to_float_any_edge_cases(self):
        # Brazilian currency format with dots for thousands (if logic supports it? code says replace , with .)
        # Code: float(str(x).replace(",", ".")) -> "1.000,00" -> "1.000.00" -> Error?
        # Usually simple replacement isn't enough for thousands separators.
        # Let's test what the current implementation actually does.
        
        assert data_service.to_float_any("1234") == 1234.0
        assert data_service.to_float_any("1234,56") == 1234.56
        assert data_service.to_float_any("  1234,56  ") == 1234.56
        
        # Check invalid inputs
        assert np.isnan(data_service.to_float_any("abc"))
        assert np.isnan(data_service.to_float_any([]))
        
    def test_process_column_with_exception(self):
        df = pd.DataFrame({"src": ["a", "b"]})
        
        def faulty_func(x):
            raise ValueError("Error")
            
        # If func raises exception, apply might fail.
        # The current implementation does: df[dest] = df[src].apply(func)
        # If apply fails, it propagates the exception.
        # Let's verify this behavior or if we need to wrap it.
        with pytest.raises(ValueError):
             data_service.process_column(df, "src", "dest", faulty_func)

    # --- get_dados Logic Tests ---

    @patch("services.data.load_sheet")
    def test_get_dados_missing_optional_cols(self, mock_load_sheet):
        # Setup minimal dataframe
        raw_data = {
            "Partner Name": ["Partner A"],
            C.COL_SRC_TIMESTAMP: ["01/01/2023"],
            C.COL_SRC_STATUS: ["Assinado"],
            C.COL_SRC_STATE: ["SP"],
            # Missing CITY, CEP, CAPTADOR etc.
        }
        mock_df = pd.DataFrame(raw_data)
        mock_load_sheet.return_value = mock_df

        # Use unique ID to bypass cache
        df = data_service.get_dados("dummy_id_missing_cols")
        
        # Check if missing columns were created with defaults
        assert C.COL_INT_CITY in df.columns
        assert df.iloc[0][C.COL_INT_CITY] == ""
        assert C.COL_INT_CEP in df.columns
        assert df.iloc[0][C.COL_INT_CEP] == ""

    @patch("services.data.load_sheet")
    def test_get_dados_region_mapping(self, mock_load_sheet):
        raw_data = {
            "Partner Name": ["P1", "P2", "P3"],
            C.COL_SRC_STATE: ["SP", "BA", "XX"], # SP=Sudeste, BA=Nordeste, XX=Unknown
            C.COL_SRC_TIMESTAMP: ["01/01/2023"] * 3
        }
        mock_df = pd.DataFrame(raw_data)
        mock_load_sheet.return_value = mock_df

        df = data_service.get_dados("dummy_id_region")
        
        assert df.iloc[0][C.COL_INT_REGION] == "Sudeste" # Assuming mapping exists in constants
        assert df.iloc[1][C.COL_INT_REGION] == "Nordeste"
        assert df.iloc[2][C.COL_INT_REGION] == C.DEFAULT_REGION_OTHER

    @patch("services.data.load_sheet")
    def test_get_dados_empty_sheet(self, mock_load_sheet):
        mock_load_sheet.return_value = pd.DataFrame()
        df = data_service.get_dados("dummy_id_empty")
        assert df.empty

    # --- get_faturamento Logic Tests ---

    @patch("services.data.load_sheet")
    def test_get_faturamento_malformed_values(self, mock_load_sheet):
        raw_data = {
            "Partner Name": ["P1", "P2"],
            C.COL_SRC_VALOR: ["1000,00", "invalid"],
            C.COL_SRC_COMISSAO: ["10,0", "nan"],
            C.COL_SRC_DATA: ["01/01/2023", "invalid-date"]
        }
        mock_df = pd.DataFrame(raw_data)
        mock_load_sheet.return_value = mock_df

        df = data_service.get_faturamento("dummy_id_malformed")
        
        # Check Value parsing
        assert df.iloc[0][C.COL_INT_VALOR] == 1000.0
        assert np.isnan(df.iloc[1][C.COL_INT_VALOR])
        
        # Check Date parsing
        assert df.iloc[0][C.COL_INT_DATA] == pd.Timestamp("2023-01-01")
        assert pd.isna(df.iloc[1][C.COL_INT_DATA])
