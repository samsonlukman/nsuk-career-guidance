#!/usr/bin/env python3
"""Start the hosted web app: migrate, load O*NET, optional demo admin, then serve.

Used by the Docker image. Does not change recommendation scoring.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import normalize_database_url
from app.db.session import make_engine
from app.services.bootstrap import ensure_demo_admin
from app.services.onet_loader import default_processed_dir, load_processed_snapshot


def _prepare_env() -> str:
    raw = os.environ.get("DATABASE_URL")
    if not raw:
        raise SystemExit("DATABASE_URL is required")
    url = normalize_database_url(raw)
    os.environ["DATABASE_URL"] = url
    os.environ.setdefault("AUTH_COOKIE_SECURE", "true")
    return url


def _migrate(url: str) -> None:
    cfg = Config(str(ROOT / "backend" / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "backend" / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")


def _load_onet(url: str) -> None:
    engine = make_engine(url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, class_=Session)
    session = SessionLocal()
    try:
        load_processed_snapshot(session, default_processed_dir(ROOT))
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


def _bootstrap_admin(url: str) -> None:
    engine = make_engine(url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, class_=Session)
    session = SessionLocal()
    try:
        action = ensure_demo_admin(session)
        session.commit()
        if action:
            print(f"demo_admin: {action}", flush=True)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


def main() -> int:
    url = _prepare_env()
    _migrate(url)
    _load_onet(url)
    _bootstrap_admin(url)
    port = int(os.environ.get("PORT", "8000"))
    os.execvp(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
            "--proxy-headers",
            "--forwarded-allow-ips",
            "*",
        ],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
