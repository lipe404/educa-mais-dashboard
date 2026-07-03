import sqlite3
import time
import random
import logging
from datetime import datetime, timezone
from geopy.geocoders import Nominatim
from geopy.exc import (
    GeocoderTimedOut,
    GeocoderUnavailable,
    GeocoderRateLimited,
    GeocoderServiceError,
)
import os
import constants as C


logger = logging.getLogger(__name__)


class GeocodingService:
    """
    Service for geocoding addresses and caching results in a SQLite database.
    """

    def __init__(self, db_path=C.GEO_DB_PATH, negative_ttl=86400):
        """
        Initialize the GeocodingService.

        Args:
            db_path (str, optional): Path to the SQLite cache database. Defaults to C.GEO_DB_PATH.
            negative_ttl (int, optional): Time-to-live for negative cache entries in seconds. Defaults to 86400 (24 hours).
        """
        self.db_path = db_path
        self.negative_ttl = negative_ttl
        self._init_db()
        self.geolocator = Nominatim(user_agent=C.GEO_USER_AGENT)

    def _init_db(self):
        """
        Initialize the SQLite database and create the cache table if it doesn't exist.
        """
        with sqlite3.connect(self.db_path) as conn:
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
            # Garantir índice na coluna key para performance (embora PK já crie índice implícito,
            # isso garante redundância caso o esquema mude)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON cache (key)")

    def _parse_timestamp(self, val) -> float:
        """
        Parses a timestamp value from the database into a float unix timestamp.
        Supports both datetime string format and numeric epoch timestamp.
        """
        if val is None:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                # SQLite CURRENT_TIMESTAMP is UTC
                dt = datetime.strptime(val_str, fmt).replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except ValueError:
                continue
        try:
            return float(val_str)
        except ValueError:
            return 0.0

    def cleanup_expired_negative_cache(self) -> int:
        """
        Deletes expired negative cache entries from the database.

        Returns:
            int: The number of deleted entries.
        """
        now_epoch = time.time()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT key, timestamp FROM cache WHERE lat IS NULL OR lon IS NULL")
            rows = cursor.fetchall()
            keys_to_delete = []
            for key, ts in rows:
                ts_epoch = self._parse_timestamp(ts)
                if now_epoch - ts_epoch > self.negative_ttl:
                    keys_to_delete.append(key)

            if keys_to_delete:
                conn.executemany("DELETE FROM cache WHERE key = ?", [(k,) for k in keys_to_delete])
                conn.commit()
            return len(keys_to_delete)

    def _geocode_with_retry(self, query, max_retries=3, initial_delay=1.5):
        """
        Helper method to execute geocoding with retry logic and exponential backoff.
        
        Args:
            query (str|dict): The address string or dict query for geocoding.
            max_retries (int): Maximum number of retry attempts.
            initial_delay (float): Initial delay in seconds before request.
            
        Returns:
            Location: The geopy Location object or None if failed.
        """
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                # Add jitter to avoid synchronized retries
                sleep_time = delay + random.uniform(0, 0.5)
                time.sleep(sleep_time)
                
                return self.geolocator.geocode(query, timeout=10)
                
            except (GeocoderTimedOut, GeocoderUnavailable):
                logger.warning(f"Geocoding timeout/unavailable. Attempt {attempt + 1}/{max_retries}.")
            except GeocoderRateLimited:
                logger.warning(f"Geocoding rate limited. Attempt {attempt + 1}/{max_retries}.")
                # Increase delay significantly on rate limit
                delay += 5.0
            except Exception as e:
                logger.error(f"Unexpected geocoding error: {e}")
                # Don't retry on unknown errors unless we want to be very robust
                return None
            
            # Exponential backoff
            delay *= 2
        
        logger.error(f"Failed to geocode '{query}' after {max_retries} attempts.")
        return None

    def get_coords(self, city: str, state: str) -> tuple[float | None, float | None]:
        """
        Get coordinates (latitude, longitude) for a given city and state.

        Checks the local cache first; if not found, queries the Nominatim API.

        Args:
            city (str): The city name.
            state (str): The state name or abbreviation.

        Returns:
            tuple[float | None, float | None]: A tuple containing (latitude, longitude),
                                               or (None, None) if not found.
        """
        if not city or not state:
            return None, None

        key = f"{city.strip().lower()}|{state.strip().lower()}"

        # Check cache
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT lat, lon, timestamp FROM cache WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                lat = row[0]
                lon = row[1]
                ts = row[2] if len(row) >= 3 else None
                if lat is None or lon is None:
                    ts_epoch = self._parse_timestamp(ts)
                    if time.time() - ts_epoch > self.negative_ttl:
                        # Expired negative cache, proceed to fetch from API
                        pass
                    else:
                        # Still valid negative cache
                        return None, None
                else:
                    # Positive cache (never expires)
                    return lat, lon

        # Fetch from API
        query = f"{city}, {state}, {C.GEO_COUNTRY}"
        
        loc = self._geocode_with_retry(query)

        lat, lon = None, None
        if loc:
            lat, lon = loc.latitude, loc.longitude

        # Save to cache (even if None, to avoid re-querying invalid cities)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache (key, lat, lon, timestamp) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                    (key, lat, lon),
                )
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")

        return lat, lon

    def get_coords_by_zip(self, zip_code: str) -> tuple[float | None, float | None]:
        """
        Get coordinates (latitude, longitude) for a given zip code.

        Checks the local cache first; if not found, queries the Nominatim API.

        Args:
            zip_code (str): The zip code string.

        Returns:
            tuple[float | None, float | None]: A tuple containing (latitude, longitude),
                                               or (None, None) if not found.
        """
        if not zip_code:
            return None, None

        # Clean zip code (keep only numbers)
        clean_zip = "".join(filter(str.isdigit, str(zip_code)))
        if not clean_zip:
            return None, None

        key = f"zip|{clean_zip}"

        # Check cache
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT lat, lon, timestamp FROM cache WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                lat = row[0]
                lon = row[1]
                ts = row[2] if len(row) >= 3 else None
                if lat is None or lon is None:
                    ts_epoch = self._parse_timestamp(ts)
                    if time.time() - ts_epoch > self.negative_ttl:
                        # Expired negative cache, proceed to fetch from API
                        pass
                    else:
                        # Still valid negative cache
                        return None, None
                else:
                    # Positive cache (never expires)
                    return lat, lon

        # Fetch from API
        # Using structured query for postalcode
        query = {"postalcode": clean_zip, "country": C.GEO_COUNTRY}
        
        loc = self._geocode_with_retry(query)

        lat, lon = None, None
        if loc:
            lat, lon = loc.latitude, loc.longitude

        # Save to cache
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache (key, lat, lon, timestamp) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                    (key, lat, lon),
                )
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")

        return lat, lon
