import type { JarEvent } from "@/lib/types";
import { fmtTime } from "@/lib/format";

export function EventTable({ events }: { events: JarEvent[] }) {
  if (!events.length) return <p className="text-sm text-muted">No events yet.</p>;
  return (
    <div className="max-h-96 overflow-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-raised text-left text-muted">
          <tr><th className="px-3 py-2">Time</th><th className="px-3 py-2">Service</th><th className="px-3 py-2">Severity</th><th className="px-3 py-2">Message</th></tr>
        </thead>
        <tbody>
          {events.slice(0, 200).map((e) => (
            <tr key={e.id} className={e.is_anomaly ? "bg-affected-wash" : ""}>
              <td className="tabular whitespace-nowrap px-3 py-1 font-mono text-xs">{fmtTime(e.timestamp)}</td>
              <td className="whitespace-nowrap px-3 py-1 font-mono text-xs">{e.service}</td>
              <td className="px-3 py-1">{e.severity}{e.signature ? ` · ${e.signature}` : ""}</td>
              <td className="px-3 py-1 font-mono text-xs">{e.message}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
