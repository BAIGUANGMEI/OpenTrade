from __future__ import annotations

import asyncio
import json
from time import perf_counter

from pydantic import ValidationError
from sqlalchemy import delete, select

from app.core.config import get_settings
from app.core.database import db_session
from app.core.time import app_now, utc_now, utc_to_app_timezone
from app.core.ws import ws_hub
from app.models.audit_log import AuditLog
from app.models.decision import Decision
from app.models.market_snapshot import MarketSnapshot
from app.models.model_config import ModelConfig
from app.models.order import Order
from app.models.portfolio_cash import PortfolioCash
from app.models.portfolio_nav import PortfolioNav
from app.models.position import Position
from app.models.strategy_run import StrategyRun
from app.models.strategy_settings import StrategySettings
from app.schemas.decision import DecisionPayload
from app.services.audit_service import audit_service
from app.services.llm_router import llm_router
from app.services.market_service import market_service
from app.services.paper_executor import paper_executor
from app.services.portfolio_service import portfolio_service
from app.services.prompt_builder import DEFAULT_PROMPT_TEMPLATE, prompt_builder


class DecisionScheduler:
    def __init__(self) -> None:
        settings = get_settings()
        self.default_interval_seconds = settings.decision_interval_seconds
        self._task: asyncio.Task | None = None
        self._running = False
        self._last_run_at = None
        self._last_run_status: str = "idle"
        self._cycle_lock = asyncio.Lock()

    async def start(self) -> None:
        self._running = True
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        while self._running:
            interval = self.default_interval_seconds
            try:
                with db_session() as db:
                    settings = self.ensure_strategy_settings(db)
                    interval = settings.decision_interval_seconds
                    enabled = settings.enabled
                if enabled:
                    await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                self._last_run_status = "error"
            await asyncio.sleep(interval)

    def ensure_strategy_settings(self, db) -> StrategySettings:
        settings = db.scalar(select(StrategySettings).where(StrategySettings.id == 1))
        if settings:
            return settings
        settings = StrategySettings(
            id=1,
            enabled=False,
            decision_interval_seconds=self.default_interval_seconds,
            prompt_template=DEFAULT_PROMPT_TEMPLATE,
        )
        db.add(settings)
        db.flush()
        return settings

    def get_state(self) -> dict:
        return {
            "running": self._running,
            "last_run_at": self._last_run_at,
            "last_run_status": self._last_run_status,
            "default_interval_seconds": self.default_interval_seconds,
        }

    async def run_once(self) -> dict:
        async with self._cycle_lock:
            started = perf_counter()
            self._last_run_status = "running"
            with db_session() as db:
                strategy_settings = self.ensure_strategy_settings(db)
                strategy_run = StrategyRun(status="running")
                db.add(strategy_run)
                db.flush()
                try:
                    price_lookup = {item["symbol"]: item["price"] for item in market_service.get_ticker_list() if item["price"]}
                    paper_executor.apply_take_profit_stop_loss(db, price_lookup)
                    market_context = await self._build_market_snapshot()
                    db.add(MarketSnapshot(strategy_run_id=strategy_run.id, snapshot_json=json.dumps(market_context, default=str)))
                    db.flush()
                    model_configs = list(
                        db.scalars(
                            select(ModelConfig).where(
                                ModelConfig.enabled.is_(True),
                                ModelConfig.include_in_strategy.is_(True),
                            )
                        ).all()
                    )
                    decisions = []
                    for config in model_configs:
                        decision = await self._run_for_model(db, config, strategy_run.id, strategy_settings.prompt_template, market_context)
                        decisions.append(decision)
                        market_price = price_lookup.get(decision.symbol) if decision.symbol else None
                        paper_executor.execute(db, decision, market_price)
                        portfolio_service.record_nav(db, config.id, price_lookup)
                    strategy_run.status = "completed"
                    strategy_run.finished_at = utc_now()
                    strategy_run.duration_ms = (perf_counter() - started) * 1000
                    self._last_run_at = strategy_run.finished_at
                    self._last_run_status = "completed"
                    await ws_hub.broadcast("dashboard", {"type": "strategy-run", "status": "completed"})
                    return {"run_id": strategy_run.id, "decisions": len(decisions)}
                except Exception as exc:
                    strategy_run.status = "failed"
                    strategy_run.finished_at = utc_now()
                    strategy_run.duration_ms = (perf_counter() - started) * 1000
                    strategy_run.error = str(exc)
                    self._last_run_at = strategy_run.finished_at
                    self._last_run_status = "failed"
                    audit_service.log(db, "strategy_run_failed", str(exc), level="error")
                    raise

    async def reset_trading_data(self) -> dict:
        async with self._cycle_lock:
            with db_session() as db:
                deleted = {
                    "orders": db.execute(delete(Order)).rowcount or 0,
                    "decisions": db.execute(delete(Decision)).rowcount or 0,
                    "positions": db.execute(delete(Position)).rowcount or 0,
                    "nav_points": db.execute(delete(PortfolioNav)).rowcount or 0,
                    "cash_accounts": db.execute(delete(PortfolioCash)).rowcount or 0,
                    "market_snapshots": db.execute(delete(MarketSnapshot)).rowcount or 0,
                    "strategy_runs": db.execute(delete(StrategyRun)).rowcount or 0,
                    "audit_logs": db.execute(delete(AuditLog)).rowcount or 0,
                }
                self._last_run_at = None
                self._last_run_status = "idle"
            await ws_hub.broadcast("dashboard", {"type": "trading-data-reset"})
            return {"status": "ok", "deleted": deleted}

    async def _build_market_snapshot(self) -> dict:
        result = {}
        for symbol in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
            result[symbol] = await market_service.get_symbol_context(symbol)
        return result

    async def _run_for_model(self, db, config: ModelConfig, strategy_run_id: int, strategy_prompt: str, market_context: dict) -> Decision:
        price_lookup = {item["symbol"]: item["price"] for item in market_service.get_ticker_list() if item["price"]}
        portfolio_snapshot = portfolio_service.get_overview(db, price_lookup)
        historical_decisions = list(
            db.scalars(
                select(Decision)
                .where(Decision.model_config_id == config.id)
                .order_by(Decision.created_at.desc())
                .limit(10)
            ).all()
        )
        context = {
            "now": app_now().isoformat(),
            "portfolio": portfolio_snapshot,
            "market": market_context,
            "recent_decisions": [
                {
                    "symbol": item.symbol,
                    "action": item.action,
                    "buy_pct": item.buy_pct,
                    "sell_pct": item.sell_pct,
                    "take_profit": item.take_profit,
                    "stop_loss": item.stop_loss,
                    "confidence": item.confidence,
                    "reason": item.reason,
                    "created_at": utc_to_app_timezone(item.created_at).isoformat(),
                }
                for item in historical_decisions
            ],
            "active_model": {
                "id": config.id,
                "name": config.name,
                "provider": config.provider,
                "model": config.model,
            },
        }
        messages = prompt_builder.build(strategy_prompt, context)
        raw_response = ""
        status = "accepted"
        validation_error = None
        payload = DecisionPayload(action="HOLD", reason="Fallback HOLD")
        try:
            raw_response = await llm_router.run_completion(config, messages)
            parsed = llm_router.parse_json_response(raw_response)
            payload = DecisionPayload.model_validate(parsed)
        except (ValidationError, ValueError, KeyError, json.JSONDecodeError) as exc:
            status = "fallback_hold"
            validation_error = str(exc)
            payload = DecisionPayload(action="HOLD", reason="Invalid response, fallback HOLD")
            audit_service.log(db, "decision_validation_failed", f"Model {config.name} produced invalid output", "warning", {"error": str(exc)})
        except Exception as exc:
            status = "fallback_hold"
            validation_error = str(exc)
            payload = DecisionPayload(action="HOLD", reason="Timeout or provider failure, fallback HOLD")
            audit_service.log(db, "decision_provider_failed", f"Model {config.name} request failed", "error", {"error": str(exc)})
        decision = Decision(
            model_config_id=config.id,
            strategy_run_id=strategy_run_id,
            symbol=payload.symbol,
            action=payload.action,
            buy_pct=payload.buy_pct,
            sell_pct=payload.sell_pct,
            take_profit=payload.take_profit,
            stop_loss=payload.stop_loss,
            confidence=payload.confidence,
            reason=payload.reason,
            status=status,
            raw_response=raw_response,
            validation_error=validation_error,
        )
        db.add(decision)
        db.flush()
        return decision


decision_scheduler = DecisionScheduler()
