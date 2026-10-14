"""Server-side client for the public GOG catalog."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal
from urllib.parse import urlparse

import httpx

GOG_CATALOG_URL = "https://catalog.gog.com/v1/catalog"
GOG_TIMEOUT_SECONDS = 8.0
GOG_COVER_HOST = "images.gog-statics.com"
GOG_STORE_HOST = "www.gog.com"

GogPriceStatus = Literal["paid", "free", "unavailable"]


class GogServiceError(Exception):
    """Raised when a GOG request fails or returns an invalid response."""


@dataclass(frozen=True)
class GogOffer:
    product_id: str
    title: str
    store_url: str
    cover_url: str
    status: GogPriceStatus
    final_price_minor: int | None = None


def normalize_title(title: str) -> str:
    return " ".join(title.split()).casefold()


def _validated_https_url(value: object, allowed_host: str) -> str:
    if not isinstance(value, str):
        raise GogServiceError("A GOG retornou um link inválido.")

    try:
        parsed = urlparse(value)
        valid = (
            parsed.scheme == "https"
            and parsed.hostname == allowed_host
            and parsed.username is None
            and parsed.password is None
            and parsed.port is None
            and parsed.path.startswith("/")
        )
    except ValueError as error:
        raise GogServiceError("A GOG retornou um link inválido.") from error
    if not valid:
        raise GogServiceError("A GOG retornou um link inválido.")
    return value


def _parse_price(product: dict[str, object]) -> tuple[GogPriceStatus, int | None]:
    price = product.get("price")
    if not isinstance(price, dict):
        return "unavailable", None

    final_money = price.get("finalMoney")
    if not isinstance(final_money, dict) or final_money.get("currency") != "BRL":
        return "unavailable", None

    amount = final_money.get("amount")
    if not isinstance(amount, str):
        return "unavailable", None
    try:
        decimal_amount = Decimal(amount)
    except InvalidOperation:
        return "unavailable", None
    if not decimal_amount.is_finite() or decimal_amount < 0:
        return "unavailable", None

    cents = decimal_amount * 100
    if cents != cents.to_integral_value():
        return "unavailable", None
    final_price_minor = int(cents)
    return ("free", 0) if final_price_minor == 0 else ("paid", final_price_minor)


def parse_catalog_results(payload: object, requested_title: str) -> GogOffer | None:
    if not isinstance(payload, dict):
        raise GogServiceError("A GOG retornou uma resposta de busca inválida.")

    products = payload.get("products")
    if not isinstance(products, list):
        raise GogServiceError("A GOG retornou uma resposta de busca inválida.")

    normalized_title = normalize_title(requested_title)
    exact_matches: list[dict[str, object]] = []
    for product in products:
        if not isinstance(product, dict):
            raise GogServiceError("A GOG retornou um resultado inválido.")
        title = product.get("title")
        if not isinstance(title, str):
            raise GogServiceError("A GOG retornou um resultado inválido.")
        if (
            product.get("productType") == "game"
            and normalize_title(title) == normalized_title
        ):
            exact_matches.append(product)

    if len(exact_matches) != 1:
        return None

    product = exact_matches[0]
    product_id = product.get("id")
    title = product.get("title")
    if not isinstance(product_id, (str, int)) or isinstance(product_id, bool):
        raise GogServiceError("A GOG retornou um resultado inválido.")
    if not isinstance(title, str) or not title.strip():
        raise GogServiceError("A GOG retornou um resultado inválido.")

    store_url = _validated_https_url(product.get("storeLink"), GOG_STORE_HOST)
    cover_url = _validated_https_url(product.get("coverHorizontal"), GOG_COVER_HOST)
    status, final_price_minor = _parse_price(product)
    return GogOffer(
        product_id=str(product_id),
        title=title.strip(),
        store_url=store_url,
        cover_url=cover_url,
        status=status,
        final_price_minor=final_price_minor,
    )


async def _get_json(
    params: dict[str, str | int],
    transport: httpx.AsyncBaseTransport | None = None,
) -> object:
    try:
        async with httpx.AsyncClient(
            timeout=GOG_TIMEOUT_SECONDS,
            transport=transport,
        ) as client:
            response = await client.get(GOG_CATALOG_URL, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as error:
        raise GogServiceError(
            "A GOG demorou demais para responder. Tente novamente."
        ) from error
    except httpx.HTTPStatusError as error:
        raise GogServiceError(
            "A GOG não está disponível no momento. Tente novamente."
        ) from error
    except httpx.RequestError as error:
        raise GogServiceError(
            "Não foi possível conectar à GOG. Tente novamente."
        ) from error
    except (json.JSONDecodeError, ValueError) as error:
        raise GogServiceError(
            "A GOG retornou uma resposta inválida. Tente novamente."
        ) from error


async def search_gog_offer(
    title: str,
    transport: httpx.AsyncBaseTransport | None = None,
) -> GogOffer | None:
    normalized_title = " ".join(title.split())
    if not normalized_title:
        raise ValueError("O título do jogo não pode ser vazio.")

    payload = await _get_json(
        {
            "limit": 50,
            "order": "desc:trending",
            "productType": "in:game",
            "query": normalized_title,
            "locale": "en-US",
            "currencyCode": "BRL",
            "countryCode": "BR",
        },
        transport=transport,
    )
    return parse_catalog_results(payload, normalized_title)
