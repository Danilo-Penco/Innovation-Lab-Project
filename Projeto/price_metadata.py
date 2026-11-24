"""Source logos and timestamps for transient price comparisons."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

STEAM_LOGO_URL = "https://store.steampowered.com/favicon.ico"
GOG_LOGO_URL = "https://www.gog.com/favicon.ico"
LOCAL_TIMEZONE = ZoneInfo("America/Sao_Paulo")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_unix_timestamp(value: object) -> datetime | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        timestamp = value
    elif isinstance(value, str) and value.isdigit():
        timestamp = int(value)
    else:
        return None
    if timestamp <= 0:
        return None
    try:
        return datetime.fromtimestamp(timestamp, timezone.utc)
    except (OSError, OverflowError, ValueError):
        return None


def format_price_timestamp(
    source_updated_at: datetime | None,
    fetched_at: datetime | None,
    source_name: str,
) -> str:
    timestamp = source_updated_at or fetched_at or utc_now()
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    local_timestamp = timestamp.astimezone(LOCAL_TIMEZONE).strftime(
        "%d/%m/%Y às %H:%M"
    )
    if source_updated_at is not None:
        return f"Atualização informada pela {source_name}: {local_timestamp}"
    return f"Consultado pelo ComparaKeys: {local_timestamp}"
