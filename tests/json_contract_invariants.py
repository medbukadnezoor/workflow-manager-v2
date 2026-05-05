from __future__ import annotations

import json
from pathlib import Path


EXPECTED_JSON_CONTRACT_SCHEMA_VERSION = "1.2.0"
JSON_CONTRACT_SURFACES = (
    "status",
    "doctor",
    "doctor_write_report",
    "roots",
)
JSON_CONTRACT_BREAKING_CHANGE_CATEGORIES = (
    "remove-governed-top-level-field",
    "rename-governed-top-level-field",
    "change-governed-field-type",
    "remove-governed-health-subsystem",
    "change-pass-warning-fail-vocabulary",
    "change-doctor-exit-code-semantics",
)
JSON_CONTRACT_ADDITIVE_CHANGE_CATEGORIES = (
    "add-governed-top-level-field",
    "add-governed-nested-field",
    "add-governed-health-subsystem",
)
JSON_CONTRACT_RESERVED_ADDITIVE_ENABLEMENT_STEPS = (
    "bump-shared-schema-minor-version",
    "update-additive-policy",
    "update-json-contract-invariants",
    "update-focused-json-tests",
    "update-repo-docs",
)
EXPECTED_JSON_CONTRACT_POLICY_KEYS = (
    "shared_schema_version",
    "versioning_mode",
    "versioning_scheme",
    "all_surfaces_share_version",
    "command_specific_versioning",
    "patch_change_rule",
    "minor_change_rule",
    "major_change_rule",
    "additive_keys_allowed",
    "breaking_changes_require_version_bump",
    "coordinated_updates_required",
    "breaking_change_categories",
    "additive_change_categories",
)
EXPECTED_JSON_CONTRACT_RESERVED_ADDITIVE_POLICY_KEYS = (
    "status",
    "enabled_by_default",
    "current_schema_version",
    "future_minor_version_path",
    "minor_version_bump_required",
    "all_surfaces_must_move_together",
    "command_specific_additions_allowed",
    "new_fields_must_be_optional_for_consumers",
    "new_fields_must_not_change_existing_field_meaning",
    "new_fields_must_not_change_existing_field_types",
    "new_fields_must_not_change_status_vocabulary",
    "new_fields_must_not_change_doctor_exit_code_semantics",
    "consumer_unknown_field_rule_when_enabled",
    "required_updates_before_enablement",
)
JSON_CONTRACT_EVOLUTION_POLICY = {
    "shared_schema_version": EXPECTED_JSON_CONTRACT_SCHEMA_VERSION,
    "versioning_mode": "shared",
    "versioning_scheme": "semver",
    "all_surfaces_share_version": True,
    "command_specific_versioning": False,
    "patch_change_rule": "no-governed-contract-change",
    "minor_change_rule": "reserved-for-future-additive-compatible-changes",
    "major_change_rule": "required-for-breaking-contract-changes",
    "additive_keys_allowed": False,
    "breaking_changes_require_version_bump": True,
    "coordinated_updates_required": True,
    "breaking_change_categories": JSON_CONTRACT_BREAKING_CHANGE_CATEGORIES,
    "additive_change_categories": JSON_CONTRACT_ADDITIVE_CHANGE_CATEGORIES,
}
JSON_CONTRACT_RESERVED_ADDITIVE_POLICY = {
    "status": "reserved-not-enabled",
    "enabled_by_default": False,
    "current_schema_version": EXPECTED_JSON_CONTRACT_SCHEMA_VERSION,
    "future_minor_version_path": "reserved-shared-minor-version-bump",
    "minor_version_bump_required": True,
    "all_surfaces_must_move_together": True,
    "command_specific_additions_allowed": False,
    "new_fields_must_be_optional_for_consumers": True,
    "new_fields_must_not_change_existing_field_meaning": True,
    "new_fields_must_not_change_existing_field_types": True,
    "new_fields_must_not_change_status_vocabulary": True,
    "new_fields_must_not_change_doctor_exit_code_semantics": True,
    "consumer_unknown_field_rule_when_enabled": (
        "ignore-unknown-optional-fields-only-after-an-explicit-shared-minor-version-upgrade"
    ),
    "required_updates_before_enablement": JSON_CONTRACT_RESERVED_ADDITIVE_ENABLEMENT_STEPS,
}
SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION = "1.3.0"
JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD = "compatibility_example"
EXPECTED_JSON_CONTRACT_COMPATIBILITY_EXAMPLE_KEYS = (
    "status",
    "shared_minor_version",
    "optional_for_consumers",
    "live_contract_unchanged",
    "consumer_unknown_field_rule",
)
JSON_CONTRACT_CONSUMER_EXAMPLE_MODE = "example-only-pre-hermes-tolerant-shared-minor"
EXPECTED_JSON_CONTRACT_CONSUMER_EXAMPLE_KEYS = (
    "surface",
    "schema_version",
    "consumer_mode",
    "known_payload",
    "tolerated_optional_fields",
    "preserved_optional_fields",
)
EXPECTED_JSON_CONTRACT_CHANGE_ASSESSMENT_KEYS = (
    "classification",
    "required_version_change",
    "requires_policy_update",
    "all_surfaces_must_move_together",
    "consumer_guidance",
    "reason",
)

EXPECTED_STATUS_KEYS = (
    "schema_version",
    "command",
    "repo_path",
    "classification",
    "project",
    "continuity",
    "migration",
    "doctor_summary",
    "health_overview",
    "health",
    "git",
    "notes",
)

EXPECTED_DOCTOR_KEYS = (
    "schema_version",
    "command",
    "repo_path",
    "classification",
    "result_status",
    "passed",
    "wrote_report",
    "drift_report_path",
    "health_overview",
    "health",
    "notes",
    "findings",
    "errors",
    "warnings",
)

EXPECTED_ROOTS_KEYS = (
    "schema_version",
    "command",
    "validate_requested",
    "passed_validation",
    "health",
)

EXPECTED_PROJECT_KEYS = (
    "name",
    "what_this_project_is",
    "current_task",
    "next_step",
    "manifest_scaffold",
)

EXPECTED_CONTINUITY_KEYS = ("sources",)
REQUIRED_CONTINUITY_SOURCE_KEYS = (
    "legacy_preserved",
    "handoff",
    "active_state",
    "progress",
    "session_log",
)
OPTIONAL_CONTINUITY_SOURCE_KEYS = (
    "legacy_handoff",
    "legacy_state",
    "legacy_task",
    "legacy_session_log",
)

EXPECTED_MIGRATION_KEYS = (
    "summary",
    "status",
    "phase",
    "legacy_preserved",
    "branch",
)

EXPECTED_DOCTOR_SUMMARY_KEYS = ("summary",)
EXPECTED_HEALTH_OVERVIEW_KEYS = (
    "overall_status",
    "summary",
    "subsystems",
    "sync_needed",
    "default_root_operations_safe",
    "pre_hermes_readiness",
)
EXPECTED_HEALTH_SUBSYSTEM_KEYS = (
    "command_help_docs",
    "manifest",
    "mirror_lock_shim",
    "memory",
    "continuity_state",
    "roots",
    "role_contract",
    "docs_health",
)

EXPECTED_HEALTH_KEYS = EXPECTED_HEALTH_SUBSYSTEM_KEYS
EXPECTED_COMMAND_DOCS_KEYS = ("status", "summary", "path", "entries", "issues")
EXPECTED_MANIFEST_KEYS = ("status", "summary", "path", "issues")
EXPECTED_MIRROR_KEYS = ("status", "summary", "path", "sync_needed", "issues")
EXPECTED_MEMORY_KEYS = ("status", "summary", "path", "entries", "issues")
EXPECTED_CONTINUITY_STATE_KEYS = ("status", "summary", "path", "entries", "issues")
EXPECTED_ROOTS_HEALTH_KEYS = (
    "status",
    "summary",
    "config_path",
    "source_label",
    "default_root_operations_safe",
    "roots",
    "usable_roots",
    "entries",
    "issues",
)
EXPECTED_ROLE_CONTRACT_HEALTH_KEYS = (
    "status",
    "summary",
    "path",
    "canonical_roles",
    "reserved_roles",
    "supported_harnesses",
    "issues",
)
EXPECTED_DOCS_HEALTH_KEYS = ("status", "summary", "path", "entries", "issues")
EXPECTED_DOCS_HEALTH_ENTRY_KEYS = ("relative_path", "status", "line_count", "budget", "summary")

EXPECTED_ISSUE_KEYS = ("level", "message")
EXPECTED_COMMAND_DOCS_ENTRY_KEYS = ("surface", "status", "summary")
EXPECTED_MEMORY_ENTRY_KEYS = ("relative_path", "status", "summary")
EXPECTED_ROOTS_ENTRY_KEYS = ("path", "status")
EXPECTED_FINDING_KEYS = ("surface", "level", "message", "text")

ALLOWED_HEALTH_STATUSES = {"pass", "warning", "fail"}
ALLOWED_ISSUE_LEVELS = {"warning", "error"}
ALLOWED_FINDING_SURFACES = {
    "repo",
    "command_help_docs",
    "manifest",
    "mirror_lock_shim",
    "memory",
    "continuity_state",
    "roots",
    "role_contract",
    "docs_health",
}
ALLOWED_PRE_HERMES_READINESS = {
    "blocked",
    "needs-review",
    "pre-hermes-foundation-ready",
}


def _assert_json_object(label: str, payload: object) -> dict:
    if not isinstance(payload, dict):
        raise AssertionError(f"`{label}` must be a JSON object.")
    return payload


def _assert_exact_keys(label: str, payload: dict, expected_keys: tuple[str, ...]) -> None:
    actual = set(payload.keys())
    expected = set(expected_keys)
    if actual == expected:
        return

    parts = [f"`{label}` keys drifted."]
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        parts.append(f"Missing keys: {missing}.")
    if unexpected:
        parts.append(f"Unexpected keys: {unexpected}.")
        if not JSON_CONTRACT_EVOLUTION_POLICY["additive_keys_allowed"]:
            parts.append(
                "Additive governed keys are intentionally gated until the JSON schema policy, invariant tests, and reserved shared minor-version path are updated together."
            )
    raise AssertionError(" ".join(parts))


def _assert_allowed_keys(
    label: str,
    payload: dict,
    *,
    required_keys: tuple[str, ...],
    optional_keys: tuple[str, ...] = (),
) -> None:
    actual = set(payload.keys())
    required = set(required_keys)
    allowed = required | set(optional_keys)
    missing = sorted(required - actual)
    unexpected = sorted(actual - allowed)
    if not missing and not unexpected:
        return

    parts = [f"`{label}` keys drifted."]
    if missing:
        parts.append(f"Missing keys: {missing}.")
    if unexpected:
        parts.append(f"Unexpected keys: {unexpected}.")
    raise AssertionError(" ".join(parts))


def _assert_string(label: str, value: object) -> None:
    if not isinstance(value, str):
        raise AssertionError(f"`{label}` must be a string.")


def _assert_optional_string(label: str, value: object) -> None:
    if value is not None and not isinstance(value, str):
        raise AssertionError(f"`{label}` must be a string or null.")


def _assert_bool(label: str, value: object) -> None:
    if not isinstance(value, bool):
        raise AssertionError(f"`{label}` must be a boolean.")


def _assert_int(label: str, value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise AssertionError(f"`{label}` must be an integer.")


def _assert_string_list(label: str, value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise AssertionError(f"`{label}` must be a list of strings.")
    return value


def _assert_string_sequence(label: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) for item in value):
        raise AssertionError(f"`{label}` must be a list or tuple of strings.")
    return tuple(value)


def _assert_status(label: str, value: object) -> str:
    _assert_string(label, value)
    if value not in ALLOWED_HEALTH_STATUSES:
        raise AssertionError(f"`{label}` must be one of {sorted(ALLOWED_HEALTH_STATUSES)}.")
    return value


def verify_json_contract_evolution_policy() -> dict:
    policy = JSON_CONTRACT_EVOLUTION_POLICY
    _assert_exact_keys(
        "JSON contract evolution policy",
        policy,
        EXPECTED_JSON_CONTRACT_POLICY_KEYS,
    )
    _assert_string(
        "JSON contract evolution policy.shared_schema_version",
        policy["shared_schema_version"],
    )
    if policy["shared_schema_version"] != EXPECTED_JSON_CONTRACT_SCHEMA_VERSION:
        raise AssertionError(
            "The JSON contract evolution policy drifted from the governed shared schema version."
        )
    if policy["versioning_mode"] != "shared":
        raise AssertionError("JSON contract versioning mode must remain `shared` for all governed commands.")
    if policy["versioning_scheme"] != "semver":
        raise AssertionError("JSON contract versioning scheme must remain `semver`.")
    _assert_bool(
        "JSON contract evolution policy.all_surfaces_share_version",
        policy["all_surfaces_share_version"],
    )
    if not policy["all_surfaces_share_version"]:
        raise AssertionError("All governed JSON commands must share one schema version for now.")
    _assert_bool(
        "JSON contract evolution policy.command_specific_versioning",
        policy["command_specific_versioning"],
    )
    if policy["command_specific_versioning"]:
        raise AssertionError("Command-specific JSON schema versioning is intentionally not used in this slice.")
    _assert_string("JSON contract evolution policy.patch_change_rule", policy["patch_change_rule"])
    if policy["patch_change_rule"] != "no-governed-contract-change":
        raise AssertionError(
            "Patch JSON schema changes must remain reserved for non-contract implementation or documentation work."
        )
    _assert_string("JSON contract evolution policy.minor_change_rule", policy["minor_change_rule"])
    if policy["minor_change_rule"] != "reserved-for-future-additive-compatible-changes":
        raise AssertionError(
            "Minor JSON schema changes must remain reserved for future additive compatible work."
        )
    _assert_string("JSON contract evolution policy.major_change_rule", policy["major_change_rule"])
    if policy["major_change_rule"] != "required-for-breaking-contract-changes":
        raise AssertionError("Breaking JSON schema changes must require a major version bump.")
    _assert_bool(
        "JSON contract evolution policy.additive_keys_allowed",
        policy["additive_keys_allowed"],
    )
    if policy["additive_keys_allowed"]:
        raise AssertionError("Additive governed JSON keys are intentionally gated for now.")
    _assert_bool(
        "JSON contract evolution policy.breaking_changes_require_version_bump",
        policy["breaking_changes_require_version_bump"],
    )
    if not policy["breaking_changes_require_version_bump"]:
        raise AssertionError("Breaking JSON contract changes must require a version bump.")
    _assert_bool(
        "JSON contract evolution policy.coordinated_updates_required",
        policy["coordinated_updates_required"],
    )
    if not policy["coordinated_updates_required"]:
        raise AssertionError("Intentional JSON contract changes must require coordinated policy, test, and doc updates.")
    if _assert_string_sequence(
        "JSON contract evolution policy.breaking_change_categories",
        policy["breaking_change_categories"],
    ) != JSON_CONTRACT_BREAKING_CHANGE_CATEGORIES:
        raise AssertionError("Breaking JSON contract categories drifted from the governed baseline.")
    if _assert_string_sequence(
        "JSON contract evolution policy.additive_change_categories",
        policy["additive_change_categories"],
    ) != JSON_CONTRACT_ADDITIVE_CHANGE_CATEGORIES:
        raise AssertionError("Additive JSON contract categories drifted from the governed baseline.")
    return policy


def verify_json_contract_reserved_additive_policy() -> dict:
    evolution_policy = verify_json_contract_evolution_policy()
    policy = JSON_CONTRACT_RESERVED_ADDITIVE_POLICY
    _assert_exact_keys(
        "JSON contract reserved additive policy",
        policy,
        EXPECTED_JSON_CONTRACT_RESERVED_ADDITIVE_POLICY_KEYS,
    )
    _assert_string("JSON contract reserved additive policy.status", policy["status"])
    if policy["status"] != "reserved-not-enabled":
        raise AssertionError("Reserved additive JSON policy must remain `reserved-not-enabled` for now.")
    _assert_bool(
        "JSON contract reserved additive policy.enabled_by_default",
        policy["enabled_by_default"],
    )
    if policy["enabled_by_default"]:
        raise AssertionError("Reserved additive JSON policy must not enable additive keys by default.")
    _assert_string(
        "JSON contract reserved additive policy.current_schema_version",
        policy["current_schema_version"],
    )
    if policy["current_schema_version"] != evolution_policy["shared_schema_version"]:
        raise AssertionError(
            "Reserved additive JSON policy drifted from the governed shared schema version."
        )
    _assert_string(
        "JSON contract reserved additive policy.future_minor_version_path",
        policy["future_minor_version_path"],
    )
    if policy["future_minor_version_path"] != "reserved-shared-minor-version-bump":
        raise AssertionError(
            "Reserved additive JSON policy must keep the shared minor-version path explicit."
        )
    _assert_bool(
        "JSON contract reserved additive policy.minor_version_bump_required",
        policy["minor_version_bump_required"],
    )
    if not policy["minor_version_bump_required"]:
        raise AssertionError("Reserved additive JSON changes must require a minor version bump.")
    _assert_bool(
        "JSON contract reserved additive policy.all_surfaces_must_move_together",
        policy["all_surfaces_must_move_together"],
    )
    if not policy["all_surfaces_must_move_together"]:
        raise AssertionError("Reserved additive JSON changes must move all governed commands together.")
    _assert_bool(
        "JSON contract reserved additive policy.command_specific_additions_allowed",
        policy["command_specific_additions_allowed"],
    )
    if policy["command_specific_additions_allowed"]:
        raise AssertionError("Command-specific additive JSON fields are intentionally not allowed.")
    _assert_bool(
        "JSON contract reserved additive policy.new_fields_must_be_optional_for_consumers",
        policy["new_fields_must_be_optional_for_consumers"],
    )
    if not policy["new_fields_must_be_optional_for_consumers"]:
        raise AssertionError("Reserved additive JSON fields must remain optional for consumers.")
    _assert_bool(
        "JSON contract reserved additive policy.new_fields_must_not_change_existing_field_meaning",
        policy["new_fields_must_not_change_existing_field_meaning"],
    )
    if not policy["new_fields_must_not_change_existing_field_meaning"]:
        raise AssertionError("Reserved additive JSON fields must not change the meaning of existing fields.")
    _assert_bool(
        "JSON contract reserved additive policy.new_fields_must_not_change_existing_field_types",
        policy["new_fields_must_not_change_existing_field_types"],
    )
    if not policy["new_fields_must_not_change_existing_field_types"]:
        raise AssertionError("Reserved additive JSON fields must not change existing field types.")
    _assert_bool(
        "JSON contract reserved additive policy.new_fields_must_not_change_status_vocabulary",
        policy["new_fields_must_not_change_status_vocabulary"],
    )
    if not policy["new_fields_must_not_change_status_vocabulary"]:
        raise AssertionError("Reserved additive JSON fields must not change pass/warning/fail vocabulary.")
    _assert_bool(
        "JSON contract reserved additive policy.new_fields_must_not_change_doctor_exit_code_semantics",
        policy["new_fields_must_not_change_doctor_exit_code_semantics"],
    )
    if not policy["new_fields_must_not_change_doctor_exit_code_semantics"]:
        raise AssertionError("Reserved additive JSON fields must not change doctor exit semantics.")
    _assert_string(
        "JSON contract reserved additive policy.consumer_unknown_field_rule_when_enabled",
        policy["consumer_unknown_field_rule_when_enabled"],
    )
    if (
        policy["consumer_unknown_field_rule_when_enabled"]
        != "ignore-unknown-optional-fields-only-after-an-explicit-shared-minor-version-upgrade"
    ):
        raise AssertionError(
            "Reserved additive JSON consumer guidance drifted from the governed future minor-version rule."
        )
    if _assert_string_sequence(
        "JSON contract reserved additive policy.required_updates_before_enablement",
        policy["required_updates_before_enablement"],
    ) != JSON_CONTRACT_RESERVED_ADDITIVE_ENABLEMENT_STEPS:
        raise AssertionError("Reserved additive JSON enablement steps drifted from the governed baseline.")
    return policy


def assess_json_contract_change(
    change_category: str,
    *,
    command_specific_addition: bool = False,
    changes_existing_field_type: bool = False,
    changes_existing_field_meaning: bool = False,
    changes_status_vocabulary: bool = False,
    changes_doctor_exit_code_semantics: bool = False,
) -> dict:
    verify_json_contract_evolution_policy()
    additive_policy = verify_json_contract_reserved_additive_policy()
    all_categories = set(JSON_CONTRACT_BREAKING_CHANGE_CATEGORIES) | set(
        JSON_CONTRACT_ADDITIVE_CHANGE_CATEGORIES
    )
    if change_category not in all_categories:
        raise AssertionError(f"Unknown JSON contract change category `{change_category}`.")

    reasons: list[str] = []
    if change_category in JSON_CONTRACT_BREAKING_CHANGE_CATEGORIES:
        reasons.append(f"`{change_category}` is explicitly governed as breaking.")
    if changes_existing_field_type:
        reasons.append("Changing the type of an existing governed field is breaking.")
    if changes_existing_field_meaning:
        reasons.append("Changing the meaning of an existing governed field is breaking.")
    if changes_status_vocabulary:
        reasons.append("Changing pass/warning/fail vocabulary is breaking.")
    if changes_doctor_exit_code_semantics:
        reasons.append("Changing doctor exit-code semantics is breaking.")
    if reasons:
        return {
            "classification": "breaking",
            "required_version_change": "major",
            "requires_policy_update": True,
            "all_surfaces_must_move_together": True,
            "consumer_guidance": "existing-fields-remain-authoritative",
            "reason": " ".join(reasons),
        }

    if command_specific_addition and not additive_policy["command_specific_additions_allowed"]:
        return {
            "classification": "reserved-additive-policy-violation",
            "required_version_change": "minor",
            "requires_policy_update": True,
            "all_surfaces_must_move_together": additive_policy["all_surfaces_must_move_together"],
            "consumer_guidance": additive_policy["consumer_unknown_field_rule_when_enabled"],
            "reason": (
                "Reserved additive JSON changes must move all governed commands together; "
                "command-specific additive fields are not allowed."
            ),
        }

    return {
        "classification": "reserved-additive-requires-policy-update",
        "required_version_change": "minor",
        "requires_policy_update": True,
        "all_surfaces_must_move_together": additive_policy["all_surfaces_must_move_together"],
        "consumer_guidance": additive_policy["consumer_unknown_field_rule_when_enabled"],
        "reason": (
            "Additive governed JSON fields remain gated today; a future additive change requires "
            "a shared minor schema-version bump plus coordinated policy, test, and doc updates."
        ),
    }


def _strip_compatibility_example_for_live_validation(surface: str, payload: dict) -> dict:
    stripped = json.loads(json.dumps(payload))
    stripped.pop(JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD, None)
    stripped["schema_version"] = EXPECTED_JSON_CONTRACT_SCHEMA_VERSION
    if surface == "status":
        verify_status_json_contract(stripped)
        return stripped
    if surface == "doctor":
        verify_doctor_json_contract(stripped)
        return stripped
    if surface == "doctor_write_report":
        verify_doctor_json_contract(
            stripped,
            expect_wrote_report=stripped["wrote_report"],
        )
        return stripped
    if surface == "roots":
        verify_roots_json_contract(stripped)
        return stripped
    raise AssertionError(f"Unknown JSON contract surface `{surface}`.")


def build_future_minor_compatibility_examples(surface_payloads: dict[str, dict]) -> dict[str, dict]:
    additive_policy = verify_json_contract_reserved_additive_policy()
    if set(surface_payloads) != set(JSON_CONTRACT_SURFACES):
        raise AssertionError(
            "Future minor compatibility examples must cover all governed JSON commands together."
        )

    examples: dict[str, dict] = {}
    for surface in JSON_CONTRACT_SURFACES:
        payload = json.loads(json.dumps(surface_payloads[surface]))
        payload["schema_version"] = SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION
        payload[JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD] = {
            "status": "example-only",
            "shared_minor_version": SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION,
            "optional_for_consumers": True,
            "live_contract_unchanged": True,
            "consumer_unknown_field_rule": additive_policy["consumer_unknown_field_rule_when_enabled"],
        }
        examples[surface] = payload
    return examples


def verify_future_minor_compatibility_examples(example_payloads: dict[str, dict]) -> dict[str, dict]:
    additive_policy = verify_json_contract_reserved_additive_policy()
    if set(example_payloads) != set(JSON_CONTRACT_SURFACES):
        raise AssertionError(
            "Future minor compatibility examples must include all governed JSON commands together."
        )

    validated: dict[str, dict] = {}
    for surface in JSON_CONTRACT_SURFACES:
        payload = _assert_json_object(f"{surface} compatibility example", example_payloads[surface])
        _assert_string(
            f"{surface} compatibility example.schema_version",
            payload.get("schema_version"),
        )
        if payload["schema_version"] != SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION:
            raise AssertionError(
                f"`{surface}` compatibility example must use simulated future version `{SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION}`."
            )

        current_expected_keys = {
            "status": EXPECTED_STATUS_KEYS,
            "doctor": EXPECTED_DOCTOR_KEYS,
            "doctor_write_report": EXPECTED_DOCTOR_KEYS,
            "roots": EXPECTED_ROOTS_KEYS,
        }[surface]
        actual_keys = set(payload.keys())
        expected_current_keys = set(current_expected_keys)
        extra_keys = sorted(actual_keys - expected_current_keys)
        missing_keys = sorted(expected_current_keys - actual_keys)
        if missing_keys:
            raise AssertionError(
                f"`{surface}` compatibility example is missing current governed keys: {missing_keys}."
            )
        if extra_keys != [JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD]:
            raise AssertionError(
                f"`{surface}` compatibility example must add only `{JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD}`; found extras {extra_keys}."
            )

        example = _assert_json_object(
            f"{surface} compatibility example.{JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD}",
            payload[JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD],
        )
        _assert_exact_keys(
            f"{surface} compatibility example.{JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD}",
            example,
            EXPECTED_JSON_CONTRACT_COMPATIBILITY_EXAMPLE_KEYS,
        )
        _assert_string(
            f"{surface} compatibility example.{JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD}.status",
            example["status"],
        )
        if example["status"] != "example-only":
            raise AssertionError(
                f"`{surface}` compatibility example must stay example-only and not become live contract data."
            )
        _assert_string(
            f"{surface} compatibility example.{JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD}.shared_minor_version",
            example["shared_minor_version"],
        )
        if example["shared_minor_version"] != SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION:
            raise AssertionError(
                f"`{surface}` compatibility example must advertise shared minor version `{SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION}`."
            )
        _assert_bool(
            f"{surface} compatibility example.{JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD}.optional_for_consumers",
            example["optional_for_consumers"],
        )
        if not example["optional_for_consumers"]:
            raise AssertionError(
                f"`{surface}` compatibility example must keep additive fields optional for consumers."
            )
        _assert_bool(
            f"{surface} compatibility example.{JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD}.live_contract_unchanged",
            example["live_contract_unchanged"],
        )
        if not example["live_contract_unchanged"]:
            raise AssertionError(
                f"`{surface}` compatibility example must keep the live contract unchanged."
            )
        _assert_string(
            f"{surface} compatibility example.{JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD}.consumer_unknown_field_rule",
            example["consumer_unknown_field_rule"],
        )
        if (
            example["consumer_unknown_field_rule"]
            != additive_policy["consumer_unknown_field_rule_when_enabled"]
        ):
            raise AssertionError(
                f"`{surface}` compatibility example drifted from the reserved consumer unknown-field rule."
            )

        _strip_compatibility_example_for_live_validation(surface, payload)
        validated[surface] = payload

    shared_versions = {
        validated[surface][JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD]["shared_minor_version"]
        for surface in JSON_CONTRACT_SURFACES
    }
    if shared_versions != {SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION}:
        raise AssertionError(
            "Future minor compatibility examples must move all governed JSON commands to the same simulated shared minor version."
        )
    return validated


def verify_future_minor_consumer_handling_example(consumed_payloads: dict[str, dict]) -> dict[str, dict]:
    additive_policy = verify_json_contract_reserved_additive_policy()
    if set(consumed_payloads) != set(JSON_CONTRACT_SURFACES):
        raise AssertionError(
            "Future minor consumer-handling examples must include all governed JSON commands together."
        )

    validated: dict[str, dict] = {}
    for surface in JSON_CONTRACT_SURFACES:
        item = _assert_json_object(
            f"{surface} consumer-handling example",
            consumed_payloads[surface],
        )
        _assert_exact_keys(
            f"{surface} consumer-handling example",
            item,
            EXPECTED_JSON_CONTRACT_CONSUMER_EXAMPLE_KEYS,
        )
        _assert_string(f"{surface} consumer-handling example.surface", item["surface"])
        if item["surface"] != surface:
            raise AssertionError(
                f"`{surface}` consumer-handling example must keep its surface label aligned."
            )
        _assert_string(
            f"{surface} consumer-handling example.schema_version",
            item["schema_version"],
        )
        if item["schema_version"] != SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION:
            raise AssertionError(
                f"`{surface}` consumer-handling example must use simulated future version `{SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION}`."
            )
        _assert_string(
            f"{surface} consumer-handling example.consumer_mode",
            item["consumer_mode"],
        )
        if item["consumer_mode"] != JSON_CONTRACT_CONSUMER_EXAMPLE_MODE:
            raise AssertionError(
                f"`{surface}` consumer-handling example drifted from the governed consumer mode `{JSON_CONTRACT_CONSUMER_EXAMPLE_MODE}`."
            )

        tolerated = _assert_string_list(
            f"{surface} consumer-handling example.tolerated_optional_fields",
            item["tolerated_optional_fields"],
        )
        if tolerated != [JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD]:
            raise AssertionError(
                f"`{surface}` consumer-handling example must tolerate only `{JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD}`."
            )

        preserved = _assert_json_object(
            f"{surface} consumer-handling example.preserved_optional_fields",
            item["preserved_optional_fields"],
        )
        if sorted(preserved.keys()) != [JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD]:
            raise AssertionError(
                f"`{surface}` consumer-handling example must preserve only `{JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD}`."
            )
        example = _assert_json_object(
            f"{surface} consumer-handling example.preserved_optional_fields.{JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD}",
            preserved[JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD],
        )
        _assert_exact_keys(
            f"{surface} consumer-handling example.preserved_optional_fields.{JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD}",
            example,
            EXPECTED_JSON_CONTRACT_COMPATIBILITY_EXAMPLE_KEYS,
        )
        if example["status"] != "example-only":
            raise AssertionError(
                f"`{surface}` consumer-handling example must preserve the example-only marker."
            )
        if example["shared_minor_version"] != SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION:
            raise AssertionError(
                f"`{surface}` consumer-handling example must preserve shared minor version `{SIMULATED_FUTURE_MINOR_JSON_CONTRACT_VERSION}`."
            )
        if not example["optional_for_consumers"]:
            raise AssertionError(
                f"`{surface}` consumer-handling example must preserve optional-for-consumers guidance."
            )
        if (
            example["consumer_unknown_field_rule"]
            != additive_policy["consumer_unknown_field_rule_when_enabled"]
        ):
            raise AssertionError(
                f"`{surface}` consumer-handling example drifted from the governed unknown-field rule."
            )

        known_payload = _assert_json_object(
            f"{surface} consumer-handling example.known_payload",
            item["known_payload"],
        )
        if JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD in known_payload:
            raise AssertionError(
                f"`{surface}` consumer-handling example must keep optional fields out of the authoritative known payload."
            )
        if surface == "status":
            verify_status_json_contract(known_payload)
        elif surface == "doctor":
            verify_doctor_json_contract(known_payload)
        elif surface == "doctor_write_report":
            verify_doctor_json_contract(
                known_payload,
                expect_wrote_report=known_payload["wrote_report"],
            )
        elif surface == "roots":
            verify_roots_json_contract(known_payload)
        else:
            raise AssertionError(f"Unknown JSON contract surface `{surface}`.")
        validated[surface] = item

    return validated


def consume_future_minor_optional_fields_example(example_payloads: dict[str, dict]) -> dict[str, dict]:
    verified_examples = verify_future_minor_compatibility_examples(example_payloads)
    consumed: dict[str, dict] = {}
    for surface in JSON_CONTRACT_SURFACES:
        payload = verified_examples[surface]
        consumed[surface] = {
            "surface": surface,
            "schema_version": payload["schema_version"],
            "consumer_mode": JSON_CONTRACT_CONSUMER_EXAMPLE_MODE,
            "known_payload": _strip_compatibility_example_for_live_validation(surface, payload),
            "tolerated_optional_fields": [JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD],
            "preserved_optional_fields": {
                JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD: json.loads(
                    json.dumps(payload[JSON_CONTRACT_COMPATIBILITY_EXAMPLE_FIELD])
                )
            },
        }
    return verify_future_minor_consumer_handling_example(consumed)


def _assert_json_schema_version(payload: dict, label: str) -> None:
    policy = verify_json_contract_evolution_policy()
    if payload.get("schema_version") != policy["shared_schema_version"]:
        raise AssertionError(
            f"`{label}.schema_version` drifted from shared JSON schema version `{policy['shared_schema_version']}`."
        )


def _verify_issue_list(label: str, issues: object) -> None:
    if not isinstance(issues, list):
        raise AssertionError(f"`{label}` must be a list.")
    for index, issue in enumerate(issues):
        item = _assert_json_object(f"{label}[{index}]", issue)
        _assert_exact_keys(f"{label}[{index}]", item, EXPECTED_ISSUE_KEYS)
        _assert_string(f"{label}[{index}].level", item["level"])
        if item["level"] not in ALLOWED_ISSUE_LEVELS:
            raise AssertionError(
                f"`{label}[{index}].level` must be one of {sorted(ALLOWED_ISSUE_LEVELS)}."
            )
        _assert_string(f"{label}[{index}].message", item["message"])


def _verify_command_docs_entries(label: str, entries: object) -> None:
    if not isinstance(entries, list):
        raise AssertionError(f"`{label}` must be a list.")
    for index, entry in enumerate(entries):
        item = _assert_json_object(f"{label}[{index}]", entry)
        _assert_exact_keys(f"{label}[{index}]", item, EXPECTED_COMMAND_DOCS_ENTRY_KEYS)
        _assert_string(f"{label}[{index}].surface", item["surface"])
        _assert_status(f"{label}[{index}].status", item["status"])
        _assert_string(f"{label}[{index}].summary", item["summary"])


def _verify_file_entries(label: str, entries: object) -> None:
    if not isinstance(entries, list):
        raise AssertionError(f"`{label}` must be a list.")
    for index, entry in enumerate(entries):
        item = _assert_json_object(f"{label}[{index}]", entry)
        _assert_exact_keys(f"{label}[{index}]", item, EXPECTED_MEMORY_ENTRY_KEYS)
        _assert_string(f"{label}[{index}].relative_path", item["relative_path"])
        _assert_status(f"{label}[{index}].status", item["status"])
        _assert_string(f"{label}[{index}].summary", item["summary"])


def _verify_docs_health_entries(label: str, entries: object) -> None:
    if not isinstance(entries, list):
        raise AssertionError(f"`{label}` must be a list.")
    for index, entry in enumerate(entries):
        item = _assert_json_object(f"{label}[{index}]", entry)
        _assert_exact_keys(f"{label}[{index}]", item, EXPECTED_DOCS_HEALTH_ENTRY_KEYS)
        _assert_string(f"{label}[{index}].relative_path", item["relative_path"])
        _assert_status(f"{label}[{index}].status", item["status"])
        _assert_int(f"{label}[{index}].line_count", item["line_count"])
        _assert_int(f"{label}[{index}].budget", item["budget"])
        _assert_string(f"{label}[{index}].summary", item["summary"])


def _verify_roots_entries(label: str, entries: object) -> None:
    if not isinstance(entries, list):
        raise AssertionError(f"`{label}` must be a list.")
    for index, entry in enumerate(entries):
        item = _assert_json_object(f"{label}[{index}]", entry)
        _assert_exact_keys(f"{label}[{index}]", item, EXPECTED_ROOTS_ENTRY_KEYS)
        _assert_string(f"{label}[{index}].path", item["path"])
        _assert_string(f"{label}[{index}].status", item["status"])


def verify_health_overview_contract(overview: object) -> dict:
    item = _assert_json_object("health_overview", overview)
    _assert_exact_keys("health_overview", item, EXPECTED_HEALTH_OVERVIEW_KEYS)
    _assert_status("health_overview.overall_status", item["overall_status"])
    _assert_string("health_overview.summary", item["summary"])
    _assert_bool("health_overview.sync_needed", item["sync_needed"])
    _assert_bool(
        "health_overview.default_root_operations_safe",
        item["default_root_operations_safe"],
    )
    _assert_string("health_overview.pre_hermes_readiness", item["pre_hermes_readiness"])
    if item["pre_hermes_readiness"] not in ALLOWED_PRE_HERMES_READINESS:
        raise AssertionError(
            "`health_overview.pre_hermes_readiness` drifted from the current deterministic vocabulary."
        )

    subsystems = _assert_json_object("health_overview.subsystems", item["subsystems"])
    _assert_exact_keys(
        "health_overview.subsystems",
        subsystems,
        EXPECTED_HEALTH_SUBSYSTEM_KEYS,
    )
    for subsystem in EXPECTED_HEALTH_SUBSYSTEM_KEYS:
        _assert_status(
            f"health_overview.subsystems.{subsystem}",
            subsystems[subsystem],
        )
    return item


def verify_health_bundle_contract(health: object) -> dict:
    item = _assert_json_object("health", health)
    _assert_exact_keys("health", item, EXPECTED_HEALTH_KEYS)

    command_docs = _assert_json_object("health.command_help_docs", item["command_help_docs"])
    _assert_exact_keys("health.command_help_docs", command_docs, EXPECTED_COMMAND_DOCS_KEYS)
    _assert_status("health.command_help_docs.status", command_docs["status"])
    _assert_string("health.command_help_docs.summary", command_docs["summary"])
    _assert_string("health.command_help_docs.path", command_docs["path"])
    _verify_command_docs_entries("health.command_help_docs.entries", command_docs["entries"])
    _verify_issue_list("health.command_help_docs.issues", command_docs["issues"])

    manifest = _assert_json_object("health.manifest", item["manifest"])
    _assert_exact_keys("health.manifest", manifest, EXPECTED_MANIFEST_KEYS)
    _assert_status("health.manifest.status", manifest["status"])
    _assert_string("health.manifest.summary", manifest["summary"])
    _assert_string("health.manifest.path", manifest["path"])
    _verify_issue_list("health.manifest.issues", manifest["issues"])

    mirror = _assert_json_object("health.mirror_lock_shim", item["mirror_lock_shim"])
    _assert_exact_keys("health.mirror_lock_shim", mirror, EXPECTED_MIRROR_KEYS)
    _assert_status("health.mirror_lock_shim.status", mirror["status"])
    _assert_string("health.mirror_lock_shim.summary", mirror["summary"])
    _assert_string("health.mirror_lock_shim.path", mirror["path"])
    _assert_bool("health.mirror_lock_shim.sync_needed", mirror["sync_needed"])
    _verify_issue_list("health.mirror_lock_shim.issues", mirror["issues"])

    memory = _assert_json_object("health.memory", item["memory"])
    _assert_exact_keys("health.memory", memory, EXPECTED_MEMORY_KEYS)
    _assert_status("health.memory.status", memory["status"])
    _assert_string("health.memory.summary", memory["summary"])
    _assert_string("health.memory.path", memory["path"])
    _verify_file_entries("health.memory.entries", memory["entries"])
    _verify_issue_list("health.memory.issues", memory["issues"])

    continuity = _assert_json_object("health.continuity_state", item["continuity_state"])
    _assert_exact_keys("health.continuity_state", continuity, EXPECTED_CONTINUITY_STATE_KEYS)
    _assert_status("health.continuity_state.status", continuity["status"])
    _assert_string("health.continuity_state.summary", continuity["summary"])
    _assert_string("health.continuity_state.path", continuity["path"])
    _verify_file_entries("health.continuity_state.entries", continuity["entries"])
    _verify_issue_list("health.continuity_state.issues", continuity["issues"])

    roots = _assert_json_object("health.roots", item["roots"])
    verify_roots_health_contract(roots, label="health.roots")

    role_contract = _assert_json_object("health.role_contract", item["role_contract"])
    _assert_exact_keys("health.role_contract", role_contract, EXPECTED_ROLE_CONTRACT_HEALTH_KEYS)
    _assert_status("health.role_contract.status", role_contract["status"])
    _assert_string("health.role_contract.summary", role_contract["summary"])
    _assert_string("health.role_contract.path", role_contract["path"])
    _assert_string_list("health.role_contract.canonical_roles", role_contract["canonical_roles"])
    _assert_string_list("health.role_contract.reserved_roles", role_contract["reserved_roles"])
    _assert_string_list("health.role_contract.supported_harnesses", role_contract["supported_harnesses"])
    _verify_issue_list("health.role_contract.issues", role_contract["issues"])

    docs_health = _assert_json_object("health.docs_health", item["docs_health"])
    _assert_exact_keys("health.docs_health", docs_health, EXPECTED_DOCS_HEALTH_KEYS)
    _assert_status("health.docs_health.status", docs_health["status"])
    _assert_string("health.docs_health.summary", docs_health["summary"])
    _assert_string("health.docs_health.path", docs_health["path"])
    _verify_docs_health_entries("health.docs_health.entries", docs_health["entries"])
    _verify_issue_list("health.docs_health.issues", docs_health["issues"])

    return item


def verify_roots_health_contract(roots_health: object, *, label: str) -> dict:
    item = _assert_json_object(label, roots_health)
    _assert_exact_keys(label, item, EXPECTED_ROOTS_HEALTH_KEYS)
    _assert_status(f"{label}.status", item["status"])
    _assert_string(f"{label}.summary", item["summary"])
    _assert_optional_string(f"{label}.config_path", item["config_path"])
    _assert_string(f"{label}.source_label", item["source_label"])
    _assert_bool(f"{label}.default_root_operations_safe", item["default_root_operations_safe"])
    _assert_string_list(f"{label}.roots", item["roots"])
    _assert_string_list(f"{label}.usable_roots", item["usable_roots"])
    _verify_roots_entries(f"{label}.entries", item["entries"])
    _verify_issue_list(f"{label}.issues", item["issues"])
    return item


def _verify_status_health_consistency(overview: dict, health: dict) -> None:
    if overview["subsystems"]["command_help_docs"] != health["command_help_docs"]["status"]:
        raise AssertionError("`health_overview.subsystems.command_help_docs` drifted from `health.command_help_docs.status`.")
    if overview["subsystems"]["manifest"] != health["manifest"]["status"]:
        raise AssertionError("`health_overview.subsystems.manifest` drifted from `health.manifest.status`.")
    if overview["subsystems"]["mirror_lock_shim"] != health["mirror_lock_shim"]["status"]:
        raise AssertionError("`health_overview.subsystems.mirror_lock_shim` drifted from `health.mirror_lock_shim.status`.")
    if overview["subsystems"]["memory"] != health["memory"]["status"]:
        raise AssertionError("`health_overview.subsystems.memory` drifted from `health.memory.status`.")
    if overview["subsystems"]["continuity_state"] != health["continuity_state"]["status"]:
        raise AssertionError("`health_overview.subsystems.continuity_state` drifted from `health.continuity_state.status`.")
    if overview["subsystems"]["roots"] != health["roots"]["status"]:
        raise AssertionError("`health_overview.subsystems.roots` drifted from `health.roots.status`.")
    if overview["subsystems"]["role_contract"] != health["role_contract"]["status"]:
        raise AssertionError("`health_overview.subsystems.role_contract` drifted from `health.role_contract.status`.")
    if overview["subsystems"]["docs_health"] != health["docs_health"]["status"]:
        raise AssertionError("`health_overview.subsystems.docs_health` drifted from `health.docs_health.status`.")
    if overview["sync_needed"] != health["mirror_lock_shim"]["sync_needed"]:
        raise AssertionError("`health_overview.sync_needed` drifted from `health.mirror_lock_shim.sync_needed`.")
    if overview["default_root_operations_safe"] != health["roots"]["default_root_operations_safe"]:
        raise AssertionError(
            "`health_overview.default_root_operations_safe` drifted from `health.roots.default_root_operations_safe`."
        )


def verify_status_json_contract(payload: object) -> dict:
    item = _assert_json_object("status payload", payload)
    _assert_exact_keys("status payload", item, EXPECTED_STATUS_KEYS)
    _assert_json_schema_version(item, "status payload")
    if item["command"] != "status":
        raise AssertionError("`status payload.command` must be `status`.")
    _assert_string("status payload.repo_path", item["repo_path"])
    _assert_string("status payload.classification", item["classification"])

    project = _assert_json_object("status payload.project", item["project"])
    _assert_exact_keys("status payload.project", project, EXPECTED_PROJECT_KEYS)
    for key in EXPECTED_PROJECT_KEYS:
        _assert_string(f"status payload.project.{key}", project[key])

    continuity = _assert_json_object("status payload.continuity", item["continuity"])
    _assert_exact_keys("status payload.continuity", continuity, EXPECTED_CONTINUITY_KEYS)
    sources = _assert_json_object("status payload.continuity.sources", continuity["sources"])
    _assert_allowed_keys(
        "status payload.continuity.sources",
        sources,
        required_keys=REQUIRED_CONTINUITY_SOURCE_KEYS,
        optional_keys=OPTIONAL_CONTINUITY_SOURCE_KEYS,
    )
    _assert_bool(
        "status payload.continuity.sources.legacy_preserved",
        sources["legacy_preserved"],
    )
    for key in REQUIRED_CONTINUITY_SOURCE_KEYS[1:]:
        _assert_string(f"status payload.continuity.sources.{key}", sources[key])
    for key in OPTIONAL_CONTINUITY_SOURCE_KEYS:
        if key in sources:
            _assert_string(f"status payload.continuity.sources.{key}", sources[key])

    migration = _assert_json_object("status payload.migration", item["migration"])
    _assert_exact_keys("status payload.migration", migration, EXPECTED_MIGRATION_KEYS)
    _assert_string("status payload.migration.summary", migration["summary"])
    _assert_string("status payload.migration.status", migration["status"])
    _assert_string("status payload.migration.phase", migration["phase"])
    _assert_bool("status payload.migration.legacy_preserved", migration["legacy_preserved"])
    if migration["branch"] is not None:
        _assert_string("status payload.migration.branch", migration["branch"])

    doctor_summary = _assert_json_object("status payload.doctor_summary", item["doctor_summary"])
    _assert_exact_keys("status payload.doctor_summary", doctor_summary, EXPECTED_DOCTOR_SUMMARY_KEYS)
    _assert_string("status payload.doctor_summary.summary", doctor_summary["summary"])

    overview = verify_health_overview_contract(item["health_overview"])
    health = verify_health_bundle_contract(item["health"])
    _verify_status_health_consistency(overview, health)

    _assert_string("status payload.git", item["git"])
    _assert_string_list("status payload.notes", item["notes"])
    return item


def verify_doctor_json_contract(
    payload: object,
    *,
    expect_wrote_report: bool | None = None,
    expected_drift_report_path: Path | None = None,
) -> dict:
    item = _assert_json_object("doctor payload", payload)
    _assert_exact_keys("doctor payload", item, EXPECTED_DOCTOR_KEYS)
    _assert_json_schema_version(item, "doctor payload")
    if item["command"] != "doctor":
        raise AssertionError("`doctor payload.command` must be `doctor`.")
    _assert_string("doctor payload.repo_path", item["repo_path"])
    _assert_string("doctor payload.classification", item["classification"])
    _assert_string("doctor payload.result_status", item["result_status"])
    if item["result_status"] not in {"pass", "fail"}:
        raise AssertionError("`doctor payload.result_status` must be `pass` or `fail`.")
    _assert_bool("doctor payload.passed", item["passed"])
    if item["passed"] != (item["result_status"] == "pass"):
        raise AssertionError("`doctor payload.passed` drifted from `doctor payload.result_status`.")

    _assert_bool("doctor payload.wrote_report", item["wrote_report"])
    if expect_wrote_report is not None and item["wrote_report"] != expect_wrote_report:
        raise AssertionError(
            f"`doctor payload.wrote_report` drifted from the expected value `{expect_wrote_report}`."
        )
    _assert_optional_string("doctor payload.drift_report_path", item["drift_report_path"])
    if item["wrote_report"] and item["drift_report_path"] is None:
        raise AssertionError("`doctor payload.drift_report_path` must be set when `wrote_report` is true.")
    if not item["wrote_report"] and item["drift_report_path"] is not None:
        raise AssertionError("`doctor payload.drift_report_path` must be null when `wrote_report` is false.")
    if expected_drift_report_path is not None:
        actual = Path(item["drift_report_path"]).resolve() if item["drift_report_path"] else None
        if actual != expected_drift_report_path.resolve():
            raise AssertionError(
                "`doctor payload.drift_report_path` drifted from the expected report location."
            )

    overview = verify_health_overview_contract(item["health_overview"])
    health = verify_health_bundle_contract(item["health"])
    _verify_status_health_consistency(overview, health)

    _assert_string_list("doctor payload.notes", item["notes"])

    if not isinstance(item["findings"], list):
        raise AssertionError("`doctor payload.findings` must be a list.")
    errors_from_findings: list[str] = []
    warnings_from_findings: list[str] = []
    for index, finding in enumerate(item["findings"]):
        entry = _assert_json_object(f"doctor payload.findings[{index}]", finding)
        _assert_exact_keys(
            f"doctor payload.findings[{index}]",
            entry,
            EXPECTED_FINDING_KEYS,
        )
        _assert_string(f"doctor payload.findings[{index}].surface", entry["surface"])
        if entry["surface"] not in ALLOWED_FINDING_SURFACES:
            raise AssertionError(
                f"`doctor payload.findings[{index}].surface` drifted from the current contract vocabulary."
            )
        _assert_string(f"doctor payload.findings[{index}].level", entry["level"])
        if entry["level"] not in ALLOWED_ISSUE_LEVELS:
            raise AssertionError(
                f"`doctor payload.findings[{index}].level` must be one of {sorted(ALLOWED_ISSUE_LEVELS)}."
            )
        _assert_string(f"doctor payload.findings[{index}].message", entry["message"])
        _assert_string(f"doctor payload.findings[{index}].text", entry["text"])
        if entry["level"] == "error":
            errors_from_findings.append(entry["message"])
        else:
            warnings_from_findings.append(entry["message"])

    if _assert_string_list("doctor payload.errors", item["errors"]) != errors_from_findings:
        raise AssertionError("`doctor payload.errors` drifted from the error findings list.")
    if _assert_string_list("doctor payload.warnings", item["warnings"]) != warnings_from_findings:
        raise AssertionError("`doctor payload.warnings` drifted from the warning findings list.")
    return item


def verify_roots_json_contract(payload: object) -> dict:
    item = _assert_json_object("roots payload", payload)
    _assert_exact_keys("roots payload", item, EXPECTED_ROOTS_KEYS)
    _assert_json_schema_version(item, "roots payload")
    if item["command"] != "roots":
        raise AssertionError("`roots payload.command` must be `roots`.")
    _assert_bool("roots payload.validate_requested", item["validate_requested"])
    _assert_bool("roots payload.passed_validation", item["passed_validation"])
    verify_roots_health_contract(item["health"], label="roots payload.health")
    return item


def verify_json_contract_stdout(
    stdout: str,
    surface: str,
    *,
    expect_wrote_report: bool | None = None,
    expected_drift_report_path: Path | None = None,
) -> dict:
    verify_json_contract_evolution_policy()
    payload = json.loads(stdout)
    if surface == "status":
        return verify_status_json_contract(payload)
    if surface == "doctor":
        return verify_doctor_json_contract(payload)
    if surface == "doctor_write_report":
        return verify_doctor_json_contract(
            payload,
            expect_wrote_report=expect_wrote_report,
            expected_drift_report_path=expected_drift_report_path,
        )
    if surface == "roots":
        return verify_roots_json_contract(payload)
    raise AssertionError(f"Unknown JSON contract surface `{surface}`.")
