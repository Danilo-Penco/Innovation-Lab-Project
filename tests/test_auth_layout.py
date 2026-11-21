import unittest

from Projeto.Projeto import (
    GLOBAL_CSS,
    auth_brand,
    login_card,
    login_page,
    register_card,
    register_page,
)


class AuthenticationLayoutTests(unittest.TestCase):
    def test_login_and_registration_cards_use_compact_responsive_padding(self) -> None:
        for card_factory in (login_card, register_card):
            with self.subTest(card=card_factory.__name__):
                self.assertIn(
                    "clamp(1rem, 3vh, 1.5rem)",
                    repr(card_factory()),
                )

    def test_auth_pages_center_forms_and_reduce_outer_spacing(self) -> None:
        for page_factory in (login_page, register_page):
            with self.subTest(page=page_factory.__name__):
                page = repr(page_factory())
                self.assertIn("minHeight", page)
                self.assertIn("0.75rem", page)

        self.assertIn("@media (max-height: 720px)", GLOBAL_CSS)

    def test_login_brand_is_static_and_registration_brand_links_to_catalog(self) -> None:
        self.assertNotIn("/catalogo", repr(login_card()))
        self.assertNotIn("/catalogo", repr(auth_brand()))
        self.assertIn("/catalogo", repr(auth_brand(clickable=True)))
        self.assertIn("/catalogo", repr(register_card()))

    def test_registration_requires_name(self) -> None:
        registration = repr(register_card())
        self.assertIn("Nome", registration)
        self.assertIn("required", registration)

    def test_password_rule_and_accessible_visibility_control_on_both_forms(self) -> None:
        for card_factory, hint_id in (
            (login_card, "login-password-rule"),
            (register_card, "register-password-rule"),
        ):
            with self.subTest(card=card_factory.__name__):
                component = repr(card_factory())
                self.assertIn("password_visible", component)
                self.assertIn("Mostrar senha", component)
                self.assertIn("Ocultar senha", component)
                self.assertIn("aria-label", component)
                self.assertIn(hint_id, component)
                self.assertIn("caracteres e ao menos uma letra", component)

        self.assertIn(":focus-visible", GLOBAL_CSS)


if __name__ == "__main__":
    unittest.main()
