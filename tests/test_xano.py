import json
import unittest
from unittest.mock import patch

import httpx

from Projeto import xano

_REAL_ASYNC_CLIENT = httpx.AsyncClient


class XanoClientTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.environment = patch.dict(
            "os.environ",
            {"XANO_API_URL": "https://instance.example/api:auth"},
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def _client_patch(self, handler):
        transport = httpx.MockTransport(handler)
        return patch(
            "Projeto.xano.httpx.AsyncClient",
            side_effect=lambda **kwargs: _REAL_ASYNC_CLIENT(
                transport=transport,
                **kwargs,
            ),
        )

    async def test_signup_sends_normalized_email_and_returns_token(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={"authToken": "token-value", "user_id": 41},
            )

        with self._client_patch(handler):
            session = await xano.signup(
                "  Ada Lovelace ",
                " Ada@Example.com ",
                "correct horse battery staple",
            )

        self.assertEqual(session, xano.AuthSession("token-value", 41))
        request = requests[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(str(request.url), "https://instance.example/api:auth/auth/signup")
        self.assertEqual(
            json.loads(request.content),
            {
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "password": "correct horse battery staple",
            },
        )

    async def test_login_sends_expected_payload(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={"authToken": "login-token", "user_id": 9},
            )

        with self._client_patch(handler):
            session = await xano.login("User@Example.com", "password")

        self.assertEqual(session.auth_token, "login-token")
        self.assertEqual(session.user_id, 9)
        self.assertEqual(
            json.loads(requests[0].content),
            {"email": "user@example.com", "password": "password"},
        )

    async def test_me_sends_token_in_authorization_header(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={
                    "id": 9,
                    "created_at": 1762000000000,
                    "name": "Ada Lovelace",
                    "email": "ada@example.com",
                    "role": "user",
                },
            )

        with self._client_patch(handler):
            user = await xano.me("session-token")

        self.assertEqual(user.id, 9)
        self.assertEqual(requests[0].method, "GET")
        self.assertEqual(
            requests[0].headers["Authorization"],
            "Bearer session-token",
        )
        self.assertIsNone(requests[0].content or None)

    async def test_known_endpoint_errors_are_mapped(self) -> None:
        duplicate_body = {
            "code": "ERROR_CODE_ACCESS_DENIED",
            "message": "An account with this email already exists.",
            "payload": {},
        }
        with self._client_patch(
            lambda request: httpx.Response(403, json=duplicate_body)
        ):
            with self.assertRaises(xano.DuplicateEmailError):
                await xano.signup("Ada", "ada@example.com", "valid password")

        invalid_credentials = {
            "code": "ERROR_CODE_ACCESS_DENIED",
            "message": "Invalid Credentials.",
            "payload": {},
        }
        with self._client_patch(
            lambda request: httpx.Response(403, json=invalid_credentials)
        ):
            with self.assertRaises(xano.InvalidCredentialsError):
                await xano.login("ada@example.com", "wrong password")

        invalid_email = {
            "code": "ERROR_CODE_INPUT_ERROR",
            "message": "Invalid input",
            "payload": {"param": "email"},
        }
        with self._client_patch(
            lambda request: httpx.Response(400, json=invalid_email)
        ):
            with self.assertRaises(xano.AuthInputError):
                await xano.signup("Ada", "ada@example.com", "valid password")

        weak_password = {
            "code": "ERROR_CODE_INPUT_ERROR",
            "message": "Invalid input",
            "payload": {"param": "password"},
        }
        with self._client_patch(
            lambda request: httpx.Response(400, json=weak_password)
        ):
            with self.assertRaises(xano.AuthInputError) as error:
                await xano.signup("Ada", "ada@example.com", "valid password")
            self.assertEqual(str(error.exception), xano.WEAK_PASSWORD_MESSAGE)

    async def test_me_rejects_unauthorized_token(self) -> None:
        with self._client_patch(
            lambda request: httpx.Response(401, text="Invalid token.")
        ):
            with self.assertRaises(xano.InvalidTokenError):
                await xano.me("invalid-token")

    async def test_network_and_timeout_errors_retry_once(self) -> None:
        for error_type in (httpx.ConnectError, httpx.ReadTimeout):
            with self.subTest(error_type=error_type.__name__):
                requests: list[httpx.Request] = []

                def handler(request: httpx.Request) -> httpx.Response:
                    requests.append(request)
                    if len(requests) == 1:
                        raise error_type("temporary failure", request=request)
                    return httpx.Response(
                        200,
                        json={"authToken": "login-token", "user_id": 9},
                    )

                with self._client_patch(handler):
                    session = await xano.login("ada@example.com", "valid password")

                self.assertEqual(session.auth_token, "login-token")
                self.assertEqual(len(requests), 2)

    async def test_client_does_not_retry_a_four_hundred_response(self) -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                400,
                json={
                    "code": "ERROR_CODE_INPUT_ERROR",
                    "message": "Invalid input",
                    "payload": {"param": "password"},
                },
            )

        with self._client_patch(handler):
            with self.assertRaises(xano.AuthInputError):
                await xano.signup("Ada", "ada@example.com", "valid password")

        self.assertEqual(len(requests), 1)

    async def test_network_server_and_invalid_success_responses_fail_clearly(self) -> None:
        def connection_error(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

        with self._client_patch(connection_error):
            with self.assertRaises(xano.XanoUnavailableError):
                await xano.login("ada@example.com", "valid password")

        def timeout_error(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("request timed out", request=request)

        with self._client_patch(timeout_error):
            with self.assertRaises(xano.XanoUnavailableError):
                await xano.login("ada@example.com", "valid password")

        with self._client_patch(
            lambda request: httpx.Response(503, json={"message": "unavailable"})
        ):
            with self.assertRaises(xano.XanoApiError) as error:
                await xano.login("ada@example.com", "valid password")
        self.assertEqual(error.exception.status_code, 503)
        self.assertEqual(error.exception.message, "unavailable")

        with self._client_patch(
            lambda request: httpx.Response(
                200,
                content=b"not-json",
                headers={"content-type": "application/json"},
            )
        ):
            with self.assertRaises(xano.XanoUnavailableError):
                await xano.login("ada@example.com", "valid password")

        with self._client_patch(
            lambda request: httpx.Response(200, json={"user_id": 1})
        ):
            with self.assertRaises(xano.XanoUnavailableError):
                await xano.login("ada@example.com", "valid password")

    async def test_missing_base_url_and_invalid_inputs_are_rejected(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(xano.XanoUnavailableError):
                await xano.login("ada@example.com", "password")

        with self.assertRaisesRegex(xano.AuthInputError, "Informe seu nome"):
            await xano.signup(" ", "ada@example.com", "valid password")
        with self.assertRaisesRegex(xano.AuthInputError, "e-mail válido"):
            await xano.signup("Ada", "invalid-email", "valid password")
        with self.assertRaisesRegex(xano.AuthInputError, "8 e 128"):
            await xano.signup("Ada", "ada@example.com", "short")
        with self.assertRaises(xano.AuthInputError) as error:
            xano.validate_password("12345678")
        self.assertEqual(str(error.exception), xano.WEAK_PASSWORD_MESSAGE)


if __name__ == "__main__":
    unittest.main()
