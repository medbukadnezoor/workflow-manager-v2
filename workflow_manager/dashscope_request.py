from __future__ import annotations

from dataclasses import dataclass

from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL, DashScopeLocalReadiness


DASHSCOPE_OFFLINE_REQUEST_SHAPE_VERSION = "1.0.0"
DASHSCOPE_OFFLINE_REQUEST_SOURCE = "hermes_inventory"
DASHSCOPE_OFFLINE_REQUEST_MODE = "offline_request_shape_only"
DASHSCOPE_OFFLINE_REQUEST_ALLOWED_FIELDS = (
    "request_shape_version",
    "source",
    "mode",
    "intended_model",
    "selected_model",
    "selected_model_variable_name",
    "selected_model_variable_category",
    "model_policy_status",
    "model_policy_ready",
    "model_policy_requires_update",
    "local_config_ready",
    "runtime_enabled",
    "network_calls_allowed",
    "qwen_dashscope_enabled",
    "graphify_enabled",
    "migration_writes_enabled",
    "request_policy",
    "input_summary",
    "forbidden_fields",
)
DASHSCOPE_OFFLINE_REQUEST_POLICY_KEYS = (
    "scope",
    "uses_only_deterministic_inventory_metadata",
    "includes_root_paths",
    "includes_project_paths",
    "includes_project_source_code",
    "includes_target_repo_file_contents",
    "includes_env_values",
    "includes_api_key_values",
    "includes_large_prompt_bodies",
    "includes_hidden_reasoning",
    "forbidden_field_handling",
    "sensitive_value_handling",
)
DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS = (
    "source_schema_version",
    "source_command",
    "source_mode",
    "source_dry_run",
    "inventory_summary",
    "classification_counts",
    "root_count",
    "total_project_count",
    "root_classification_counts",
    "warning_count",
    "error_count",
)
DASHSCOPE_OFFLINE_REQUEST_FORBIDDEN_FIELDS = (
    "api_key",
    "api_key_prefix",
    "api_key_suffix",
    "credentials",
    "tokens",
    "env_values",
    "raw_env",
    "root_paths",
    "project_paths",
    "prompt_text",
    "project_source_code",
    "target_repo_file_contents",
    "generated_shim_contents",
    "memory_file_bodies",
    "state_file_bodies",
    "migration_write_instructions",
    "hidden_reasoning",
)
DASHSCOPE_OFFLINE_REQUEST_FORBIDDEN_FIELD_FRAGMENTS = (
    "api_key",
    "secret",
    "token",
    "credential",
    "env",
    "prompt",
    "source_code",
    "file_content",
    "reasoning",
    "migration_write",
)
DASHSCOPE_OFFLINE_REQUEST_ALLOWED_METADATA_FIELDS: tuple[str, ...] = ()
DASHSCOPE_OFFLINE_REQUEST_POLICY = {
    "scope": "future-hermes-qwen-request-blueprint",
    "uses_only_deterministic_inventory_metadata": True,
    "includes_root_paths": False,
    "includes_project_paths": False,
    "includes_project_source_code": False,
    "includes_target_repo_file_contents": False,
    "includes_env_values": False,
    "includes_api_key_values": False,
    "includes_large_prompt_bodies": False,
    "includes_hidden_reasoning": False,
    "forbidden_field_handling": "reject",
    "sensitive_value_handling": "full-redaction-or-rejection",
}
DASHSCOPE_OFFLINE_REQUEST_SOURCE_KEYS = (
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
DASHSCOPE_OFFLINE_REQUEST_CLASSIFICATION_COUNT_KEYS = (
    "v2",
    "legacy",
    "mixed",
    "unmanaged",
    "error",
)


def _assert_json_object(label: str, value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object.")
    return dict(value)


def _assert_bool(label: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be a boolean.")
    return value


def _assert_string(label: str, value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string.")
    return value


def _assert_string_list(label: str, value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{label} must be a list of strings.")
    return list(value)


def _assert_non_negative_int(label: str, value: object) -> int:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer.")
    return value


def _assert_exact_keys(label: str, payload: dict[str, object], expected_keys: tuple[str, ...]) -> None:
    actual = set(payload.keys())
    expected = set(expected_keys)
    if actual == expected:
        return
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    parts = [f"{label} keys drifted."]
    if missing:
        parts.append(f"Missing keys: {missing}.")
    if unexpected:
        parts.append(f"Unexpected keys: {unexpected}.")
    raise ValueError(" ".join(parts))


def _normalize_readiness(readiness: DashScopeLocalReadiness | dict[str, object]) -> dict[str, object]:
    payload = readiness.to_safe_dict() if hasattr(readiness, "to_safe_dict") else dict(readiness)
    required_keys = (
        "intended_model_name",
        "selected_model_name",
        "selected_model_variable_name",
        "selected_model_variable_category",
        "model_policy_status",
        "model_policy_ready",
        "model_policy_requires_update",
        "local_config_ready",
        "runtime_enabled",
        "network_calls_allowed",
    )
    missing = [key for key in required_keys if key not in payload]
    if missing:
        raise ValueError(f"DashScope local readiness payload is missing required keys for request shaping: {missing}.")
    return payload


def _summarize_root_classifications(roots: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for root in roots:
        classification = _assert_string("Hermes inventory roots[].classification", root.get("classification"))
        counts[classification] = counts.get(classification, 0) + 1
    return dict(sorted(counts.items()))


def sanitize_dashscope_request_metadata(candidate_metadata: dict[str, object] | None) -> dict[str, object]:
    if not candidate_metadata:
        return {}

    forbidden = []
    unexpected = []
    for key in candidate_metadata:
        key_lower = key.lower()
        if key in DASHSCOPE_OFFLINE_REQUEST_FORBIDDEN_FIELDS or any(
            fragment in key_lower for fragment in DASHSCOPE_OFFLINE_REQUEST_FORBIDDEN_FIELD_FRAGMENTS
        ):
            forbidden.append(key)
            continue
        if key not in DASHSCOPE_OFFLINE_REQUEST_ALLOWED_METADATA_FIELDS:
            unexpected.append(key)

    if forbidden:
        raise ValueError(
            "Offline DashScope/Qwen request metadata contains forbidden fields: "
            + ", ".join(sorted(forbidden))
            + "."
        )
    if unexpected:
        raise ValueError(
            "Offline DashScope/Qwen request metadata does not allow extra fields yet: "
            + ", ".join(sorted(unexpected))
            + "."
        )
    return {}


@dataclass(frozen=True)
class DashScopeOfflineRequestShape:
    request_shape_version: str
    source: str
    mode: str
    intended_model: str
    selected_model: str
    selected_model_variable_name: str | None
    selected_model_variable_category: str | None
    model_policy_status: str
    model_policy_ready: bool
    model_policy_requires_update: bool
    local_config_ready: bool
    runtime_enabled: bool
    network_calls_allowed: bool
    qwen_dashscope_enabled: bool
    graphify_enabled: bool
    migration_writes_enabled: bool
    request_policy: dict[str, object]
    input_summary: dict[str, object]
    forbidden_fields: tuple[str, ...]

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "request_shape_version": self.request_shape_version,
            "source": self.source,
            "mode": self.mode,
            "intended_model": self.intended_model,
            "selected_model": self.selected_model,
            "selected_model_variable_name": self.selected_model_variable_name,
            "selected_model_variable_category": self.selected_model_variable_category,
            "model_policy_status": self.model_policy_status,
            "model_policy_ready": self.model_policy_ready,
            "model_policy_requires_update": self.model_policy_requires_update,
            "local_config_ready": self.local_config_ready,
            "runtime_enabled": self.runtime_enabled,
            "network_calls_allowed": self.network_calls_allowed,
            "qwen_dashscope_enabled": self.qwen_dashscope_enabled,
            "graphify_enabled": self.graphify_enabled,
            "migration_writes_enabled": self.migration_writes_enabled,
            "request_policy": dict(self.request_policy),
            "input_summary": dict(self.input_summary),
            "forbidden_fields": list(self.forbidden_fields),
        }


def build_hermes_qwen_offline_request_shape(
    hermes_inventory_payload: dict[str, object],
    readiness: DashScopeLocalReadiness | dict[str, object],
    *,
    candidate_metadata: dict[str, object] | None = None,
) -> DashScopeOfflineRequestShape:
    sanitize_dashscope_request_metadata(candidate_metadata)

    source_payload = _assert_json_object("Hermes inventory payload", hermes_inventory_payload)
    _assert_exact_keys(
        "Hermes inventory payload",
        source_payload,
        DASHSCOPE_OFFLINE_REQUEST_SOURCE_KEYS,
    )
    readiness_payload = _normalize_readiness(readiness)

    source_schema_version = _assert_string(
        "Hermes inventory payload.schema_version",
        source_payload["schema_version"],
    )
    source_command = _assert_string(
        "Hermes inventory payload.command",
        source_payload["command"],
    )
    source_mode = _assert_string(
        "Hermes inventory payload.mode",
        source_payload["mode"],
    )
    source_dry_run = _assert_bool(
        "Hermes inventory payload.dry_run",
        source_payload["dry_run"],
    )
    inventory_summary = _assert_string(
        "Hermes inventory payload.summary",
        source_payload["summary"],
    )
    classification_counts = _assert_json_object(
        "Hermes inventory payload.classification_counts",
        source_payload["classification_counts"],
    )
    if set(classification_counts.keys()) != set(DASHSCOPE_OFFLINE_REQUEST_CLASSIFICATION_COUNT_KEYS):
        raise ValueError("Hermes inventory payload.classification_counts drifted from the governed inventory vocabulary.")
    for key in DASHSCOPE_OFFLINE_REQUEST_CLASSIFICATION_COUNT_KEYS:
        _assert_non_negative_int(
            f"Hermes inventory payload.classification_counts.{key}",
            classification_counts[key],
        )

    roots = source_payload["roots"]
    if not isinstance(roots, list) or not all(isinstance(item, dict) for item in roots):
        raise ValueError("Hermes inventory payload.roots must be a list of objects.")
    warnings = _assert_string_list("Hermes inventory payload.warnings", source_payload["warnings"])
    errors = _assert_string_list("Hermes inventory payload.errors", source_payload["errors"])

    if _assert_bool("Hermes inventory payload.target_repos_modified", source_payload["target_repos_modified"]):
        raise ValueError("Offline request shaping forbids target repo modifications.")
    qwen_dashscope_enabled = _assert_bool(
        "Hermes inventory payload.qwen_dashscope_enabled",
        source_payload["qwen_dashscope_enabled"],
    )
    graphify_enabled = _assert_bool(
        "Hermes inventory payload.graphify_enabled",
        source_payload["graphify_enabled"],
    )
    migration_writes_enabled = _assert_bool(
        "Hermes inventory payload.migration_writes_enabled",
        source_payload["migration_writes_enabled"],
    )
    if qwen_dashscope_enabled or graphify_enabled or migration_writes_enabled or not source_dry_run:
        raise ValueError(
            "Offline request shaping requires dry-run Hermes inventory with Qwen, Graphify, and migration writes disabled."
        )

    total_project_count = 0
    for index, root in enumerate(roots):
        _assert_non_negative_int(
            f"Hermes inventory payload.roots[{index}].project_count",
            root.get("project_count"),
        )
        total_project_count += int(root["project_count"])

    input_summary = {
        "source_schema_version": source_schema_version,
        "source_command": source_command,
        "source_mode": source_mode,
        "source_dry_run": source_dry_run,
        "inventory_summary": inventory_summary,
        "classification_counts": {
            key: int(classification_counts[key])
            for key in DASHSCOPE_OFFLINE_REQUEST_CLASSIFICATION_COUNT_KEYS
        },
        "root_count": len(roots),
        "total_project_count": total_project_count,
        "root_classification_counts": _summarize_root_classifications(roots),
        "warning_count": len(warnings),
        "error_count": len(errors),
    }

    selected_model = readiness_payload["selected_model_name"] or readiness_payload["intended_model_name"]
    return DashScopeOfflineRequestShape(
        request_shape_version=DASHSCOPE_OFFLINE_REQUEST_SHAPE_VERSION,
        source=DASHSCOPE_OFFLINE_REQUEST_SOURCE,
        mode=DASHSCOPE_OFFLINE_REQUEST_MODE,
        intended_model=_assert_string("DashScope readiness intended_model_name", readiness_payload["intended_model_name"]),
        selected_model=_assert_string("DashScope readiness selected_model_name", selected_model),
        selected_model_variable_name=readiness_payload["selected_model_variable_name"],
        selected_model_variable_category=readiness_payload["selected_model_variable_category"],
        model_policy_status=_assert_string("DashScope readiness model_policy_status", readiness_payload["model_policy_status"]),
        model_policy_ready=_assert_bool("DashScope readiness model_policy_ready", readiness_payload["model_policy_ready"]),
        model_policy_requires_update=_assert_bool(
            "DashScope readiness model_policy_requires_update",
            readiness_payload["model_policy_requires_update"],
        ),
        local_config_ready=_assert_bool("DashScope readiness local_config_ready", readiness_payload["local_config_ready"]),
        runtime_enabled=_assert_bool("DashScope readiness runtime_enabled", readiness_payload["runtime_enabled"]),
        network_calls_allowed=_assert_bool(
            "DashScope readiness network_calls_allowed",
            readiness_payload["network_calls_allowed"],
        ),
        qwen_dashscope_enabled=qwen_dashscope_enabled,
        graphify_enabled=graphify_enabled,
        migration_writes_enabled=migration_writes_enabled,
        request_policy=DASHSCOPE_OFFLINE_REQUEST_POLICY,
        input_summary=input_summary,
        forbidden_fields=DASHSCOPE_OFFLINE_REQUEST_FORBIDDEN_FIELDS,
    )
