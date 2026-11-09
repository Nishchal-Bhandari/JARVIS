"""What-if replay: fixing earlier avoids a share of the impact, and
fixing at +0s avoids everything (same predicates as impact.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core import impact as impact_mod
from app.core.whatif import compute_whatif
from tests.test_golden import _anomalous


def test_whatif_s1():
    events = _anomalous()
    started = min(e["timestamp"] for e in events)
    imp = impact_mod.compute_impact(events, [], {"services": []})
    all_fixed = compute_whatif(events, started, 0)
    assert all_fixed["avoided_users"] == imp["users_affected"], (all_fixed, imp)
    assert all_fixed["avoided_failed_transactions"] == imp["failed_transactions"]
    assert all_fixed["avoided_revenue_inr"] == imp["failed_transactions"] * 500
    assert "assumes the fix works immediately" in all_fixed["note"]
    at_30 = compute_whatif(events, started, 30)
    # All failed payments happen after +30s in S1, so fixing at +30s avoids
    # all of them — but 2 users already hit errors before +30s.
    assert at_30["avoided_failed_transactions"] == imp["failed_transactions"], at_30
    assert 0 < at_30["avoided_users"] < imp["users_affected"], at_30
    assert at_30["total_users"] == imp["users_affected"], at_30
    at_60 = compute_whatif(events, started, 60)
    assert 0 < at_60["avoided_failed_transactions"] < imp["failed_transactions"], at_60
    assert 0 < at_60["avoided_users"] < imp["users_affected"], at_60
