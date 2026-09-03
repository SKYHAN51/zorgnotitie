from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import ExtractionDraft
from app.extraction import ExtractionError

client = TestClient(app)

VALID_DRAFT = ExtractionDraft(
    actual_care_summary="Aankleden met extra hulp; douchen niet uitgevoerd.",
    deviation_detected=True,
    deviation_reason="Cliënt voelde zich moe",
    mood_observation="stiller dan normaal",
    mood_changed=True,
    behaviour_observation="verminderde eetlust",
    behaviour_changed=True,
)


def test_extract_endpoint_returns_draft(fake_supabase):
    fake_supabase.table("zorgmomenten").insert({
        "id": "zm-1", "transcript": "iets gezegd", "planned_care_summary": "Ochtendzorg.",
    }).execute()
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase), \
         patch("app.routes.zorgmomenten.extract", return_value=VALID_DRAFT):
        response = client.post("/zorgmomenten/zm-1/extract")
    assert response.status_code == 200
    body = response.json()
    assert body["review_status"] == "needs_review"
    assert body["extraction_json"]["deviation_detected"] is True


def test_extract_endpoint_surfaces_extraction_failure(fake_supabase):
    fake_supabase.table("zorgmomenten").insert({
        "id": "zm-1", "transcript": "iets gezegd", "planned_care_summary": "Ochtendzorg.",
    }).execute()
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase), \
         patch("app.routes.zorgmomenten.extract", side_effect=ExtractionError("bad json")):
        response = client.post("/zorgmomenten/zm-1/extract")
    assert response.status_code == 422
    assert response.json()["review_status"] == "failed"
