"""Server-side client for the public Steam Store endpoints."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

import httpx

STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
STEAM_APP_DETAILS_URL = "https://store.steampowered.com/api/appdetails"
STEAM_TIMEOUT_SECONDS = 8.0
MAX_SEARCH_LENGTH = 100

PriceStatus = Literal["paid", "free", "unavailable"]


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

    if data.get("type") != "game":
        return SteamPrice(app_id=app_id, name=name.strip(), status="unavailable")
    if data.get("is_free") is True:
        return SteamPrice(app_id=app_id, name=name.strip(), status="free")
    if data.get("is_free") is not False:
        return SteamPrice(app_id=app_id, name=name.strip(), status="unavailable")

    price_overview = data.get("price_overview")
    if not isinstance(price_overview, dict):
        return SteamPrice(app_id=app_id, name=name.strip(), status="unavailable")

    currency = price_overview.get("currency")
    final_price = price_overview.get("final")
    if (
        currency != "BRL"
        or not isinstance(final_price, int)
        or isinstance(final_price, bool)
        or final_price < 0
    ):
        return SteamPrice(app_id=app_id, name=name.strip(), status="unavailable")

    return SteamPrice(
        app_id=app_id,
        name=name.strip(),
        status="paid",
        final_price_minor=final_price,
    )


async def _get_json(
    url: str,
    params: dict[str, str | int],
    transport: httpx.AsyncBaseTransport | None = None,
) -> object:
    try:
        async with httpx.AsyncClient(
            timeout=STEAM_TIMEOUT_SECONDS,
            transport=transport,
        ) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as error:
        raise SteamServiceError(
            "A Steam demorou demais para responder. Tente novamente."
        ) from error
    except httpx.HTTPStatusError as error:
        raise SteamServiceError(
            "A Steam não está disponível no momento. Tente novamente."
        ) from error
    except httpx.RequestError as error:
        raise SteamServiceError(
            "Não foi possível conectar à Steam. Tente novamente."
        ) from error
    except (json.JSONDecodeError, ValueError) as error:
        raise SteamServiceError(
            "A Steam retornou uma resposta inválida. Tente novamente."
        ) from error


async def search_steam_games(
    term: str,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[SteamGame]:
    normalized = validate_search_term(term)
    payload = await _get_json(
        STEAM_SEARCH_URL,
        {"term": normalized, "cc": "BR", "l": "brazilian"},
        transport=transport,
    )
    return parse_search_results(payload)


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
    return parse_game_price(payload, app_id)
