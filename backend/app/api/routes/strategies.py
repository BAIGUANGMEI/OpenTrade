from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.time import utc_to_app_timezone
from app.models.strategy_run import StrategyRun
from app.schemas.strategy import StrategyRunRead, StrategySettingsRead, StrategySettingsUpdate
from app.services.decision_scheduler import decision_scheduler

router = APIRouter()


@router.get("/settings", response_model=StrategySettingsRead)
def get_strategy_settings(db: Session = Depends(get_db)):
    settings = decision_scheduler.ensure_strategy_settings(db)
    db.commit()
    db.refresh(settings)
    return {
        "id": settings.id,
        "enabled": settings.enabled,
        "decision_interval_seconds": settings.decision_interval_seconds,
        "prompt_template": settings.prompt_template,
        "created_at": utc_to_app_timezone(settings.created_at),
        "updated_at": utc_to_app_timezone(settings.updated_at),
    }


@router.put("/settings", response_model=StrategySettingsRead)
def update_strategy_settings(payload: StrategySettingsUpdate, db: Session = Depends(get_db)):
    settings = decision_scheduler.ensure_strategy_settings(db)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(settings, key, value)
    db.commit()
    db.refresh(settings)
    return {
        "id": settings.id,
        "enabled": settings.enabled,
        "decision_interval_seconds": settings.decision_interval_seconds,
        "prompt_template": settings.prompt_template,
        "created_at": utc_to_app_timezone(settings.created_at),
        "updated_at": utc_to_app_timezone(settings.updated_at),
    }


@router.get("/runs", response_model=list[StrategyRunRead])
def list_strategy_runs(limit: int = 30, db: Session = Depends(get_db)) -> list[dict]:
    runs = list(db.scalars(select(StrategyRun).order_by(StrategyRun.started_at.desc()).limit(limit)).all())
    return [
        {
            "id": item.id,
            "status": item.status,
            "started_at": utc_to_app_timezone(item.started_at),
            "finished_at": utc_to_app_timezone(item.finished_at),
            "duration_ms": item.duration_ms,
            "error": item.error,
        }
        for item in runs
    ]


@router.get("/state")
def get_scheduler_state() -> dict:
    state = decision_scheduler.get_state()
    return {
        **state,
        "last_run_at": utc_to_app_timezone(state.get("last_run_at")),
    }


@router.post("/reset")
async def reset_trading_data() -> dict:
    return await decision_scheduler.reset_trading_data()
