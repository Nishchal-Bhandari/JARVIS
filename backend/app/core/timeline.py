"""Propagation timeline (specsheet §9). Pure functions."""

from collections import defaultdict


def build_timeline(events, dependencies):
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
    return stages
