import io
from openai import OpenAI
from app.config import get_settings


class TranscriptionError(Exception):
    """Raised when speech-to-text fails or returns unusable output.
    Callers must surface this as a retry-able error, never fall back
    to an empty or guessed transcript."""


_client = OpenAI(api_key=get_settings().openai_api_key)


def transcribe(audio_bytes: bytes, filename: str) -> str:
    try:
        buf = io.BytesIO(audio_bytes)
        buf.name = filename
        response = _client.audio.transcriptions.create(
            model="whisper-1",
            file=buf,
        )
    except Exception as exc:
        raise TranscriptionError(f"STT call failed: {exc}") from exc

    text = (response.text or "").strip()
    if not text:
        raise TranscriptionError("STT returned an empty transcript.")
    return text
