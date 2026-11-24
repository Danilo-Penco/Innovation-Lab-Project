import unittest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

import httpx

from Projeto import cheapshark
from Projeto import external_api
from Projeto.cache import MemoryTTLCache


def deal(
    deal_id: str,
    store_id: int,
    sale_price: str,
    *,
    app_id: int = 369000,
    currency: str | None = None,
    last_change: int | str | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {
        "dealID": deal_id,
        "storeID": str(store_id),
        "steamAppID": str(app_id),
        "salePrice": sale_price,
    }
    if currency is not None:
        result["currency"] = currency
    if last_change is not None:
        result["lastChange"] = last_change
    return result


def stores(
    *entries: tuple[int, str, int],
    logo_by_store: dict[int, str] | None = None,
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for store_id, name, active in entries:
        store: dict[str, object] = {
            "storeID": str(store_id),
            "storeName": name,
            "isActive": active,
        }
        if logo_by_store and store_id in logo_by_store:
            store["images"] = {"logo": logo_by_store[store_id]}
        result.append(store)
    return result


class CheapSharkServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.offers_cache = cheapshark._CHEAPSHARK_RESULT_CACHE
        self.store_cache = cheapshark._STORE_CACHE
        self.rate_cache = cheapshark._RATE_CACHE
        cheapshark._CHEAPSHARK_RESULT_CACHE.clear()
        cheapshark._STORE_CACHE.clear()
        cheapshark._RATE_CACHE.clear()
        external_api._RATE_LIMIT_UNTIL.clear()

    def tearDown(self) -> None:
        cheapshark._CHEAPSHARK_RESULT_CACHE = self.offers_cache
        cheapshark._STORE_CACHE = self.store_cache
        cheapshark._RATE_CACHE = self.rate_cache
        self.offers_cache.clear()
        self.store_cache.clear()
        self.rate_cache.clear()
        external_api._RATE_LIMIT_UNTIL.clear()

    def test_exchange_rate_requires_a_valid_quote_and_date(self) -> None:
        rate = cheapshark.parse_exchange_rate(
            {
                "base": "USD",
                "quote": "BRL",
                "rate": "5.9079",
                "date": "2026-11-21",
            }
        )
        self.assertEqual(rate.value, Decimal("5.9079"))
        self.assertEqual(rate.quote_date.isoformat(), "2026-11-21")

        invalid_responses = [
            {"base": "USD", "quote": "BRL", "rate": "5.9"},
            {
                "base": "USD",
                "quote": "BRL",
                "rate": "5.9",
                "date": "21/11/2026",
            },
            {
                "base": "USD",
                "quote": "BRL",
                "rate": "NaN",
                "date": "2026-11-21",
            },
            {
                "base": "EUR",
                "quote": "BRL",
                "rate": "5.9",
                "date": "2026-11-21",
            },
        ]
        for payload in invalid_responses:
            with self.subTest(payload=payload):
                with self.assertRaises(cheapshark.ExchangeRateError):
                    cheapshark.parse_exchange_rate(payload)

    def test_source_time_and_store_logo_reject_invalid_values(self) -> None:
        parsed_deal = cheapshark._parse_deals(
            [deal("valid-time", 35, "1.00", last_change=1794817753)],
            369000,
        )[0]
        self.assertEqual(
            parsed_deal.source_updated_at,
            datetime.fromtimestamp(1794817753, timezone.utc),
        )

        invalid_deal = cheapshark._parse_deals(
            [deal("bad-time", 35, "1.00", last_change="not-a-time")],
            369000,
        )[0]
        self.assertIsNone(invalid_deal.source_updated_at)
        parsed_store = cheapshark._parse_stores(
            stores(
                (35, "DreamGame", 1),
                logo_by_store={35: "https://attacker.invalid/logo.png"},
            )
        )[0]
        self.assertEqual(parsed_store.name, "DreamGame")
        self.assertEqual(parsed_store.logo_url, "")

    async def test_native_brl_offer_is_not_converted(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if request.url.path.endswith("/deals"):
                return httpx.Response(
                    200,
                    json=[deal("native%3D", 35, "10.00", currency="BRL")],
                )
            if request.url.path.endswith("/stores"):
                return httpx.Response(
                    200,
                    json=stores(
                        (35, "DreamGame", 1),
                        logo_by_store={35: "/img/stores/logos/34.png"},
                    ),
                )
            self.fail(f"Unexpected request: {request.url}")

        result = await cheapshark.search_cheapshark_offers(
            369000,
            transport=httpx.MockTransport(handler),
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].price_label, "R$ 10,00")
        self.assertEqual(result[0].price_brl_minor, 1000)
        self.assertFalse(result[0].is_approximate)
        self.assertEqual(result[0].source_currency, "BRL")
        self.assertEqual(result[0].original_amount, "10.00")
        self.assertEqual(
            result[0].store_logo_url,
            "https://www.cheapshark.com/img/stores/logos/34.png",
        )
        self.assertIsNone(result[0].source_updated_at)
        self.assertTrue(
            result[0].timestamp_label.startswith("Consultado pelo ComparaKeys:")
        )
        self.assertTrue(result[0].deal_url.endswith("dealID=native%3D"))
        self.assertEqual(len(requests), 2)
        deals_request = next(
            request for request in requests if request.url.path.endswith("/deals")
        )
        self.assertEqual(deals_request.url.params["steamAppID"], "369000")
        self.assertEqual(deals_request.url.params["pageSize"], "60")
        self.assertEqual(deals_request.url.params["country"], "BR")
        for request in requests:
            self.assertEqual(
                request.headers["User-Agent"],
                cheapshark.CHEAPSHARK_USER_AGENT,
            )
            self.assertEqual(
                request.extensions["timeout"]["connect"],
                cheapshark.CHEAPSHARK_TIMEOUT_SECONDS,
            )

    async def test_usd_offers_convert_sort_filter_and_limit_distinct_stores(self) -> None:
        offers = [
            deal("duplicate-expensive", 35, "0.30"),
            deal(
                "dreamgame-cheapest",
                35,
                "0.05",
                last_change=1794817753,
            ),
            deal("gamesplanet", 27, "0.10"),
            deal("fanatical", 15, "0.20"),
            deal("gamersgate", 2, "0.40"),
            deal("indiegala", 30, "0.50"),
            deal("sixth", 38, "0.60"),
            deal("steam", 1, "0.01"),
            deal("gog", 7, "0.02"),
            deal("inactive", 99, "0.001"),
            deal("different-game", 35, "0.001", app_id=620),
        ]
        store_list = stores(
            (35, "DreamGame", 1),
            (27, "Gamesplanet", 1),
            (15, "Fanatical", 1),
            (2, "GamersGate", 1),
            (30, "IndieGala", 1),
            (38, "Sixth Store", 1),
            (1, "Steam", 1),
            (7, "GOG", 1),
            (99, "Inactive Store", 0),
            logo_by_store={35: "/img/stores/logos/34.png"},
        )
        requests: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request.url.host + request.url.path)
            if request.url.path.endswith("/deals"):
                return httpx.Response(200, json=offers)
            if request.url.path.endswith("/stores"):
                return httpx.Response(200, json=store_list)
            if request.url.path == "/v2/rate/usd/brl":
                return httpx.Response(
                    200,
                    json={
                        "base": "USD",
                        "quote": "BRL",
                        "rate": 5,
                        "date": "2026-11-21",
                    },
                )
            self.fail(f"Unexpected request: {request.url}")

        result = await cheapshark.search_cheapshark_offers(
            369000,
            transport=httpx.MockTransport(handler),
        )

        self.assertEqual(
            [offer.store_name for offer in result],
            ["DreamGame", "Gamesplanet", "Fanatical", "GamersGate", "IndieGala"],
        )
        self.assertEqual(
            [offer.price_brl_minor for offer in result],
            [25, 50, 100, 200, 250],
        )
        self.assertTrue(all(offer.is_approximate for offer in result))
        self.assertEqual(
            result[0].price_label,
            "US$ 0,05 ≈ R$ 0,25",
        )
        self.assertEqual(result[0].source_currency, "USD")
        self.assertEqual(result[0].original_amount, "0.05")
        self.assertEqual(
            result[0].store_logo_url,
            "https://www.cheapshark.com/img/stores/logos/34.png",
        )
        self.assertEqual(
            result[0].source_updated_at,
            datetime.fromtimestamp(1794817753, timezone.utc),
        )
        self.assertTrue(
            result[0].timestamp_label.startswith(
                "Atualização informada pela CheapShark:"
            )
        )
        self.assertEqual(result[0].rate_label, (
            "Cotação usada: US$ 1,00 = R$ 5; Frankfurter em 21/11/2026."
        ))
        self.assertEqual(
            result[0].deal_url,
            "https://www.cheapshark.com/redirect?dealID=dreamgame-cheapest",
        )
        self.assertEqual(
            requests,
            [
                "www.cheapshark.com/api/1.0/deals",
                "www.cheapshark.com/api/1.0/stores",
                "api.frankfurter.dev/v2/rate/usd/brl",
            ],
        )

    async def test_missing_exchange_rate_keeps_usd_offers(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/deals"):
                return httpx.Response(
                    200,
                    json=[deal("dollar-deal", 35, "1.25")],
                )
            if request.url.path.endswith("/stores"):
                return httpx.Response(
                    200,
                    json=stores((35, "DreamGame", 1)),
                )
            if request.url.path == "/v2/rate/usd/brl":
                return httpx.Response(503, json={"error": "unavailable"})
            self.fail(f"Unexpected request: {request.url}")

        result = await cheapshark.search_cheapshark_offers(
            369000,
            transport=httpx.MockTransport(handler),
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].price_label, "US$ 1,25")
        self.assertIsNone(result[0].price_brl_minor)
        self.assertFalse(result[0].is_approximate)

    async def test_missing_rate_field_keeps_usd_offers(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/deals"):
                return httpx.Response(
                    200,
                    json=[deal("missing-rate", 35, "0.75")],
                )
            if request.url.path.endswith("/stores"):
                return httpx.Response(
                    200,
                    json=stores((35, "DreamGame", 1)),
                )
            if request.url.path == "/v2/rate/usd/brl":
                return httpx.Response(
                    200,
                    json={"base": "USD", "quote": "BRL"},
                )
            self.fail(f"Unexpected request: {request.url}")

        result = await cheapshark.search_cheapshark_offers(
            369000,
            transport=httpx.MockTransport(handler),
        )

        self.assertEqual(result[0].price_label, "US$ 0,75")
        self.assertIsNone(result[0].price_brl_minor)

    async def test_empty_offers_do_not_request_stores_or_exchange(self) -> None:
        requests: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request.url.path)
            return httpx.Response(200, json=[])

        result = await cheapshark.search_cheapshark_offers(
            369000,
            transport=httpx.MockTransport(handler),
        )

        self.assertEqual(result, [])
        self.assertEqual(requests, ["/api/1.0/deals"])

    async def test_invalid_deal_response_has_a_specific_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"deals": []})

        with self.assertRaisesRegex(
            cheapshark.CheapSharkServiceError,
            "lista de ofertas inválida",
        ):
            await cheapshark.search_cheapshark_offers(
                369000,
                transport=httpx.MockTransport(handler),
            )

    async def test_invalid_json_has_a_specific_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=b"not json")

        with self.assertRaisesRegex(
            cheapshark.CheapSharkServiceError,
            "resposta inválida",
        ):
            await cheapshark.search_cheapshark_offers(
                369000,
                transport=httpx.MockTransport(handler),
            )

    async def test_network_error_retries_once(self) -> None:
        calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise httpx.ConnectError("network failure", request=request)
            return httpx.Response(200, json=[])

        result = await cheapshark.search_cheapshark_offers(
            369000,
            transport=httpx.MockTransport(handler),
        )

        self.assertEqual(result, [])
        self.assertEqual(calls, 2)

    async def test_http_error_is_not_retried_and_429_honors_retry_after(self) -> None:
        calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return httpx.Response(
                429,
                headers={"Retry-After": "30"},
                json={"error": "rate limited"},
            )

        transport = httpx.MockTransport(handler)
        with self.assertRaisesRegex(
            cheapshark.CheapSharkServiceError,
            "limite temporário",
        ):
            await cheapshark.search_cheapshark_offers(369000, transport=transport)

        self.assertEqual(calls, 1)
        with self.assertRaisesRegex(
            cheapshark.CheapSharkServiceError,
            "limite temporário",
        ):
            await cheapshark.search_cheapshark_offers(369000, transport=transport)
        self.assertEqual(calls, 1)

    async def test_server_error_is_not_retried(self) -> None:
        calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return httpx.Response(503, json={"error": "unavailable"})

        with self.assertRaisesRegex(
            cheapshark.CheapSharkServiceError,
            "não está disponível",
        ):
            await cheapshark.search_cheapshark_offers(
                369000,
                transport=httpx.MockTransport(handler),
            )

        self.assertEqual(calls, 1)

    async def test_frankfurter_429_honors_retry_after(self) -> None:
        calls = 0

        def respond(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return httpx.Response(
                429,
                headers={"Retry-After": "30"},
                request=request,
            )

        transport = httpx.MockTransport(respond)
        for _ in range(2):
            with self.assertRaisesRegex(
                cheapshark.ExchangeRateError,
                "limite temporário",
            ):
                await cheapshark.get_usd_brl_rate(transport=transport)

        self.assertEqual(calls, 1)

    async def test_offer_cache_is_five_minutes_and_rate_cache_is_one_hour(self) -> None:
        now = [0.0]
        cheapshark._CHEAPSHARK_RESULT_CACHE = MemoryTTLCache(
            max_entries=256,
            ttl_seconds=300,
            clock=lambda: now[0],
        )
        cheapshark._STORE_CACHE = MemoryTTLCache(
            max_entries=1,
            ttl_seconds=300,
            clock=lambda: now[0],
        )
        cheapshark._RATE_CACHE = MemoryTTLCache(
            max_entries=1,
            ttl_seconds=3600,
            max_ttl_seconds=3600,
            clock=lambda: now[0],
        )
        counts = {"deals": 0, "stores": 0, "rate": 0}

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/deals"):
                counts["deals"] += 1
                return httpx.Response(
                    200,
                    json=[deal("cached", 35, "1.00")],
                )
            if request.url.path.endswith("/stores"):
                counts["stores"] += 1
                return httpx.Response(
                    200,
                    json=stores((35, "DreamGame", 1)),
                )
            if request.url.path == "/v2/rate/usd/brl":
                counts["rate"] += 1
                return httpx.Response(
                    200,
                    json={
                        "base": "USD",
                        "quote": "BRL",
                        "rate": "5.00",
                        "date": "2026-11-21",
                    },
                )
            self.fail(f"Unexpected request: {request.url}")

        mock_transport = httpx.MockTransport(handler)
        real_async_client = httpx.AsyncClient
        fetched_times = iter(
            (
                datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc),
                datetime(2026, 11, 21, 12, 5, tzinfo=timezone.utc),
                datetime(2026, 11, 21, 13, 0, tzinfo=timezone.utc),
            )
        )

        def client_factory(*args, **kwargs):
            kwargs["transport"] = mock_transport
            return real_async_client(*args, **kwargs)

        with (
            patch.object(
                cheapshark.httpx,
                "AsyncClient",
                side_effect=client_factory,
            ),
            patch.object(
                cheapshark,
                "utc_now",
                side_effect=lambda: next(fetched_times),
            ),
        ):
            first = await cheapshark.search_cheapshark_offers(369000)
            now[0] = 100
            cached = await cheapshark.search_cheapshark_offers(369000)
            self.assertEqual(first[0].fetched_at, cached[0].fetched_at)
            self.assertEqual(
                first[0].fetched_at,
                datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc),
            )
            self.assertEqual(counts, {"deals": 1, "stores": 1, "rate": 1})

            now[0] = 300
            expired = await cheapshark.search_cheapshark_offers(369000)
            self.assertNotEqual(first[0].fetched_at, expired[0].fetched_at)
            self.assertEqual(counts, {"deals": 2, "stores": 2, "rate": 1})

            now[0] = 3600
            await cheapshark.search_cheapshark_offers(369000)
            self.assertEqual(counts, {"deals": 3, "stores": 3, "rate": 2})


if __name__ == "__main__":
    unittest.main()
