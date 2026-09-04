from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import ExtractionDraft
from app.extraction import ExtractionError
from tests.conftest import TEST_AUTH_HEADERS

client = TestClient(app, headers=TEST_AUTH_HEADERS)

VALID_DRAFT = ExtractionDraft(
    actual_care_summary="Aankleden met extra hulp; douchen niet uitgevoerd.",
    deviation_detected=True,
    deviation_reason="Cliënt voelde zich moe",
    mood_observation="stiller dan normaal",
    mood_changed=True,
    behaviour_observation="verminderde eetlust",
    behaviour_changed=True,
)


def _seed_transcribed_zorgmoment(fake_supabase, **overrides):
    """A zorgmoment whose audio has already been transcribed — the only
    state extraction is allowed to run from."""
    row = {
        "id": "zm-1",
        "transcript": "iets gezegd",
        "planned_care_summary": "Ochtendzorg.",
        "audio_status": "transcribed",
        "review_status": "processing",
    }
    row.update(overrides)
    fake_supabase.table("zorgmomenten").insert(row).execute()
    return row


def test_extract_endpoint_returns_draft(fake_supabase):
    _seed_transcribed_zorgmoment(fake_supabase)
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase), \
         patch("app.routes.zorgmomenten.extract", return_value=VALID_DRAFT):
        response = client.post("/zorgmomenten/zm-1/extract")
    assert response.status_code == 200
    body = response.json()
    assert body["review_status"] == "needs_review"
    assert body["extraction_json"]["deviation_detected"] is True


def test_extract_endpoint_includes_raw_transcript_in_response(fake_supabase):
    """I2: the review page needs the raw transcript alongside the AI's
    structured draft so the caregiver has something to check it against."""
    _seed_transcribed_zorgmoment(fake_supabase, transcript="Mevrouw wilde niet douchen vandaag.")
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase), \
         patch("app.routes.zorgmomenten.extract", return_value=VALID_DRAFT):
        response = client.post("/zorgmomenten/zm-1/extract")
    assert response.status_code == 200
    assert response.json()["transcript"] == "Mevrouw wilde niet douchen vandaag."


def test_extract_endpoint_surfaces_extraction_failure(fake_supabase):
    _seed_transcribed_zorgmoment(fake_supabase)
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase), \
         patch("app.routes.zorgmomenten.extract", side_effect=ExtractionError("bad json")):
        response = client.post("/zorgmomenten/zm-1/extract")
    assert response.status_code == 422
    assert response.json()["review_status"] == "failed"


def test_extract_rejected_when_already_reviewed(fake_supabase):
    """C2: re-running extraction on an already-reviewed row (e.g. reachable
    via the browser back-button after save) must be rejected, not silently
    overwrite extraction_json and flip review_status back."""
    _seed_transcribed_zorgmoment(fake_supabase, review_status="reviewed")
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase), \
         patch("app.routes.zorgmomenten.extract", return_value=VALID_DRAFT) as mock_extract:
        response = client.post("/zorgmomenten/zm-1/extract")
    assert response.status_code == 409
    assert "beoordeeld" in response.json()["detail"]
    mock_extract.assert_not_called()


def test_extract_rejected_when_audio_not_transcribed(fake_supabase):
    """C2: extraction must not run before audio_status == 'transcribed' —
    otherwise the LLM receives a null/placeholder transcript and can
    fabricate a plausible-sounding note."""
    fake_supabase.table("zorgmomenten").insert({
        "id": "zm-1",
        "transcript": None,
        "planned_care_summary": "Ochtendzorg.",
        "audio_status": "pending",
        "review_status": "processing",
    }).execute()
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase), \
         patch("app.routes.zorgmomenten.extract", return_value=VALID_DRAFT) as mock_extract:
        response = client.post("/zorgmomenten/zm-1/extract")
    assert response.status_code == 409
    assert "getranscribeerd" in response.json()["detail"]
    mock_extract.assert_not_called()


def test_extract_rejected_when_transcript_empty_string(fake_supabase):
    """Same guard, but for the audio_status='transcribed'-with-empty-transcript
    edge case rather than a missing/null transcript."""
    _seed_transcribed_zorgmoment(fake_supabase, transcript="   ")
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase), \
         patch("app.routes.zorgmomenten.extract", return_value=VALID_DRAFT) as mock_extract:
        response = client.post("/zorgmomenten/zm-1/extract")
    assert response.status_code == 409
    mock_extract.assert_not_called()


def test_extract_returns_404_on_unknown_id(fake_supabase):
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase):
        response = client.post("/zorgmomenten/does-not-exist/extract")
    assert response.status_code == 404
