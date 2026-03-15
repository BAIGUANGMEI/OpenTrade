from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StrategySettingsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    enabled: bool
    decision_interval_seconds: int
    prompt_template: str
    created_at: datetime
    updated_at: datetime


class StrategySettingsUpdate(BaseModel):
    enabled: bool | None = None
    decision_interval_seconds: int | None = Field(default=None, ge=30, le=86400)
    prompt_template: str | None = None


class StrategyRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    started_at: datetime
    finished_at: datetime | None
    duration_ms: float | None
    error: str | None
