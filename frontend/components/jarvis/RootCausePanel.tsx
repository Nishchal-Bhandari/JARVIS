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
          <div className="mt-4 border-t border-border pt-3">
            <h3 className="text-sm font-semibold">Why not the others?</h3>
            <ul className="mt-2 space-y-3">
              {rootCause.alternatives.map((a) => (
                <li key={a.service} className="text-sm">
                  <span className="font-mono font-semibold">{a.service}</span>
                  {" — "}
                  <span className="text-muted">{Math.round(a.confidence * 100)}% confidence</span>
                  {a.score !== undefined && (
                    <span className="text-muted"> · score {a.score.toFixed(2)}</span>
                  )}
                  {(a.why_not?.length ?? 0) > 0 && (
                    <ul className="mt-0.5 list-disc space-y-0.5 pl-5 text-muted">
                      {a.why_not!.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
