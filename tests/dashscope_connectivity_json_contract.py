from __future__ import annotations

from copy import deepcopy
import json
import unittest

from workflow_manager.dashscope_env import (
    DASHSCOPE_ACTIVE_ENV_KEYS,
    DASHSCOPE_FALLBACK_ONLY_ENV_KEYS,
)


EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_FIELDS = (
    "schema_version",
    "command",
    "mode",
    "intended_model",
    "selected_model",
    "selected_api_key_name",
    "selected_api_key_category",
    "local_config_ready",
    "model_policy_status",
    "probe_requested",
    "no_content",
    "yes_network",
    "interactive_required",
    "interactive_session",
    "operator_gate_satisfied",
    "network_attempted",
    "connectivity_status",
    "sanitized_error_category",
    "http_status_category",
    "request_method",
    "request_body_kind",
    "request_body_bytes_length",
    "project_content_sent",
    "inventory_content_sent",
    "prompt_preview_content_sent",
    "target_repo_content_sent",
    "qwen_analysis_enabled",
    "report_writing_enabled",
    "migration_writes_enabled",
    "graphify_enabled",
    "health_surface_integration_enabled",
    "warnings",
    "errors",
)
EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_SCHEMA_VERSION = "1.0.0"
EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_COMMAND = "hermes_qwen_connectivity"
EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_MODE = "explicit_opt_in_no_content_probe"
EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_INTENDED_MODEL = "qwen3.6-plus"
EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_MODEL_POLICY_STATUSES = (
    "default",
    "explicit-match",
    "fallback-match",
    "mismatch",
    "error",
)
EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_STATUSES = (
    "not-requested",
    "not-configured",
    "model-policy-mismatch",
    "reachable",
    "auth-error",
    "throttled",
    "http-error",
    "service-error",
    "network-error",
    "transport-error",
)
EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_ERROR_CATEGORIES = (
    "none",
    "missing-api-key",
    "local-config-not-ready",
    "model-policy-mismatch",
    "http-401",
    "http-403",
    "http-404",
    "http-429",
    "http-4xx",
    "http-5xx",
    "timeout",
    "connection-error",
    "dns-error",
    "ssl-error",
    "unexpected-transport-error",
)
EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_HTTP_STATUS_CATEGORIES = (
    "not-attempted",
    "2xx",
    "401",
    "403",
    "404",
    "429",
    "4xx",
    "5xx",
    "other",
)
EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_API_KEY_NAMES = DASHSCOPE_ACTIVE_ENV_KEYS + DASHSCOPE_FALLBACK_ONLY_ENV_KEYS
EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_API_KEY_CATEGORIES = ("active", "fallback-only")


def build_valid_dashscope_connectivity_json_example() -> dict[str, object]:
    return {
        "schema_version": EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_SCHEMA_VERSION,
        "command": EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_COMMAND,
        "mode": EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_MODE,
        "intended_model": EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_INTENDED_MODEL,
        "selected_model": EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_INTENDED_MODEL,
        "selected_api_key_name": "DASHSCOPE_API_KEY_WORKFLOW_MANAGER",
        "selected_api_key_category": "active",
        "local_config_ready": True,
        "model_policy_status": "default",
        "probe_requested": False,
        "no_content": False,
        "yes_network": False,
        "interactive_required": True,
        "interactive_session": False,
        "operator_gate_satisfied": False,
        "network_attempted": False,
        "connectivity_status": "not-requested",
        "sanitized_error_category": "none",
        "http_status_category": "not-attempted",
        "request_method": "GET",
        "request_body_kind": "none",
        "request_body_bytes_length": 0,
        "project_content_sent": False,
        "inventory_content_sent": False,
        "prompt_preview_content_sent": False,
        "target_repo_content_sent": False,
        "qwen_analysis_enabled": False,
        "report_writing_enabled": False,
        "migration_writes_enabled": False,
        "graphify_enabled": False,
        "health_surface_integration_enabled": False,
        "warnings": [
            "network stays disabled until `--probe --no-content --yes-network` are all present.",
        ],
        "errors": [],
    }


def verify_dashscope_connectivity_json_payload(payload: dict[str, object] | object) -> dict[str, object]:
    result = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)

    actual_keys = set(result.keys())
    expected_keys = set(EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_FIELDS)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        parts = ["DashScope connectivity CLI JSON keys drifted."]
        if missing:
            parts.append(f"Missing keys: {missing}.")
        if unexpected:
            parts.append(f"Unexpected keys: {unexpected}.")
        raise AssertionError(" ".join(parts))

    if result["schema_version"] != EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_SCHEMA_VERSION:
        raise AssertionError("DashScope connectivity CLI JSON schema_version drifted.")
    if result["command"] != EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_COMMAND:
        raise AssertionError("DashScope connectivity CLI JSON command drifted.")
    if result["mode"] != EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_MODE:
        raise AssertionError("DashScope connectivity CLI JSON mode drifted.")
    if result["intended_model"] != EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_INTENDED_MODEL:
        raise AssertionError("DashScope connectivity CLI JSON intended_model drifted.")
    if not isinstance(result["selected_model"], str):
        raise AssertionError("DashScope connectivity CLI JSON selected_model must be a string.")
    if result["selected_api_key_name"] is not None and result["selected_api_key_name"] not in EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_API_KEY_NAMES:
        raise AssertionError("DashScope connectivity CLI JSON selected_api_key_name drifted.")
    if result["selected_api_key_category"] is not None and result["selected_api_key_category"] not in EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_API_KEY_CATEGORIES:
        raise AssertionError("DashScope connectivity CLI JSON selected_api_key_category drifted.")

    for key in (
        "local_config_ready",
        "probe_requested",
        "no_content",
        "yes_network",
        "interactive_required",
        "interactive_session",
        "operator_gate_satisfied",
        "network_attempted",
        "project_content_sent",
        "inventory_content_sent",
        "prompt_preview_content_sent",
        "target_repo_content_sent",
        "qwen_analysis_enabled",
        "report_writing_enabled",
        "migration_writes_enabled",
        "graphify_enabled",
        "health_surface_integration_enabled",
    ):
        if not isinstance(result[key], bool):
            raise AssertionError(f"DashScope connectivity CLI JSON {key} must be a boolean.")

    if result["interactive_required"] is not True:
        raise AssertionError("DashScope connectivity CLI JSON interactive_required must remain true.")
    if result["model_policy_status"] not in EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_MODEL_POLICY_STATUSES:
        raise AssertionError("DashScope connectivity CLI JSON model_policy_status drifted.")
    if result["connectivity_status"] not in EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_STATUSES:
        raise AssertionError("DashScope connectivity CLI JSON connectivity_status drifted.")
    if result["sanitized_error_category"] not in EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_ERROR_CATEGORIES:
        raise AssertionError("DashScope connectivity CLI JSON sanitized_error_category drifted.")
    if result["http_status_category"] not in EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_HTTP_STATUS_CATEGORIES:
        raise AssertionError("DashScope connectivity CLI JSON http_status_category drifted.")
    if result["request_method"] != "GET":
        raise AssertionError("DashScope connectivity CLI JSON request_method drifted.")
    if result["request_body_kind"] != "none":
        raise AssertionError("DashScope connectivity CLI JSON request_body_kind drifted.")
    if result["request_body_bytes_length"] != 0:
        raise AssertionError("DashScope connectivity CLI JSON must remain no-content.")

    if result["project_content_sent"] is not False:
        raise AssertionError("DashScope connectivity CLI JSON must keep project_content_sent false.")
    if result["inventory_content_sent"] is not False:
        raise AssertionError("DashScope connectivity CLI JSON must keep inventory_content_sent false.")
    if result["prompt_preview_content_sent"] is not False:
        raise AssertionError("DashScope connectivity CLI JSON must keep prompt_preview_content_sent false.")
    if result["target_repo_content_sent"] is not False:
        raise AssertionError("DashScope connectivity CLI JSON must keep target_repo_content_sent false.")
    if result["qwen_analysis_enabled"] is not False:
        raise AssertionError("DashScope connectivity CLI JSON must keep qwen_analysis_enabled false.")
    if result["report_writing_enabled"] is not False:
        raise AssertionError("DashScope connectivity CLI JSON must keep report_writing_enabled false.")
    if result["migration_writes_enabled"] is not False:
        raise AssertionError("DashScope connectivity CLI JSON must keep migration_writes_enabled false.")
    if result["graphify_enabled"] is not False:
        raise AssertionError("DashScope connectivity CLI JSON must keep graphify_enabled false.")
    if result["health_surface_integration_enabled"] is not False:
        raise AssertionError("DashScope connectivity CLI JSON must keep health_surface_integration_enabled false.")

    if not isinstance(result["warnings"], list) or not all(isinstance(value, str) and value.strip() for value in result["warnings"]):
        raise AssertionError("DashScope connectivity CLI JSON warnings must be a list of non-empty strings.")
    if not isinstance(result["errors"], list) or not all(isinstance(value, str) and value.strip() for value in result["errors"]):
        raise AssertionError("DashScope connectivity CLI JSON errors must be a list of non-empty strings.")

    if result["operator_gate_satisfied"]:
        if not (
            result["probe_requested"]
            and result["no_content"]
            and result["yes_network"]
            and result["interactive_session"]
        ):
            raise AssertionError(
                "DashScope connectivity CLI JSON operator_gate_satisfied must require probe/no-content/yes-network/interactive-session."
            )
    else:
        if result["network_attempted"]:
            raise AssertionError(
                "DashScope connectivity CLI JSON must keep network_attempted false when operator_gate_satisfied is false."
            )
        if result["connectivity_status"] != "not-requested":
            raise AssertionError(
                "DashScope connectivity CLI JSON must stay not-requested when operator_gate_satisfied is false."
            )
        if result["sanitized_error_category"] != "none":
            raise AssertionError(
                "DashScope connectivity CLI JSON must stay at sanitized_error_category `none` when operator_gate_satisfied is false."
            )
        if result["http_status_category"] != "not-attempted":
            raise AssertionError(
                "DashScope connectivity CLI JSON must stay at http_status_category `not-attempted` when operator_gate_satisfied is false."
            )

    if result["network_attempted"]:
        if not result["operator_gate_satisfied"]:
            raise AssertionError(
                "DashScope connectivity CLI JSON must not attempt network unless the explicit operator gate is satisfied."
            )
        if result["http_status_category"] == "not-attempted":
            raise AssertionError(
                "DashScope connectivity CLI JSON must not report http_status_category `not-attempted` when network was attempted."
            )

    serialized = json.dumps(result, sort_keys=True)
    if "Authorization:" in serialized:
        raise AssertionError("DashScope connectivity CLI JSON must never include Authorization headers.")
    if "Bearer " in serialized:
        raise AssertionError("DashScope connectivity CLI JSON must never include bearer tokens.")

    return result


def verify_dashscope_connectivity_json_stdout(stdout: str) -> dict[str, object]:
    return verify_dashscope_connectivity_json_payload(json.loads(stdout))


class DashScopeConnectivityJsonContractTests(unittest.TestCase):
    def test_dashscope_connectivity_json_contract_accepts_governed_example(self) -> None:
        payload = verify_dashscope_connectivity_json_payload(build_valid_dashscope_connectivity_json_example())
        self.assertEqual(payload["command"], EXPECTED_DASHSCOPE_CONNECTIVITY_JSON_COMMAND)
        self.assertFalse(payload["network_attempted"])
        self.assertEqual(payload["connectivity_status"], "not-requested")

    def test_dashscope_connectivity_json_contract_rejects_missing_fields_and_wrong_types(self) -> None:
        missing = build_valid_dashscope_connectivity_json_example()
        del missing["command"]
        with self.assertRaisesRegex(AssertionError, "Missing keys"):
            verify_dashscope_connectivity_json_payload(missing)

        wrong_type = build_valid_dashscope_connectivity_json_example()
        wrong_type["probe_requested"] = "yes"
        with self.assertRaisesRegex(AssertionError, "probe_requested must be a boolean"):
            verify_dashscope_connectivity_json_payload(wrong_type)

    def test_dashscope_connectivity_json_contract_rejects_invalid_vocabularies(self) -> None:
        invalid_status = build_valid_dashscope_connectivity_json_example()
        invalid_status["connectivity_status"] = "unexpected"
        with self.assertRaisesRegex(AssertionError, "connectivity_status drifted"):
            verify_dashscope_connectivity_json_payload(invalid_status)

        invalid_error = build_valid_dashscope_connectivity_json_example()
        invalid_error["sanitized_error_category"] = "bad-error"
        with self.assertRaisesRegex(AssertionError, "sanitized_error_category drifted"):
            verify_dashscope_connectivity_json_payload(invalid_error)

        invalid_http = build_valid_dashscope_connectivity_json_example()
        invalid_http["http_status_category"] = "bad-http"
        with self.assertRaisesRegex(AssertionError, "http_status_category drifted"):
            verify_dashscope_connectivity_json_payload(invalid_http)

    def test_dashscope_connectivity_json_contract_rejects_unsafe_flags_and_gating_drift(self) -> None:
        unsafe = build_valid_dashscope_connectivity_json_example()
        unsafe["project_content_sent"] = True
        with self.assertRaisesRegex(AssertionError, "project_content_sent false"):
            verify_dashscope_connectivity_json_payload(unsafe)

        gating = build_valid_dashscope_connectivity_json_example()
        gating["network_attempted"] = True
        with self.assertRaisesRegex(AssertionError, "network_attempted false when operator_gate_satisfied is false"):
            verify_dashscope_connectivity_json_payload(gating)

        gated_attempt = deepcopy(build_valid_dashscope_connectivity_json_example())
        gated_attempt["probe_requested"] = True
        gated_attempt["no_content"] = True
        gated_attempt["yes_network"] = True
        gated_attempt["interactive_session"] = True
        gated_attempt["operator_gate_satisfied"] = True
        gated_attempt["network_attempted"] = True
        gated_attempt["connectivity_status"] = "reachable"
        gated_attempt["sanitized_error_category"] = "none"
        gated_attempt["http_status_category"] = "2xx"
        payload = verify_dashscope_connectivity_json_payload(gated_attempt)
        self.assertTrue(payload["network_attempted"])
