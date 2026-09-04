# backend/tests/test_routes_save.py
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import TEST_AUTH_HEADERS

client = TestClient(app, headers=TEST_AUTH_HEADERS)


def _seed_needs_review_zorgmoment(fake_supabase, **extraction_overrides):
    extraction_json = {
        "actual_care_summary": "Aankleden met extra hulp; douchen niet uitgevoerd.",
        "deviation_detected": True,
        "deviation_reason": "Cliënt voelde zich moe",
        "mood_observation": "stiller dan normaal",
        "mood_changed": True,
        "behaviour_observation": "verminderde eetlust",
        "behaviour_changed": True,
    }
    extraction_json.update(extraction_overrides)
    fake_supabase.table("zorgmomenten").insert({
        "id": "zm-1", "review_status": "needs_review", "extraction_json": extraction_json,
    }).execute()
    return extraction_json


def test_save_writes_final_fields_from_human_approved_body(fake_supabase):
    _seed_needs_review_zorgmoment(fake_supabase)
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase):
        response = client.post("/zorgmomenten/zm-1/save", json={
            "actual_care_summary": "Aankleden met extra hulp; douchen niet uitgevoerd (bevestigd).",
            "deviation_detected": True,
            "deviation_reason": "Cliënt voelde zich moe",
            "mood_observation": "stiller dan normaal",
            "mood_changed": True,
            "behaviour_observation": "verminderde eetlust",
            "behaviour_changed": True,
            "reviewed_by": "demo-zorgmedewerker",
        })
    assert response.status_code == 200
    saved_rows = [r for r in fake_supabase.table("zorgmomenten").select("*").execute().data if r.get("review_status") == "reviewed"]
    assert len(saved_rows) == 1
    assert saved_rows[0]["actual_care_summary"].endswith("(bevestigd).")


def test_save_creates_alerts_matching_final_fields(fake_supabase):
    _seed_needs_review_zorgmoment(fake_supabase)
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase):
        client.post("/zorgmomenten/zm-1/save", json={
            "actual_care_summary": "iets",
            "deviation_detected": True, "deviation_reason": "reden",
            "mood_observation": "stemming", "mood_changed": True,
            "behaviour_observation": "gedrag", "behaviour_changed": True,
            "reviewed_by": "demo-zorgmedewerker",
        })
    alert_rows = fake_supabase.table("alerts").select("*").execute().data
    types = {a["alert_type"] for a in alert_rows}
    assert types == {"care_deviation", "mood_change", "behaviour_change"}


def test_save_writes_audit_log_with_before_and_after(fake_supabase):
    original = _seed_needs_review_zorgmoment(fake_supabase)
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase):
        client.post("/zorgmomenten/zm-1/save", json={
            "actual_care_summary": "GEWIJZIGD door zorgmedewerker",
            "deviation_detected": True, "deviation_reason": "reden",
            "mood_observation": "stemming", "mood_changed": True,
            "behaviour_observation": "gedrag", "behaviour_changed": True,
            "reviewed_by": "demo-zorgmedewerker",
        })
    audit_rows = fake_supabase.table("audit_log").select("*").execute().data
    assert len(audit_rows) == 1
    assert audit_rows[0]["before_json"]["actual_care_summary"] == original["actual_care_summary"]
    assert audit_rows[0]["after_json"]["actual_care_summary"] == "GEWIJZIGD door zorgmedewerker"
    assert audit_rows[0]["actor_type"] == "human"


def test_save_when_caregiver_clears_a_flagged_field_creates_no_alert_for_it(fake_supabase):
    """The caregiver can override the AI's proposed booleans during review —
    if they correct mood_changed to false, no mood_change alert is created,
    even though the AI's original draft had it true."""
    _seed_needs_review_zorgmoment(fake_supabase, mood_changed=True)
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase):
        client.post("/zorgmomenten/zm-1/save", json={
            "actual_care_summary": "iets",
            "deviation_detected": False, "deviation_reason": None,
            "mood_observation": "geen verandering na overleg", "mood_changed": False,
            "behaviour_observation": "geen bijzonderheden", "behaviour_changed": False,
            "reviewed_by": "demo-zorgmedewerker",
        })
    alert_rows = fake_supabase.table("alerts").select("*").execute().data
    assert alert_rows == []


def test_resaving_an_already_reviewed_zorgmoment_is_rejected(fake_supabase):
    """A zorgmoment can only move from needs_review -> reviewed once.
    This prevents duplicate alerts if a caregiver double-clicks Save or
    the client retries a slow request."""
    fake_supabase.table("zorgmomenten").insert({
        "id": "zm-1", "review_status": "reviewed",
    }).execute()
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase):
        response = client.post("/zorgmomenten/zm-1/save", json={
            "actual_care_summary": "iets",
            "deviation_detected": True, "deviation_reason": "reden",
            "mood_observation": "stemming", "mood_changed": True,
            "behaviour_observation": "gedrag", "behaviour_changed": True,
            "reviewed_by": "demo-zorgmedewerker",
        })
    assert response.status_code == 409
    alert_rows = fake_supabase.table("alerts").select("*").execute().data
    assert alert_rows == []
