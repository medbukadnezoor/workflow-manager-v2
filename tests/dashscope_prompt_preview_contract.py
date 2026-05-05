from __future__ import annotations

from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL
from workflow_manager.dashscope_prompt import DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS
from workflow_manager.dashscope_prompt_preview import (
    DASHSCOPE_OFFLINE_PROMPT_PREVIEW_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_PROMPT_PREVIEW_MODE,
    DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SECTION_ORDER,
    DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SOURCE,
    DASHSCOPE_OFFLINE_PROMPT_PREVIEW_TYPE,
    DASHSCOPE_OFFLINE_PROMPT_PREVIEW_VERSION,
)
from workflow_manager.dashscope_request import DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS


EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_FIELDS = DASHSCOPE_OFFLINE_PROMPT_PREVIEW_ALLOWED_FIELDS
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_VERSION = DASHSCOPE_OFFLINE_PROMPT_PREVIEW_VERSION
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_TYPE = DASHSCOPE_OFFLINE_PROMPT_PREVIEW_TYPE
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SOURCE = DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SOURCE
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_MODE = DASHSCOPE_OFFLINE_PROMPT_PREVIEW_MODE
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SECTION_ORDER = DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SECTION_ORDER
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_INTENDED_MODEL = DASHSCOPE_INTENDED_MODEL
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_INPUT_SUMMARY_KEYS = DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS
ALLOWED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_MODEL_POLICY_STATUSES = (
    "default",
    "explicit-match",
    "fallback-match",
    "mismatch",
)


def verify_dashscope_offline_prompt_preview_contract(payload: dict | object) -> dict:
    preview = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)

    actual_keys = set(preview.keys())
    expected_keys = set(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_FIELDS)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        parts = ["DashScope offline prompt preview contract keys drifted."]
        if missing:
            parts.append(f"Missing keys: {missing}.")
        if unexpected:
            parts.append(f"Unexpected keys: {unexpected}.")
        raise AssertionError(" ".join(parts))

    if preview["prompt_preview_version"] != EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_VERSION:
        raise AssertionError("DashScope offline prompt preview version drifted.")
    if preview["preview_type"] != EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_TYPE:
        raise AssertionError("DashScope offline prompt preview type drifted.")
    if preview["source"] != EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SOURCE:
        raise AssertionError("DashScope offline prompt preview source drifted.")
    if preview["mode"] != EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_MODE:
        raise AssertionError("DashScope offline prompt preview mode drifted.")
    if preview["preview_only"] is not True:
        raise AssertionError("DashScope offline prompt preview must remain preview-only.")
    if preview["prompt_execution_enabled"] is not False:
        raise AssertionError("DashScope offline prompt preview must keep prompt execution disabled.")
    if preview["intended_model"] != EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_INTENDED_MODEL:
        raise AssertionError("DashScope offline prompt preview intended model drifted.")
    if not isinstance(preview["selected_model"], str):
        raise AssertionError("DashScope offline prompt preview selected_model must be a string.")
    if preview["model_policy_status"] not in ALLOWED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_MODEL_POLICY_STATUSES:
        raise AssertionError("DashScope offline prompt preview model policy status drifted.")
    if not isinstance(preview["model_policy_ready"], bool):
        raise AssertionError("DashScope offline prompt preview model_policy_ready must be a boolean.")
    if not isinstance(preview["model_policy_requires_update"], bool):
        raise AssertionError("DashScope offline prompt preview model_policy_requires_update must be a boolean.")
    if not isinstance(preview["local_config_ready"], bool):
        raise AssertionError("DashScope offline prompt preview local_config_ready must be a boolean.")
    if preview["runtime_enabled"] is not False:
        raise AssertionError("DashScope offline prompt preview runtime_enabled must remain false.")
    if preview["network_calls_allowed"] is not False:
        raise AssertionError("DashScope offline prompt preview network_calls_allowed must remain false.")
    if preview["qwen_dashscope_enabled"] is not False:
        raise AssertionError("DashScope offline prompt preview qwen_dashscope_enabled must remain false.")
    if preview["graphify_enabled"] is not False:
        raise AssertionError("DashScope offline prompt preview graphify_enabled must remain false.")
    if preview["migration_writes_enabled"] is not False:
        raise AssertionError("DashScope offline prompt preview migration_writes_enabled must remain false.")

    if preview["request_shape_source"] != "hermes_inventory":
        raise AssertionError("DashScope offline prompt preview request_shape_source must remain hermes_inventory.")
    if preview["request_shape_mode"] != "offline_request_shape_only":
        raise AssertionError("DashScope offline prompt preview request_shape_mode must remain offline_request_shape_only.")
    if preview["prompt_template_mode"] != "offline_prompt_template_only":
        raise AssertionError("DashScope offline prompt preview prompt_template_mode must remain offline_prompt_template_only.")

    if preview["section_order"] != list(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SECTION_ORDER):
        raise AssertionError("DashScope offline prompt preview section_order drifted.")

    sections = preview["sections"]
    if not isinstance(sections, dict):
        raise AssertionError("DashScope offline prompt preview sections must be an object.")
    if tuple(sections.keys()) != EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SECTION_ORDER:
        raise AssertionError("DashScope offline prompt preview sections keys drifted.")
    if tuple(sections.keys()) != DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS:
        raise AssertionError("DashScope offline prompt preview sections must stay aligned with the prompt-template requirements.")
    if not all(isinstance(value, str) and value.strip() for value in sections.values()):
        raise AssertionError("DashScope offline prompt preview section values must be non-empty strings.")

    assembled = preview["assembled_prompt_preview"]
    if not isinstance(assembled, str) or not assembled.strip():
        raise AssertionError("DashScope offline prompt preview assembled_prompt_preview must be a non-empty string.")
    for key in EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SECTION_ORDER:
        if sections[key] not in assembled:
            raise AssertionError(f"DashScope offline prompt preview must include section `{key}` in the assembled preview.")

    if preview["redaction_policy"] != sections["redaction_policy"]:
        raise AssertionError("DashScope offline prompt preview redaction_policy must stay aligned with the rendered section.")
    if "qwen3.6-plus" not in preview["redaction_policy"]:
        raise AssertionError("DashScope offline prompt preview redaction_policy must keep the intended model explicit.")

    if not isinstance(preview["forbidden_content_policy"], list) or not preview["forbidden_content_policy"]:
        raise AssertionError("DashScope offline prompt preview forbidden_content_policy must be a non-empty list.")
    if "hidden reasoning requests" not in preview["forbidden_content_policy"]:
        raise AssertionError("DashScope offline prompt preview forbidden_content_policy drifted.")

    input_summary = preview["input_summary"]
    if not isinstance(input_summary, dict):
        raise AssertionError("DashScope offline prompt preview input_summary must be an object.")
    if set(input_summary.keys()) != set(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_PREVIEW_INPUT_SUMMARY_KEYS):
        raise AssertionError("DashScope offline prompt preview input_summary keys drifted.")
    if input_summary["source_command"] != "hermes_inventory":
        raise AssertionError("DashScope offline prompt preview input_summary.source_command must remain hermes_inventory.")
    if input_summary["source_mode"] != "inventory":
        raise AssertionError("DashScope offline prompt preview input_summary.source_mode must remain inventory.")
    if input_summary["source_dry_run"] is not True:
        raise AssertionError("DashScope offline prompt preview input_summary.source_dry_run must remain true.")

    return preview
