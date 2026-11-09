"""Recommendations from the rulebook (specsheet §10). Pure functions."""

from .anomaly import load_rules


def recommendations_for(root_cause, rules=None):
    rules = rules or load_rules()
    sig_label = (root_cause or {}).get("label", "")
    out = []
    for rule in rules:
        if rule.get("label") == sig_label:
            for a in rule.get("actions", []):
                out.append(
                    {
                        "priority": a["priority"],
                        "title": a["title"],
                        "detail": a.get("detail", ""),
                        "risk": a.get("risk", "low"),
                        "source": "rule",
                    }
                )
            break
    if not out:
        out = [
            {
                "priority": 1,
                "title": "Check the root-cause service health",
                "detail": "Inspect logs, metrics and recent deploys for the root-cause service.",
                "risk": "low",
                "source": "rule",
            }
        ]
    return sorted(out, key=lambda r: r["priority"])
