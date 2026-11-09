"""In-memory WebSocket broadcast hub."""

import asyncio
import json

subscribers: set[asyncio.Queue] = set()


def broadcast(message: dict):
    payload = json.dumps(message, default=str)
    for q in list(subscribers):
        try:
            q.put_nowait(payload)
        except Exception:
            pass
