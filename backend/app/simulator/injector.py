"""Generic fault injector (chaos button).

inject(service, fault_type) makes the chosen service emit errors, then
spreads symptoms to its dependents along the topology graph, each hop
delayed ~8-20s, plus a little healthy noise. Nothing here is scripted
per scenario: the engine has to find the injected service from the
events alone, exactly as it would a real fault.

Every event in one injection shares a trace id, so correlation can link
the cascade (time + topology + shared trace), and dependent symptoms
repeat the fault's key phrase so the signature tags on them too.
Deterministic with SEED.
"""

import random
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta

BASE = datetime(2026, 11, 9, 10, 15, 0, tzinfo=UTC)

# fault_type -> root-cause fault: the phrase the injected service emits,
# the signature it should tag as, and the phrase dependents repeat.
FAULTS = {
    "pool_exhaustion": {
        "label": "Connection pool exhaustion",
        "signature": "db_pool_exhausted",
        "root_messages": [
            (0, "warning", "connections 90/100"),
            (2, "error", "too many connections"),
            (4, "error", "timeout acquiring connection from pool"),
        ],
        "symptom_phrase": "timeout acquiring connection from pool",
    },
    "cache_failure": {
        "label": "Cache failure",
        "signature": "cache_failure",
        "root_messages": [
            (0, "error", "connection refused"),
            (3, "error", "redis connection refused: cache unavailable"),
        ],
        "symptom_phrase": "cache miss storm",
    },
    "deploy_failure": {
        "label": "Bad deploy",
        "signature": "bad_deploy",
        "root_messages": [
            (0, "error", "deploy v2.4.2 failed: crash loop after release"),
            (3, "error", "error rate above threshold after deploy v2.4.2"),
        ],
        "symptom_phrase": "upstream timeout after deploy",
    },
    "oom": {
        "label": "Memory pressure / OOM",
        "signature": "oom",
        "root_messages": [
            (0, "error", "out of memory: heap exhausted"),
            (3, "error", "memory pressure: heap usage 98%"),
        ],
        "symptom_phrase": "upstream timeout",
    },
    "latency": {
        "label": "Latency spike",
        "signature": None,
        "root_messages": [
            (0, "error", "p95 latency 2400ms"),
            (3, "error", "p95 latency 2600ms, requests queueing"),
        ],
        "symptom_phrase": "slow responses",
    },
}

FAULT_TYPES = list(FAULTS)


def dependents_by_hop(service, dependencies):
    """{hop: [services]} — services that depend on `service`, by BFS distance
    over reverse edges (A depends on B => B's failure reaches A)."""
    rev = defaultdict(set)
    for d in dependencies:
        rev[d["to"]].add(d["from"])
    hops, seen, queue = {}, {service}, deque([(service, 0)])
    while queue:
        node, h = queue.popleft()
        for nb in sorted(rev.get(node, [])):
            if nb not in seen:
                seen.add(nb)
                hops[nb] = h + 1
                queue.append((nb, h + 1))
    by_hop = defaultdict(list)
    for s, h in hops.items():
        by_hop[h].append(s)
    return dict(by_hop)


def _symptom_message(service, fault, target):
    """What a dependent service reports when `target` fails."""
    phrase = fault["symptom_phrase"]
    if service == "payment-service":
        return "payment failed: could not persist transaction"
    if service == "auth-service":
        return "login failed: upstream timeout"
    if service == "api-gateway":
        return "504 gateway timeout"
    if "pool" in phrase:
        return f"timeout acquiring connection from pool ({target})"
    if "cache" in phrase:
        return f"slow queries: cache miss storm ({target})"
    if "deploy" in phrase:
        return f"upstream timeout after deploy on {target}"
    if phrase == "upstream timeout":
        return f"upstream timeout waiting for {target}"
    return f"slow responses from {target}"


def generate_injected_events(service, fault_type, seed=42, base=None, topology=None):
    """Return event dicts (same shape as scenarios.generate_scenario_events).
    Raises ValueError for an unknown service or fault type."""
    if fault_type not in FAULTS:
        raise ValueError(f"unknown fault type: {fault_type}")
    fault = FAULTS[fault_type]
    topology = topology or {"services": [], "dependencies": []}
    services = {s["id"] for s in topology.get("services", [])}
    if services and service not in services:
        raise ValueError(f"unknown service: {service}")
    rng = random.Random(seed)
    base = base or BASE
    trace = f"tr_inj_{seed}"
    events = []

    def ev(offset, svc, severity, message, **kw):
        d = {
            "offset_seconds": offset,
            "service": svc,
            "severity": severity,
            "message": message,
            "type": "log",
            "source": "simulator",
            "trace_id": trace,
            "host": f"{svc.split('-')[0]}-inj",
        }
        d.update(kw)
        return d

    # Root-cause service emits the fault first. Always >= 3 root events, so
    # even a service with no dependents (e.g. web-app) forms a cluster.
    for off, sev, msg in fault["root_messages"]:
        e = ev(off, service, sev, msg)
        if fault["signature"]:
            e["signature"] = fault["signature"]
        if fault_type == "latency":
            e["metric"] = {"name": "p95_latency_ms", "value": 2400}
        events.append(e)
    e = ev(6, service, "error", f"{fault['label']}: still failing")
    if fault["signature"]:
        e["signature"] = fault["signature"]
    if fault_type == "latency":
        e["metric"] = {"name": "p95_latency_ms", "value": 2500}
    events.append(e)

    # Symptoms spread outward, one hop every ~8-20s.
    by_hop = dependents_by_hop(service, topology.get("dependencies", []))
    for hop in sorted(by_hop):
        delay = hop * rng.uniform(8, 20)
        for dep in by_hop[hop]:
            msg = _symptom_message(dep, fault, service)
            events.append(ev(delay, dep, "warning", msg))
            events.append(ev(delay + rng.uniform(1, 4), dep, "error", msg))
            # User-visible failures on the roles that have users.
            if dep == "payment-service":
                for i in range(15):
                    events.append(
                        ev(
                            delay + 5 + i,
                            dep,
                            "error",
                            "payment failed: could not persist transaction",
                            user_id=f"u_inj_{seed}_{i}",
                            signature="payment_failed",
                            attrs={"status": 500, "endpoint": "/v1/charge"},
                        )
                    )
            if dep == "auth-service":
                for i in range(10):
                    events.append(
                        ev(
                            delay + 5 + i,
                            dep,
                            "error",
                            "login failed: upstream timeout",
                            user_id=f"u_inj_{seed}_a{i}",
                            signature="login_failed",
                        )
                    )
    # Healthy background noise (info only — never anomalous).
    for i in range(6):
        events.append(ev(i * 11, "web-app", "info", "request served OK", host="web-1"))
    events.sort(key=lambda e: e["offset_seconds"])
    out = []
    for i, e in enumerate(events):
        off = e.pop("offset_seconds")
        d = dict(e)
        d["timestamp"] = base + timedelta(seconds=off)
        d["id"] = f"evt_inj_{seed}_{i:04d}"
        out.append(d)
    return out
