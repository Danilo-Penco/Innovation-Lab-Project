"""HTTP client for the existing Xano Authentication endpoints."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx
from dotenv import load_dotenv

load_dotenv()

XANO_API_URL_ENV = "XANO_API_URL"
REQUEST_TIMEOUT_SECONDS = 10.0
AUTH_SERVICE_UNAVAILABLE_MESSAGE = (
    "Não foi possível conectar ao serviço de autenticação. Tente novamente."
)
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
WEAK_PASSWORD_MESSAGE = (
    "A senha deve ter entre 8 e 128 caracteres e conter ao menos uma letra."
)

_EMAIL_LOCAL_PART = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+")
_EMAIL_DOMAIN_LABEL = re.compile(
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
)


class AuthInputError(ValueError):
    """Raised when locally validated authentication input is invalid."""


class DuplicateEmailError(ValueError):
    """Raised when Xano reports that an email is already registered."""


class InvalidCredentialsError(ValueError):
    """Raised when Xano rejects a login."""


class InvalidTokenError(ValueError):
    """Raised when Xano rejects the current session token."""


class XanoUnavailableError(RuntimeError):
    """Raised when Xano cannot be reached or returns an unusable response."""


class XanoApiError(RuntimeError):
    """Raised for a Xano error response that has no known user-facing mapping."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        payload_param: str | None = None,
    ) -> None:
        super().__init__(f"Xano returned HTTP {status_code}: {code}")
        self.status_code = status_code
        self.code = code
        self.message = message
        self.payload_param = payload_param


@dataclass(frozen=True)
class AuthSession:
    auth_token: str
    user_id: int


@dataclass(frozen=True)
class AuthenticatedUser:
    id: int
    created_at: int
    name: str
    email: str
    role: str


def _unavailable() -> XanoUnavailableError:
    return XanoUnavailableError(AUTH_SERVICE_UNAVAILABLE_MESSAGE)


def normalize_email(email: str) -> str:
    if not isinstance(email, str):
        raise AuthInputError("Informe um e-mail válido.")
    normalized = email.strip().lower()
    if len(normalized) > 254 or normalized.count("@") != 1:
        raise AuthInputError("Informe um e-mail válido.")

    local_part, domain = normalized.rsplit("@", 1)
    labels = domain.split(".")
    if (
        not local_part
        or len(local_part) > 64
        or local_part.startswith(".")
        or local_part.endswith(".")
        or ".." in local_part
        or not _EMAIL_LOCAL_PART.fullmatch(local_part)
        or len(labels) < 2
        or any(not _EMAIL_DOMAIN_LABEL.fullmatch(label) for label in labels)
    ):
        raise AuthInputError("Informe um e-mail válido.")
    return normalized


def validate_password(password: str) -> None:
    if not isinstance(password, str):
        raise AuthInputError("Informe uma senha válida.")
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise AuthInputError(
            "A senha deve ter entre "
            f"{MIN_PASSWORD_LENGTH} e {MAX_PASSWORD_LENGTH} caracteres."
        )
    if not any(character.isalpha() for character in password):
        raise AuthInputError(WEAK_PASSWORD_MESSAGE)


def _base_url() -> str:
    value = os.environ.get(XANO_API_URL_ENV, "").strip().rstrip("/")
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise _unavailable()
    return value


def _parse_error(response: httpx.Response, endpoint: str) -> XanoApiError:
    if response.status_code == 401 and endpoint == "auth/me":
        raise InvalidTokenError("Sessão inválida.")
    try:
        body = response.json()
    except ValueError:
        body = {}
    if not isinstance(body, dict):
        body = {}

    code = body.get("code")
    message = body.get("message")
    payload = body.get("payload")
    if not isinstance(code, str) or not code:
        code = f"HTTP_{response.status_code}"
    if not isinstance(message, str) or not message.strip():
        message = f"Xano rejected the request with HTTP {response.status_code}."

    payload_param = payload.get("param") if isinstance(payload, dict) else None
    if not isinstance(payload_param, str):
        payload_param = None

    if response.status_code == 400 and payload_param == "email":
        raise AuthInputError("Informe um e-mail válido.")
    if response.status_code == 400 and payload_param == "password":
        raise AuthInputError(WEAK_PASSWORD_MESSAGE)
    if response.status_code == 403 and code == "ERROR_CODE_ACCESS_DENIED":
        normalized_message = message.casefold()
        if endpoint == "auth/signup" and "already exists" in normalized_message:
            raise DuplicateEmailError("Este endereço de e-mail já está em uso.")
        if endpoint == "auth/login" and normalized_message == "invalid credentials.":
            raise InvalidCredentialsError("E-mail ou senha inválidos.")

    return XanoApiError(
        response.status_code,
        code,
        message,
        payload_param,
    )


async def _request(
    method: str,
    endpoint: str,
    *,
    payload: dict[str, str] | None = None,
    auth_token: str | None = None,
) -> dict[str, object]:
    headers = {"Authorization": f"Bearer {auth_token}"} if auth_token is not None else {}
    url = f"{_base_url()}/{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            for attempt in range(2):
                try:
                    response = await client.request(
                        method,
                        url,
                        json=payload,
                        headers=headers,
                    )
                    break
                except (httpx.TimeoutException, httpx.NetworkError) as error:
                    if attempt == 1:
                        raise _unavailable() from error
                except (httpx.InvalidURL, httpx.RequestError) as error:
                    raise _unavailable() from error
    except (httpx.InvalidURL, httpx.RequestError) as error:
        raise _unavailable() from error

    if response.status_code != 200:
        raise _parse_error(response, endpoint)

    try:
        body = response.json()
    except ValueError as error:
        raise _unavailable() from error
    if not isinstance(body, dict):
        raise _unavailable()
    return body


async def _authenticated_request(
    method: str,
    endpoint: str,
    auth_token: str,
    *,
    payload: dict[str, str] | None = None,
) -> dict[str, object]:
    if not auth_token:
        raise InvalidTokenError("Sessão inválida.")
    return await _request(
        method,
        endpoint,
        payload=payload,
        auth_token=auth_token,
    )


def _auth_session(body: dict[str, object]) -> AuthSession:
    auth_token = body.get("authToken")
    user_id = body.get("user_id")
    if (
        not isinstance(auth_token, str)
        or not auth_token.strip()
        or not isinstance(user_id, int)
        or isinstance(user_id, bool)
    ):
        raise _unavailable()
    return AuthSession(auth_token=auth_token, user_id=user_id)


async def signup(name: str, email: str, password: str) -> AuthSession:
    normalized_name = name.strip() if isinstance(name, str) else ""
    if not normalized_name:
        raise AuthInputError("Informe seu nome.")
    normalized_email = normalize_email(email)
    validate_password(password)

    body = await _request(
        "POST",
        "auth/signup",
        payload={
            "name": normalized_name,
            "email": normalized_email,
            "password": password,
        },
    )
    return _auth_session(body)


async def login(email: str, password: str) -> AuthSession:
    normalized_email = normalize_email(email)
    body = await _request(
        "POST",
        "auth/login",
        payload={"email": normalized_email, "password": password},
    )
    return _auth_session(body)


async def me(auth_token: str) -> AuthenticatedUser:
    if not auth_token:
        raise InvalidTokenError("Sessão inválida.")
    body = await _authenticated_request("GET", "auth/me", auth_token)

    user_id = body.get("id")
    created_at = body.get("created_at")
    name = body.get("name")
    email = body.get("email")
    role = body.get("role")
    if (
        not isinstance(user_id, int)
        or isinstance(user_id, bool)
        or not isinstance(created_at, int)
        or isinstance(created_at, bool)
        or not isinstance(name, str)
        or not isinstance(email, str)
        or not isinstance(role, str)
    ):
        raise _unavailable()
    return AuthenticatedUser(
        id=user_id,
        created_at=created_at,
        name=name,
        email=email,
        role=role,
    )