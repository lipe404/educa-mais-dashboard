import pytest
import pandas as pd
import os
from unittest.mock import patch, MagicMock
import constants as C
from geocoding_service import GeocodingService
from services import data as data_service

class TestIntegration:
    @patch("services.data.requests.get")
    @patch("geocoding_service.sqlite3")
    def test_data_load_and_geocode_flow(self, mock_sqlite, mock_get):
        # 1. Mock Data Loading from Google Sheets
        csv_content = f"{C.COL_SRC_TIMESTAMP},{C.COL_SRC_CITY},{C.COL_SRC_STATE}\n01/01/2023,TestCity,SP"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = csv_content
        mock_get.return_value = mock_response

        # 2. Load Data
        df = data_service.get_dados("dummy_id_integration")
        
        assert not df.empty
        assert len(df) == 1
        city = df.iloc[0][C.COL_INT_CITY]
        state = df.iloc[0][C.COL_INT_STATE]
        
        assert city == "TestCity"
        assert state == "SP"

        # 3. Mock Geocoding Database Logic
        # Mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Correctly mock the context manager for sqlite3.connect
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.__enter__.return_value = mock_conn
        
        # Correctly mock conn.execute (used directly in service)
        mock_conn.execute.return_value = mock_cursor
        
        mock_cursor.fetchone.return_value = None # Simulate Cache Miss

        with patch("geopy.geocoders.Nominatim.geocode") as mock_nominatim:
            # Mock Nominatim response
            mock_location = MagicMock()
            mock_location.latitude = -23.55
            mock_location.longitude = -46.63
            mock_nominatim.return_value = mock_location
            
            # 4. Initialize Service and Geocode
            geo_service = GeocodingService()
            lat, lon = geo_service.get_coords(city, state)
            
            # 5. Verify Results
            assert lat == -23.55
            assert lon == -46.63
            
            # Verify Nominatim was called
            mock_nominatim.assert_called()
            
            # Verify DB insert was attempted (Cache update)
            # We look for an INSERT statement in execute calls
            found_insert = False
            for call in mock_conn.execute.call_args_list:
                args = call[0]
                if "INSERT OR REPLACE INTO cache" in args[0]:
                    found_insert = True
                    break
            
            assert found_insert, "Should have attempted to cache the result"

    def test_geocoding_cache_hit(self):
        # Test that if DB returns data, we don't call Nominatim
        with patch("geocoding_service.sqlite3") as mock_sqlite:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            
            mock_sqlite.connect.return_value = mock_conn
            mock_conn.__enter__.return_value = mock_conn
            mock_conn.execute.return_value = mock_cursor
            
            # Simulate Cache Hit
            mock_cursor.fetchone.return_value = (-10.0, -20.0) # lat, lon
            
            with patch("geopy.geocoders.Nominatim.geocode") as mock_nominatim:
                geo_service = GeocodingService()
                lat, lon = geo_service.get_coords("CachedCity", "SP")
                
                assert lat == -10.0
                assert lon == -20.0
                
                # Verify Nominatim was NOT called
                mock_nominatim.assert_not_called()
