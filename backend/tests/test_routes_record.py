# backend/tests/test_routes_record.py
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

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
