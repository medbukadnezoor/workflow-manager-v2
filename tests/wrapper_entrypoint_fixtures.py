from __future__ import annotations

import difflib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WRAPPER_ENTRYPOINT = ROOT / "bin/workflow-wrapper"
WRAPPER_ENTRYPOINT_FIXTURE_DIR = ROOT / "tests/fixtures/wrapper-entrypoint"
WRAPPER_ENTRYPOINT_FIXTURE_NAME = "workflow-wrapper.txt"

REQUIRED_ENTRYPOINT_SNIPPETS = {
    "shebang": "#!/usr/bin/env zsh",
    "self-location-resolution": 'WORKFLOW_WRAPPER_SOURCE="${${(%):-%x}:A}"',
    "repo-home-derivation": 'WORKFLOW_WRAPPER_HOME="${WORKFLOW_WRAPPER_SOURCE:h:h}"',
    "repo-owned-shell-bridge": 'source "$WORKFLOW_WRAPPER_HOME/scripts/workflow.sh"',
    "dispatch-by-basename": 'cmd=$(basename "$0")',
    "delegate-to-wrapper-command": '"$cmd" "$@"',
}

FORBIDDEN_ENTRYPOINT_SNIPPETS = {
    "hardcoded-user-project-root": "<private-project-root>",
    "hardcoded-user-research-root": "<private-research-root>",
    "primary-workflow-roots-env": "WORKFLOW_ROOTS=",
    "legacy-scaffold-template": ".ai/context/scaffold-template",
    "shell-startup-edits": "~/.zshrc",
    "hermes-implemented-claim": "Hermes is implemented",
    "dashscope-implemented-claim": "DashScope is integrated",
    "qwen-implemented-claim": "Qwen integration is complete",
    "graphify-implemented-claim": "Graphify is implemented",
    "spec-kit-complete-claim": "full spec-kit fork/preset is implemented",
}


def normalize_wrapper_entrypoint_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    if not normalized.endswith("\n"):
        normalized += "\n"
    return normalized


def entrypoint_fixture_path(directory: Path | None = None) -> Path:
    directory = directory or WRAPPER_ENTRYPOINT_FIXTURE_DIR
    return directory / WRAPPER_ENTRYPOINT_FIXTURE_NAME


def build_current_wrapper_entrypoint_text(path: Path | None = None) -> str:
    path = path or WRAPPER_ENTRYPOINT
    return normalize_wrapper_entrypoint_text(path.read_text(encoding="utf-8"))


def verify_wrapper_entrypoint_invariants(text: str) -> None:
    errors: list[str] = []
    for label, snippet in REQUIRED_ENTRYPOINT_SNIPPETS.items():
        if snippet not in text:
            errors.append(
                f"`bin/workflow-wrapper` invariant `{label}` is missing snippet: {snippet}"
            )
    for label, snippet in FORBIDDEN_ENTRYPOINT_SNIPPETS.items():
        if snippet in text:
            errors.append(
                f"`bin/workflow-wrapper` invariant `{label}` was violated by forbidden snippet: {snippet}"
            )
    if errors:
        raise AssertionError("\n".join(errors))


def load_expected_wrapper_entrypoint_fixture(directory: Path | None = None) -> str:
    path = entrypoint_fixture_path(directory)
    if not path.exists():
        raise FileNotFoundError(f"Missing wrapper entrypoint fixture: {path}")
    return normalize_wrapper_entrypoint_text(path.read_text(encoding="utf-8"))


def verify_wrapper_entrypoint_fixture(
    directory: Path | None = None,
    *,
    current_text: str | None = None,
) -> None:
    current = normalize_wrapper_entrypoint_text(
        current_text if current_text is not None else build_current_wrapper_entrypoint_text()
    )
    verify_wrapper_entrypoint_invariants(current)

    path = entrypoint_fixture_path(directory)
    if not path.exists():
        raise FileNotFoundError(f"Missing wrapper entrypoint fixture: {path}")

    expected = normalize_wrapper_entrypoint_text(path.read_text(encoding="utf-8"))
    if expected == current:
        return

    diff = "\n".join(
        difflib.unified_diff(
            expected.splitlines(),
            current.splitlines(),
            fromfile=str(path),
            tofile="workflow-wrapper (current)",
            lineterm="",
        )
    )
    raise AssertionError(
        "\n".join(
            [
                f"Wrapper entrypoint fixture mismatch: {path}",
                diff or "(diff unavailable)",
            ]
        )
    )


def write_wrapper_entrypoint_fixture(directory: Path | None = None) -> Path:
    directory = directory or WRAPPER_ENTRYPOINT_FIXTURE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = entrypoint_fixture_path(directory)
    path.write_text(build_current_wrapper_entrypoint_text(), encoding="utf-8")
    return path
