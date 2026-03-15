from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import cipher
from app.core.time import utc_to_app_timezone
from app.models.model_config import ModelConfig
from app.schemas.model_config import ModelConfigCreate, ModelConfigRead, ModelConfigUpdate
from app.services.portfolio_service import portfolio_service

router = APIRouter()


def to_read_model(item: ModelConfig) -> ModelConfigRead:
    api_key = cipher.decrypt(item.api_key_encrypted)
    return ModelConfigRead(
        id=item.id,
        name=item.name,
        provider=item.provider,
        model=item.model,
        base_url=item.base_url,
        enabled=item.enabled,
        temperature=item.temperature,
        max_tokens=item.max_tokens,
        timeout_seconds=item.timeout_seconds,
        include_in_strategy=item.include_in_strategy,
        api_key_masked=cipher.mask(api_key),
        has_api_key=bool(api_key),
        created_at=utc_to_app_timezone(item.created_at),
        updated_at=utc_to_app_timezone(item.updated_at),
    )


@router.get("", response_model=list[ModelConfigRead])
def list_models(db: Session = Depends(get_db)) -> list[ModelConfigRead]:
    items = list(db.scalars(select(ModelConfig).order_by(ModelConfig.name)).all())
    for item in items:
        portfolio_service.ensure_cash_account(db, item.id)
    db.commit()
    return [to_read_model(item) for item in items]


@router.post("", response_model=ModelConfigRead, status_code=status.HTTP_201_CREATED)
def create_model(payload: ModelConfigCreate, db: Session = Depends(get_db)) -> ModelConfigRead:
    existing = db.scalar(select(ModelConfig).where(ModelConfig.name == payload.name))
    if existing:
        raise HTTPException(status_code=409, detail="Model name already exists")
    item = ModelConfig(
        name=payload.name,
        provider=payload.provider,
        model=payload.model,
        base_url=str(payload.base_url),
        api_key_encrypted=cipher.encrypt(payload.api_key),
        enabled=payload.enabled,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        timeout_seconds=payload.timeout_seconds,
        include_in_strategy=payload.include_in_strategy,
    )
    db.add(item)
    db.flush()
    portfolio_service.ensure_cash_account(db, item.id)
    db.commit()
    db.refresh(item)
    return to_read_model(item)


@router.put("/{model_id}", response_model=ModelConfigRead)
def update_model(model_id: int, payload: ModelConfigUpdate, db: Session = Depends(get_db)) -> ModelConfigRead:
    item = db.get(ModelConfig, model_id)
    if not item:
        raise HTTPException(status_code=404, detail="Model not found")
    data = payload.model_dump(exclude_unset=True)
    if "base_url" in data and data["base_url"] is not None:
        data["base_url"] = str(data["base_url"])
    if "api_key" in data and data["api_key"]:
        item.api_key_encrypted = cipher.encrypt(data.pop("api_key"))
    for key, value in data.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return to_read_model(item)


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(model_id: int, db: Session = Depends(get_db)) -> None:
    item = db.get(ModelConfig, model_id)
    if not item:
        raise HTTPException(status_code=404, detail="Model not found")
    db.delete(item)
    db.commit()
