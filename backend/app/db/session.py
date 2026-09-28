"""Database engine helpers. Connection URL comes from the environment."""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def make_engine(url: str | None = None, *, echo: bool = False) -> Engine:
    return create_engine(url or get_settings().database_url, echo=echo, future=True, pool_pre_ping=True)


@lru_cache
def get_engine() -> Engine:
    return make_engine()


def get_session() -> Generator[Session, None, None]:
    SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, class_=Session)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
