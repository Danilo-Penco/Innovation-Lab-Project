"""Account storage and credential verification for the Reflex application."""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, MetaData, UniqueConstraint, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlmodel import Field, Session, SQLModel

DATABASE_URL = "sqlite:///reflex.db"
PASSWORD_HASH_ITERATIONS = 600_000
PASSWORD_SALT_BYTES = 16
PASSWORD_HASH_BYTES = 32
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
_DUMMY_SALT = b"ComparaKeys-dummy-salt"
_EMAIL_LOCAL_PART = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+")
_EMAIL_DOMAIN_LABEL = re.compile(
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
)


class AuthInputError(ValueError):
    """Raised when registration input does not meet the account requirements."""


class DuplicateEmailError(ValueError):
    """Raised when a normalized email is already associated with an account."""


class AuthModelBase(SQLModel):
    metadata = MetaData()


class UserAccount(AuthModelBase, table=True):
    __tablename__ = "user_accounts"
    __table_args__ = (
        UniqueConstraint("email_normalized", name="uq_user_accounts_email_normalized"),
    )

    id: int | None = Field(default=None, primary_key=True)
    email_normalized: str = Field(max_length=254)
    password_salt: str = Field(max_length=64)
    password_hash: str = Field(max_length=64)


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Register the SQLModel table with Reflex's migration metadata while avoiding its
# deprecated rx.Model base class.
from reflex.model import ModelRegistry  # noqa: E402

ModelRegistry.register(UserAccount)


@contextmanager
def _session_scope(database_engine: Engine) -> Iterator[Session]:
    with Session(database_engine) as session:
        yield session


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


def _derive_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
        dklen=PASSWORD_HASH_BYTES,
    )


def _encode_bytes(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii")


def _decode_bytes(value: str) -> bytes:
    return base64.urlsafe_b64decode(value.encode("ascii"))


def _is_duplicate_email_violation(error: IntegrityError) -> bool:
    return (
        isinstance(error.orig, sqlite3.IntegrityError)
        and str(error.orig)
        == "UNIQUE constraint failed: user_accounts.email_normalized"
    )


def register_account(
    email: str,
    password: str,
    database_engine: Engine = engine,
) -> int:
    normalized_email = normalize_email(email)
    validate_password(password)
    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)
    account = UserAccount(
        email_normalized=normalized_email,
        password_salt=_encode_bytes(salt),
        password_hash=_encode_bytes(_derive_password(password, salt)),
    )

    with _session_scope(database_engine) as session:
        existing = session.scalars(
            select(UserAccount).where(
                UserAccount.email_normalized == normalized_email
            )
        ).first()
        if existing is not None:
            raise DuplicateEmailError("Este endereço de e-mail já está em uso.")

        session.add(account)
        try:
            session.commit()
        except IntegrityError as error:
            session.rollback()
            if _is_duplicate_email_violation(error):
                raise DuplicateEmailError(
                    "Este endereço de e-mail já está em uso."
                ) from error
            raise

        session.refresh(account)
        if account.id is None:
            raise RuntimeError("O banco não retornou o identificador da conta.")
        return account.id


def verify_credentials(
    email: str,
    password: str,
    database_engine: Engine = engine,
) -> int | None:
    if not isinstance(password, str) or len(password) > MAX_PASSWORD_LENGTH:
        return None
    try:
        normalized_email = normalize_email(email)
    except AuthInputError:
        normalized_email = ""

    with _session_scope(database_engine) as session:
        account = session.scalars(
            select(UserAccount).where(
                UserAccount.email_normalized == normalized_email
            )
        ).first()
        if account is None:
            _derive_password(password, _DUMMY_SALT)
            return None

        actual_hash = _derive_password(password, _decode_bytes(account.password_salt))
        expected_hash = _decode_bytes(account.password_hash)
        if hmac.compare_digest(actual_hash, expected_hash):
            return account.id
        return None


def account_exists(user_id: int, database_engine: Engine = engine) -> bool:
    with _session_scope(database_engine) as session:
        return (
            session.scalar(select(UserAccount.id).where(UserAccount.id == user_id))
            is not None
        )
