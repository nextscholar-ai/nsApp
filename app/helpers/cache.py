import threading
import time
from collections.abc import Callable
from typing import Any


class TTLCache:
    def __init__(self, default_ttl: float = 60.0) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._default_ttl = default_ttl
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expiry = entry
            if time.monotonic() > expiry:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        expiry = time.monotonic() + (ttl if ttl is not None else self._default_ttl)
        with self._lock:
            self._store[key] = (value, expiry)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def cached(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: float | None = None,
    ) -> Any:
        existing = self.get(key)
        if existing is not None:
            return existing
        value = factory()
        self.set(key, value, ttl)
        return value


search_cache = TTLCache(default_ttl=60.0)
