from __future__ import annotations

from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL
from workflow_manager.dashscope_prompt import (
    DASHSCOPE_OFFLINE_PROMPT_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_PROMPT_ALLOWED_SECTIONS,
    DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_CONTENT,
    DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_SECTIONS,
    DASHSCOPE_OFFLINE_PROMPT_MODE,
    DASHSCOPE_OFFLINE_PROMPT_POLICY,
    DASHSCOPE_OFFLINE_PROMPT_POLICY_KEYS,
    DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS,
    DASHSCOPE_OFFLINE_PROMPT_SOURCE,
    DASHSCOPE_OFFLINE_PROMPT_TEMPLATE_VERSION,
)


EXPECTED_DASHSCOPE_OFFLINE_PROMPT_FIELDS = DASHSCOPE_OFFLINE_PROMPT_ALLOWED_FIELDS
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_ALLOWED_SECTIONS = DASHSCOPE_OFFLINE_PROMPT_ALLOWED_SECTIONS
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS = DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_SECTIONS = DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_SECTIONS
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_CONTENT = DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_CONTENT
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_POLICY = DASHSCOPE_OFFLINE_PROMPT_POLICY
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_POLICY_KEYS = DASHSCOPE_OFFLINE_PROMPT_POLICY_KEYS
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_TEMPLATE_VERSION = DASHSCOPE_OFFLINE_PROMPT_TEMPLATE_VERSION
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_SOURCE = DASHSCOPE_OFFLINE_PROMPT_SOURCE
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_MODE = DASHSCOPE_OFFLINE_PROMPT_MODE
EXPECTED_DASHSCOPE_OFFLINE_PROMPT_INTENDED_MODEL = DASHSCOPE_INTENDED_MODEL
ALLOWED_DASHSCOPE_OFFLINE_PROMPT_MODEL_POLICY_STATUSES = (
    "default",
    "explicit-match",
    "fallback-match",
    "mismatch",
)


def verify_dashscope_offline_prompt_contract(payload: dict | object) -> dict:
    prompt = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)

    actual_keys = set(prompt.keys())
    expected_keys = set(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_FIELDS)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        parts = ["DashScope offline prompt contract keys drifted."]
        if missing:
            parts.append(f"Missing keys: {missing}.")
        if unexpected:
            parts.append(f"Unexpected keys: {unexpected}.")
        raise AssertionError(" ".join(parts))

    if prompt["prompt_template_version"] != EXPECTED_DASHSCOPE_OFFLINE_PROMPT_TEMPLATE_VERSION:
        raise AssertionError("DashScope offline prompt template version drifted.")
    if prompt["source"] != EXPECTED_DASHSCOPE_OFFLINE_PROMPT_SOURCE:
        raise AssertionError("DashScope offline prompt source drifted.")
    if prompt["mode"] != EXPECTED_DASHSCOPE_OFFLINE_PROMPT_MODE:
        raise AssertionError("DashScope offline prompt mode drifted.")
    if prompt["intended_model"] != EXPECTED_DASHSCOPE_OFFLINE_PROMPT_INTENDED_MODEL:
        raise AssertionError("DashScope offline prompt intended model drifted.")
    if not isinstance(prompt["selected_model"], str):
        raise AssertionError("DashScope offline prompt selected_model must be a string.")
    if prompt["model_policy_status"] not in ALLOWED_DASHSCOPE_OFFLINE_PROMPT_MODEL_POLICY_STATUSES:
        raise AssertionError("DashScope offline prompt model policy status drifted.")
    if not isinstance(prompt["model_policy_ready"], bool):
        raise AssertionError("DashScope offline prompt model_policy_ready must be a boolean.")
    if not isinstance(prompt["model_policy_requires_update"], bool):
        raise AssertionError("DashScope offline prompt model_policy_requires_update must be a boolean.")
    if not isinstance(prompt["local_config_ready"], bool):
        raise AssertionError("DashScope offline prompt local_config_ready must be a boolean.")
    if prompt["runtime_enabled"] is not False:
        raise AssertionError("DashScope offline prompt runtime_enabled must remain false.")
    if prompt["network_calls_allowed"] is not False:
        raise AssertionError("DashScope offline prompt network_calls_allowed must remain false.")
    if prompt["qwen_dashscope_enabled"] is not False:
        raise AssertionError("DashScope offline prompt qwen_dashscope_enabled must remain false.")
    if prompt["graphify_enabled"] is not False:
        raise AssertionError("DashScope offline prompt graphify_enabled must remain false.")
    if prompt["migration_writes_enabled"] is not False:
        raise AssertionError("DashScope offline prompt migration_writes_enabled must remain false.")

    if not isinstance(prompt["request_shape_version"], str):
        raise AssertionError("DashScope offline prompt request_shape_version must be a string.")
    if prompt["request_shape_source"] != "hermes_inventory":
        raise AssertionError("DashScope offline prompt request_shape_source must remain hermes_inventory.")
    if prompt["request_shape_mode"] != "offline_request_shape_only":
        raise AssertionError("DashScope offline prompt request_shape_mode must remain offline_request_shape_only.")
    if prompt["request_shape_scope"] != "future-hermes-qwen-request-blueprint":
        raise AssertionError("DashScope offline prompt request_shape_scope drifted.")

    if prompt["allowed_sections"] != list(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_ALLOWED_SECTIONS):
        raise AssertionError("DashScope offline prompt allowed_sections drifted.")
    if prompt["required_sections"] != list(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS):
        raise AssertionError("DashScope offline prompt required_sections drifted.")
    if prompt["forbidden_sections"] != list(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_SECTIONS):
        raise AssertionError("DashScope offline prompt forbidden_sections drifted.")
    if prompt["forbidden_content"] != list(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_CONTENT):
        raise AssertionError("DashScope offline prompt forbidden_content drifted.")

    prompt_policy = prompt["prompt_policy"]
    if not isinstance(prompt_policy, dict):
        raise AssertionError("DashScope offline prompt prompt_policy must be an object.")
    if set(prompt_policy.keys()) != set(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_POLICY_KEYS):
        raise AssertionError("DashScope offline prompt prompt_policy keys drifted.")
    if prompt_policy != EXPECTED_DASHSCOPE_OFFLINE_PROMPT_POLICY:
        raise AssertionError("DashScope offline prompt prompt_policy drifted from the governed policy.")

    rendered_sections = prompt["rendered_sections"]
    if not isinstance(rendered_sections, dict):
        raise AssertionError("DashScope offline prompt rendered_sections must be an object.")
    if set(rendered_sections.keys()) != set(EXPECTED_DASHSCOPE_OFFLINE_PROMPT_REQUIRED_SECTIONS):
        raise AssertionError("DashScope offline prompt rendered_sections keys drifted.")
    if not all(isinstance(value, str) and value.strip() for value in rendered_sections.values()):
        raise AssertionError("DashScope offline prompt rendered section values must be non-empty strings.")

    for forbidden in EXPECTED_DASHSCOPE_OFFLINE_PROMPT_FORBIDDEN_SECTIONS:
        if forbidden in rendered_sections:
            raise AssertionError(f"DashScope offline prompt must not expose forbidden section `{forbidden}`.")

    if "qwen3.6-plus" not in rendered_sections["redaction_policy"]:
        raise AssertionError("DashScope offline prompt redaction_policy must keep the intended model explicit.")

    return prompt
