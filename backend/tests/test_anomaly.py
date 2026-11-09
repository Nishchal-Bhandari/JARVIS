"""Anomaly tests (specsheet §6.1)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.anomaly import is_anomaly, robust_z


def test_spike_flagged_steady_ignored():
    hist = [180.0] * 30
    assert (
        is_anomaly(
            {
                "severity": "info",
                "message": "ok",
                "metric": {"name": "p95_latency_ms", "value": 2300},
            }
        )
        is True
    )
    assert (
        is_anomaly(
            {
                "severity": "info",
                "message": "ok",
                "metric": {"name": "p95_latency_ms", "value": 180},
            }
        )
        is False
    )
    assert robust_z(2300, hist) > 3.5
    assert robust_z(185, hist) < 3.5


def test_signature_tags_anomaly():
    assert is_anomaly({"severity": "info", "message": "too many connections"}) is True
    assert is_anomaly({"severity": "info", "message": "request served OK"}) is False
