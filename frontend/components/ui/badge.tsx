import type { ReactNode } from "react";

export function Badge({ children, tone = "default" }: { children: ReactNode; tone?: "default" | "cause" | "affected" | "steady" | "trace" }) {
  const tones: Record<string, string> = {
    default: "border-border text-muted",
    cause: "border-cause bg-cause-wash text-cause-ink",
    affected: "border-affected bg-affected-wash text-affected-ink",
    steady: "border-steady bg-steady-wash text-steady",
    trace: "border-trace bg-trace-wash text-trace",
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${tones[tone]}`}>
      {children}
    </span>
  );
}
