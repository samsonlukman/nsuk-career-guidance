"""Refuse evaluation operations against development, test, or production databases."""

from __future__ import annotations

import os
import re
from urllib.parse import urlparse

CONFIRM_VALUE = "I_UNDERSTAND"
DEFAULT_EVALUATION_DATABASE_URL = "postgresql+psycopg://apple@localhost:5432/nsuk_career_eval"
PROTECTED_DATABASE_NAMES = frozenset(
    {
        "nsuk_career",
        "nsuk_career_test",
        "postgres",
        "template0",
        "template1",
    }
)
_SAFE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class EvaluationTargetError(ValueError):
    """The configured database is not a permitted evaluation target."""


def sqlalchemy_url_database_name(url: str) -> str:
    normalized = url.replace("postgresql+psycopg", "postgresql", 1)
    parsed = urlparse(normalized)
    return (parsed.path or "").lstrip("/").split("?")[0]


def resolve_evaluation_database_url(explicit: str | None = None) -> str:
    """Return the evaluation URL. Never falls back to the development DATABASE_URL."""
    return explicit or os.environ.get("EVALUATION_DATABASE_URL") or DEFAULT_EVALUATION_DATABASE_URL


def assert_safe_database_name(name: str) -> None:
    if not name or not _SAFE_NAME.match(name):
        raise EvaluationTargetError("Database name is not a safe identifier.")
    if name in PROTECTED_DATABASE_NAMES:
        raise EvaluationTargetError(
            f"Refusing evaluation operation on protected database '{name}'. "
            "Use a dedicated database whose name ends with _eval."
        )
    if not name.endswith("_eval"):
        raise EvaluationTargetError(
            f"Evaluation operations require a database name ending in '_eval' (got '{name}')."
        )


def assert_evaluation_target(url: str, *, mutating: bool) -> str:
    """Validate an evaluation database URL.

    Mutating commands also require EVALUATION_CONFIRM=I_UNDERSTAND so a
    mis-pointed shell cannot wipe or seed the wrong database.
    """
    name = sqlalchemy_url_database_name(url)
    assert_safe_database_name(name)
    if mutating and os.environ.get("EVALUATION_CONFIRM") != CONFIRM_VALUE:
        raise EvaluationTargetError(
            "Refusing mutating evaluation operation. Set EVALUATION_CONFIRM=I_UNDERSTAND "
            "in the environment after confirming EVALUATION_DATABASE_URL points at the "
            "evaluation database (name must end with _eval)."
        )
    return name
