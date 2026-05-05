from __future__ import annotations

from dataclasses import dataclass

from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL
from workflow_manager.dashscope_request import (
    DASHSCOPE_OFFLINE_REQUEST_CLASSIFICATION_COUNT_KEYS,
    DASHSCOPE_OFFLINE_REQUEST_MODE,
    DASHSCOPE_OFFLINE_REQUEST_SHAPE_VERSION,
    DASHSCOPE_OFFLINE_REQUEST_SOURCE,
)


DASHSCOPE_OFFLINE_PROMPT_TEMPLATE_VERSION = "1.0.0"
DASHSCOPE_OFFLINE_PROMPT_SOURCE = "hermes_inventory"
DASHSCOPE_OFFLINE_PROMPT_MODE = "offline_prompt_template_only"
DASHSCOPE_OFFLINE_PROMPT_ALLOWED_FIELDS = (
    "prompt_template_version",
    "source",
    "mode",
    "intended_model",
    "selected_model",
    "model_policy_status",
    "model_policy_ready",
    "model_policy_requires_update",
    "local_config_ready",
    "runtime_enabled",
    "network_calls_allowed",
    "qwen_dashscope_enabled",
    "graphify_enabled",
    "migration_writes_enabled",
    "request_shape_version",
    "request_shape_source",
    "request_shape_mode",
    "request_shape_scope",
    "allowed_sections",
    "required_sections",
    "forbidden_sections",
    "forbidden_content",
    "prompt_policy",
    "rendered_sections",
)
DASHSCOPE_OFFLINE_PROMPT_ALLOWED_SECTIONS = (
    "system_role",
    "task",
    "source_of_truth",
    "inventory_summary",
    "classification_counts",
    "safety_constraints",
    "forbidden_actions",
    "expected_output_shape",
    "redaction_policy",
)
DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS = DASHSCOPE_OFFLINE_PROMPT_ALLOWED_SECTIONS
DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_SECTIONS = (
    "hidden_reasoning",
    "chain_of_thought",
    "migration_write_instructions",
    "target_repo_file_contents",
    "project_source_code",
    "generated_shim_contents",
    "memory_state_file_bodies",
    "raw_env",
    "api_key_material",
)
DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_SECTION_FRAGMENTS = (
    "reasoning",
    "chain_of_thought",
    "migration",
    "source_code",
    "file_contents",
    "env",
    "api_key",
    "token",
    "credential",
)
DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_CONTENT = (
    "api-key values",
    "api-key prefixes or suffixes",
    ".env values",
    "raw env text",
    "credentials",
    "tokens",
    "target-repo file contents",
    "project source code",
    "generated shim contents",
    "memory/state file bodies",
    "hidden reasoning requests",
    "migration-write instructions",
    "network execution instructions",
    "graphify instructions",
    "report-writing instructions",
    "unconstrained free-form repo text",
)
DASHSCOPE_OFFLINE_PROMPT_POLICY_KEYS = (
    "scope",
    "uses_only_deterministic_request_shape_metadata",
    "uses_only_deterministic_inventory_metadata",
    "allows_custom_section_content",
    "includes_env_values",
    "includes_api_key_values",
    "includes_project_source_code",
    "includes_target_repo_file_contents",
    "includes_hidden_reasoning",
    "includes_migration_write_instructions",
    "forbidden_section_handling",
    "unknown_section_handling",
)
DASHSCOPE_OFFLINE_PROMPT_POLICY = {
    "scope": "future-hermes-qwen-prompt-template",
    "uses_only_deterministic_request_shape_metadata": True,
    "uses_only_deterministic_inventory_metadata": True,
    "allows_custom_section_content": False,
    "includes_env_values": False,
    "includes_api_key_values": False,
    "includes_project_source_code": False,
    "includes_target_repo_file_contents": False,
    "includes_hidden_reasoning": False,
    "includes_migration_write_instructions": False,
    "forbidden_section_handling": "reject",
    "unknown_section_handling": "reject",
}
DASHSCOPE_OFFLINE_PROMPT_REQUEST_KEYS = (
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
DASHSCOPE_OFFLINE_PROMPT_INPUT_SUMMARY_KEYS = (
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


def _assert_non_negative_int(label: str, value: object) -> int:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer.")
    return value


def _normalize_request_shape(payload: DashScopeOfflinePromptTemplate | dict[str, object] | object) -> dict[str, object]:
    request_shape = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)
    actual_keys = set(request_shape.keys())
    expected_keys = set(DASHSCOPE_OFFLINE_PROMPT_REQUEST_KEYS)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        parts = ["Offline DashScope/Qwen prompt templating received a drifted request shape."]
        if missing:
            parts.append(f"Missing keys: {missing}.")
        if unexpected:
            parts.append(f"Unexpected keys: {unexpected}.")
        raise ValueError(" ".join(parts))

    if _assert_string("request shape source", request_shape["source"]) != DASHSCOPE_OFFLINE_REQUEST_SOURCE:
        raise ValueError("Offline prompt templating requires hermes_inventory request shape input.")
    if _assert_string("request shape mode", request_shape["mode"]) != DASHSCOPE_OFFLINE_REQUEST_MODE:
        raise ValueError("Offline prompt templating requires offline_request_shape_only input mode.")
    if _assert_string("request shape version", request_shape["request_shape_version"]) != DASHSCOPE_OFFLINE_REQUEST_SHAPE_VERSION:
        raise ValueError("Offline prompt templating received an unexpected request-shape version.")
    if _assert_string("request shape intended_model", request_shape["intended_model"]) != DASHSCOPE_INTENDED_MODEL:
        raise ValueError("Offline prompt templating requires the governed intended model.")
    if _assert_bool("request shape runtime_enabled", request_shape["runtime_enabled"]):
        raise ValueError("Offline prompt templating requires runtime_enabled=false.")
    if _assert_bool("request shape network_calls_allowed", request_shape["network_calls_allowed"]):
        raise ValueError("Offline prompt templating requires network_calls_allowed=false.")
    if _assert_bool("request shape qwen_dashscope_enabled", request_shape["qwen_dashscope_enabled"]):
        raise ValueError("Offline prompt templating requires qwen_dashscope_enabled=false.")
    if _assert_bool("request shape graphify_enabled", request_shape["graphify_enabled"]):
        raise ValueError("Offline prompt templating requires graphify_enabled=false.")
    if _assert_bool("request shape migration_writes_enabled", request_shape["migration_writes_enabled"]):
        raise ValueError("Offline prompt templating requires migration_writes_enabled=false.")

    request_policy = _assert_json_object("request shape request_policy", request_shape["request_policy"])
    _assert_string("request shape request_policy.scope", request_policy.get("scope"))

    input_summary = _assert_json_object("request shape input_summary", request_shape["input_summary"])
    actual_summary_keys = set(input_summary.keys())
    expected_summary_keys = set(DASHSCOPE_OFFLINE_PROMPT_INPUT_SUMMARY_KEYS)
    if actual_summary_keys != expected_summary_keys:
        raise ValueError("Offline prompt templating received a drifted request-shape input summary.")
    if _assert_string("request shape input_summary.source_command", input_summary["source_command"]) != DASHSCOPE_OFFLINE_REQUEST_SOURCE:
        raise ValueError("Offline prompt templating requires hermes_inventory as the source command.")
    if _assert_string("request shape input_summary.source_mode", input_summary["source_mode"]) != "inventory":
        raise ValueError("Offline prompt templating requires inventory mode.")
    if not _assert_bool("request shape input_summary.source_dry_run", input_summary["source_dry_run"]):
        raise ValueError("Offline prompt templating requires dry-run Hermes inventory input.")

    classification_counts = _assert_json_object(
        "request shape input_summary.classification_counts",
        input_summary["classification_counts"],
    )
    if set(classification_counts.keys()) != set(DASHSCOPE_OFFLINE_REQUEST_CLASSIFICATION_COUNT_KEYS):
        raise ValueError("Offline prompt templating received drifted Hermes classification counts.")
    for key in DASHSCOPE_OFFLINE_REQUEST_CLASSIFICATION_COUNT_KEYS:
        _assert_non_negative_int(
            f"request shape input_summary.classification_counts.{key}",
            classification_counts[key],
        )

    return request_shape


def sanitize_dashscope_prompt_section_overrides(candidate_sections: dict[str, object] | None) -> dict[str, str]:
    if not candidate_sections:
        return {}

    if not isinstance(candidate_sections, dict):
        raise ValueError("Offline DashScope/Qwen prompt template section overrides must be an object.")

    forbidden = []
    custom = []
    unexpected = []

    for key, value in candidate_sections.items():
        if not isinstance(value, str):
            raise ValueError(f"Offline DashScope/Qwen prompt template section `{key}` must be a string.")
        key_lower = key.lower()
        if key in DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_SECTIONS or any(
            fragment in key_lower for fragment in DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_SECTION_FRAGMENTS
        ):
            forbidden.append(key)
            continue
        if key in DASHSCOPE_OFFLINE_PROMPT_ALLOWED_SECTIONS:
            custom.append(key)
            continue
        unexpected.append(key)

    if forbidden:
        raise ValueError(
            "Offline DashScope/Qwen prompt template contains forbidden sections: "
            + ", ".join(sorted(forbidden))
            + "."
        )
    if custom:
        raise ValueError(
            "Offline DashScope/Qwen prompt template does not allow custom section content yet: "
            + ", ".join(sorted(custom))
            + "."
        )
    if unexpected:
        raise ValueError(
            "Offline DashScope/Qwen prompt template does not allow extra sections yet: "
            + ", ".join(sorted(unexpected))
            + "."
        )
    return {}


def _render_classification_counts(classification_counts: dict[str, object]) -> str:
    return ", ".join(
        f"{key}={_assert_non_negative_int(f'classification_counts.{key}', classification_counts[key])}"
        for key in DASHSCOPE_OFFLINE_REQUEST_CLASSIFICATION_COUNT_KEYS
    )


@dataclass(frozen=True)
class DashScopeOfflinePromptTemplate:
    prompt_template_version: str
    source: str
    mode: str
    intended_model: str
    selected_model: str
    model_policy_status: str
    model_policy_ready: bool
    model_policy_requires_update: bool
    local_config_ready: bool
    runtime_enabled: bool
    network_calls_allowed: bool
    qwen_dashscope_enabled: bool
    graphify_enabled: bool
    migration_writes_enabled: bool
    request_shape_version: str
    request_shape_source: str
    request_shape_mode: str
    request_shape_scope: str
    allowed_sections: tuple[str, ...]
    required_sections: tuple[str, ...]
    forbidden_sections: tuple[str, ...]
    forbidden_content: tuple[str, ...]
    prompt_policy: dict[str, object]
    rendered_sections: dict[str, str]

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "prompt_template_version": self.prompt_template_version,
            "source": self.source,
            "mode": self.mode,
            "intended_model": self.intended_model,
            "selected_model": self.selected_model,
            "model_policy_status": self.model_policy_status,
            "model_policy_ready": self.model_policy_ready,
            "model_policy_requires_update": self.model_policy_requires_update,
            "local_config_ready": self.local_config_ready,
            "runtime_enabled": self.runtime_enabled,
            "network_calls_allowed": self.network_calls_allowed,
            "qwen_dashscope_enabled": self.qwen_dashscope_enabled,
            "graphify_enabled": self.graphify_enabled,
            "migration_writes_enabled": self.migration_writes_enabled,
            "request_shape_version": self.request_shape_version,
            "request_shape_source": self.request_shape_source,
            "request_shape_mode": self.request_shape_mode,
            "request_shape_scope": self.request_shape_scope,
            "allowed_sections": list(self.allowed_sections),
            "required_sections": list(self.required_sections),
            "forbidden_sections": list(self.forbidden_sections),
            "forbidden_content": list(self.forbidden_content),
            "prompt_policy": dict(self.prompt_policy),
            "rendered_sections": dict(self.rendered_sections),
        }


def build_hermes_qwen_offline_prompt_template(
    request_shape: DashScopeOfflinePromptTemplate | dict[str, object] | object,
    *,
    candidate_sections: dict[str, object] | None = None,
) -> DashScopeOfflinePromptTemplate:
    sanitize_dashscope_prompt_section_overrides(candidate_sections)

    payload = _normalize_request_shape(request_shape)
    input_summary = _assert_json_object("request shape input_summary", payload["input_summary"])
    request_policy = _assert_json_object("request shape request_policy", payload["request_policy"])
    request_shape_scope = _assert_string("request shape request_policy.scope", request_policy["scope"])
    inventory_summary = _assert_string("request shape input_summary.inventory_summary", input_summary["inventory_summary"])
    root_count = _assert_non_negative_int("request shape input_summary.root_count", input_summary["root_count"])
    total_project_count = _assert_non_negative_int(
        "request shape input_summary.total_project_count",
        input_summary["total_project_count"],
    )
    warning_count = _assert_non_negative_int("request shape input_summary.warning_count", input_summary["warning_count"])
    error_count = _assert_non_negative_int("request shape input_summary.error_count", input_summary["error_count"])
    classification_counts = _assert_json_object(
        "request shape input_summary.classification_counts",
        input_summary["classification_counts"],
    )

    rendered_sections = {
        "system_role": (
            "You are the future Hermes-to-Qwen analysis assistant for workflow-manager. "
            "Use governed metadata only."
        ),
        "task": (
            "Review the deterministic Hermes inventory summary and prepare a safe offline analysis prompt "
            "without enabling runtime Qwen behavior."
        ),
        "source_of_truth": (
            "Use only the governed offline request-shape metadata from hermes_inventory dry-run output, "
            "the safety flags, and the governed model policy."
        ),
        "inventory_summary": (
            f"{inventory_summary} Roots={root_count}; projects={total_project_count}; "
            f"warnings={warning_count}; errors={error_count}."
        ),
        "classification_counts": _render_classification_counts(classification_counts) + ".",
        "safety_constraints": (
            "Keep runtime_enabled=false, network_calls_allowed=false, qwen_dashscope_enabled=false, "
            "graphify_enabled=false, migration_writes_enabled=false, and target-repo writes disabled."
        ),
        "forbidden_actions": (
            "Do not include secrets, .env values, credentials, tokens, root/project paths, source code, "
            "target-repo file contents, hidden reasoning requests, migration-write instructions, "
            "Graphify actions, or report-writing actions."
        ),
        "expected_output_shape": (
            "Return a concise structured result with readiness_status, evidence, blockers_or_open_questions, "
            "and next_safe_step."
        ),
        "redaction_policy": (
            f"Treat {DASHSCOPE_INTENDED_MODEL} as non-secret model metadata. Exclude API-key material, "
            "env values, file bodies, and unconstrained repo text."
        ),
    }

    return DashScopeOfflinePromptTemplate(
        prompt_template_version=DASHSCOPE_OFFLINE_PROMPT_TEMPLATE_VERSION,
        source=DASHSCOPE_OFFLINE_PROMPT_SOURCE,
        mode=DASHSCOPE_OFFLINE_PROMPT_MODE,
        intended_model=_assert_string("request shape intended_model", payload["intended_model"]),
        selected_model=_assert_string("request shape selected_model", payload["selected_model"]),
        model_policy_status=_assert_string("request shape model_policy_status", payload["model_policy_status"]),
        model_policy_ready=_assert_bool("request shape model_policy_ready", payload["model_policy_ready"]),
        model_policy_requires_update=_assert_bool(
            "request shape model_policy_requires_update",
            payload["model_policy_requires_update"],
        ),
        local_config_ready=_assert_bool("request shape local_config_ready", payload["local_config_ready"]),
        runtime_enabled=_assert_bool("request shape runtime_enabled", payload["runtime_enabled"]),
        network_calls_allowed=_assert_bool(
            "request shape network_calls_allowed",
            payload["network_calls_allowed"],
        ),
        qwen_dashscope_enabled=_assert_bool(
            "request shape qwen_dashscope_enabled",
            payload["qwen_dashscope_enabled"],
        ),
        graphify_enabled=_assert_bool("request shape graphify_enabled", payload["graphify_enabled"]),
        migration_writes_enabled=_assert_bool(
            "request shape migration_writes_enabled",
            payload["migration_writes_enabled"],
        ),
        request_shape_version=_assert_string("request shape version", payload["request_shape_version"]),
        request_shape_source=_assert_string("request shape source", payload["source"]),
        request_shape_mode=_assert_string("request shape mode", payload["mode"]),
        request_shape_scope=request_shape_scope,
        allowed_sections=DASHSCOPE_OFFLINE_PROMPT_ALLOWED_SECTIONS,
        required_sections=DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS,
        forbidden_sections=DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_SECTIONS,
        forbidden_content=DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_CONTENT,
        prompt_policy=DASHSCOPE_OFFLINE_PROMPT_POLICY,
        rendered_sections=rendered_sections,
    )
