"""Incidents, report, ask, topology, stats (specsheet §11)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..core import copilot
from ..core import report as report_mod
from ..db import get_db

router = APIRouter()


def _out(inc: models.Incident, event_count: int = 0):
    return schemas.IncidentOut(
        id=inc.id,
        title=inc.title,
        status=inc.status,
        severity=inc.severity,
        started_at=inc.started_at,
        last_event_at=inc.last_event_at,
        root_cause_service=inc.root_cause_service,
        root_cause_label=inc.root_cause_label,
        confidence=inc.confidence,
        user_impact=inc.user_impact,
        failed_txn_count=inc.failed_txn_count,
        summary=inc.summary,
        root_cause=inc.root_cause,
        impact=inc.impact,
        timeline=inc.timeline or [],
        recommendations=inc.recommendations or [],
        event_count=event_count,
    )


@router.get("/incidents", response_model=list[schemas.IncidentOut])
def list_incidents(
    status: str | None = None, severity: str | None = None, db: Session = Depends(get_db)
):
    q = db.query(models.Incident).order_by(models.Incident.started_at.desc())
    if status:
        q = q.filter(models.Incident.status == status)
    if severity:
        q = q.filter(models.Incident.severity == severity)
    out = []
    for inc in q.all():
        n = (
            db.query(models.IncidentEvent)
            .filter(models.IncidentEvent.incident_id == inc.id)
            .count()
        )
        out.append(_out(inc, n))
    return out


@router.get("/incidents/{incident_id}", response_model=schemas.IncidentDetail)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(models.Incident).get(incident_id)
    if not inc:
        raise HTTPException(404, "incident not found")
    links = (
        db.query(models.IncidentEvent).filter(models.IncidentEvent.incident_id == incident_id).all()
    )
    ids = [l.event_id for l in links]
    rows = (
        db.query(models.Event)
        .filter(models.Event.id.in_(ids))
        .order_by(models.Event.timestamp)
        .all()
        if ids
        else []
    )
    services = db.query(models.Service).all()
    deps = db.query(models.Dependency).all()
    detail = _out(inc, len(rows))
    return schemas.IncidentDetail(
        **detail.model_dump(),
        events=[
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
        ],
        graph={
            "services": [
                {"id": s.id, "kind": s.kind, "tier": s.tier, "critical": bool(s.critical)}
                for s in services
            ],
            "dependencies": [{"from": d.from_service, "to": d.to_service} for d in deps],
        },
    )


@router.patch("/incidents/{incident_id}")
def update_incident(incident_id: str, payload: dict, db: Session = Depends(get_db)):
    inc = db.query(models.Incident).get(incident_id)
    if not inc:
        raise HTTPException(404, "incident not found")
    if "status" in payload:
        inc.status = payload["status"]
    db.commit()
    return {"id": inc.id, "status": inc.status}


@router.get("/incidents/{incident_id}/report")
def get_report(incident_id: str, format: str = "md", db: Session = Depends(get_db)):
    inc = db.query(models.Incident).get(incident_id)
    if not inc:
        raise HTTPException(404, "incident not found")
    data = {
        "title": inc.title,
        "severity": inc.severity,
        "summary": inc.summary,
        "root_cause": inc.root_cause,
        "impact": inc.impact,
        "timeline": inc.timeline or [],
        "recommendations": inc.recommendations or [],
    }
    md, by = report_mod.generate_report(data)
    if format == "json":
        return {"markdown": md, "generated_by": by}
    return {"markdown": md, "generated_by": by}


@router.post("/incidents/{incident_id}/report/regenerate")
def regenerate_report(incident_id: str, db: Session = Depends(get_db)):
    return get_report(incident_id, db=db)


@router.post("/incidents/{incident_id}/ask")
def ask(incident_id: str, payload: schemas.AskIn, db: Session = Depends(get_db)):
    inc = db.query(models.Incident).get(incident_id)
    if not inc:
        raise HTTPException(404, "incident not found")
    data = {
        "title": inc.title,
        "severity": inc.severity,
        "summary": inc.summary,
        "root_cause": inc.root_cause,
        "impact": inc.impact,
        "timeline": inc.timeline or [],
        "recommendations": inc.recommendations or [],
    }
    return copilot.answer_question(data, payload.question)


@router.get("/topology")
def get_topology(db: Session = Depends(get_db)):
    services = db.query(models.Service).all()
    deps = db.query(models.Dependency).all()
    return {
        "services": [
            {"id": s.id, "kind": s.kind, "tier": s.tier, "critical": bool(s.critical)}
            for s in services
        ],
        "dependencies": [{"from": d.from_service, "to": d.to_service} for d in deps],
    }


@router.put("/topology")
def put_topology(payload: dict, db: Session = Depends(get_db)):
    db.query(models.Dependency).delete()
    db.query(models.Service).delete()
    for s in payload.get("services", []):
        db.add(
            models.Service(
                id=s["id"],
                kind=s.get("kind", "service"),
                tier=s.get("tier", 2),
                critical=1 if s.get("critical") else 0,
            )
        )
    for d in payload.get("dependencies", []):
        db.add(models.Dependency(from_service=d["from"], to_service=d["to"]))
    db.commit()
    return {"ok": True}


@router.get("/stats/overview")
def stats(db: Session = Depends(get_db)):
    open_n = db.query(models.Incident).filter(models.Incident.status != "resolved").count()
    total_incidents = db.query(models.Incident).count()
    total_events = db.query(models.Event).count()
    affected = set()
    for inc in db.query(models.Incident).filter(models.Incident.status != "resolved").all():
        affected.update((inc.impact or {}).get("affected_services", []))
    # Noise reduction: how much of the alert stream collapsed into incidents.
    # 87 alerts -> 2 incidents = 97.7% of alerts were symptoms, not new problems.
    noise_pct = round((1 - total_incidents / total_events) * 100, 1) if total_events else 0.0
    return {
        "open_incidents": open_n,
        "total_incidents": total_incidents,
        "total_events": total_events,
        "affected_services": len(affected),
        "events_per_minute": total_events,
        "noise_reduction_pct": noise_pct,
    }
