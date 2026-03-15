from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.decision import Decision
from app.models.order import Order
from app.models.position import Position
from app.services.portfolio_service import portfolio_service

FEE_RATE = 0.0005
SLIPPAGE_BP = 10.0


class PaperExecutor:
    def _price_with_slippage(self, price: float, side: str) -> float:
        adjustment = SLIPPAGE_BP / 10000
        if side == "BUY":
            return price * (1 + adjustment)
        return price * (1 - adjustment)

    def execute(self, db: Session, decision: Decision, market_price: float | None) -> Order | None:
        if decision.action == "HOLD" or not decision.symbol or not market_price:
            return None

        cash_account = portfolio_service.ensure_cash_account(db, decision.model_config_id)
        position = db.scalar(
            select(Position).where(
                Position.model_config_id == decision.model_config_id,
                Position.symbol == decision.symbol,
            )
        )

        if decision.action == "BUY":
            open_positions = list(
                db.scalars(
                    select(Position).where(
                        Position.model_config_id == decision.model_config_id,
                        Position.quantity > 0,
                    )
                ).all()
            )
            nav = cash_account.cash_balance + sum(item.market_price * item.quantity for item in open_positions)
            spend = min(cash_account.cash_balance, nav * decision.buy_pct)
            if spend <= 0:
                return None
            fill_price = self._price_with_slippage(market_price, "BUY")
            fee = spend * FEE_RATE
            net_spend = max(spend - fee, 0)
            quantity = net_spend / fill_price if fill_price else 0
            if quantity <= 0:
                return None
            cash_account.cash_balance -= spend
            if position:
                total_cost = (position.avg_price * position.quantity) + net_spend
                new_qty = position.quantity + quantity
                position.avg_price = total_cost / new_qty
                position.quantity = new_qty
                position.market_price = market_price
                position.take_profit = decision.take_profit
                position.stop_loss = decision.stop_loss
            else:
                position = Position(
                    model_config_id=decision.model_config_id,
                    symbol=decision.symbol,
                    quantity=quantity,
                    avg_price=fill_price,
                    market_price=market_price,
                    take_profit=decision.take_profit,
                    stop_loss=decision.stop_loss,
                )
                db.add(position)
            order = Order(
                model_config_id=decision.model_config_id,
                decision_id=decision.id,
                symbol=decision.symbol,
                side="BUY",
                quantity=quantity,
                price=fill_price,
                fee=fee,
                slippage_bp=SLIPPAGE_BP,
            )
            db.add(order)
            return order

        if not position or position.quantity <= 0:
            return None
        fill_price = self._price_with_slippage(market_price, "SELL")
        sell_qty = position.quantity * decision.sell_pct
        if decision.sell_pct <= 0 or sell_qty <= 0:
            sell_qty = position.quantity
        proceeds = sell_qty * fill_price
        fee = proceeds * FEE_RATE
        cash_account.cash_balance += max(proceeds - fee, 0)
        realized = (fill_price - position.avg_price) * sell_qty
        position.quantity -= sell_qty
        position.market_price = market_price
        position.realized_pnl += realized - fee
        if position.quantity <= 1e-10:
            db.delete(position)
        order = Order(
            model_config_id=decision.model_config_id,
            decision_id=decision.id,
            symbol=decision.symbol,
            side="SELL",
            quantity=sell_qty,
            price=fill_price,
            fee=fee,
            slippage_bp=SLIPPAGE_BP,
        )
        db.add(order)
        return order

    def apply_take_profit_stop_loss(self, db: Session, price_lookup: dict[str, float]) -> list[Order]:
        forced_orders: list[Order] = []
        positions = list(db.scalars(select(Position).where(Position.quantity > 0)).all())
        for position in positions:
            market_price = price_lookup.get(position.symbol)
            if not market_price:
                continue
            should_sell = bool(position.take_profit and market_price >= position.take_profit) or bool(
                position.stop_loss and market_price <= position.stop_loss
            )
            if not should_sell:
                continue
            decision = Decision(
                model_config_id=position.model_config_id,
                symbol=position.symbol,
                action="SELL",
                buy_pct=0.0,
                sell_pct=1.0,
                take_profit=position.take_profit,
                stop_loss=position.stop_loss,
                confidence=1.0,
                reason="Auto exit by take-profit/stop-loss",
                status="auto_exit",
                raw_response="{}",
            )
            db.add(decision)
            db.flush()
            order = self.execute(db, decision, market_price)
            if order:
                forced_orders.append(order)
        return forced_orders


paper_executor = PaperExecutor()
