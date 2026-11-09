"""Weighted pairwise correlation + union-find clustering (specsheet §6).
Pure functions. Edge A->B means A depends on B; hops are undirected."""

import math
import re
from collections import defaultdict

TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str):
    return set(TOKEN_RE.findall((text or "").lower()))


def text_sim(a: str, b: str) -> float:
    """TF-IDF cosine approximated by token overlap (Jaccard) — deterministic, no deps."""
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def hops(graph, a: str, b: str):
    """Undirected shortest path length; None if disconnected/unmapped."""
    if a == b:
        return 0
    if a not in graph or b not in graph:
        return None
    seen, frontier, d = {a}, [a], 0
    while frontier:
        d += 1
        nxt = []
        for node in frontier:
            for nb in graph.get(node, set()):
                if nb == b:
                    return d
                if nb not in seen:
                    seen.add(nb)
                    nxt.append(nb)
        frontier = nxt
    return None


def build_graph(dependencies):
    g = defaultdict(set)
    for dep in dependencies:
        a, b = dep["from"], dep["to"]
        g[a].add(b)
        g[b].add(a)
        g.setdefault(a, set())
        g.setdefault(b, set())
    return dict(g)


def pair_weight(e1, e2, graph, threshold=0.45):
    dt = abs((e1["timestamp"] - e2["timestamp"]).total_seconds())
    time_prox = math.exp(-dt / 120.0)
    h = hops(graph, e1["service"], e2["service"])
    topo_prox = 1.0 / (1 + h) if h is not None else 0.0
    if e1.get("trace_id") and e1.get("trace_id") == e2.get("trace_id"):
        shared = 1.0
    elif e1.get("user_id") and e1.get("user_id") == e2.get("user_id") and dt <= 60:
        shared = 0.6
    elif e1.get("host") and e1.get("host") == e2.get("host"):
        shared = 0.4
    else:
        shared = 0.0
    w = (
        0.40 * time_prox
        + 0.35 * topo_prox
        + 0.15 * shared
        + 0.10 * text_sim(e1.get("message", ""), e2.get("message", ""))
    )
    return w


class UnionFind:
    def __init__(self, items):
        self.parent = {i: i for i in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def cluster_events(events, dependencies, threshold=0.45):
    """Return list of clusters (lists of events). Only anomalous events are clustered
    by the caller. Clusters need >=3 events; >=2 services is a normal incident,
    a single-service cluster with >=3 events is kept as a low-severity cluster
    (so the CDN distractor stays visible and separate, specsheet §15)."""
    graph = build_graph(dependencies)
    evs = sorted(events, key=lambda e: e["timestamp"])
    uf = UnionFind([e["id"] for e in evs])
    for i, e1 in enumerate(evs):
        for e2 in evs[i + 1 :]:
            dt = abs((e1["timestamp"] - e2["timestamp"]).total_seconds())
            if dt > 300:
                break
            if pair_weight(e1, e2, graph, threshold) >= threshold:
                uf.union(e1["id"], e2["id"])
    groups = defaultdict(list)
    for e in evs:
        groups[uf.find(e["id"])].append(e)
    clusters = [g for g in groups.values() if len(g) >= 3]
    return clusters
