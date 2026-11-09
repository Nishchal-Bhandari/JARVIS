"""Shared ingest helper: canonical dict -> DB row, auto-add unmapped services."""

from sqlalchemy.orm import Session

from .. import models
from ..core import anomaly
from ..core.anomaly import load_rules


def store_event(db: Session, ev: dict) -> models.Event:
    if db.query(models.Service).get(ev["service"]) is None:
        db.add(models.Service(id=ev["service"], kind="service", tier=2, critical=0))
    sig, _ = anomaly.tag_signature(ev.get("message", ""), load_rules())
    if sig and not ev.get("signature"):
        ev["signature"] = sig
    row = db.query(models.Event).get(ev["id"])
    if row is None:
        row = models.Event(
            id=ev["id"],
            timestamp=ev["timestamp"],
            source=ev.get("source", "api"),
            service=ev["service"],
            host=ev.get("host"),
            type=ev.get("type", "log"),
            severity=ev.get("severity", "info"),
            message=ev.get("message", ""),
            metric=ev.get("metric"),
            user_id=ev.get("user_id"),
            trace_id=ev.get("trace_id"),
            signature=ev.get("signature"),
            is_anomaly=1 if anomaly.is_anomaly(ev) else 0,
            attrs=ev.get("attrs") or {},
        )
        db.add(row)
    db.commit()
    return row
