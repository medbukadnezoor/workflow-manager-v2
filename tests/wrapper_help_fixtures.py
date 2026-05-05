from __future__ import annotations

import difflib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/workflow.sh"
WRAPPER_FIXTURE_DIR = ROOT / "tests/fixtures/wrapper-help"
WORKFLOW_MANAGER_PLACEHOLDER = "<WORKFLOW_MANAGER_HOME>"

WRAPPER_HELP_CASES = {
    "project-add-root-usage": {
        "command": "project-add-root",
    },
    "project-add-root-instructions": {
        "command": "project-add-root /tmp/example-root",
    },
    "project-open-invalid-argument": {
        "command": "project-open demo-project --bad",
    },
}


def normalize_wrapper_output(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    normalized = normalized.replace(str(ROOT), WORKFLOW_MANAGER_PLACEHOLDER)
    if not normalized.endswith("\n"):
        normalized += "\n"
    return normalized


def fixture_filename_for_label(label: str) -> str:
    return label + ".txt"


def fixture_path_for_label(label: str, directory: Path | None = None) -> Path:
    directory = directory or WRAPPER_FIXTURE_DIR
    return directory / fixture_filename_for_label(label)


def expected_fixture_paths(directory: Path | None = None) -> dict[str, Path]:
    return {label: fixture_path_for_label(label, directory) for label in WRAPPER_HELP_CASES}


def _run_wrapper_command(command: str) -> tuple[int, str]:
    shell_command = "\n".join(
        [
            f"WORKFLOW_MANAGER_HOME={ROOT}",
            f"source {SCRIPT}",
            command,
        ]
    )
    result = subprocess.run(
        ["zsh", "-lc", shell_command],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.returncode, result.stdout


def render_wrapper_fixture(exit_code: int, output: str) -> str:
    return f"exit={exit_code}\n" + normalize_wrapper_output(output)


def build_current_wrapper_fixtures() -> dict[str, str]:
    current: dict[str, str] = {}
    for label, case in WRAPPER_HELP_CASES.items():
        exit_code, output = _run_wrapper_command(case["command"])
        current[label] = render_wrapper_fixture(exit_code, output)
    return current


def load_expected_wrapper_fixtures(directory: Path | None = None) -> dict[str, str]:
    expected: dict[str, str] = {}
    for label, path in expected_fixture_paths(directory).items():
        if not path.exists():
            raise FileNotFoundError(f"Missing wrapper fixture for `{label}`: {path}")
        expected[label] = normalize_wrapper_output(path.read_text(encoding="utf-8"))
    return expected


def verify_wrapper_help_fixtures(directory: Path | None = None) -> None:
    current = build_current_wrapper_fixtures()
    errors: list[str] = []

    for label, path in expected_fixture_paths(directory).items():
        if not path.exists():
            errors.append(f"Missing wrapper fixture for `{label}`: {path}")
            continue
        expected = normalize_wrapper_output(path.read_text(encoding="utf-8"))
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
                    f"Wrapper fixture mismatch for `{label}`: {path}",
                    diff or "(diff unavailable)",
                ]
            )
        )

    if errors:
        raise AssertionError("\n\n".join(errors))


def write_wrapper_help_fixtures(directory: Path | None = None) -> dict[str, Path]:
    directory = directory or WRAPPER_FIXTURE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    current = build_current_wrapper_fixtures()
    written: dict[str, Path] = {}
    for label, text in current.items():
        path = fixture_path_for_label(label, directory)
        path.write_text(text, encoding="utf-8")
        written[label] = path
    return written
