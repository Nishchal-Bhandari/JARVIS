import type { Impact } from "@/lib/types";
import { Card, CardTitle } from "@/components/ui/card";

export function ImpactCard({ impact }: { impact: Impact }) {
  return (
    <Card>
      <CardTitle>Impact</CardTitle>
      <div className="mt-3 grid grid-cols-3 gap-2 text-center">
        <div><div className="tabular text-2xl font-bold">{impact.affected_services.length}</div><div className="text-xs text-muted">services</div></div>
        <div><div className="tabular text-2xl font-bold">{impact.users_affected}</div><div className="text-xs text-muted">users</div></div>
        <div><div className="tabular text-2xl font-bold">{impact.failed_transactions}</div><div className="text-xs text-muted">failed payments</div></div>
      </div>
      <p className="mt-3 text-sm">
        {impact.critical_path_hit ? "⚠ Critical path affected" : "✓ Critical path not affected"}
      </p>
      {impact.at_risk_services.length > 0 && (
        <p className="mt-1 text-sm text-muted">At risk: {impact.at_risk_services.join(", ")}</p>
      )}
    </Card>
  );
}
