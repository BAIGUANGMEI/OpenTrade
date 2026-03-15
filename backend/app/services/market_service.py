from __future__ import annotations

from app.core.ws import ws_hub
from app.core.time import timestamp_to_app_timezone
from app.services.binance_ws import BinanceWebSocketClient
from app.services.indicator_service import compute_indicators
from app.services.klines import KlineService


class MarketService:
    def __init__(self) -> None:
        self.tickers: dict[str, dict] = {}
        self.kline_service = KlineService()
        self.ws_client = BinanceWebSocketClient(self.handle_ticker)

    async def start(self) -> None:
        await self.ws_client.start()

    async def stop(self) -> None:
        await self.ws_client.stop()

    async def handle_ticker(self, payload: dict) -> None:
        symbol = payload.get("s")
        if not symbol:
            return
        self.tickers[symbol] = {
            "symbol": symbol,
            "price": float(payload.get("c", 0)),
            "change_percent": float(payload.get("P", 0)),
            "event_time": timestamp_to_app_timezone(payload.get("E", 0) / 1000) if payload.get("E") else None,
        }
        await ws_hub.broadcast(
            "market",
            {
                "type": "tickers",
                "data": self.get_ticker_list(),
            },
        )

    def get_ticker_list(self) -> list[dict]:
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        result = []
        for symbol in symbols:
            result.append(
                self.tickers.get(
                    symbol,
                    {"symbol": symbol, "price": 0.0, "change_percent": 0.0, "event_time": None},
                )
            )
        return result

    def get_price(self, symbol: str) -> float | None:
        ticker = self.tickers.get(symbol)
        return None if not ticker else ticker["price"]

    async def get_symbol_context(self, symbol: str) -> dict:
        klines_1m = await self.kline_service.fetch_klines(symbol, interval="1m", limit=60)
        klines_5m = await self.kline_service.fetch_klines(symbol, interval="5m", limit=60)
        klines_15m = await self.kline_service.fetch_klines(symbol, interval="15m", limit=60)
        return {
            "symbol": symbol,
            "ticker": self.tickers.get(symbol, {"symbol": symbol, "price": 0.0, "change_percent": 0.0, "event_time": None}),
            "klines": {"1m": klines_1m, "5m": klines_5m, "15m": klines_15m},
            "indicators": {
                "1m": compute_indicators(klines_1m),
                "5m": compute_indicators(klines_5m),
                "15m": compute_indicators(klines_15m),
            },
        }


market_service = MarketService()
