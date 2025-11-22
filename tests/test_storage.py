import time
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from src.storage import _BaseStore, SessionStore, PreferenceStore

class TestBaseStore:
    def test_set_get(self):
        store = _BaseStore()
        store.set("key", "value")
        assert store.get("key") == "value"

    def test_default_factory(self):
        store = _BaseStore()
        val = store.get("key", default_factory=list)
        assert val == []
        assert store.get("key") == []

    def test_ttl_expiration(self):
        # Mock datetime to control time
        with patch("src.storage.datetime") as mock_datetime:
            # Start time
            start_time = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = start_time
            
            store = _BaseStore(ttl_hours=1)
            store.set("key", "value")
            assert store.get("key") == "value"
            
            # Advance time by 2 hours
            mock_datetime.utcnow.return_value = start_time + timedelta(hours=2)
            assert store.get("key") is None

    def test_max_size_eviction(self):
        store = _BaseStore(max_size=2)
        store.set("k1", "v1")
        store.set("k2", "v2")
        store.set("k3", "v3")  # Should evict k1
        
        assert store.get("k1") is None
        assert store.get("k2") == "v2"
        assert store.get("k3") == "v3"

    def test_lru_behavior(self):
        store = _BaseStore(max_size=2)
        store.set("k1", "v1")
        store.set("k2", "v2")
        
        # Access k1 to make it recently used
        store.get("k1")
        
        store.set("k3", "v3")  # Should evict k2 (least recently used)
        
        assert store.get("k1") == "v1"
        assert store.get("k2") is None
        assert store.get("k3") == "v3"

def test_session_store():
    store = SessionStore()
    from langchain_community.chat_message_histories import ChatMessageHistory
    history = store.get_history("session1")
    assert isinstance(history, ChatMessageHistory)
    # Check persistence
    history.add_user_message("hi")
    history2 = store.get_history("session1")
    assert len(history2.messages) == 1

def test_preference_store():
    store = PreferenceStore()
    store.set("user1", "audio")
    assert store.get("user1") == "audio"
