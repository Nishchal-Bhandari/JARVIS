"use client";
import { useState } from "react";
import { useStream } from "@/store/stream";
import { api } from "@/lib/api";

export function TopBar() {
  const connected = useStream((s) => s.connected);
  const [running, setRunning] = useState(false);
  const [scenario, setScenario] = useState("db_pool_exhaustion");

  async function toggle() {
    if (running) { await api.simulatorStop(); setRunning(false); }
    else { await api.simulatorStart(scenario, 5); setRunning(true); }
  }

  return (
    <header className="flex flex-wrap items-center gap-4 border-b border-border bg-card px-6 py-3">
      <span className="text-sm font-semibold">J.A.R.V.I.S.</span>
      <span aria-live="polite" className={`inline-flex items-center gap-1 text-xs ${connected ? "text-steady" : "text-affected-ink"}`}>
        <span aria-hidden>●</span> {connected ? "Live" : "Reconnecting…"}
      </span>
      {!connected && <span className="rounded bg-affected-wash px-2 py-1 text-xs text-affected-ink">Live updates paused. Reconnecting…</span>}
      <div className="ml-auto flex items-center gap-2">
        <label className="sr-only" htmlFor="scenario">Scenario</label>
        <select id="scenario" value={scenario} onChange={(e) => setScenario(e.target.value)} className="rounded-md border border-border bg-raised px-2 py-1 text-sm">
          <option value="db_pool_exhaustion">db_pool_exhaustion</option>
          <option value="bad_deploy">bad_deploy</option>
          <option value="cache_failure">cache_failure</option>
        </select>
        <button onClick={toggle} className="rounded-md bg-accent px-3 py-1 text-sm text-white">{running ? "Stop simulator" : "Start simulator"}</button>
      </div>
    </header>
  );
}
