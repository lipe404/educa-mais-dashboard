import sqlite3
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import os
import constants as C


class GeocodingService:
    def __init__(self, db_path=C.GEO_DB_PATH):
        self.db_path = db_path
        self._init_db()
        self.geolocator = Nominatim(user_agent=C.GEO_USER_AGENT)

    def _init_db(self):
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
        except Exception as e:
            print(f"Geocoding error for {query}: {e}")
            return None, None
