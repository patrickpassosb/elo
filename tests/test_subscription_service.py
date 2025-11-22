"""
Unit tests for subscription service.
"""

import pytest
from services.subscription_service import subscribe_topic, unsubscribe_topic, get_subscriptions
from storage import subscription_store


@pytest.fixture(autouse=True)
def clear_store():
    """Clear subscription store before each test."""
    subscription_store.clear()
    yield
    subscription_store.clear()


def test_subscribe_topic_success():
    """Test successful topic subscription."""
    user_id = 12345
    topic = "educação"
    
    result = subscribe_topic(user_id, topic)
    
    assert result is True
    subscriptions = get_subscriptions(user_id)
    assert "educação" in subscriptions


def test_subscribe_multiple_topics():
    """Test subscribing to multiple topics."""
    user_id = 12345
    
    subscribe_topic(user_id, "educação")
    subscribe_topic(user_id, "saúde")
    subscribe_topic(user_id, "meio ambiente")
    
    subscriptions = get_subscriptions(user_id)
    assert len(subscriptions) == 3
    assert "educação" in subscriptions
    assert "saúde" in subscriptions
    assert "meio ambiente" in subscriptions


def test_subscribe_duplicate_topic():
    """Test that duplicate subscriptions are handled correctly."""
    user_id = 12345
    topic = "educação"
    
    subscribe_topic(user_id, topic)
    subscribe_topic(user_id, topic)  # Duplicate
    
    subscriptions = get_subscriptions(user_id)
    assert len(subscriptions) == 1
    assert subscriptions.count("educação") == 1


def test_topic_normalization():
    """Test that topics are normalized (lowercase, trimmed)."""
    user_id = 12345
    
    subscribe_topic(user_id, "  EDUCAÇÃO  ")
    
    subscriptions = get_subscriptions(user_id)
    assert "educação" in subscriptions


def test_unsubscribe_topic_success():
    """Test successful topic unsubscription."""
    user_id = 12345
    topic = "educação"
    
    subscribe_topic(user_id, topic)
    result = unsubscribe_topic(user_id, topic)
    
    assert result is True
    subscriptions = get_subscriptions(user_id)
    assert topic not in subscriptions


def test_unsubscribe_nonexistent_topic():
    """Test unsubscribing from a topic user is not subscribed to."""
    user_id = 12345
    
    result = unsubscribe_topic(user_id, "educação")
    
    assert result is False


def test_get_subscriptions_empty():
    """Test getting subscriptions for user with no subscriptions."""
    user_id = 12345
    
    subscriptions = get_subscriptions(user_id)
    
    assert subscriptions == []


def test_multiple_users():
    """Test that different users have separate subscriptions."""
    user1 = 11111
    user2 = 22222
    
    subscribe_topic(user1, "educação")
    subscribe_topic(user2, "saúde")
    
    subs1 = get_subscriptions(user1)
    subs2 = get_subscriptions(user2)
    
    assert "educação" in subs1
    assert "educação" not in subs2
    assert "saúde" in subs2
    assert "saúde" not in subs1
