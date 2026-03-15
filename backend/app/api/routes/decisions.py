from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.time import utc_to_app_timezone
from app.models.decision import Decision
from app.models.model_config import ModelConfig
from app.schemas.decision import DecisionRead
from app.services.decision_scheduler import decision_scheduler

router = APIRouter()


@router.get("", response_model=list[DecisionRead])
def list_decisions(limit: int = 50, db: Session = Depends(get_db)) -> list[dict]:
    decisions = list(db.scalars(select(Decision).order_by(Decision.created_at.desc()).limit(limit)).all())
    model_ids = sorted({item.model_config_id for item in decisions})
    model_name_by_id = {}
    if model_ids:
        models = list(db.scalars(select(ModelConfig).where(ModelConfig.id.in_(model_ids))).all())
        model_name_by_id = {item.id: item.name for item in models}
    return [
        {
            "id": item.id,
            "model_config_id": item.model_config_id,
            "model_name": model_name_by_id.get(item.model_config_id, f"Model #{item.model_config_id}"),
            "strategy_run_id": item.strategy_run_id,
            "symbol": item.symbol,
            "action": item.action,
            "buy_pct": item.buy_pct,
            "sell_pct": item.sell_pct,
            "take_profit": item.take_profit,
            "stop_loss": item.stop_loss,
            "confidence": item.confidence,
            "reason": item.reason,
            "status": item.status,
            "raw_response": item.raw_response,
            "validation_error": item.validation_error,
            "created_at": utc_to_app_timezone(item.created_at),
        }
        for item in decisions
    ]


@router.post("/run")
async def run_decisions_once() -> dict:
    return await decision_scheduler.run_once()
