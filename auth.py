import hashlib
import hmac
import re
import secrets
import sqlite3
from contextlib import closing
from pathlib import Path


PASSWORD_ITERATIONS = 600_000
USERNAME_PATTERN = re.compile(r"[a-zA-Z0-9_.-]{3,32}\Z")
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+\Z")


def initialize_auth_db(db_path: Path) -> None:
    with closing(sqlite3.connect(db_path)) as connection:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS app_users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    password_salt TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(app_users)"
                )
            }
            if "email" not in columns:
                connection.execute("ALTER TABLE app_users ADD COLUMN email TEXT")
            connection.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS app_users_email_unique
                ON app_users(email COLLATE NOCASE)
                """
            )


def register_user(
    db_path: Path,
    username: str,
    email: str,
    password: str,
) -> bool:
    normalized_username = username.strip().lower()
    normalized_email = email.strip().lower()
    if not USERNAME_PATTERN.fullmatch(normalized_username):
        raise ValueError(
            "Username must be 3–32 characters: letters, numbers, ., _ or -."
        )
    if not EMAIL_PATTERN.fullmatch(normalized_email):
        raise ValueError("Enter a valid email address.")
    if not 8 <= len(password) <= 128:
        raise ValueError("Password must be between 8 and 128 characters.")

    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )

    with closing(sqlite3.connect(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO app_users (
                    username,
                    email,
                    password_salt,
                    password_hash
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT DO NOTHING
                """,
                (
                    normalized_username,
                    normalized_email,
                    salt.hex(),
                    password_hash.hex(),
                ),
            )

    return cursor.rowcount == 1


def authenticate_user(
    db_path: Path,
    identifier: str,
    password: str,
) -> str | None:
    normalized_identifier = identifier.strip().lower()
    if not normalized_identifier or not password or len(password) > 128:
        return None

    with closing(sqlite3.connect(db_path)) as connection:
        user = connection.execute(
            """
            SELECT username, password_salt, password_hash
            FROM app_users
            WHERE username = ? COLLATE NOCASE
               OR email = ? COLLATE NOCASE
            """,
            (normalized_identifier, normalized_identifier),
        ).fetchone()

    salt = bytes.fromhex(user[1]) if user else bytes(16)
    expected_hash = bytes.fromhex(user[2]) if user else bytes(32)
    actual_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )

    if user and hmac.compare_digest(actual_hash, expected_hash):
        return user[0]

    return None
