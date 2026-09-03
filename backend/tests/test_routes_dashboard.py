# backend/tests/test_routes_dashboard.py
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dashboard_list_excludes_unreviewed_rows(fake_supabase):
    fake_supabase.table("zorgmomenten").insert({"id": "zm-1", "review_status": "reviewed", "actual_care_summary": "a"}).execute()
    fake_supabase.table("zorgmomenten").insert({"id": "zm-2", "review_status": "needs_review", "actual_care_summary": "b"}).execute()
    fake_supabase.table("zorgmomenten").insert({"id": "zm-3", "review_status": "failed"}).execute()
    with patch("app.routes.dashboard.get_client", return_value=fake_supabase):
        response = client.get("/dashboard/zorgmomenten")
    ids = [r["id"] for r in response.json()]
    assert ids == ["zm-1"]


def test_dashboard_detail_includes_audit_log(fake_supabase):
    fake_supabase.table("zorgmomenten").insert({"id": "zm-1", "review_status": "reviewed"}).execute()
    fake_supabase.table("audit_log").insert({"zorgmoment_id": "zm-1", "actor_type": "human", "event_type": "review_saved"}).execute()
    with patch("app.routes.dashboard.get_client", return_value=fake_supabase):
        response = client.get("/dashboard/zorgmomenten/zm-1")
    assert response.status_code == 200
    assert len(response.json()["audit_log"]) == 1


def test_open_alerts_endpoint_filters_by_status(fake_supabase):
    fake_supabase.table("alerts").insert({"id": "a1", "zorgmoment_id": "zm-1", "alert_type": "mood_change", "status": "open"}).execute()
    fake_supabase.table("alerts").insert({"id": "a2", "zorgmoment_id": "zm-1", "alert_type": "care_deviation", "status": "resolved"}).execute()
    with patch("app.routes.dashboard.get_client", return_value=fake_supabase):
        response = client.get("/dashboard/alerts?status=open")
    ids = [a["id"] for a in response.json()]
    assert ids == ["a1"]
