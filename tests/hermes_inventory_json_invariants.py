from __future__ import annotations

import json
from pathlib import Path


EXPECTED_HERMES_INVENTORY_JSON_SCHEMA_VERSION = "1.0.0"
EXPECTED_HERMES_INVENTORY_JSON_COMMAND = "hermes_inventory"
EXPECTED_HERMES_INVENTORY_JSON_MODE = "inventory"
HERMES_INVENTORY_JSON_BREAKING_CHANGE_CATEGORIES = (
    "remove-governed-top-level-field",
    "rename-governed-top-level-field",
    "change-governed-top-level-field-type",
    "remove-governed-root-field",
    "rename-governed-root-field",
    "change-governed-root-field-type",
    "remove-governed-project-field",
    "rename-governed-project-field",
    "change-governed-project-field-type",
    "change-root-classification-vocabulary",
    "change-project-classification-vocabulary",
    "change-safety-flag-semantics",
    "change-dry-run-gating-semantics",
    "change-deterministic-ordering-guarantee",
    "allow-target-repo-writes",
)
HERMES_INVENTORY_JSON_ADDITIVE_CHANGE_CATEGORIES = (
    "add-governed-top-level-field",
    "add-governed-root-field",
    "add-governed-project-field",
)
HERMES_INVENTORY_JSON_RESERVED_ADDITIVE_ENABLEMENT_STEPS = (
    "bump-hermes-inventory-schema-minor-version",
    "update-hermes-inventory-json-policy",
    "update-hermes-inventory-json-invariants",
    "update-focused-hermes-inventory-tests",
    "update-repo-docs",
)
SIMULATED_FUTURE_MINOR_HERMES_INVENTORY_JSON_SCHEMA_VERSION = "1.1.0"
HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD = "compatibility_example"
EXPECTED_HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_KEYS = (
    "status",
    "schema_surface",
    "future_minor_version",
    "optional_for_consumers",
    "live_contract_unchanged",
    "consumer_unknown_field_rule",
)
EXPECTED_HERMES_INVENTORY_JSON_KEYS = (
    "schema_version",
    "command",
    "mode",
    "dry_run",
    "roots_config_path",
    "summary",
    "classification_counts",
    "roots",
    "warnings",
    "errors",
    "target_repos_modified",
    "qwen_dashscope_enabled",
    "graphify_enabled",
    "migration_writes_enabled",
)
EXPECTED_HERMES_INVENTORY_CLASSIFICATION_COUNT_KEYS = (
    "v2",
    "legacy",
    "mixed",
    "unmanaged",
    "error",
)
EXPECTED_HERMES_INVENTORY_ROOT_KEYS = (
    "path",
    "classification",
    "exists",
    "is_directory",
    "project_count",
    "issues",
    "projects",
)
EXPECTED_HERMES_INVENTORY_PROJECT_KEYS = (
    "name",
    "path",
    "root",
    "classification",
    "notes",
)
ALLOWED_HERMES_PROJECT_CLASSIFICATIONS = {
    "v2",
    "legacy",
    "mixed",
    "unmanaged",
    "error",
}
ALLOWED_HERMES_ROOT_CLASSIFICATIONS = {
    "configured-root",
    "missing-root",
    "invalid-root",
}
EXPECTED_HERMES_INVENTORY_JSON_POLICY_KEYS = (
    "schema_surface",
    "schema_version",
    "versioning_mode",
    "versioning_scheme",
    "separate_from_health_json_contract",
    "command_specific_versioning",
    "patch_change_rule",
    "minor_change_rule",
    "major_change_rule",
    "additive_keys_allowed",
    "breaking_changes_require_version_bump",
    "coordinated_updates_required",
    "classification_vocabularies_governed",
    "safety_flags_governed",
    "dry_run_gating_governed",
    "read_only_behavior_governed",
    "deterministic_ordering_governed",
    "breaking_change_categories",
    "additive_change_categories",
)
EXPECTED_HERMES_INVENTORY_JSON_RESERVED_ADDITIVE_POLICY_KEYS = (
    "status",
    "enabled_by_default",
    "current_schema_version",
    "future_minor_version_path",
    "minor_version_bump_required",
    "new_fields_must_be_optional_for_consumers",
    "new_fields_must_not_change_existing_field_meaning",
    "new_fields_must_not_change_existing_field_types",
    "new_fields_must_not_change_classification_vocabularies",
    "new_fields_must_not_change_safety_flag_semantics",
    "new_fields_must_not_change_dry_run_gating",
    "new_fields_must_not_change_read_only_behavior",
    "new_fields_must_not_change_deterministic_ordering",
    "consumer_unknown_field_rule_when_enabled",
    "required_updates_before_enablement",
)
EXPECTED_HERMES_INVENTORY_JSON_CHANGE_ASSESSMENT_KEYS = (
    "classification",
    "required_version_change",
    "requires_policy_update",
    "consumer_guidance",
    "read_only_behavior_must_remain",
    "reason",
)
HERMES_INVENTORY_JSON_EVOLUTION_POLICY = {
    "schema_surface": EXPECTED_HERMES_INVENTORY_JSON_COMMAND,
    "schema_version": EXPECTED_HERMES_INVENTORY_JSON_SCHEMA_VERSION,
    "versioning_mode": "surface-local",
    "versioning_scheme": "semver",
    "separate_from_health_json_contract": True,
    "command_specific_versioning": False,
    "patch_change_rule": "no-governed-contract-change",
    "minor_change_rule": "reserved-for-future-additive-compatible-changes",
    "major_change_rule": "required-for-breaking-contract-changes",
    "additive_keys_allowed": False,
    "breaking_changes_require_version_bump": True,
    "coordinated_updates_required": True,
    "classification_vocabularies_governed": True,
    "safety_flags_governed": True,
    "dry_run_gating_governed": True,
    "read_only_behavior_governed": True,
    "deterministic_ordering_governed": True,
    "breaking_change_categories": HERMES_INVENTORY_JSON_BREAKING_CHANGE_CATEGORIES,
    "additive_change_categories": HERMES_INVENTORY_JSON_ADDITIVE_CHANGE_CATEGORIES,
}
HERMES_INVENTORY_JSON_RESERVED_ADDITIVE_POLICY = {
    "status": "reserved-not-enabled",
    "enabled_by_default": False,
    "current_schema_version": EXPECTED_HERMES_INVENTORY_JSON_SCHEMA_VERSION,
    "future_minor_version_path": "reserved-hermes-inventory-minor-version-bump",
    "minor_version_bump_required": True,
    "new_fields_must_be_optional_for_consumers": True,
    "new_fields_must_not_change_existing_field_meaning": True,
    "new_fields_must_not_change_existing_field_types": True,
    "new_fields_must_not_change_classification_vocabularies": True,
    "new_fields_must_not_change_safety_flag_semantics": True,
    "new_fields_must_not_change_dry_run_gating": True,
    "new_fields_must_not_change_read_only_behavior": True,
    "new_fields_must_not_change_deterministic_ordering": True,
    "consumer_unknown_field_rule_when_enabled": (
        "ignore-unknown-optional-fields-only-after-an-explicit-hermes-inventory-minor-version-upgrade"
    ),
    "required_updates_before_enablement": HERMES_INVENTORY_JSON_RESERVED_ADDITIVE_ENABLEMENT_STEPS,
}


def _assert_json_object(label: str, payload: object) -> dict:
    if not isinstance(payload, dict):
        raise AssertionError(f"{label} must be a JSON object.")
    return payload


def _assert_exact_keys(label: str, payload: dict, expected_keys: tuple[str, ...]) -> None:
    actual = set(payload.keys())
    expected = set(expected_keys)
    if actual == expected:
        return

    parts = [f"{label} keys drifted."]
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        parts.append(f"Missing keys: {missing}.")
    if unexpected:
        parts.append(f"Unexpected keys: {unexpected}.")
    raise AssertionError(" ".join(parts))


def _assert_string(label: str, value: object) -> str:
    if not isinstance(value, str):
        raise AssertionError(f"{label} must be a string.")
    return value


def _assert_integer(label: str, value: object) -> int:
    if not isinstance(value, int):
        raise AssertionError(f"{label} must be an integer.")
    return value


def _assert_bool(label: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise AssertionError(f"{label} must be a boolean.")
    return value


def _assert_string_list(label: str, value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise AssertionError(f"{label} must be a list of strings.")
    return list(value)


def _assert_string_sequence(label: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) for item in value):
        raise AssertionError(f"{label} must be a list or tuple of strings.")
    return tuple(value)


def verify_hermes_inventory_json_evolution_policy() -> dict:
    policy = HERMES_INVENTORY_JSON_EVOLUTION_POLICY
    _assert_exact_keys(
        "Hermes inventory JSON evolution policy",
        policy,
        EXPECTED_HERMES_INVENTORY_JSON_POLICY_KEYS,
    )
    schema_surface = _assert_string(
        "Hermes inventory JSON evolution policy.schema_surface",
        policy["schema_surface"],
    )
    if schema_surface != EXPECTED_HERMES_INVENTORY_JSON_COMMAND:
        raise AssertionError("Hermes inventory JSON must remain a separate `hermes_inventory` schema surface.")
    schema_version = _assert_string(
        "Hermes inventory JSON evolution policy.schema_version",
        policy["schema_version"],
    )
    if schema_version != EXPECTED_HERMES_INVENTORY_JSON_SCHEMA_VERSION:
        raise AssertionError(
            "Hermes inventory JSON evolution policy drifted from the governed schema version."
        )
    if policy["versioning_mode"] != "surface-local":
        raise AssertionError("Hermes inventory JSON versioning mode must remain `surface-local`.")
    if policy["versioning_scheme"] != "semver":
        raise AssertionError("Hermes inventory JSON versioning scheme must remain `semver`.")
    separate_surface = _assert_bool(
        "Hermes inventory JSON evolution policy.separate_from_health_json_contract",
        policy["separate_from_health_json_contract"],
    )
    if not separate_surface:
        raise AssertionError(
            "Hermes inventory JSON must remain a separate schema surface from status/doctor/roots JSON."
        )
    command_specific_versioning = _assert_bool(
        "Hermes inventory JSON evolution policy.command_specific_versioning",
        policy["command_specific_versioning"],
    )
    if command_specific_versioning:
        raise AssertionError(
            "Command-specific versioning is intentionally not used within Hermes inventory JSON."
        )
    patch_change_rule = _assert_string(
        "Hermes inventory JSON evolution policy.patch_change_rule",
        policy["patch_change_rule"],
    )
    if patch_change_rule != "no-governed-contract-change":
        raise AssertionError(
            "Patch Hermes inventory JSON changes must remain reserved for non-contract implementation or documentation work."
        )
    minor_change_rule = _assert_string(
        "Hermes inventory JSON evolution policy.minor_change_rule",
        policy["minor_change_rule"],
    )
    if minor_change_rule != "reserved-for-future-additive-compatible-changes":
        raise AssertionError(
            "Minor Hermes inventory JSON changes must remain reserved for future additive compatible work."
        )
    major_change_rule = _assert_string(
        "Hermes inventory JSON evolution policy.major_change_rule",
        policy["major_change_rule"],
    )
    if major_change_rule != "required-for-breaking-contract-changes":
        raise AssertionError("Breaking Hermes inventory JSON changes must require a major version bump.")
    additive_keys_allowed = _assert_bool(
        "Hermes inventory JSON evolution policy.additive_keys_allowed",
        policy["additive_keys_allowed"],
    )
    if additive_keys_allowed:
        raise AssertionError("Additive Hermes inventory JSON keys are intentionally gated for now.")
    if not _assert_bool(
        "Hermes inventory JSON evolution policy.breaking_changes_require_version_bump",
        policy["breaking_changes_require_version_bump"],
    ):
        raise AssertionError("Breaking Hermes inventory JSON changes must require a version bump.")
    if not _assert_bool(
        "Hermes inventory JSON evolution policy.coordinated_updates_required",
        policy["coordinated_updates_required"],
    ):
        raise AssertionError(
            "Intentional Hermes inventory JSON contract changes must require coordinated policy, test, and doc updates."
        )
    if not _assert_bool(
        "Hermes inventory JSON evolution policy.classification_vocabularies_governed",
        policy["classification_vocabularies_governed"],
    ):
        raise AssertionError("Hermes inventory classification vocabularies must remain governed contract elements.")
    if not _assert_bool(
        "Hermes inventory JSON evolution policy.safety_flags_governed",
        policy["safety_flags_governed"],
    ):
        raise AssertionError("Hermes inventory safety flags must remain governed contract elements.")
    if not _assert_bool(
        "Hermes inventory JSON evolution policy.dry_run_gating_governed",
        policy["dry_run_gating_governed"],
    ):
        raise AssertionError("Hermes inventory dry-run gating must remain a governed contract element.")
    if not _assert_bool(
        "Hermes inventory JSON evolution policy.read_only_behavior_governed",
        policy["read_only_behavior_governed"],
    ):
        raise AssertionError("Hermes inventory read-only behavior must remain a governed contract element.")
    if not _assert_bool(
        "Hermes inventory JSON evolution policy.deterministic_ordering_governed",
        policy["deterministic_ordering_governed"],
    ):
        raise AssertionError("Hermes inventory deterministic ordering must remain a governed contract element.")
    if _assert_string_sequence(
        "Hermes inventory JSON evolution policy.breaking_change_categories",
        policy["breaking_change_categories"],
    ) != HERMES_INVENTORY_JSON_BREAKING_CHANGE_CATEGORIES:
        raise AssertionError("Hermes inventory JSON breaking change categories drifted from the governed baseline.")
    if _assert_string_sequence(
        "Hermes inventory JSON evolution policy.additive_change_categories",
        policy["additive_change_categories"],
    ) != HERMES_INVENTORY_JSON_ADDITIVE_CHANGE_CATEGORIES:
        raise AssertionError("Hermes inventory JSON additive change categories drifted from the governed baseline.")
    return policy


def verify_hermes_inventory_json_reserved_additive_policy() -> dict:
    evolution_policy = verify_hermes_inventory_json_evolution_policy()
    policy = HERMES_INVENTORY_JSON_RESERVED_ADDITIVE_POLICY
    _assert_exact_keys(
        "Hermes inventory JSON reserved additive policy",
        policy,
        EXPECTED_HERMES_INVENTORY_JSON_RESERVED_ADDITIVE_POLICY_KEYS,
    )
    if _assert_string(
        "Hermes inventory JSON reserved additive policy.status",
        policy["status"],
    ) != "reserved-not-enabled":
        raise AssertionError("Hermes inventory reserved additive policy must remain `reserved-not-enabled` for now.")
    if _assert_bool(
        "Hermes inventory JSON reserved additive policy.enabled_by_default",
        policy["enabled_by_default"],
    ):
        raise AssertionError("Hermes inventory reserved additive policy must not enable additive keys by default.")
    current_schema_version = _assert_string(
        "Hermes inventory JSON reserved additive policy.current_schema_version",
        policy["current_schema_version"],
    )
    if current_schema_version != evolution_policy["schema_version"]:
        raise AssertionError(
            "Hermes inventory reserved additive policy drifted from the governed schema version."
        )
    future_minor_path = _assert_string(
        "Hermes inventory JSON reserved additive policy.future_minor_version_path",
        policy["future_minor_version_path"],
    )
    if future_minor_path != "reserved-hermes-inventory-minor-version-bump":
        raise AssertionError(
            "Hermes inventory reserved additive policy must keep the surface-local minor-version path explicit."
        )
    if not _assert_bool(
        "Hermes inventory JSON reserved additive policy.minor_version_bump_required",
        policy["minor_version_bump_required"],
    ):
        raise AssertionError("Reserved additive Hermes inventory JSON changes must require a minor version bump.")
    if not _assert_bool(
        "Hermes inventory JSON reserved additive policy.new_fields_must_be_optional_for_consumers",
        policy["new_fields_must_be_optional_for_consumers"],
    ):
        raise AssertionError("Reserved additive Hermes inventory JSON fields must remain optional for consumers.")
    if not _assert_bool(
        "Hermes inventory JSON reserved additive policy.new_fields_must_not_change_existing_field_meaning",
        policy["new_fields_must_not_change_existing_field_meaning"],
    ):
        raise AssertionError(
            "Reserved additive Hermes inventory JSON fields must not change the meaning of existing fields."
        )
    if not _assert_bool(
        "Hermes inventory JSON reserved additive policy.new_fields_must_not_change_existing_field_types",
        policy["new_fields_must_not_change_existing_field_types"],
    ):
        raise AssertionError(
            "Reserved additive Hermes inventory JSON fields must not change existing field types."
        )
    if not _assert_bool(
        "Hermes inventory JSON reserved additive policy.new_fields_must_not_change_classification_vocabularies",
        policy["new_fields_must_not_change_classification_vocabularies"],
    ):
        raise AssertionError(
            "Reserved additive Hermes inventory JSON fields must not change root/project classification vocabularies."
        )
    if not _assert_bool(
        "Hermes inventory JSON reserved additive policy.new_fields_must_not_change_safety_flag_semantics",
        policy["new_fields_must_not_change_safety_flag_semantics"],
    ):
        raise AssertionError(
            "Reserved additive Hermes inventory JSON fields must not change safety-flag semantics."
        )
    if not _assert_bool(
        "Hermes inventory JSON reserved additive policy.new_fields_must_not_change_dry_run_gating",
        policy["new_fields_must_not_change_dry_run_gating"],
    ):
        raise AssertionError("Reserved additive Hermes inventory JSON fields must not change dry-run gating.")
    if not _assert_bool(
        "Hermes inventory JSON reserved additive policy.new_fields_must_not_change_read_only_behavior",
        policy["new_fields_must_not_change_read_only_behavior"],
    ):
        raise AssertionError("Reserved additive Hermes inventory JSON fields must not change read-only behavior.")
    if not _assert_bool(
        "Hermes inventory JSON reserved additive policy.new_fields_must_not_change_deterministic_ordering",
        policy["new_fields_must_not_change_deterministic_ordering"],
    ):
        raise AssertionError(
            "Reserved additive Hermes inventory JSON fields must not change deterministic ordering guarantees."
        )
    consumer_unknown_field_rule = _assert_string(
        "Hermes inventory JSON reserved additive policy.consumer_unknown_field_rule_when_enabled",
        policy["consumer_unknown_field_rule_when_enabled"],
    )
    if (
        consumer_unknown_field_rule
        != "ignore-unknown-optional-fields-only-after-an-explicit-hermes-inventory-minor-version-upgrade"
    ):
        raise AssertionError(
            "Reserved additive Hermes inventory JSON consumer guidance drifted from the governed future minor-version rule."
        )
    if _assert_string_sequence(
        "Hermes inventory JSON reserved additive policy.required_updates_before_enablement",
        policy["required_updates_before_enablement"],
    ) != HERMES_INVENTORY_JSON_RESERVED_ADDITIVE_ENABLEMENT_STEPS:
        raise AssertionError(
            "Reserved additive Hermes inventory JSON enablement steps drifted from the governed baseline."
        )
    return policy


def assess_hermes_inventory_json_change(
    change_category: str,
    *,
    changes_existing_field_meaning: bool = False,
    changes_existing_field_type: bool = False,
    changes_classification_vocabulary: bool = False,
    changes_safety_flag_semantics: bool = False,
    changes_dry_run_gating: bool = False,
    changes_read_only_behavior: bool = False,
    changes_deterministic_ordering: bool = False,
) -> dict:
    verify_hermes_inventory_json_evolution_policy()
    additive_policy = verify_hermes_inventory_json_reserved_additive_policy()
    all_categories = set(HERMES_INVENTORY_JSON_BREAKING_CHANGE_CATEGORIES) | set(
        HERMES_INVENTORY_JSON_ADDITIVE_CHANGE_CATEGORIES
    )
    if change_category not in all_categories:
        raise AssertionError(f"Unknown Hermes inventory JSON change category `{change_category}`.")

    reasons: list[str] = []
    if change_category in HERMES_INVENTORY_JSON_BREAKING_CHANGE_CATEGORIES:
        reasons.append(f"`{change_category}` is explicitly governed as breaking.")
    if changes_existing_field_meaning:
        reasons.append("Changing the meaning of an existing governed Hermes inventory JSON field is breaking.")
    if changes_existing_field_type:
        reasons.append("Changing the type of an existing governed Hermes inventory JSON field is breaking.")
    if changes_classification_vocabulary:
        reasons.append("Changing the governed Hermes inventory classification vocabulary is breaking.")
    if changes_safety_flag_semantics:
        reasons.append("Changing Hermes inventory safety-flag semantics is breaking.")
    if changes_dry_run_gating:
        reasons.append("Changing Hermes inventory dry-run gating is breaking.")
    if changes_read_only_behavior:
        reasons.append("Changing Hermes inventory read-only behavior is breaking.")
    if changes_deterministic_ordering:
        reasons.append("Changing Hermes inventory deterministic ordering guarantees is breaking.")
    if reasons:
        assessment = {
            "classification": "breaking",
            "required_version_change": "major",
            "requires_policy_update": True,
            "consumer_guidance": "existing-fields-remain-authoritative",
            "read_only_behavior_must_remain": True,
            "reason": " ".join(reasons),
        }
        _assert_exact_keys(
            "Hermes inventory JSON change assessment",
            assessment,
            EXPECTED_HERMES_INVENTORY_JSON_CHANGE_ASSESSMENT_KEYS,
        )
        return assessment

    assessment = {
        "classification": "reserved-additive-requires-policy-update",
        "required_version_change": "minor",
        "requires_policy_update": True,
        "consumer_guidance": additive_policy["consumer_unknown_field_rule_when_enabled"],
        "read_only_behavior_must_remain": True,
        "reason": (
            "Additive governed Hermes inventory JSON fields remain gated today; a future additive change requires "
            "an explicit Hermes inventory minor schema-version bump plus coordinated policy, test, and doc updates."
        ),
    }
    _assert_exact_keys(
        "Hermes inventory JSON change assessment",
        assessment,
        EXPECTED_HERMES_INVENTORY_JSON_CHANGE_ASSESSMENT_KEYS,
    )
    return assessment


def _strip_hermes_inventory_compatibility_example_for_live_validation(payload: dict) -> dict:
    stripped = json.loads(json.dumps(payload))
    stripped.pop(HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD, None)
    stripped["schema_version"] = EXPECTED_HERMES_INVENTORY_JSON_SCHEMA_VERSION
    verify_hermes_inventory_json_payload(stripped)
    return stripped


def build_hermes_inventory_future_minor_compatibility_example(live_payload: dict) -> dict:
    additive_policy = verify_hermes_inventory_json_reserved_additive_policy()
    payload = json.loads(json.dumps(verify_hermes_inventory_json_payload(live_payload)))
    payload["schema_version"] = SIMULATED_FUTURE_MINOR_HERMES_INVENTORY_JSON_SCHEMA_VERSION
    payload[HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD] = {
        "status": "example-only",
        "schema_surface": EXPECTED_HERMES_INVENTORY_JSON_COMMAND,
        "future_minor_version": SIMULATED_FUTURE_MINOR_HERMES_INVENTORY_JSON_SCHEMA_VERSION,
        "optional_for_consumers": True,
        "live_contract_unchanged": True,
        "consumer_unknown_field_rule": additive_policy["consumer_unknown_field_rule_when_enabled"],
    }
    return payload


def verify_hermes_inventory_future_minor_compatibility_example(example_payload: object) -> dict:
    additive_policy = verify_hermes_inventory_json_reserved_additive_policy()
    payload = _assert_json_object("Hermes inventory compatibility example", example_payload)
    _assert_string(
        "Hermes inventory compatibility example.schema_version",
        payload.get("schema_version"),
    )
    if payload["schema_version"] != SIMULATED_FUTURE_MINOR_HERMES_INVENTORY_JSON_SCHEMA_VERSION:
        raise AssertionError(
            "Hermes inventory compatibility example must use simulated future version "
            f"`{SIMULATED_FUTURE_MINOR_HERMES_INVENTORY_JSON_SCHEMA_VERSION}`."
        )

    actual_keys = set(payload.keys())
    expected_current_keys = set(EXPECTED_HERMES_INVENTORY_JSON_KEYS)
    extra_keys = sorted(actual_keys - expected_current_keys)
    missing_keys = sorted(expected_current_keys - actual_keys)
    if missing_keys:
        raise AssertionError(
            "Hermes inventory compatibility example is missing current governed keys: "
            f"{missing_keys}."
        )
    if extra_keys != [HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD]:
        raise AssertionError(
            "Hermes inventory compatibility example must add only "
            f"`{HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD}`; found extras {extra_keys}."
        )

    example = _assert_json_object(
        f"Hermes inventory compatibility example.{HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD}",
        payload[HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD],
    )
    _assert_exact_keys(
        f"Hermes inventory compatibility example.{HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD}",
        example,
        EXPECTED_HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_KEYS,
    )
    if _assert_string(
        f"Hermes inventory compatibility example.{HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD}.status",
        example["status"],
    ) != "example-only":
        raise AssertionError(
            "Hermes inventory compatibility example must stay example-only and not become live contract data."
        )
    if _assert_string(
        f"Hermes inventory compatibility example.{HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD}.schema_surface",
        example["schema_surface"],
    ) != EXPECTED_HERMES_INVENTORY_JSON_COMMAND:
        raise AssertionError(
            "Hermes inventory compatibility example must stay on the separate `hermes_inventory` schema surface."
        )
    if _assert_string(
        f"Hermes inventory compatibility example.{HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD}.future_minor_version",
        example["future_minor_version"],
    ) != SIMULATED_FUTURE_MINOR_HERMES_INVENTORY_JSON_SCHEMA_VERSION:
        raise AssertionError(
            "Hermes inventory compatibility example must advertise the simulated future version "
            f"`{SIMULATED_FUTURE_MINOR_HERMES_INVENTORY_JSON_SCHEMA_VERSION}`."
        )
    if not _assert_bool(
        f"Hermes inventory compatibility example.{HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD}.optional_for_consumers",
        example["optional_for_consumers"],
    ):
        raise AssertionError(
            "Hermes inventory compatibility example must keep additive fields optional for consumers."
        )
    if not _assert_bool(
        f"Hermes inventory compatibility example.{HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD}.live_contract_unchanged",
        example["live_contract_unchanged"],
    ):
        raise AssertionError(
            "Hermes inventory compatibility example must keep the live contract unchanged."
        )
    if _assert_string(
        f"Hermes inventory compatibility example.{HERMES_INVENTORY_JSON_COMPATIBILITY_EXAMPLE_FIELD}.consumer_unknown_field_rule",
        example["consumer_unknown_field_rule"],
    ) != additive_policy["consumer_unknown_field_rule_when_enabled"]:
        raise AssertionError(
            "Hermes inventory compatibility example drifted from the reserved consumer unknown-field rule."
        )

    _strip_hermes_inventory_compatibility_example_for_live_validation(payload)
    return payload


def verify_hermes_inventory_json_payload(
    payload: object,
    *,
    expected_roots_config_path: Path | None = None,
) -> dict:
    payload = _assert_json_object("Hermes inventory payload", payload)
    _assert_exact_keys(
        "Hermes inventory payload",
        payload,
        EXPECTED_HERMES_INVENTORY_JSON_KEYS,
    )

    schema_version = _assert_string("Hermes inventory payload.schema_version", payload["schema_version"])
    if schema_version != EXPECTED_HERMES_INVENTORY_JSON_SCHEMA_VERSION:
        raise AssertionError(
            f"Hermes inventory payload.schema_version must be `{EXPECTED_HERMES_INVENTORY_JSON_SCHEMA_VERSION}`."
        )

    command = _assert_string("Hermes inventory payload.command", payload["command"])
    if command != EXPECTED_HERMES_INVENTORY_JSON_COMMAND:
        raise AssertionError(
            f"Hermes inventory payload.command must be `{EXPECTED_HERMES_INVENTORY_JSON_COMMAND}`."
        )

    mode = _assert_string("Hermes inventory payload.mode", payload["mode"])
    if mode != EXPECTED_HERMES_INVENTORY_JSON_MODE:
        raise AssertionError(
            f"Hermes inventory payload.mode must be `{EXPECTED_HERMES_INVENTORY_JSON_MODE}`."
        )

    dry_run = _assert_bool("Hermes inventory payload.dry_run", payload["dry_run"])
    if dry_run is not True:
        raise AssertionError("Hermes inventory payload.dry_run must remain `true`.")

    roots_config_path = payload["roots_config_path"]
    if roots_config_path is not None and not isinstance(roots_config_path, str):
        raise AssertionError("Hermes inventory payload.roots_config_path must be a string or null.")
    if expected_roots_config_path is not None:
        expected_path = str(expected_roots_config_path.resolve())
        if roots_config_path != expected_path:
            raise AssertionError(
                f"Hermes inventory payload.roots_config_path drifted. Expected `{expected_path}`, got `{roots_config_path}`."
            )

    _assert_string("Hermes inventory payload.summary", payload["summary"])

    classification_counts = _assert_json_object(
        "Hermes inventory payload.classification_counts",
        payload["classification_counts"],
    )
    _assert_exact_keys(
        "Hermes inventory payload.classification_counts",
        classification_counts,
        EXPECTED_HERMES_INVENTORY_CLASSIFICATION_COUNT_KEYS,
    )
    for key in EXPECTED_HERMES_INVENTORY_CLASSIFICATION_COUNT_KEYS:
        _assert_integer(f"Hermes inventory payload.classification_counts.{key}", classification_counts[key])

    _assert_string_list("Hermes inventory payload.warnings", payload["warnings"])
    _assert_string_list("Hermes inventory payload.errors", payload["errors"])

    safety_flags = {
        "target_repos_modified": False,
        "qwen_dashscope_enabled": False,
        "graphify_enabled": False,
        "migration_writes_enabled": False,
    }
    for key, expected in safety_flags.items():
        actual = _assert_bool(f"Hermes inventory payload.{key}", payload[key])
        if actual is not expected:
            rendered = "true" if expected else "false"
            raise AssertionError(f"Hermes inventory payload.{key} must remain `{rendered}`.")

    roots = payload["roots"]
    if not isinstance(roots, list):
        raise AssertionError("Hermes inventory payload.roots must be a list.")
    root_paths = []
    for root in roots:
        root_payload = _assert_json_object("Hermes inventory root payload", root)
        _assert_exact_keys(
            "Hermes inventory root payload",
            root_payload,
            EXPECTED_HERMES_INVENTORY_ROOT_KEYS,
        )
        root_path = _assert_string("Hermes inventory root payload.path", root_payload["path"])
        root_paths.append(root_path)
        root_classification = _assert_string(
            "Hermes inventory root payload.classification",
            root_payload["classification"],
        )
        if root_classification not in ALLOWED_HERMES_ROOT_CLASSIFICATIONS:
            raise AssertionError(
                "Hermes inventory root payload.classification must be one of "
                f"{sorted(ALLOWED_HERMES_ROOT_CLASSIFICATIONS)}."
            )
        _assert_bool("Hermes inventory root payload.exists", root_payload["exists"])
        _assert_bool("Hermes inventory root payload.is_directory", root_payload["is_directory"])
        _assert_integer("Hermes inventory root payload.project_count", root_payload["project_count"])
        _assert_string_list("Hermes inventory root payload.issues", root_payload["issues"])

        projects = root_payload["projects"]
        if not isinstance(projects, list):
            raise AssertionError("Hermes inventory root payload.projects must be a list.")
        if root_payload["project_count"] != len(projects):
            raise AssertionError(
                "Hermes inventory root payload.project_count must match the number of project entries."
            )

        ordered_projects: list[tuple[str, str]] = []
        for project in projects:
            project_payload = _assert_json_object("Hermes inventory project payload", project)
            _assert_exact_keys(
                "Hermes inventory project payload",
                project_payload,
                EXPECTED_HERMES_INVENTORY_PROJECT_KEYS,
            )
            project_name = _assert_string("Hermes inventory project payload.name", project_payload["name"])
            project_path = _assert_string("Hermes inventory project payload.path", project_payload["path"])
            ordered_projects.append((project_name, project_path))
            project_root = _assert_string("Hermes inventory project payload.root", project_payload["root"])
            if project_root != root_path:
                raise AssertionError(
                    "Hermes inventory project payload.root must match its parent root payload.path."
                )
            project_classification = _assert_string(
                "Hermes inventory project payload.classification",
                project_payload["classification"],
            )
            if project_classification not in ALLOWED_HERMES_PROJECT_CLASSIFICATIONS:
                raise AssertionError(
                    "Hermes inventory project payload.classification must be one of "
                    f"{sorted(ALLOWED_HERMES_PROJECT_CLASSIFICATIONS)}."
                )
            _assert_string_list("Hermes inventory project payload.notes", project_payload["notes"])

        if ordered_projects != sorted(ordered_projects):
            raise AssertionError(
                "Hermes inventory root payload.projects must be ordered deterministically by project name/path."
            )

    if root_paths != sorted(root_paths):
        raise AssertionError("Hermes inventory payload.roots must be ordered deterministically by root path.")

    return payload


def verify_hermes_inventory_json_stdout(
    stdout: str,
    *,
    expected_roots_config_path: Path | None = None,
) -> dict:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Hermes inventory stdout must be valid JSON: {exc}") from exc
    return verify_hermes_inventory_json_payload(
        payload,
        expected_roots_config_path=expected_roots_config_path,
    )
