# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.zorgmomenten import router as zorgmomenten_router
from app.routes.dashboard import router as dashboard_router

app = FastAPI(title="ZorgNotitie API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # tighten to the deployed frontend origin in Phase 7
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(zorgmomenten_router)
app.include_router(dashboard_router)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "zorgnotitie"}
