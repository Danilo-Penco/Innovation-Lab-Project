import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from Projeto.auth import (
    AuthInputError,
    AuthModelBase,
    DuplicateEmailError,
    UserAccount,
    account_exists,
    normalize_email,
    register_account,
    validate_password,
    verify_credentials,
)


class AuthServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "auth-test.db"
        self.engine = create_engine(
            f"sqlite:///{database_path}",
            connect_args={"check_same_thread": False},
        )
        AuthModelBase.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        self.engine.dispose()
        self.temporary_directory.cleanup()

    def test_email_is_trimmed_and_case_insensitive(self) -> None:
        self.assertEqual(
            normalize_email("  Person.Name+tag@Example.COM "),
            "person.name+tag@example.com",
        )

    def test_email_validation_rejects_invalid_addresses(self) -> None:
        for email in ("", "not-an-email", "a@b", "a..b@example.com", "a@-example.com"):
            with self.subTest(email=email):
                with self.assertRaises(AuthInputError):
                    normalize_email(email)

    def test_password_validation_enforces_length_bounds(self) -> None:
        validate_password("p" * 8)
        validate_password("p" * 128)
        for password in ("", "p" * 7, "p" * 129):
            with self.subTest(password_length=len(password)):
                with self.assertRaises(AuthInputError):
                    validate_password(password)

    def test_registration_persists_a_hash_and_verifies_credentials(self) -> None:
        user_id = register_account(
            "  User@Example.com ",
            "correct horse battery staple",
            self.engine,
        )

        self.assertTrue(account_exists(user_id, self.engine))
        self.assertEqual(
            verify_credentials(
                "user@example.com", "correct horse battery staple", self.engine
            ),
            user_id,
        )
        self.assertIsNone(
            verify_credentials("USER@example.com", "wrong password", self.engine)
        )
        with Session(self.engine) as session:
            account = session.scalars(
                select(UserAccount).where(UserAccount.id == user_id)
            ).one()
        self.assertNotIn("correct horse battery staple", account.password_hash)
        self.assertNotEqual(account.password_hash, account.password_salt)

    def test_duplicate_normalized_email_is_rejected(self) -> None:
        register_account("user@example.com", "valid password", self.engine)
        with self.assertRaises(DuplicateEmailError):
            register_account(" USER@EXAMPLE.COM ", "another valid password", self.engine)

    def test_unique_constraint_race_becomes_duplicate_email_error(self) -> None:
        register_account("existing@example.com", "valid password", self.engine)
        race_error = IntegrityError(
            "INSERT",
            {},
            sqlite3.IntegrityError(
                "UNIQUE constraint failed: user_accounts.email_normalized"
            ),
        )
        with patch.object(Session, "commit", side_effect=race_error):
            with self.assertRaises(DuplicateEmailError):
                register_account("racing@example.com", "valid password", self.engine)

    def test_unrelated_database_error_is_not_hidden(self) -> None:
        disk_error = IntegrityError(
            "INSERT",
            {},
            sqlite3.IntegrityError("disk I/O error"),
        )
        with patch.object(Session, "commit", side_effect=disk_error):
            with self.assertRaises(IntegrityError):
                register_account("database@example.com", "valid password", self.engine)

    def test_invalid_credentials_never_create_a_session_identity(self) -> None:
        self.assertIsNone(
            verify_credentials("missing@example.com", "password", self.engine)
        )
        self.assertFalse(account_exists(987654321, self.engine))


if __name__ == "__main__":
    unittest.main()
