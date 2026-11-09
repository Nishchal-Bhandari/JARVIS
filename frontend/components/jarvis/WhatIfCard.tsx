"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardTitle } from "@/components/ui/card";

interface WhatIf {
  fix_at_seconds: number; avoided_users: number; avoided_failed_transactions: number;
  avoided_revenue_inr: number; total_users: number; total_failed_transactions: number;
  avg_order_value_inr: number; duration_seconds: number; note: string;
}

export function WhatIfCard({ incidentId, startedAt, lastEventAt }: { incidentId: string; startedAt?: string | null; lastEventAt?: string | null }) {
  const duration = startedAt && lastEventAt
    ? Math.max(1, Math.round((new Date(lastEventAt).getTime() - new Date(startedAt).getTime()) / 1000))
    : 60;
  const [fixAt, setFixAt] = useState(Math.min(30, duration));
  const [data, setData] = useState<WhatIf | null>(null);

  useEffect(() => {
    const t = setTimeout(() => {
      api.whatif(incidentId, fixAt).then(setData).catch(() => setData(null));
    }, 200);
    return () => clearTimeout(t);
  }, [incidentId, fixAt]);

  return (
    <Card>
      <CardTitle>What if the fix had landed sooner?</CardTitle>
      <label className="mt-3 block text-sm">
        Fix applied at +{fixAt}s
        <input
          type="range" min={0} max={duration} value={fixAt}
          onChange={(e) => setFixAt(Number(e.target.value))}
          className="mt-1 w-full" aria-label="Fix applied at, seconds after incident start"
        />
      </label>
      {data && (
        <div className="mt-2 text-sm">
          <p>
            About <span className="font-semibold">{data.avoided_users} of {data.total_users} users</span>
            {" "}and <span className="font-semibold">{data.avoided_failed_transactions} of {data.total_failed_transactions} failed payments</span>
            {" "}would have been avoided — <span className="font-semibold">≈ ₹{data.avoided_revenue_inr.toLocaleString("en-IN")}</span>.
          </p>
          <p className="mt-1 text-xs text-muted">
            {data.note} Estimate only — {data.total_failed_transactions} failed payments × ₹
            {data.avg_order_value_inr.toLocaleString("en-IN")} assumed average order value.
          </p>
        </div>
      )}
    </Card>
  );
}
