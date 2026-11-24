import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import httpx

from Projeto.steam import (
    _SEARCH_CACHE,
    InvalidSearchTerm,
    SteamServiceError,
    SteamGame,
    find_game_by_app_id,
    format_brl,
    get_steam_game_price,
    parse_game_price,
    parse_search_results,
    search_steam_games,
    validate_search_term,
)
from Projeto import external_api
from Projeto.price_metadata import STEAM_LOGO_URL


class SearchValidationTests(unittest.TestCase):
    def test_search_term_is_trimmed(self) -> None:
        self.assertEqual(validate_search_term("  Portal  "), "Portal")

    def test_search_term_rejects_blank_and_oversized_values(self) -> None:
        with self.assertRaises(InvalidSearchTerm):
            validate_search_term(" \t ")
        with self.assertRaises(InvalidSearchTerm):
            validate_search_term("x" * 101)

    def test_format_brl_uses_cents_and_localized_separators(self) -> None:
        self.assertEqual(format_brl(659), "R$ 6,59")
        self.assertEqual(format_brl(123456789), "R$ 1.234.567,89")


class SteamResponseParsingTests(unittest.TestCase):
    def test_search_results_include_named_apps_only(self) -> None:
        games = parse_search_results(
            {
                "items": [
                    {"type": "app", "id": 620, "name": "Portal 2"},
                    {"type": "bundle", "id": 1, "name": "Bundle"},
                ]
            }
        )
        self.assertEqual([(game.app_id, game.name) for game in games], [(620, "Portal 2")])

    def test_game_selection_resolves_app_id_not_similar_name(self) -> None:
        games = [
            SteamGame(app_id=620, name="Portal 2"),
            SteamGame(app_id=400, name="Portal"),
        ]
        self.assertEqual(find_game_by_app_id(games, 400), games[1])
        self.assertIsNone(find_game_by_app_id(games, 999))

    def test_paid_price_uses_brl_cents(self) -> None:
        price = parse_game_price(
            {
                "620": {
                    "success": True,
                    "data": {
                        "type": "game",
                        "name": "Portal 2",
                        "is_free": False,
                        "header_image": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/620/header.jpg",
                        "price_overview": {"currency": "BRL", "final": 659},
                    },
                }
            },
            620,
        )
        self.assertEqual(price.status, "paid")
        self.assertEqual(price.final_price_minor, 659)
        self.assertEqual(
            price.header_image,
            "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/620/header.jpg",
        )

    def test_unsafe_header_image_is_rejected(self) -> None:
        with self.assertRaises(SteamServiceError):
            parse_game_price(
                {
                    "620": {
                        "success": True,
                        "data": {
                            "type": "game",
                            "name": "Portal 2",
                            "is_free": False,
                            "header_image": "https://attacker.invalid/cover.jpg",
                            "price_overview": {"currency": "BRL", "final": 659},
                        },
                    }
                },
                620,
            )

    def test_free_game_does_not_require_price_overview(self) -> None:
        price = parse_game_price(
            {
                "440": {
                    "success": True,
                    "data": {
                        "type": "game",
                        "name": "Team Fortress 2",
                        "is_free": True,
                    },
                }
            },
            440,
        )
        self.assertEqual(price.status, "free")
        self.assertIsNone(price.final_price_minor)

    def test_non_brl_and_missing_prices_are_unavailable(self) -> None:
        cases = [
            {"currency": "USD", "final": 659},
            {"currency": "BRL"},
        ]
        for price_overview in cases:
            with self.subTest(price_overview=price_overview):
                price = parse_game_price(
                    {
                        "620": {
                            "success": True,
                            "data": {
                                "type": "game",
                                "name": "Portal 2",
                                "is_free": False,
                                "price_overview": price_overview,
                            },
                        }
                    },
                    620,
                )
                self.assertEqual(price.status, "unavailable")
                self.assertIsNone(price.final_price_minor)

    def test_steam_not_found_is_unavailable(self) -> None:
        price = parse_game_price({"620": {"success": False}}, 620)
        self.assertEqual(price.status, "unavailable")

    def test_malformed_search_response_raises(self) -> None:
        with self.assertRaises(SteamServiceError):
            parse_search_results({"items": "invalid"})


class SteamHttpTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        _SEARCH_CACHE.clear()
        external_api._RATE_LIMIT_UNTIL.clear()

    async def asyncTearDown(self) -> None:
        external_api._RATE_LIMIT_UNTIL.clear()

    async def test_search_request_uses_brazil_and_parses_results(self) -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.params["term"], "Portal")
            self.assertEqual(request.url.params["cc"], "BR")
            self.assertEqual(request.url.params["l"], "brazilian")
            return httpx.Response(
                200,
                json={"items": [{"type": "app", "id": 620, "name": "Portal 2"}]},
                request=request,
            )

        games = await search_steam_games(
            " Portal ",
            transport=httpx.MockTransport(respond),
        )
        self.assertEqual([(game.app_id, game.name) for game in games], [(620, "Portal 2")])

    async def test_price_request_uses_brazil_and_parses_details(self) -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            self.assertEqual(request.url.params["appids"], "620")
            self.assertEqual(request.url.params["cc"], "br")
            self.assertEqual(request.url.params["l"], "brazilian")
            return httpx.Response(
                200,
                json={
                    "620": {
                        "success": True,
                        "data": {
                            "type": "game",
                            "name": "Portal 2",
                            "is_free": False,
                            "price_overview": {"currency": "BRL", "final": 659},
                        },
                    }
                },
                request=request,
            )

        price = await get_steam_game_price(
            620,
            transport=httpx.MockTransport(respond),
        )
        self.assertEqual(price.status, "paid")
        self.assertEqual(price.final_price_minor, 659)
        self.assertEqual(price.source_currency, "BRL")
        self.assertEqual(price.original_price_minor, 659)
        self.assertEqual(price.price_brl_minor, 659)
        self.assertEqual(price.store_logo_url, STEAM_LOGO_URL)
        self.assertIsNone(price.source_updated_at)
        self.assertIsNotNone(price.fetched_at)

    async def test_rate_limit_is_not_retried_and_has_a_steam_message(self) -> None:
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
            with self.assertRaisesRegex(SteamServiceError, "limite temporário"):
                await get_steam_game_price(620, transport=transport)

        self.assertEqual(calls, 1)

    async def test_repeated_price_requests_fetch_current_steam_values(self) -> None:
        prices = iter((659, 559))
        requests: list[httpx.Request] = []

        def respond(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={
                    "620": {
                        "success": True,
                        "data": {
                            "type": "game",
                            "name": "Portal 2",
                            "is_free": False,
                            "price_overview": {
                                "currency": "BRL",
                                "final": next(prices),
                            },
                        },
                    }
                },
                request=request,
            )

        transport = httpx.MockTransport(respond)
        first = await get_steam_game_price(620, transport=transport)
        second = await get_steam_game_price(620, transport=transport)

        self.assertEqual(len(requests), 2)
        self.assertEqual(first.final_price_minor, 659)
        self.assertEqual(second.final_price_minor, 559)

    async def test_non_success_http_status_is_recoverable_error(self) -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, request=request)

        with self.assertRaises(SteamServiceError):
            await search_steam_games(
                "Portal",
                transport=httpx.MockTransport(respond),
            )

    async def test_invalid_json_is_recoverable_error(self) -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=b"not-json", request=request)

        with self.assertRaises(SteamServiceError):
            await search_steam_games(
                "Portal",
                transport=httpx.MockTransport(respond),
            )

    async def test_timeout_is_recoverable_error(self) -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timeout", request=request)

        with self.assertRaisesRegex(SteamServiceError, "demorou demais"):
            await search_steam_games(
                "Portal",
                transport=httpx.MockTransport(respond),
            )


class SteamSearchCacheTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        _SEARCH_CACHE.clear()

    async def test_search_reuses_normalized_results_without_sharing_mutable_lists(self):
        response = [SteamGame(app_id=620, name="Portal 2")]
        with patch(
            "Projeto.steam._get_json",
            new=AsyncMock(
                return_value={
                    "items": [
                        {"type": "app", "id": game.app_id, "name": game.name}
                        for game in response
                    ]
                }
            ),
        ) as get_json:
            results = await search_steam_games(" Portal ")
            results.clear()
            cached_results = await search_steam_games("portal")

        get_json.assert_awaited_once()
        self.assertEqual(cached_results, response)


if __name__ == "__main__":
    unittest.main()
