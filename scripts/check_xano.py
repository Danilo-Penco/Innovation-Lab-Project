"""Safely check the Xano API contract against a disposable test instance."""

from __future__ import annotations

import os
import sys
import uuid
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


def _positive_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _history_items(response: httpx.Response) -> list[dict[str, object]] | None:
    try:
        body = response.json()
    except ValueError:
        return None
    if not isinstance(body, list):
        return None

    fields = {"id", "term", "steam_app_id", "game_name", "created_at"}
    items: list[dict[str, object]] = []
    for item in body:
        term = item.get("term") if isinstance(item, dict) else None
        game_name = item.get("game_name") if isinstance(item, dict) else None
        created_at = item.get("created_at") if isinstance(item, dict) else None
        if (
            not isinstance(item, dict)
            or set(item) != fields
            or not _positive_integer(item.get("id"))
            or not _positive_integer(item.get("steam_app_id"))
            or not isinstance(term, str)
            or not 1 <= len(term) <= 100
            or not isinstance(game_name, str)
            or not 1 <= len(game_name) <= 200
            or not isinstance(created_at, int)
            or isinstance(created_at, bool)
            or created_at < 0
        ):
            return None
        items.append(item)
    return items


def _history_id(response: httpx.Response) -> int | None:
    body = _response_object(response)
    if body is None or set(body) != {"id"}:
        return None
    identifier = body.get("id")
    return identifier if _positive_integer(identifier) else None


def _deleted_count(response: httpx.Response) -> int | None:
    body = _response_object(response)
    if body is None or set(body) != {"deleted"}:
        return None
    count = body.get("deleted")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        return None
    return count


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
    email_2 = os.environ.get("XANO_TEST_EMAIL_2", "").strip()
    password_2 = os.environ.get("XANO_TEST_PASSWORD_2", "")
    missing = [
        key
        for key, value in (
            ("XANO_API_URL", base_url),
            ("XANO_TEST_EMAIL", email),
            ("XANO_TEST_PASSWORD", password),
            ("XANO_TEST_EMAIL_2", email_2),
            ("XANO_TEST_PASSWORD_2", password_2),
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
        payload: dict[str, object] | None = None,
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
        user_id_1: int | None = None
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
                user_id_1 = user_id
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

        auth_token_2: str | None = None
        user_id_2: int | None = None
        login_2 = request(
            client,
            "POST",
            "auth/login",
            payload={"email": email_2, "password": password_2},
        )
        if login_2 is None:
            pass
        elif login_2.status_code != 200:
            status = "SKIP" if login_2.status_code >= 500 or login_2.is_redirect else "FAIL"
            report(status, "POST /auth/login conta 2", f"HTTP {login_2.status_code}")
        else:
            login_body_2 = _response_object(login_2)
            token_2 = login_body_2.get("authToken") if login_body_2 else None
            user_id_value_2 = login_body_2.get("user_id") if login_body_2 else None
            if (
                isinstance(token_2, str)
                and token_2.strip()
                and isinstance(user_id_value_2, int)
                and not isinstance(user_id_value_2, bool)
            ):
                auth_token_2 = token_2
                user_id_2 = user_id_value_2
                if user_id_1 is not None and user_id_2 != user_id_1:
                    report("PASS", "POST /auth/login conta 2", "conta distinta")
                elif user_id_1 is None:
                    report("SKIP", "POST /auth/login conta 2", "primeira conta não validada")
                else:
                    report("FAIL", "POST /auth/login conta 2", "as contas de teste devem ser distintas")
                    auth_token_2 = None
            else:
                report("FAIL", "POST /auth/login conta 2", "formato de resposta inválido")

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

        if (
            auth_token is None
            or auth_token_2 is None
            or user_id_1 is None
            or user_id_2 is None
            or user_id_1 == user_id_2
        ):
            report("SKIP", "endpoints /history", "duas contas de teste distintas não foram validadas")
        else:
            history_accounts = (
                ("conta 1", auth_token),
                ("conta 2", auth_token_2),
            )
            histories_empty = True
            for label, token in history_accounts:
                response = request(
                    client,
                    "GET",
                    "history",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if response is None:
                    histories_empty = False
                elif response.status_code != 200:
                    status = (
                        "SKIP"
                        if response.status_code >= 500 or response.is_redirect
                        else "FAIL"
                    )
                    report(status, f"GET /history {label} pré-condição", f"HTTP {response.status_code}")
                    histories_empty = False
                else:
                    items = _history_items(response)
                    if items is None:
                        report("FAIL", f"GET /history {label} pré-condição", "formato de resposta inválido")
                        histories_empty = False
                    elif items:
                        report("SKIP", f"GET /history {label} pré-condição", "a conta deve iniciar sem histórico")
                        histories_empty = False
                    else:
                        report("PASS", f"GET /history {label} pré-condição", "histórico vazio")

            if histories_empty:
                test_tag = uuid.uuid4().hex[:12]
                test_app_id = 1_000_000_000 + uuid.uuid4().int % 900_000_000
                update_payload = {
                    "term": f"checker atualizado {test_tag}",
                    "steam_app_id": test_app_id,
                    "game_name": f"Jogo checker atualizado {test_tag}",
                }
                first_payload = {
                    "term": f"checker {test_tag}",
                    "steam_app_id": test_app_id,
                    "game_name": f"Jogo checker {test_tag}",
                }

                unauthenticated_history_payload = {
                    "term": f"sem token {test_tag}",
                    "steam_app_id": test_app_id + 2,
                    "game_name": f"Jogo sem token {test_tag}",
                }
                for method, payload in (
                    ("POST", unauthenticated_history_payload),
                    ("GET", None),
                    ("DELETE", None),
                ):
                    response = request(
                        client,
                        method,
                        "history",
                        payload=payload,
                    )
                    if response is None:
                        continue
                    label = f"{method} /history sem token"
                    if response.status_code == 401:
                        report("PASS", label, "HTTP 401")
                    elif response.status_code >= 500 or response.is_redirect:
                        report("SKIP", label, f"status inesperado (HTTP {response.status_code})")
                    else:
                        report("FAIL", label, f"esperado HTTP 401, recebido HTTP {response.status_code}")

                def post_history(
                    token: str,
                    payload: dict[str, object],
                    label: str,
                    *,
                    expected_id: int | None = None,
                ) -> int | None:
                    response = request(
                        client,
                        "POST",
                        "history",
                        payload=payload,
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    if response is None:
                        return None
                    if response.status_code != 200:
                        status = (
                            "SKIP"
                            if response.status_code >= 500 or response.is_redirect
                            else "FAIL"
                        )
                        report(status, label, f"HTTP {response.status_code}")
                        return None
                    identifier = _history_id(response)
                    if identifier is None:
                        report("FAIL", label, "resposta deve conter somente um id inteiro positivo")
                    elif expected_id is not None and identifier != expected_id:
                        report("FAIL", label, "o id retornado não corresponde ao registro existente")
                    else:
                        report("PASS", label, "HTTP 200, id válido")
                    return identifier

                def get_history(token: str, label: str) -> list[dict[str, object]] | None:
                    response = request(
                        client,
                        "GET",
                        "history",
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    if response is None:
                        return None
                    if response.status_code != 200:
                        status = (
                            "SKIP"
                            if response.status_code >= 500 or response.is_redirect
                            else "FAIL"
                        )
                        report(status, label, f"HTTP {response.status_code}")
                        return None
                    items = _history_items(response)
                    if items is None:
                        report("FAIL", label, "formato de resposta inválido")
                    else:
                        report("PASS", label, "HTTP 200, formato válido")
                    return items

                def delete_history(
                    token: str,
                    label: str,
                    expected_count: int | None,
                ) -> None:
                    response = request(
                        client,
                        "DELETE",
                        "history",
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    if response is None:
                        return
                    if response.status_code != 200:
                        status = (
                            "SKIP"
                            if response.status_code >= 500 or response.is_redirect
                            else "FAIL"
                        )
                        report(status, label, f"HTTP {response.status_code}")
                        return
                    deleted = _deleted_count(response)
                    if deleted is None:
                        report("FAIL", label, 'resposta deve conter somente "deleted" inteiro não negativo')
                    elif expected_count is not None and deleted != expected_count:
                        report("FAIL", label, "quantidade removida difere dos registros criados no teste")
                    else:
                        report("PASS", label, f"HTTP 200, {deleted} removidos")

                # The accounts must be dedicated and empty; deletion below then removes only checker data.
                first_id = post_history(
                    auth_token,
                    first_payload,
                    "POST /history inserir",
                )
                if first_id is not None:
                    updated_id = post_history(
                        auth_token,
                        update_payload,
                        "POST /history deduplicação consecutiva",
                        expected_id=first_id,
                    )
                    updated_items = get_history(
                        auth_token,
                        "GET /history após deduplicação",
                    )
                    if (
                        updated_id == first_id
                        and updated_items is not None
                        and len(updated_items) == 1
                        and updated_items[0]["id"] == first_id
                        and updated_items[0]["term"] == update_payload["term"]
                        and updated_items[0]["game_name"] == update_payload["game_name"]
                    ):
                        report("PASS", "POST /history deduplicação", "registro recente atualizado sem duplicata")
                    else:
                        report("FAIL", "POST /history deduplicação", "registro repetido não foi atualizado corretamente")

                second_id: int | None = None
                account_2_id: int | None = None
                if first_id is not None and updated_id == first_id:
                    second_payload = {
                        "term": f"segundo jogo {test_tag}",
                        "steam_app_id": test_app_id + 1,
                        "game_name": f"Segundo jogo checker {test_tag}",
                    }
                    second_id = post_history(
                        auth_token,
                        second_payload,
                        "POST /history novo jogo",
                    )
                    if second_id is not None:
                        if second_id != first_id:
                            report("PASS", "POST /history novo jogo", "criou registro distinto")
                        else:
                            report("FAIL", "POST /history novo jogo", "jogo diferente reutilizou o id anterior")

                    account_2_id = post_history(
                        auth_token_2,
                        first_payload,
                        "POST /history conta 2",
                    )
                    if account_2_id is not None:
                        if account_2_id != first_id:
                            report("PASS", "POST /history conta 2", "registro próprio criado")
                        else:
                            report("FAIL", "POST /history conta 2", "id inesperadamente compartilhado")
                else:
                    report("SKIP", "isolamento /history", "inserção ou deduplicação inicial não validada")

                items_1 = get_history(auth_token, "GET /history conta 1")
                items_2 = get_history(auth_token_2, "GET /history conta 2")
                if items_1 is not None and first_id is not None and second_id is not None:
                    ids_1 = [item["id"] for item in items_1]
                    expected_ids_1 = {first_id, second_id}
                    ordered_1 = sorted(
                        items_1,
                        key=lambda item: (item["created_at"], item["id"]),
                        reverse=True,
                    )
                    if (
                        len(items_1) <= 20
                        and set(ids_1) == expected_ids_1
                        and len(ids_1) == len(expected_ids_1)
                        and items_1 == ordered_1
                    ):
                        report("PASS", "GET /history conta 1", "limite, ordem e registros próprios válidos")
                    else:
                        report("FAIL", "GET /history conta 1", "limite, ordem ou escopo de registros inválido")
                elif items_1 is not None:
                    report("SKIP", "GET /history conta 1", "inserções do teste não foram validadas")

                if items_2 is not None and account_2_id is not None and first_id is not None:
                    if (
                        len(items_2) == 1
                        and items_2[0]["id"] == account_2_id
                        and items_2[0]["steam_app_id"] == test_app_id
                        and account_2_id != first_id
                    ):
                        report("PASS", "GET /history isolamento entre contas", "cada conta vê somente o próprio registro")
                    else:
                        report("FAIL", "GET /history isolamento entre contas", "dados de outra conta foram retornados")
                elif items_2 is not None:
                    report("SKIP", "GET /history isolamento entre contas", "registro da segunda conta não foi validado")

                cleanup_items_1 = get_history(auth_token, "GET /history para limpeza conta 1")
                cleanup_items_2 = get_history(auth_token_2, "GET /history para limpeza conta 2")
                delete_history(
                    auth_token,
                    "DELETE /history conta 1",
                    len(cleanup_items_1) if cleanup_items_1 is not None else None,
                )
                delete_history(
                    auth_token_2,
                    "DELETE /history conta 2",
                    len(cleanup_items_2) if cleanup_items_2 is not None else None,
                )
                after_delete_1 = get_history(auth_token, "GET /history após limpeza conta 1")
                after_delete_2 = get_history(auth_token_2, "GET /history após limpeza conta 2")
                if after_delete_1 == []:
                    report("PASS", "DELETE /history conta 1", "histórico de teste limpo")
                else:
                    report("FAIL", "DELETE /history conta 1", "dados de teste permaneceram")
                if after_delete_2 == []:
                    report("PASS", "DELETE /history conta 2", "histórico de teste limpo")
                else:
                    report("FAIL", "DELETE /history conta 2", "dados de teste permaneceram")

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
