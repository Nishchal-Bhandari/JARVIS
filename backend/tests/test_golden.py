"""Golden test (agent.md §8): S1 / SEED=42 -> exactly one main incident,
root cause postgres-primary, confidence >= 0.70, >=5 services, >=30 users,
plus a separate low-severity CDN cluster that is NOT merged."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core import anomaly, correlation, rootcause, severity
from app.core import impact as impact_mod
from app.core.anomaly import load_rules
from app.simulator.scenarios import generate_scenario_events

TOPO = {
    "services": [
        {"id": "web-app", "critical": False},
        {"id": "api-gateway", "critical": True},
        {"id": "auth-service", "critical": True},
        {"id": "payment-service", "critical": True},
        {"id": "order-service", "critical": False},
        {"id": "notification-service", "critical": False},
        {"id": "redis-cache", "critical": False},
        {"id": "postgres-primary", "critical": True},
        {"id": "cdn", "critical": False},
    ],
    "dependencies": [
        {"from": "web-app", "to": "api-gateway"},
        {"from": "api-gateway", "to": "auth-service"},
        {"from": "api-gateway", "to": "payment-service"},
        {"from": "api-gateway", "to": "order-service"},
        {"from": "auth-service", "to": "postgres-primary"},
        {"from": "auth-service", "to": "redis-cache"},
        {"from": "payment-service", "to": "postgres-primary"},
        {"from": "order-service", "to": "postgres-primary"},
        {"from": "payment-service", "to": "notification-service"},
        {"from": "web-app", "to": "cdn"},
    ],
}


def _anomalous():
    rules = load_rules()
    out = []
    for e in generate_scenario_events("db_pool_exhaustion", seed=42):
        d = dict(e)
        sig, _ = anomaly.tag_signature(d.get("message", ""), rules)
        if sig and not d.get("signature"):
            d["signature"] = sig
        if anomaly.is_anomaly(d, rules=rules):
            out.append(d)
    return out


def test_golden_db_pool_exhaustion():
    events = _anomalous()
    clusters = correlation.cluster_events(events, TOPO["dependencies"], threshold=0.45)
    assert len(clusters) == 2, f"expected 2 clusters (main + CDN), got {len(clusters)}"
    main = max(clusters, key=len)
    cdn = min(clusters, key=len)
    assert {e["service"] for e in cdn} == {"cdn"}, "CDN cluster must contain only cdn"
    assert "cdn" not in {e["service"] for e in main}, "CDN must NOT merge into main incident"
    rules = load_rules()
    rc = rootcause.score_root_cause(main, TOPO["dependencies"], rules)
    assert rc["service"] == "postgres-primary", rc
    assert rc["confidence"] >= 0.70, rc
    assert len(rc["evidence"]) >= 3, rc
    imp = impact_mod.compute_impact(main, TOPO["dependencies"], TOPO)
    assert len(imp["affected_services"]) >= 5, imp
    assert imp["users_affected"] >= 30, imp
    assert imp["failed_transactions"] >= 30, imp
    assert severity.compute_severity(imp) == "P1", imp
    cdn_imp = impact_mod.compute_impact(cdn, TOPO["dependencies"], TOPO)
    assert severity.compute_severity(cdn_imp) == "P4", cdn_imp


def test_rootcause_s2_s3():
    rules = load_rules()
    for scenario, expected in [("bad_deploy", "auth-service"), ("cache_failure", "redis-cache")]:
        events = []
        for e in generate_scenario_events(scenario, seed=42):
            d = dict(e)
            sig, _ = anomaly.tag_signature(d.get("message", ""), rules)
            if sig and not d.get("signature"):
                d["signature"] = sig
            if anomaly.is_anomaly(d, rules=rules):
                events.append(d)
        clusters = correlation.cluster_events(events, TOPO["dependencies"], threshold=0.45)
        assert clusters, scenario
        main = max(clusters, key=len)
        rc = rootcause.score_root_cause(main, TOPO["dependencies"], rules)
        assert rc["service"] == expected, (scenario, rc)
