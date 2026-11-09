"""What-if replay: "fix applied at +N seconds" — how much impact would
have been avoided? Needs no new data: it re-counts the incident's own
events after the fix time, with the same predicates as impact.py.

Simulation: assumes the fix works immediately. The numbers are what
*would* have been avoided, labelled as such everywhere they are shown.
"""

from .impact import AVG_ORDER_VALUE_INR, count_failed_transactions, count_users


def compute_whatif(events, started_at, fix_at_seconds, avg_order_value_inr=AVG_ORDER_VALUE_INR):
    """events: incident event dicts with timestamps. fix_at_seconds is
    measured from the incident start; clamped to [0, duration] by the API."""
    after = [e for e in events if (e["timestamp"] - started_at).total_seconds() > fix_at_seconds]
    avoided_failed = count_failed_transactions(after)
    return {
        "fix_at_seconds": fix_at_seconds,
        "avoided_users": count_users(after),
        "avoided_failed_transactions": avoided_failed,
        "avoided_revenue_inr": avoided_failed * avg_order_value_inr,
        "total_users": count_users(events),
        "total_failed_transactions": count_failed_transactions(events),
        "avg_order_value_inr": avg_order_value_inr,
        "note": "Simulation: assumes the fix works immediately.",
    }
