from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import get_settings

DEFAULT_TIMEZONE = "Asia/Shanghai"


def get_app_timezone() -> ZoneInfo:
    timezone_name = get_settings().app_timezone or DEFAULT_TIMEZONE
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo(DEFAULT_TIMEZONE)


def app_now() -> datetime:
    return datetime.now(get_app_timezone())


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_to_app_timezone(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(get_app_timezone())


def timestamp_to_app_timezone(seconds: float) -> datetime:
    return datetime.fromtimestamp(seconds, tz=get_app_timezone())
