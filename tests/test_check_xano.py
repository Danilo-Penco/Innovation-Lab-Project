import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import httpx

from scripts import check_xano

TEST_EMAIL = "test-xano@example.invalid"
TEST_PASSWORD = "test-only-password"
TEST_TOKEN = "test-only-token"


class FakeClient:
    def __init__(
        self,
        *,
        legacy_statuses=None,
        login_status=200,
        network_error=None,
        signup_error_field="name",
        unauthenticated_me_status=401,
    ):
        self.legacy_statuses = legacy_statuses or {}
        self.login_status = login_status
        self.network_error = network_error
        self.signup_error_field = signup_error_field
        self.unauthenticated_me_status = unauthenticated_me_status
        self.requests = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def request(self, method, url, *, json=None, headers=None):
        path = url.split("/api:auth", 1)[-1]
        self.requests.append((method, path, json, headers))
        if self.network_error and path == "/auth/login":
            raise self.network_error
        if path == "/auth/login":
            return httpx.Response(
                self.login_status,
                json={"authToken": TEST_TOKEN, "user_id": 17},
                request=httpx.Request(method, url),
            )
        if path == "/auth/me" and not headers:
            return httpx.Response(
                self.unauthenticated_me_status,
                request=httpx.Request(method, url),
            )
        if path == "/auth/me":
            return httpx.Response(
                200,
                json={
                    "id": 17,
                    "created_at": 1762000000000,
                    "name": "Test",
                    "email": TEST_EMAIL,
                    "role": "user",
                },
                request=httpx.Request(method, url),
            )
        if path == "/auth/signup":
            body = {"code": "ERROR_CODE_INPUT_ERROR", "message": "Invalid input"}
            if self.signup_error_field:
                body["payload"] = {"param": self.signup_error_field}
            return httpx.Response(
                400,
                json=body,
                request=httpx.Request(method, url),
            )
        status = self.legacy_statuses.get((method, path), 404)
        return httpx.Response(status, request=httpx.Request(method, url))


class XanoCheckerTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(
            os.environ,
            {
                "XANO_API_URL": "https://xano.test/api:auth",
                "XANO_TEST_EMAIL": TEST_EMAIL,
                "XANO_TEST_PASSWORD": TEST_PASSWORD,
            },
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def run_checker(self, client):
        output = io.StringIO()
        with patch("scripts.check_xano.httpx.Client", return_value=client):
            with redirect_stdout(output):
                result = check_xano.run_check()
        return result, output.getvalue()

    def test_checker_passes_contract_without_printing_secrets_or_sending_them_to_legacy_routes(self):
        client = FakeClient()

        result, output = self.run_checker(client)

        self.assertEqual(result, 0)
        self.assertIn("PASS POST /auth/login", output)
        self.assertIn("PASS GET /auth/me sem token", output)
        self.assertIn("PASS POST /auth/signup sem name", output)
        self.assertIn("PASS POST /message/send_welcome_email", output)
        self.assertNotIn(TEST_EMAIL, output)
        self.assertNotIn(TEST_PASSWORD, output)
        self.assertNotIn(TEST_TOKEN, output)

        legacy_requests = [
            request
            for request in client.requests
            if request[1].startswith(("/message/", "/reset/"))
        ]
        self.assertEqual(len(legacy_requests), 4)
        self.assertTrue(
            all(
                request[2] == ({} if request[0] == "POST" else None)
                and not request[3]
                for request in legacy_requests
            )
        )
        signup_request = next(request for request in client.requests if request[1] == "/auth/signup")
        self.assertEqual(signup_request[2], {})
        authenticated_me = next(
            request
            for request in client.requests
            if request[1] == "/auth/me" and request[3]
        )
        self.assertEqual(
            authenticated_me[3],
            {"Authorization": f"Bearer {TEST_TOKEN}"},
        )

    def test_legacy_route_401_is_failure_not_absence(self):
        client = FakeClient(
            legacy_statuses={
                ("POST", "/message/send_welcome_email"): 401,
            },
        )

        result, output = self.run_checker(client)

        self.assertEqual(result, 1)
        self.assertIn(
            "FAIL POST /message/send_welcome_email: rota existente (HTTP 401)",
            output,
        )

    def test_generic_signup_rejection_is_skipped_when_name_is_not_identified(self):
        client = FakeClient(signup_error_field=None)

        result, output = self.run_checker(client)

        self.assertEqual(result, 2)
        self.assertIn(
            "SKIP POST /auth/signup sem name: HTTP 400 sem identificação do campo name",
            output,
        )

    def test_unexpected_legacy_status_is_skipped(self):
        client = FakeClient(
            legacy_statuses={
                ("POST", "/reset/magic-link-login"): 500,
            },
        )

        result, output = self.run_checker(client)

        self.assertEqual(result, 2)
        self.assertIn(
            "SKIP POST /reset/magic-link-login: status inesperado (HTTP 500)",
            output,
        )

    def test_unexpected_auth_me_status_is_skipped(self):
        client = FakeClient(unauthenticated_me_status=503)

        result, output = self.run_checker(client)

        self.assertEqual(result, 2)
        self.assertIn(
            "SKIP GET /auth/me sem token: status inesperado (HTTP 503)",
            output,
        )

    def test_network_failure_is_skip_without_request_details(self):
        client = FakeClient(network_error=httpx.ConnectError("private connection detail"))

        result, output = self.run_checker(client)

        self.assertEqual(result, 2)
        self.assertIn("SKIP POST /auth/login: falha de rede (ConnectError)", output)
        self.assertNotIn("private connection detail", output)
        self.assertNotIn(TEST_PASSWORD, output)
        self.assertNotIn(TEST_TOKEN, output)


if __name__ == "__main__":
    unittest.main()
