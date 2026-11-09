"""Incident report: template first, LLM second (specsheet §10).
Never sends raw logs to the LLM; only the structured incident summary.
Works with no API key."""

import os


def template_report(incident: dict) -> str:
    rc = incident.get("root_cause") or {}
    impact = incident.get("impact") or {}
    lines = [
        f"# Incident report: {incident.get('title', '')}",
        "",
        "## Summary",
        incident.get("summary", ""),
        "",
        "## Root cause",
        f"- Service: {rc.get('service', 'unknown')}",
        f"- Label: {rc.get('label', 'unknown')}",
        f"- Confidence: {rc.get('confidence', 0)}",
        "",
        "Why we think this:",
    ]
    for ev in rc.get("evidence", []):
        lines.append(f"- {ev}")
    lines += ["", "## Timeline"]
    for stage in incident.get("timeline", []):
        lines.append(
            f"- +{stage.get('offset_seconds', 0):.0f}s: {', '.join(stage.get('services', []))}"
        )
    lines += [
        "",
        "## Impact",
        f"- Affected services: {len(impact.get('affected_services', []))}",
        f"- Users affected: {impact.get('users_affected', 0)}",
        f"- Failed transactions: {impact.get('failed_transactions', 0)}",
        f"- Critical path hit: {impact.get('critical_path_hit', False)}",
        "",
        "## Recommended actions",
    ]
    for rec in incident.get("recommendations", []):
        lines.append(f"{rec.get('priority')}. {rec.get('title')} — {rec.get('detail', '')}")
    lines += [
        "",
        "## Open questions",
        "- Was this root cause confirmed by the on-call engineer? (unknown)",
        "- Are there other services still affected? (unknown)",
    ]
    return "\n".join(lines)


def generate_report(incident: dict) -> tuple[str, str]:
    """Return (markdown, generated_by). LLM path only with a key, 15s timeout."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "")
    if not key or not model:
        return template_report(incident), "template"
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=key, timeout=15)
        summary = {
            k: incident.get(k)
            for k in ("title", "severity", "root_cause", "impact", "timeline", "recommendations")
        }
        msg = client.messages.create(
            model=model,
            max_tokens=800,
            messages=[
                {
                    "role": "user",
                    "content": "Write an incident report from ONLY these facts; say 'unknown' otherwise. "
                    "Sections: Summary, Root cause, Timeline, Impact, Recommended actions, Open questions.\n"
                    f"{summary}",
                }
            ],
        )
        return msg.content[0].text, "llm"
    except Exception:
        return template_report(incident), "template"
