"""Suspect-change marker: a deploy/config change shortly before the first
error is flagged (evidence + timeline marker), with only a +0.05 score
boost — and the golden test stays at 0.78 when there is no change."""

import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core import anomaly, correlation, rootcause
from app.core import engine as engine_mod
from app.core.anomaly import load_rules
from app.simulator.scenarios import generate_scenario_events
from tests.test_golden import TOPO, _anomalous


def test_golden_confidence_unchanged_without_change():
    """No change events -> no boost -> golden stays exactly at 0.78."""
    events = _anomalous()
    clusters = correlation.cluster_events(events, TOPO["dependencies"], threshold=0.45)
    main = max(clusters, key=len)
    rc = rootcause.score_root_cause(main, TOPO["dependencies"], load_rules())
    assert rc["confidence"] == 0.78, rc
    assert rc.get("suspect_change") is None, rc


def _bad_deploy_events():
    rules = load_rules()
    out = []
    for e in generate_scenario_events("bad_deploy", seed=42):
        d = dict(e)
        sig, _ = anomaly.tag_signature(d.get("message", ""), rules)
        if sig and not d.get("signature"):
            d["signature"] = sig
        if anomaly.is_anomaly(d, rules=rules):
            out.append(d)
    return out


def test_suspect_change_flagged():
    events = _bad_deploy_events()
    first_error = min(e["timestamp"] for e in events if e["severity"] == "error")
    deploy = {
        "service": "auth-service",
        "type": "deploy",
        "severity": "info",
        "message": "deploy v2.4.1 started",
        "timestamp": first_error - timedelta(minutes=3),
    }
    analysis = engine_mod.analyse_cluster(events, TOPO, load_rules(), change_events=[deploy])
    rc = analysis["root_cause"]
    assert rc["service"] == "auth-service", rc
    assert rc["suspect_change"]["service"] == "auth-service", rc
    assert rc["suspect_change"]["minutes_before"] == 3.0, rc
    assert rc["evidence"][0].startswith("Suspect: auth-service deploy v2.4.1"), rc
    markers = [s for s in analysis["timeline"] if s.get("marker")]
    assert len(markers) == 1, analysis["timeline"]
    assert markers[0]["offset_seconds"] < 0, markers
    assert "deploy v2.4.1" in markers[0]["key_events"][0], markers


def test_change_boost_is_small():
    """Same cluster with and without a change: confidence moves a little,
    and never flips the winner on its own."""
    events = _bad_deploy_events()
    rules = load_rules()
    plain = rootcause.score_root_cause(events, TOPO["dependencies"], rules)
    boosted = rootcause.score_root_cause(
        events, TOPO["dependencies"], rules, change_services={"auth-service"}
    )
    assert boosted["service"] == plain["service"] == "auth-service"
    assert 0 < boosted["confidence"] - plain["confidence"] < 0.1, (plain, boosted)
