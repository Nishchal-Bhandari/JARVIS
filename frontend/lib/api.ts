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
  patchIncident: (id: string, status: string) =>
    fetch(`${API}/api/v1/incidents/${id}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }).then((r) => r.json()),
};
export { API };
