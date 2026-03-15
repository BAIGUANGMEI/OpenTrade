from datetime import datetime

from pydantic import BaseModel


class TickerRead(BaseModel):
    symbol: str
    price: float
    change_percent: float
    event_time: datetime | None


class KlineRead(BaseModel):
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class DashboardSnapshot(BaseModel):
    tickers: list[TickerRead]
    last_decisions: list[dict]
    portfolio: dict
    scheduler: dict
