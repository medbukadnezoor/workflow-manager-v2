from __future__ import annotations

import difflib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHELL_BRIDGE = ROOT / "scripts/workflow.sh"
SHELL_BRIDGE_FIXTURE_DIR = ROOT / "tests/fixtures/shell-bridge"
SHELL_BRIDGE_FIXTURE_NAME = "workflow-sh-profile.txt"

EXPECTED_WRAPPER_FUNCTIONS = [
    "project-open",
    "project-close",
    "project-save",
    "project-list",
    "project-status",
    "project-init",
    "project-sync",
    "project-add-root",
]

REQUIRED_SHELL_BRIDGE_SNIPPETS = {
    "workflow-cli-dispatch": 'command python3 "$WORKFLOW_MANAGER_HOME/bin/workflow" "$@"',
    "roots-source-of-truth": 'WORKFLOW_ROOT_SOURCE="$WORKFLOW_MANAGER_HOME/.workflow/roots.json"',
    "temporary-workflow-roots-override": 'WORKFLOW_ROOT_SOURCE="temporary WORKFLOW_ROOTS override"',
    "cli-roots-shell-export": 'roots_payload=$(workflow roots --format shell) || return 1',
    "project-open-shell-cd": 'cd "$WORKFLOW_OPEN_PATH" || return 1',
    "project-open-cli-status": "workflow status",
    "project-close-shell-open": '_workflow_open_file "$WORKFLOW_CLOSE_OPEN_PATH"',
    "project-list-cli-delegation": 'workflow list "${WORKFLOW_ROOT_ARGS[@]}"',
    "project-status-cli-delegation": 'workflow status "$@"',
    "project-init-cli-delegation": 'workflow init "$@"',
    "project-sync-cli-delegation": 'workflow sync "$@"',
    "workflow-doctor-cli-delegation": 'workflow doctor "$@"',
    "project-add-root-roots-json-guidance": 'echo "$WORKFLOW_MANAGER_HOME/.workflow/roots.json"',
    "project-add-root-validate-guidance": 'echo "workflow roots --validate"',
    "project-add-root-no-shell-startup-edits": 'echo "This repo does not edit shell startup files automatically."',
}

FORBIDDEN_SHELL_BRIDGE_SNIPPETS = {
    "hardcoded-user-project-root": "<private-project-root>",
    "hardcoded-user-research-root": "<private-research-root>",
    "shell-startup-edits": "~/.zshrc",
    "live-scaffold-template": ".ai/context/scaffold-template",
    "edit-workflow-sh-as-primary-roots-path": "edit scripts/workflow.sh",
    "hermes-implemented-claim": "Hermes is implemented",
    "dashscope-implemented-claim": "DashScope is integrated",
    "qwen-implemented-claim": "Qwen integration is complete",
    "graphify-implemented-claim": "Graphify is implemented",
    "spec-kit-complete-claim": "full spec-kit fork/preset is implemented",
}

FORBIDDEN_SHELL_BRIDGE_REGEXES = {
    "default-workflow-roots-assignment": re.compile(r"(?m)^\s*(?:export\s+)?WORKFLOW_ROOTS=\("),
}

SHELL_BRIDGE_FUNCTION_PATTERN = re.compile(r"(?m)^([A-Za-z0-9_-]+)\(\) \{")


def normalize_shell_bridge_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    if not normalized.endswith("\n"):
        normalized += "\n"
    return normalized


def shell_bridge_fixture_path(directory: Path | None = None) -> Path:
    directory = directory or SHELL_BRIDGE_FIXTURE_DIR
    return directory / SHELL_BRIDGE_FIXTURE_NAME


def build_current_shell_bridge_text(path: Path | None = None) -> str:
    path = path or SHELL_BRIDGE
    return normalize_shell_bridge_text(path.read_text(encoding="utf-8"))


def _strip_comment_lines(text: str) -> str:
    return "\n".join(
        line for line in normalize_shell_bridge_text(text).splitlines() if not line.lstrip().startswith("#")
    )


def _line_containing(text: str, snippet: str) -> str:
    for line in normalize_shell_bridge_text(text).splitlines():
        if snippet in line:
            return line.strip()
    return "(missing)"


def extract_shell_bridge_functions(text: str) -> list[str]:
    functions = [match.group(1) for match in SHELL_BRIDGE_FUNCTION_PATTERN.finditer(text)]
    return [
        name
        for name in functions
        if name.startswith("project-") or name in {"workflow", "workflow-doctor"}
    ]


def verify_shell_bridge_invariants(text: str) -> None:
    current = normalize_shell_bridge_text(text)
    code_only = _strip_comment_lines(current)
    errors: list[str] = []

    functions = extract_shell_bridge_functions(current)
    for name in EXPECTED_WRAPPER_FUNCTIONS:
        if name not in functions:
            errors.append(f"`scripts/workflow.sh` invariant `wrapper-function:{name}` is missing.")

    for label, snippet in REQUIRED_SHELL_BRIDGE_SNIPPETS.items():
        if snippet not in current:
            errors.append(
                f"`scripts/workflow.sh` invariant `{label}` is missing snippet: {snippet}"
            )

    for label, snippet in FORBIDDEN_SHELL_BRIDGE_SNIPPETS.items():
        if snippet in code_only:
            errors.append(
                f"`scripts/workflow.sh` invariant `{label}` was violated by forbidden snippet: {snippet}"
            )

    for label, pattern in FORBIDDEN_SHELL_BRIDGE_REGEXES.items():
        if pattern.search(code_only):
            errors.append(f"`scripts/workflow.sh` invariant `{label}` was violated.")

    if errors:
        raise AssertionError("\n".join(errors))


def render_shell_bridge_profile(text: str | None = None) -> str:
    current = normalize_shell_bridge_text(
        text if text is not None else build_current_shell_bridge_text()
    )
    verify_shell_bridge_invariants(current)
    code_only = _strip_comment_lines(current)
    functions = extract_shell_bridge_functions(current)

    lines = [
        "script: scripts/workflow.sh",
        "",
        "wrapper functions:",
    ]
    lines.extend(f"- {name}" for name in functions)
    lines.append("")
    lines.append("required lines:")
    for label, snippet in REQUIRED_SHELL_BRIDGE_SNIPPETS.items():
        lines.append(f"- {label}: {_line_containing(current, snippet)}")
    lines.append("")
    lines.append("forbidden markers:")
    for label, snippet in FORBIDDEN_SHELL_BRIDGE_SNIPPETS.items():
        marker = "present" if snippet in code_only else "absent"
        lines.append(f"- {label}: {marker}")
    for label, pattern in FORBIDDEN_SHELL_BRIDGE_REGEXES.items():
        marker = "present" if pattern.search(code_only) else "absent"
        lines.append(f"- {label}: {marker}")
    lines.append("")
    return "\n".join(lines)


def load_expected_shell_bridge_fixture(directory: Path | None = None) -> str:
    path = shell_bridge_fixture_path(directory)
    if not path.exists():
        raise FileNotFoundError(f"Missing shell-bridge fixture: {path}")
    return normalize_shell_bridge_text(path.read_text(encoding="utf-8"))


def verify_shell_bridge_fixture(
    directory: Path | None = None,
    *,
    current_text: str | None = None,
) -> None:
    current = render_shell_bridge_profile(current_text)
    path = shell_bridge_fixture_path(directory)
    if not path.exists():
        raise FileNotFoundError(f"Missing shell-bridge fixture: {path}")

    expected = normalize_shell_bridge_text(path.read_text(encoding="utf-8"))
    if expected == current:
        return

    diff = "\n".join(
        difflib.unified_diff(
            expected.splitlines(),
            current.splitlines(),
            fromfile=str(path),
            tofile="scripts/workflow.sh (current profile)",
            lineterm="",
        )
    )
    raise AssertionError(
        "\n".join(
            [
                f"Shell-bridge fixture mismatch: {path}",
                diff or "(diff unavailable)",
            ]
        )
    )


def write_shell_bridge_fixture(directory: Path | None = None) -> Path:
    directory = directory or SHELL_BRIDGE_FIXTURE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = shell_bridge_fixture_path(directory)
    path.write_text(render_shell_bridge_profile(), encoding="utf-8")
    return path
