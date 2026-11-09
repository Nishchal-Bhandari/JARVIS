"""FastAPI app: routers, CORS, lifespan (loads topology on startup)."""

import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import models
from .api import events, incidents, simulator, ws
from .config import settings
from .db import Base, SessionLocal, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Service).count() == 0:
            path = os.path.join(os.path.dirname(__file__), "data", "topology.json")
            with open(path) as f:  # noqa: ASYNC230 (startup, once)
                topo = json.load(f)
            for s in topo["services"]:
                db.add(
                    models.Service(
                        id=s["id"],
                        kind=s["kind"],
                        tier=s["tier"],
                        critical=1 if s.get("critical") else 0,
                    )
                )
            for d in topo["dependencies"]:
                db.add(models.Dependency(from_service=d["from"], to_service=d["to"]))
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(title="J.A.R.V.I.S.", lifespan=lifespan)


@app.exception_handler(Exception)
async def error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500, content={"error": {"code": "internal_error", "message": str(exc)}}
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(events.router, prefix="/api/v1")
app.include_router(incidents.router, prefix="/api/v1")
app.include_router(simulator.router, prefix="/api/v1")
app.include_router(ws.router)
