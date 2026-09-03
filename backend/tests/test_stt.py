from unittest.mock import patch, MagicMock
import pytest
from app.stt import transcribe, TranscriptionError


def test_transcribe_returns_text_on_success():
    fake_response = MagicMock()
    fake_response.text = "Mevrouw De Vries wilde vandaag niet douchen."
    with patch("app.stt._client") as mock_client:
        mock_client.audio.transcriptions.create.return_value = fake_response
        result = transcribe(b"fake-audio-bytes", "note.webm")
    assert result == "Mevrouw De Vries wilde vandaag niet douchen."


def test_transcribe_raises_on_empty_result():
    fake_response = MagicMock()
    fake_response.text = "   "
    with patch("app.stt._client") as mock_client:
        mock_client.audio.transcriptions.create.return_value = fake_response
        with pytest.raises(TranscriptionError):
            transcribe(b"fake-audio-bytes", "note.webm")


def test_transcribe_raises_on_api_error():
    with patch("app.stt._client") as mock_client:
        mock_client.audio.transcriptions.create.side_effect = Exception("timeout")
        with pytest.raises(TranscriptionError):
            transcribe(b"fake-audio-bytes", "note.webm")
