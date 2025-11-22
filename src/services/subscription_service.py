"""
Subscription service for managing user topic subscriptions.

This service allows users to subscribe to legislative topics and receive
notifications when relevant bills are discussed or voted on.

TODO: Phase 1 Integration
- Replace mock topic validation with real Câmara API
- Integrate with actual bill search by topic
- Add notification scheduling logic
"""

from typing import List, Optional
from storage import subscription_store
from logging_config import logger


def subscribe_topic(user_id: int, topic: str) -> bool:
    """
    Subscribe a user to a legislative topic.
    
    Args:
        user_id: Telegram user ID
        topic: Topic name (e.g., "educação", "saúde")
        
    Returns:
        True if subscription successful, False otherwise
        
    TODO: Phase 1 Integration
    - Add topic validation against Câmara API categories
    - Example: from camara_api import validate_topic
    """
    try:
        topic_normalized = topic.lower().strip()
        
        # TODO: Phase 1 - Validate topic exists in Câmara API
        # if not validate_topic(topic_normalized):
        #     logger.warning(f"Invalid topic: {topic_normalized}")
        #     return False
        
        # Get existing subscriptions
        existing = subscription_store.get(str(user_id), default_factory=list)
        if existing is None:
            existing = []
        
        # Avoid duplicates
        if topic_normalized in existing:
            logger.info(f"User {user_id} already subscribed to {topic_normalized}")
            return True
        
        # Add new subscription
        existing.append(topic_normalized)
        subscription_store.set(str(user_id), existing)
        
        logger.info(f"✅ User {user_id} subscribed to topic: {topic_normalized}")
        return True
        
    except Exception as e:
        logger.error(f"Error subscribing user {user_id} to {topic}: {e}", exc_info=True)
        return False


def unsubscribe_topic(user_id: int, topic: str) -> bool:
    """
    Unsubscribe a user from a legislative topic.
    
    Args:
        user_id: Telegram user ID
        topic: Topic name to unsubscribe from
        
    Returns:
        True if unsubscription successful, False otherwise
    """
    try:
        topic_normalized = topic.lower().strip()
        
        existing = subscription_store.get(str(user_id))
        if not existing or topic_normalized not in existing:
            logger.info(f"User {user_id} not subscribed to {topic_normalized}")
            return False
        
        existing.remove(topic_normalized)
        subscription_store.set(str(user_id), existing)
        
        logger.info(f"❌ User {user_id} unsubscribed from topic: {topic_normalized}")
        return True
        
    except Exception as e:
        logger.error(f"Error unsubscribing user {user_id} from {topic}: {e}", exc_info=True)
        return False


def get_subscriptions(user_id: int) -> List[str]:
    """
    Get all topics a user is subscribed to.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        List of subscribed topic names
    """
    try:
        subscriptions = subscription_store.get(str(user_id))
        if subscriptions is None:
            return []
        return subscriptions
        
    except Exception as e:
        logger.error(f"Error getting subscriptions for user {user_id}: {e}", exc_info=True)
        return []


def get_mock_bills_by_topic(topic: str) -> List[dict]:
    """
    Mock function to simulate bill search by topic.
    
    TODO: Phase 1 Integration
    - Replace with real Câmara API call
    - Example: from camara_api import CamaraClient
    - return CamaraClient().search_bills(topic=topic)
    
    Args:
        topic: Topic to search for
        
    Returns:
        List of mock bill dictionaries
    """
    # Mock data for demonstration
    mock_bills = {
        "educação": [
            {"id": "PL2024/001", "title": "Ampliação do FUNDEB", "status": "Em tramitação"},
            {"id": "PL2024/042", "title": "Educação Integral", "status": "Aprovado"},
        ],
        "saúde": [
            {"id": "PL2024/015", "title": "SUS Digital", "status": "Em tramitação"},
            {"id": "PL2024/089", "title": "Telemedicina", "status": "Em votação"},
        ],
        "meio ambiente": [
            {"id": "PL2024/033", "title": "Proteção da Amazônia", "status": "Em tramitação"},
        ],
    }
    
    topic_normalized = topic.lower().strip()
    return mock_bills.get(topic_normalized, [])
