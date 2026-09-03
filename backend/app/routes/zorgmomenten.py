# backend/app/routes/zorgmomenten.py
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.db import get_client
from app.stt import transcribe, TranscriptionError
from app.extraction import extract, ExtractionError
from app.events import log_event

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
