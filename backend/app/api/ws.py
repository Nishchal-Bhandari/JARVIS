"""WebSocket /ws/stream (specsheet §11)."""

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .broadcast import subscribers

router = APIRouter()


@router.websocket("/ws/stream")
async def stream(ws: WebSocket):
    await ws.accept()
    q: asyncio.Queue = asyncio.Queue()
    subscribers.add(q)
    try:
        while True:
            msg = await q.get()
            await ws.send_text(msg)
    except WebSocketDisconnect:
        pass
    finally:
        subscribers.discard(q)
