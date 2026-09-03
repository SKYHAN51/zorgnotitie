from typing import Optional
from pydantic import BaseModel, ConfigDict


class ExtractionDraft(BaseModel):
    model_config = ConfigDict(strict=True)

    actual_care_summary: str
    deviation_detected: bool
    deviation_reason: Optional[str] = None
    mood_observation: str
    mood_changed: bool
    behaviour_observation: str
    behaviour_changed: bool


def validate_extraction(raw: dict) -> ExtractionDraft:
    """Validate the LLM's raw JSON proposal against the fixed schema.
    Raises pydantic.ValidationError on any malformed or missing field —
    callers must not silently pass through invalid extraction output."""
    return ExtractionDraft(**raw)
