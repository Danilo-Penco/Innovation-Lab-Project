import asyncio
import importlib
import unittest
from unittest.mock import AsyncMock, patch

from Projeto.gog import GogOffer, GogServiceError
from Projeto.steam import SteamGame, SteamPrice


app_module = importlib.import_module("Projeto.Projeto")


class SearchStateComparisonTests(unittest.IsolatedAsyncioTestCase):
    def make_state(self):
        state = app_module.SearchState(_reflex_internal_init=True)
        state.games = [
            SteamGame(app_id=620, name="Portal 2"),
            SteamGame(app_id=440, name="Team Fortress 2"),
        ]
        return state

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
                new=AsyncMock(return_value=gog_offer),
            ),
        ):
            await app_module.SearchState.select_game.fn(state, 620)

        self.assertEqual(state.selected_name, "Portal 2")
        self.assertEqual(state.selected_cover_url, steam_price.header_image)
        self.assertEqual(state.price_cents, 659)
        self.assertEqual(state.gog_cover_url, gog_offer.cover_url)
        self.assertEqual(state.gog_price_cents, 499)
        self.assertTrue(state.gog_is_cheapest)
        self.assertFalse(state.steam_is_cheapest)

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
            await app_module.SearchState.select_game.fn(state, 620)

        self.assertEqual(state.price_cents, 659)
        self.assertEqual(state.price_status, "paid")
        self.assertEqual(state.gog_status, "")
        self.assertIn("indisponível", state.gog_error)
        self.assertFalse(state.is_loading_price)
        self.assertFalse(state.is_loading_gog)

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

    async def test_late_selection_response_cannot_replace_newer_selection(self) -> None:
        state = self.make_state()
        first_requests_started = asyncio.Event()
        release_first_requests = asyncio.Event()
        started: set[str] = set()

        async def fake_steam_price(app_id: int) -> SteamPrice:
            if app_id == 620:
                started.add("steam")
                if len(started) == 2:
                    first_requests_started.set()
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

        async def fake_gog_offer(title: str) -> GogOffer | None:
            if title == "Portal 2":
                started.add("gog")
                if len(started) == 2:
                    first_requests_started.set()
                await release_first_requests.wait()
                return GogOffer(
                    product_id="portal2",
                    title="Portal 2",
                    store_url="https://www.gog.com/en/game/portal_2",
                    cover_url="https://images.gog-statics.com/portal2.png",
                    status="paid",
                    final_price_minor=499,
                )
            return None

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
                app_module.SearchState.select_game.fn(state, 620)
            )
            await first_requests_started.wait()
            await app_module.SearchState.select_game.fn(state, 440)
            release_first_requests.set()
            await first_selection

        self.assertEqual(state.selected_app_id, 440)
        self.assertEqual(state.selected_name, "Team Fortress 2")
        self.assertEqual(state.price_cents, 0)
        self.assertEqual(state.gog_status, "")
        self.assertIn("correspondência", state.gog_error)


if __name__ == "__main__":
    unittest.main()
