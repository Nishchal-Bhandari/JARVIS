"use client";
import { useRef, useState } from "react";
import { api, API } from "@/lib/api";
import { Card, CardTitle } from "@/components/ui/card";
import { Button, GhostButton } from "@/components/ui/button";

const INJECT_SERVICES = ["postgres-primary", "redis-cache", "auth-service", "payment-service", "api-gateway", "order-service", "web-app", "notification-service", "cdn"];
const FAULTS = [
  { id: "pool_exhaustion", label: "Connection pool exhaustion" },
  { id: "cache_failure", label: "Cache failure" },
  { id: "deploy_failure", label: "Bad deploy" },
  { id: "oom", label: "Memory pressure / OOM" },
  { id: "latency", label: "Latency spike" },
];

export default function Sources() {
  const [result, setResult] = useState<{ accepted: number; rejected: number; errors: string[] } | null>(null);
  const [scenario, setScenario] = useState("db_pool_exhaustion");
  const [speed, setSpeed] = useState(5);
  const [simStatus, setSimStatus] = useState("");
  const [injectService, setInjectService] = useState("redis-cache");
  const [injectFault, setInjectFault] = useState("cache_failure");
  const [changeService, setChangeService] = useState("auth-service");
  const [changeType, setChangeType] = useState<"deploy" | "config">("deploy");
  const [changeDetail, setChangeDetail] = useState("v2.4.1");
  const [changeStatus, setChangeStatus] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  async function onFile(f: File) {
    const r = await api.upload(f);
    setResult(r);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Data sources</h1>
      <div className="grid gap-6 lg:grid-cols-3">
        <Card>
          <CardTitle>Upload a log file</CardTitle>
          <p className="mt-1 text-sm text-muted">JSONL, CSV or raw log. Max 20 MB. Bad lines are skipped and counted.</p>
          <input ref={fileRef} type="file" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) onFile(f); }} />
          <div className="mt-3 rounded-lg border border-dashed border-border p-6 text-center">
            <Button onClick={() => fileRef.current?.click()}>Choose file</Button>
          </div>
          {result && (
            <p className="mt-3 text-sm">{result.accepted} accepted · {result.rejected} skipped{result.errors.length ? `. ${result.errors[0]}` : ""}</p>
          )}
        </Card>
        <Card>
          <CardTitle>API ingest</CardTitle>
          <p className="mt-1 text-sm text-muted">Send events to the REST endpoint:</p>
          <pre className="mt-3 overflow-auto rounded bg-raised p-3 font-mono text-xs">{`curl -X POST ${API}/api/v1/events \\
  -H 'Content-Type: application/json' \\
  -d '[{"service":"payment-service","severity":"error","message":"timeout acquiring connection from pool"}]'`}</pre>
        </Card>
        <Card>
          <CardTitle>Simulator</CardTitle>
          <div className="mt-3 space-y-3">
            <label className="block text-sm">Scenario
              <select value={scenario} onChange={(e) => setScenario(e.target.value)} className="mt-1 w-full rounded-md border border-border bg-raised px-2 py-1">
                <option value="db_pool_exhaustion">db_pool_exhaustion</option>
                <option value="bad_deploy">bad_deploy</option>
                <option value="cache_failure">cache_failure</option>
              </select>
            </label>
            <div className="flex gap-2" role="group" aria-label="Speed">
              {[1, 5, 10].map((s) => (
                <button key={s} className={`rounded border px-3 py-1 text-sm ${speed === s ? "border-trace bg-trace-wash" : "border-border"}`} onClick={() => setSpeed(s)}>{s}×</button>
              ))}
            </div>
            <div className="flex gap-2">
              <Button onClick={async () => { await api.simulatorStart(scenario, speed); setSimStatus("Simulator started"); }}>Start simulator</Button>
              <GhostButton onClick={async () => { await api.simulatorStop(); setSimStatus("Simulator stopped"); }}>Stop</GhostButton>
              <GhostButton onClick={async () => { await api.simulatorReset(); setSimStatus("All data cleared"); }}>Reset</GhostButton>
            </div>
            {simStatus && <p className="text-sm text-muted">{simStatus}</p>}
          </div>
        </Card>
        <Card>
          <CardTitle>Break something</CardTitle>
          <p className="mt-1 text-sm text-muted">Judge&apos;s choice: pick a service and a fault. J.A.R.V.I.S. has to find it live — nothing is scripted per service.</p>
          <div className="mt-3 space-y-3">
            <label className="block text-sm">Service
              <select value={injectService} onChange={(e) => setInjectService(e.target.value)} className="mt-1 w-full rounded-md border border-border bg-raised px-2 py-1">
                {INJECT_SERVICES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </label>
            <label className="block text-sm">Fault
              <select value={injectFault} onChange={(e) => setInjectFault(e.target.value)} className="mt-1 w-full rounded-md border border-border bg-raised px-2 py-1">
                {FAULTS.map((f) => <option key={f.id} value={f.id}>{f.label}</option>)}
              </select>
            </label>
            <Button onClick={async () => { const r = await api.inject(injectService, injectFault); setSimStatus(r.started ? `Injected ${injectFault} into ${injectService} — watch Overview for the incident` : "Simulator already running"); }}>Break it</Button>
          </div>
        </Card>
        <Card>
          <CardTitle>Record a change</CardTitle>
          <p className="mt-1 text-sm text-muted">Log a deploy or config change. If errors follow within 10 minutes on that service or a neighbour, J.A.R.V.I.S. flags it as a suspect change.</p>
          <div className="mt-3 space-y-3">
            <label className="block text-sm">Service
              <select value={changeService} onChange={(e) => setChangeService(e.target.value)} className="mt-1 w-full rounded-md border border-border bg-raised px-2 py-1">
                {INJECT_SERVICES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </label>
            <label className="block text-sm">Type
              <select value={changeType} onChange={(e) => setChangeType(e.target.value as "deploy" | "config")} className="mt-1 w-full rounded-md border border-border bg-raised px-2 py-1">
                <option value="deploy">Deploy</option>
                <option value="config">Config change</option>
              </select>
            </label>
            <label className="block text-sm">Detail
              <input value={changeDetail} onChange={(e) => setChangeDetail(e.target.value)} className="mt-1 w-full rounded-md border border-border bg-raised px-2 py-1" placeholder="v2.4.1" />
            </label>
            <Button onClick={async () => { await api.recordChange(changeService, changeType, changeDetail); setChangeStatus(`Recorded ${changeType} on ${changeService}`); }}>Record change</Button>
            {changeStatus && <p className="text-sm text-muted">{changeStatus}</p>}
          </div>
        </Card>
      </div>
    </div>
  );
}
