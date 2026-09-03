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
    audio_bytes = await audio.read()

    log_event(client, zorgmoment_id, "stt", "started")
    try:
        transcript = transcribe(audio_bytes, audio.filename or "note.webm")
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
    return client.table("demo_clients").execute().data


@router.post("/zorgmomenten/{zorgmoment_id}/extract")
def extract_zorgmoment(zorgmoment_id: str):
    client = get_client()
    existing = client.table("zorgmomenten").execute().data
    row = next((r for r in existing if r.get("id") == zorgmoment_id), None)
    if row is None:
        raise HTTPException(status_code=404, detail="Zorgmoment niet gevonden.")

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
    return {"id": zorgmoment_id, "review_status": "needs_review", "extraction_json": extraction_json}


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
    existing = client.table("zorgmomenten").execute().data
    row = next((r for r in existing if r.get("id") == zorgmoment_id), None)
    if row is None:
        raise HTTPException(status_code=404, detail="Zorgmoment niet gevonden.")
    if row.get("review_status") != "needs_review":
        raise HTTPException(status_code=409, detail="Dit zorgmoment is niet klaar om op te slaan.")

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
