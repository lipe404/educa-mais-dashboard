import sqlite3
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import os
import constants as C


class GeocodingService:
    """
    Service for geocoding addresses and caching results in a SQLite database.
    """

    def __init__(self, db_path=C.GEO_DB_PATH):
        """
        Initialize the GeocodingService.

        Args:
            db_path (str, optional): Path to the SQLite cache database. Defaults to C.GEO_DB_PATH.
        """
        self.db_path = db_path
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
            cursor = conn.execute("SELECT lat, lon FROM cache WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                # If lat/lon are None in DB, it means we tried before and failed (negative cache)
                # But here we store actual None as NULL.
                # If we want to retry failed ones occasionally, we'd check timestamp.
                # For now, simplistic permanent cache.
                return row[0], row[1]

        # Fetch from API
        query = f"{city}, {state}, {C.GEO_COUNTRY}"
        try:
            # Respect rate limit of Nominatim (1 req/sec)
            # We can't easily sync this across processes without a lock file or server,
            # but for a single dashboard instance this is okay.
            time.sleep(1.1)

            loc = self.geolocator.geocode(query, timeout=4)

            lat, lon = None, None
            if loc:
                lat, lon = loc.latitude, loc.longitude

            # Save to cache (even if None, to avoid re-querying invalid cities)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache (key, lat, lon) VALUES (?, ?, ?)",
                    (key, lat, lon),
                )

            return lat, lon

        except (GeocoderTimedOut, GeocoderUnavailable):
            # Don't cache timeout errors, we want to retry them later
            return None, None

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
            cursor = conn.execute("SELECT lat, lon FROM cache WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row[0], row[1]

        # Fetch from API
        # Using structured query for postalcode
        query = {"postalcode": clean_zip, "country": C.GEO_COUNTRY}
        try:
            time.sleep(1.1)
            loc = self.geolocator.geocode(query, timeout=4)

            lat, lon = None, None
            if loc:
                lat, lon = loc.latitude, loc.longitude

            # Save to cache
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache (key, lat, lon) VALUES (?, ?, ?)",
                    (key, lat, lon),
                )

            return lat, lon

        except (GeocoderTimedOut, GeocoderUnavailable):
            return None, None
        except Exception as e:
            print(f"Geocoding error for zip {clean_zip}: {e}")
            return None, None
