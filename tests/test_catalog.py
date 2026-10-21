import unittest
from random import Random
from urllib.parse import parse_qs, urlsplit
from unittest.mock import call, patch

from Projeto.Projeto import (
    CatalogState,
    catalog_game_card,
    catalog_page,
    navbar,
    price_comparison_page,
    steam_search,
)
from Projeto.catalog import (
    CATALOG_DISPLAY_COUNT,
    CATALOG_GAMES,
    build_catalog_comparison_url,
    build_steam_search_url,
    select_catalog_games,
)
from Projeto.steam import InvalidSearchTerm


class CatalogTests(unittest.TestCase):
    def test_catalog_examples_have_names_and_steam_cover_urls(self) -> None:
        self.assertGreaterEqual(len(CATALOG_GAMES), 12)
        self.assertEqual(len({game.app_id for game in CATALOG_GAMES}), len(CATALOG_GAMES))
        for game in CATALOG_GAMES:
            with self.subTest(game=game.name):
                self.assertTrue(game.name)
                self.assertTrue(game.cover_url.startswith("https://"))
                self.assertIn(f"/{game.app_id}/header.jpg", game.cover_url)

    def test_catalog_selection_has_eight_unique_games_and_one_featured_game(self) -> None:
        selected, featured = select_catalog_games(Random(42))

        self.assertEqual(len(selected), CATALOG_DISPLAY_COUNT)
        self.assertEqual(len({game.app_id for game in selected}), CATALOG_DISPLAY_COUNT)
        self.assertIn(featured, selected)

    def test_prepare_page_sets_selected_ids_and_featured_game(self) -> None:
        selected = CATALOG_GAMES[:CATALOG_DISPLAY_COUNT]
        featured = selected[3]
        next_selected = CATALOG_GAMES[4 : 4 + CATALOG_DISPLAY_COUNT]
        next_featured = next_selected[-1]
        state = type(
            "CatalogStateStub",
            (),
            {
                "search_error": "previous error",
                "visible_app_ids": [],
                "featured_app_id": 0,
            },
        )()
        with patch(
            "Projeto.Projeto.select_catalog_games",
            side_effect=[
                (selected, featured),
                (next_selected, next_featured),
            ],
        ) as select_games:
            CatalogState.prepare_page.fn(state)
            CatalogState.prepare_page.fn(state)

        select_games.assert_has_calls([call(), call()])
        self.assertEqual(state.search_error, "")
        self.assertEqual(
            state.visible_app_ids,
            [game.app_id for game in next_selected],
        )
        self.assertEqual(state.featured_app_id, next_featured.app_id)

    def test_search_url_encodes_and_preserves_the_term(self) -> None:
        term = "Portal 2 & Friends"
        url = build_steam_search_url(term)
        parsed = urlsplit(url)

        self.assertEqual(parsed.path, "/buscar")
        self.assertEqual(parse_qs(parsed.query), {"term": [term]})

    def test_every_catalog_game_has_a_valid_comparison_url(self) -> None:
        for game in CATALOG_GAMES:
            with self.subTest(game=game.name):
                self.assertGreater(game.app_id, 0)
                self.assertEqual(
                    build_catalog_comparison_url(game.app_id),
                    f"/comparar?app_id={game.app_id}",
                )
                for featured in (False, True):
                    card = catalog_game_card(game, featured=featured)
                    self.assertEqual(
                        card.children[0].to._var_value,
                        f"/comparar?app_id={game.app_id}",
                    )

    def test_comparison_url_rejects_non_positive_app_ids(self) -> None:
        for app_id in (0, -1):
            with self.subTest(app_id=app_id):
                with self.assertRaises(ValueError):
                    build_catalog_comparison_url(app_id)

    def test_catalog_footer_follows_game_grid_and_links_to_search(self) -> None:
        page = repr(catalog_page())

        self.assertIn("ComparaKeys ajuda", page)
        self.assertIn("/buscar", page)
        self.assertLess(
            page.index("catalog-games-grid"),
            page.index("catalog-footer"),
        )

    def test_shared_header_brand_links_to_catalog_on_all_header_routes(self) -> None:
        brand_link = repr(navbar().children[0])

        self.assertIn("/catalogo", brand_link)
        for page_factory in (catalog_page, steam_search, price_comparison_page):
            with self.subTest(page=page_factory.__name__):
                self.assertIn("/catalogo", repr(page_factory()))

    def test_search_url_rejects_blank_and_oversized_terms(self) -> None:
        for term in ("  \t", "x" * 101):
            with self.subTest(term=term):
                with self.assertRaises(InvalidSearchTerm):
                    build_steam_search_url(term)


if __name__ == "__main__":
    unittest.main()
