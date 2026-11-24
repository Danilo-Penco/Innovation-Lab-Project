import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from Projeto.Projeto import AuthState, SESSION_EXPIRED_MESSAGE
from Projeto.xano import (
    AUTH_SERVICE_UNAVAILABLE_MESSAGE,
    AuthInputError,
    AuthSession,
    AuthenticatedUser,
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidTokenError,
    XanoApiError,
    XanoUnavailableError,
)


def build_state(**overrides):
    values = {
        "name": "",
        "email": "user@example.com",
        "password": "valid password",
        "password_visible": False,
        "auth_error": "",
        "is_splash_visible": False,
        "is_submitting": False,
        "_auth_token": None,
        "_catalog_authorized": False,
        "router": SimpleNamespace(
            url=SimpleNamespace(query_parameters={}),
        ),
    }
    values.update(overrides)
    state = SimpleNamespace(**values)
    state._start_authenticated_transition = (
        lambda session: AuthState._start_authenticated_transition(state, session)
    )
    state._api_error_message = (
        lambda error: AuthState._api_error_message(state, error)
    )
    return state


class AuthStateTests(unittest.IsolatedAsyncioTestCase):
    def test_authentication_indicator_follows_session_token(self) -> None:
        is_authenticated = AuthState.is_authenticated.fget

        self.assertFalse(is_authenticated(SimpleNamespace(_auth_token=None)))
        self.assertTrue(is_authenticated(SimpleNamespace(_auth_token="token")))
        self.assertFalse(is_authenticated(SimpleNamespace(_auth_token="")))

    def test_logout_clears_session_and_form_state(self) -> None:
        state = build_state(
            name="Ada Lovelace",
            _auth_token="token",
            _catalog_authorized=True,
            is_splash_visible=True,
            is_submitting=True,
            auth_error="old error",
            password_visible=True,
        )

        redirect = AuthState.logout.fn(state)

        self.assertIsNotNone(redirect)
        self.assertIn("/entrar", repr(redirect))
        self.assertIsNone(state._auth_token)
        self.assertFalse(state._catalog_authorized)
        self.assertFalse(state.is_splash_visible)
        self.assertFalse(state.is_submitting)
        self.assertEqual(state.name, "")
        self.assertEqual(state.email, "")
        self.assertEqual(state.password, "")
        self.assertFalse(state.password_visible)
        self.assertEqual(state.auth_error, "")

    def test_password_visibility_toggle_is_reversible_and_reset_on_navigation(self) -> None:
        state = build_state()
        self.assertFalse(state.password_visible)

        AuthState.toggle_password_visibility.fn(state)
        self.assertTrue(state.password_visible)
        AuthState.toggle_password_visibility.fn(state)
        self.assertFalse(state.password_visible)

        state.password_visible = True
        AuthState.open_register.fn(state)
        self.assertFalse(state.password_visible)

    def test_open_login_uses_entrar_route(self) -> None:
        state = build_state(name="Ada Lovelace", password="secret")

        redirect = AuthState.open_login.fn(state)

        self.assertIn("/entrar", repr(redirect))
        self.assertEqual(state.name, "")
        self.assertEqual(state.password, "")

    async def test_login_success_stores_token_only_after_xano_success(self) -> None:
        state = build_state()
        with patch(
            "Projeto.Projeto.xano.login",
            new=AsyncMock(return_value=AuthSession("valid-token", 42)),
        ):
            transition = await AuthState.login.fn(state)

        self.assertIsNotNone(transition)
        self.assertEqual(state._auth_token, "valid-token")
        self.assertTrue(state.is_splash_visible)
        self.assertFalse(state._catalog_authorized)
        self.assertEqual(state.password, "")
        self.assertFalse(state.password_visible)
        self.assertFalse(state.is_submitting)

    async def test_login_requires_fields_and_rejects_password_over_128_characters(self) -> None:
        cases = (
            ({"email": "  "}, "Informe seu e-mail."),
            ({"password": ""}, "Informe a senha."),
            (
                {"password": "x" * 129},
                "A senha deve ter no máximo 128 caracteres.",
            ),
        )
        for overrides, expected_message in cases:
            with self.subTest(expected_message=expected_message):
                state = build_state(password_visible=True, **overrides)
                with patch(
                    "Projeto.Projeto.xano.login",
                    new=AsyncMock(),
                ) as login:
                    await AuthState.login.fn(state)

                login.assert_not_awaited()
                self.assertEqual(state.auth_error, expected_message)
                self.assertFalse(state.password_visible)
                self.assertFalse(state.is_submitting)

    async def test_login_sends_short_password_without_strength_validation(self) -> None:
        state = build_state(password="x")
        with patch(
            "Projeto.Projeto.xano.login",
            new=AsyncMock(return_value=AuthSession("valid-token", 42)),
        ) as login:
            await AuthState.login.fn(state)

        login.assert_awaited_once_with(state.email, "x")

    async def test_login_errors_keep_session_clear_and_show_expected_message(self) -> None:
        cases = (
            (InvalidCredentialsError("private detail"), "E-mail ou senha inválidos."),
            (AuthInputError("Informe um e-mail válido."), "E-mail ou senha inválidos."),
            (
                XanoApiError(
                    400,
                    "ERROR_CODE_INPUT_ERROR",
                    "Rejected valid password",
                    "password",
                ),
                "E-mail ou senha inválidos.",
            ),
            (XanoApiError(500, "ERROR_CODE_UNKNOWN", "Internal detail"), "E-mail ou senha inválidos."),
            (XanoUnavailableError("network detail"), AUTH_SERVICE_UNAVAILABLE_MESSAGE),
        )
        for error, expected_message in cases:
            with self.subTest(error=type(error).__name__):
                state = build_state(_auth_token="previous-token")
                with patch(
                    "Projeto.Projeto.xano.login",
                    new=AsyncMock(side_effect=error),
                ):
                    await AuthState.login.fn(state)

                self.assertIsNone(state._auth_token)
                self.assertFalse(state.is_splash_visible)
                self.assertFalse(state.is_submitting)
                self.assertEqual(state.password, "")
                self.assertFalse(state.password_visible)
                self.assertEqual(state.auth_error, expected_message)

    async def test_registration_requires_name_before_calling_xano(self) -> None:
        state = build_state()
        with patch("Projeto.xano._request", new=AsyncMock()) as request:
            await AuthState.register.fn(state)

        request.assert_not_awaited()
        self.assertEqual(state.auth_error, "Informe seu nome.")
        self.assertIsNone(state._auth_token)
        self.assertEqual(state.password, "")
        self.assertFalse(state.password_visible)

    def test_prepare_form_shows_expired_session_notice(self) -> None:
        state = build_state()
        state.router.url.query_parameters = {"session": "expired"}

        AuthState.prepare_form.fn(state)

        self.assertEqual(state.auth_error, SESSION_EXPIRED_MESSAGE)
        self.assertEqual(state.password, "")

    async def test_registration_success_stores_session_and_clears_form_secrets(self) -> None:
        state = build_state(name="Ada Lovelace")
        with patch(
            "Projeto.Projeto.xano.signup",
            new=AsyncMock(return_value=AuthSession("signup-token", 17)),
        ):
            transition = await AuthState.register.fn(state)

        self.assertIsNotNone(transition)
        self.assertEqual(state._auth_token, "signup-token")
        self.assertEqual(state.name, "")
        self.assertEqual(state.password, "")
        self.assertFalse(state.password_visible)
        self.assertTrue(state.is_splash_visible)

    async def test_registration_maps_duplicate_and_connection_errors(self) -> None:
        cases = (
            (
                DuplicateEmailError("Este endereço de e-mail já está em uso."),
                "Este endereço de e-mail já está em uso.",
            ),
            (XanoUnavailableError("network detail"), AUTH_SERVICE_UNAVAILABLE_MESSAGE),
        )
        for error, expected_message in cases:
            with self.subTest(error=type(error).__name__):
                state = build_state(name="Ada Lovelace")
                with patch(
                    "Projeto.Projeto.xano.signup",
                    new=AsyncMock(side_effect=error),
                ):
                    await AuthState.register.fn(state)

                self.assertIsNone(state._auth_token)
                self.assertFalse(state.is_splash_visible)
                self.assertFalse(state.is_submitting)
                self.assertEqual(state.password, "")
                self.assertFalse(state.password_visible)
                self.assertEqual(state.auth_error, expected_message)

    async def test_catalog_guard_redirects_without_token_or_for_invalid_token(self) -> None:
        unauthenticated = build_state()
        redirect = await AuthState.guard_catalog.fn(unauthenticated)
        self.assertIsNotNone(redirect)
        self.assertIn("/entrar", repr(redirect))
        self.assertFalse(unauthenticated._catalog_authorized)

        authenticated = build_state(_auth_token="invalid-token")
        with patch(
            "Projeto.Projeto.xano.me",
            new=AsyncMock(side_effect=InvalidTokenError("invalid")),
        ):
            redirect = await AuthState.guard_catalog.fn(authenticated)

        self.assertIsNotNone(redirect)
        self.assertIn("/entrar", repr(redirect))
        self.assertIn("session=expired", repr(redirect))
        self.assertIsNone(authenticated._auth_token)
        self.assertFalse(authenticated._catalog_authorized)

    async def test_catalog_guard_validates_token_and_fails_closed_on_network_error(self) -> None:
        authenticated = build_state(
            _auth_token="valid-token",
            is_splash_visible=True,
        )
        with patch(
            "Projeto.Projeto.xano.me",
            new=AsyncMock(
                return_value=AuthenticatedUser(
                    id=42,
                    created_at=1762000000000,
                    name="Ada Lovelace",
                    email="ada@example.com",
                    role="user",
                )
            ),
        ) as me:
            redirect = await AuthState.guard_catalog.fn(authenticated)

        me.assert_awaited_once_with("valid-token")
        self.assertIsNone(redirect)
        self.assertTrue(authenticated._catalog_authorized)
        self.assertFalse(authenticated.is_splash_visible)

        unavailable = build_state(_auth_token="valid-token")
        with patch(
            "Projeto.Projeto.xano.me",
            new=AsyncMock(side_effect=XanoUnavailableError("network detail")),
        ):
            redirect = await AuthState.guard_catalog.fn(unavailable)

        self.assertIsNone(redirect)
        self.assertFalse(unavailable._catalog_authorized)
        self.assertEqual(unavailable._auth_token, "valid-token")
        self.assertEqual(
            unavailable.auth_error,
            AUTH_SERVICE_UNAVAILABLE_MESSAGE,
        )

    async def test_login_session_revalidates_auth_me_after_reload(self) -> None:
        state = build_state()
        user = AuthenticatedUser(
            id=42,
            created_at=1762000000000,
            name="Ada Lovelace",
            email="ada@example.com",
            role="user",
        )
        with (
            patch(
                "Projeto.Projeto.xano.login",
                new=AsyncMock(return_value=AuthSession("session-token", 42)),
            ),
            patch(
                "Projeto.Projeto.xano.me",
                new=AsyncMock(return_value=user),
            ) as me,
        ):
            await AuthState.login.fn(state)
            await AuthState.guard_catalog.fn(state)

            state._catalog_authorized = False
            await AuthState.guard_catalog.fn(state)

        self.assertEqual(state._auth_token, "session-token")
        self.assertTrue(state._catalog_authorized)
        self.assertEqual(me.await_count, 2)
        me.assert_awaited_with("session-token")


if __name__ == "__main__":
    unittest.main()
