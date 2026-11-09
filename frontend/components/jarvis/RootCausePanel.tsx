import type { RootCause } from "@/lib/types";
import { ConfidenceMeter } from "./ConfidenceMeter";

export function RootCausePanel({ rootCause }: { rootCause: RootCause }) {
  const uncertain = rootCause.confidence < 0.5;
  return (
    <div className={`rounded-lg border border-border bg-card ${uncertain ? "border-l-4 border-l-affected" : "border-l-4 border-l-cause"}`}>
      <div className={`px-4 py-3 ${uncertain ? "bg-affected-wash" : "bg-cause-wash"}`}>
        <h2 className="text-sm font-semibold">{uncertain ? "Root cause uncertain" : "Most likely cause"}</h2>
      </div>
      <div className="p-4">
        <div className="flex flex-wrap items-center gap-4">
          <span className="font-mono text-lg font-bold">{rootCause.service}</span>
          <span className="text-muted">{rootCause.label}</span>
          <ConfidenceMeter confidence={rootCause.confidence} />
        </div>
        <h3 className="mt-4 text-sm font-semibold">Why we think this</h3>
        <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-muted">
          {rootCause.evidence.slice(0, 5).map((e, i) => (
            <li key={i}>{e}</li>
          ))}
        </ul>
        {rootCause.alternatives.length > 0 && (
          <details className="mt-3 text-sm">
            <summary className="cursor-pointer text-trace">Other candidates</summary>
            <ul className="mt-1 list-disc pl-5 text-muted">
              {rootCause.alternatives.map((a) => (
                <li key={a.service}>{a.service} — {Math.round(a.confidence * 100)}%</li>
              ))}
            </ul>
          </details>
        )}
      </div>
    </div>
  );
}
