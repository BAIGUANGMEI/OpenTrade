import asyncio
import json
from collections import defaultdict
from typing import Any, DefaultDict, Set

from fastapi import WebSocket


class WebSocketHub:
    def __init__(self) -> None:
        self._channels: DefaultDict[str, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._channels[channel].add(websocket)

    async def disconnect(self, channel: str, websocket: WebSocket) -> None:
        async with self._lock:
            if channel in self._channels and websocket in self._channels[channel]:
                self._channels[channel].remove(websocket)

    async def broadcast(self, channel: str, payload: Any) -> None:
        message = json.dumps(payload, default=str)
        async with self._lock:
            sockets = list(self._channels.get(channel, set()))
        stale: list[WebSocket] = []
        for websocket in sockets:
            try:
                await websocket.send_text(message)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            await self.disconnect(channel, websocket)


ws_hub = WebSocketHub()
