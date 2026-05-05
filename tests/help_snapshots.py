from __future__ import annotations

import difflib
from pathlib import Path

from workflow_manager import cli as workflow_cli


ROOT = Path(__file__).resolve().parents[1]
HELP_FIXTURE_DIR = ROOT / "tests/fixtures/help"
HELP_SNAPSHOT_LABELS = ["workflow", *[f"workflow {command}" for command in workflow_cli.EXPECTED_WORKFLOW_COMMANDS]]


def normalize_help_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    if not normalized.endswith("\n"):
        normalized += "\n"
    return normalized


def snapshot_filename_for_label(label: str) -> str:
    return label.replace(" ", "-") + ".txt"


def snapshot_path_for_label(label: str, directory: Path | None = None) -> Path:
    directory = directory or HELP_FIXTURE_DIR
    return directory / snapshot_filename_for_label(label)


def expected_snapshot_paths(directory: Path | None = None) -> dict[str, Path]:
    return {label: snapshot_path_for_label(label, directory) for label in HELP_SNAPSHOT_LABELS}


def build_current_help_snapshots() -> dict[str, str]:
    snapshot = workflow_cli.build_cli_surface_snapshot()
    current: dict[str, str] = {}
    for label in HELP_SNAPSHOT_LABELS:
        if label not in snapshot.help_texts:
            raise AssertionError(f"Current CLI surface is missing help output for `{label}`.")
        current[label] = normalize_help_text(snapshot.help_texts[label])
    return current


def load_expected_help_snapshots(directory: Path | None = None) -> dict[str, str]:
    expected: dict[str, str] = {}
    for label, path in expected_snapshot_paths(directory).items():
        if not path.exists():
            raise FileNotFoundError(f"Missing help snapshot for `{label}`: {path}")
        expected[label] = normalize_help_text(path.read_text(encoding="utf-8"))
    return expected


def verify_help_snapshots(directory: Path | None = None) -> None:
    current = build_current_help_snapshots()
    errors: list[str] = []

    for label, path in expected_snapshot_paths(directory).items():
        if not path.exists():
            errors.append(f"Missing help snapshot for `{label}`: {path}")
            continue
        expected = normalize_help_text(path.read_text(encoding="utf-8"))
        actual = current[label]
        if expected == actual:
            continue
        diff = "\n".join(
            difflib.unified_diff(
                expected.splitlines(),
                actual.splitlines(),
                fromfile=str(path),
                tofile=f"{label} (current)",
                lineterm="",
            )
        )
        errors.append(
            "\n".join(
                [
                    f"Help snapshot mismatch for `{label}`: {path}",
                    diff or "(diff unavailable)",
                ]
            )
        )

    if errors:
        raise AssertionError("\n\n".join(errors))


def write_help_snapshots(directory: Path | None = None) -> dict[str, Path]:
    directory = directory or HELP_FIXTURE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    current = build_current_help_snapshots()
    written: dict[str, Path] = {}
    for label, text in current.items():
        path = snapshot_path_for_label(label, directory)
        path.write_text(text, encoding="utf-8")
        written[label] = path
    return written
