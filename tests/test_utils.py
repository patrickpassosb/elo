import pytest
from unittest.mock import Mock, patch, MagicMock
from ai.openai_client import transcribe_audio, text_to_speech
from utils.media import download_media
from exceptions import APIError, MediaError

@pytest.fixture
def mock_openai(monkeypatch):
    mock_client = MagicMock()
    monkeypatch.setattr("ai.openai_client.client", mock_client)
    return mock_client

@pytest.fixture
def mock_requests(monkeypatch):
    mock_req = MagicMock()
    monkeypatch.setattr("utils.media.requests", mock_req)
    return mock_req

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
    
    with patch("tempfile.mkstemp") as mock_mkstemp, \
         patch("os.close"), \
         patch("os.remove"), \
         patch("os.path.exists", return_value=False):
        
        mock_mkstemp.return_value = (123, "temp.mp3")
        
        result = text_to_speech("Hello")
        
        assert result == "temp.mp3"
        mock_openai.audio.speech.create.assert_called_once()
        mock_response.stream_to_file.assert_called_once_with("temp.mp3")


