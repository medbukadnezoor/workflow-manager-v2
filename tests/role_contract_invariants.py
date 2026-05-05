from __future__ import annotations

from pathlib import Path

from workflow_manager.role_contract import (
    CANONICAL_ROLES,
    RESERVED_ROLES,
    ROLE_ACTION_CATEGORIES,
    ROLE_CONTRACT_SCHEMA_VERSION,
    ROLE_CONTRACT_SOURCE,
    SUPPORTED_ROLE_CONTRACT_HARNESSES,
    role_contract_payload,
    validate_role_contract_payload,
)


EXPECTED_ROLE_CONTRACT_SCHEMA_VERSION = "1.0.0"
EXPECTED_CANONICAL_ROLES = ("architect", "coder", "verifier")
EXPECTED_RESERVED_ROLES = ("tester",)
EXPECTED_SUPPORTED_HARNESSES = (
    "claude-code-cli",
    "opencode",
    "factory-droid",
    "codex-cli",
    "gemini-cli",
    "antigravity-ide",
    "cursor",
)
EXPECTED_ROLE_CONTRACT_PAYLOAD_KEYS = (
    "schema_version",
    "source",
    "scope",
    "canonical_roles",
    "reserved_roles",
    "supported_harnesses",
    "role_action_categories",
    "reserved_role_policy",
)
EXPECTED_ROLE_ACTION_POLICY_KEYS = ("allowed", "forbidden")


def verify_role_contract_helper() -> dict[str, object]:
    payload = validate_role_contract_payload(role_contract_payload())
    if ROLE_CONTRACT_SCHEMA_VERSION != EXPECTED_ROLE_CONTRACT_SCHEMA_VERSION:
        raise AssertionError("Role contract schema version drifted.")
    if tuple(CANONICAL_ROLES) != EXPECTED_CANONICAL_ROLES:
        raise AssertionError("Canonical role names drifted.")
    if tuple(RESERVED_ROLES) != EXPECTED_RESERVED_ROLES:
        raise AssertionError("Reserved role names drifted.")
    if tuple(SUPPORTED_ROLE_CONTRACT_HARNESSES) != EXPECTED_SUPPORTED_HARNESSES:
        raise AssertionError("Supported role-contract harness list drifted.")
    if tuple(payload) != EXPECTED_ROLE_CONTRACT_PAYLOAD_KEYS:
        raise AssertionError("Role contract payload key order drifted.")
    if payload["source"] != ROLE_CONTRACT_SOURCE or payload["source"] != "~/ROLES.md":
        raise AssertionError("Role contract helper must point at `~/ROLES.md`.")
    for role in EXPECTED_CANONICAL_ROLES:
        policy = ROLE_ACTION_CATEGORIES.get(role)
        if not isinstance(policy, dict):
            raise AssertionError(f"Missing action policy for `{role}`.")
        if tuple(policy) != EXPECTED_ROLE_ACTION_POLICY_KEYS:
            raise AssertionError(f"Action policy keys drifted for `{role}`.")
        if not policy["allowed"] or not policy["forbidden"]:
            raise AssertionError(f"Action policy for `{role}` must not be empty.")
    return payload


def verify_global_roles_doc(global_roles_path: Path | None = None) -> str:
    path = global_roles_path or (Path.home() / "ROLES.md")
    text = path.read_text(encoding="utf-8")
    for heading in ("### Architect", "### Coder", "### Verifier"):
        if heading not in text:
            raise AssertionError(f"Global `~/ROLES.md` is missing `{heading}`.")
    if "Reserved 4th-role slot" not in text or "Tester" not in text:
        raise AssertionError("Global `~/ROLES.md` must preserve the reserved Tester slot.")
    if "must not be added to a single harness in isolation" not in text:
        raise AssertionError("Global `~/ROLES.md` must preserve coordinated Tester activation policy.")
    return text


def verify_local_roles_pointer(local_roles_path: Path) -> str:
    text = local_roles_path.read_text(encoding="utf-8")
    if "`~/ROLES.md`" not in text:
        raise AssertionError("Local `ROLES.md` must point to `~/ROLES.md`.")
    for forbidden_heading in ("### Architect", "### Coder", "### Verifier"):
        if forbidden_heading in text:
            raise AssertionError("Local `ROLES.md` must not redefine canonical role prose.")
    for harness in ("Claude Code CLI", "OpenCode", "Factory Droid", "Codex CLI", "Gemini CLI", "Antigravity IDE", "Cursor"):
        if harness not in text:
            raise AssertionError(f"Local `ROLES.md` mapping table is missing {harness}.")
    if "Architect → Product" not in text or "Coder → Code" not in text or "Verifier → Reliability" not in text:
        raise AssertionError("Local `ROLES.md` must preserve the fixed Factory Droid mapping.")
    return text


def verify_role_contract_no_leak_text(text: str) -> None:
    forbidden = (
        "DASHSCOPE_API_KEY",
        "Authorization:",
        "BEGIN PRIVATE" " KEY",
        "sk-",
        "migration_write_instructions",
        "hidden reasoning",
    )
    lower_text = text.lower()
    for token in forbidden:
        if token.lower() in lower_text:
            raise AssertionError(f"Role contract surface leaked forbidden token `{token}`.")
