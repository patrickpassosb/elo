"""
Unit tests for feedback service.
"""

import pytest
from services.feedback_service import save_feedback, get_sentiment_summary
from storage import feedback_store


@pytest.fixture(autouse=True)
def clear_store():
    """Clear feedback store before each test."""
    feedback_store.clear()
    yield
    feedback_store.clear()


def test_save_feedback_success():
    """Test successful feedback save."""
    user_id = 12345
    bill_id = "PL2024/001"
    sentiment = "concordo"
    
    result = save_feedback(user_id, bill_id, sentiment)
    
    assert result is True


def test_save_feedback_invalid_sentiment():
    """Test that invalid sentiment is rejected."""
    user_id = 12345
    bill_id = "PL2024/001"
    sentiment = "invalid"
    
    result = save_feedback(user_id, bill_id, sentiment)
    
    assert result is False


def test_sentiment_normalization():
    """Test that sentiments are normalized (lowercase, trimmed)."""
    user_id = 12345
    bill_id = "PL2024/001"
    
    result = save_feedback(user_id, bill_id, "  CONCORDO  ")
    
    assert result is True


def test_get_sentiment_summary_empty():
    """Test sentiment summary for bill with no feedback."""
    bill_id = "PL2024/999"
    
    summary = get_sentiment_summary(bill_id)
    
    assert summary["concordo"] == 0
    assert summary["discordo"] == 0
    assert summary["neutro"] == 0
    assert summary["total"] == 0


def test_get_sentiment_summary_single_feedback():
    """Test sentiment summary with one feedback."""
    user_id = 12345
    bill_id = "PL2024/001"
    
    save_feedback(user_id, bill_id, "concordo")
    summary = get_sentiment_summary(bill_id)
    
    assert summary["concordo"] == 1
    assert summary["discordo"] == 0
    assert summary["neutro"] == 0
    assert summary["total"] == 1


def test_get_sentiment_summary_multiple_feedback():
    """Test sentiment summary with multiple users."""
    bill_id = "PL2024/001"
    
    save_feedback(11111, bill_id, "concordo")
    save_feedback(22222, bill_id, "concordo")
    save_feedback(33333, bill_id, "discordo")
    save_feedback(44444, bill_id, "neutro")
    
    summary = get_sentiment_summary(bill_id)
    
    assert summary["concordo"] == 2
    assert summary["discordo"] == 1
    assert summary["neutro"] == 1
    assert summary["total"] == 4


def test_user_can_update_feedback():
    """Test that user can update their feedback on same bill."""
    user_id = 12345
    bill_id = "PL2024/001"
    
    save_feedback(user_id, bill_id, "concordo")
    save_feedback(user_id, bill_id, "discordo")  # Update
    
    summary = get_sentiment_summary(bill_id)
    
    # Should only count the latest feedback
    assert summary["discordo"] == 1
    assert summary["concordo"] == 0
    assert summary["total"] == 1


def test_different_bills_separate_feedback():
    """Test that feedback for different bills is separate."""
    user_id = 12345
    
    save_feedback(user_id, "PL2024/001", "concordo")
    save_feedback(user_id, "PL2024/002", "discordo")
    
    summary1 = get_sentiment_summary("PL2024/001")
    summary2 = get_sentiment_summary("PL2024/002")
    
    assert summary1["concordo"] == 1
    assert summary1["discordo"] == 0
    
    assert summary2["concordo"] == 0
    assert summary2["discordo"] == 1


def test_all_sentiment_types():
    """Test all three sentiment types."""
    bill_id = "PL2024/001"
    
    save_feedback(11111, bill_id, "concordo")
    save_feedback(22222, bill_id, "discordo")
    save_feedback(33333, bill_id, "neutro")
    
    summary = get_sentiment_summary(bill_id)
    
    assert summary["concordo"] == 1
    assert summary["discordo"] == 1
    assert summary["neutro"] == 1
    assert summary["total"] == 3
