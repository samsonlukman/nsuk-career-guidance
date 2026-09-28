#!/usr/bin/env python3
"""Download official O*NET 30.3 files into data/raw/.

Source: O*NET Resource Center
https://www.onetcenter.org/database.html

The O*NET 30.3 Database is licensed under Creative Commons Attribution 4.0.
https://www.onetcenter.org/license_db.html

This script downloads official tab-delimited files. It does not fabricate
occupational records. Re-run it to refresh a local copy.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import subprocess
import sys
import urllib.parse
from pathlib import Path

VERSION = "30.3"
BASE_URL = "https://www.onetcenter.org/dl_files/database/db_30_3_text"
ZIP_URL = "https://www.onetcenter.org/dl_files/database/db_30_3_text.zip"
DICTIONARY_URL = "https://www.onetcenter.org/dictionary/30.3/text/"
LICENSE_URL = "https://www.onetcenter.org/license_db.html"

# Files required for the proposed recommendation architecture.
REQUIRED_FILES = [
    "Read Me.txt",
    "Occupation Data.txt",
    "Content Model Reference.txt",
    "Scales Reference.txt",
    "Career Interest Types.txt",
    "Specific Interest Areas.txt",
    "Knowledge.txt",
    "Essential Skills.txt",
    "Transferable Skills.txt",
    "Work Styles.txt",
    "Work Activities.txt",
    "Abilities.txt",
    "Job Zones.txt",
    "Job Zone Reference.txt",
    "Education.txt",
    "Education Categories.txt",
    "Work Context.txt",
    "Work Context Categories.txt",
    "Training and Experience.txt",
    "Training and Experience Categories.txt",
    "Occupation Level Metadata.txt",
]

# Useful later for occupation pages; not required for KNN vectors.
OPTIONAL_FILES = [
    "Task Statements.txt",
    "Related Occupations.txt",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def curl_download(url: str, dest: Path, timeout: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "curl",
        "-L",
        "--fail",
        "--retry",
        "5",
        "--retry-delay",
        "3",
        "-C",
        "-",
        "--max-time",
        str(timeout),
        "-o",
        str(dest),
        url,
    ]
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Download failed ({result.returncode}): {url}")


def write_manifest(raw_dir: Path, files_dir: Path) -> None:
    lines = [
        f"source=https://www.onetcenter.org/database.html",
        f"version=O*NET {VERSION}",
        f"license={LICENSE_URL}",
        f"dictionary={DICTIONARY_URL}",
        f"download_base={BASE_URL}/",
        f"archive={ZIP_URL}",
        f"manifest_updated_utc={datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "format=tab-delimited text",
        "",
    ]
    if files_dir.exists():
        for path in sorted(files_dir.glob("*.txt")):
            lines.append(
                f"file={path.name}\tbytes={path.stat().st_size}\tsha256={sha256_file(path)}"
            )
    (raw_dir / "DOWNLOAD_MANIFEST.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Download official O*NET 30.3 database files.")
    parser.add_argument(
        "--full-zip",
        action="store_true",
        help="Download the complete official text zip instead of selected files.",
    )
    parser.add_argument(
        "--optional",
        action="store_true",
        help="Also download optional files (tasks, related occupations).",
    )
    parser.add_argument("--timeout", type=int, default=600, help="Per-file curl timeout in seconds.")
    args = parser.parse_args()

    raw_dir = repo_root() / "data" / "raw"
    files_dir = raw_dir / "db_30_3_text"
    files_dir.mkdir(parents=True, exist_ok=True)

    if args.full_zip:
        zip_path = raw_dir / "db_30_3_text.zip"
        print(f"Downloading {ZIP_URL}")
        curl_download(ZIP_URL, zip_path, timeout=max(args.timeout, 1200))
        subprocess.run(["unzip", "-o", str(zip_path), "-d", str(files_dir)], check=True)
    else:
        names = list(REQUIRED_FILES)
        if args.optional:
            names.extend(OPTIONAL_FILES)
        for name in names:
            url = f"{BASE_URL}/{urllib.parse.quote(name)}"
            dest = files_dir / name
            print(f"Downloading {name}")
            try:
                curl_download(url, dest, timeout=args.timeout)
            except RuntimeError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                return 1

    write_manifest(raw_dir, files_dir)
    print(f"Wrote {raw_dir / 'DOWNLOAD_MANIFEST.txt'}")
    print("Done. Attribute O*NET data to the U.S. Department of Labor / O*NET Resource Center.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
