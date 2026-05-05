from __future__ import annotations

from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL
from workflow_manager.dashscope_request import DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS
from workflow_manager.dashscope_response_consumer import (
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_AUTHORITY_POLICY,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_AUTHORITY_POLICY_KEYS,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_DEFAULT_SIMULATED_EXAMPLES,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_FORBIDDEN_EVIDENCE_REFERENCES,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_MODE,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_POLICY_VERSION,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_REQUIRED_EVIDENCE_RULES,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SIMULATED_EXAMPLE_KEYS,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SOURCE,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_TYPE,
)


EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_FIELDS = DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_FIELDS
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_POLICY_VERSION = DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_POLICY_VERSION
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_TYPE = DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_TYPE
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SOURCE = DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SOURCE
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_MODE = DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_MODE
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_INTENDED_MODEL = DASHSCOPE_INTENDED_MODEL
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES = (
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES
)
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE = (
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE
)
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_REQUIRED_EVIDENCE_RULES = (
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_REQUIRED_EVIDENCE_RULES
)
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_FORBIDDEN_EVIDENCE_REFERENCES = (
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_FORBIDDEN_EVIDENCE_REFERENCES
)
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_AUTHORITY_POLICY_KEYS = (
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_AUTHORITY_POLICY_KEYS
)
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_AUTHORITY_POLICY = DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_AUTHORITY_POLICY
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SIMULATED_EXAMPLE_KEYS = (
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SIMULATED_EXAMPLE_KEYS
)
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SIMULATED_EXAMPLE_NAMES = tuple(
    example["example_name"] for example in DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_DEFAULT_SIMULATED_EXAMPLES
)
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_INPUT_SUMMARY_KEYS = DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS
ALLOWED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_MODEL_POLICY_STATUSES = (
    "default",
    "explicit-match",
    "fallback-match",
    "mismatch",
)


def verify_dashscope_offline_response_consumer_contract(payload: dict | object) -> dict:
    policy = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)

    actual_keys = set(policy.keys())
    expected_keys = set(EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_FIELDS)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        parts = ["DashScope offline response-consumer contract keys drifted."]
        if missing:
            parts.append(f"Missing keys: {missing}.")
        if unexpected:
            parts.append(f"Unexpected keys: {unexpected}.")
        raise AssertionError(" ".join(parts))

    if policy["response_consumer_policy_version"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_POLICY_VERSION:
        raise AssertionError("DashScope offline response-consumer version drifted.")
    if policy["consumer_type"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_TYPE:
        raise AssertionError("DashScope offline response-consumer type drifted.")
    if policy["source"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SOURCE:
        raise AssertionError("DashScope offline response-consumer source drifted.")
    if policy["mode"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_MODE:
        raise AssertionError("DashScope offline response-consumer mode drifted.")
    if policy["intended_model"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_INTENDED_MODEL:
        raise AssertionError("DashScope offline response-consumer intended model drifted.")
    if not isinstance(policy["selected_model"], str):
        raise AssertionError("DashScope offline response-consumer selected_model must be a string.")
    if policy["model_policy_status"] not in ALLOWED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_MODEL_POLICY_STATUSES:
        raise AssertionError("DashScope offline response-consumer model policy status drifted.")
    if not isinstance(policy["model_policy_ready"], bool):
        raise AssertionError("DashScope offline response-consumer model_policy_ready must be a boolean.")
    if not isinstance(policy["model_policy_requires_update"], bool):
        raise AssertionError("DashScope offline response-consumer model_policy_requires_update must be a boolean.")
    if not isinstance(policy["local_config_ready"], bool):
        raise AssertionError("DashScope offline response-consumer local_config_ready must be a boolean.")
    if policy["runtime_enabled"] is not False:
        raise AssertionError("DashScope offline response-consumer runtime_enabled must remain false.")
    if policy["network_calls_allowed"] is not False:
        raise AssertionError("DashScope offline response-consumer network_calls_allowed must remain false.")
    if policy["qwen_dashscope_enabled"] is not False:
        raise AssertionError("DashScope offline response-consumer qwen_dashscope_enabled must remain false.")
    if policy["graphify_enabled"] is not False:
        raise AssertionError("DashScope offline response-consumer graphify_enabled must remain false.")
    if policy["migration_writes_enabled"] is not False:
        raise AssertionError("DashScope offline response-consumer migration_writes_enabled must remain false.")
    if policy["response_shape_version"] != "1.0.0":
        raise AssertionError("DashScope offline response-consumer response_shape_version drifted.")
    if policy["response_type"] != "explanatory_response_shape":
        raise AssertionError("DashScope offline response-consumer response_type must remain explanatory_response_shape.")
    if policy["response_mode"] != "offline_response_shape_only":
        raise AssertionError("DashScope offline response-consumer response_mode must remain offline_response_shape_only.")
    if policy["response_explanatory_only"] is not True:
        raise AssertionError("DashScope offline response-consumer must remain explanatory-only.")
    if policy["live_response_parsing_enabled"] is not False:
        raise AssertionError("DashScope offline response-consumer must keep live response parsing disabled.")

    if tuple(policy["allowed_evidence_reference_categories"]) != (
        EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES
    ):
        raise AssertionError("DashScope offline response-consumer allowed_evidence_reference_categories drifted.")
    if tuple(policy["response_fields_requiring_evidence"]) != (
        EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE
    ):
        raise AssertionError("DashScope offline response-consumer response_fields_requiring_evidence drifted.")
    if policy["required_evidence_rules"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_REQUIRED_EVIDENCE_RULES:
        raise AssertionError("DashScope offline response-consumer required_evidence_rules drifted.")
    if tuple(policy["forbidden_evidence_references"]) != (
        EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_FORBIDDEN_EVIDENCE_REFERENCES
    ):
        raise AssertionError("DashScope offline response-consumer forbidden_evidence_references drifted.")

    authority_policy = policy["consumer_authority_policy"]
    if not isinstance(authority_policy, dict):
        raise AssertionError("DashScope offline response-consumer consumer_authority_policy must be an object.")
    if tuple(authority_policy.keys()) != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_AUTHORITY_POLICY_KEYS:
        raise AssertionError("DashScope offline response-consumer consumer_authority_policy keys drifted.")
    if authority_policy != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_AUTHORITY_POLICY:
        raise AssertionError("DashScope offline response-consumer consumer_authority_policy drifted.")
    if authority_policy["qwen_output_is_explanatory_only"] is not True:
        raise AssertionError("DashScope offline response-consumer must keep Qwen output explanatory-only.")
    if authority_policy["source_of_truth_override_handling"] != "reject":
        raise AssertionError("DashScope offline response-consumer must reject source-of-truth override claims.")
    if authority_policy["migration_write_authorization_handling"] != "reject":
        raise AssertionError("DashScope offline response-consumer must reject migration-write authorization.")

    if "Reject" not in policy["ungrounded_recommendation_policy"]:
        raise AssertionError("DashScope offline response-consumer ungrounded_recommendation_policy must stay explicit.")
    if "uncertainty" not in policy["uncertainty_policy"]:
        raise AssertionError("DashScope offline response-consumer uncertainty_policy must stay explicit.")
    if policy["simulated_examples_in_memory_only"] is not True:
        raise AssertionError("DashScope offline response-consumer simulated examples must remain in-memory only.")

    examples = policy["simulated_examples"]
    if not isinstance(examples, list) or not examples:
        raise AssertionError("DashScope offline response-consumer simulated_examples must be a non-empty list.")
    if tuple(example["example_name"] for example in examples) != (
        EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SIMULATED_EXAMPLE_NAMES
    ):
        raise AssertionError("DashScope offline response-consumer simulated example order drifted.")
    if not any(example["expected_consumer_action"] == "accept" for example in examples):
        raise AssertionError("DashScope offline response-consumer simulated examples must include an accept case.")
    if not any(example["expected_consumer_action"] == "reject" for example in examples):
        raise AssertionError("DashScope offline response-consumer simulated examples must include reject cases.")
    for example in examples:
        if tuple(example.keys()) != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SIMULATED_EXAMPLE_KEYS:
            raise AssertionError("DashScope offline response-consumer simulated example keys drifted.")
        if example["expected_consumer_action"] not in ("accept", "reject"):
            raise AssertionError("DashScope offline response-consumer simulated example action drifted.")
        if example["grounding_status"] not in ("grounded", "ungrounded"):
            raise AssertionError("DashScope offline response-consumer simulated example grounding status drifted.")
        if not isinstance(example["response_fields_present"], list):
            raise AssertionError("DashScope offline response-consumer simulated example response_fields_present must be a list.")
        if not isinstance(example["evidence_references"], dict):
            raise AssertionError("DashScope offline response-consumer simulated example evidence_references must be an object.")
        if not isinstance(example["invalid_evidence_references"], list):
            raise AssertionError("DashScope offline response-consumer simulated example invalid_evidence_references must be a list.")
        if not isinstance(example["forbidden_or_unexpected_fields"], list):
            raise AssertionError(
                "DashScope offline response-consumer simulated example forbidden_or_unexpected_fields must be a list."
            )
        if not isinstance(example["consumer_reason"], str) or not example["consumer_reason"].strip():
            raise AssertionError("DashScope offline response-consumer simulated example consumer_reason must be a non-empty string.")

    if "qwen3.6-plus" not in policy["redaction_policy"]:
        raise AssertionError("DashScope offline response-consumer redaction_policy must keep the intended model explicit.")

    input_summary = policy["input_summary"]
    if not isinstance(input_summary, dict):
        raise AssertionError("DashScope offline response-consumer input_summary must be an object.")
    if set(input_summary.keys()) != set(EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_INPUT_SUMMARY_KEYS):
        raise AssertionError("DashScope offline response-consumer input_summary keys drifted.")
    if input_summary["source_command"] != "hermes_inventory":
        raise AssertionError("DashScope offline response-consumer input_summary.source_command must remain hermes_inventory.")
    if input_summary["source_mode"] != "inventory":
        raise AssertionError("DashScope offline response-consumer input_summary.source_mode must remain inventory.")
    if input_summary["source_dry_run"] is not True:
        raise AssertionError("DashScope offline response-consumer input_summary.source_dry_run must remain true.")

    return policy
