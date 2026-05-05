#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.wrapper_entrypoint_fixtures import (  # noqa: E402
    WRAPPER_ENTRYPOINT_FIXTURE_DIR,
    write_wrapper_entrypoint_fixture,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh the repo-owned wrapper-entrypoint fixture for bin/workflow-wrapper. "
            "This is a manual developer governance step and does not run during normal validation."
        )
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Explicitly refresh the stored wrapper-entrypoint fixture.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(WRAPPER_ENTRYPOINT_FIXTURE_DIR),
        help="Target fixture directory; defaults to tests/fixtures/wrapper-entrypoint.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.write:
        parser.error("pass `--write` to refresh wrapper-entrypoint fixtures intentionally")

    output_dir = Path(args.output_dir).resolve()
    written = write_wrapper_entrypoint_fixture(output_dir)
    print(f"Wrote wrapper-entrypoint fixture to {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
