"use client";
import { useMemo, useState } from "react";
import { Background, Controls, Edge, Node, ReactFlow } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { IncidentDetail } from "@/lib/types";

export function CausalGraph({ incident }: { incident: IncidentDetail }) {
  const [listView, setListView] = useState(false);
  const { nodes, edges } = useMemo(() => {
    const services = incident.graph?.services || [];
    const deps = incident.graph?.dependencies || [];
    const affected = new Set(incident.impact?.affected_services || []);
    const atRisk = new Set(incident.impact?.at_risk_services || []);
    const root = incident.root_cause_service;
    const byTier = new Map<number, typeof services>();
    services.forEach((s) => {
      const arr = byTier.get(s.tier) || [];
      arr.push(s);
      byTier.set(s.tier, arr);
    });
    const nodes: Node[] = [];
    byTier.forEach((list, tier) => {
      list.forEach((s, i) => {
        const isRoot = s.id === root;
        const isAffected = affected.has(s.id);
        const border = isRoot ? "3px solid var(--cause)" : isAffected ? "2px solid var(--affected)" : atRisk.has(s.id) ? "2px dashed var(--affected)" : "1px solid var(--border)";
        nodes.push({
          id: s.id,
          position: { x: tier * 220, y: i * 90 },
          data: { label: `${s.id}${isRoot ? " ★ root cause" : isAffected ? " · affected" : atRisk.has(s.id) ? " · at risk" : ""}` },
          style: { width: 180, border, borderRadius: 8, padding: 10, background: isRoot ? "var(--cause-wash)" : "var(--card)", color: "var(--foreground)", fontSize: 12 },
          className: isRoot ? "cause-pulse" : undefined,
        });
      });
    });
    const edges: Edge[] = deps
      .filter((d) => affected.has(d.from) || affected.has(d.to))
      .map((d) => ({
        id: `${d.from}-${d.to}`,
        source: d.to, target: d.from, animated: true,
        label: d.to === root ? "propagates" : undefined,
        style: { stroke: d.to === root ? "var(--trace)" : "var(--border)", strokeWidth: d.to === root ? 2.5 : 1.5 },
      }));
    return { nodes, edges };
  }, [incident]);

  if (listView) {
    return (
      <div>
        <button className="mb-2 rounded border border-border px-2 py-1 text-xs" onClick={() => setListView(false)}>View as graph</button>
        <ul className="space-y-1 text-sm">
          {(incident.impact?.affected_services || []).map((s) => (
            <li key={s} aria-label={`${s}, affected`}>{s === incident.root_cause_service ? "★ " : ""}{s} — {s === incident.root_cause_service ? "root cause" : "affected"}</li>
          ))}
        </ul>
      </div>
    );
  }
  return (
    <div>
      <button className="mb-2 rounded border border-border px-2 py-1 text-xs" onClick={() => setListView(true)}>View as list</button>
      <div style={{ height: 320 }} className="rounded-lg border border-border bg-card">
        <ReactFlow nodes={nodes} edges={edges} fitView>
          <Background />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  );
}
