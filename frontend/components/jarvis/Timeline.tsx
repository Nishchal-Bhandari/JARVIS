"use client";
import { useEffect, useRef, useState } from "react";
import type { TimelineStage } from "@/lib/types";

export function Timeline({ stages }: { stages: TimelineStage[] }) {
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [index, setIndex] = useState(0);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (playing) {
      timer.current = setInterval(() => {
        setIndex((i) => {
          if (i + 1 >= stages.length) { setPlaying(false); return i; }
          return i + 1;
        });
      }, 1000 / speed);
    }
    return () => { if (timer.current) clearInterval(timer.current); };
  }, [playing, speed, stages.length]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") setIndex((i) => Math.min(i + 1, stages.length - 1));
      if (e.key === "ArrowLeft") setIndex((i) => Math.max(i - 1, 0));
      if (e.key === " ") { e.preventDefault(); setPlaying((p) => !p); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [stages.length]);

  if (!stages.length) return <p className="text-sm text-muted">No timeline stages yet.</p>;
  const maxOffset = Math.max(...stages.map((s) => Math.max(s.offset_seconds, 0)), 1);
  const fmtOffset = (s: number) => `${s < 0 ? "−" : "+"}${Math.abs(s).toFixed(0)}s`;
  return (
    <div>
      <div className="mb-2 flex items-center gap-2">
        <button aria-label={playing ? "Pause timeline" : "Play timeline"} className="rounded border border-border px-3 py-1 text-sm" onClick={() => setPlaying((p) => !p)}>{playing ? "⏸ Pause" : "▶ Play"}</button>
        {[1, 5, 10].map((s) => (
          <button key={s} aria-label={`Speed ${s}x`} className={`rounded border px-2 py-1 text-xs ${speed === s ? "border-trace bg-trace-wash" : "border-border"}`} onClick={() => setSpeed(s)}>{s}×</button>
        ))}
        <button className="rounded border border-border px-2 py-1 text-xs" onClick={() => { setIndex(0); setPlaying(false); }}>Jump to start</button>
      </div>
      <div className="space-y-2">
        {stages.map((stage, i) => (
          <div key={i} className={`flex items-center gap-3 rounded border p-2 text-sm ${stage.marker ? "border-affected bg-affected-wash" : i <= index ? "border-trace bg-trace-wash" : "border-border"}`}>
            <span className="tabular w-14 shrink-0 font-mono">{fmtOffset(stage.offset_seconds)}</span>
            <span className={`h-2 rounded-full ${stage.marker ? "bg-affected" : "bg-trace"}`} style={{ width: `${Math.max(4, (Math.max(stage.offset_seconds, 0) / maxOffset) * 100)}px` }} />
            <span>{stage.marker ? `⚠ Suspect change: ${stage.services.join(", ")}` : stage.services.join(", ")}</span>
            <span className="truncate text-muted">{stage.key_events[0] || ""}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
