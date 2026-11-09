"""Root-cause scoring (specsheet §7). Pure functions.
Edge A->B means A depends on B, so a failure in B propagates to A."""

import math
from collections import defaultdict

SEV_NORM = {"info": 0.0, "warning": 0.33, "error": 0.66, "critical": 1.0}


def dependency_closure(dependencies):
    """dependents[s] = services that transitively depend on s."""
    dependents = defaultdict(set)
    # reverse edges: B -> A if A depends on B
    rev = defaultdict(set)
    nodes = set()
    for d in dependencies:
        rev[d["to"]].add(d["from"])
        nodes.add(d["from"])
        nodes.add(d["to"])
    for s in nodes:
        seen, stack = set(), list(rev.get(s, []))
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            stack.extend(rev.get(n, []))
        dependents[s] = seen
    return dependents


def score_root_cause(events, dependencies, rules):
    """Return {service, label, confidence, evidence, alternatives}."""
    services = sorted({e["service"] for e in events})
    if not services:
        return None
    first_seen = {}
    peak_sev = {}
    sig_by_service = defaultdict(list)
    for e in events:
        s = e["service"]
        if s not in first_seen or e["timestamp"] < first_seen[s]:
            first_seen[s] = e["timestamp"]
        peak_sev[s] = max(peak_sev.get(s, 0), SEV_NORM.get(e.get("severity", "info"), 0))
        if e.get("signature"):
            sig_by_service[s].append(e["signature"])
    ordered = sorted(services, key=lambda s: first_seen[s])
    n = len(services)
    dependents = dependency_closure(dependencies)
    rule_by_id = {r["id"]: r for r in rules}
    raw, factors = {}, {}
    for idx, s in enumerate(ordered):
        earliness = 1.0 if n == 1 else 1 - idx / (n - 1)
        others = [o for o in services if o != s]
        upstream = len([o for o in others if o in dependents.get(s, set())]) / max(len(others), 1)
        sig = 0.0
        for sig_id in sig_by_service.get(s, []):
            sig = max(sig, float(rule_by_id.get(sig_id, {}).get("prior", 0.5)))
        raw[s] = 0.35 * earliness + 0.35 * upstream + 0.20 * sig + 0.10 * peak_sev.get(s, 0)
        factors[s] = (earliness, upstream, sig, peak_sev.get(s, 0))
    # softmax confidence, temperature 0.15
    exps = {s: math.exp(v / 0.15) for s, v in raw.items()}
    total = sum(exps.values())
    conf = {s: exps[s] / total for s in raw}
    top = max(services, key=lambda s: conf[s])
    t0 = first_seen[top]
    evidence = []
    if factors[top][0] == 1.0:
        evidence.append(f"First anomaly in the incident at {t0.strftime('%H:%M:%S')}")
    else:
        evidence.append(f"Early anomaly at {t0.strftime('%H:%M:%S')}")
    n_dep = len([o for o in services if o != top and o in dependents.get(top, set())])
    if n_dep:
        evidence.append(f"{n_dep} of the other {len(services) - 1} affected services depend on it")
    for sig_id in sig_by_service.get(top, [])[:1]:
        rule = rule_by_id.get(sig_id)
        if rule:
            evidence.append(f"Matched signature: '{rule['label']}'")
        else:
            evidence.append(f"Matched signature: '{sig_id}'")
    # a real observed metric/message line, if any
    top_events = [e for e in events if e["service"] == top and e.get("message")]
    if top_events:
        evidence.append(f"Observed: '{top_events[0]['message'][:90]}'")
    if peak_sev.get(top, 0) >= 0.66:
        evidence.append("Peak severity on this service was error or critical")
    label = "Unknown cause"
    for sig_id in sig_by_service.get(top, []):
        if sig_id in rule_by_id:
            label = rule_by_id[sig_id]["label"]
            break
    # Runner-up candidates, with the plain-English reasons they lost.
    # Each reason compares the candidate's factor against the winner's,
    # so "why not X?" is answered from the same scoring, not invented.
    top_dep_n = len([o for o in services if o != top and o in dependents.get(top, set())])
    alternatives = []
    for s in sorted(services, key=lambda s: -conf[s]):
        if s == top:
            continue
        f = factors[s]
        why_not = []
        delay = (first_seen[s] - t0).total_seconds()
        if delay > 0:
            why_not.append(f"First anomaly {delay:.0f}s after {top}")
        dep_n = len([o for o in services if o != s and o in dependents.get(s, set())])
        if dep_n < top_dep_n:
            why_not.append(
                f"Only {dep_n} of {len(services) - 1} affected services depend on it "
                f"(vs {top_dep_n} for {top})"
            )
        if f[2] == 0:
            why_not.append("No matching failure signature")
        if f[3] < 0.66:
            sev = "warning" if f[3] >= 0.33 else "info"
            why_not.append(f"Peak severity was only {sev}, not error")
        alternatives.append(
            {
                "service": s,
                "confidence": round(conf[s], 3),
                "score": round(raw[s], 3),
                "factors": {
                    "earliness": round(f[0], 2),
                    "upstream": round(f[1], 2),
                    "signature": round(f[2], 2),
                    "severity": round(f[3], 2),
                },
                "why_not": why_not[:2],
            }
        )
    alternatives = alternatives[:3]
    return {
        "service": top,
        "label": label,
        "confidence": round(conf[top], 3),
        "evidence": evidence[:5],
        "alternatives": alternatives,
    }
