"""Impact analysis (specsheet §8). Pure functions.

Revenue impact is an *estimate*, not a measured figure: failed transactions
times an assumed average order value. The assumption is returned with the
number (avg_order_value_inr) and shown in the UI, so it is never presented
as exact revenue lost.
"""

from collections import defaultdict

# Assumed average order value for the payment platform, in INR.
AVG_ORDER_VALUE_INR = 500


def count_users(events):
    """Distinct users on error/critical events (fall back to any user id)."""
    users = {
        e["user_id"]
        for e in events
        if e.get("user_id") and e.get("severity") in ("error", "critical")
    }
    if not users:
        users = {e["user_id"] for e in events if e.get("user_id")}
    return len(users)


def count_failed_transactions(events):
    """Failed payments: payment_failed signature, or a 5xx on payment-service."""
    return sum(
        1
        for e in events
        if e.get("signature") == "payment_failed"
        or (e.get("attrs") or {}).get("status") in (500, 502, 503, 504)
        and "payment" in (e.get("service") or "")
    )


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
    users = count_users(events)
    failed = count_failed_transactions(events)
    critical_ids = {s["id"] for s in topology.get("services", []) if s.get("critical")}
    return {
        "affected_services": affected,
        "at_risk_services": sorted(at_risk),
        "users_affected": users,
        "failed_transactions": failed,
        "critical_path_hit": bool(set(affected) & critical_ids),
        "estimated_revenue_impact_inr": failed * AVG_ORDER_VALUE_INR,
        "avg_order_value_inr": AVG_ORDER_VALUE_INR,
    }
