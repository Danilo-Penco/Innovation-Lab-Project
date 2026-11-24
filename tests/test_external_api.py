import unittest

import httpx

from Projeto import external_api


class PublicApiRequestTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        external_api._RATE_LIMIT_UNTIL.clear()

    async def asyncTearDown(self) -> None:
        external_api._RATE_LIMIT_UNTIL.clear()

    async def test_network_failure_retries_once_with_bounded_timeout(self) -> None:
        calls = 0

        def respond(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            self.assertEqual(request.extensions["timeout"]["connect"], 10.0)
            if calls == 1:
                raise httpx.ConnectError("network failure", request=request)
            return httpx.Response(200, json={"ok": True}, request=request)

        payload = await external_api.get_json(
            "https://api.example.test/data",
            None,
            timeout_seconds=10.0,
            transport=httpx.MockTransport(respond),
        )

        self.assertEqual(payload, {"ok": True})
        self.assertEqual(calls, 2)

    async def test_http_failure_is_not_retried(self) -> None:
        calls = 0

        def respond(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return httpx.Response(503, request=request)

        with self.assertRaises(external_api.PublicApiRequestError) as error:
            await external_api.get_json(
                "https://api.example.test/data",
                None,
                timeout_seconds=10.0,
                transport=httpx.MockTransport(respond),
            )

        self.assertEqual(error.exception.kind, "http")
        self.assertEqual(calls, 1)

    async def test_timeout_is_retried_once(self) -> None:
        calls = 0

        def respond(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise httpx.ReadTimeout("timeout", request=request)
            return httpx.Response(200, json={"ok": True}, request=request)

        payload = await external_api.get_json(
            "https://timeout.example.test/data",
            None,
            timeout_seconds=10.0,
            transport=httpx.MockTransport(respond),
        )

        self.assertEqual(payload, {"ok": True})
        self.assertEqual(calls, 2)

    async def test_429_honors_retry_after_without_an_automatic_retry(self) -> None:
        calls = 0

        def respond(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return httpx.Response(
                429,
                headers={"Retry-After": "30"},
                request=request,
            )

        transport = httpx.MockTransport(respond)
        with self.assertRaises(external_api.PublicApiRequestError) as first_error:
            await external_api.get_json(
                "https://api.example.test/data",
                None,
                timeout_seconds=10.0,
                transport=transport,
            )
        self.assertEqual(first_error.exception.kind, "rate_limited")

        with self.assertRaises(external_api.PublicApiRequestError) as next_error:
            await external_api.get_json(
                "https://api.example.test/data",
                None,
                timeout_seconds=10.0,
                transport=transport,
            )
        self.assertEqual(next_error.exception.kind, "rate_limited")
        self.assertEqual(calls, 1)

    async def test_invalid_json_is_reported_without_retry(self) -> None:
        calls = 0

        def respond(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return httpx.Response(200, content=b"not-json", request=request)

        with self.assertRaises(external_api.PublicApiRequestError) as error:
            await external_api.get_json(
                "https://api.example.test/data",
                None,
                timeout_seconds=10.0,
                transport=httpx.MockTransport(respond),
            )

        self.assertEqual(error.exception.kind, "invalid_json")
        self.assertEqual(calls, 1)


if __name__ == "__main__":
    unittest.main()
