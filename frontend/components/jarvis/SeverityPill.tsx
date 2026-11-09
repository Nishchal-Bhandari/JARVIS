import { severityIcon, severityLabel } from "@/lib/format";

export function SeverityPill({ severity }: { severity: string }) {
  const tone = severity === "P1" ? "bg-cause text-white" : severity === "P2" ? "bg-affected text-black" : severity === "P3" ? "border border-affected text-affected-ink" : "border border-unmapped text-muted";
  return (
    <span aria-label={`Severity ${severity}, ${severityLabel(severity)}`} className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-semibold ${tone}`}>
      {severityIcon(severity)} {severity} · {severityLabel(severity)}
    </span>
  );
}
