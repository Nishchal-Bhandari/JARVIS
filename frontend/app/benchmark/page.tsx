"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { Card, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface Row {
  service: string; fault_type: string; seed: number; expected: string;
  found: string | null; correct: boolean; time_to_detect_s: number | null; events: number;
}
interface Result {
  total_runs: number; correct: number; accuracy_pct: number;
  avg_time_to_detect_s: number | null; misses: Row[]; rows: Row[];
}

export default function Benchmark() {
  const [result, setResult] = useState<Result | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    setRunning(true);
    setError("");
    try {
      setResult(await api.runBenchmark());
    } catch {
      setError("Benchmark run failed — is the API running?");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Benchmark</h1>
      <p className="text-sm text-muted">
        The fault injector runs every service × every fault type, 5 seeds each (225 runs).
        Top-1 root-cause accuracy and time to detect are measured from the engine alone —
        misses are listed, never hidden. Time to detect is scenario time, from the first
        anomalous event until the engine first names the injected service.
      </p>
      <Button onClick={run} disabled={running}>{running ? "Running…" : "Run benchmark"}</Button>
      {error && <p className="text-sm text-cause">{error}</p>}
      {result && (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <Card><div className="tabular text-3xl font-bold">{result.accuracy_pct}%</div><div className="text-sm text-muted">top-1 accuracy</div></Card>
            <Card><div className="tabular text-3xl font-bold">{result.correct}/{result.total_runs}</div><div className="text-sm text-muted">correct runs</div></Card>
            <Card><div className="tabular text-3xl font-bold">{result.avg_time_to_detect_s ?? "—"}s</div><div className="text-sm text-muted">avg time to detect</div></Card>
            <Card><div className="tabular text-3xl font-bold">{result.misses.length}</div><div className="text-sm text-muted">misses</div></Card>
          </div>
          {result.misses.length > 0 && (
            <Card>
              <CardTitle>Misses</CardTitle>
              <ul className="mt-2 space-y-1 text-sm">
                {result.misses.map((m, i) => (
                  <li key={i} className="text-cause">{m.service} × {m.fault_type} (seed {m.seed}) — found {m.found ?? "nothing"}</li>
                ))}
              </ul>
            </Card>
          )}
          <Card>
            <CardTitle>All runs</CardTitle>
            <div className="mt-3 max-h-96 overflow-auto">
              <table className="w-full text-sm">
                <thead><tr className="text-left text-muted"><th className="py-1">Service</th><th>Fault</th><th>Seed</th><th>Found</th><th>Correct</th><th>Detect (s)</th></tr></thead>
                <tbody>
                  {result.rows.map((r, i) => (
                    <tr key={i} className={`border-t border-border ${r.correct ? "" : "text-cause"}`}>
                      <td className="py-1 font-mono">{r.service}</td>
                      <td>{r.fault_type}</td>
                      <td className="tabular">{r.seed}</td>
                      <td className="font-mono">{r.found ?? "—"}</td>
                      <td>{r.correct ? "✓" : "✗"}</td>
                      <td className="tabular">{r.time_to_detect_s ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          <p className="text-xs text-muted">
            Honest scope: this measures the engine on injected cascades built from the
            topology graph, not on wild production logs. A 100% here means the engine
            is consistent on this matrix — re-run it after any scoring change.
          </p>
        </>
      )}
    </div>
  );
}
