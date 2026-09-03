import json
from unittest.mock import patch, MagicMock
import pytest
from app.extraction import extract, ExtractionError

VALID_JSON = json.dumps({
    "actual_care_summary": "Aankleden met extra hulp; douchen niet uitgevoerd.",
    "deviation_detected": True,
    "deviation_reason": "Cliënt voelde zich moe",
    "mood_observation": "stiller dan normaal",
    "mood_changed": True,
    "behaviour_observation": "verminderde eetlust",
    "behaviour_changed": True,
})


def _mock_completion(content: str):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


def test_extract_returns_validated_draft():
    with patch("app.extraction._client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_completion(VALID_JSON)
        draft = extract("transcript hier", "geplande zorg hier")
    assert draft.deviation_detected is True
    assert draft.mood_changed is True


def test_extract_raises_on_invalid_json():
    with patch("app.extraction._client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_completion("dit is geen json")
        with pytest.raises(ExtractionError):
            extract("transcript hier", "geplande zorg hier")


def test_extract_raises_on_schema_mismatch():
    bad_json = json.dumps({"actual_care_summary": "iets", "deviation_detected": "niet een boolean"})
    with patch("app.extraction._client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_completion(bad_json)
        with pytest.raises(ExtractionError):
            extract("transcript hier", "geplande zorg hier")


def test_extract_raises_on_api_error():
    with patch("app.extraction._client") as mock_client:
        mock_client.chat.completions.create.side_effect = Exception("rate limited")
        with pytest.raises(ExtractionError):
            extract("transcript hier", "geplande zorg hier")
