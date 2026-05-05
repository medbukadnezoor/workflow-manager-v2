from __future__ import annotations

import json
from pathlib import Path

from workflow_manager import cli as workflow_cli


EXPECTED_OPENCODE_ADAPTERS = {
    ".opencode/agents/architect.md": {
        "role": "Architect",
        "mode": "subagent",
        "permission": {
            "edit": "deny",
            "bash": "deny",
            "webfetch": "deny",
        },
    },
    ".opencode/agents/coder.md": {
        "role": "Coder",
        "mode": "subagent",
        "permission": {
            "edit": "ask",
            "bash": "ask",
            "webfetch": "deny",
        },
    },
    ".opencode/agents/verifier.md": {
        "role": "Verifier",
        "mode": "subagent",
        "permission": {
            "edit": "deny",
            "bash": "ask",
            "webfetch": "deny",
        },
    },
}
EXPECTED_OPENCODE_ADAPTER_LOCK_KEYS = ("format", "full_checksum", "mode", "permission", "role")
FORBIDDEN_OPENCODE_ADAPTER_SNIPPETS = (
    "The Architect must:",
    "The Coder must:",
    "The Verifier must:",
    "write all code",
    "stay read-only",
    "DASHSCOPE_API_KEY",
    "Authorization:",
    "BEGIN PRIVATE" " KEY",
)


def verify_opencode_adapter_registry() -> dict[str, dict[str, object]]:
    registry = workflow_cli.MANAGED_OPENCODE_ADAPTERS
    if set(registry) != set(EXPECTED_OPENCODE_ADAPTERS):
        raise AssertionError("Managed OpenCode adapter registry paths drifted.")
    for relative_path, expected in EXPECTED_OPENCODE_ADAPTERS.items():
        adapter = registry[relative_path]
        for key, value in expected.items():
            if adapter.get(key) != value:
                raise AssertionError(f"Managed OpenCode adapter `{relative_path}` field `{key}` drifted.")
        if not adapter.get("description"):
            raise AssertionError(f"Managed OpenCode adapter `{relative_path}` must include a description.")
    return registry


def verify_opencode_adapter_text(relative_path: str, text: str) -> dict[str, object]:
    expected = EXPECTED_OPENCODE_ADAPTERS[relative_path]
    parsed = workflow_cli.parse_generated_opencode_adapter(text)
    if parsed is None:
        raise AssertionError(f"`{relative_path}` is not a generated OpenCode adapter.")
    if parsed["mode"] != expected["mode"]:
        raise AssertionError(f"`{relative_path}` frontmatter mode drifted.")
    if parsed["permission"] != expected["permission"]:
        raise AssertionError(f"`{relative_path}` frontmatter permission drifted.")
    if "workflow-generated:version=workflow-managed-v1;tool=opencode-agent;source=ROLES.md" not in text:
        raise AssertionError(f"`{relative_path}` is missing the workflow-generated OpenCode marker.")
    if "Canonical role contract: `~/ROLES.md`" not in text:
        raise AssertionError(f"`{relative_path}` must point at the canonical global role contract.")
    if "Workflow-manager local mapping: `ROLES.md`" not in text:
        raise AssertionError(f"`{relative_path}` must point at the workflow-manager local role mapping.")
    if "must not copy or replace the role definitions" not in text:
        raise AssertionError(f"`{relative_path}` must state the thin-pointer policy.")
    if ".opencode/agent/" in text:
        raise AssertionError(f"`{relative_path}` must not preserve the older singular OpenCode agent path.")
    for forbidden in FORBIDDEN_OPENCODE_ADAPTER_SNIPPETS:
        if forbidden in text:
            raise AssertionError(f"`{relative_path}` copied or leaked forbidden snippet `{forbidden}`.")
    return parsed


def verify_rendered_opencode_adapters() -> dict[str, dict[str, object]]:
    verify_opencode_adapter_registry()
    parsed: dict[str, dict[str, object]] = {}
    for relative_path in EXPECTED_OPENCODE_ADAPTERS:
        rendered = workflow_cli.render_opencode_adapter(relative_path)
        parsed[relative_path] = verify_opencode_adapter_text(relative_path, rendered)
    return parsed


def verify_opencode_adapter_files(repo: Path) -> dict[str, dict[str, object]]:
    parsed: dict[str, dict[str, object]] = {}
    for relative_path in EXPECTED_OPENCODE_ADAPTERS:
        path = repo / relative_path
        if not path.exists():
            raise AssertionError(f"Missing generated OpenCode adapter `{relative_path}`.")
        text = path.read_text(encoding="utf-8")
        expected_text = workflow_cli.render_opencode_adapter(relative_path)
        if text != expected_text:
            raise AssertionError(f"Generated OpenCode adapter `{relative_path}` drifted from renderer.")
        parsed[relative_path] = verify_opencode_adapter_text(relative_path, text)
    return parsed


def verify_opencode_adapter_lock(repo: Path) -> dict[str, dict[str, object]]:
    lock_path = repo / ".workflow/mirror-lock.json"
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    adapters = payload.get("opencode_adapters")
    if not isinstance(adapters, dict):
        raise AssertionError("Mirror lock must include `opencode_adapters`.")
    if set(adapters) != set(EXPECTED_OPENCODE_ADAPTERS):
        raise AssertionError("Mirror lock OpenCode adapter paths drifted.")
    for relative_path, locked in adapters.items():
        if tuple(locked) != EXPECTED_OPENCODE_ADAPTER_LOCK_KEYS:
            raise AssertionError(f"Mirror lock OpenCode adapter keys drifted for `{relative_path}`.")
        expected = EXPECTED_OPENCODE_ADAPTERS[relative_path]
        if locked["format"] != workflow_cli.GENERATED_FORMAT_VERSION:
            raise AssertionError(f"Mirror lock OpenCode adapter format drifted for `{relative_path}`.")
        for key in ("mode", "permission", "role"):
            if locked[key] != expected[key]:
                raise AssertionError(f"Mirror lock OpenCode adapter `{relative_path}` field `{key}` drifted.")
        current = (repo / relative_path).read_text(encoding="utf-8")
        if locked["full_checksum"] != workflow_cli.sha256_text(current):
            raise AssertionError(f"Mirror lock checksum drifted for `{relative_path}`.")
    return adapters
