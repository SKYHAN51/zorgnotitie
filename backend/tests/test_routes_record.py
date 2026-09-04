# backend/tests/test_routes_record.py
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.routes.zorgmomenten import MAX_AUDIO_BYTES

client = TestClient(app)


def test_create_zorgmoment_returns_id_and_processing_status(fake_supabase):
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase):
        fake_supabase.table("demo_clients").insert({
            "id": "client-1", "display_name": "Mevrouw De Vries",
            "care_plan_summary": "Ochtendzorg.",
        }).execute()
        response = client.post("/zorgmomenten", json={
            "demo_client_id": "client-1",
            "planned_care_summary": "Ochtendzorg.",
        })
    assert response.status_code == 201
    body = response.json()
    assert body["review_status"] == "processing"
    assert "id" in body


def test_record_endpoint_transcribes_and_updates_status(fake_supabase):
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase), \
         patch("app.routes.zorgmomenten.transcribe", return_value="Testnotitie."):
        create_resp = client.post("/zorgmomenten", json={
            "demo_client_id": "client-1",
            "planned_care_summary": "Ochtendzorg.",
        })
        zm_id = create_resp.json()["id"]
        response = client.post(
            f"/zorgmomenten/{zm_id}/record",
            files={"audio": ("note.webm", b"fake-bytes", "audio/webm")},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["audio_status"] == "transcribed"
    assert body["transcript"] == "Testnotitie."


def test_record_endpoint_surfaces_stt_failure(fake_supabase):
    from app.stt import TranscriptionError
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase), \
         patch("app.routes.zorgmomenten.transcribe", side_effect=TranscriptionError("timeout")):
        create_resp = client.post("/zorgmomenten", json={
            "demo_client_id": "client-1",
            "planned_care_summary": "Ochtendzorg.",
        })
        zm_id = create_resp.json()["id"]
        response = client.post(
            f"/zorgmomenten/{zm_id}/record",
            files={"audio": ("note.webm", b"fake-bytes", "audio/webm")},
        )
    assert response.status_code == 422
    assert response.json()["audio_status"] == "failed"


def test_record_endpoint_passes_care_context_as_whisper_prompt(fake_supabase):
    """Whisper's prompt is a vocabulary hint, built from this zorgmoment's
    planned_care_summary, so recognizably-spoken client/care terms transcribe
    more accurately — it must never be used to invent transcript content."""
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase), \
         patch("app.routes.zorgmomenten.transcribe", return_value="Testnotitie.") as mock_transcribe:
        create_resp = client.post("/zorgmomenten", json={
            "demo_client_id": "client-1",
            "planned_care_summary": "Ochtendzorg: hulp bij wassen en aankleden.",
        })
        zm_id = create_resp.json()["id"]
        client.post(
            f"/zorgmomenten/{zm_id}/record",
            files={"audio": ("note.webm", b"fake-bytes", "audio/webm")},
        )
    _, kwargs = mock_transcribe.call_args
    assert "Ochtendzorg: hulp bij wassen en aankleden." in kwargs["prompt"]


def test_record_returns_404_on_unknown_id(fake_supabase):
    """C2/I1: recording onto an unknown zorgmoment id used to be a silent
    no-op (the update simply matched zero rows). It must now 404 instead."""
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase):
        response = client.post(
            "/zorgmomenten/does-not-exist/record",
            files={"audio": ("note.webm", b"fake-bytes", "audio/webm")},
        )
    assert response.status_code == 404


def test_record_rejects_oversized_audio_upload(fake_supabase):
    """I4: an oversized upload must be rejected before the bytes are ever
    read into memory. Uses a mocked UploadFile so the test doesn't need to
    actually construct a >10MB payload."""
    import asyncio
    from app.routes.zorgmomenten import record_audio

    fake_supabase.table("zorgmomenten").insert({
        "id": "zm-1", "audio_status": "pending", "review_status": "processing",
    }).execute()

    fake_audio = MagicMock()
    fake_audio.size = MAX_AUDIO_BYTES + 1
    fake_audio.content_type = "audio/webm"
    fake_audio.filename = "note.webm"

    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase):
        response = asyncio.run(record_audio("zm-1", fake_audio))

    assert response.status_code == 413
    fake_audio.read.assert_not_called()


def test_list_demo_clients_returns_seeded_rows(fake_supabase):
    fake_supabase.table("demo_clients").insert({
        "id": "client-1", "display_name": "Mevrouw De Vries",
        "care_plan_summary": "Ochtendzorg.",
    }).execute()
    fake_supabase.table("demo_clients").insert({
        "id": "client-2", "display_name": "Meneer Bakker",
        "care_plan_summary": "Avondzorg.",
    }).execute()
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase):
        response = client.get("/demo-clients")
    assert response.status_code == 200
    names = [c["display_name"] for c in response.json()]
    assert names == ["Mevrouw De Vries", "Meneer Bakker"]
