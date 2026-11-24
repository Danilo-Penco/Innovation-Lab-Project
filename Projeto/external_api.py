"""Shared request handling for public JSON APIs."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from threading import Lock
from time import monotonic
from typing import Literal
from urllib.parse import urlparse

import httpx

ApiFailureKind = Literal[
    "rate_limited",
    "timeout",
    "network",
    "http",
    "invalid_json",
]

_RATE_LIMIT_LOCK = Lock()
_RATE_LIMIT_UNTIL: dict[str, float] = {}


class PublicApiRequestError(Exception):
    def __init__(
        self,
        kind: ApiFailureKind,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(kind)
        self.kind = kind
        self.retry_after_seconds = retry_after_seconds


def _retry_after_seconds(value: str | None) -> float | None:
    if not value:
        return None

    try:
        seconds = float(value)
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        seconds = (retry_at - datetime.now(timezone.utc)).total_seconds()

    if not math.isfinite(seconds):
        return None
    return max(0.0, seconds)


def _host_key(url: str) -> str:
    host = urlparse(url).hostname
    if host is None:
        raise ValueError("A URL da integração pública não é válida.")
    return host.casefold()


def _raise_if_rate_limited(host: str) -> None:
    with _RATE_LIMIT_LOCK:
        until = _RATE_LIMIT_UNTIL.get(host)
        if until is None:
            return
        remaining = until - monotonic()
        if remaining <= 0:
            del _RATE_LIMIT_UNTIL[host]
            return
    raise PublicApiRequestError("rate_limited", remaining)


def _record_rate_limit(host: str, retry_after: str | None) -> float | None:
    seconds = _retry_after_seconds(retry_after)
    if seconds is None:
        return None

    with _RATE_LIMIT_LOCK:
        _RATE_LIMIT_UNTIL[host] = max(
            _RATE_LIMIT_UNTIL.get(host, 0.0),
            monotonic() + seconds,
        )
    return seconds


async def get_json(
    url: str,
    params: dict[str, str | int] | None,
    *,
    timeout_seconds: float,
    headers: dict[str, str] | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> object:
    host = _host_key(url)
    _raise_if_rate_limited(host)

    for attempt in range(2):
        try:
            async with httpx.AsyncClient(
                timeout=timeout_seconds,
                headers=headers,
                transport=transport,
            ) as client:
                response = await client.get(url, params=params)
        except httpx.RequestError as error:
            if attempt == 0:
                continue
            kind = (
                "timeout"
                if isinstance(error, httpx.TimeoutException)
                else "network"
            )
            raise PublicApiRequestError(kind) from error

        if response.status_code == 429:
            retry_after = _record_rate_limit(
                host,
                response.headers.get("Retry-After"),
            )
            raise PublicApiRequestError("rate_limited", retry_after)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise PublicApiRequestError("http") from error

        try:
            return response.json()
        except (ValueError, httpx.DecodingError) as error:
            raise PublicApiRequestError("invalid_json") from error

    raise AssertionError("A requisição pública terminou sem resultado.")
