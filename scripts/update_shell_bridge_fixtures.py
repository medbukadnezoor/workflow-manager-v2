#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.shell_bridge_fixtures import (  # noqa: E402
    SHELL_BRIDGE_FIXTURE_DIR,
    write_shell_bridge_fixture,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh the repo-owned shell-bridge fixture for scripts/workflow.sh. "
            "This is a manual developer governance step and does not run during normal validation."
        )
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Explicitly refresh the stored shell-bridge fixture.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(SHELL_BRIDGE_FIXTURE_DIR),
        help="Target fixture directory; defaults to tests/fixtures/shell-bridge.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.write:
        parser.error("pass `--write` to refresh shell-bridge fixtures intentionally")

    output_dir = Path(args.output_dir).resolve()
    written = write_shell_bridge_fixture(output_dir)
    print(f"Wrote shell-bridge fixture to {written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
