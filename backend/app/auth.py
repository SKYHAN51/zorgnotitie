from fastapi import Header, HTTPException
from app.config import get_settings


def verify_demo_secret(x_demo_secret: str = Header(default="")):
    """Shared-secret gate for the demo API. Not real per-user auth — this
    is a portfolio demo with no user accounts — but it stops opportunistic
    bots/scanners from hitting a public Render URL and running up real
    OpenAI charges. The frontend sends the same secret on every request;
    combined with per-IP rate limiting (see main.py) for actual cost
    protection against a determined caller who reads it out of the page."""
    if x_demo_secret != get_settings().demo_api_secret:
        raise HTTPException(status_code=401, detail="Ongeldige of ontbrekende API-sleutel.")
