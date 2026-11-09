export function fmtTime(iso?: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
export function fmtDuration(start?: string | null, end?: string | null): string {
  if (!start) return "—";
  const s = (new Date(end || Date.now()).getTime() - new Date(start).getTime()) / 1000;
  if (s < 60) return `${Math.round(s)}s`;
  return `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
}
export function severityLabel(sev: string): string {
  return { P1: "Critical", P2: "High", P3: "Medium", P4: "Low" }[sev] || sev;
}
export function severityIcon(sev: string): string {
  return sev === "P1" || sev === "P2" ? "▲" : sev === "P3" ? "●" : "○";
}
