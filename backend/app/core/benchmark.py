"""Benchmark: run the fault injector across every service and fault type,
several seeds each, and report top-1 root-cause accuracy and time to detect.

Time to detect = seconds from the first anomalous event until the engine's
top root cause first becomes the injected service (replayed in time order,
checked every 2 events). Only what the run produces is reported — misses
are listed, never hidden. Pure functions; no DB, no HTTP.
"""

from ..simulator.injector import FAULT_TYPES, generate_injected_events
from . import anomaly, correlation, rootcause
from .anomaly import load_rules


def _anomalous(events, rules):
    out = []
    for e in events:
        d = dict(e)
        sig, _ = anomaly.tag_signature(d.get("message", ""), rules)
        if sig and not d.get("signature"):
            d["signature"] = sig
        if anomaly.is_anomaly(d, rules=rules):
            out.append(d)
    return sorted(out, key=lambda x: x["timestamp"])


def _top_root_cause(events, dependencies, rules):
    clusters = correlation.cluster_events(events, dependencies, threshold=0.45)
    if not clusters:
        return None
    main = max(clusters, key=len)
    rc = rootcause.score_root_cause(main, dependencies, rules)
    return rc["service"] if rc else None


def run_one(service, fault, seed, topology, rules):
    events = generate_injected_events(service, fault, seed=seed, topology=topology)
    anomalous = _anomalous(events, rules)
    deps = topology["dependencies"]
    detected_at = None
    found = None
    # Replay in time order; first moment the engine names the right service.
    for k in range(3, len(anomalous) + 1, 2):
        if _top_root_cause(anomalous[:k], deps, rules) == service:
            detected_at = (
                anomalous[k - 1]["timestamp"] - anomalous[0]["timestamp"]
            ).total_seconds()
            found = service
            break
    if detected_at is None:
        found = _top_root_cause(anomalous, deps, rules)
    return {
        "service": service,
        "fault_type": fault,
        "seed": seed,
        "expected": service,
        "found": found,
        "correct": found == service,
        "time_to_detect_s": round(detected_at, 1) if detected_at is not None else None,
        "events": len(anomalous),
    }


def run_benchmark(topology, rules=None, services=None, faults=None, seeds=(42, 43, 44, 45, 46)):
    rules = rules or load_rules()
    services = services or [s["id"] for s in topology["services"]]
    faults = faults or FAULT_TYPES
    rows = []
    for service in services:
        for fault in faults:
            for seed in seeds:
                rows.append(run_one(service, fault, seed, topology, rules))
    correct = [r for r in rows if r["correct"]]
    detected = [r["time_to_detect_s"] for r in correct if r["time_to_detect_s"] is not None]
    return {
        "total_runs": len(rows),
        "correct": len(correct),
        "accuracy_pct": round(100 * len(correct) / len(rows), 1) if rows else 0.0,
        "avg_time_to_detect_s": (round(sum(detected) / len(detected), 1) if detected else None),
        "misses": [r for r in rows if not r["correct"]],
        "rows": rows,
    }
