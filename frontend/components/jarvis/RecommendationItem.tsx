import { useState } from "react";
import type { Recommendation } from "@/lib/types";

export function RecommendationItem({ rec }: { rec: Recommendation }) {
  const [copied, setCopied] = useState(false);
  return (
    <li className="rounded-lg border border-border bg-card p-3">
      <div className="flex items-start gap-3">
        <span className="tabular flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-raised text-sm font-bold">{rec.priority}</span>
        <div className="min-w-0 flex-1">
          <p className="font-medium">{rec.title}</p>
          <p className="text-sm text-muted">{rec.detail}</p>
          <p className="mt-1 text-xs text-muted">Risk: {rec.risk} · Source: {rec.source === "rule" ? "Rulebook" : "AI-assisted"}</p>
        </div>
        <button
          aria-label={`Copy recommendation ${rec.priority}`}
          className="rounded border border-border px-2 py-1 text-xs hover:bg-raised"
          onClick={async () => { await navigator.clipboard.writeText(`${rec.title} — ${rec.detail}`); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
    </li>
  );
}
