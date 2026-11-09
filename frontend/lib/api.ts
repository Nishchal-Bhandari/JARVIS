import type { Incident, IncidentDetail, JarEvent, Stats, Topology } from "./types";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}/api/v1${path}`);
  if (!res.ok) throw new Error(`API ${res.status} on ${path}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => fetch(`${API}/health`).then((r) => r.json()),
  incidents: () => get<Incident[]>("/incidents"),
  incident: (id: string) => get<IncidentDetail>(`/incidents/${id}`),
  events: (limit = 100) => get<JarEvent[]>(`/events?limit=${limit}`),
  topology: () => get<Topology>("/topology"),
  stats: () => get<Stats>("/stats/overview"),
  report: (id: string) =>
    get<{ markdown: string; generated_by: string }>(`/incidents/${id}/report`),
  whatif: (id: string, fixAt: number) =>
    get<{
      fix_at_seconds: number; avoided_users: number; avoided_failed_transactions: number;
      avoided_revenue_inr: number; total_users: number; total_failed_transactions: number;
      avg_order_value_inr: number; duration_seconds: number; note: string;
    }>(`/incidents/${id}/whatif?fix_at=${fixAt}`),
  regenerateReport: (id: string) =>
    fetch(`${API}/api/v1/incidents/${id}/report/regenerate`, { method: "POST" }).then((r) => r.json()),
  ask: (id: string, question: string) =>
    fetch(`${API}/api/v1/incidents/${id}/ask`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }).then((r) => r.json()),
  upload: async (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(`${API}/api/v1/ingest/upload`, { method: "POST", body: fd });
    return res.json();
  },
  simulatorStart: (scenario: string, speed: number) =>
    fetch(`${API}/api/v1/simulator/start`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario, speed }),
    }).then((r) => r.json()),
  simulatorStop: () =>
    fetch(`${API}/api/v1/simulator/stop`, { method: "POST" }).then((r) => r.json()),
  simulatorReset: () =>
    fetch(`${API}/api/v1/simulator/reset`, { method: "POST" }).then((r) => r.json()),
  simulatorStatus: () => get<{ running: boolean; scenario: string; progress: number; total: number }>("/simulator/status"),
  recordChange: (service: string, changeType: "deploy" | "config", detail: string) =>
    fetch(`${API}/api/v1/events`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify([{
        service, type: changeType, severity: "info",
        message: changeType === "deploy" ? `deploy ${detail} started` : `config change: ${detail}`,
      }]),
    }).then((r) => r.json()),
  runBenchmark: (seeds: number[] = [42, 43, 44, 45, 46]) =>
    fetch(`${API}/api/v1/benchmark/run`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seeds }),
    }).then((r) => r.json()),
  benchmarkLatest: () => get<{ total_runs: number; correct: number; accuracy_pct: number; avg_time_to_detect_s: number | null; misses: unknown[]; rows: unknown[] }>("/benchmark/latest"),
  inject: (service: string, faultType: string, seed = 42, speed = 10) =>
    fetch(`${API}/api/v1/simulator/inject`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ service, fault_type: faultType, seed, speed }),
    }).then((r) => r.json()),
  patchIncident: (id: string, status: string) =>
    fetch(`${API}/api/v1/incidents/${id}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }).then((r) => r.json()),
};
export { API };
