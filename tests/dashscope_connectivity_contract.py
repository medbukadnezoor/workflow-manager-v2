from __future__ import annotations

from workflow_manager.dashscope_connectivity import (
    DASHSCOPE_CONNECTIVITY_ALLOWED_ERROR_CATEGORIES,
    DASHSCOPE_CONNECTIVITY_ALLOWED_FIELDS,
    DASHSCOPE_CONNECTIVITY_ALLOWED_HTTP_STATUS_CATEGORIES,
    DASHSCOPE_CONNECTIVITY_ALLOWED_STATUSES,
    DASHSCOPE_CONNECTIVITY_MODE,
    DASHSCOPE_CONNECTIVITY_POLICY_VERSION,
    DASHSCOPE_CONNECTIVITY_PROBE_ENDPOINT_LABEL,
    DASHSCOPE_CONNECTIVITY_PROBE_TYPE,
    DASHSCOPE_CONNECTIVITY_REQUEST_BODY_KIND,
    DASHSCOPE_CONNECTIVITY_REQUEST_METHOD,
    DASHSCOPE_CONNECTIVITY_SOURCE,
)
from workflow_manager.dashscope_env import (
    DASHSCOPE_ACTIVE_ENV_KEYS,
    DASHSCOPE_FALLBACK_ONLY_ENV_KEYS,
    DASHSCOPE_INTENDED_MODEL,
)


EXPECTED_DASHSCOPE_CONNECTIVITY_FIELDS = DASHSCOPE_CONNECTIVITY_ALLOWED_FIELDS
EXPECTED_DASHSCOPE_CONNECTIVITY_VERSION = DASHSCOPE_CONNECTIVITY_POLICY_VERSION
EXPECTED_DASHSCOPE_CONNECTIVITY_TYPE = DASHSCOPE_CONNECTIVITY_PROBE_TYPE
EXPECTED_DASHSCOPE_CONNECTIVITY_SOURCE = DASHSCOPE_CONNECTIVITY_SOURCE
EXPECTED_DASHSCOPE_CONNECTIVITY_MODE = DASHSCOPE_CONNECTIVITY_MODE
EXPECTED_DASHSCOPE_CONNECTIVITY_INTENDED_MODEL = DASHSCOPE_INTENDED_MODEL
EXPECTED_DASHSCOPE_CONNECTIVITY_STATUSES = DASHSCOPE_CONNECTIVITY_ALLOWED_STATUSES
EXPECTED_DASHSCOPE_CONNECTIVITY_HTTP_STATUS_CATEGORIES = DASHSCOPE_CONNECTIVITY_ALLOWED_HTTP_STATUS_CATEGORIES
EXPECTED_DASHSCOPE_CONNECTIVITY_ERROR_CATEGORIES = DASHSCOPE_CONNECTIVITY_ALLOWED_ERROR_CATEGORIES


def verify_dashscope_connectivity_contract(payload: dict | object) -> dict:
    result = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)

    actual_keys = set(result.keys())
    expected_keys = set(EXPECTED_DASHSCOPE_CONNECTIVITY_FIELDS)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        parts = ["DashScope connectivity contract keys drifted."]
        if missing:
            parts.append(f"Missing keys: {missing}.")
        if unexpected:
            parts.append(f"Unexpected keys: {unexpected}.")
        raise AssertionError(" ".join(parts))

    if result["connectivity_policy_version"] != EXPECTED_DASHSCOPE_CONNECTIVITY_VERSION:
        raise AssertionError("DashScope connectivity version drifted.")
    if result["probe_type"] != EXPECTED_DASHSCOPE_CONNECTIVITY_TYPE:
        raise AssertionError("DashScope connectivity probe type drifted.")
    if result["source"] != EXPECTED_DASHSCOPE_CONNECTIVITY_SOURCE:
        raise AssertionError("DashScope connectivity source drifted.")
    if result["mode"] != EXPECTED_DASHSCOPE_CONNECTIVITY_MODE:
        raise AssertionError("DashScope connectivity mode drifted.")
    if result["intended_model"] != EXPECTED_DASHSCOPE_CONNECTIVITY_INTENDED_MODEL:
        raise AssertionError("DashScope connectivity intended model drifted.")
    if result["probe_endpoint_label"] != DASHSCOPE_CONNECTIVITY_PROBE_ENDPOINT_LABEL:
        raise AssertionError("DashScope connectivity probe endpoint label drifted.")
    if result["request_method"] != DASHSCOPE_CONNECTIVITY_REQUEST_METHOD:
        raise AssertionError("DashScope connectivity request method drifted.")
    if result["request_body_kind"] != DASHSCOPE_CONNECTIVITY_REQUEST_BODY_KIND:
        raise AssertionError("DashScope connectivity request_body_kind drifted.")
    if result["request_body_bytes_length"] != 0:
        raise AssertionError("DashScope connectivity must remain a no-content request.")
    if result["connectivity_status"] not in EXPECTED_DASHSCOPE_CONNECTIVITY_STATUSES:
        raise AssertionError("DashScope connectivity connectivity_status drifted.")
    if result["sanitized_error_category"] not in EXPECTED_DASHSCOPE_CONNECTIVITY_ERROR_CATEGORIES:
        raise AssertionError("DashScope connectivity sanitized_error_category drifted.")
    if result["http_status_category"] not in EXPECTED_DASHSCOPE_CONNECTIVITY_HTTP_STATUS_CATEGORIES:
        raise AssertionError("DashScope connectivity http_status_category drifted.")

    if not isinstance(result["probe_requested"], bool):
        raise AssertionError("DashScope connectivity probe_requested must be a boolean.")
    if not isinstance(result["network_attempted"], bool):
        raise AssertionError("DashScope connectivity network_attempted must be a boolean.")
    if not isinstance(result["local_config_ready"], bool):
        raise AssertionError("DashScope connectivity local_config_ready must be a boolean.")
    if result["selected_api_key_name"] is not None and result["selected_api_key_name"] not in (
        DASHSCOPE_ACTIVE_ENV_KEYS + DASHSCOPE_FALLBACK_ONLY_ENV_KEYS
    ):
        raise AssertionError("DashScope connectivity selected_api_key_name must stay within the governed key set.")
    if result["selected_api_key_category"] is not None and result["selected_api_key_category"] not in {"active", "fallback-only"}:
        raise AssertionError("DashScope connectivity selected_api_key_category drifted.")
    if not isinstance(result["selected_model"], str):
        raise AssertionError("DashScope connectivity selected_model must be a string.")
    if result["model_policy_status"] not in {"default", "explicit-match", "fallback-match", "mismatch"}:
        raise AssertionError("DashScope connectivity model_policy_status drifted.")
    if not isinstance(result["model_policy_ready"], bool):
        raise AssertionError("DashScope connectivity model_policy_ready must be a boolean.")
    if not isinstance(result["model_policy_requires_update"], bool):
        raise AssertionError("DashScope connectivity model_policy_requires_update must be a boolean.")

    if result["project_content_sent"] is not False:
        raise AssertionError("DashScope connectivity must keep project_content_sent false.")
    if result["inventory_content_sent"] is not False:
        raise AssertionError("DashScope connectivity must keep inventory_content_sent false.")
    if result["prompt_preview_content_sent"] is not False:
        raise AssertionError("DashScope connectivity must keep prompt_preview_content_sent false.")
    if result["target_repo_content_sent"] is not False:
        raise AssertionError("DashScope connectivity must keep target_repo_content_sent false.")
    if result["qwen_analysis_enabled"] is not False:
        raise AssertionError("DashScope connectivity must keep qwen_analysis_enabled false.")
    if result["runtime_enabled"] is not False:
        raise AssertionError("DashScope connectivity must keep runtime_enabled false.")
    if result["report_writing_enabled"] is not False:
        raise AssertionError("DashScope connectivity must keep report_writing_enabled false.")
    if result["health_surface_integration_enabled"] is not False:
        raise AssertionError("DashScope connectivity must keep health_surface_integration_enabled false.")
    if result["authorization_header_logged"] is not False:
        raise AssertionError("DashScope connectivity must never log Authorization headers.")
    if result["raw_request_headers_logged"] is not False:
        raise AssertionError("DashScope connectivity must never log raw request headers.")
    if result["raw_response_body_logged"] is not False:
        raise AssertionError("DashScope connectivity must never log raw response bodies.")

    if "Authorization headers" not in result["redaction_policy"]:
        raise AssertionError("DashScope connectivity redaction policy must mention Authorization headers.")
    if "qwen3.6-plus" not in result["redaction_policy"]:
        raise AssertionError("DashScope connectivity redaction policy must keep the intended model explicit.")

    return result
