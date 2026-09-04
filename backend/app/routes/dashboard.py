# backend/app/routes/dashboard.py
from fastapi import APIRouter, HTTPException, Query
from app.db import get_client

router = APIRouter(prefix="/dashboard")


@router.get("/zorgmomenten")
def list_reviewed_zorgmomenten():
    client = get_client()
    all_rows = client.table("zorgmomenten").select("*").execute().data
    return [r for r in all_rows if r.get("review_status") == "reviewed"]


@router.get("/zorgmomenten/{zorgmoment_id}")
def get_zorgmoment_detail(zorgmoment_id: str):
    client = get_client()
    all_rows = client.table("zorgmomenten").select("*").execute().data
    row = next((r for r in all_rows if r.get("id") == zorgmoment_id), None)
    if row is None or row.get("review_status") != "reviewed":
        raise HTTPException(status_code=404, detail="Zorgmoment niet gevonden.")

    audit_rows = [
        a for a in client.table("audit_log").select("*").execute().data
        if a.get("zorgmoment_id") == zorgmoment_id
    ]
    alert_rows = [
        a for a in client.table("alerts").select("*").execute().data
        if a.get("zorgmoment_id") == zorgmoment_id
    ]
    return {**row, "audit_log": audit_rows, "alerts": alert_rows}


@router.get("/alerts")
def list_alerts(status: str = Query(default="open")):
    client = get_client()
    all_rows = client.table("alerts").select("*").execute().data
    return [a for a in all_rows if a.get("status") == status]
