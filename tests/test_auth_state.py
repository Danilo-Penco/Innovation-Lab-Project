import unittest
from types import SimpleNamespace
from unittest.mock import patch

from Projeto.Projeto import AuthState


class AuthStateTests(unittest.TestCase):
    def test_authentication_indicator_follows_session_identity(self) -> None:
        is_authenticated = AuthState.is_authenticated.fget

        self.assertFalse(is_authenticated(SimpleNamespace(_user_id=None)))
        self.assertTrue(is_authenticated(SimpleNamespace(_user_id=42)))
        self.assertFalse(is_authenticated(SimpleNamespace(_user_id=True)))

    def test_logout_clears_session_state_and_redirects(self) -> None:
        state = SimpleNamespace(
            _user_id=42,
            _catalog_authorized=True,
            is_splash_visible=True,
            is_submitting=True,
            email="user@example.invalid",
            password="sensitive",
            auth_error="old error",
        )

        redirect = AuthState.logout.fn(state)

        self.assertIsNotNone(redirect)
        self.assertIsNone(state._user_id)
        self.assertFalse(state._catalog_authorized)
        self.assertFalse(state.is_splash_visible)
        self.assertFalse(state.is_submitting)
        self.assertEqual(state.email, "")
        self.assertEqual(state.password, "")
        self.assertEqual(state.auth_error, "")

    def test_catalog_guard_redirects_without_session_and_allows_valid_session(self) -> None:
        unauthenticated = SimpleNamespace(
            _user_id=None,
            _catalog_authorized=False,
            is_splash_visible=False,
        )
        with patch("Projeto.Projeto.account_exists", return_value=False):
            redirect = AuthState.guard_catalog.fn(unauthenticated)

        self.assertIsNotNone(redirect)
        self.assertIsNone(unauthenticated._user_id)
        self.assertFalse(unauthenticated._catalog_authorized)

        authenticated = SimpleNamespace(
            _user_id=42,
            _catalog_authorized=False,
            is_splash_visible=True,
        )
        with patch("Projeto.Projeto.account_exists", return_value=True):
            redirect = AuthState.guard_catalog.fn(authenticated)

        self.assertIsNone(redirect)
        self.assertTrue(authenticated._catalog_authorized)
        self.assertFalse(authenticated.is_splash_visible)


if __name__ == "__main__":
    unittest.main()
