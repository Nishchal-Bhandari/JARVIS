"use client";
import { use, useState } from "react";
import dynamic from "next/dynamic";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardTitle } from "@/components/ui/card";
import { SeverityPill } from "@/components/jarvis/SeverityPill";
import { RootCausePanel } from "@/components/jarvis/RootCausePanel";
import { ImpactCard } from "@/components/jarvis/ImpactCard";
import { RecommendationItem } from "@/components/jarvis/RecommendationItem";
import { Timeline } from "@/components/jarvis/Timeline";
import { EventTable } from "@/components/jarvis/EventTable";
import { CopilotPanel } from "@/components/jarvis/CopilotPanel";
import { WhatIfCard } from "@/components/jarvis/WhatIfCard";
import { fmtDuration, fmtTime } from "@/lib/format";

const CausalGraph = dynamic(() => import("@/components/jarvis/CausalGraph").then((m) => m.CausalGraph), { ssr: false });

export default function IncidentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [tab, setTab] = useState<"events" | "report">("events");
  const [report, setReport] = useState<{ markdown: string; generated_by: string } | null>(null);
  const inc = useQuery({ queryKey: ["incidents", id], queryFn: () => api.incident(id) });

  if (inc.isLoading) return <p>Loading incident…</p>;
  if (inc.isError || !inc.data) return <p>Incident not found. <button className="underline" onClick={() => inc.refetch()}>Retry</button></p>;
  const d = inc.data;

  async function loadReport(regen = false) {
    const r = regen ? await api.regenerateReport(id) : await api.report(id);
    setReport(r);
  }

  return (
    <div className="space-y-6" aria-live="polite">
      <div className="flex flex-wrap items-center gap-3">
        <SeverityPill severity={d.severity} />
        <h1 className="text-xl font-bold">{d.title}</h1>
        <span className="text-sm text-muted">{d.status} · started {fmtTime(d.started_at)} · {fmtDuration(d.started_at, d.last_event_at)}</span>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {d.root_cause && <RootCausePanel rootCause={d.root_cause} />}
          <Card>
            <CardTitle>Causal graph</CardTitle>
            <div className="mt-3"><CausalGraph incident={d} /></div>
          </Card>
          <Card>
            <CardTitle>Timeline</CardTitle>
            <div className="mt-3"><Timeline stages={d.timeline || []} /></div>
          </Card>
        </div>
        <div className="space-y-6">
          {d.impact && <ImpactCard impact={d.impact} />}
          <WhatIfCard incidentId={id} startedAt={d.started_at} lastEventAt={d.last_event_at} />
          <Card>
            <CardTitle>Recommended fixes</CardTitle>
            <ol className="mt-3 space-y-2">
              {(d.recommendations || []).map((r) => <RecommendationItem key={r.priority} rec={r} />)}
            </ol>
          </Card>
          <CopilotPanel incidentId={id} />
        </div>
      </div>

      <Card>
        <div className="flex gap-2" role="tablist">
          <button role="tab" aria-selected={tab === "events"} className={`rounded px-3 py-1 text-sm ${tab === "events" ? "bg-raised" : ""}`} onClick={() => setTab("events")}>Events</button>
          <button role="tab" aria-selected={tab === "report"} className={`rounded px-3 py-1 text-sm ${tab === "report" ? "bg-raised" : ""}`} onClick={() => { setTab("report"); if (!report) loadReport(); }}>Report</button>
        </div>
        <div className="mt-3">
          {tab === "events" ? <EventTable events={d.events || []} /> : (
            <div>
              <div className="mb-2 flex gap-2">
                <button className="rounded border border-border px-3 py-1 text-sm" onClick={() => loadReport(true)}>Regenerate report</button>
                {report && (
                  <a className="rounded border border-border px-3 py-1 text-sm" href={`data:text/markdown;charset=utf-8,${encodeURIComponent(report.markdown)}`} download={`incident-${id}.md`}>Download report</a>
                )}
                {report && <span className="rounded-full border border-border px-2 py-1 text-xs">{report.generated_by === "llm" ? "Written by AI" : "Generated from template"}</span>}
              </div>
              <pre className="max-w-[70ch] whitespace-pre-wrap font-mono text-sm">{report ? report.markdown : "Loading report…"}</pre>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
