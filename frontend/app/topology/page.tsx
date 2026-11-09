"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardTitle } from "@/components/ui/card";

export default function TopologyPage() {
  const topo = useQuery({ queryKey: ["topology"], queryFn: api.topology });
  if (topo.isLoading) return <p>Loading…</p>;
  if (topo.isError || !topo.data) return <p>Could not load topology.</p>;
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Topology</h1>
      <Card>
        <CardTitle>Services and dependencies</CardTitle>
        <p className="mt-1 text-sm text-muted">An edge A → B means A depends on B. Failures propagate from B to A.</p>
        <ul className="mt-3 space-y-1 text-sm">
          {topo.data.services.map((s) => (
            <li key={s.id} className="flex gap-2"><span className="font-mono">{s.id}</span><span className="text-muted">{s.kind} · tier {s.tier}{s.critical ? " · critical" : ""}</span></li>
          ))}
        </ul>
        <ul className="mt-4 space-y-1 font-mono text-xs text-muted">
          {topo.data.dependencies.map((d, i) => <li key={i}>{d.from} → {d.to}</li>)}
        </ul>
      </Card>
    </div>
  );
}
