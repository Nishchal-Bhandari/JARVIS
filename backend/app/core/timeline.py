"""Propagation timeline (specsheet §9). Pure functions."""

from collections import defaultdict


def build_timeline(events, dependencies, change_events=None):
    first = {}
    for e in sorted(events, key=lambda x: x["timestamp"]):
        s = e["service"]
        if s not in first:
            first[s] = e["timestamp"]
    if not first:
        return []
    t0 = min(first.values())
    buckets = defaultdict(list)
    for s, t in first.items():
        buckets[int((t - t0).total_seconds() // 15)].append(s)
    stages = []
    for b in sorted(buckets):
        services = sorted(buckets[b], key=lambda s: first[s])
        key = [e["message"] for e in events if e["service"] in services][:3]
        stages.append(
            {
                "t": min(first[s] for s in services),
                "offset_seconds": float((min(first[s] for s in services) - t0).total_seconds()),
                "services": services,
                "key_events": key,
            }
        )
    # Suspect-change markers sit before the first anomaly (negative offset).
    for c in sorted(change_events or [], key=lambda x: x["timestamp"]):
        stages.append(
            {
                "t": c["timestamp"],
                "offset_seconds": float((c["timestamp"] - t0).total_seconds()),
                "services": [c["service"]],
                "key_events": [c.get("label", c.get("message", "change"))],
                "marker": True,
            }
        )
    stages.sort(key=lambda s: s["offset_seconds"])
    return stages
