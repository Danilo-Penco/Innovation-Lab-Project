"""Server-side client for the public GOG catalog."""

from __future__ import annotations

import json
import re
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
GogMatchStatus = Literal["matched", "not_found", "ambiguous"]


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


@dataclass(frozen=True)
class GogMatchResult:
    status: GogMatchStatus
    offer: GogOffer | None = None


def normalize_title(title: str) -> str:
    return " ".join(title.split()).casefold()


def _normalize_query(title: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", title, flags=re.UNICODE).split())


_EDITION_SUFFIX = re.compile(
    r"(?:\s*[-:–—]\s*|\s+)"
    r"(?:deluxe|definitive|digital|game of the year|goty|complete|"
    r"enhanced|ultimate|collector['’]?s|special|anniversary)"
    r"(?:\s+(?:edition|version|pack))?$",
    re.IGNORECASE,
)


def _normalized_match_title(title: str) -> str:
    return normalize_title(title)


def _strip_edition_suffix(title: str) -> str:
    normalized = title.strip()
    while True:
        stripped = _EDITION_SUFFIX.sub("", normalized).strip()
        if stripped == normalized:
            return normalized
        normalized = stripped


def _is_approximate_match(requested_title: str, product_title: str) -> bool:
    requested = _normalize_query(_strip_edition_suffix(requested_title))
    candidate = _normalize_query(_strip_edition_suffix(product_title))
    if not requested or not candidate:
        return False
    return (
        candidate.startswith(requested)
        or requested.startswith(candidate)
        or requested in candidate
        or candidate in requested
    )


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


def _make_offer(product: dict[str, object]) -> GogOffer:
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


def parse_catalog_results(payload: object, requested_title: str) -> GogMatchResult:
    if not isinstance(payload, dict):
        raise GogServiceError("A GOG retornou uma resposta de busca inválida.")

    products = payload.get("products")
    if not isinstance(products, list):
        raise GogServiceError("A GOG retornou uma resposta de busca inválida.")

    normalized_title = _normalized_match_title(requested_title)
    exact_matches: list[dict[str, object]] = []
    for product in products:
        if not isinstance(product, dict):
            raise GogServiceError("A GOG retornou um resultado inválido.")
        title = product.get("title")
        if not isinstance(title, str):
            raise GogServiceError("A GOG retornou um resultado inválido.")
        if (
            product.get("productType") == "game"
            and _normalized_match_title(title) == normalized_title
        ):
            exact_matches.append(product)

    if len(exact_matches) == 1:
        return GogMatchResult(status="matched", offer=_make_offer(exact_matches[0]))
    if len(exact_matches) > 1:
        return GogMatchResult(status="ambiguous")

    approximate_matches: dict[str, dict[str, object]] = {}
    for product in products:
        if (
            product.get("productType") != "game"
            or not isinstance(product.get("title"), str)
            or not _is_approximate_match(requested_title, product["title"])
        ):
            continue
        product_id = product.get("id")
        if not isinstance(product_id, (str, int)) or isinstance(product_id, bool):
            raise GogServiceError("A GOG retornou um resultado inválido.")
        approximate_matches[str(product_id)] = product

    if len(approximate_matches) == 1:
        product = next(iter(approximate_matches.values()))
        return GogMatchResult(status="matched", offer=_make_offer(product))
    if len(approximate_matches) > 1:
        return GogMatchResult(status="ambiguous")
    return GogMatchResult(status="not_found")


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
) -> GogMatchResult:
    normalized_title = " ".join(title.split())
    if not normalized_title:
        raise ValueError("O título do jogo não pode ser vazio.")

    params = {
        "limit": 50,
        "order": "desc:trending",
        "productType": "in:game",
        "query": normalized_title,
        "locale": "en-US",
        "currencyCode": "BRL",
        "countryCode": "BR",
    }
    payload = await _get_json(params, transport=transport)
    result = parse_catalog_results(payload, normalized_title)
    if result.status == "matched":
        return result

    normalized_query = _normalize_query(normalized_title)
    if normalized_query == normalized_title:
        return result

    params["query"] = normalized_query
    normalized_payload = await _get_json(params, transport=transport)
    products = payload.get("products") if isinstance(payload, dict) else None
    normalized_products = (
        normalized_payload.get("products")
        if isinstance(normalized_payload, dict)
        else None
    )
    if not isinstance(products, list) or not isinstance(normalized_products, list):
        raise GogServiceError("A GOG retornou uma resposta de busca inválida.")

    combined_products: dict[str, dict[str, object]] = {}
    for product in [*products, *normalized_products]:
        if not isinstance(product, dict):
            raise GogServiceError("A GOG retornou um resultado inválido.")
        product_id = product.get("id")
        if not isinstance(product_id, (str, int)) or isinstance(product_id, bool):
            raise GogServiceError("A GOG retornou um resultado inválido.")
        combined_products[str(product_id)] = product
    return parse_catalog_results(
        {"products": list(combined_products.values())},
        normalized_title,
    )
