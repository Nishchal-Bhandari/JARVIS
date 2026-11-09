"""Copilot Q&A grounded in one incident's structured data (specsheet §12.3).
No-LLM fallback: intent matching over the same JSON."""

from .llm import complete


def answer_question(incident: dict, question: str) -> dict:
    q = (question or "").lower()
    rc = incident.get("root_cause") or {}
    impact = incident.get("impact") or {}
    timeline = incident.get("timeline") or []
    recs = incident.get("recommendations") or []
    if any(k in q for k in ("why", "cause", "root")):
        answer = (
            f"The most likely cause is {rc.get('service')} — {rc.get('label')} "
            f"(confidence {rc.get('confidence')}). Evidence: "
            + "; ".join(rc.get("evidence", [])[:3])
        )
        based = ["root_cause"]
    elif any(k in q for k in ("who", "affect", "user", "impact")):
        answer = (
            f"{len(impact.get('affected_services', []))} services affected "
            f"({', '.join(impact.get('affected_services', []))}), "
            f"{impact.get('users_affected')} users affected, "
            f"{impact.get('failed_transactions')} failed transactions."
        )
        based = ["impact"]
    elif any(k in q for k in ("first", "do", "fix", "recommend")):
        first = recs[0] if recs else {}
        answer = f"First: {first.get('title', 'check the root-cause service')} — {first.get('detail', '')}"
        based = ["recommendations"]
    elif "timeline" in q or "spread" in q or "when" in q:
        stages = "; ".join(
            f"+{s.get('offset_seconds', 0):.0f}s {', '.join(s.get('services', []))}"
            for s in timeline
        )
        answer = f"The failure spread: {stages}" if stages else "No timeline stages recorded."
        based = ["timeline"]
    elif "confiden" in q:
        answer = (
            f"Confidence is {rc.get('confidence')} for {rc.get('service')}. "
            "It is high when the earliest anomaly, the dependency direction and the "
            "signature all point at the same service."
        )
        based = ["root_cause"]
    else:
        answer = (
            f"This incident's most likely cause is {rc.get('service')} "
            f"({rc.get('label')}), confidence {rc.get('confidence')}. "
            f"{impact.get('users_affected')} users affected."
        )
        based = ["root_cause", "impact"]
    # LLM path (optional, fact-only, 15s timeout) — only if a key is set.
    # Uses OpenRouter; default model is free, so limited credits are safe.
    summary = {
        k: incident.get(k)
        for k in (
            "title",
            "severity",
            "root_cause",
            "impact",
            "timeline",
            "recommendations",
        )
    }
    llm_answer = complete(
        "Answer ONLY from these incident facts; say 'unknown' otherwise.\n"
        f"Facts: {summary}\nQuestion: {question}",
        max_tokens=400,
    )
    if llm_answer:
        return {"answer": llm_answer, "based_on": based}
    return {"answer": answer, "based_on": based}
