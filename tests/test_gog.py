import unittest

import httpx

from Projeto.gog import (
    GOG_CATALOG_URL,
    GogServiceError,
    normalize_title,
    parse_catalog_results,
    search_gog_offer,
)


def gog_product(
    *,
    title: str = "Baldur's Gate 3",
    amount: str | None = "199.99",
    currency: str | None = "BRL",
    store_url: str = "https://www.gog.com/en/game/baldurs_gate_iii",
    cover_url: str = "https://images.gog-statics.com/example.png",
) -> dict[str, object]:
    price: dict[str, object] = {}
    if amount is not None and currency is not None:
        price["finalMoney"] = {"amount": amount, "currency": currency}
    return {
        "id": "1456460669",
        "title": title,
        "productType": "game",
        "storeLink": store_url,
        "coverHorizontal": cover_url,
        "price": price,
    }


class GogCatalogParsingTests(unittest.TestCase):
    def test_title_normalization_only_trims_and_collapses_whitespace(self) -> None:
        self.assertEqual(normalize_title("  BALDUR'S   GATE 3 "), "baldur's gate 3")

    def test_exact_normalized_title_returns_brl_offer(self) -> None:
        offer = parse_catalog_results(
            {"products": [gog_product()]},
            "  baldur's   gate 3 ",
        )

        self.assertIsNotNone(offer)
        assert offer is not None
        self.assertEqual(offer.product_id, "1456460669")
        self.assertEqual(offer.title, "Baldur's Gate 3")
        self.assertEqual(offer.status, "paid")
        self.assertEqual(offer.final_price_minor, 19999)
        self.assertEqual(
            offer.store_url,
            "https://www.gog.com/en/game/baldurs_gate_iii",
        )
        self.assertEqual(
            offer.cover_url,
            "https://images.gog-statics.com/example.png",
        )

    def test_missing_and_ambiguous_exact_matches_return_no_offer(self) -> None:
        self.assertIsNone(parse_catalog_results({"products": []}, "Baldur's Gate 3"))
        self.assertIsNone(
            parse_catalog_results(
                {"products": [gog_product(), gog_product()]},
                "Baldur's Gate 3",
            )
        )

    def test_non_exact_and_non_game_results_are_not_matches(self) -> None:
        self.assertIsNone(
            parse_catalog_results(
                {
                    "products": [
                        gog_product(title="Baldur's Gate 3 Deluxe Edition"),
                        {**gog_product(), "productType": "dlc"},
                    ]
                },
                "Baldur's Gate 3",
            )
        )

    def test_free_game_is_zero_brl(self) -> None:
        offer = parse_catalog_results(
            {"products": [gog_product(amount="0.00")]},
            "Baldur's Gate 3",
        )

        self.assertIsNotNone(offer)
        assert offer is not None
        self.assertEqual(offer.status, "free")
        self.assertEqual(offer.final_price_minor, 0)

    def test_missing_or_non_brl_price_is_unavailable(self) -> None:
        cases = [
            gog_product(amount=None, currency=None),
            gog_product(currency="USD"),
            gog_product(amount="not-a-price"),
            gog_product(amount="1.001"),
        ]
        for product in cases:
            with self.subTest(product=product):
                offer = parse_catalog_results(
                    {"products": [product]},
                    "Baldur's Gate 3",
                )
                self.assertIsNotNone(offer)
                assert offer is not None
                self.assertEqual(offer.status, "unavailable")
                self.assertIsNone(offer.final_price_minor)

    def test_unsafe_store_and_cover_urls_are_rejected(self) -> None:
        cases = [
            gog_product(store_url="http://www.gog.com/en/game/game"),
            gog_product(store_url="https://www.gog.com.attacker.invalid/game/game"),
            gog_product(cover_url="https://images.gog-statics.com.attacker.invalid/cover.png"),
        ]
        for product in cases:
            with self.subTest(product=product):
                with self.assertRaises(GogServiceError):
                    parse_catalog_results(
                        {"products": [product]},
                        "Baldur's Gate 3",
                    )

    def test_malformed_catalog_response_raises(self) -> None:
        with self.assertRaises(GogServiceError):
            parse_catalog_results({"products": "invalid"}, "Baldur's Gate 3")
        with self.assertRaises(GogServiceError):
            parse_catalog_results({"products": [None]}, "Baldur's Gate 3")


class GogHttpTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_uses_public_brazil_catalog_parameters(self) -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            self.assertEqual(str(request.url.copy_with(query=None)), GOG_CATALOG_URL)
            self.assertEqual(request.url.params["limit"], "50")
            self.assertEqual(request.url.params["order"], "desc:trending")
            self.assertEqual(request.url.params["productType"], "in:game")
            self.assertEqual(request.url.params["query"], "Baldur's Gate 3")
            self.assertEqual(request.url.params["locale"], "en-US")
            self.assertEqual(request.url.params["currencyCode"], "BRL")
            self.assertEqual(request.url.params["countryCode"], "BR")
            return httpx.Response(
                200,
                json={"products": [gog_product()]},
                request=request,
            )

        offer = await search_gog_offer(
            "  Baldur's Gate 3  ",
            transport=httpx.MockTransport(respond),
        )
        self.assertIsNotNone(offer)

    async def test_http_status_invalid_json_and_timeout_raise_recoverable_errors(self) -> None:
        transports = [
            (
                httpx.MockTransport(
                    lambda request: httpx.Response(503, request=request)
                ),
                "não está disponível",
            ),
            (
                httpx.MockTransport(
                    lambda request: httpx.Response(
                        200,
                        content=b"not-json",
                        request=request,
                    )
                ),
                "resposta inválida",
            ),
            (
                httpx.MockTransport(
                    lambda request: (_ for _ in ()).throw(
                        httpx.ReadTimeout("timeout", request=request)
                    )
                ),
                "demorou demais",
            ),
        ]
        for transport, message in transports:
            with self.subTest(message=message):
                with self.assertRaisesRegex(GogServiceError, message):
                    await search_gog_offer("Baldur's Gate 3", transport=transport)


if __name__ == "__main__":
    unittest.main()
