from __future__ import annotations

from dataclasses import dataclass

from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL
from workflow_manager.dashscope_prompt import (
    DASHSCOPE_OFFLINE_PROMPT_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_PROMPT_ALLOWED_SECTIONS,
    DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_CONTENT,
    DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_SECTION_FRAGMENTS,
    DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_SECTIONS,
    DASHSCOPE_OFFLINE_PROMPT_MODE,
    DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS,
    DASHSCOPE_OFFLINE_PROMPT_SOURCE,
    DASHSCOPE_OFFLINE_PROMPT_TEMPLATE_VERSION,
)
from workflow_manager.dashscope_request import (
    DASHSCOPE_OFFLINE_REQUEST_CLASSIFICATION_COUNT_KEYS,
    DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS,
    DASHSCOPE_OFFLINE_REQUEST_MODE,
    DASHSCOPE_OFFLINE_REQUEST_SHAPE_VERSION,
    DASHSCOPE_OFFLINE_REQUEST_SOURCE,
)


DASHSCOPE_OFFLINE_PROMPT_PREVIEW_VERSION = "1.0.0"
DASHSCOPE_OFFLINE_PROMPT_PREVIEW_TYPE = "assembled_prompt_preview"
DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SOURCE = "hermes_inventory"
DASHSCOPE_OFFLINE_PROMPT_PREVIEW_MODE = "offline_prompt_preview_only"
DASHSCOPE_OFFLINE_PROMPT_PREVIEW_ALLOWED_FIELDS = (
    "prompt_preview_version",
    "preview_type",
    "source",
    "mode",
    "preview_only",
    "prompt_execution_enabled",
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
    "prompt_template_version",
    "prompt_template_mode",
    "section_order",
    "sections",
    "assembled_prompt_preview",
    "redaction_policy",
    "forbidden_content_policy",
    "input_summary",
)
DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SECTION_ORDER = DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS
DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SECTION_TITLES = {
    "system_role": "System Role",
    "task": "Task",
    "source_of_truth": "Source Of Truth",
    "inventory_summary": "Inventory Summary",
    "classification_counts": "Classification Counts",
    "safety_constraints": "Safety Constraints",
    "forbidden_actions": "Forbidden Actions",
    "expected_output_shape": "Expected Output Shape",
    "redaction_policy": "Redaction Policy",
}


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


def _normalize_request_shape(payload: DashScopeOfflinePromptPreview | dict[str, object] | object) -> dict[str, object]:
    request_shape = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)
    expected_keys = {
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
    }
    actual_keys = set(request_shape.keys())
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        parts = ["Offline DashScope/Qwen prompt preview received a drifted request shape."]
        if missing:
            parts.append(f"Missing keys: {missing}.")
        if unexpected:
            parts.append(f"Unexpected keys: {unexpected}.")
        raise ValueError(" ".join(parts))

    if _assert_string("request shape source", request_shape["source"]) != DASHSCOPE_OFFLINE_REQUEST_SOURCE:
        raise ValueError("Offline prompt preview requires hermes_inventory request-shape input.")
    if _assert_string("request shape mode", request_shape["mode"]) != DASHSCOPE_OFFLINE_REQUEST_MODE:
        raise ValueError("Offline prompt preview requires offline_request_shape_only mode.")
    if _assert_string("request shape version", request_shape["request_shape_version"]) != DASHSCOPE_OFFLINE_REQUEST_SHAPE_VERSION:
        raise ValueError("Offline prompt preview received an unexpected request-shape version.")
    if _assert_string("request shape intended_model", request_shape["intended_model"]) != DASHSCOPE_INTENDED_MODEL:
        raise ValueError("Offline prompt preview requires the governed intended model.")
    if _assert_bool("request shape runtime_enabled", request_shape["runtime_enabled"]):
        raise ValueError("Offline prompt preview requires runtime_enabled=false.")
    if _assert_bool("request shape network_calls_allowed", request_shape["network_calls_allowed"]):
        raise ValueError("Offline prompt preview requires network_calls_allowed=false.")
    if _assert_bool("request shape qwen_dashscope_enabled", request_shape["qwen_dashscope_enabled"]):
        raise ValueError("Offline prompt preview requires qwen_dashscope_enabled=false.")
    if _assert_bool("request shape graphify_enabled", request_shape["graphify_enabled"]):
        raise ValueError("Offline prompt preview requires graphify_enabled=false.")
    if _assert_bool("request shape migration_writes_enabled", request_shape["migration_writes_enabled"]):
        raise ValueError("Offline prompt preview requires migration_writes_enabled=false.")

    input_summary = _assert_json_object("request shape input_summary", request_shape["input_summary"])
    if set(input_summary.keys()) != set(DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS):
        raise ValueError("Offline prompt preview received a drifted request-shape input summary.")
    if _assert_string("request shape input_summary.source_command", input_summary["source_command"]) != DASHSCOPE_OFFLINE_REQUEST_SOURCE:
        raise ValueError("Offline prompt preview requires hermes_inventory as the source command.")
    if _assert_string("request shape input_summary.source_mode", input_summary["source_mode"]) != "inventory":
        raise ValueError("Offline prompt preview requires inventory mode.")
    if not _assert_bool("request shape input_summary.source_dry_run", input_summary["source_dry_run"]):
        raise ValueError("Offline prompt preview requires dry-run request-shape input.")
    classification_counts = _assert_json_object(
        "request shape input_summary.classification_counts",
        input_summary["classification_counts"],
    )
    if set(classification_counts.keys()) != set(DASHSCOPE_OFFLINE_REQUEST_CLASSIFICATION_COUNT_KEYS):
        raise ValueError("Offline prompt preview received drifted Hermes classification counts.")
    for key in DASHSCOPE_OFFLINE_REQUEST_CLASSIFICATION_COUNT_KEYS:
        _assert_non_negative_int(
            f"request shape input_summary.classification_counts.{key}",
            classification_counts[key],
        )
    return request_shape


def _normalize_prompt_template(payload: DashScopeOfflinePromptPreview | dict[str, object] | object) -> dict[str, object]:
    prompt_template = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)
    actual_keys = set(prompt_template.keys())
    expected_keys = set(DASHSCOPE_OFFLINE_PROMPT_ALLOWED_FIELDS)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        parts = ["Offline DashScope/Qwen prompt preview received a drifted prompt template."]
        if missing:
            parts.append(f"Missing keys: {missing}.")
        if unexpected:
            parts.append(f"Unexpected keys: {unexpected}.")
        raise ValueError(" ".join(parts))

    if _assert_string("prompt template source", prompt_template["source"]) != DASHSCOPE_OFFLINE_PROMPT_SOURCE:
        raise ValueError("Offline prompt preview requires hermes_inventory prompt-template input.")
    if _assert_string("prompt template mode", prompt_template["mode"]) != DASHSCOPE_OFFLINE_PROMPT_MODE:
        raise ValueError("Offline prompt preview requires offline_prompt_template_only mode.")
    if _assert_string("prompt template version", prompt_template["prompt_template_version"]) != DASHSCOPE_OFFLINE_PROMPT_TEMPLATE_VERSION:
        raise ValueError("Offline prompt preview received an unexpected prompt-template version.")
    if _assert_string("prompt template intended_model", prompt_template["intended_model"]) != DASHSCOPE_INTENDED_MODEL:
        raise ValueError("Offline prompt preview requires the governed intended model.")
    if _assert_bool("prompt template runtime_enabled", prompt_template["runtime_enabled"]):
        raise ValueError("Offline prompt preview requires runtime_enabled=false in the prompt template.")
    if _assert_bool("prompt template network_calls_allowed", prompt_template["network_calls_allowed"]):
        raise ValueError("Offline prompt preview requires network_calls_allowed=false in the prompt template.")
    if _assert_bool("prompt template qwen_dashscope_enabled", prompt_template["qwen_dashscope_enabled"]):
        raise ValueError("Offline prompt preview requires qwen_dashscope_enabled=false in the prompt template.")
    if _assert_bool("prompt template graphify_enabled", prompt_template["graphify_enabled"]):
        raise ValueError("Offline prompt preview requires graphify_enabled=false in the prompt template.")
    if _assert_bool("prompt template migration_writes_enabled", prompt_template["migration_writes_enabled"]):
        raise ValueError("Offline prompt preview requires migration_writes_enabled=false in the prompt template.")
    if tuple(prompt_template["allowed_sections"]) != DASHSCOPE_OFFLINE_PROMPT_ALLOWED_SECTIONS:
        raise ValueError("Offline prompt preview received drifted allowed prompt sections.")
    if tuple(prompt_template["required_sections"]) != DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS:
        raise ValueError("Offline prompt preview received drifted required prompt sections.")
    rendered_sections = _assert_json_object("prompt template rendered_sections", prompt_template["rendered_sections"])
    if tuple(rendered_sections.keys()) != DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS:
        raise ValueError("Offline prompt preview requires deterministic rendered prompt sections.")
    for key in DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS:
        _assert_string(f"prompt template rendered_sections.{key}", rendered_sections[key])
    return prompt_template


def sanitize_dashscope_prompt_preview_sections(candidate_sections: dict[str, object] | None) -> dict[str, str]:
    if not candidate_sections:
        return {}

    if not isinstance(candidate_sections, dict):
        raise ValueError("Offline DashScope/Qwen prompt preview section overrides must be an object.")

    forbidden = []
    custom = []
    unexpected = []
    for key, value in candidate_sections.items():
        if not isinstance(value, str):
            raise ValueError(f"Offline DashScope/Qwen prompt preview section `{key}` must be a string.")
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
            "Offline DashScope/Qwen prompt preview contains forbidden sections: "
            + ", ".join(sorted(forbidden))
            + "."
        )
    if custom:
        raise ValueError(
            "Offline DashScope/Qwen prompt preview does not allow custom section content yet: "
            + ", ".join(sorted(custom))
            + "."
        )
    if unexpected:
        raise ValueError(
            "Offline DashScope/Qwen prompt preview does not allow extra sections yet: "
            + ", ".join(sorted(unexpected))
            + "."
        )
    return {}


def _assemble_prompt_preview(section_order: tuple[str, ...], sections: dict[str, str]) -> str:
    parts = []
    for name in section_order:
        parts.append(f"## {DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SECTION_TITLES[name]}")
        parts.append(sections[name])
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


@dataclass(frozen=True)
class DashScopeOfflinePromptPreview:
    prompt_preview_version: str
    preview_type: str
    source: str
    mode: str
    preview_only: bool
    prompt_execution_enabled: bool
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
    prompt_template_version: str
    prompt_template_mode: str
    section_order: tuple[str, ...]
    sections: dict[str, str]
    assembled_prompt_preview: str
    redaction_policy: str
    forbidden_content_policy: tuple[str, ...]
    input_summary: dict[str, object]

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "prompt_preview_version": self.prompt_preview_version,
            "preview_type": self.preview_type,
            "source": self.source,
            "mode": self.mode,
            "preview_only": self.preview_only,
            "prompt_execution_enabled": self.prompt_execution_enabled,
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
            "prompt_template_version": self.prompt_template_version,
            "prompt_template_mode": self.prompt_template_mode,
            "section_order": list(self.section_order),
            "sections": dict(self.sections),
            "assembled_prompt_preview": self.assembled_prompt_preview,
            "redaction_policy": self.redaction_policy,
            "forbidden_content_policy": list(self.forbidden_content_policy),
            "input_summary": dict(self.input_summary),
        }


def build_hermes_qwen_offline_prompt_preview(
    request_shape: DashScopeOfflinePromptPreview | dict[str, object] | object,
    prompt_template: DashScopeOfflinePromptPreview | dict[str, object] | object,
    *,
    candidate_sections: dict[str, object] | None = None,
) -> DashScopeOfflinePromptPreview:
    sanitize_dashscope_prompt_preview_sections(candidate_sections)

    request_payload = _normalize_request_shape(request_shape)
    prompt_payload = _normalize_prompt_template(prompt_template)
    input_summary = _assert_json_object("request shape input_summary", request_payload["input_summary"])
    rendered_sections = _assert_json_object("prompt template rendered_sections", prompt_payload["rendered_sections"])

    if request_payload["request_shape_version"] != prompt_payload["request_shape_version"]:
        raise ValueError("Offline prompt preview requires request-shape version linkage to remain exact.")
    if request_payload["source"] != prompt_payload["request_shape_source"]:
        raise ValueError("Offline prompt preview requires prompt-template linkage to the same request source.")
    if request_payload["mode"] != prompt_payload["request_shape_mode"]:
        raise ValueError("Offline prompt preview requires prompt-template linkage to the same request mode.")
    if request_payload["intended_model"] != prompt_payload["intended_model"]:
        raise ValueError("Offline prompt preview requires matching intended model metadata.")
    if request_payload["selected_model"] != prompt_payload["selected_model"]:
        raise ValueError("Offline prompt preview requires matching selected model metadata.")
    if request_payload["model_policy_status"] != prompt_payload["model_policy_status"]:
        raise ValueError("Offline prompt preview requires matching model policy status.")

    section_order = DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SECTION_ORDER
    sections = {name: rendered_sections[name] for name in section_order}
    assembled_prompt_preview = _assemble_prompt_preview(section_order, sections)

    return DashScopeOfflinePromptPreview(
        prompt_preview_version=DASHSCOPE_OFFLINE_PROMPT_PREVIEW_VERSION,
        preview_type=DASHSCOPE_OFFLINE_PROMPT_PREVIEW_TYPE,
        source=DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SOURCE,
        mode=DASHSCOPE_OFFLINE_PROMPT_PREVIEW_MODE,
        preview_only=True,
        prompt_execution_enabled=False,
        intended_model=_assert_string("request shape intended_model", request_payload["intended_model"]),
        selected_model=_assert_string("request shape selected_model", request_payload["selected_model"]),
        model_policy_status=_assert_string("request shape model_policy_status", request_payload["model_policy_status"]),
        model_policy_ready=_assert_bool("request shape model_policy_ready", request_payload["model_policy_ready"]),
        model_policy_requires_update=_assert_bool(
            "request shape model_policy_requires_update",
            request_payload["model_policy_requires_update"],
        ),
        local_config_ready=_assert_bool("request shape local_config_ready", request_payload["local_config_ready"]),
        runtime_enabled=False,
        network_calls_allowed=False,
        qwen_dashscope_enabled=False,
        graphify_enabled=False,
        migration_writes_enabled=False,
        request_shape_version=_assert_string("request shape version", request_payload["request_shape_version"]),
        request_shape_source=_assert_string("request shape source", request_payload["source"]),
        request_shape_mode=_assert_string("request shape mode", request_payload["mode"]),
        prompt_template_version=_assert_string(
            "prompt template version",
            prompt_payload["prompt_template_version"],
        ),
        prompt_template_mode=_assert_string("prompt template mode", prompt_payload["mode"]),
        section_order=section_order,
        sections=sections,
        assembled_prompt_preview=assembled_prompt_preview,
        redaction_policy=_assert_string(
            "prompt template rendered_sections.redaction_policy",
            rendered_sections["redaction_policy"],
        ),
        forbidden_content_policy=DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_CONTENT,
        input_summary=input_summary,
    )
