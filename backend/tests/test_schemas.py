import pytest
from pydantic import ValidationError
from app.schemas import ExtractionDraft, validate_extraction


def test_valid_extraction_parses():
    raw = {
        "actual_care_summary": "Aankleden met extra hulp; douchen niet uitgevoerd.",
        "deviation_detected": True,
        "deviation_reason": "Cliënt voelde zich moe en weigerde douchen",
        "mood_observation": "veranderd: stiller dan normaal",
        "mood_changed": True,
        "behaviour_observation": "verminderde eetlust",
        "behaviour_changed": True,
    }
    draft = validate_extraction(raw)
    assert isinstance(draft, ExtractionDraft)
    assert draft.deviation_detected is True
    assert draft.mood_changed is True


def test_missing_required_field_raises():
    raw = {
        "actual_care_summary": "Aankleden gelukt.",
        "deviation_detected": False,
        # deviation_reason omitted — allowed to be None, so this alone should NOT fail.
        # mood_observation intentionally omitted to trigger the failure.
        "mood_changed": False,
        "behaviour_observation": "geen bijzonderheden",
        "behaviour_changed": False,
    }
    with pytest.raises(ValidationError):
        validate_extraction(raw)


def test_wrong_type_raises():
    raw = {
        "actual_care_summary": "Aankleden gelukt.",
        "deviation_detected": "yes",  # must be bool, not str
        "deviation_reason": None,
        "mood_observation": "geen verandering",
        "mood_changed": False,
        "behaviour_observation": "geen bijzonderheden",
        "behaviour_changed": False,
    }
    with pytest.raises(ValidationError):
        validate_extraction(raw)


def test_deviation_false_allows_null_reason():
    raw = {
        "actual_care_summary": "Alles volgens plan uitgevoerd.",
        "deviation_detected": False,
        "deviation_reason": None,
        "mood_observation": "geen verandering",
        "mood_changed": False,
        "behaviour_observation": "geen bijzonderheden",
        "behaviour_changed": False,
    }
    draft = validate_extraction(raw)
    assert draft.deviation_reason is None
