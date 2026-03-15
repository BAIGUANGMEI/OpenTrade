from datetime import datetime

from pydantic import BaseModel


class PositionRead(BaseModel):
    model_config_id: int
    model_name: str
    symbol: str
    quantity: float
    avg_price: float
    market_price: float
    unrealized_pnl: float
    realized_pnl: float
    take_profit: float | None
    stop_loss: float | None
    updated_at: datetime


class OrderRead(BaseModel):
    id: int
    model_config_id: int
    model_name: str
    decision_id: int | None
    symbol: str
    side: str
    quantity: float
    price: float
    fee: float
    slippage_bp: float
    status: str
    created_at: datetime


class NavPoint(BaseModel):
    id: int
    model_config_id: int
    cash_balance: float
    positions_value: float
    total_nav: float
    daily_pnl: float
    created_at: datetime


class ModelPortfolioSummary(BaseModel):
    model_config_id: int
    model_name: str
    initial_capital: float
    cash_balance: float
    positions_value: float
    total_nav: float
    realized_pnl: float
    unrealized_pnl: float


class PortfolioOverview(BaseModel):
    generated_at: datetime
    models: list[ModelPortfolioSummary]
    positions: list[PositionRead]
    recent_orders: list[OrderRead]
