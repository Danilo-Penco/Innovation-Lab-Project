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
TEST_EMAIL_2 = "test-xano-2@example.invalid"
TEST_PASSWORD_2 = "test-only-password-2"
TEST_TOKEN_2 = "test-only-token-2"


class FakeClient:
    def __init__(
        self,
        *,
        legacy_statuses=None,
        login_status=200,
        network_error=None,
        signup_error_field="name",
        unauthenticated_me_status=401,
        unauthenticated_history_statuses=None,
        history_deduplicates=True,
        history_leaks=False,
    ):
        self.legacy_statuses = legacy_statuses or {}
        self.login_status = login_status
        self.network_error = network_error
        self.signup_error_field = signup_error_field
        self.unauthenticated_me_status = unauthenticated_me_status
        self.unauthenticated_history_statuses = unauthenticated_history_statuses or {}
        self.history_deduplicates = history_deduplicates
        self.history_leaks = history_leaks
        self.histories = {17: [], 18: []}
        self.next_history_id = 500
        self.history_clock = 1762000000000
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
            if json and json.get("email") == TEST_EMAIL_2:
                return httpx.Response(
                    200,
                    json={"authToken": TEST_TOKEN_2, "user_id": 18},
                    request=httpx.Request(method, url),
                )
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
            auth_token = headers.get("Authorization", "").removeprefix("Bearer ")
            user_id = 18 if auth_token == TEST_TOKEN_2 else 17
            return httpx.Response(
                200,
                json={
                    "id": user_id,
                    "created_at": 1762000000000,
                    "name": "Test",
                    "email": TEST_EMAIL_2 if user_id == 18 else TEST_EMAIL,
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
        if path == "/history":
            if not headers:
                return httpx.Response(
                    self.unauthenticated_history_statuses.get(method, 401),
                    request=httpx.Request(method, url),
                )
            auth_token = headers.get("Authorization", "").removeprefix("Bearer ")
            user_id = 17 if auth_token == TEST_TOKEN else 18 if auth_token == TEST_TOKEN_2 else None
            if user_id is None:
                return httpx.Response(401, request=httpx.Request(method, url))
            if method == "GET":
                items = (
                    [item for values in self.histories.values() for item in values]
                    if self.history_leaks
                    else self.histories[user_id]
                )
                return httpx.Response(
                    200,
                    json=sorted(items, key=lambda item: (item["created_at"], item["id"]), reverse=True),
                    request=httpx.Request(method, url),
                )
            if method == "POST":
                payload = json or {}
                records = self.histories[user_id]
                if (
                    self.history_deduplicates
                    and records
                    and records[-1]["steam_app_id"] == payload.get("steam_app_id")
                ):
                    record = records[-1]
                    record["term"] = payload["term"]
                    record["game_name"] = payload["game_name"]
                else:
                    self.next_history_id += 1
                    record = {
                        "id": self.next_history_id,
                        "term": payload["term"],
                        "steam_app_id": payload["steam_app_id"],
                        "game_name": payload["game_name"],
                        "created_at": self.history_clock,
                    }
                    records.append(record)
                self.history_clock += 1
                record["created_at"] = self.history_clock
                return httpx.Response(
                    200,
                    json={"id": record["id"]},
                    request=httpx.Request(method, url),
                )
            if method == "DELETE":
                deleted = len(self.histories[user_id])
                self.histories[user_id].clear()
                return httpx.Response(
                    200,
                    json={"deleted": deleted},
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
                "XANO_TEST_EMAIL_2": TEST_EMAIL_2,
                "XANO_TEST_PASSWORD_2": TEST_PASSWORD_2,
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
        self.assertNotIn(TEST_EMAIL_2, output)
        self.assertNotIn(TEST_PASSWORD_2, output)
        self.assertNotIn(TEST_TOKEN_2, output)

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
        history_requests = [request for request in client.requests if request[1] == "/history"]
        self.assertTrue(history_requests)
        unauthenticated_history_requests = [
            request for request in history_requests if request[3] is None
        ]
        self.assertEqual(
            {request[0] for request in unauthenticated_history_requests},
            {"GET", "POST", "DELETE"},
        )
        authenticated_history_requests = [
            request for request in history_requests if request[3] is not None
        ]
        self.assertTrue(
            all(
                request[3]
                in (
                    {"Authorization": f"Bearer {TEST_TOKEN}"},
                    {"Authorization": f"Bearer {TEST_TOKEN_2}"},
                )
                for request in authenticated_history_requests
            )
        )
        self.assertTrue(
            all(
                set(request[2]) == {"term", "steam_app_id", "game_name"}
                for request in history_requests
                if request[0] == "POST" and request[3] is not None
            )
        )
        self.assertTrue(
            any(
                request[0] == "GET"
                and request[3] == {"Authorization": f"Bearer {TEST_TOKEN}"}
                for request in history_requests
            )
        )
        self.assertTrue(
            any(
                request[0] == "GET"
                and request[3] == {"Authorization": f"Bearer {TEST_TOKEN_2}"}
                for request in history_requests
            )
        )
        self.assertTrue(all(not request[2] or "user_id" not in request[2] for request in history_requests))
        self.assertEqual(client.histories, {17: [], 18: []})
        for method in ("POST", "GET", "DELETE"):
            self.assertIn(f"PASS {method} /history sem token: HTTP 401", output)

    def test_nonempty_test_account_is_skipped_without_mutating_history(self):
        client = FakeClient()
        client.histories[17].append(
            {
                "id": 9,
                "term": "Existing",
                "steam_app_id": 10,
                "game_name": "Existing",
                "created_at": 1762000000000,
            }
        )

        result, output = self.run_checker(client)

        self.assertEqual(result, 2)
        self.assertIn("SKIP GET /history conta 1 pré-condição", output)
        self.assertFalse(any(request[1] == "/history" and request[0] in {"POST", "DELETE"} for request in client.requests))
        self.assertEqual(len(client.histories[17]), 1)

    def test_checker_fails_when_history_is_not_isolated(self):
        client = FakeClient(history_leaks=True)

        result, output = self.run_checker(client)

        self.assertEqual(result, 1)
        self.assertIn("FAIL GET /history isolamento entre contas", output)
        self.assertEqual(client.histories, {17: [], 18: []})

    def test_checker_fails_when_consecutive_history_is_not_deduplicated(self):
        client = FakeClient(history_deduplicates=False)

        result, output = self.run_checker(client)

        self.assertEqual(result, 1)
        self.assertIn("FAIL POST /history deduplicação", output)
        self.assertEqual(client.histories, {17: [], 18: []})

    def test_checker_fails_when_unauthenticated_history_delete_is_not_401(self):
        client = FakeClient(unauthenticated_history_statuses={"DELETE": 200})

        result, output = self.run_checker(client)

        self.assertEqual(result, 1)
        self.assertIn("FAIL DELETE /history sem token", output)

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
