import time
import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)


class TTLCache:
    """Simple in-process TTL cache."""

    def __init__(self, ttl: int = 3600):
        self._store: dict[str, tuple[Any, float]] = {}
        self.ttl = ttl

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl = ttl or self.ttl
        self._store[key] = (value, time.time() + ttl)
        logger.debug("Cache SET key=%s ttl=%ds", key, ttl)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)


def file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


document_cache = TTLCache(ttl=3600)
