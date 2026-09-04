from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import TEST_AUTH_HEADERS

client = TestClient(app)


def test_protected_route_rejects_missing_secret(fake_supabase):
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase):
        response = client.get("/demo-clients")
    assert response.status_code == 401


def test_protected_route_rejects_wrong_secret(fake_supabase):
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase):
        response = client.get("/demo-clients", headers={"X-Demo-Secret": "wrong"})
    assert response.status_code == 401


def test_protected_route_accepts_correct_secret(fake_supabase):
    with patch("app.routes.zorgmomenten.get_client", return_value=fake_supabase):
        response = client.get("/demo-clients", headers=TEST_AUTH_HEADERS)
    assert response.status_code == 200


def test_dashboard_route_also_protected(fake_supabase):
    with patch("app.routes.dashboard.get_client", return_value=fake_supabase):
        response = client.get("/dashboard/alerts")
    assert response.status_code == 401


def test_health_endpoint_does_not_require_secret():
    """Render's health checks hit this without any header — it must stay open."""
    response = client.get("/health")
    assert response.status_code == 200
