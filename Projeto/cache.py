"""Small process-local cache with bounded lifetime and size."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable, Hashable
from threading import RLock
from time import monotonic
from typing import Generic, TypeVar

MAX_TTL_SECONDS = 300.0

Key = TypeVar("Key", bound=Hashable)
Value = TypeVar("Value")


class MemoryTTLCache(Generic[Key, Value]):
    def __init__(
        self,
        *,
        max_entries: int,
        ttl_seconds: float = MAX_TTL_SECONDS,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be positive.")
        if not 0 < ttl_seconds <= MAX_TTL_SECONDS:
            raise ValueError(
                f"ttl_seconds must be between 0 and {MAX_TTL_SECONDS}."
            )
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._entries: OrderedDict[Key, tuple[float, Value]] = OrderedDict()
        self._lock = RLock()

    def get(self, key: Key) -> Value | None:
        now = self._clock()
        with self._lock:
            self._purge_expired(now)
            entry = self._entries.get(key)
            if entry is None:
                return None
            _, value = entry
            self._entries.move_to_end(key)
            return value

    def set(self, key: Key, value: Value) -> None:
        now = self._clock()
        with self._lock:
            self._purge_expired(now)
            self._entries[key] = (now + self._ttl_seconds, value)
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        now = self._clock()
        with self._lock:
            self._purge_expired(now)
            return len(self._entries)

    def _purge_expired(self, now: float) -> None:
        expired = [
            key
            for key, (expires_at, _) in self._entries.items()
            if expires_at <= now
        ]
        for key in expired:
            del self._entries[key]
