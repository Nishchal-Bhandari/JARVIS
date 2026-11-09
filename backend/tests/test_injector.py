"""Fault injector tests: the engine must find the injected service from
the generated events alone — nothing is scripted per service/fault."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core import anomaly, correlation, rootcause
from app.core.anomaly import load_rules
from app.simulator.injector import FAULT_TYPES, generate_injected_events
from tests.test_golden import TOPO

SERVICES = [s["id"] for s in TOPO["services"]]


def _analyse(service, fault, seed=42):
    rules = load_rules()
    events = []
    for e in generate_injected_events(service, fault, seed=seed, topology=TOPO):
        d = dict(e)
        sig, _ = anomaly.tag_signature(d.get("message", ""), rules)
        if sig and not d.get("signature"):
            d["signature"] = sig
        if anomaly.is_anomaly(d, rules=rules):
            events.append(d)
    clusters = correlation.cluster_events(events, TOPO["dependencies"], threshold=0.45)
    assert clusters, (service, fault, seed)
    main = max(clusters, key=len)
    return rootcause.score_root_cause(main, TOPO["dependencies"], rules), len(clusters)


def test_inject_redis_cache_found_live():
    """The user's explicit check: injecting redis-cache must be found as
    redis-cache by the engine, not by a script."""
    rc, n_clusters = _analyse("redis-cache", "cache_failure")
    assert rc["service"] == "redis-cache", rc
    assert rc["confidence"] >= 0.5, rc
    assert n_clusters == 1, "injection must form exactly one incident"


def test_injector_matrix_seed42():
    """Every service x every fault type, seed 42: root cause is the injected
    service. A miss here is a real engine/injector weakness, not a test bug."""
    misses = []
    for service in SERVICES:
        for fault in FAULT_TYPES:
            rc, _ = _analyse(service, fault)
            if rc["service"] != service:
                misses.append((service, fault, rc["service"], rc["confidence"]))
    assert not misses, f"injector misses: {misses}"
