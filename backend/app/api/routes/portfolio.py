from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.time import utc_to_app_timezone
from app.services.market_service import market_service
from app.services.portfolio_service import portfolio_service

router = APIRouter()


@router.get("/overview")
def get_portfolio_overview(db: Session = Depends(get_db)) -> dict:
    prices = {item["symbol"]: item["price"] for item in market_service.get_ticker_list() if item["price"]}
    return portfolio_service.get_overview(db, prices)


@router.get("/nav/{model_config_id}")
def get_nav_series(model_config_id: int, limit: int = 100, db: Session = Depends(get_db)) -> list[dict]:
    series = portfolio_service.get_nav_series(db, model_config_id, limit=limit)
    return [
        {
            "id": item.id,
            "model_config_id": item.model_config_id,
            "cash_balance": item.cash_balance,
            "positions_value": item.positions_value,
            "total_nav": item.total_nav,
            "daily_pnl": item.daily_pnl,
            "created_at": utc_to_app_timezone(item.created_at),
        }
        for item in series
    ]
