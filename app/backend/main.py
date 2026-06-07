from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.backend.api import calculations, dashboard, digitized_graphs, exports, projects, reports, scenarios, standards
from app.backend.database.models import Base
from app.backend.database.seed import seed_if_empty
from app.backend.database.session import SessionLocal, engine
from app.standards.metadata import APP_VERSION, ENGINE_VERSION

app = FastAPI(title="API RP 1102 Loading Calculator", version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="app/backend/static"), name="static")

DIGITIZED_DIR = Path("Refs/digitized_api_1102")
if DIGITIZED_DIR.exists():
    app.mount("/api/digitized-assets", StaticFiles(directory=DIGITIZED_DIR), name="digitized-assets")

app.include_router(dashboard.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(calculations.router, prefix="/api")
app.include_router(scenarios.router, prefix="/api")
app.include_router(standards.router, prefix="/api")
app.include_router(exports.router, prefix="/api")
app.include_router(digitized_graphs.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"ok": True, "app_version": APP_VERSION, "calculation_engine_version": ENGINE_VERSION}
