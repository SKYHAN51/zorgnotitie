# backend/scripts/demo_walkthrough.py
"""Manual end-to-end smoke script — run against a live backend
(uvicorn app.main:app --reload) with real Supabase + OpenAI credentials.
Not part of the pytest suite: this hits real APIs and costs real tokens."""
import requests

BASE = "http://localhost:8000"

def main():
    health = requests.get(f"{BASE}/health").json()
    print("Health:", health)
    assert health["status"] == "healthy"

    create = requests.post(f"{BASE}/zorgmomenten", json={
        "demo_client_id": "REPLACE_WITH_REAL_DEMO_CLIENT_ID",
        "planned_care_summary": "Ochtendzorg: hulp bij wassen en aankleden, medicatieherinnering en ontbijtvoorbereiding.",
    })
    zm_id = create.json()["id"]
    print("Created zorgmoment:", zm_id)

    print("Manually record and upload audio via the frontend for this ID, then run:")
    print(f"  requests.post('{BASE}/zorgmomenten/{zm_id}/extract')")
    print("to continue this walkthrough.")


if __name__ == "__main__":
    main()
