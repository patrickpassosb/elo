"""
Feedback service for collecting and aggregating user sentiment on bills.

This service allows users to provide feedback (concordo/discordo/neutro) on
legislative bills and provides aggregated sentiment summaries.

TODO: Phase 1 Integration
- Optionally persist feedback to external database
- Add analytics and reporting features
"""

from typing import Dict, Optional
from collections import Counter
from storage import feedback_store
from logging_config import logger


VALID_SENTIMENTS = {"concordo", "discordo", "neutro"}


def save_feedback(user_id: int, bill_id: str, sentiment: str) -> bool:
    """
    Save user feedback on a bill.
    
    Args:
        user_id: Telegram user ID
        bill_id: Bill identifier (e.g., "PL2024/001")
        sentiment: User sentiment - "concordo", "discordo", or "neutro"
        
    Returns:
        True if feedback saved successfully, False otherwise
    """
    try:
        sentiment_normalized = sentiment.lower().strip()
        
        if sentiment_normalized not in VALID_SENTIMENTS:
            logger.warning(f"Invalid sentiment: {sentiment_normalized}")
            return False
        
        # Store feedback with composite key
        feedback_key = f"{bill_id}:{user_id}"
        feedback_store.set(feedback_key, sentiment_normalized)
        
        logger.info(f"💬 User {user_id} feedback on {bill_id}: {sentiment_normalized}")
        
        # TODO: Phase 1 Integration
        # - Optionally send to external analytics service
        # - Example: analytics_client.track_feedback(user_id, bill_id, sentiment)
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving feedback for user {user_id} on {bill_id}: {e}", exc_info=True)
        return False


def get_sentiment_summary(bill_id: str) -> Dict[str, int]:
    """
    Get aggregated sentiment summary for a bill.
    
    Args:
        bill_id: Bill identifier
        
    Returns:
        Dictionary with sentiment counts, e.g.:
        {"concordo": 10, "discordo": 3, "neutro": 2, "total": 15}
    """
    try:
        # Get all feedback entries for this bill
        # Note: This is a simple implementation. For production, consider
        # using a more efficient data structure or external database.
        
        sentiments = []
        
        # Scan all feedback entries (inefficient but works for MVP)
        # In production, use indexed queries or separate aggregation store
        all_keys = _get_all_feedback_keys()
        
        for key in all_keys:
            if key.startswith(f"{bill_id}:"):
                sentiment = feedback_store.get(key)
                if sentiment:
                    sentiments.append(sentiment)
        
        # Count sentiments
        counts = Counter(sentiments)
        
        summary = {
            "concordo": counts.get("concordo", 0),
            "discordo": counts.get("discordo", 0),
            "neutro": counts.get("neutro", 0),
            "total": len(sentiments),
        }
        
        logger.info(f"📊 Sentiment summary for {bill_id}: {summary}")
        return summary
        
    except Exception as e:
        logger.error(f"Error getting sentiment summary for {bill_id}: {e}", exc_info=True)
        return {"concordo": 0, "discordo": 0, "neutro": 0, "total": 0}


def _get_all_feedback_keys() -> list:
    """
    Internal helper to get all feedback keys from store.
    
    Note: This is a workaround since _BaseStore doesn't expose keys().
    In production, consider adding a keys() method or using a proper database.
    
    Returns:
        List of all feedback keys
    """
    # Access internal store (not ideal but works for MVP)
    try:
        if hasattr(feedback_store, '_store'):
            return list(feedback_store._store.keys())
        return []
    except Exception as e:
        logger.error(f"Error getting feedback keys: {e}")
        return []


def get_mock_bill_info(bill_id: str) -> Optional[Dict]:
    """
    Mock function to get bill information.
    
    TODO: Phase 1 Integration
    - Replace with real Câmara API call
    - Example: from camara_api import CamaraClient
    - return CamaraClient().get_bill(bill_id)
    
    Args:
        bill_id: Bill identifier
        
    Returns:
        Mock bill information dictionary
    """
    # Mock data for demonstration
    mock_bills = {
        "PL2024/001": {
            "id": "PL2024/001",
            "title": "Ampliação do FUNDEB",
            "summary": "Projeto que amplia recursos para educação básica",
            "status": "Em tramitação",
        },
        "PL2024/015": {
            "id": "PL2024/015",
            "title": "SUS Digital",
            "summary": "Modernização do Sistema Único de Saúde",
            "status": "Em tramitação",
        },
    }
    
    return mock_bills.get(bill_id)
