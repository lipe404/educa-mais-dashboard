import os
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
import pytest

from geocoding_service import GeocodingService


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_geocache.db"
    return str(db_file)


def test_cache_hit_positive(temp_db):
    # Setup database with positive cache entry
    # (lat, lon) are set and valid
    with sqlite3.connect(temp_db) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                lat REAL,
                lon REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.execute(
            "INSERT INTO cache (key, lat, lon, timestamp) VALUES (?, ?, ?, ?)",
            ("recife|pe", -8.0539, -34.8811, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
        )
    
    # Initialize service with negative_ttl = 10s
    service = GeocodingService(db_path=temp_db, negative_ttl=10)
    
    # Mock the geolocator to verify it is NOT called
    service.geolocator = MagicMock()
    
    # Execute get_coords
    lat, lon = service.get_coords("recife", "pe")
    
    assert lat == -8.0539
    assert lon == -34.8811
    service.geolocator.geocode.assert_not_called()


def test_negative_cache_still_valid(temp_db):
    # Setup database with a fresh negative cache entry
    # (lat, lon) are None
    with sqlite3.connect(temp_db) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                lat REAL,
                lon REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        # 2 seconds ago (still valid since negative_ttl=10s)
        recent_ts = (datetime.now(timezone.utc) - timedelta(seconds=2)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO cache (key, lat, lon, timestamp) VALUES (?, ?, ?, ?)",
            ("invalidcity|xx", None, None, recent_ts)
        )
        
    service = GeocodingService(db_path=temp_db, negative_ttl=10)
    service.geolocator = MagicMock()
    
    lat, lon = service.get_coords("invalidcity", "xx")
    
    assert lat is None
    assert lon is None
    service.geolocator.geocode.assert_not_called()


def test_negative_cache_expired(temp_db):
    # Setup database with an expired negative cache entry
    with sqlite3.connect(temp_db) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                lat REAL,
                lon REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        # 12 seconds ago (expired since negative_ttl=10s)
        old_ts = (datetime.now(timezone.utc) - timedelta(seconds=12)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO cache (key, lat, lon, timestamp) VALUES (?, ?, ?, ?)",
            ("invalidcity|xx", None, None, old_ts)
        )
        
    service = GeocodingService(db_path=temp_db, negative_ttl=10)
    
    # Mock geolocator to return coordinates this time
    mock_location = MagicMock()
    mock_location.latitude = -5.1234
    mock_location.longitude = -15.5678
    service.geolocator.geocode = MagicMock(return_value=mock_location)
    
    lat, lon = service.get_coords("invalidcity", "xx")
    
    # It should have called the API and returned new coordinates
    assert lat == -5.1234
    assert lon == -15.5678
    service.geolocator.geocode.assert_called_once()
    
    # Check that cache is updated to positive cache (or new coordinates)
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.execute("SELECT lat, lon FROM cache WHERE key = ?", ("invalidcity|xx",))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == -5.1234
        assert row[1] == -15.5678


def test_cleanup_expired_negative_cache(temp_db):
    # Setup database with positive, valid negative, and expired negative cache entries
    with sqlite3.connect(temp_db) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                lat REAL,
                lon REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        # 1. Positive cache (lat/lon not null, never expires)
        old_positive_ts = (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO cache (key, lat, lon, timestamp) VALUES (?, ?, ?, ?)",
            ("pos|ok", -10.0, -20.0, old_positive_ts)
        )
        # 2. Fresh negative cache (lat/lon null, timestamp recent)
        fresh_negative_ts = (datetime.now(timezone.utc) - timedelta(seconds=2)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO cache (key, lat, lon, timestamp) VALUES (?, ?, ?, ?)",
            ("neg|fresh", None, None, fresh_negative_ts)
        )
        # 3. Expired negative cache (lat/lon null, timestamp old)
        expired_negative_ts = (datetime.now(timezone.utc) - timedelta(seconds=15)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO cache (key, lat, lon, timestamp) VALUES (?, ?, ?, ?)",
            ("neg|expired", None, None, expired_negative_ts)
        )
        
    service = GeocodingService(db_path=temp_db, negative_ttl=10)
    
    # Run cleanup
    deleted_count = service.cleanup_expired_negative_cache()
    
    assert deleted_count == 1
    
    # Verify remaining records
    with sqlite3.connect(temp_db) as conn:
        cursor = conn.execute("SELECT key FROM cache ORDER BY key")
        keys = [row[0] for row in cursor.fetchall()]
        assert "pos|ok" in keys
        assert "neg|fresh" in keys
        assert "neg|expired" not in keys
