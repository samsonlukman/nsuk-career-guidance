from app.core.config import normalize_database_url


def test_hosted_postgres_urls_use_psycopg() -> None:
    assert (
        normalize_database_url("postgres://user:pass@host:5432/db")
        == "postgresql+psycopg://user:pass@host:5432/db"
    )
    assert (
        normalize_database_url("postgresql://user:pass@host:5432/db?sslmode=require")
        == "postgresql+psycopg://user:pass@host:5432/db?sslmode=require"
    )
    assert normalize_database_url("postgresql+psycopg://apple@localhost:5432/nsuk_career").startswith(
        "postgresql+psycopg://"
    )
