#!/usr/bin/env python3
"""Load data/processed/onet_30_3_v1/ into PostgreSQL.

Does not read raw O*NET TSV files. Safe to re-run (upserts occupations;
skips feature COPY when the snapshot is already complete).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.db.session import make_engine  # noqa: E402
from app.services.onet_loader import default_processed_dir, load_processed_snapshot  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Load processed O*NET 30.3 snapshot into PostgreSQL")
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=default_processed_dir(ROOT),
        help="Directory produced by scripts/ingest_onet.py",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="SQLAlchemy URL (defaults to DATABASE_URL / Settings)",
    )
    parser.add_argument(
        "--force-features",
        action="store_true",
        help="Delete and reload occupation_features even if counts already match",
    )
    args = parser.parse_args()
    engine = make_engine(args.database_url or get_settings().database_url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, class_=Session)
    session = SessionLocal()
    try:
        result = load_processed_snapshot(
            session,
            args.processed_dir,
            force_features=args.force_features,
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()
    print(json.dumps(asdict(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
