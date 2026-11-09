"""Pydantic contracts (specsheet §5, §7, §11). Mirrored in frontend/lib/types.ts."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Metric(BaseModel):
    name: str
    value: float


class EventIn(BaseModel):
    id: str | None = None
    timestamp: datetime | None = None
    source: str = "api"
    service: str
    host: str | None = None
    type: str = "log"
    severity: str | None = None
    message: str | None = None
    metric: Metric | None = None
    user_id: str | None = None
    trace_id: str | None = None
    signature: str | None = None
    attrs: dict[str, Any] = Field(default_factory=dict)


class EventOut(BaseModel):
    id: str
    timestamp: datetime
    source: str
    service: str
    host: str | None = None
    type: str
    severity: str
    message: str
    metric: dict | None = None
    user_id: str | None = None
    trace_id: str | None = None
    signature: str | None = None
    is_anomaly: bool
    attrs: dict = Field(default_factory=dict)


class Alternative(BaseModel):
    service: str
    confidence: float
    score: float = 0.0
    factors: dict = Field(default_factory=dict)
    why_not: list[str] = Field(default_factory=list)


class RootCause(BaseModel):
    service: str
    label: str
    confidence: float
    evidence: list[str]
    alternatives: list[Alternative] = Field(default_factory=list)
    suspect_change: dict | None = None


class Impact(BaseModel):
    affected_services: list[str] = Field(default_factory=list)
    at_risk_services: list[str] = Field(default_factory=list)
    users_affected: int = 0
    failed_transactions: int = 0
    critical_path_hit: bool = False
    # Estimate only: failed_transactions x avg_order_value_inr (assumption, shown in UI).
    estimated_revenue_impact_inr: int = 0
    avg_order_value_inr: int = 500


class TimelineStage(BaseModel):
    t: datetime
    offset_seconds: float
    services: list[str] = Field(default_factory=list)
    key_events: list[str] = Field(default_factory=list)
    marker: bool = False


class Recommendation(BaseModel):
    priority: int
    title: str
    detail: str
    risk: str = "low"
    source: str = "rule"


class IncidentOut(BaseModel):
    id: str
    title: str
    status: str
    severity: str
    started_at: datetime | None = None
    last_event_at: datetime | None = None
    root_cause_service: str | None = None
    root_cause_label: str | None = None
    confidence: float = 0.0
    user_impact: int = 0
    failed_txn_count: int = 0
    summary: str = ""
    root_cause: RootCause | None = None
    impact: Impact | None = None
    timeline: list[TimelineStage] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    event_count: int = 0


class IncidentDetail(IncidentOut):
    events: list[EventOut] = Field(default_factory=list)
    graph: dict = Field(default_factory=dict)


class UploadResult(BaseModel):
    accepted: int
    rejected: int
    errors: list[str] = Field(default_factory=list)


class SimulatorStart(BaseModel):
    scenario: str = "db_pool_exhaustion"
    speed: float = 1.0


class InjectIn(BaseModel):
    service: str
    fault_type: str
    seed: int = 42
    speed: float = 10.0


class AskIn(BaseModel):
    question: str
