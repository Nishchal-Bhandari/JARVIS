"""Async simulator playback with speed control (skillbuild P2)."""

import asyncio
from datetime import UTC, datetime

from .scenarios import generate_scenario_events


class Simulator:
    def __init__(self):
        self.running = False
        self.scenario = None
        self.speed = 1.0
        self.progress = 0
        self.total = 0
        self._task = None

    async def start(self, scenario, speed, ingest, broadcast=None, on_done=None):
        if self.running:
            return False
        self.running = True
        self.scenario = scenario
        self.speed = speed
        events = generate_scenario_events(scenario, base=datetime.now(UTC))
        self.total = len(events)
        self.progress = 0

        async def _run():
            prev = 0.0
            try:
                for ev in events:
                    if not self.running:
                        break
                    off = (ev["timestamp"] - events[0]["timestamp"]).total_seconds()
                    wait = max(0.0, (off - prev) / max(speed, 0.1))
                    if wait:
                        await asyncio.sleep(wait)
                    prev = off
                    # Keep the scripted timestamp (start + offset): the
                    # correlation window and timeline then work at any speed.
                    ingest(dict(ev))
                    self.progress += 1
                    if broadcast:
                        broadcast(
                            {
                                "type": "simulator.progress",
                                "progress": self.progress,
                                "total": self.total,
                            }
                        )
            finally:
                self.running = False
                if on_done:
                    on_done()

        self._task = asyncio.create_task(_run())
        return True

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            self._task = None

    def status(self):
        return {
            "running": self.running,
            "scenario": self.scenario,
            "speed": self.speed,
            "progress": self.progress,
            "total": self.total,
        }


simulator = Simulator()
