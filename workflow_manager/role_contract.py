from __future__ import annotations

ROLE_CONTRACT_SCHEMA_VERSION = "1.0.0"
ROLE_CONTRACT_SOURCE = "~/ROLES.md"
ROLE_CONTRACT_SCOPE = "architect-coder-verifier"

CANONICAL_ROLES = ("architect", "coder", "verifier")
RESERVED_ROLES = ("tester",)
SUPPORTED_ROLE_CONTRACT_HARNESSES = (
    "claude-code-cli",
    "opencode",
    "factory-droid",
    "codex-cli",
    "gemini-cli",
    "antigravity-ide",
    "cursor",
)

ROLE_ACTION_CATEGORIES = {
    "architect": {
        "allowed": ("read", "plan", "orchestrate"),
        "forbidden": ("write-code", "write-patches", "detailed-implementation-snippets"),
    },
    "coder": {
        "allowed": ("write-code", "edit-files", "run-required-checks"),
        "forbidden": ("skip-required-checks", "request-human-manual-code", "verify-own-work-as-final"),
    },
    "verifier": {
        "allowed": ("read", "run-checks", "review-diff", "judge-evidence"),
        "forbidden": ("write-code", "write-patches", "approve-without-evidence"),
    },
}

RESERVED_ROLE_POLICY = {
    "tester": {
        "status": "reserved-disabled",
        "activation_policy": "coordinated-global-and-all-harness-update-required",
    },
}


def role_contract_payload() -> dict[str, object]:
    return {
        "schema_version": ROLE_CONTRACT_SCHEMA_VERSION,
        "source": ROLE_CONTRACT_SOURCE,
        "scope": ROLE_CONTRACT_SCOPE,
        "canonical_roles": list(CANONICAL_ROLES),
        "reserved_roles": list(RESERVED_ROLES),
        "supported_harnesses": list(SUPPORTED_ROLE_CONTRACT_HARNESSES),
        "role_action_categories": {
            role: {
                "allowed": list(policy["allowed"]),
                "forbidden": list(policy["forbidden"]),
            }
            for role, policy in ROLE_ACTION_CATEGORIES.items()
        },
        "reserved_role_policy": {
            role: dict(policy)
            for role, policy in RESERVED_ROLE_POLICY.items()
        },
    }


def validate_role_contract_payload(payload: dict[str, object] | None = None) -> dict[str, object]:
    item = role_contract_payload() if payload is None else payload
    expected_keys = {
        "schema_version",
        "source",
        "scope",
        "canonical_roles",
        "reserved_roles",
        "supported_harnesses",
        "role_action_categories",
        "reserved_role_policy",
    }
    if set(item) != expected_keys:
        raise ValueError("Role contract payload keys drifted.")
    if item["schema_version"] != ROLE_CONTRACT_SCHEMA_VERSION:
        raise ValueError("Role contract schema version drifted.")
    if tuple(item["canonical_roles"]) != CANONICAL_ROLES:
        raise ValueError("Canonical role names drifted.")
    if tuple(item["reserved_roles"]) != RESERVED_ROLES:
        raise ValueError("Reserved role names drifted.")
    if tuple(item["supported_harnesses"]) != SUPPORTED_ROLE_CONTRACT_HARNESSES:
        raise ValueError("Supported role-contract harnesses drifted.")
    action_categories = item["role_action_categories"]
    if not isinstance(action_categories, dict):
        raise ValueError("Role action categories must be an object.")
    if set(action_categories) != set(CANONICAL_ROLES):
        raise ValueError("Role action category names drifted from canonical roles.")
    for role in CANONICAL_ROLES:
        policy = action_categories[role]
        if not isinstance(policy, dict) or set(policy) != {"allowed", "forbidden"}:
            raise ValueError(f"Role action policy for `{role}` drifted.")
        allowed = policy["allowed"]
        forbidden = policy["forbidden"]
        if not isinstance(allowed, list) or not all(isinstance(item, str) for item in allowed):
            raise ValueError(f"Allowed action categories for `{role}` must be strings.")
        if not isinstance(forbidden, list) or not all(isinstance(item, str) for item in forbidden):
            raise ValueError(f"Forbidden action categories for `{role}` must be strings.")
        if not allowed or not forbidden:
            raise ValueError(f"Role action policy for `{role}` must not be empty.")
    reserved_policy = item["reserved_role_policy"]
    if not isinstance(reserved_policy, dict) or set(reserved_policy) != set(RESERVED_ROLES):
        raise ValueError("Reserved role policy drifted from reserved roles.")
    for role in RESERVED_ROLES:
        policy = reserved_policy[role]
        if not isinstance(policy, dict):
            raise ValueError(f"Reserved role policy for `{role}` must be an object.")
        if policy.get("status") != "reserved-disabled":
            raise ValueError(f"Reserved role `{role}` must stay disabled.")
    return item
