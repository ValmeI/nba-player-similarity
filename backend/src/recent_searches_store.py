import json
import os
import tempfile
import threading
from datetime import datetime, timedelta
from datetime import timezone as _tz

from shared.config import settings
from shared.utils.app_logger import logger

MAX_ENTRIES = 5000


class RecentSearchesStore:
    def __init__(self, file_path: str, ttl_days: int):
        self.file_path = file_path
        self.ttl_days = ttl_days
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def _read(self) -> list[dict]:
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, ValueError):
            logger.warning(f"Corrupt recent searches file at {self.file_path}, resetting.")
            return []

    def _write(self, entries: list[dict]) -> None:
        dir_name = os.path.dirname(self.file_path)
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(entries, f, indent=2)
            os.replace(tmp_path, self.file_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def _purge_expired(self, entries: list[dict]) -> list[dict]:
        cutoff = datetime.now(_tz.utc) - timedelta(days=self.ttl_days)
        result = []
        for e in entries:
            try:
                if datetime.fromisoformat(e["searched_at"]) >= cutoff:
                    result.append(e)
            except (ValueError, KeyError):
                continue
        return result

    def record_search(
        self,
        player_name: str,
        position: str | None = None,
        era: str | None = None,
        original_query: str | None = None,
        search_source: str | None = None,
        results_found: bool | None = None,
        client_ip: str | None = None,
        country: str | None = None,
        region: str | None = None,
        city: str | None = None,
        timezone: str | None = None,
    ) -> None:
        try:
            with self._lock:
                entries = self._read()
                entries = self._purge_expired(entries)

                now = datetime.now(_tz.utc).isoformat()

                entries.append({
                    "player_name": player_name.title(),
                    "position": position,
                    "era": era,
                    "searched_at": now,
                    "original_query": original_query,
                    "search_source": search_source,
                    "results_found": results_found,
                    "client_ip": client_ip,
                    "country": country,
                    "region": region,
                    "city": city,
                    "timezone": timezone,
                })

                # Cap at MAX_ENTRIES (keep most recent)
                entries.sort(key=lambda e: e["searched_at"], reverse=True)
                entries = entries[:MAX_ENTRIES]

                self._write(entries)
        except Exception as e:
            logger.error(f"Failed to record recent search: {e}")

    def get_recent_searches(self, limit: int) -> list[dict]:
        try:
            entries = self._read()
            entries = self._purge_expired(entries)
            entries.sort(key=lambda e: e["searched_at"], reverse=True)
            return entries[:limit]
        except Exception as e:
            logger.error(f"Failed to read recent searches: {e}")
            return []


recent_searches_store = RecentSearchesStore(
    file_path=settings.RECENT_SEARCHES_FILE_PATH,
    ttl_days=settings.RECENT_SEARCHES_TTL_DAYS,
)
