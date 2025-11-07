"""Sistema sencillo de caché en disco y en memoria."""

from __future__ import annotations

import functools
import hashlib
import pickle
import time
from pathlib import Path
from typing import Any, Callable, Optional


class DiskCache:
    """Caché en disco con expiración basada en tiempo."""

    def __init__(self, directory: Path = Path(".cache"), ttl: int = 60 * 60) -> None:
        self.directory = directory
        self.ttl = ttl
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path_for_key(self, key: str) -> Path:
        hashed = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.directory / f"{hashed}.pkl"

    def get(self, key: str) -> Optional[Any]:
        path = self._path_for_key(key)
        if not path.exists():
            return None

        with path.open("rb") as fh:
            payload = pickle.load(fh)

        timestamp = payload.get("timestamp", 0)
        if self.ttl and time.time() - timestamp > self.ttl:
            path.unlink(missing_ok=True)
            return None

        return payload.get("value")

    def set(self, key: str, value: Any) -> None:
        path = self._path_for_key(key)
        with path.open("wb") as fh:
            pickle.dump({"timestamp": time.time(), "value": value}, fh)

    def invalidate(self, key: Optional[str] = None) -> None:
        if key is None:
            for file in self.directory.glob("*.pkl"):
                file.unlink(missing_ok=True)
        else:
            self._path_for_key(key).unlink(missing_ok=True)


def cache(ttl: int = 0) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorador simple para cachear funciones en memoria (LRU)."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        cached_func = functools.lru_cache(maxsize=None)(func)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return cached_func(*args, **tuple(sorted(kwargs.items())))

        wrapper.cache_clear = cached_func.cache_clear  # type: ignore[attr-defined]
        return wrapper

    return decorator


