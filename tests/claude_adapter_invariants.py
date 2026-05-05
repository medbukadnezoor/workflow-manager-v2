from __future__ import annotations

import json
from pathlib import Path

from workflow_manager import cli as workflow_cli


EXPECTED_CLAUDE_ADAPTERS = {
    ".claude/agents/architect.md": {
        "name": "architect",
        "role": "Architect",
        "tools": "Read, Grep, Glob, LS",
    },
    ".claude/agents/coder.md": {
        "name": "coder",
        "role": "Coder",
        "tools": "Read, Grep, Glob, LS, Edit, MultiEdit, Write, Bash",
    },
    ".claude/agents/verifier.md": {
        "name": "verifier",
        "role": "Verifier",
        "tools": "Read, Grep, Glob, LS, Bash",
    },
}
EXPECTED_CLAUDE_ADAPTER_LOCK_KEYS = ("format", "full_checksum", "name", "role", "tools")
FORBIDDEN_CLAUDE_ADAPTER_SNIPPETS = (
    "The Architect must:",
    "The Coder must:",
    "The Verifier must:",
    "write all code",
    "stay read-only",
    "DASHSCOPE_API_KEY",
    "Authorization:",
    "BEGIN PRIVATE" " KEY",
)


def verify_claude_adapter_registry() -> dict[str, dict[str, str]]:
    registry = workflow_cli.MANAGED_CLAUDE_ADAPTERS
    if set(registry) != set(EXPECTED_CLAUDE_ADAPTERS):
        raise AssertionError("Managed Claude adapter registry paths drifted.")
    for relative_path, expected in EXPECTED_CLAUDE_ADAPTERS.items():
        adapter = registry[relative_path]
        for key, value in expected.items():
            if adapter.get(key) != value:
                raise AssertionError(f"Managed Claude adapter `{relative_path}` field `{key}` drifted.")
        if not adapter.get("description"):
            raise AssertionError(f"Managed Claude adapter `{relative_path}` must include a description.")
    return registry


def verify_claude_adapter_text(relative_path: str, text: str) -> dict[str, str]:
    expected = EXPECTED_CLAUDE_ADAPTERS[relative_path]
    parsed = workflow_cli.parse_generated_claude_adapter(text)
    if parsed is None:
        raise AssertionError(f"`{relative_path}` is not a generated Claude adapter.")
    if parsed["name"] != expected["name"]:
        raise AssertionError(f"`{relative_path}` frontmatter name drifted.")
    if parsed["tools"] != expected["tools"]:
        raise AssertionError(f"`{relative_path}` frontmatter tools drifted.")
    if "workflow-generated:version=workflow-managed-v1;tool=claude-subagent;source=ROLES.md" not in text:
        raise AssertionError(f"`{relative_path}` is missing the workflow-generated Claude marker.")
    if "Canonical role contract: `~/ROLES.md`" not in text:
        raise AssertionError(f"`{relative_path}` must point at the canonical global role contract.")
    if "Workflow-manager local mapping: `ROLES.md`" not in text:
        raise AssertionError(f"`{relative_path}` must point at the workflow-manager local role mapping.")
    if "must not copy or replace the role definitions" not in text:
        raise AssertionError(f"`{relative_path}` must state the thin-pointer policy.")
    for forbidden in FORBIDDEN_CLAUDE_ADAPTER_SNIPPETS:
        if forbidden in text:
            raise AssertionError(f"`{relative_path}` copied or leaked forbidden snippet `{forbidden}`.")
    return parsed


def verify_rendered_claude_adapters() -> dict[str, dict[str, str]]:
    verify_claude_adapter_registry()
    parsed: dict[str, dict[str, str]] = {}
    for relative_path in EXPECTED_CLAUDE_ADAPTERS:
        rendered = workflow_cli.render_claude_adapter(relative_path)
        parsed[relative_path] = verify_claude_adapter_text(relative_path, rendered)
    return parsed


def verify_claude_adapter_files(repo: Path) -> dict[str, dict[str, str]]:
    parsed: dict[str, dict[str, str]] = {}
    for relative_path in EXPECTED_CLAUDE_ADAPTERS:
        path = repo / relative_path
        if not path.exists():
            raise AssertionError(f"Missing generated Claude adapter `{relative_path}`.")
        text = path.read_text(encoding="utf-8")
        expected_text = workflow_cli.render_claude_adapter(relative_path)
        if text != expected_text:
            raise AssertionError(f"Generated Claude adapter `{relative_path}` drifted from renderer.")
        parsed[relative_path] = verify_claude_adapter_text(relative_path, text)
    return parsed


def verify_claude_adapter_lock(repo: Path) -> dict[str, dict[str, str]]:
    lock_path = repo / ".workflow/mirror-lock.json"
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    adapters = payload.get("claude_adapters")
    if not isinstance(adapters, dict):
        raise AssertionError("Mirror lock must include `claude_adapters`.")
    if set(adapters) != set(EXPECTED_CLAUDE_ADAPTERS):
        raise AssertionError("Mirror lock Claude adapter paths drifted.")
    for relative_path, locked in adapters.items():
        if tuple(locked) != EXPECTED_CLAUDE_ADAPTER_LOCK_KEYS:
            raise AssertionError(f"Mirror lock Claude adapter keys drifted for `{relative_path}`.")
        expected = EXPECTED_CLAUDE_ADAPTERS[relative_path]
        if locked["format"] != workflow_cli.GENERATED_FORMAT_VERSION:
            raise AssertionError(f"Mirror lock Claude adapter format drifted for `{relative_path}`.")
        for key in ("name", "role", "tools"):
            if locked[key] != expected[key]:
                raise AssertionError(f"Mirror lock Claude adapter `{relative_path}` field `{key}` drifted.")
        current = (repo / relative_path).read_text(encoding="utf-8")
        if locked["full_checksum"] != workflow_cli.sha256_text(current):
            raise AssertionError(f"Mirror lock checksum drifted for `{relative_path}`.")
    return adapters
