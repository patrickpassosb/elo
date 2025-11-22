# storage.py
"""
Utility classes for in‑memory session and preference storage with TTL and size limits.
These replace the unbounded dictionaries used previously.
"""

import threading
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any


class _BaseStore:
    """Thread‑safe base store with TTL and LRU eviction."""

    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self._store: OrderedDict[str, Any] = OrderedDict()
        self._timestamps: dict[str, datetime] = {}
        self._lock = threading.RLock()

    def _cleanup(self) -> None:
        """Remove expired entries and enforce size limit."""
        now = datetime.utcnow()
        # Remove expired
        expired_keys = [k for k, ts in self._timestamps.items() if now - ts > self.ttl]
        for k in expired_keys:
            self._store.pop(k, None)
            self._timestamps.pop(k, None)
        # Enforce max size (LRU eviction)
        while len(self._store) > self.max_size:
            oldest_key, _ = self._store.popitem(last=False)
            self._timestamps.pop(oldest_key, None)

    def get(self, key: str, default_factory=None) -> Any:
        with self._lock:
            self._cleanup()
            if key in self._store:
                # Update LRU order
                self._store.move_to_end(key)
                self._timestamps[key] = datetime.utcnow()
                return self._store[key]
            else:
                if default_factory is not None:
                    value = default_factory()
                    self.set(key, value)
                    return value
                return None

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._cleanup()
            self._store[key] = value
            self._store.move_to_end(key)
            self._timestamps[key] = datetime.utcnow()

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)
            self._timestamps.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._timestamps.clear()


class SessionStore(_BaseStore):
    """Store for LangChain `ChatMessageHistory` objects."""

    def get_history(self, session_id: str):
        from langchain_community.chat_message_histories import ChatMessageHistory
        return self.get(session_id, default_factory=ChatMessageHistory)


class PreferenceStore(_BaseStore):
    """Generic key/value store for user preferences or other data."""
    pass

# Global instances (imported where needed)
session_store = SessionStore()
preference_store = PreferenceStore()

__all__ = ["session_store", "preference_store", "SessionStore", "PreferenceStore"]
