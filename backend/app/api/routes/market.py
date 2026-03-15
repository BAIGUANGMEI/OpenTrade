from fastapi import APIRouter

from app.services.market_service import market_service

router = APIRouter()


@router.get("/tickers")
def get_tickers() -> list[dict]:
    return market_service.get_ticker_list()


@router.get("/klines/{symbol}")
async def get_klines(symbol: str, interval: str = "1m", limit: int = 60) -> list[dict]:
    return await market_service.kline_service.fetch_klines(symbol.upper(), interval=interval, limit=limit)
