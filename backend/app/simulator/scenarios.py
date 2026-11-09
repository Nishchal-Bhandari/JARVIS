"""Scripted scenarios (specsheet §13). Deterministic with SEED.
Each event: (offset_seconds, template dict)."""

import random
from datetime import UTC, datetime, timedelta

BASE = datetime(2026, 11, 9, 10, 15, 0, tzinfo=UTC)


def _ev(offset, service, severity, message, **kw):
    d = {
        "offset_seconds": offset,
        "service": service,
        "severity": severity,
        "message": message,
        "type": "log",
        "source": "simulator",
    }
    d.update(kw)
    return d


def generate_scenario_events(scenario: str, seed: int = 42, base=None):
    """Return a list of canonical-ish event dicts with real timestamps.
    base: scenario start time (default: the fixed 2026-11-09 10:15 UTC, so
    sample files are stable). The live runner passes now, so event
    timestamps keep their scripted offsets whatever the playback speed is."""
    random.Random(seed)  # seed the generator for determinism
    base = base or BASE
    events = []
    if scenario == "db_pool_exhaustion":
        events = [
            _ev(0, "postgres-primary", "warning", "connections 90/100", host="pg-1"),
            _ev(
                2,
                "postgres-primary",
                "error",
                "too many connections",
                host="pg-1",
                signature="db_pool_exhausted",
            ),
            _ev(
                4,
                "postgres-primary",
                "error",
                "timeout acquiring connection from pool",
                host="pg-1",
                signature="db_pool_exhausted",
                metric={"name": "active_connections", "value": 100},
            ),
            _ev(
                11,
                "payment-service",
                "error",
                "timeout acquiring connection from pool",
                host="pay-2",
                trace_id="tr_9ac1",
                user_id="u_4821",
                signature="db_pool_exhausted",
                metric={"name": "p95_latency_ms", "value": 2300},
            ),
            _ev(
                13,
                "payment-service",
                "error",
                "timeout acquiring connection from pool",
                host="pay-2",
                trace_id="tr_9ac2",
                user_id="u_4822",
                signature="db_pool_exhausted",
            ),
            _ev(
                19,
                "auth-service",
                "warning",
                "slow queries on postgres-primary",
                host="auth-1",
                trace_id="tr_77b1",
            ),
            _ev(
                21,
                "auth-service",
                "error",
                "slow queries: p95 latency 1800ms",
                host="auth-1",
                metric={"name": "p95_latency_ms", "value": 1800},
            ),
            _ev(
                34,
                "auth-service",
                "error",
                "login failed: upstream timeout",
                host="auth-1",
                trace_id="tr_77b2",
                signature="login_failed",
            ),
            _ev(
                47,
                "api-gateway",
                "error",
                "504 gateway timeout",
                host="gw-1",
                status=504,
                signature="http_5xx",
                metric={"name": "p95_latency_ms", "value": 3100},
            ),
            _ev(
                49,
                "api-gateway",
                "error",
                "502 bad gateway from payment-service",
                host="gw-1",
                status=502,
                signature="http_5xx",
            ),
            _ev(
                55,
                "order-service",
                "error",
                "timeout acquiring connection from pool",
                host="ord-1",
                signature="db_pool_exhausted",
            ),
            _ev(
                68,
                "web-app",
                "error",
                "checkout errors reported by users",
                host="web-1",
                signature="payment_failed",
            ),
            # CDN distractor — separate, no shared trace/user, far in topology.
            # Note: placed at +120s (not +20s as in specsheet §13) because with the
            # spec's 0.45 correlation threshold a +20s CDN event links to the
            # web-app/payment events via the 1-hop cdn->web-app edge and merges.
            _ev(120, "cdn", "warning", "image latency above baseline p95=950ms", host="cdn-1"),
            _ev(125, "cdn", "warning", "image latency above baseline p95=980ms", host="cdn-1"),
            _ev(130, "cdn", "warning", "slow image delivery from edge node", host="cdn-1"),
        ]
        # login failures: 20 distinct users
        for i in range(20):
            events.append(
                _ev(
                    34 + i,
                    "auth-service",
                    "error",
                    "login failed: upstream timeout",
                    host="auth-1",
                    user_id=f"u_{1000 + i}",
                    trace_id=f"tr_login_{i}",
                    signature="login_failed",
                )
            )
        # payment failures: 40 distinct users
        for i in range(40):
            events.append(
                _ev(
                    55 + i,
                    "payment-service",
                    "error",
                    "payment failed: could not persist transaction",
                    host="pay-2",
                    user_id=f"u_{2000 + i}",
                    trace_id=f"tr_pay_{i}",
                    signature="payment_failed",
                    attrs={"status": 500, "endpoint": "/v1/charge"},
                )
            )
        # healthy background noise (info, not anomalous)
        for i in range(12):
            events.append(_ev(i * 7, "web-app", "info", "request served OK", host="web-1"))
    elif scenario == "bad_deploy":
        events = [
            _ev(0, "auth-service", "info", "deploy v2.4.1 started", signature="deploy"),
            _ev(
                5,
                "auth-service",
                "error",
                "login failed: authentication failed",
                user_id="u_3001",
                signature="login_failed",
            ),
            _ev(
                12,
                "auth-service",
                "error",
                "error rate above threshold",
                metric={"name": "error_rate", "value": 0.12},
            ),
            _ev(
                20, "api-gateway", "error", "504 gateway timeout", status=504, signature="http_5xx"
            ),
        ]
        for i in range(8):
            events.append(
                _ev(
                    6 + i,
                    "auth-service",
                    "error",
                    "login failed: authentication failed",
                    user_id=f"u_{3000 + i}",
                    signature="login_failed",
                )
            )
    elif scenario == "cache_failure":
        events = [
            _ev(0, "redis-cache", "error", "connection refused", signature="cache_failure"),
            _ev(
                8,
                "auth-service",
                "warning",
                "slow queries: cache miss storm",
                metric={"name": "p95_latency_ms", "value": 1500},
            ),
            _ev(
                15,
                "auth-service",
                "error",
                "login failed: upstream timeout",
                user_id="u_4001",
                signature="login_failed",
            ),
        ]
        for i in range(8):
            events.append(
                _ev(
                    16 + i,
                    "auth-service",
                    "error",
                    "login failed: upstream timeout",
                    user_id=f"u_{4000 + i}",
                    signature="login_failed",
                )
            )
    else:
        raise ValueError(f"unknown scenario: {scenario}")
    events.sort(key=lambda e: e["offset_seconds"])
    out = []
    for i, e in enumerate(events):
        off = e.pop("offset_seconds")
        ts = base + timedelta(seconds=off)
        d = dict(e)
        d["timestamp"] = ts
        d["id"] = f"evt_sim_{i:04d}"
        # move status into attrs for the normalizer
        if "status" in d:
            d.setdefault("attrs", {})["status"] = d.pop("status")
        out.append(d)
    return out
