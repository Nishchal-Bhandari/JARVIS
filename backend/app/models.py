"""SQLAlchemy models (specsheet §5.4). JSON columns hold structured analysis."""

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text

from .db import Base


class Event(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    source = Column(String, default="api")
    service = Column(String, nullable=False, index=True)
    host = Column(String, nullable=True)
    type = Column(String, default="log")
    severity = Column(String, default="info")
    message = Column(Text, default="")
    metric = Column(JSON, nullable=True)
    user_id = Column(String, nullable=True)
    trace_id = Column(String, nullable=True)
    signature = Column(String, nullable=True)
    is_anomaly = Column(Integer, default=0)
    attrs = Column(JSON, default=dict)


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True)
    title = Column(String, default="")
    status = Column(String, default="open")
    severity = Column(String, default="P4")
    started_at = Column(DateTime, nullable=True)
    last_event_at = Column(DateTime, nullable=True)
    root_cause_service = Column(String, nullable=True)
    root_cause_label = Column(String, nullable=True)
    confidence = Column(Float, default=0.0)
    user_impact = Column(Integer, default=0)
    failed_txn_count = Column(Integer, default=0)
    summary = Column(Text, default="")
    root_cause = Column(JSON, default=dict)
    impact = Column(JSON, default=dict)
    timeline = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)


class IncidentEvent(Base):
    __tablename__ = "incident_events"
    incident_id = Column(String, ForeignKey("incidents.id"), primary_key=True)
    event_id = Column(String, ForeignKey("events.id"), primary_key=True)


class Service(Base):
    __tablename__ = "services"
    id = Column(String, primary_key=True)
    kind = Column(String, default="service")
    tier = Column(Integer, default=2)
    critical = Column(Integer, default=0)


class Dependency(Base):
    __tablename__ = "dependencies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_service = Column(String, nullable=False)
    to_service = Column(String, nullable=False)
