import unittest

import httpx

from Projeto.steam import (
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
                        "price_overview": {"currency": "BRL", "final": 659},
                    },
                }
            },
            620,
        )
        self.assertEqual(price.status, "paid")
        self.assertEqual(price.final_price_minor, 659)

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


if __name__ == "__main__":
    unittest.main()
