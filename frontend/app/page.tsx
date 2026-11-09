"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardTitle } from "@/components/ui/card";
import { SeverityPill } from "@/components/jarvis/SeverityPill";
import { fmtTime } from "@/lib/format";

export default function Overview() {
  const stats = useQuery({ queryKey: ["stats"], queryFn: api.stats });
  const incidents = useQuery({ queryKey: ["incidents"], queryFn: api.incidents });
  const events = useQuery({ queryKey: ["events"], queryFn: () => api.events(20) });

  if (incidents.isLoading) return <p>Loading…</p>;
  if (incidents.isError) return <p>Could not load incidents. <button className="underline" onClick={() => incidents.refetch()}>Retry</button></p>;

  const list = incidents.data || [];
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Overview</h1>
      {(stats.data?.total_events ?? 0) > 0 && (stats.data?.total_incidents ?? 0) > 0 && (
        <Card>
          <p className="text-lg">
            <span className="tabular font-bold">{stats.data!.total_events} alerts</span>
            {" → "}
            <span className="tabular font-bold">{stats.data!.total_incidents} incidents</span>
            {" — "}
            <span className="font-bold text-accent">{stats.data!.noise_reduction_pct}% noise reduced</span>
          </p>
          <p className="mt-1 text-sm text-muted">
            Most alerts were symptoms of the same underlying problem, not new problems.
          </p>
        </Card>
      )}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card><div className="tabular text-3xl font-bold">{stats.data?.open_incidents ?? "—"}</div><div className="text-sm text-muted">open incidents</div></Card>
        <Card><div className="tabular text-3xl font-bold">{stats.data?.affected_services ?? "—"}</div><div className="text-sm text-muted">services affected</div></Card>
        <Card><div className="tabular text-3xl font-bold">{stats.data?.total_events ?? "—"}</div><div className="text-sm text-muted">events ingested</div></Card>
        <Card><div className="tabular text-3xl font-bold">{list[0] ? `${Math.round(list[0].confidence * 100)}%` : "—"}</div><div className="text-sm text-muted">top root-cause confidence</div></Card>
      </div>

      {list.length === 0 ? (
        <Card>
          <p className="font-medium">No incidents yet. Start the simulator or upload a log file.</p>
          <div className="mt-3 flex gap-2">
            <Link href="/sources" className="rounded-md bg-accent px-4 py-2 text-sm text-white">Go to Sources</Link>
          </div>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardTitle>Incidents</CardTitle>
            <ul className="mt-3 space-y-2">
              {list.map((inc) => (
                <li key={inc.id} className="rounded-lg border border-border border-l-4 p-3" style={{ borderLeftColor: inc.severity === "P1" ? "var(--cause)" : inc.severity === "P4" ? "var(--unmapped)" : "var(--affected)" }}>
                  <Link href={`/incidents/${inc.id}`} className="block focus:outline-none focus:ring-2 focus:ring-trace">
                    <span className="flex items-center gap-2"><SeverityPill severity={inc.severity} /><span className="font-medium">{inc.title}</span></span>
                    <span className="mt-1 block text-sm text-muted">{inc.impact?.affected_services.length || 0} services · {inc.user_impact} users · started {fmtTime(inc.started_at)}</span>
                    <span className="mt-1 block font-mono text-xs text-muted">Root cause: {inc.root_cause_service || "unknown"}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </Card>
          <Card>
            <CardTitle>Live events</CardTitle>
            <ul className="mt-3 space-y-1 font-mono text-xs">
              {(events.data || []).slice(0, 12).map((e) => (
                <li key={e.id} className="flex gap-2"><span className="tabular text-muted">{fmtTime(e.timestamp)}</span><span>{e.service}</span><span className="truncate">{e.message}</span></li>
              ))}
            </ul>
          </Card>
        </div>
      )}
    </div>
  );
}
