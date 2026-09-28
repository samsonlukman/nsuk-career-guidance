#!/usr/bin/env python3
"""Ingest official O*NET 30.3 files into data/processed/onet_30_3_v1/.

Never writes to data/raw/. Re-run after refreshing the official snapshot.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.recommendation.ingest import default_output_dir, default_raw_dir, run_ingest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build processed O*NET 30.3 occupational features")
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=default_raw_dir(ROOT),
        help="Directory of official O*NET tab-delimited files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir(ROOT),
        help="Destination for processed tables (must not be inside raw-dir)",
    )
    args = parser.parse_args()
    snapshot = run_ingest(args.raw_dir, args.output_dir)
    print(json.dumps({"feature_version": snapshot.feature_version, "counts": snapshot.counts}, indent=2))
    print(f"Wrote {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
