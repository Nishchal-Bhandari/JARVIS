"""Engine tick: detect -> correlate -> analyse -> persist -> broadcast.
Only engine.py and api/* touch the DB (agent.md §4)."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from . import anomaly, correlation, recommend, rootcause, severity, timeline
from . import impact as impact_mod
from .anomaly import load_rules


def load_topology(db: Session):
    services = [
        {"id": s.id, "kind": s.kind, "tier": s.tier, "critical": bool(s.critical)}
        for s in db.query(models.Service).all()
    ]
    deps = [{"from": d.from_service, "to": d.to_service} for d in db.query(models.Dependency).all()]
    return {"services": services, "dependencies": deps}


def event_to_dict(ev: models.Event) -> dict:
    return {
        "id": ev.id,
        "timestamp": ev.timestamp,
        "source": ev.source,
        "service": ev.service,
        "host": ev.host,
        "type": ev.type,
        "severity": ev.severity,
        "message": ev.message,
        "metric": ev.metric,
        "user_id": ev.user_id,
        "trace_id": ev.trace_id,
        "signature": ev.signature,
        "attrs": ev.attrs or {},
    }


def analyse_cluster(cluster, topology, rules):
    rc = rootcause.score_root_cause(cluster, topology["dependencies"], rules)
    imp = impact_mod.compute_impact(cluster, topology["dependencies"], topology)
    sev = severity.compute_severity(imp)
    tl = timeline.build_timeline(cluster, topology["dependencies"])
    recs = recommend.recommendations_for(rc, rules)
    services = sorted({e["service"] for e in cluster})
    title = f"{rc['label']} — {rc['service']}" if rc else "Incident"
    summary = (
        f"{len(cluster)} anomalous events across {len(services)} services. "
        f"Most likely cause: {rc['service']} ({rc['label']}), "
        f"confidence {rc['confidence']}. {imp['users_affected']} users affected, "
        f"{imp['failed_transactions']} failed transactions."
    )
    return {
        "root_cause": rc,
        "impact": imp,
        "severity": sev,
        "timeline": tl,
        "recommendations": recs,
        "title": title,
        "summary": summary,
    }


def tick(db: Session, broadcast=None):
    """One correlation tick over the sliding window. Returns incident ids created/updated."""
    topology = load_topology(db)
    rules = load_rules()
    cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=settings.window_minutes)
    rows = (
        db.query(models.Event)
        .filter(models.Event.timestamp >= cutoff)
        .order_by(models.Event.timestamp)
        .all()
    )
    # tag anomalies in-memory (signature + severity); persist is_anomaly flag
    events = []
    for row in rows:
        d = event_to_dict(row)
        sig, _ = anomaly.tag_signature(d.get("message", ""), rules)
        if sig and not d.get("signature"):
            d["signature"] = sig
            row.signature = sig
        d["is_anomaly"] = anomaly.is_anomaly(d, rules=rules)
        row.is_anomaly = 1 if d["is_anomaly"] else 0
        if d["is_anomaly"]:
            events.append(d)
    db.commit()
    clusters = correlation.cluster_events(
        events, topology["dependencies"], threshold=settings.correlation_threshold
    )
    open_incidents = db.query(models.Incident).filter(models.Incident.status != "resolved").all()
    changed = []
    for cluster in clusters:
        services = {e["service"] for e in cluster}
        # Merge into an existing open incident when >=50% of the smaller
        # service set overlaps (either direction), so an early single-service
        # postgres cluster merges into the full incident instead of lingering.
        target = None
        for inc in open_incidents:
            inc_services = {s for s in (inc.impact or {}).get("affected_services", [])}
            if (
                inc_services
                and len(services & inc_services) / min(len(services), len(inc_services)) >= 0.5
            ):
                target = inc
                break
        analysis = analyse_cluster(cluster, topology, rules)
        started = min(e["timestamp"] for e in cluster)
        last = max(e["timestamp"] for e in cluster)
        if target is None:
            target = models.Incident(id=f"inc_{uuid.uuid4().hex[:10]}")
            db.add(target)
        target.title = analysis["title"]
        target.severity = analysis["severity"]
        target.started_at = started
        target.last_event_at = last
        target.root_cause_service = analysis["root_cause"]["service"]
        target.root_cause_label = analysis["root_cause"]["label"]
        target.confidence = analysis["root_cause"]["confidence"]
        target.user_impact = analysis["impact"]["users_affected"]
        target.failed_txn_count = analysis["impact"]["failed_transactions"]
        target.summary = analysis["summary"]
        target.root_cause = analysis["root_cause"]
        target.impact = analysis["impact"]
        # timeline datetimes -> ISO for JSON storage
        target.timeline = [{**s, "t": s["t"].isoformat()} for s in analysis["timeline"]]
        target.recommendations = analysis["recommendations"]
        db.flush()
        db.query(models.IncidentEvent).filter(
            models.IncidentEvent.incident_id == target.id
        ).delete()
        for e in cluster:
            db.add(models.IncidentEvent(incident_id=target.id, event_id=e["id"]))
        changed.append(target.id)
        if broadcast:
            broadcast({"type": "incident.updated", "incident_id": target.id})
    # Auto-resolve open incidents quiet for 5 minutes.
    quiet_cutoff = datetime.now(UTC) - timedelta(minutes=5)
    for inc in open_incidents:
        # SQLite returns naive datetimes; treat them as UTC.
        last = inc.last_event_at
        if last is not None and last.tzinfo is None:
            last = last.replace(tzinfo=UTC)
        if last and last < quiet_cutoff and inc.id not in changed:
            inc.status = "resolved"
    db.commit()
    return changed
