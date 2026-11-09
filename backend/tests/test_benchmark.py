"""Benchmark smoke test: small matrix runs end to end and reports honestly."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core import benchmark as bench_mod
from app.core.anomaly import load_rules
from tests.test_golden import TOPO


def test_benchmark_small_matrix():
    res = bench_mod.run_benchmark(
        TOPO,
        load_rules(),
        services=["redis-cache", "postgres-primary"],
        faults=["cache_failure", "pool_exhaustion"],
        seeds=(42,),
    )
    assert res["total_runs"] == 4, res
    assert res["correct"] == 4, res
    assert res["accuracy_pct"] == 100.0, res
    assert res["avg_time_to_detect_s"] is not None, res
    assert res["misses"] == [], res
    row = res["rows"][0]
    assert row["correct"] is True and row["time_to_detect_s"] is not None, row
