from __future__ import annotations

from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL
from workflow_manager.dashscope_response import (
    DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS,
    DASHSCOPE_OFFLINE_RESPONSE_FIELD_ORDER,
    DASHSCOPE_OFFLINE_RESPONSE_FORBIDDEN_RESPONSE_FIELDS,
    DASHSCOPE_OFFLINE_RESPONSE_MODE,
    DASHSCOPE_OFFLINE_RESPONSE_REQUIRED_RESPONSE_FIELDS,
    DASHSCOPE_OFFLINE_RESPONSE_SHAPE_VERSION,
    DASHSCOPE_OFFLINE_RESPONSE_SOURCE,
    DASHSCOPE_OFFLINE_RESPONSE_SOURCE_OF_TRUTH_POLICY,
    DASHSCOPE_OFFLINE_RESPONSE_TYPE,
)
from workflow_manager.dashscope_request import DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS


EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_FIELDS = DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_FIELDS
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_SHAPE_VERSION = DASHSCOPE_OFFLINE_RESPONSE_SHAPE_VERSION
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_TYPE = DASHSCOPE_OFFLINE_RESPONSE_TYPE
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_SOURCE = DASHSCOPE_OFFLINE_RESPONSE_SOURCE
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_MODE = DASHSCOPE_OFFLINE_RESPONSE_MODE
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_INTENDED_MODEL = DASHSCOPE_INTENDED_MODEL
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS = DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_REQUIRED_RESPONSE_FIELDS = DASHSCOPE_OFFLINE_RESPONSE_REQUIRED_RESPONSE_FIELDS
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_FIELD_ORDER = DASHSCOPE_OFFLINE_RESPONSE_FIELD_ORDER
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_FORBIDDEN_RESPONSE_FIELDS = DASHSCOPE_OFFLINE_RESPONSE_FORBIDDEN_RESPONSE_FIELDS
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_SOURCE_OF_TRUTH_POLICY = DASHSCOPE_OFFLINE_RESPONSE_SOURCE_OF_TRUTH_POLICY
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_INPUT_SUMMARY_KEYS = DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS
ALLOWED_DASHSCOPE_OFFLINE_RESPONSE_MODEL_POLICY_STATUSES = (
    "default",
    "explicit-match",
    "fallback-match",
    "mismatch",
)


def verify_dashscope_offline_response_contract(payload: dict | object) -> dict:
    response = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)

    actual_keys = set(response.keys())
    expected_keys = set(EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_FIELDS)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        parts = ["DashScope offline response contract keys drifted."]
        if missing:
            parts.append(f"Missing keys: {missing}.")
        if unexpected:
            parts.append(f"Unexpected keys: {unexpected}.")
        raise AssertionError(" ".join(parts))

    if response["response_shape_version"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_SHAPE_VERSION:
        raise AssertionError("DashScope offline response version drifted.")
    if response["response_type"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_TYPE:
        raise AssertionError("DashScope offline response type drifted.")
    if response["source"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_SOURCE:
        raise AssertionError("DashScope offline response source drifted.")
    if response["mode"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_MODE:
        raise AssertionError("DashScope offline response mode drifted.")
    if response["intended_model"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_INTENDED_MODEL:
        raise AssertionError("DashScope offline response intended model drifted.")
    if not isinstance(response["selected_model"], str):
        raise AssertionError("DashScope offline response selected_model must be a string.")
    if response["model_policy_status"] not in ALLOWED_DASHSCOPE_OFFLINE_RESPONSE_MODEL_POLICY_STATUSES:
        raise AssertionError("DashScope offline response model policy status drifted.")
    if not isinstance(response["model_policy_ready"], bool):
        raise AssertionError("DashScope offline response model_policy_ready must be a boolean.")
    if not isinstance(response["model_policy_requires_update"], bool):
        raise AssertionError("DashScope offline response model_policy_requires_update must be a boolean.")
    if not isinstance(response["local_config_ready"], bool):
        raise AssertionError("DashScope offline response local_config_ready must be a boolean.")
    if response["runtime_enabled"] is not False:
        raise AssertionError("DashScope offline response runtime_enabled must remain false.")
    if response["network_calls_allowed"] is not False:
        raise AssertionError("DashScope offline response network_calls_allowed must remain false.")
    if response["qwen_dashscope_enabled"] is not False:
        raise AssertionError("DashScope offline response qwen_dashscope_enabled must remain false.")
    if response["graphify_enabled"] is not False:
        raise AssertionError("DashScope offline response graphify_enabled must remain false.")
    if response["migration_writes_enabled"] is not False:
        raise AssertionError("DashScope offline response migration_writes_enabled must remain false.")
    if response["preview_type"] != "assembled_prompt_preview":
        raise AssertionError("DashScope offline response preview_type must remain assembled_prompt_preview.")
    if response["prompt_preview_mode"] != "offline_prompt_preview_only":
        raise AssertionError("DashScope offline response prompt_preview_mode must remain offline_prompt_preview_only.")
    if response["preview_only"] is not True:
        raise AssertionError("DashScope offline response must remain preview-only.")
    if response["response_explanatory_only"] is not True:
        raise AssertionError("DashScope offline response must remain explanatory-only.")
    if response["live_response_parsing_enabled"] is not False:
        raise AssertionError("DashScope offline response must keep live response parsing disabled.")

    if tuple(response["allowed_response_fields"]) != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS:
        raise AssertionError("DashScope offline response allowed_response_fields drifted.")
    if tuple(response["required_response_fields"]) != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_REQUIRED_RESPONSE_FIELDS:
        raise AssertionError("DashScope offline response required_response_fields drifted.")
    if tuple(response["response_field_order"]) != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_FIELD_ORDER:
        raise AssertionError("DashScope offline response response_field_order drifted.")

    response_slots = response["response_slots"]
    if not isinstance(response_slots, dict):
        raise AssertionError("DashScope offline response response_slots must be an object.")
    if tuple(response_slots.keys()) != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_FIELD_ORDER:
        raise AssertionError("DashScope offline response response_slots keys drifted.")
    if not all(isinstance(value, str) and value.strip() for value in response_slots.values()):
        raise AssertionError("DashScope offline response response_slots values must be non-empty strings.")

    if tuple(response["forbidden_response_fields"]) != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_FORBIDDEN_RESPONSE_FIELDS:
        raise AssertionError("DashScope offline response forbidden_response_fields drifted.")
    if response["source_of_truth_policy"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_SOURCE_OF_TRUTH_POLICY:
        raise AssertionError("DashScope offline response source_of_truth_policy drifted.")
    if "source of truth" not in response["source_of_truth_policy"]:
        raise AssertionError("DashScope offline response source_of_truth_policy must stay explicit.")
    if "explanatory only" not in response["source_of_truth_policy"]:
        raise AssertionError("DashScope offline response must keep Qwen output explanatory only.")
    if "cannot authorize migration writes" not in response["source_of_truth_policy"]:
        raise AssertionError("DashScope offline response must keep migration-write authority blocked.")

    if not isinstance(response["forbidden_output_policy"], list) or not response["forbidden_output_policy"]:
        raise AssertionError("DashScope offline response forbidden_output_policy must be a non-empty list.")
    if "hidden reasoning or chain-of-thought" not in response["forbidden_output_policy"]:
        raise AssertionError("DashScope offline response forbidden_output_policy drifted.")
    if "claims that Qwen output is source of truth" not in response["forbidden_output_policy"]:
        raise AssertionError("DashScope offline response forbidden_output_policy must block source-of-truth overrides.")

    if response["redaction_policy"] != response_slots["redaction_policy"]:
        raise AssertionError("DashScope offline response redaction_policy must stay aligned with the response slot.")
    if "qwen3.6-plus" not in response["redaction_policy"]:
        raise AssertionError("DashScope offline response redaction_policy must keep the intended model explicit.")

    input_summary = response["input_summary"]
    if not isinstance(input_summary, dict):
        raise AssertionError("DashScope offline response input_summary must be an object.")
    if set(input_summary.keys()) != set(EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_INPUT_SUMMARY_KEYS):
        raise AssertionError("DashScope offline response input_summary keys drifted.")
    if input_summary["source_command"] != "hermes_inventory":
        raise AssertionError("DashScope offline response input_summary.source_command must remain hermes_inventory.")
    if input_summary["source_mode"] != "inventory":
        raise AssertionError("DashScope offline response input_summary.source_mode must remain inventory.")
    if input_summary["source_dry_run"] is not True:
        raise AssertionError("DashScope offline response input_summary.source_dry_run must remain true.")

    return response
