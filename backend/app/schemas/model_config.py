from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ModelConfigBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    provider: str | None = Field(default=None, max_length=50)
    model: str = Field(min_length=1, max_length=200)
    base_url: HttpUrl
    enabled: bool = True
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=800, ge=1, le=16000)
    timeout_seconds: int = Field(default=20, ge=5, le=120)
    include_in_strategy: bool = True


class ModelConfigCreate(ModelConfigBase):
    api_key: str = Field(min_length=1)


class ModelConfigUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    provider: str | None = Field(default=None, max_length=50)
    model: str | None = Field(default=None, min_length=1, max_length=200)
    base_url: HttpUrl | None = None
    api_key: str | None = None
    enabled: bool | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=16000)
    timeout_seconds: int | None = Field(default=None, ge=5, le=120)
    include_in_strategy: bool | None = None


class ModelConfigRead(ModelConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    api_key_masked: str
    has_api_key: bool
    created_at: datetime
    updated_at: datetime
