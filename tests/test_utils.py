import pytest
from unittest.mock import Mock, patch, MagicMock
from src.ai.openai_client import transcribe_audio, text_to_speech
from src.utils.media import download_media
from src.exceptions import APIError, MediaError

@pytest.fixture
def mock_openai(monkeypatch):
    mock_client = MagicMock()
    monkeypatch.setattr("src.ai.openai_client.client", mock_client)
    return mock_client

def test_transcribe_audio_success(mock_openai):
    mock_openai.audio.transcriptions.create.return_value.text = "Hello world"
    
    with patch("builtins.open", new_callable=MagicMock):
        result = transcribe_audio("dummy.ogg")
        
    assert result == "Hello world"
    mock_openai.audio.transcriptions.create.assert_called_once()

def test_transcribe_audio_failure(mock_openai):
    mock_openai.audio.transcriptions.create.side_effect = Exception("API Error")
    
    with patch("builtins.open", new_callable=MagicMock):
        with pytest.raises(APIError) as exc:
            transcribe_audio("dummy.ogg")
    
    assert "API Error" in str(exc.value)

def test_text_to_speech_success(mock_openai):
    mock_response = MagicMock()
    mock_openai.audio.speech.create.return_value = mock_response
    
    with patch("ai.openai_client.temporary_file") as mock_temp:
        mock_temp.return_value.__enter__.return_value = "temp.mp3"
        result = text_to_speech("Hello")
        
    assert result == "temp.mp3"
    mock_response.stream_to_file.assert_called_once_with("temp.mp3")

def test_download_media_success(mock_requests):
    mock_resp = MagicMock()
    mock_resp.content = b"data"
    mock_requests.get.return_value = mock_resp
    
    with patch("utils.media.temporary_file") as mock_temp:
        mock_temp.return_value.__enter__.return_value = "temp.jpg"
        with patch("builtins.open", new_callable=MagicMock):
            result = download_media("http://example.com/img.jpg", "jpg")
            
    assert result == "temp.jpg"

def test_download_media_failure(mock_requests):
    mock_requests.get.side_effect = Exception("Network Error")
    
    with pytest.raises(MediaError):
        download_media("http://example.com/img.jpg", "jpg")
