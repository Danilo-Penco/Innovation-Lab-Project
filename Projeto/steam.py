"""Server-side client for the public Steam Store endpoints."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

import httpx

from Projeto.cache import MemoryTTLCache
from Projeto.external_api import PublicApiRequestError, get_json
from Projeto.price_metadata import STEAM_LOGO_URL, utc_now

STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
STEAM_APP_DETAILS_URL = "https://store.steampowered.com/api/appdetails"
STEAM_TIMEOUT_SECONDS = 10.0
MAX_SEARCH_LENGTH = 100
STEAM_SEARCH_CACHE_MAX_ENTRIES = 256

PriceStatus = Literal["paid", "free", "unavailable"]

_SEARCH_CACHE: MemoryTTLCache[
    tuple[str, str, str],
    tuple[SteamGame, ...],
] = MemoryTTLCache(max_entries=STEAM_SEARCH_CACHE_MAX_ENTRIES)


class SteamServiceError(Exception):
    """Raised when a Steam request fails or returns an invalid response."""


class InvalidSearchTerm(ValueError):
    """Raised when a search term is empty or too long."""


@dataclass(frozen=True)
class SteamGame:
    app_id: int
    name: str


@dataclass(frozen=True)
class SteamPrice:
    app_id: int
    name: str
    status: PriceStatus
    final_price_minor: int | None = None
    header_image: str = ""
    source_currency: Literal["BRL"] = "BRL"
    store_name: str = "Steam"
    store_logo_url: str = STEAM_LOGO_URL
    source_updated_at: datetime | None = None
    fetched_at: datetime | None = None

    @property
    def original_price_minor(self) -> int | None:
        return self.final_price_minor

    @property
    def price_brl_minor(self) -> int | None:
        if self.status in ("paid", "free"):
            return self.final_price_minor or 0
        return None


def validate_search_term(term: str) -> str:
    normalized = term.strip()
    if not normalized:
        raise InvalidSearchTerm("Digite o nome de um jogo.")
    if len(normalized) > MAX_SEARCH_LENGTH:
        raise InvalidSearchTerm(
            f"A busca deve ter no máximo {MAX_SEARCH_LENGTH} caracteres."
        )
    return normalized


def format_brl(final_price_minor: int) -> str:
    if (
        not isinstance(final_price_minor, int)
        or isinstance(final_price_minor, bool)
        or final_price_minor < 0
    ):
        raise ValueError("O preço em centavos deve ser um inteiro não negativo.")

    whole_reais, cents = divmod(final_price_minor, 100)
    formatted_reais = f"{whole_reais:,}".replace(",", ".")
    return f"R$ {formatted_reais},{cents:02d}"


def parse_search_results(payload: object) -> list[SteamGame]:
    if not isinstance(payload, dict):
        raise SteamServiceError("A Steam retornou uma resposta de busca inválida.")

    items = payload.get("items")
    if not isinstance(items, list):
        raise SteamServiceError("A Steam retornou uma resposta de busca inválida.")

    games: list[SteamGame] = []
    for item in items:
        if not isinstance(item, dict):
            raise SteamServiceError("A Steam retornou um resultado inválido.")
        if item.get("type") != "app":
            continue

        app_id = item.get("id")
        name = item.get("name")
        if (
            not isinstance(app_id, int)
            or isinstance(app_id, bool)
            or app_id <= 0
            or not isinstance(name, str)
            or not name.strip()
        ):
            raise SteamServiceError("A Steam retornou um resultado inválido.")

        games.append(SteamGame(app_id=app_id, name=name.strip()))

    return games


def find_game_by_app_id(games: list[SteamGame], app_id: int) -> SteamGame | None:
    return next((game for game in games if game.app_id == app_id), None)


def parse_game_price(payload: object, app_id: int) -> SteamPrice:
    unavailable = SteamPrice(
        app_id=app_id,
        name="",
        status="unavailable",
    )
    if not isinstance(payload, dict):
        raise SteamServiceError("A Steam retornou uma resposta de preço inválida.")

    app_result = payload.get(str(app_id))
    if not isinstance(app_result, dict):
        raise SteamServiceError("A Steam retornou uma resposta de preço inválida.")
    if app_result.get("success") is not True:
        return unavailable

    data = app_result.get("data")
    if not isinstance(data, dict):
        raise SteamServiceError("A Steam retornou uma resposta de preço inválida.")

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise SteamServiceError("A Steam retornou uma resposta de preço inválida.")
    header_image = data.get("header_image", "")
    if not isinstance(header_image, str):
        raise SteamServiceError("A Steam retornou uma resposta de preço inválida.")
    if header_image:
        try:
            parsed_image_url = urlparse(header_image)
            valid_image_url = (
                parsed_image_url.scheme == "https"
                and parsed_image_url.hostname is not None
                and (
                    parsed_image_url.hostname == "steamstatic.com"
                    or parsed_image_url.hostname.endswith(".steamstatic.com")
                )
                and parsed_image_url.username is None
                and parsed_image_url.password is None
                and parsed_image_url.port is None
            )
        except ValueError as error:
            raise SteamServiceError("A Steam retornou uma imagem inválida.") from error
        if not valid_image_url:
            raise SteamServiceError("A Steam retornou uma imagem inválida.")

    if data.get("type") != "game":
        return SteamPrice(
            app_id=app_id,
            name=name.strip(),
            status="unavailable",
            header_image=header_image,
        )
    if data.get("is_free") is True:
        return SteamPrice(
            app_id=app_id,
            name=name.strip(),
            status="free",
            header_image=header_image,
        )
    if data.get("is_free") is not False:
        return SteamPrice(
            app_id=app_id,
            name=name.strip(),
            status="unavailable",
            header_image=header_image,
        )

    price_overview = data.get("price_overview")
    if not isinstance(price_overview, dict):
        return SteamPrice(
            app_id=app_id,
            name=name.strip(),
            status="unavailable",
            header_image=header_image,
        )

    currency = price_overview.get("currency")
    final_price = price_overview.get("final")
    if (
        currency != "BRL"
        or not isinstance(final_price, int)
        or isinstance(final_price, bool)
        or final_price < 0
    ):
        return SteamPrice(
            app_id=app_id,
            name=name.strip(),
            status="unavailable",
            header_image=header_image,
        )

    return SteamPrice(
        app_id=app_id,
        name=name.strip(),
        status="paid",
        final_price_minor=final_price,
        header_image=header_image,
    )


async def _get_json(
    url: str,
    params: dict[str, str | int],
    transport: httpx.AsyncBaseTransport | None = None,
) -> object:
    try:
        return await get_json(
            url,
            params,
            timeout_seconds=STEAM_TIMEOUT_SECONDS,
            transport=transport,
        )
    except PublicApiRequestError as error:
        messages = {
            "rate_limited": (
                "A Steam atingiu o limite temporário. Tente novamente mais tarde."
            ),
            "timeout": "A Steam demorou demais para responder. Tente novamente.",
            "network": "Não foi possível conectar à Steam. Tente novamente.",
            "http": "A Steam não está disponível no momento. Tente novamente.",
            "invalid_json": (
                "A Steam retornou uma resposta inválida. Tente novamente."
            ),
        }
        raise SteamServiceError(messages[error.kind]) from error


async def search_steam_games(
    term: str,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[SteamGame]:
    normalized = validate_search_term(term)
    cache_key = (normalized.casefold(), "BR", "brazilian")
    if transport is None:
        cached_games = _SEARCH_CACHE.get(cache_key)
        if cached_games is not None:
            return list(cached_games)

    payload = await _get_json(
        STEAM_SEARCH_URL,
        {"term": normalized, "cc": "BR", "l": "brazilian"},
        transport=transport,
    )
    games = parse_search_results(payload)
    if transport is None:
        _SEARCH_CACHE.set(cache_key, tuple(games))
    return games


async def get_steam_game_price(
    app_id: int,
    transport: httpx.AsyncBaseTransport | None = None,
) -> SteamPrice:
    if not isinstance(app_id, int) or isinstance(app_id, bool) or app_id <= 0:
        raise ValueError("O App ID da Steam deve ser um inteiro positivo.")

    payload = await _get_json(
        STEAM_APP_DETAILS_URL,
        {"appids": app_id, "cc": "br", "l": "brazilian"},
        transport=transport,
    )
    return replace(
        parse_game_price(payload, app_id),
        fetched_at=utc_now(),
    )
