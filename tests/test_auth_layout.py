import unittest

from Projeto.Projeto import (
    GLOBAL_CSS,
    auth_brand,
    landing_page,
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

    def test_brand_routes_to_home_or_catalog_based_on_session(self) -> None:
        for component in (auth_brand(), login_card(), register_card()):
            with self.subTest(component=type(component).__name__):
                rendered = repr(component)
                self.assertIn("/catalogo", rendered)
                self.assertIn("/", rendered)
                self.assertIn("is_authenticated", rendered)

    def test_registration_requires_name(self) -> None:
        registration = repr(register_card())
        self.assertIn("Nome", registration)
        self.assertIn("required", registration)

    def test_registration_link_and_submit_labels_are_distinct(self) -> None:
        login = repr(login_card())
        registration = repr(register_card())

        self.assertIn("Cadastrar", login)
        self.assertNotIn("Cadastrar-se", login)
        self.assertIn("Cadastrar-se", registration)

    def test_password_visibility_control_on_both_forms_and_rule_on_registration_only(
        self,
    ) -> None:
        for card_factory in (login_card, register_card):
            with self.subTest(card=card_factory.__name__):
                component = repr(card_factory())
                self.assertIn("password_visible", component)
                self.assertIn("Mostrar senha", component)
                self.assertIn("Ocultar senha", component)
                self.assertIn("aria-label", component)

        login = repr(login_card())
        registration = repr(register_card())
        self.assertNotIn("Mínimo de 8 caracteres", login)
        self.assertNotIn("login-password-rule", login)
        self.assertIn("8 caracteres e ao menos uma letra.", registration)
        self.assertIn("register-password-rule", registration)
        self.assertIn(":focus-visible", GLOBAL_CSS)

    def test_landing_page_has_required_content_and_routes(self) -> None:
        page = repr(landing_page())

        for text in (
            "Compara Keys",
            "Quem somos",
            "Objetivo do site e por que usar",
            "Entrar",
            "Cadastrar",
            "/entrar",
            "/cadastro",
            "/catalogo",
        ):
            with self.subTest(text=text):
                self.assertIn(text, page)

        self.assertNotIn("Comparar Preços", page)
        self.assertNotIn("Nome do jogo", page)

    def test_landing_topbar_has_conditional_navigation_without_duplicate_ctas(
        self,
    ) -> None:
        landing = landing_page()
        page = repr(landing)
        stack = landing.children[1]
        brand = stack.children[0].children[0]

        for text in (
            "LucideGamepad2",
            "landing-topbar",
            "auth_state.is_authenticated",
            "Entrar",
            "Cadastrar",
            "Ir para o cat",
            "Sair",
            "/entrar",
            "/cadastro",
            "/catalogo",
        ):
            with self.subTest(text=text):
                self.assertIn(text, page)

        self.assertEqual(
            brand.custom_attrs.get("aria-label"),
            "ComparaKeys — início",
        )
        self.assertEqual(brand.children[0].to._var_value, "/")
        self.assertIn("landing-topbar", repr(stack.children[0]))
        self.assertIn("landing-hero", repr(stack.children[1]))
        self.assertNotIn("Criar conta", page)
        self.assertNotIn("landing-actions", page)
        self.assertNotIn("Comparar Preços", page)
        self.assertNotIn("landing-search", page)
        self.assertNotIn("on_scroll", page)
        self.assertIn("position: sticky", GLOBAL_CSS)
        self.assertIn("top: 0", GLOBAL_CSS)
        self.assertIn("height: 64px", GLOBAL_CSS)
        self.assertIn("z-index: 10", GLOBAL_CSS)
        self.assertIn("border-bottom: 1px solid var(--ck-purple-border)", GLOBAL_CSS)
        self.assertIn("background-color: var(--ck-black)", GLOBAL_CSS)
        self.assertIn("@supports (backdrop-filter: blur(1px))", GLOBAL_CSS)
        self.assertIn("background-color: rgba(5, 4, 7, 0.9)", GLOBAL_CSS)
        self.assertIn("backdrop-filter: blur(12px)", GLOBAL_CSS)
        self.assertIn("min-height: calc(100svh - 64px)", GLOBAL_CSS)
        self.assertIn("overflow-x: clip", GLOBAL_CSS)
        self.assertIn("white-space: nowrap", GLOBAL_CSS)

    def test_landing_css_has_diagonal_mobile_layout_and_reduced_motion(self) -> None:
        for css in (
            ".landing-hero",
            "min-height: calc(100svh - 64px)",
            "clip-path: polygon(18% 0, 100% 0, 100% 100%, 0 100%)",
            "@media (max-width: 700px)",
            "grid-template-columns: minmax(0, 1fr)",
            ".landing-info-card",
            "prefers-reduced-motion: reduce",
            "--ck-purple-border",
        ):
            with self.subTest(css=css):
                self.assertIn(css, GLOBAL_CSS)


if __name__ == "__main__":
    unittest.main()
