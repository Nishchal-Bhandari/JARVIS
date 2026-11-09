"""make seed: write S1 events to sample_data/payment_outage.{jsonl,log,csv}."""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from app.simulator.scenarios import generate_scenario_events  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "sample_data")
os.makedirs(OUT, exist_ok=True)

events = generate_scenario_events("db_pool_exhaustion", seed=42)

with open(os.path.join(OUT, "payment_outage.jsonl"), "w") as f:
    for e in events:
        d = dict(e)
        d["timestamp"] = d["timestamp"].isoformat().replace("+00:00", "Z")
        f.write(json.dumps(d) + "\n")

with open(os.path.join(OUT, "payment_outage.log"), "w") as f:
    for e in events:
        extra = ""
        if e.get("user_id"):
            extra += f" user={e['user_id']}"
        if e.get("trace_id"):
            extra += f" trace={e['trace_id']}"
        f.write(f"{e['timestamp'].isoformat().replace('+00:00', 'Z')} "
                f"{e['severity'].upper()} {e['service']} {e['message']}{extra}\n")

with open(os.path.join(OUT, "payment_outage.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["timestamp", "service", "severity", "message", "user_id", "trace_id"])
    for e in events:
        w.writerow([e["timestamp"].isoformat().replace("+00:00", "Z"), e["service"],
                    e["severity"], e["message"], e.get("user_id", ""), e.get("trace_id", "")])

print(f"wrote {len(events)} events to {OUT}")
