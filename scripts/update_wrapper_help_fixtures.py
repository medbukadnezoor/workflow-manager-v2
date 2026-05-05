#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.wrapper_help_fixtures import WRAPPER_FIXTURE_DIR, write_wrapper_help_fixtures  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh the repo-owned shell-wrapper help fixtures. This is a manual "
            "developer governance step and does not run during normal validation."
        )
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Explicitly refresh the stored wrapper-help fixtures.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(WRAPPER_FIXTURE_DIR),
        help="Target fixture directory; defaults to tests/fixtures/wrapper-help.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.write:
        parser.error("pass `--write` to refresh wrapper-help fixtures intentionally")

    output_dir = Path(args.output_dir).resolve()
    written = write_wrapper_help_fixtures(output_dir)
    print(f"Wrote {len(written)} wrapper-help fixture files to {output_dir}")
    for label, path in written.items():
        print(f"- {label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
