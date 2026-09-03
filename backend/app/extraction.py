import json
from openai import OpenAI
from pydantic import ValidationError
from app.config import get_settings
from app.schemas import ExtractionDraft, validate_extraction

_client = OpenAI(api_key=get_settings().openai_api_key)

_SYSTEM_PROMPT = """Je bent een assistent die gesproken zorgobservaties omzet \
in een gestructureerd concept volgens de Z=P=R,T-methodiek (Zorgplan=Planning=\
Realisatie, tenzij). Je output is UITSLUITEND een JSON-object met exact deze \
velden, geen extra tekst eromheen:
{
  "actual_care_summary": string — wat er werkelijk is gebeurd tijdens het zorgmoment,
  "deviation_detected": boolean — week de uitgevoerde zorg af van de planning,
  "deviation_reason": string of null — reden voor de afwijking, alleen indien deviation_detected true is,
  "mood_observation": string — korte beschrijving van de stemming van de cliënt,
  "mood_changed": boolean — was er een merkbare verandering in stemming,
  "behaviour_observation": string — korte beschrijving van gedrag/gedragsverandering,
  "behaviour_changed": boolean — was er een merkbare gedragsverandering
}
Je doet een voorstel, geen definitieve beoordeling. Gebruik geen medische \
diagnoses, risicoscores of urgentieclassificaties."""


class ExtractionError(Exception):
    """Raised when the LLM's output can't be parsed or doesn't match the
    schema. Callers must surface this as a retry-able error, never guess
    at a structured draft from malformed output."""


def extract(transcript: str, planned_care_summary: str) -> ExtractionDraft:
    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Geplande zorg: {planned_care_summary}\n\n"
                    f"Gesproken observatie (transcript): {transcript}"
                )},
            ],
            response_format={"type": "json_object"},
        )
        raw_content = response.choices[0].message.content
    except Exception as exc:
        raise ExtractionError(f"Extraction API call failed: {exc}") from exc

    try:
        raw = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise ExtractionError(f"Extraction output was not valid JSON: {exc}") from exc

    try:
        return validate_extraction(raw)
    except ValidationError as exc:
        raise ExtractionError(f"Extraction output did not match the schema: {exc}") from exc
