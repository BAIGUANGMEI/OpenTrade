from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.time import app_now, utc_to_app_timezone
from app.models.model_config import ModelConfig
from app.models.order import Order
from app.models.portfolio_cash import PortfolioCash
from app.models.portfolio_nav import PortfolioNav
from app.models.position import Position


class PortfolioService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def ensure_cash_account(self, db: Session, model_config_id: int) -> PortfolioCash:
        account = db.scalar(select(PortfolioCash).where(PortfolioCash.model_config_id == model_config_id))
        if account:
            return account
        account = PortfolioCash(model_config_id=model_config_id, cash_balance=self.settings.initial_cash_usdt)
        db.add(account)
        db.flush()
        return account

    def get_positions(self, db: Session, model_config_id: int | None = None) -> list[Position]:
        query = select(Position)
        if model_config_id is not None:
            query = query.where(Position.model_config_id == model_config_id)
        return list(db.scalars(query.order_by(Position.updated_at.desc())).all())

    def refresh_position_marks(self, db: Session, model_config_id: int, price_lookup: dict[str, float]) -> tuple[float, float]:
        positions_value = 0.0
        unrealized = 0.0
        positions = self.get_positions(db, model_config_id)
        for position in positions:
            market_price = price_lookup.get(position.symbol, position.market_price or position.avg_price)
            position.market_price = market_price
            position.unrealized_pnl = (market_price - position.avg_price) * position.quantity
            positions_value += market_price * position.quantity
            unrealized += position.unrealized_pnl
        return positions_value, unrealized

    def record_nav(self, db: Session, model_config_id: int, price_lookup: dict[str, float]) -> PortfolioNav:
        cash_account = self.ensure_cash_account(db, model_config_id)
        positions_value, _ = self.refresh_position_marks(db, model_config_id, price_lookup)
        total_nav = cash_account.cash_balance + positions_value
        latest = db.scalar(
            select(PortfolioNav)
            .where(PortfolioNav.model_config_id == model_config_id)
            .order_by(desc(PortfolioNav.created_at))
        )
        baseline = latest.total_nav if latest else self.settings.initial_cash_usdt
        nav = PortfolioNav(
            model_config_id=model_config_id,
            cash_balance=cash_account.cash_balance,
            positions_value=positions_value,
            total_nav=total_nav,
            daily_pnl=total_nav - baseline,
        )
        db.add(nav)
        db.flush()
        return nav

    def get_overview(self, db: Session, price_lookup: dict[str, float]) -> dict:
        models = list(db.scalars(select(ModelConfig).order_by(ModelConfig.name)).all())
        model_name_by_id = {model.id: model.name for model in models}
        model_summaries = []
        all_positions = []
        for model in models:
            cash = self.ensure_cash_account(db, model.id)
            positions_value, unrealized = self.refresh_position_marks(db, model.id, price_lookup)
            positions = self.get_positions(db, model.id)
            realized = sum(item.realized_pnl for item in positions)
            all_positions.extend(
                [
                    {
                        "model_config_id": item.model_config_id,
                        "model_name": model_name_by_id.get(item.model_config_id, f"Model #{item.model_config_id}"),
                        "symbol": item.symbol,
                        "quantity": item.quantity,
                        "avg_price": item.avg_price,
                        "market_price": item.market_price,
                        "unrealized_pnl": item.unrealized_pnl,
                        "realized_pnl": item.realized_pnl,
                        "take_profit": item.take_profit,
                        "stop_loss": item.stop_loss,
                        "updated_at": utc_to_app_timezone(item.updated_at),
                    }
                    for item in positions
                ]
            )
            model_summaries.append(
                {
                    "model_config_id": model.id,
                    "model_name": model.name,
                    "initial_capital": self.settings.initial_cash_usdt,
                    "cash_balance": cash.cash_balance,
                    "positions_value": positions_value,
                    "total_nav": cash.cash_balance + positions_value,
                    "realized_pnl": realized,
                    "unrealized_pnl": unrealized,
                }
            )
        recent_orders = list(db.scalars(select(Order).order_by(Order.created_at.desc()).limit(30)).all())
        return {
            "generated_at": app_now(),
            "models": model_summaries,
            "positions": all_positions,
            "recent_orders": [
                {
                    "id": item.id,
                    "model_config_id": item.model_config_id,
                    "model_name": model_name_by_id.get(item.model_config_id, f"Model #{item.model_config_id}"),
                    "decision_id": item.decision_id,
                    "symbol": item.symbol,
                    "side": item.side,
                    "quantity": item.quantity,
                    "price": item.price,
                    "fee": item.fee,
                    "slippage_bp": item.slippage_bp,
                    "status": item.status,
                    "created_at": utc_to_app_timezone(item.created_at),
                }
                for item in recent_orders
            ],
        }

    def get_nav_series(self, db: Session, model_config_id: int, limit: int = 100) -> list[PortfolioNav]:
        return list(
            db.scalars(
                select(PortfolioNav)
                .where(PortfolioNav.model_config_id == model_config_id)
                .order_by(PortfolioNav.created_at.desc())
                .limit(limit)
            ).all()
        )[::-1]


portfolio_service = PortfolioService()
