from __future__ import annotations

import json
from pathlib import Path

from workflow_manager import cli as workflow_cli


EXPECTED_DROID_ADAPTERS = {
    ".factory/droids/architect.md": {
        "name": "architect",
        "role": "Architect",
        "droid_type": "Product",
        "model": "inherit",
        "tools": "read-only",
    },
    ".factory/droids/coder.md": {
        "name": "coder",
        "role": "Coder",
        "droid_type": "Code",
        "model": "inherit",
        "tools": '["Read", "LS", "Grep", "Glob", "Create", "Edit", "ApplyPatch", "Execute"]',
    },
    ".factory/droids/verifier.md": {
        "name": "verifier",
        "role": "Verifier",
        "droid_type": "Reliability",
        "model": "inherit",
        "tools": '["Read", "LS", "Grep", "Glob", "Execute"]',
    },
}
EXPECTED_DROID_ADAPTER_LOCK_KEYS = (
    "droid_type",
    "format",
    "full_checksum",
    "model",
    "name",
    "role",
    "tools",
)
FORBIDDEN_DROID_ADAPTER_SNIPPETS = (
    "The Architect must:",
    "The Coder must:",
    "The Verifier must:",
    "Knowledge",
    "Tutorial",
    "DASHSCOPE_API_KEY",
    "Authorization:",
    "BEGIN PRIVATE" " KEY",
)


def verify_droid_adapter_registry() -> dict[str, dict[str, str]]:
    registry = workflow_cli.MANAGED_DROID_ADAPTERS
    if set(registry) != set(EXPECTED_DROID_ADAPTERS):
        raise AssertionError("Managed Factory Droid adapter registry paths drifted.")
    for relative_path, expected in EXPECTED_DROID_ADAPTERS.items():
        adapter = registry[relative_path]
        for key, value in expected.items():
            if adapter.get(key) != value:
                raise AssertionError(f"Managed Factory Droid adapter `{relative_path}` field `{key}` drifted.")
        if not adapter.get("description"):
            raise AssertionError(f"Managed Factory Droid adapter `{relative_path}` must include a description.")
    return registry


def verify_droid_adapter_text(relative_path: str, text: str) -> dict[str, str]:
    expected = EXPECTED_DROID_ADAPTERS[relative_path]
    parsed = workflow_cli.parse_generated_droid_adapter(text)
    if parsed is None:
        raise AssertionError(f"`{relative_path}` is not a generated Factory Droid adapter.")
    for key in ("name", "model", "tools"):
        if parsed[key] != expected[key]:
            raise AssertionError(f"`{relative_path}` frontmatter `{key}` drifted.")
    if "workflow-generated:version=workflow-managed-v1;tool=factory-droid;source=ROLES.md" not in text:
        raise AssertionError(f"`{relative_path}` is missing the workflow-generated Factory Droid marker.")
    if f"Factory Droid type assignment: {expected['droid_type']}" not in text:
        raise AssertionError(f"`{relative_path}` must state the fixed Factory Droid type assignment.")
    if "Canonical role contract: `~/ROLES.md`" not in text:
        raise AssertionError(f"`{relative_path}` must point at the canonical global role contract.")
    if "Workflow-manager local mapping: `ROLES.md`" not in text:
        raise AssertionError(f"`{relative_path}` must point at the workflow-manager local role mapping.")
    if "must not copy or replace the role definitions" not in text:
        raise AssertionError(f"`{relative_path}` must state the thin-pointer policy.")
    for forbidden in FORBIDDEN_DROID_ADAPTER_SNIPPETS:
        if forbidden in text and forbidden != expected["droid_type"]:
            raise AssertionError(f"`{relative_path}` copied or leaked forbidden snippet `{forbidden}`.")
    return parsed


def verify_rendered_droid_adapters() -> dict[str, dict[str, str]]:
    verify_droid_adapter_registry()
    parsed: dict[str, dict[str, str]] = {}
    for relative_path in EXPECTED_DROID_ADAPTERS:
        rendered = workflow_cli.render_droid_adapter(relative_path)
        parsed[relative_path] = verify_droid_adapter_text(relative_path, rendered)
    return parsed


def verify_droid_adapter_files(repo: Path) -> dict[str, dict[str, str]]:
    parsed: dict[str, dict[str, str]] = {}
    for relative_path in EXPECTED_DROID_ADAPTERS:
        path = repo / relative_path
        if not path.exists():
            raise AssertionError(f"Missing generated Factory Droid adapter `{relative_path}`.")
        text = path.read_text(encoding="utf-8")
        expected_text = workflow_cli.render_droid_adapter(relative_path)
        if text != expected_text:
            raise AssertionError(f"Generated Factory Droid adapter `{relative_path}` drifted from renderer.")
        parsed[relative_path] = verify_droid_adapter_text(relative_path, text)
    return parsed


def verify_droid_adapter_lock(repo: Path) -> dict[str, dict[str, str]]:
    lock_path = repo / ".workflow/mirror-lock.json"
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    adapters = payload.get("droid_adapters")
    if not isinstance(adapters, dict):
        raise AssertionError("Mirror lock must include `droid_adapters`.")
    if set(adapters) != set(EXPECTED_DROID_ADAPTERS):
        raise AssertionError("Mirror lock Factory Droid adapter paths drifted.")
    for relative_path, locked in adapters.items():
        if tuple(locked) != EXPECTED_DROID_ADAPTER_LOCK_KEYS:
            raise AssertionError(f"Mirror lock Factory Droid adapter keys drifted for `{relative_path}`.")
        expected = EXPECTED_DROID_ADAPTERS[relative_path]
        if locked["format"] != workflow_cli.GENERATED_FORMAT_VERSION:
            raise AssertionError(f"Mirror lock Factory Droid adapter format drifted for `{relative_path}`.")
        for key in ("name", "role", "droid_type", "model", "tools"):
            if locked[key] != expected[key]:
                raise AssertionError(f"Mirror lock Factory Droid adapter `{relative_path}` field `{key}` drifted.")
        current = (repo / relative_path).read_text(encoding="utf-8")
        if locked["full_checksum"] != workflow_cli.sha256_text(current):
            raise AssertionError(f"Mirror lock checksum drifted for `{relative_path}`.")
    return adapters
