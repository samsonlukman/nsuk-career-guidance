"""Shared runtime-database fixtures for O*NET load and API tests.

Schema tests use nsuk_career_test and must not wipe this database.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import REPO_ROOT, get_settings
from app.db.session import get_engine
from app.recommendation.constants import FEATURE_VERSION
from app.services.onet_loader import default_processed_dir, load_processed_snapshot

RUNTIME_DATABASE_URL = os.environ.get(
    "RUNTIME_DATABASE_URL",
    "postgresql+psycopg://apple@localhost:5432/nsuk_career",
)
PROCESSED_DIR = default_processed_dir(REPO_ROOT)


def _alembic_config(url: str) -> Config:
    cfg = Config(str(REPO_ROOT / "backend" / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "backend" / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def _ensure_runtime_migrated(url: str) -> None:
    engine = create_engine(url, future=True)
    try:
        inspector = inspect(engine)
        if "occupations" not in inspector.get_table_names() or "alembic_version" not in inspector.get_table_names():
            command.upgrade(_alembic_config(url), "head")
            return
    finally:
        engine.dispose()
    command.upgrade(_alembic_config(url), "head")


@pytest.fixture(scope="session")
def processed_dir() -> Path:
    if not (PROCESSED_DIR / "metadata.json").is_file():
        pytest.skip(f"Processed snapshot missing: {PROCESSED_DIR}")
    return PROCESSED_DIR


@pytest.fixture(scope="session")
def runtime_engine(processed_dir: Path):
    os.environ["DATABASE_URL"] = RUNTIME_DATABASE_URL
    get_settings.cache_clear()
    get_engine.cache_clear()
    _ensure_runtime_migrated(RUNTIME_DATABASE_URL)
    engine = create_engine(RUNTIME_DATABASE_URL, future=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def loaded_snapshot(runtime_engine, processed_dir: Path):
    SessionLocal = sessionmaker(bind=runtime_engine, autoflush=False, class_=Session)
    session = SessionLocal()
    try:
        result = load_processed_snapshot(session, processed_dir)
        session.commit()
        assert result.feature_version == FEATURE_VERSION
        yield result
    finally:
        session.close()


@pytest.fixture
def db_session(runtime_engine, loaded_snapshot):
    SessionLocal = sessionmaker(bind=runtime_engine, autoflush=False, class_=Session)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
