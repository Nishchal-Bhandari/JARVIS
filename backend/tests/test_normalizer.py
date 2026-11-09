"""Normalizer tests (specsheet §5.2)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.normalizer import parse_csv, parse_jsonl, parse_log

LOG = """2026-11-09T10:15:00Z WARN  postgres-primary connections 90/100 host=pg-1
2026-11-09T10:15:02Z ERROR postgres-primary too many connections host=pg-1
not a log line at all
2026-11-09T10:15:13Z ERROR payment-service timeout acquiring connection from pool trace=tr_9ac1 user=u_4821 latency=2300ms
"""


def test_parse_log():
    events, errors = parse_log(LOG)
    assert len(events) == 3
    assert len(errors) == 1
    assert events[0]["service"] == "postgres-primary"
    assert events[0]["severity"] == "warning"
    assert events[2]["user_id"] == "u_4821"
    assert events[2]["trace_id"] == "tr_9ac1"


def test_parse_jsonl():
    text = '{"timestamp":"2026-11-09T10:15:02Z","service":"auth-service","message":"login failed"}\nbad json\n'
    events, errors = parse_jsonl(text)
    assert len(events) == 1
    assert len(errors) == 1
    assert events[0]["severity"] == "error"  # inferred from "failed"


def test_parse_csv():
    text = "timestamp,service,severity,message,user_id\n2026-11-09T10:15:02Z,auth-service,error,login failed,u_1\n"
    events, errors = parse_csv(text)
    assert len(events) == 1 and not errors
    assert events[0]["user_id"] == "u_1"
