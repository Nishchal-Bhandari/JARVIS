"""Anomaly detection + signature tagging (specsheet §6.1). Pure functions."""

import statistics

import yaml

RULES_PATH = __file__.replace("core/anomaly.py", "data/rules.yaml")


def load_rules():
    with open(RULES_PATH) as f:
        return yaml.safe_load(f) or []


def tag_signature(message: str, rules=None):
    """Return (signature, rule) for the first matching rule, else (None, None)."""
    msg = (message or "").lower()
    for rule in rules or load_rules():
        if any(pat in msg for pat in rule.get("match", [])):
            return rule["id"], rule
    return None, None


SEV_ORDER = {"info": 0, "warning": 1, "error": 2, "critical": 3}


def is_anomaly(event: dict, metric_history=None, rules=None) -> bool:
    """Logs/alerts: severity >= warning or a signature matches.
    Metrics: robust z-score (median/MAD) > 3.5 or absolute thresholds."""
    if event.get("signature") or tag_signature(event.get("message", ""), rules)[0]:
        return True
    if SEV_ORDER.get(event.get("severity", "info"), 0) >= 1:
        return True
    metric = event.get("metric") or {}
    if metric:
        name, value = metric.get("name", ""), float(metric.get("value") or 0)
        if name == "p95_latency_ms" and value > 1000:
            return True
        if name == "error_rate" and value > 0.05:
            return True
        hist = list(metric_history or [])
        if len(hist) >= 10 and abs(robust_z(value, hist)) > 3.5:
            return True
    return False


def robust_z(value: float, history: list[float]) -> float:
    if len(history) < 5:
        return 0.0
    med = statistics.median(history)
    mad = statistics.median([abs(x - med) for x in history])
    if mad == 0:
        # Constant history: scale by 1% of the median so a small drift is not a spike.
        scale = max(abs(med) * 0.01, 1.0)
        return 0.6745 * (value - med) / scale
    return 0.6745 * (value - med) / mad
