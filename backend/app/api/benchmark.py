"""Benchmark endpoints: run the fault-injector matrix and report accuracy."""

from fastapi import APIRouter
from pydantic import BaseModel

from ..core import benchmark as bench_mod
from ..core.anomaly import load_rules
from ..core.engine import load_topology
from ..db import SessionLocal

router = APIRouter()
LAST = {"result": None}


class BenchmarkRunIn(BaseModel):
    seeds: list[int] = [42, 43, 44, 45, 46]


@router.post("/benchmark/run")
def run(payload: BenchmarkRunIn):
    db = SessionLocal()
    try:
        topology = load_topology(db)
    finally:
        db.close()
    result = bench_mod.run_benchmark(topology, load_rules(), seeds=tuple(payload.seeds))
    LAST["result"] = result
    return result


@router.get("/benchmark/latest")
def latest():
    return LAST["result"] or {"total_runs": 0, "rows": [], "misses": []}
