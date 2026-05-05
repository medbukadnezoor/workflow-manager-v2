from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI_ENTRYPOINT = ROOT / "bin/workflow"

REQUIRED_CLI_ENTRYPOINT_SNIPPETS = {
    "python-shebang": "#!/usr/bin/env python3",
    "path-import": "from pathlib import Path",
    "sys-import": "import sys",
    "repo-root-derivation": "ROOT = Path(__file__).resolve().parent.parent",
    "sys-path-guard": "if str(ROOT) not in sys.path:",
    "sys-path-insert": 'sys.path.insert(0, str(ROOT))',
    "cli-main-import": "from workflow_manager.cli import main",
    "system-exit-main": "raise SystemExit(main())",
}

FORBIDDEN_CLI_ENTRYPOINT_SNIPPETS = {
    "hardcoded-user-project-root": "<private-project-root>",
    "hardcoded-user-research-root": "<private-research-root>",
    "workflow-roots-env": "WORKFLOW_ROOTS",
    "direct-roots-config-logic": ".workflow/roots.json",
    "legacy-scaffold-template": ".ai/context/scaffold-template",
    "shell-startup-edits": "~/.zshrc",
    "managed-shim-logic": "CLAUDE.md",
    "managed-shim-logic-gemini": "GEMINI.md",
    "canonical-contract-logic": "AGENTS.md",
    "hermes-implemented-claim": "Hermes is implemented",
    "dashscope-implemented-claim": "DashScope is integrated",
    "qwen-implemented-claim": "Qwen integration is complete",
    "graphify-implemented-claim": "Graphify is implemented",
    "json-output-implemented-claim": "--json",
    "spec-kit-complete-claim": "full spec-kit fork/preset is implemented",
}


def normalize_cli_entrypoint_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n")
    if not normalized.endswith("\n"):
        normalized += "\n"
    return normalized


def build_current_cli_entrypoint_text(path: Path | None = None) -> str:
    path = path or CLI_ENTRYPOINT
    return normalize_cli_entrypoint_text(path.read_text(encoding="utf-8"))


def verify_cli_entrypoint_invariants(text: str | None = None) -> None:
    current = normalize_cli_entrypoint_text(
        text if text is not None else build_current_cli_entrypoint_text()
    )
    errors: list[str] = []

    for label, snippet in REQUIRED_CLI_ENTRYPOINT_SNIPPETS.items():
        if snippet not in current:
            errors.append(
                f"`bin/workflow` invariant `{label}` is missing snippet: {snippet}"
            )

    for label, snippet in FORBIDDEN_CLI_ENTRYPOINT_SNIPPETS.items():
        if snippet in current:
            errors.append(
                f"`bin/workflow` invariant `{label}` was violated by forbidden snippet: {snippet}"
            )

    if errors:
        raise AssertionError("\n".join(errors))
