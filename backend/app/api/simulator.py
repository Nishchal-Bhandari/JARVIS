"""Simulator endpoints (specsheet §11, §13)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..core import engine as engine_mod
from ..db import get_db
from ..simulator.runner import simulator
from .broadcast import broadcast
from .helpers import store_event

router = APIRouter()


@router.post("/simulator/start")
async def start(payload: schemas.SimulatorStart, db: Session = Depends(get_db)):
    count = {"n": 0}

    def ingest(ev):
        # fresh DB session per event (runner runs in background)
        # Tick every 5 events, not every event, so playback keeps up.
        from ..db import SessionLocal

        s = SessionLocal()
        try:
            store_event(s, ev)
            count["n"] += 1
            if count["n"] % 5 == 0:
                engine_mod.tick(s, broadcast=broadcast)
        finally:
            s.close()

    def on_done():
        from ..db import SessionLocal

        s = SessionLocal()
        try:
            engine_mod.tick(s, broadcast=broadcast)
        finally:
            s.close()

    ok = await simulator.start(
        payload.scenario, payload.speed, ingest, broadcast=broadcast, on_done=on_done
    )
    return {"started": ok, "scenario": payload.scenario, "speed": payload.speed}


@router.post("/simulator/stop")
def stop():
    simulator.stop()
    return {"running": False}


@router.post("/simulator/reset")
def reset(db: Session = Depends(get_db)):
    simulator.stop()
    db.query(models.IncidentEvent).delete()
    db.query(models.Incident).delete()
    db.query(models.Event).delete()
    db.commit()
    return {"ok": True}


@router.get("/simulator/status")
def status():
    return simulator.status()
