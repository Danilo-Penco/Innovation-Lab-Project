"""Safely check the Xano API contract against a disposable test instance."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT_SECONDS = 10.0
LEGACY_ROUTES = (
    ("POST", "message/send_welcome_email"),
    ("POST", "reset/magic-link-login"),
    ("GET", "reset/request-reset-link"),
    ("POST", "reset/update_password"),
)


def _url(base_url: str, endpoint: str) -> str:
    return f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"


def _response_object(response: httpx.Response) -> dict[str, object] | None:
    try:
        body = response.json()
    except ValueError:
        return None
    return body if isinstance(body, dict) else None


def _valid_base_url(value: str) -> bool:
    parsed = urlsplit(value)
    if not parsed.hostname or parsed.username or parsed.password:
        return False
    if parsed.query or parsed.fragment:
        return False
    if parsed.scheme == "https":
        return True
    return parsed.scheme == "http" and parsed.hostname in {
        "localhost",
        "127.0.0.1",
        "::1",
    }


def run_check() -> int:
    load_dotenv(ROOT / ".env")
    base_url = os.environ.get("XANO_API_URL", "").strip().rstrip("/")
    email = os.environ.get("XANO_TEST_EMAIL", "").strip()
    password = os.environ.get("XANO_TEST_PASSWORD", "")
    missing = [
        key
        for key, value in (
            ("XANO_API_URL", base_url),
            ("XANO_TEST_EMAIL", email),
            ("XANO_TEST_PASSWORD", password),
        )
        if not value
    ]
    if missing:
        print(f"FAIL configuração: variáveis ausentes ({', '.join(missing)})")
        return 1
    if not _valid_base_url(base_url):
        print("FAIL configuração: XANO_API_URL deve ser HTTPS e não conter credenciais")
        return 1

    counts = {"PASS": 0, "FAIL": 0, "SKIP": 0}

    def report(status: str, endpoint: str, reason: str) -> None:
        counts[status] += 1
        print(f"{status} {endpoint}: {reason}")

    def request(
        client: httpx.Client,
        method: str,
        endpoint: str,
        *,
        payload: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response | None:
        try:
            return client.request(
                method,
                _url(base_url, endpoint),
                json=payload,
                headers=headers,
            )
        except httpx.RequestError as error:
            report("SKIP", f"{method} /{endpoint}", f"falha de rede ({type(error).__name__})")
            return None

    with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
        login = request(
            client,
            "POST",
            "auth/login",
            payload={"email": email, "password": password},
        )
        auth_token: str | None = None
        if login is None:
            pass
        elif login.status_code != 200:
            status = "SKIP" if login.status_code >= 500 or login.is_redirect else "FAIL"
            report(status, "POST /auth/login", f"HTTP {login.status_code}")
        else:
            login_body = _response_object(login)
            token = login_body.get("authToken") if login_body else None
            user_id = login_body.get("user_id") if login_body else None
            if (
                isinstance(token, str)
                and token.strip()
                and isinstance(user_id, int)
                and not isinstance(user_id, bool)
            ):
                auth_token = token
                report("PASS", "POST /auth/login", "HTTP 200")
            else:
                report("FAIL", "POST /auth/login", "formato de resposta inválido")

        unauthenticated_me = request(client, "GET", "auth/me")
        if unauthenticated_me is None:
            pass
        elif unauthenticated_me.status_code == 401:
            report("PASS", "GET /auth/me sem token", "HTTP 401")
        elif unauthenticated_me.status_code >= 500 or unauthenticated_me.is_redirect:
            report(
                "SKIP",
                "GET /auth/me sem token",
                f"status inesperado (HTTP {unauthenticated_me.status_code})",
            )
        else:
            report("FAIL", "GET /auth/me sem token", f"HTTP {unauthenticated_me.status_code}")

        if auth_token is None:
            report("SKIP", "GET /auth/me com sessão de teste", "login não validado")
        else:
            authenticated_me = request(
                client,
                "GET",
                "auth/me",
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            if authenticated_me is None:
                pass
            elif authenticated_me.status_code != 200:
                status = (
                    "SKIP"
                    if authenticated_me.status_code >= 500 or authenticated_me.is_redirect
                    else "FAIL"
                )
                report(status, "GET /auth/me com sessão de teste", f"HTTP {authenticated_me.status_code}")
            else:
                user = _response_object(authenticated_me)
                if (
                    user is not None
                    and isinstance(user.get("id"), int)
                    and not isinstance(user.get("id"), bool)
                    and isinstance(user.get("created_at"), int)
                    and not isinstance(user.get("created_at"), bool)
                    and isinstance(user.get("name"), str)
                    and isinstance(user.get("email"), str)
                    and isinstance(user.get("role"), str)
                ):
                    report("PASS", "GET /auth/me com sessão de teste", "HTTP 200")
                else:
                    report("FAIL", "GET /auth/me com sessão de teste", "formato de resposta inválido")

        signup = request(client, "POST", "auth/signup", payload={})
        if signup is None:
            pass
        else:
            signup_body = _response_object(signup)
            code = signup_body.get("code") if signup_body else None
            payload = signup_body.get("payload") if signup_body else None
            field = payload.get("param") if isinstance(payload, dict) else None
            if signup.status_code == 400 and code == "ERROR_CODE_INPUT_ERROR":
                if field == "name":
                    report("PASS", "POST /auth/signup sem name", "HTTP 400, campo name")
                else:
                    report(
                        "SKIP",
                        "POST /auth/signup sem name",
                        "HTTP 400 sem identificação do campo name",
                    )
            elif signup.status_code >= 500 or signup.is_redirect:
                report(
                    "SKIP",
                    "POST /auth/signup sem name",
                    f"HTTP {signup.status_code}",
                )
            else:
                report(
                    "FAIL",
                    "POST /auth/signup sem name",
                    f"contrato não confirmado (HTTP {signup.status_code})",
                )

        for method, endpoint in LEGACY_ROUTES:
            response = request(
                client,
                method,
                endpoint,
                payload={} if method == "POST" else None,
            )
            if response is None:
                continue
            label = f"{method} /{endpoint}"
            if response.status_code == 404:
                report("PASS", label, "HTTP 404")
            elif response.status_code in {200, 400, 401, 403, 405}:
                report("FAIL", label, f"rota existente (HTTP {response.status_code})")
            else:
                report("SKIP", label, f"status inesperado (HTTP {response.status_code})")

    print(
        "Resumo: "
        f"{counts['PASS']} PASS, {counts['FAIL']} FAIL, {counts['SKIP']} SKIP"
    )
    if counts["FAIL"]:
        return 1
    return 2 if counts["SKIP"] else 0


def main() -> int:
    return run_check()


if __name__ == "__main__":
    sys.exit(main())
