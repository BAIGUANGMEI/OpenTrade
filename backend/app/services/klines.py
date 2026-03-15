from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.time import timestamp_to_app_timezone


class KlineService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def fetch_klines(self, symbol: str, interval: str = "1m", limit: int = 60) -> list[dict]:
        url = f"{self.settings.binance_rest_url}/api/v3/klines"
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
        return [
            {
                "open_time": timestamp_to_app_timezone(item[0] / 1000),
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5]),
            }
            for item in payload
        ]
