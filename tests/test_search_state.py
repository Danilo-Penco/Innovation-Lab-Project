import asyncio
import importlib
import unittest
from unittest.mock import AsyncMock, patch

from Projeto.cheapshark import (
    CHEAPSHARK_NO_OFFERS_MESSAGE,
    CHEAPSHARK_USD_FALLBACK_NOTICE,
    CheapSharkOffer,
    CheapSharkServiceError,
)
from Projeto.gog import GogMatchResult, GogOffer, GogServiceError
from Projeto.steam import SteamGame, SteamPrice


app_module = importlib.import_module("Projeto.Projeto")


class SearchStateComparisonTests(unittest.IsolatedAsyncioTestCase):
    def make_state(self):
        state = app_module.SearchState(_reflex_internal_init=True)
        state.games = [
            SteamGame(app_id=620, name="Portal 2"),
            SteamGame(app_id=440, name="Team Fortress 2"),
        ]
        cheapshark_patch = patch.object(
            app_module,
            "search_cheapshark_offers",
            new=AsyncMock(return_value=[]),
        )
        cheapshark_patch.start()
        self.addCleanup(cheapshark_patch.stop)
        gog_patch = patch.object(
            app_module,
            "search_gog_offer",
            new=AsyncMock(return_value=GogMatchResult(status="not_found")),
        )
        gog_patch.start()
        self.addCleanup(gog_patch.stop)
        return state

    async def test_search_term_automatically_loads_results(self) -> None:
        state = self.make_state()
        with patch.object(
            app_module,
            "search_steam_games",
            new=AsyncMock(return_value=[SteamGame(app_id=620, name="Portal 2")]),
        ) as search:
            await app_module.SearchState.set_search_term.fn(state, "Portal")

        search.assert_awaited_once_with("Portal")
        self.assertEqual(state.games, [SteamGame(app_id=620, name="Portal 2")])
        self.assertFalse(state.is_searching)
        self.assertFalse(state.no_results)

    async def test_catalog_query_term_uses_the_automatic_search_flow(self) -> None:
        state = self.make_state()
        with patch.object(
            app_module,
            "search_steam_games",
            new=AsyncMock(return_value=[SteamGame(app_id=620, name="Portal 2")]),
        ) as search:
            await app_module.SearchState._load_search_term(state, "Portal")

        search.assert_awaited_once_with("Portal")
        self.assertEqual(state.search_term, "Portal")
        self.assertEqual(state.games[0].app_id, 620)

    async def test_empty_search_term_clears_old_results_without_request(self) -> None:
        state = self.make_state()
        state.no_results = True
        state.search_error = "erro antigo"
        with patch.object(app_module, "search_steam_games", new=AsyncMock()) as search:
            await app_module.SearchState.set_search_term.fn(state, "")

        search.assert_not_awaited()
        self.assertEqual(state.games, [])
        self.assertFalse(state.no_results)
        self.assertEqual(state.search_error, "")
        self.assertFalse(state.is_searching)

    async def test_search_failure_does_not_restore_previous_results(self) -> None:
        state = self.make_state()
        with patch.object(
            app_module,
            "search_steam_games",
            new=AsyncMock(side_effect=app_module.SteamServiceError("Steam offline")),
        ):
            await app_module.SearchState.set_search_term.fn(state, "Unknown")

        self.assertEqual(state.games, [])
        self.assertTrue(state.search_error)
        self.assertFalse(state.is_searching)

    async def test_late_search_response_cannot_replace_new_term_results(self) -> None:
        state = self.make_state()
        first_search_started = asyncio.Event()
        release_first_search = asyncio.Event()

        async def fake_search(term: str) -> list[SteamGame]:
            if term == "Portal":
                first_search_started.set()
                await release_first_search.wait()
                return [SteamGame(app_id=620, name="Portal 2")]
            return [SteamGame(app_id=440, name="Team Fortress 2")]

        with patch.object(
            app_module,
            "search_steam_games",
            new=AsyncMock(side_effect=fake_search),
        ):
            first_search = asyncio.create_task(
                app_module.SearchState.set_search_term.fn(state, "Portal")
            )
            await first_search_started.wait()
            await app_module.SearchState.set_search_term.fn(state, "Team")
            release_first_search.set()
            await first_search

        self.assertEqual(state.search_term, "Team")
        self.assertEqual(state.games, [SteamGame(app_id=440, name="Team Fortress 2")])
        self.assertFalse(state.is_searching)

    async def test_selection_applies_both_store_offers_and_cheapest_color(self) -> None:
        state = self.make_state()
        steam_price = SteamPrice(
            app_id=620,
            name="Portal 2",
            status="paid",
            final_price_minor=659,
            header_image="https://shared.akamai.steamstatic.com/portal2/header.jpg",
        )
        gog_offer = GogOffer(
            product_id="portal2",
            title="Portal 2",
            store_url="https://www.gog.com/en/game/portal_2",
            cover_url="https://images.gog-statics.com/portal2.png",
            status="paid",
            final_price_minor=499,
        )
        with (
            patch.object(
                app_module,
                "get_steam_game_price",
                new=AsyncMock(return_value=steam_price),
            ),
            patch.object(
                app_module,
                "search_gog_offer",
                new=AsyncMock(
                    return_value=GogMatchResult(
                        status="matched",
                        offer=gog_offer,
                    )
                ),
            ),
        ):
            await app_module.SearchState._load_comparison(state, 620)

        self.assertEqual(state.selected_name, "Portal 2")
        self.assertEqual(state.selected_cover_url, steam_price.header_image)
        self.assertEqual(state.price_cents, 659)
        self.assertEqual(state.gog_cover_url, gog_offer.cover_url)
        self.assertEqual(state.gog_price_cents, 499)
        self.assertTrue(state.gog_is_cheapest)
        self.assertFalse(state.steam_is_cheapest)

    async def test_cheapshark_and_gog_ties_are_all_marked_as_lowest(self) -> None:
        state = self.make_state()
        cheapshark_offers = [
            CheapSharkOffer(
                store_name="DreamGame",
                price_label="≈ R$ 4,99",
                deal_url="https://www.cheapshark.com/redirect?dealID=deal",
                price_brl_minor=499,
                is_approximate=True,
            )
        ]
        with (
            patch.object(
                app_module,
                "get_steam_game_price",
                new=AsyncMock(
                    return_value=SteamPrice(
                        app_id=620,
                        name="Portal 2",
                        status="paid",
                        final_price_minor=659,
                    )
                ),
            ),
            patch.object(
                app_module,
                "search_gog_offer",
                new=AsyncMock(
                    return_value=GogMatchResult(
                        status="matched",
                        offer=GogOffer(
                            product_id="portal2",
                            title="Portal 2",
                            store_url="https://www.gog.com/en/game/portal_2",
                            cover_url="https://images.gog-statics.com/portal2.png",
                            status="paid",
                            final_price_minor=499,
                        ),
                    )
                ),
            ),
            patch.object(
                app_module,
                "search_cheapshark_offers",
                new=AsyncMock(return_value=cheapshark_offers),
            ),
        ):
            await app_module.SearchState._load_comparison(state, 620)

        self.assertTrue(state.gog_is_cheapest)
        self.assertFalse(state.steam_is_cheapest)
        self.assertTrue(state.cheapshark_offers[0].is_cheapest)
        self.assertEqual(
            state.cheapshark_currency_notice,
            "Preços internacionais em dólar, convertidos pela cotação do dia. "
            "Steam e GOG mostram o preço regional em reais, então a "
            "comparação é aproximada.",
        )

    async def test_cheapshark_failure_keeps_steam_and_gog_results(self) -> None:
        state = self.make_state()
        with (
            patch.object(
                app_module,
                "get_steam_game_price",
                new=AsyncMock(
                    return_value=SteamPrice(
                        app_id=620,
                        name="Portal 2",
                        status="paid",
                        final_price_minor=659,
                    )
                ),
            ),
            patch.object(
                app_module,
                "search_gog_offer",
                new=AsyncMock(
                    return_value=GogMatchResult(
                        status="matched",
                        offer=GogOffer(
                            product_id="portal2",
                            title="Portal 2",
                            store_url="https://www.gog.com/en/game/portal_2",
                            cover_url="https://images.gog-statics.com/portal2.png",
                            status="paid",
                            final_price_minor=499,
                        ),
                    )
                ),
            ),
            patch.object(
                app_module,
                "search_cheapshark_offers",
                new=AsyncMock(
                    side_effect=CheapSharkServiceError(
                        "A CheapShark demorou demais para responder."
                    )
                ),
            ),
        ):
            await app_module.SearchState._load_comparison(state, 620)

        self.assertEqual(state.price_cents, 659)
        self.assertEqual(state.gog_price_cents, 499)
        self.assertIn("CheapShark demorou", state.cheapshark_error)
        self.assertIn("Steam e GOG continuam disponíveis", state.cheapshark_error)
        self.assertFalse(state.is_loading_cheapshark)

    async def test_empty_cheapshark_result_has_its_own_message(self) -> None:
        state = self.make_state()
        with patch.object(
            app_module,
            "get_steam_game_price",
            new=AsyncMock(
                return_value=SteamPrice(
                    app_id=620,
                    name="Portal 2",
                    status="paid",
                    final_price_minor=659,
                )
            ),
        ):
            await app_module.SearchState._load_comparison(state, 620)

        self.assertEqual(
            state.cheapshark_error,
            CHEAPSHARK_NO_OFFERS_MESSAGE,
        )
        self.assertEqual(state.price_cents, 659)

    async def test_unconverted_usd_offer_shows_fallback_notice(self) -> None:
        state = self.make_state()
        raw_usd_offer = CheapSharkOffer(
            store_name="DreamGame",
            price_label="US$ 1,00",
            deal_url="https://www.cheapshark.com/redirect?dealID=deal",
            price_brl_minor=None,
            is_approximate=False,
        )
        with (
            patch.object(
                app_module,
                "get_steam_game_price",
                new=AsyncMock(
                    return_value=SteamPrice(
                        app_id=620,
                        name="Portal 2",
                        status="paid",
                        final_price_minor=659,
                    )
                ),
            ),
            patch.object(
                app_module,
                "search_cheapshark_offers",
                new=AsyncMock(return_value=[raw_usd_offer]),
            ),
        ):
            await app_module.SearchState._load_comparison(state, 620)

        self.assertEqual(
            state.cheapshark_currency_notice,
            CHEAPSHARK_USD_FALLBACK_NOTICE,
        )
        self.assertEqual(state.price_cents, 659)

    async def test_gog_failure_keeps_steam_price_and_sets_warning(self) -> None:
        state = self.make_state()
        steam_price = SteamPrice(
            app_id=620,
            name="Portal 2",
            status="paid",
            final_price_minor=659,
        )
        with (
            patch.object(
                app_module,
                "get_steam_game_price",
                new=AsyncMock(return_value=steam_price),
            ),
            patch.object(
                app_module,
                "search_gog_offer",
                side_effect=GogServiceError("network failure"),
            ),
        ):
            await app_module.SearchState._load_comparison(state, 620)

        self.assertEqual(state.price_cents, 659)
        self.assertEqual(state.price_status, "paid")
        self.assertEqual(state.gog_status, "")
        self.assertEqual(state.gog_error, "network failure")
        self.assertTrue(state.gog_retryable)
        self.assertFalse(state.is_loading_price)
        self.assertFalse(state.is_loading_gog)

    async def test_comparison_loads_free_and_unavailable_steam_prices(self) -> None:
        state = self.make_state()
        free_price = SteamPrice(
            app_id=620,
            name="Portal 2",
            status="free",
        )
        unavailable_price = SteamPrice(
            app_id=440,
            name="Team Fortress 2",
            status="unavailable",
        )
        with (
            patch.object(
                app_module,
                "get_steam_game_price",
                new=AsyncMock(side_effect=[free_price, unavailable_price]),
            ),
            patch.object(
                app_module,
                "search_gog_offer",
                new=AsyncMock(
                    return_value=GogMatchResult(status="not_found")
                ),
            ),
        ):
            await app_module.SearchState._load_comparison(state, 620)
            self.assertEqual(state.price_status, "free")
            await app_module.SearchState._load_comparison(state, 440)
            self.assertEqual(state.price_status, "unavailable")

        self.assertEqual(state.selected_app_id, 440)
        self.assertEqual(state.selected_name, "Team Fortress 2")
        self.assertFalse(state.is_loading_price)
        self.assertFalse(state.is_loading_gog)

    async def test_gog_match_failures_have_distinct_messages_and_keep_steam(self) -> None:
        cases = [
            (GogMatchResult(status="not_found"), "não encontrado na GOG"),
            (
                GogMatchResult(status="ambiguous"),
                "Mais de uma possível correspondência",
            ),
            (
                GogMatchResult(
                    status="matched",
                    offer=GogOffer(
                        product_id="portal2",
                        title="Portal 2",
                        store_url="https://www.gog.com/en/game/portal_2",
                        cover_url="https://images.gog-statics.com/portal2.png",
                        status="unavailable",
                    ),
                ),
                "Sem preço em BRL na GOG",
            ),
        ]
        for gog_result, expected_message in cases:
            with self.subTest(message=expected_message):
                state = self.make_state()
                with (
                    patch.object(
                        app_module,
                        "get_steam_game_price",
                        new=AsyncMock(
                            return_value=SteamPrice(
                                app_id=620,
                                name="Portal 2",
                                status="paid",
                                final_price_minor=659,
                            )
                        ),
                    ),
                    patch.object(
                        app_module,
                        "search_gog_offer",
                        new=AsyncMock(return_value=gog_result),
                    ),
                ):
                    await app_module.SearchState._load_comparison(state, 620)

                self.assertEqual(state.price_cents, 659)
                self.assertEqual(state.price_status, "paid")
                self.assertEqual(state.gog_status, "")
                self.assertIn(expected_message, state.gog_error)

    async def test_steam_failure_is_reported_on_comparison_route(self) -> None:
        state = self.make_state()
        offers = [
            CheapSharkOffer(
                store_name="DreamGame",
                price_label="US$ 1,00",
                deal_url="https://www.cheapshark.com/redirect?dealID=deal",
                price_brl_minor=None,
                is_approximate=False,
            )
        ]
        with (
            patch.object(
                app_module,
                "get_steam_game_price",
                new=AsyncMock(
                    side_effect=app_module.SteamServiceError(
                        "A Steam está indisponível."
                    )
                ),
            ),
            patch.object(
                app_module,
                "search_cheapshark_offers",
                new=AsyncMock(return_value=offers),
            ) as cheapshark_search,
        ):
            await app_module.SearchState._load_comparison(state, 620)

        cheapshark_search.assert_awaited_once_with(620)
        self.assertEqual(state.price_error, "A Steam está indisponível.")
        self.assertFalse(state.is_loading_price)
        self.assertEqual(state.price_status, "")
        self.assertEqual(state.cheapshark_offers[0].store_name, "DreamGame")

    async def test_invalid_comparison_id_is_rejected_without_request(self) -> None:
        state = self.make_state()
        with patch.object(
            app_module,
            "get_steam_game_price",
            new=AsyncMock(),
        ) as get_price:
            await app_module.SearchState._load_comparison_from_query(
                state,
                "not-an-id",
            )

        get_price.assert_not_awaited()
        self.assertEqual(state.selected_app_id, 0)
        self.assertIn("inválido", state.price_error)

    async def test_select_game_redirects_only_for_a_search_result(self) -> None:
        state = self.make_state()
        redirect = app_module.SearchState.select_game.fn(state, 620)
        self.assertIsNotNone(redirect)
        self.assertIn("/comparar?app_id=620", repr(redirect.args))
        self.assertIsNone(app_module.SearchState.select_game.fn(state, 999))

    async def test_free_price_and_tie_are_both_considered_lowest(self) -> None:
        state = self.make_state()
        state.price_status = "free"
        state.price_cents = 0
        state.gog_status = "paid"
        state.gog_price_cents = 1
        self.assertTrue(state.steam_is_cheapest)
        self.assertFalse(state.gog_is_cheapest)

        state.gog_status = "free"
        state.gog_price_cents = 0
        self.assertTrue(state.steam_is_cheapest)
        self.assertTrue(state.gog_is_cheapest)

    async def test_cheapshark_retry_only_reloads_its_own_provider(self) -> None:
        state = self.make_state()
        state.selected_app_id = 620
        state.price_cents = 659
        state.price_status = "paid"
        state.cheapshark_error = "Falha temporária."
        state.cheapshark_retryable = True
        offers = [
            CheapSharkOffer(
                store_name="DreamGame",
                price_label="US$ 1,00",
                deal_url="https://www.cheapshark.com/redirect?dealID=deal",
                price_brl_minor=None,
                is_approximate=False,
            )
        ]
        with (
            patch.object(
                app_module,
                "search_cheapshark_offers",
                new=AsyncMock(return_value=offers),
            ) as cheapshark_search,
            patch.object(app_module, "get_steam_game_price", new=AsyncMock()) as steam,
            patch.object(app_module, "search_gog_offer", new=AsyncMock()) as gog,
        ):
            await app_module.SearchState.retry_cheapshark.fn(state)

        cheapshark_search.assert_awaited_once_with(620)
        steam.assert_not_awaited()
        gog.assert_not_awaited()
        self.assertFalse(state.cheapshark_retryable)
        self.assertEqual(state.price_cents, 659)

    async def test_steam_retry_failure_preserves_other_provider_results(self) -> None:
        state = self.make_state()
        state.selected_app_id = 620
        state.cheapshark_offers = [
            CheapSharkOffer(
                store_name="DreamGame",
                price_label="US$ 1,00",
                deal_url="https://www.cheapshark.com/redirect?dealID=deal",
                price_brl_minor=None,
                is_approximate=False,
            )
        ]
        with patch.object(
            app_module,
            "get_steam_game_price",
            new=AsyncMock(
                side_effect=app_module.SteamServiceError("Steam indisponível")
            ),
        ):
            await app_module.SearchState.retry_steam.fn(state)

        self.assertEqual(state.cheapshark_offers[0].store_name, "DreamGame")
        self.assertEqual(state.price_error, "Steam indisponível")
        self.assertTrue(state.steam_retryable)

    async def test_gog_retry_only_reloads_gog_and_updates_comparable_prices(self) -> None:
        state = self.make_state()
        state.selected_app_id = 620
        state.selected_name = "Portal 2"
        state.gog_retryable = True
        state.price_status = "paid"
        state.price_cents = 659
        result = GogMatchResult(
            status="matched",
            offer=GogOffer(
                product_id="portal2",
                title="Portal 2",
                store_url="https://www.gog.com/en/game/portal_2",
                cover_url="https://images.gog-statics.com/portal2.png",
                status="paid",
                final_price_minor=499,
            ),
        )
        with (
            patch.object(
                app_module,
                "search_gog_offer",
                new=AsyncMock(return_value=result),
            ) as gog_search,
            patch.object(
                app_module,
                "get_steam_game_price",
                new=AsyncMock(),
            ) as steam,
            patch.object(
                app_module,
                "search_cheapshark_offers",
                new=AsyncMock(),
            ) as cheapshark_search,
        ):
            await app_module.SearchState.retry_gog.fn(state)

        gog_search.assert_awaited_once_with("Portal 2")
        steam.assert_not_awaited()
        cheapshark_search.assert_not_awaited()
        self.assertEqual(state.gog_price_cents, 499)
        self.assertFalse(state.gog_retryable)

    async def test_late_selection_response_cannot_replace_newer_selection(self) -> None:
        state = self.make_state()
        release_first_requests = asyncio.Event()
        first_steam_started = asyncio.Event()

        async def fake_steam_price(app_id: int) -> SteamPrice:
            if app_id == 620:
                first_steam_started.set()
                await release_first_requests.wait()
                return SteamPrice(
                    app_id=620,
                    name="Portal 2",
                    status="paid",
                    final_price_minor=659,
                )
            return SteamPrice(
                app_id=440,
                name="Team Fortress 2",
                status="paid",
                final_price_minor=0,
            )

        async def fake_gog_offer(title: str) -> GogMatchResult:
            if title == "Portal 2":
                await release_first_requests.wait()
                return GogMatchResult(
                    status="matched",
                    offer=GogOffer(
                        product_id="portal2",
                        title="Portal 2",
                        store_url="https://www.gog.com/en/game/portal_2",
                        cover_url="https://images.gog-statics.com/portal2.png",
                        status="paid",
                        final_price_minor=499,
                    ),
                )
            return GogMatchResult(status="not_found")

        with (
            patch.object(
                app_module,
                "get_steam_game_price",
                new=AsyncMock(side_effect=fake_steam_price),
            ),
            patch.object(
                app_module,
                "search_gog_offer",
                new=AsyncMock(side_effect=fake_gog_offer),
            ),
        ):
            first_selection = asyncio.create_task(
                app_module.SearchState._load_comparison(state, 620)
            )
            await first_steam_started.wait()
            await app_module.SearchState._load_comparison(state, 440)
            release_first_requests.set()
            await first_selection

        self.assertEqual(state.selected_app_id, 440)
        self.assertEqual(state.selected_name, "Team Fortress 2")
        self.assertEqual(state.price_cents, 0)
        self.assertEqual(state.gog_status, "")
        self.assertIn("não encontrado", state.gog_error)


if __name__ == "__main__":
    unittest.main()
