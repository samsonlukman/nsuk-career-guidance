#!/usr/bin/env python3
"""Evaluation environment CLI. Never targets nsuk_career or production by default.

Required for mutating commands:
  EVALUATION_CONFIRM=I_UNDERSTAND
  EVALUATION_DATABASE_URL=postgresql+psycopg://apple@localhost:5432/nsuk_career_eval

There is no public HTTP reset endpoint.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT))

from app.evaluation.operations import (  # noqa: E402
    configured_evaluation_url,
    create_evaluation_admin,
    default_export_dir,
    evaluation_status,
    export_evaluation_results,
    initialize_evaluation_environment,
    reset_evaluation_students,
    run_determinism_check,
    run_integrity_checks,
    run_performance_baseline,
)
from app.evaluation.safeguards import EvaluationTargetError  # noqa: E402


def _url(args: argparse.Namespace) -> str:
    return configured_evaluation_url(args.database_url)


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, default=str))


def main() -> int:
    parser = argparse.ArgumentParser(description="NSUK career evaluation environment tools")
    parser.add_argument(
        "--database-url",
        default=None,
        help="Evaluation SQLAlchemy URL (defaults to EVALUATION_DATABASE_URL or nsuk_career_eval)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="Show evaluation database contents without changing them")
    sub.add_parser("init", help="Create/migrate/load a clean evaluation database")
    reset = sub.add_parser("reset-students", help="Delete evaluation students/assessments/runs/ratings")
    reset.add_argument("--yes", action="store_true", help="Required confirmation flag")
    sub.add_parser("create-admin", help="Create an admin from EVAL_ADMIN_EMAIL / EVAL_ADMIN_PASSWORD")
    export = sub.add_parser("export", help="Export pseudonymous evaluation results")
    export.add_argument("--output-dir", type=Path, default=None)
    sub.add_parser("integrity", help="Run foreign-key and consistency checks")
    sub.add_parser("determinism", help="Submit the same assessment twice and compare rankings")
    baseline = sub.add_parser("baseline", help="Record local development timings")
    baseline.add_argument("--repeats", type=int, default=3)

    args = parser.parse_args()
    try:
        url = _url(args)
        if args.command == "status":
            _print(asdict(evaluation_status(url)))
        elif args.command == "init":
            _print(asdict(initialize_evaluation_environment(url)))
        elif args.command == "reset-students":
            if not args.yes:
                raise SystemExit("Refusing reset-students without --yes.")
            _print(reset_evaluation_students(url))
        elif args.command == "create-admin":
            _print(create_evaluation_admin(url))
        elif args.command == "export":
            target = export_evaluation_results(url, args.output_dir or default_export_dir())
            _print({"export_dir": str(target)})
        elif args.command == "integrity":
            report = run_integrity_checks(url)
            _print(asdict(report))
            return 0 if report.passed else 1
        elif args.command == "determinism":
            _print(run_determinism_check(url))
        elif args.command == "baseline":
            _print(run_performance_baseline(url, repeats=args.repeats))
        else:
            raise SystemExit(f"Unknown command: {args.command}")
    except EvaluationTargetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
