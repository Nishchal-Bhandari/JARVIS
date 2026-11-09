"use client";
import { useEffect, useRef, type ReactNode } from "react";
import { QueryClient, QueryClientProvider, useQueryClient } from "@tanstack/react-query";
import { useStream } from "@/store/stream";

function StreamHook() {
  const qc = useQueryClient();
  const setConnected = useStream((s) => s.setConnected);
  const push = useStream((s) => s.push);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const url = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/stream";
    let ws: WebSocket;
    let closed = false;
    const connect = () => {
      ws = new WebSocket(url);
      wsRef.current = ws;
      ws.onopen = () => setConnected(true);
      ws.onclose = () => { setConnected(false); if (!closed) setTimeout(connect, 3000); };
      ws.onmessage = (ev) => {
        push(ev.data);
        qc.invalidateQueries({ queryKey: ["incidents"] });
        qc.invalidateQueries({ queryKey: ["events"] });
        qc.invalidateQueries({ queryKey: ["stats"] });
      };
    };
    connect();
    return () => { closed = true; wsRef.current?.close(); };
  }, [qc, setConnected, push]);
  return null;
}

export function Providers({ children }: { children: ReactNode }) {
  const clientRef = useRef<QueryClient | null>(null);
  if (!clientRef.current) clientRef.current = new QueryClient();
  return (
    <QueryClientProvider client={clientRef.current}>
      <StreamHook />
      {children}
    </QueryClientProvider>
  );
}
