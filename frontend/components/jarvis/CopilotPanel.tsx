"use client";
import { useState } from "react";
import { api } from "@/lib/api";

const CHIPS = ["Why postgres-primary?", "Who is affected?", "What should I do first?"];

export function CopilotPanel({ incidentId }: { incidentId: string }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [basedOn, setBasedOn] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  async function ask(q: string) {
    setLoading(true);
    try {
      const res = await api.ask(incidentId, q);
      setAnswer(res.answer || "");
      setBasedOn(res.based_on || []);
    } catch {
      setAnswer("Could not reach the Copilot service. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h2 className="text-sm font-semibold">Ask J.A.R.V.I.S.</h2>
      <div className="mt-2 flex flex-wrap gap-2">
        {CHIPS.map((c) => (
          <button key={c} className="rounded-full border border-border px-3 py-1 text-xs hover:bg-raised" onClick={() => { setQuestion(c); ask(c); }}>{c}</button>
        ))}
      </div>
      <form className="mt-3 flex gap-2" onSubmit={(e) => { e.preventDefault(); if (question.trim()) ask(question); }}>
        <input aria-label="Ask about this incident" className="min-w-0 flex-1 rounded-md border border-border bg-raised px-3 py-2 text-sm" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask about this incident…" />
        <button className="rounded-md bg-accent px-4 py-2 text-sm text-white" disabled={loading}>{loading ? "…" : "Ask"}</button>
      </form>
      {answer && (
        <div className="mt-3 text-sm">
          <p>{answer}</p>
          <p className="mt-1 text-xs text-muted">Based on this incident&apos;s data{basedOn.length ? `: ${basedOn.join(", ")}` : ""}.</p>
        </div>
      )}
    </div>
  );
}
