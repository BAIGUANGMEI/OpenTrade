from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DecisionPayload(BaseModel):
    symbol: Literal["BTCUSDT", "ETHUSDT", "SOLUSDT"] | None = None
    action: Literal["BUY", "SELL", "HOLD"]
    buy_pct: float = Field(default=0.0, ge=0.0, le=1.0)
    sell_pct: float = Field(default=0.0, ge=0.0, le=1.0)
    take_profit: float | None = Field(default=None, gt=0)
    stop_loss: float | None = Field(default=None, gt=0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str = Field(default="", max_length=300)

    @field_validator("take_profit", "stop_loss", mode="before")
    @classmethod
    def normalize_optional_price_levels(cls, value):
        if value in (None, "", 0, 0.0, "0", "0.0"):
            return None
        return value


class DecisionRead(DecisionPayload):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model_config_id: int
    model_name: str | None = None
    strategy_run_id: int | None
    status: str
    raw_response: str
    validation_error: str | None
    created_at: datetime
