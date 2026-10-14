import unittest
from urllib.parse import parse_qs, urlsplit

from Projeto.catalog import CATALOG_GAMES, build_steam_search_url
from Projeto.steam import InvalidSearchTerm


class CatalogTests(unittest.TestCase):
    def test_catalog_examples_have_names_and_steam_cover_urls(self) -> None:
        self.assertGreater(len(CATALOG_GAMES), 0)
        for game in CATALOG_GAMES:
            with self.subTest(game=game.name):
                self.assertTrue(game.name)
                self.assertIn(f"/{game.app_id}/header.jpg", game.cover_url)

    def test_search_url_encodes_and_preserves_the_term(self) -> None:
        term = "Portal 2 & Friends"
        url = build_steam_search_url(term)
        parsed = urlsplit(url)

        self.assertEqual(parsed.path, "/buscar")
        self.assertEqual(parse_qs(parsed.query), {"term": [term]})

    def test_search_url_rejects_blank_and_oversized_terms(self) -> None:
        for term in ("  \t", "x" * 101):
            with self.subTest(term=term):
                with self.assertRaises(InvalidSearchTerm):
                    build_steam_search_url(term)


if __name__ == "__main__":
    unittest.main()
