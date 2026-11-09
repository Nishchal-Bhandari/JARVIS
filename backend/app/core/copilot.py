"""Copilot Q&A grounded in one incident's structured data (specsheet §12.3).
No-LLM fallback: intent matching over the same JSON."""

import os


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
    # LLM path (optional, fact-only, 15s timeout) — only if a key is set
    if os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("LLM_MODEL"):
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=15)
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
            msg = client.messages.create(
                model=os.environ["LLM_MODEL"],
                max_tokens=400,
                messages=[
                    {
                        "role": "user",
                        "content": "Answer ONLY from these incident facts; say 'unknown' otherwise.\n"
                        f"Facts: {summary}\nQuestion: {question}",
                    }
                ],
            )
            return {"answer": msg.content[0].text, "based_on": based}
        except Exception:
            pass
    return {"answer": answer, "based_on": based}
