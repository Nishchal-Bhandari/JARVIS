"""Simulator endpoints (specsheet §11, §13) + fault injector (chaos button)."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..core import engine as engine_mod
from ..db import get_db
from ..simulator import injector as injector_mod
from ..simulator.runner import simulator
from .broadcast import broadcast
from .helpers import store_event

router = APIRouter()


def _ingest_callbacks():
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

    return ingest, on_done


@router.post("/simulator/start")
async def start(payload: schemas.SimulatorStart, db: Session = Depends(get_db)):
    ingest, on_done = _ingest_callbacks()
    ok = await simulator.start(
        payload.scenario, payload.speed, ingest, broadcast=broadcast, on_done=on_done
    )
    return {"started": ok, "scenario": payload.scenario, "speed": payload.speed}


@router.post("/simulator/inject")
async def inject(payload: schemas.InjectIn, db: Session = Depends(get_db)):
    """Chaos button: inject a fault into a service and let the engine find it.
    Nothing is scripted per service — the injector builds the cascade from
    the topology graph, and the engine must identify the injected service."""
    from ..core.engine import load_topology

    topology = load_topology(db)
    try:
        events = injector_mod.generate_injected_events(
            payload.service,
            payload.fault_type,
            seed=payload.seed,
            base=datetime.now(UTC),
            topology=topology,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    ingest, on_done = _ingest_callbacks()
    scenario = f"injected:{payload.service}:{payload.fault_type}"
    ok = await simulator.start_events(
        events, scenario, payload.speed, ingest, broadcast=broadcast, on_done=on_done
    )
    return {
        "started": ok,
        "scenario": scenario,
        "service": payload.service,
        "fault_type": payload.fault_type,
        "seed": payload.seed,
        "speed": payload.speed,
        "events": len(events),
    }


@router.get("/simulator/faults")
def faults():
    return {"fault_types": [{"id": f, "label": v["label"]} for f, v in injector_mod.FAULTS.items()]}


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
