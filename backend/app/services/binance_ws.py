from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable

import websockets

from app.core.config import get_settings

TickerCallback = Callable[[dict], Awaitable[None]]


class BinanceWebSocketClient:
    def __init__(self, callback: TickerCallback, symbols: list[str] | None = None) -> None:
        self.settings = get_settings()
        self.callback = callback
        self.symbols = symbols or ["btcusdt", "ethusdt", "solusdt"]
        self._running = False
        self._task: asyncio.Task | None = None

    def _stream_url(self) -> str:
        streams = "/".join(f"{symbol}@miniTicker" for symbol in self.symbols)
        return f"{self.settings.binance_ws_url}?streams={streams}"

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self) -> None:
        backoff = 3
        while self._running:
            try:
                async with websockets.connect(self._stream_url(), ping_interval=20, ping_timeout=20) as socket:
                    backoff = 3
                    async for message in socket:
                        data = json.loads(message)
                        stream_data = data.get("data", {})
                        await self.callback(stream_data)
                        if not self._running:
                            break
            except asyncio.CancelledError:
                raise
            except Exception:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
