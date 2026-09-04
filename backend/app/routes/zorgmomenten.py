# backend/app/routes/zorgmomenten.py
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.db import get_client
from app.stt import transcribe, TranscriptionError
from app.extraction import extract, ExtractionError
from app.events import log_event
from app.alerts import determine_alerts
from app.schemas import ExtractionDraft

router = APIRouter()

# A demo zorgmoment is a short spoken note, not a long recording — 10MB
# comfortably covers several minutes of compressed webm/opus audio while
# rejecting anything clearly wrong (e.g. an accidental video upload).
MAX_AUDIO_BYTES = 10 * 1024 * 1024

# Common wijkverpleging vocabulary — biases Whisper's recognition toward
# these terms when they're actually spoken. Never used to alter or invent
# transcript content, only to reduce misrecognition of known words.
_CARE_VOCABULARY_HINT = (
    "medicatie, wondverzorging, bloeddruk, stemming, wassen, aankleden, "
    "mobiliteit, ontbijt, douchen"
)


def _whisper_prompt(planned_care_summary: str) -> str:
    return f"{planned_care_summary} {_CARE_VOCABULARY_HINT}".strip()


def _load_zorgmoment_or_404(client, zorgmoment_id: str) -> dict:
    """Load a zorgmoment row by id from Supabase, or raise 404 if no row
    with that id exists. Shared by every endpoint that operates on an
    existing zorgmoment (record, extract, save) so an unknown id always
    produces a clear 404 instead of a silent no-op or a KeyError."""
    rows = client.table("zorgmomenten").select("*").execute().data
    row = next((r for r in rows if r.get("id") == zorgmoment_id), None)
    if row is None:
        raise HTTPException(status_code=404, detail="Zorgmoment niet gevonden.")
    return row


def _require(condition: bool, message: str) -> None:
    """Raise 409 with a clear Dutch message when a precondition on a
    zorgmoment's status isn't met. Used to guard extract/save so a stale
    browser tab (e.g. the back-button after a save) can't silently
    re-run extraction on an already-reviewed row or run extraction
    before audio has actually been transcribed."""
    if not condition:
        raise HTTPException(status_code=409, detail=message)


class CreateZorgmomentRequest(BaseModel):
    demo_client_id: str
    planned_care_summary: str


@router.post("/zorgmomenten", status_code=201)
def create_zorgmoment(body: CreateZorgmomentRequest):
    client = get_client()
    zorgmoment_id = str(uuid.uuid4())
    result = client.table("zorgmomenten").insert({
        "id": zorgmoment_id,
        "demo_client_id": body.demo_client_id,
        "planned_care_summary": body.planned_care_summary,
        "audio_status": "pending",
        "review_status": "processing",
    }).execute()
    return result.data[0] if hasattr(result, "data") and result.data else {
        "id": zorgmoment_id, "review_status": "processing"
    }


@router.post("/zorgmomenten/{zorgmoment_id}/record")
async def record_audio(zorgmoment_id: str, audio: UploadFile = File(...)):
    client = get_client()
    # Any status is eligible to record onto (a fresh zorgmoment always is) —
    # this call only exists to 404 on an unknown id rather than silently
    # no-op'ing, which used to be the behaviour here.
    row = _load_zorgmoment_or_404(client, zorgmoment_id)

    if audio.size is not None and audio.size > MAX_AUDIO_BYTES:
        return JSONResponse(status_code=413, content={
            "audio_status": "failed",
            "message": "Audiobestand is te groot. Neem een kortere notitie op.",
        })
    if audio.content_type and not audio.content_type.startswith("audio/"):
        return JSONResponse(status_code=415, content={
            "audio_status": "failed",
            "message": "Bestandstype wordt niet ondersteund. Neem audio op.",
        })

    audio_bytes = await audio.read()

    log_event(client, zorgmoment_id, "stt", "started")
    prompt = _whisper_prompt(row.get("planned_care_summary") or "")
    try:
        transcript = transcribe(audio_bytes, audio.filename or "note.webm", prompt=prompt)
    except TranscriptionError as exc:
        log_event(client, zorgmoment_id, "stt", "failed", error_code="stt_failed",
                   error_message_safe=str(exc))
        client.table("zorgmomenten").update({
            "audio_status": "failed",
        }).eq("id", zorgmoment_id).execute()
        return JSONResponse(status_code=422, content={
            "audio_status": "failed",
            "message": "Transcriptie mislukt. Probeer het opnieuw.",
        })
    finally:
        # Audio is never persisted — it only ever existed in this
        # request's memory and is discarded when this function returns.
        del audio_bytes

    log_event(client, zorgmoment_id, "stt", "succeeded")
    client.table("zorgmomenten").update({
        "audio_status": "transcribed", "transcript": transcript,
    }).eq("id", zorgmoment_id).execute()
    return {"id": zorgmoment_id, "audio_status": "transcribed", "transcript": transcript}


@router.get("/demo-clients")
def list_demo_clients():
    client = get_client()
    return client.table("demo_clients").select("*").execute().data


@router.post("/zorgmomenten/{zorgmoment_id}/extract")
def extract_zorgmoment(zorgmoment_id: str):
    client = get_client()
    row = _load_zorgmoment_or_404(client, zorgmoment_id)
    _require(
        row.get("review_status") != "reviewed",
        "Dit zorgmoment is al beoordeeld en opgeslagen; extractie kan niet opnieuw worden uitgevoerd.",
    )
    transcript = row.get("transcript")
    _require(
        row.get("audio_status") == "transcribed" and bool(transcript and transcript.strip()),
        "Audio is nog niet getranscribeerd; extractie kan nog niet worden uitgevoerd.",
    )

    log_event(client, zorgmoment_id, "extraction", "started")
    try:
        draft = extract(row["transcript"], row["planned_care_summary"])
    except ExtractionError as exc:
        log_event(client, zorgmoment_id, "extraction", "failed",
                   error_code="extraction_failed", error_message_safe=str(exc))
        client.table("zorgmomenten").update({
            "review_status": "failed",
        }).eq("id", zorgmoment_id).execute()
        return JSONResponse(status_code=422, content={
            "review_status": "failed",
            "message": "Kon geen gestructureerd concept maken. Probeer het opnieuw.",
        })

    log_event(client, zorgmoment_id, "extraction", "succeeded")
    extraction_json = draft.model_dump()
    client.table("zorgmomenten").update({
        "review_status": "needs_review",
        "extraction_json": extraction_json,
    }).eq("id", zorgmoment_id).execute()
    return {
        "id": zorgmoment_id,
        "review_status": "needs_review",
        "extraction_json": extraction_json,
        "transcript": row["transcript"],
    }


class SaveZorgmomentRequest(BaseModel):
    actual_care_summary: str
    deviation_detected: bool
    deviation_reason: Optional[str] = None
    mood_observation: str
    mood_changed: bool
    behaviour_observation: str
    behaviour_changed: bool
    reviewed_by: str


@router.post("/zorgmomenten/{zorgmoment_id}/save")
def save_zorgmoment(zorgmoment_id: str, body: SaveZorgmomentRequest):
    client = get_client()
    row = _load_zorgmoment_or_404(client, zorgmoment_id)
    _require(row.get("review_status") == "needs_review", "Dit zorgmoment is niet klaar om op te slaan.")

    before_json = row.get("extraction_json")
    after_json = body.model_dump()

    # This is the ONLY place final fields are written — always from the
    # human-approved request body, never copied from extraction_json.
    client.table("zorgmomenten").update({
        "review_status": "reviewed",
        **after_json,
    }).eq("id", zorgmoment_id).execute()

    client.table("audit_log").insert({
        "zorgmoment_id": zorgmoment_id,
        "actor_type": "human",
        "event_type": "review_saved",
        "before_json": before_json,
        "after_json": after_json,
    }).execute()

    draft = ExtractionDraft(**after_json_without_reviewer(after_json))
    for alert in determine_alerts(draft):
        client.table("alerts").insert({
            "zorgmoment_id": zorgmoment_id,
            "alert_type": alert["alert_type"],
            "reason": alert["reason"],
        }).execute()

    return {"id": zorgmoment_id, "review_status": "reviewed"}


def after_json_without_reviewer(after_json: dict) -> dict:
    """ExtractionDraft doesn't have a reviewed_by field — strip it before
    constructing the draft used for alert determination."""
    return {k: v for k, v in after_json.items() if k != "reviewed_by"}
