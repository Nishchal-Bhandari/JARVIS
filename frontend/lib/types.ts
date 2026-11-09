// Types mirroring backend/app/schemas.py (agent.md §4.6).
export interface Metric { name: string; value: number }
export interface JarEvent {
  id: string; timestamp: string; source: string; service: string;
  host?: string | null; type: string; severity: string; message: string;
  metric?: Metric | null; user_id?: string | null; trace_id?: string | null;
  signature?: string | null; is_anomaly: boolean; attrs?: Record<string, unknown>;
}
export interface Alternative { service: string; confidence: number }
export interface RootCause {
  service: string; label: string; confidence: number;
  evidence: string[]; alternatives: Alternative[];
}
export interface Impact {
  affected_services: string[]; at_risk_services: string[];
  users_affected: number; failed_transactions: number; critical_path_hit: boolean;
}
export interface TimelineStage {
  t: string; offset_seconds: number; services: string[]; key_events: string[];
}
export interface Recommendation {
  priority: number; title: string; detail: string; risk: string; source: string;
}
export interface Incident {
  id: string; title: string; status: string; severity: string;
  started_at?: string | null; last_event_at?: string | null;
  root_cause_service?: string | null; root_cause_label?: string | null;
  confidence: number; user_impact: number; failed_txn_count: number; summary: string;
  root_cause?: RootCause | null; impact?: Impact | null;
  timeline: TimelineStage[]; recommendations: Recommendation[]; event_count: number;
}
export interface IncidentDetail extends Incident {
  events: JarEvent[];
  graph: { services: { id: string; kind: string; tier: number; critical: boolean }[];
           dependencies: { from: string; to: string }[] };
}
export interface Topology {
  services: { id: string; kind: string; tier: number; critical: boolean }[];
  dependencies: { from: string; to: string }[];
}
export interface Stats {
  open_incidents: number; total_events: number;
  affected_services: number; events_per_minute: number;
}
