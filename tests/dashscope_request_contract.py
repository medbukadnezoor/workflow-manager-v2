from __future__ import annotations

from workflow_manager.dashscope_request import (
    DASHSCOPE_OFFLINE_REQUEST_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_REQUEST_FORBIDDEN_FIELDS,
    DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS,
    DASHSCOPE_OFFLINE_REQUEST_MODE,
    DASHSCOPE_OFFLINE_REQUEST_POLICY,
    DASHSCOPE_OFFLINE_REQUEST_POLICY_KEYS,
    DASHSCOPE_OFFLINE_REQUEST_SHAPE_VERSION,
    DASHSCOPE_OFFLINE_REQUEST_SOURCE,
)
from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL


EXPECTED_DASHSCOPE_OFFLINE_REQUEST_KEYS = DASHSCOPE_OFFLINE_REQUEST_ALLOWED_FIELDS
EXPECTED_DASHSCOPE_OFFLINE_REQUEST_POLICY_KEYS = DASHSCOPE_OFFLINE_REQUEST_POLICY_KEYS
EXPECTED_DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS = DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS
EXPECTED_DASHSCOPE_OFFLINE_REQUEST_POLICY = DASHSCOPE_OFFLINE_REQUEST_POLICY
EXPECTED_DASHSCOPE_OFFLINE_REQUEST_FORBIDDEN_FIELDS = DASHSCOPE_OFFLINE_REQUEST_FORBIDDEN_FIELDS
EXPECTED_DASHSCOPE_OFFLINE_REQUEST_SHAPE_VERSION = DASHSCOPE_OFFLINE_REQUEST_SHAPE_VERSION
EXPECTED_DASHSCOPE_OFFLINE_REQUEST_SOURCE = DASHSCOPE_OFFLINE_REQUEST_SOURCE
EXPECTED_DASHSCOPE_OFFLINE_REQUEST_MODE = DASHSCOPE_OFFLINE_REQUEST_MODE
EXPECTED_DASHSCOPE_OFFLINE_REQUEST_INTENDED_MODEL = DASHSCOPE_INTENDED_MODEL
ALLOWED_DASHSCOPE_OFFLINE_REQUEST_MODEL_POLICY_STATUSES = (
    "default",
    "explicit-match",
    "fallback-match",
    "mismatch",
)
EXPECTED_DASHSCOPE_OFFLINE_REQUEST_CLASSIFICATION_COUNT_KEYS = (
    "v2",
    "legacy",
    "mixed",
    "unmanaged",
    "error",
)


def verify_dashscope_offline_request_contract(payload: dict | object) -> dict:
    request = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)

    actual_keys = set(request.keys())
    expected_keys = set(EXPECTED_DASHSCOPE_OFFLINE_REQUEST_KEYS)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        parts = ["DashScope offline request contract keys drifted."]
        if missing:
            parts.append(f"Missing keys: {missing}.")
        if unexpected:
            parts.append(f"Unexpected keys: {unexpected}.")
        raise AssertionError(" ".join(parts))

    if request["request_shape_version"] != EXPECTED_DASHSCOPE_OFFLINE_REQUEST_SHAPE_VERSION:
        raise AssertionError("DashScope offline request shape version drifted.")
    if request["source"] != EXPECTED_DASHSCOPE_OFFLINE_REQUEST_SOURCE:
        raise AssertionError("DashScope offline request source drifted.")
    if request["mode"] != EXPECTED_DASHSCOPE_OFFLINE_REQUEST_MODE:
        raise AssertionError("DashScope offline request mode drifted.")
    if request["intended_model"] != EXPECTED_DASHSCOPE_OFFLINE_REQUEST_INTENDED_MODEL:
        raise AssertionError("DashScope offline request intended model drifted.")
    if not isinstance(request["selected_model"], str):
        raise AssertionError("DashScope offline request selected_model must be a string.")
    if request["model_policy_status"] not in ALLOWED_DASHSCOPE_OFFLINE_REQUEST_MODEL_POLICY_STATUSES:
        raise AssertionError("DashScope offline request model policy status drifted.")
    if not isinstance(request["model_policy_ready"], bool):
        raise AssertionError("DashScope offline request model_policy_ready must be a boolean.")
    if not isinstance(request["model_policy_requires_update"], bool):
        raise AssertionError("DashScope offline request model_policy_requires_update must be a boolean.")
    if not isinstance(request["local_config_ready"], bool):
        raise AssertionError("DashScope offline request local_config_ready must be a boolean.")
    if request["runtime_enabled"] is not False:
        raise AssertionError("DashScope offline request runtime_enabled must remain false.")
    if request["network_calls_allowed"] is not False:
        raise AssertionError("DashScope offline request network_calls_allowed must remain false.")
    if request["qwen_dashscope_enabled"] is not False:
        raise AssertionError("DashScope offline request qwen_dashscope_enabled must remain false.")
    if request["graphify_enabled"] is not False:
        raise AssertionError("DashScope offline request graphify_enabled must remain false.")
    if request["migration_writes_enabled"] is not False:
        raise AssertionError("DashScope offline request migration_writes_enabled must remain false.")

    request_policy = request["request_policy"]
    if not isinstance(request_policy, dict):
        raise AssertionError("DashScope offline request request_policy must be an object.")
    if set(request_policy.keys()) != set(EXPECTED_DASHSCOPE_OFFLINE_REQUEST_POLICY_KEYS):
        raise AssertionError("DashScope offline request request_policy keys drifted.")
    if request_policy != EXPECTED_DASHSCOPE_OFFLINE_REQUEST_POLICY:
        raise AssertionError("DashScope offline request request_policy drifted from the governed policy.")

    input_summary = request["input_summary"]
    if not isinstance(input_summary, dict):
        raise AssertionError("DashScope offline request input_summary must be an object.")
    if set(input_summary.keys()) != set(EXPECTED_DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS):
        raise AssertionError("DashScope offline request input_summary keys drifted.")
    if input_summary["source_command"] != EXPECTED_DASHSCOPE_OFFLINE_REQUEST_SOURCE:
        raise AssertionError("DashScope offline request input_summary.source_command must remain hermes_inventory.")
    if input_summary["source_mode"] != "inventory":
        raise AssertionError("DashScope offline request input_summary.source_mode must remain inventory.")
    if input_summary["source_dry_run"] is not True:
        raise AssertionError("DashScope offline request input_summary.source_dry_run must remain true.")
    if not isinstance(input_summary["inventory_summary"], str):
        raise AssertionError("DashScope offline request input_summary.inventory_summary must be a string.")
    if not isinstance(input_summary["root_count"], int) or input_summary["root_count"] < 0:
        raise AssertionError("DashScope offline request input_summary.root_count must be a non-negative integer.")
    if not isinstance(input_summary["total_project_count"], int) or input_summary["total_project_count"] < 0:
        raise AssertionError("DashScope offline request input_summary.total_project_count must be a non-negative integer.")
    if not isinstance(input_summary["warning_count"], int) or input_summary["warning_count"] < 0:
        raise AssertionError("DashScope offline request input_summary.warning_count must be a non-negative integer.")
    if not isinstance(input_summary["error_count"], int) or input_summary["error_count"] < 0:
        raise AssertionError("DashScope offline request input_summary.error_count must be a non-negative integer.")

    classification_counts = input_summary["classification_counts"]
    if not isinstance(classification_counts, dict):
        raise AssertionError("DashScope offline request input_summary.classification_counts must be an object.")
    if set(classification_counts.keys()) != set(EXPECTED_DASHSCOPE_OFFLINE_REQUEST_CLASSIFICATION_COUNT_KEYS):
        raise AssertionError("DashScope offline request classification_counts drifted from the governed Hermes vocabulary.")
    if not all(isinstance(value, int) and value >= 0 for value in classification_counts.values()):
        raise AssertionError("DashScope offline request classification_counts must be non-negative integers.")

    root_classification_counts = input_summary["root_classification_counts"]
    if not isinstance(root_classification_counts, dict):
        raise AssertionError("DashScope offline request input_summary.root_classification_counts must be an object.")
    if not all(isinstance(key, str) for key in root_classification_counts.keys()):
        raise AssertionError("DashScope offline request root_classification_counts keys must be strings.")
    if not all(isinstance(value, int) and value >= 0 for value in root_classification_counts.values()):
        raise AssertionError("DashScope offline request root_classification_counts values must be non-negative integers.")

    forbidden_fields = request["forbidden_fields"]
    if forbidden_fields != list(EXPECTED_DASHSCOPE_OFFLINE_REQUEST_FORBIDDEN_FIELDS):
        raise AssertionError("DashScope offline request forbidden_fields drifted from the governed policy.")

    for forbidden in EXPECTED_DASHSCOPE_OFFLINE_REQUEST_FORBIDDEN_FIELDS:
        if forbidden in input_summary or forbidden in request_policy:
            raise AssertionError(f"DashScope offline request must not place forbidden field `{forbidden}` into safe payload sections.")

    return request
