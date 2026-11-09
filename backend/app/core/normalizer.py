"""Normalizer: JSONL / CSV / raw-log -> canonical events (specsheet §5.1-5.2).
Pure functions. Bad lines are skipped and counted, never crash ingestion."""

import csv
import io
import json
import re
import uuid
from datetime import UTC, datetime

LOG_RE = re.compile(
    r"^(?P<ts>\S+)\s+(?P<level>[A-Z]+)\s+(?P<service>[\w\-.]+)\s*[:\-]?\s*(?P<msg>.*)$"
)
LEVEL_SEV = {
    "DEBUG": "info",
    "INFO": "info",
    "WARN": "warning",
    "WARNING": "warning",
    "ERROR": "error",
    "CRITICAL": "critical",
    "FATAL": "critical",
}


def _parse_ts(value):
    if value is None:
        return datetime.now(UTC)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    s = str(value).strip()
    try:
        dt = datetime.fromisoformat(s)  # py3.11+ handles trailing Z
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    except ValueError:
        return datetime.now(UTC)


def _infer_severity(message: str, level=None):
    if level:
        return LEVEL_SEV.get(level.upper(), "info")
    m = (message or "").lower()
    if any(k in m for k in ("critical", "fatal", "failed", "error", "timeout", "too many")):
        return "error"
    if any(k in m for k in ("warn", "slow", "latency", "above baseline")):
        return "warning"
    return "info"


def _extract_tokens(msg: str, attrs: dict):
    for key in ("user", "trace", "status", "latency"):
        m = re.search(rf"{key}=([^\s,]+)", msg or "")
        if m:
            attrs[key] = m.group(1)
    return attrs


def canonical(raw: dict, source: str = "api") -> dict:
    """One dict-like event -> canonical event dict."""
    msg = raw.get("message") or raw.get("msg") or ""
    metric = raw.get("metric")
    if raw.get("metric_name"):
        metric = {"name": raw["metric_name"], "value": float(raw.get("metric_value") or 0)}
    attrs = dict(raw.get("attrs") or {})
    for k in ("endpoint", "status"):
        if k in raw:
            attrs[k] = raw[k]
    _extract_tokens(str(msg), attrs)
    sev = raw.get("severity") or _infer_severity(str(msg), raw.get("level"))
    return {
        "id": raw.get("id") or f"evt_{uuid.uuid4().hex[:12]}",
        "timestamp": _parse_ts(raw.get("timestamp") or raw.get("ts")),
        "source": source,
        "service": raw.get("service") or "unmapped",
        "host": raw.get("host"),
        "type": raw.get("type") or ("metric" if metric else "log"),
        "severity": sev.lower(),
        "message": str(msg),
        "metric": metric,
        "user_id": raw.get("user_id") or attrs.pop("user", None),
        "trace_id": raw.get("trace_id") or attrs.pop("trace", None),
        "signature": raw.get("signature"),
        "attrs": attrs,
    }


def parse_jsonl(text: str, source: str = "file"):
    events, errors = [], []
    for i, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if not isinstance(obj, dict) or not obj.get("service"):
                raise ValueError("missing service")
            events.append(canonical(obj, source))
        except Exception as e:
            errors.append(f"line {i}: {e}")
    return events, errors


def parse_csv(text: str, source: str = "file"):
    events, errors = [], []
    reader = csv.DictReader(io.StringIO(text))
    for i, row in enumerate(reader, 2):
        try:
            if not (row.get("service") or "").strip():
                raise ValueError("missing service")
            events.append(canonical(row, source))
        except Exception as e:
            errors.append(f"line {i}: {e}")
    return events, errors


def parse_log(text: str, source: str = "file"):
    events, errors = [], []
    for i, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        m = LOG_RE.match(line.strip())
        if not m:
            errors.append(f"line {i}: could not parse")
            continue
        msg = m.group("msg")
        attrs = {}
        _extract_tokens(msg, attrs)
        events.append(
            canonical(
                {
                    "timestamp": m.group("ts"),
                    "level": m.group("level"),
                    "service": m.group("service"),
                    "message": msg,
                    "user_id": attrs.pop("user", None),
                    "trace_id": attrs.pop("trace", None),
                    "attrs": attrs,
                },
                source,
            )
        )
    return events, errors


def parse_upload(text: str, filename: str, source: str = "file"):
    name = (filename or "").lower()
    if name.endswith((".jsonl", ".json")):
        return parse_jsonl(text, source)
    if name.endswith(".csv"):
        return parse_csv(text, source)
    # sniff: JSONL if first non-empty line starts with {
    first = next((l for l in text.splitlines() if l.strip()), "")
    if first.strip().startswith("{"):
        return parse_jsonl(text, source)
    if "," in first and "service" in first:
        return parse_csv(text, source)
    return parse_log(text, source)
