# backend/app/main.py
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.auth import verify_demo_secret
from app.rate_limit import limiter
from app.routes.zorgmomenten import router as zorgmomenten_router
from app.routes.dashboard import router as dashboard_router

app = FastAPI(title="ZorgNotitie API")

# Per-IP baseline for every route; /record and /extract carry a tighter
# limit of their own (see zorgmomenten.py) since those are the two calls
# that spend real OpenAI credits.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://localhost:\d+$",  # tighten to the deployed frontend origin in Phase 7
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(zorgmomenten_router, dependencies=[Depends(verify_demo_secret)])
app.include_router(dashboard_router, dependencies=[Depends(verify_demo_secret)])


@app.get("/health")
def health():
    return {"status": "healthy", "service": "zorgnotitie"}
