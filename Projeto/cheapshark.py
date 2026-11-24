"""Server-side clients for CheapShark offers and Frankfurter reference rates."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Literal
from urllib.parse import quote, unquote, urlsplit

import httpx

from Projeto.cache import MemoryTTLCache
from Projeto.external_api import PublicApiRequestError, get_json
from Projeto.price_metadata import (
    format_price_timestamp,
    parse_unix_timestamp,
    utc_now,
)
from Projeto.steam import format_brl

CHEAPSHARK_API_BASE = "https://www.cheapshark.com/api/1.0"
CHEAPSHARK_DEALS_URL = f"{CHEAPSHARK_API_BASE}/deals"
CHEAPSHARK_STORES_URL = f"{CHEAPSHARK_API_BASE}/stores"
FRANKFURTER_RATE_URL = "https://api.frankfurter.dev/v2/rate/usd/brl"
CHEAPSHARK_TIMEOUT_SECONDS = 10.0
CHEAPSHARK_PAGE_SIZE = 60
CHEAPSHARK_MAX_OFFERS = 5
CHEAPSHARK_USER_AGENT = (
    "ComparaKeys/1.0 "
    "(public game-price comparison; "
    "https://github.com/Danilo-Penco/Innovation-Lab-Project)"
)
CHEAPSHARK_CONVERSION_NOTICE = (
    "Preços internacionais em dólar, convertidos pela cotação do dia. "
    "Steam e GOG mostram o preço regional em reais, então a comparação é "
    "aproximada."
)
CHEAPSHARK_USD_FALLBACK_NOTICE = (
    "Cotação indisponível; ofertas da CheapShark exibidas em US$."
)
CHEAPSHARK_NO_OFFERS_MESSAGE = (
    "Não há ofertas adicionais disponíveis na CheapShark."
)
CHEAPSHARK_RATE_LIMIT_MESSAGE = (
    "A CheapShark atingiu o limite temporário. Tente novamente mais tarde."
)

_RATE_TTL_SECONDS = 3600.0


class CheapSharkServiceError(Exception):
    """Raised when CheapShark is unavailable or returns invalid data."""


class ExchangeRateError(Exception):
    """Raised when Frankfurter cannot provide a valid USD/BRL rate."""


@dataclass(frozen=True)
class CheapSharkOffer:
    store_name: str
    price_label: str
    deal_url: str
    price_brl_minor: int | None
    is_approximate: bool
    is_cheapest: bool = False
    store_logo_url: str = ""
    source_currency: Literal["BRL", "USD"] = "USD"
    original_amount: str = ""
    rate_label: str = ""
    timestamp_label: str = ""
    source_updated_at: datetime | None = None
    fetched_at: datetime | None = None


@dataclass(frozen=True)
class ExchangeRate:
    value: Decimal
    quote_date: date


@dataclass(frozen=True)
class _Deal:
    deal_id: str
    store_id: str
    price: Decimal
    currency: Literal["BRL", "USD"]
    source_updated_at: datetime | None


@dataclass(frozen=True)
class _Store:
    store_id: str
    name: str
    is_active: bool
    logo_url: str = ""


@dataclass(frozen=True)
class _PreparedOffer:
    sort_group: int
    sort_price: Decimal
    store_id: str
    offer: CheapSharkOffer


_STORE_CACHE: MemoryTTLCache[str, tuple[_Store, ...]] = MemoryTTLCache(
    max_entries=1
)
_RATE_CACHE: MemoryTTLCache[str, ExchangeRate] = MemoryTTLCache(
    max_entries=1,
    ttl_seconds=_RATE_TTL_SECONDS,
    max_ttl_seconds=_RATE_TTL_SECONDS,
)
_CHEAPSHARK_RESULT_CACHE: MemoryTTLCache[
    int,
    tuple[CheapSharkOffer, ...],
] = MemoryTTLCache(max_entries=256)


async def _request_json(
    url: str,
    params: dict[str, str | int] | None,
    *,
    service: Literal["cheapshark", "frankfurter"],
    transport: httpx.AsyncBaseTransport | None,
) -> object:
    try:
        return await get_json(
            url,
            params,
            timeout_seconds=CHEAPSHARK_TIMEOUT_SECONDS,
            headers={"User-Agent": CHEAPSHARK_USER_AGENT},
            transport=transport,
        )
    except PublicApiRequestError as error:
        if service == "cheapshark":
            messages = {
                "rate_limited": CHEAPSHARK_RATE_LIMIT_MESSAGE,
                "timeout": "A CheapShark demorou demais para responder.",
                "network": "Não foi possível conectar à CheapShark.",
                "http": "A CheapShark não está disponível no momento.",
                "invalid_json": "A CheapShark retornou uma resposta inválida.",
            }
            raise CheapSharkServiceError(messages[error.kind]) from error

        messages = {
            "rate_limited": (
                "A API de câmbio atingiu o limite temporário. "
                "Tente novamente mais tarde."
            ),
            "timeout": "A API de câmbio demorou demais para responder.",
            "network": "Não foi possível conectar à API de câmbio.",
            "http": "A API de câmbio não está disponível no momento.",
            "invalid_json": "A API de câmbio retornou uma resposta inválida.",
        }
        raise ExchangeRateError(messages[error.kind]) from error


def _positive_id(value: object) -> str:
    if isinstance(value, bool):
        raise CheapSharkServiceError("A CheapShark retornou dados inválidos.")
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and value.isdigit():
        parsed = int(value)
    else:
        raise CheapSharkServiceError("A CheapShark retornou dados inválidos.")

    if parsed <= 0:
        raise CheapSharkServiceError("A CheapShark retornou dados inválidos.")
    return str(parsed)


def _nonnegative_decimal(value: object, service: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(
        value,
        (str, int, float, Decimal),
    ):
        raise ValueError(f"{service} retornou um valor monetário inválido.")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError(
            f"{service} retornou um valor monetário inválido."
        ) from error
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"{service} retornou um valor monetário inválido.")
    return amount


def _parse_deal_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 512
        or not re.fullmatch(r"[A-Za-z0-9._~%+/=\-]+", value)
        or re.search(r"%(?![0-9A-Fa-f]{2})", value)
    ):
        raise CheapSharkServiceError("A CheapShark retornou um link inválido.")

    decoded = unquote(value)
    if not decoded or any(ord(character) < 32 for character in decoded):
        raise CheapSharkServiceError("A CheapShark retornou um link inválido.")
    return decoded


def _parse_deals(payload: object, app_id: int) -> tuple[_Deal, ...]:
    if not isinstance(payload, list):
        raise CheapSharkServiceError(
            "A CheapShark retornou uma lista de ofertas inválida."
        )

    deals: list[_Deal] = []
    for item in payload:
        if not isinstance(item, dict):
            raise CheapSharkServiceError(
                "A CheapShark retornou uma oferta inválida."
            )
        item_app_id = _positive_id(item.get("steamAppID"))
        if int(item_app_id) != app_id:
            continue

        store_id = _positive_id(item.get("storeID"))
        deal_id = _parse_deal_id(item.get("dealID"))
        try:
            price = _nonnegative_decimal(item.get("salePrice"), "CheapShark")
        except ValueError as error:
            raise CheapSharkServiceError(str(error)) from error

        raw_currency = item.get("currency") or item.get("currencyCode")
        if raw_currency in (None, ""):
            currency = "USD"
        elif isinstance(raw_currency, str) and raw_currency.upper() in (
            "BRL",
            "USD",
        ):
            currency = raw_currency.upper()
        else:
            raise CheapSharkServiceError(
                "A CheapShark retornou uma moeda não suportada."
            )

        deals.append(
            _Deal(
                deal_id=deal_id,
                store_id=store_id,
                price=price,
                currency=currency,
                source_updated_at=parse_unix_timestamp(item.get("lastChange")),
            )
        )
    return tuple(deals)


def _store_logo_url(value: object) -> str:
    if not isinstance(value, str):
        return ""
    try:
        parsed = urlsplit(value)
    except ValueError:
        return ""
    if (
        parsed.scheme
        or parsed.netloc
        or parsed.query
        or parsed.fragment
        or not re.fullmatch(r"/img/stores/logos/[A-Za-z0-9._-]{1,80}", parsed.path)
    ):
        return ""
    return f"https://www.cheapshark.com{parsed.path}"


def _parse_stores(payload: object) -> tuple[_Store, ...]:
    if not isinstance(payload, list):
        raise CheapSharkServiceError(
            "A CheapShark retornou uma lista de lojas inválida."
        )

    stores: list[_Store] = []
    for item in payload:
        if not isinstance(item, dict):
            raise CheapSharkServiceError(
                "A CheapShark retornou uma loja inválida."
            )
        store_id = _positive_id(item.get("storeID"))
        name = item.get("storeName")
        active = item.get("isActive")
        if (
            not isinstance(name, str)
            or not name.strip()
            or isinstance(active, bool)
            or active not in (0, 1)
        ):
            raise CheapSharkServiceError(
                "A CheapShark retornou uma loja inválida."
            )
        images = item.get("images")
        logo_value = images.get("logo") if isinstance(images, dict) else None
        stores.append(
            _Store(
                store_id=store_id,
                name=name.strip(),
                is_active=active == 1,
                logo_url=_store_logo_url(logo_value),
            )
        )
    return tuple(stores)


async def _get_deals(
    app_id: int,
    transport: httpx.AsyncBaseTransport | None,
) -> tuple[_Deal, ...]:
    payload = await _request_json(
        CHEAPSHARK_DEALS_URL,
        {
            "steamAppID": app_id,
            "pageSize": CHEAPSHARK_PAGE_SIZE,
            "country": "BR",
        },
        service="cheapshark",
        transport=transport,
    )
    return _parse_deals(payload, app_id)


async def _get_stores(
    transport: httpx.AsyncBaseTransport | None,
) -> tuple[_Store, ...]:
    cache_key = "stores"
    if transport is None:
        cached = _STORE_CACHE.get(cache_key)
        if cached is not None:
            return cached

    payload = await _request_json(
        CHEAPSHARK_STORES_URL,
        None,
        service="cheapshark",
        transport=transport,
    )
    stores = _parse_stores(payload)
    if transport is None:
        _STORE_CACHE.set(cache_key, stores)
    return stores


def parse_exchange_rate(payload: object) -> ExchangeRate:
    if (
        not isinstance(payload, dict)
        or payload.get("base") != "USD"
        or payload.get("quote") != "BRL"
    ):
        raise ExchangeRateError(
            "A API de câmbio não retornou uma cotação USD/BRL válida."
        )

    raw_date = payload.get("date")
    if not isinstance(raw_date, str):
        raise ExchangeRateError(
            "A API de câmbio não retornou a data da cotação."
        )
    try:
        quote_date = date.fromisoformat(raw_date)
    except ValueError as error:
        raise ExchangeRateError(
            "A API de câmbio retornou uma data de cotação inválida."
        ) from error
    if quote_date.isoformat() != raw_date:
        raise ExchangeRateError(
            "A API de câmbio retornou uma data de cotação inválida."
        )

    try:
        rate = _nonnegative_decimal(payload.get("rate"), "Frankfurter")
    except ValueError as error:
        raise ExchangeRateError(str(error)) from error
    if rate == 0:
        raise ExchangeRateError(
            "A API de câmbio não retornou uma cotação USD/BRL válida."
        )
    return ExchangeRate(value=rate, quote_date=quote_date)


async def get_usd_brl_rate(
    transport: httpx.AsyncBaseTransport | None = None,
) -> ExchangeRate:
    cache_key = "USD/BRL"
    if transport is None:
        cached = _RATE_CACHE.get(cache_key)
        if cached is not None:
            return cached

    payload = await _request_json(
        FRANKFURTER_RATE_URL,
        None,
        service="frankfurter",
        transport=transport,
    )
    rate = parse_exchange_rate(payload)
    if transport is None:
        _RATE_CACHE.set(cache_key, rate)
    return rate


def _format_rate_label(rate: ExchangeRate) -> str:
    formatted_rate = format(rate.value, "f").replace(".", ",")
    formatted_date = rate.quote_date.strftime("%d/%m/%Y")
    return (
        f"Cotação usada: US$ 1,00 = R$ {formatted_rate}; "
        f"Frankfurter em {formatted_date}."
    )


def _to_minor_units(amount: Decimal) -> int:
    return int(
        (amount * 100).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )


def _format_usd(amount: Decimal) -> str:
    rounded = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"US$ {rounded:.2f}".replace(".", ",")


async def search_cheapshark_offers(
    app_id: int,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[CheapSharkOffer]:
    if not isinstance(app_id, int) or isinstance(app_id, bool) or app_id <= 0:
        raise ValueError("O Steam App ID deve ser um inteiro positivo.")

    if transport is None:
        cached = _CHEAPSHARK_RESULT_CACHE.get(app_id)
        if cached is not None:
            return list(cached)

    deals = await _get_deals(app_id, transport)
    deals = tuple(
        deal for deal in deals if deal.store_id not in {"1", "7"}
    )
    if not deals:
        return _cache_offers(app_id, (), transport)

    stores = await _get_stores(transport)
    active_stores = {
        store.store_id: store for store in stores if store.is_active
    }
    deals = tuple(deal for deal in deals if deal.store_id in active_stores)
    if not deals:
        return _cache_offers(app_id, (), transport)

    rate: ExchangeRate | None = None
    if any(deal.currency == "USD" for deal in deals):
        try:
            rate = await get_usd_brl_rate(transport)
        except ExchangeRateError:
            rate = None

    prepared: list[_PreparedOffer] = []
    fetched_at = utc_now()
    for deal in deals:
        store = active_stores[deal.store_id]
        deal_url = (
            "https://www.cheapshark.com/redirect?dealID="
            f"{quote(deal.deal_id, safe='')}"
        )
        timestamp_label = format_price_timestamp(
            deal.source_updated_at,
            fetched_at,
            "CheapShark",
        )
        if deal.currency == "BRL":
            cents = _to_minor_units(deal.price)
            offer = CheapSharkOffer(
                store_name=store.name,
                price_label=format_brl(cents),
                deal_url=deal_url,
                price_brl_minor=cents,
                is_approximate=False,
                store_logo_url=store.logo_url,
                source_currency="BRL",
                original_amount=format(deal.price, "f"),
                timestamp_label=timestamp_label,
                source_updated_at=deal.source_updated_at,
                fetched_at=fetched_at,
            )
            prepared.append(
                _PreparedOffer(0, Decimal(cents), deal.store_id, offer)
            )
            continue

        if rate is not None:
            cents = _to_minor_units(deal.price * rate.value)
            offer = CheapSharkOffer(
                store_name=store.name,
                price_label=(
                    f"{_format_usd(deal.price)} ≈ {format_brl(cents)}"
                ),
                deal_url=deal_url,
                price_brl_minor=cents,
                is_approximate=True,
                store_logo_url=store.logo_url,
                source_currency="USD",
                original_amount=format(deal.price, "f"),
                rate_label=_format_rate_label(rate),
                timestamp_label=timestamp_label,
                source_updated_at=deal.source_updated_at,
                fetched_at=fetched_at,
            )
            prepared.append(
                _PreparedOffer(0, Decimal(cents), deal.store_id, offer)
            )
        else:
            offer = CheapSharkOffer(
                store_name=store.name,
                price_label=_format_usd(deal.price),
                deal_url=deal_url,
                price_brl_minor=None,
                is_approximate=False,
                store_logo_url=store.logo_url,
                source_currency="USD",
                original_amount=format(deal.price, "f"),
                timestamp_label=timestamp_label,
                source_updated_at=deal.source_updated_at,
                fetched_at=fetched_at,
            )
            prepared.append(
                _PreparedOffer(1, deal.price, deal.store_id, offer)
            )

    prepared.sort(
        key=lambda item: (
            item.sort_group,
            item.sort_price,
            item.offer.store_name.casefold(),
        )
    )
    selected: list[CheapSharkOffer] = []
    seen_stores: set[str] = set()
    for item in prepared:
        if item.store_id in seen_stores:
            continue
        seen_stores.add(item.store_id)
        selected.append(item.offer)
        if len(selected) == CHEAPSHARK_MAX_OFFERS:
            break
    return _cache_offers(app_id, tuple(selected), transport)


def _cache_offers(
    app_id: int,
    offers: tuple[CheapSharkOffer, ...],
    transport: httpx.AsyncBaseTransport | None,
) -> list[CheapSharkOffer]:
    if transport is None:
        _CHEAPSHARK_RESULT_CACHE.set(app_id, offers)
    return list(offers)
