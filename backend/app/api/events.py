"""POST /events, GET /events, POST /ingest/upload (specsheet §11, §5)."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, schemas
from ..core import engine as engine_mod
from ..core.normalizer import canonical, parse_upload
from ..db import get_db
from .broadcast import broadcast
from .helpers import store_event

router = APIRouter()


@router.post("/events")
def ingest_events(payload: list[schemas.EventIn] | schemas.EventIn, db: Session = Depends(get_db)):
    items = payload if isinstance(payload, list) else [payload]
    accepted = 0
    for item in items:
        ev = canonical(item.model_dump(exclude_none=False), source="api")
        store_event(db, ev)
        accepted += 1
        broadcast({"type": "event.ingested", "event_id": ev["id"]})
    engine_mod.tick(db, broadcast=broadcast)
    return {"accepted": accepted}


@router.post("/ingest/upload")
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.size and file.size > 20 * 1024 * 1024:
        raise HTTPException(413, "file too large (max 20 MB)")
    text = (await file.read()).decode("utf-8", errors="replace")
    events, errors = parse_upload(text, file.filename or "upload.log")
    for ev in events:
        store_event(db, ev)
    engine_mod.tick(db, broadcast=broadcast)
    return {"accepted": len(events), "rejected": len(errors), "errors": errors[:10]}


@router.get("/events", response_model=list[schemas.EventOut])
def list_events(
    service: str | None = None,
    severity: str | None = None,
    source: str | None = None,
    anomaly: bool | None = None,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    q = db.query(models.Event).order_by(models.Event.timestamp.desc())
    if service:
        q = q.filter(models.Event.service == service)
    if severity:
        q = q.filter(models.Event.severity == severity)
    if source:
        q = q.filter(models.Event.source == source)
    if anomaly is not None:
        q = q.filter(models.Event.is_anomaly == (1 if anomaly else 0))
    rows = q.limit(limit).all()
    return [
        schemas.EventOut(
            id=r.id,
            timestamp=r.timestamp,
            source=r.source,
            service=r.service,
            host=r.host,
            type=r.type,
            severity=r.severity,
            message=r.message,
            metric=r.metric,
            user_id=r.user_id,
            trace_id=r.trace_id,
            signature=r.signature,
            is_anomaly=bool(r.is_anomaly),
            attrs=r.attrs or {},
        )
        for r in rows
    ]
