import pytest
from unittest.mock import MagicMock, patch
from src.ai.brain import process_message

@pytest.mark.asyncio
async def test_process_message_success():
    with patch("src.ai.brain.with_message_history") as mock_chain:
        # Mock the ainvoke method
        mock_response = MagicMock()
        mock_response.content = "Hello human"
        mock_chain.ainvoke.return_value = mock_response
        
        response = await process_message("session1", "Hello")
        
        assert response == "Hello human"
        mock_chain.ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_process_message_failure():
    with patch("ai.brain.with_message_history") as mock_chain:
        mock_chain.ainvoke.side_effect = Exception("AI Error")
        
        response = await process_message("session1", "Hello")
        
        assert "Desculpe" in response
