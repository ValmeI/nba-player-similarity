import json
import os
import tempfile
import threading
from datetime import datetime, timedelta, timezone

from shared.config import settings
from shared.utils.app_logger import logger

MAX_ENTRIES = 200


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
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.ttl_days)
        result = []
        for e in entries:
            try:
                if datetime.fromisoformat(e["searched_at"]) >= cutoff:
                    result.append(e)
            except (ValueError, KeyError):
                continue
        return result

    def record_search(self, player_name: str, position: str | None = None, era: str | None = None) -> None:
        try:
            with self._lock:
                entries = self._read()
                entries = self._purge_expired(entries)

                now = datetime.now(timezone.utc).isoformat()
                normalized_name = player_name.title()
                key = (normalized_name, position, era)

                # Dedup: update timestamp if same search exists
                for entry in entries:
                    if (entry["player_name"], entry.get("position"), entry.get("era")) == key:
                        entry["searched_at"] = now
                        break
                else:
                    entries.append({
                        "player_name": normalized_name,
                        "position": position,
                        "era": era,
                        "searched_at": now,
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
