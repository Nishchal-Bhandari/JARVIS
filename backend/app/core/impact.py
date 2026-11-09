"""Impact analysis (specsheet §8). Pure functions."""

from collections import defaultdict


def compute_impact(events, dependencies, topology):
    affected = sorted({e["service"] for e in events})
    # at-risk: transitive dependents of root cause with no anomalies yet
    # (computed by caller via root cause; here: dependents of affected services not in affected)
    rev = defaultdict(set)
    for d in dependencies:
        rev[d["to"]].add(d["from"])
    at_risk = set()
    for s in affected:
        stack = list(rev.get(s, []))
        seen = set()
        while stack:
            n = stack.pop()
            if n in seen or n in affected:
                continue
            seen.add(n)
            at_risk.add(n)
            stack.extend(rev.get(n, []))
    users = {
        e["user_id"]
        for e in events
        if e.get("user_id") and e.get("severity") in ("error", "critical")
    }
    if not users:
        users = {e["user_id"] for e in events if e.get("user_id")}
    failed = sum(
        1
        for e in events
        if e.get("signature") == "payment_failed"
        or (e.get("attrs") or {}).get("status") in (500, 502, 503, 504)
        and "payment" in (e.get("service") or "")
    )
    critical_ids = {s["id"] for s in topology.get("services", []) if s.get("critical")}
    return {
        "affected_services": affected,
        "at_risk_services": sorted(at_risk),
        "users_affected": len(users),
        "failed_transactions": failed,
        "critical_path_hit": bool(set(affected) & critical_ids),
    }
