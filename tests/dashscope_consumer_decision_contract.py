from __future__ import annotations

from workflow_manager.dashscope_consumer_decision import (
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_AUTHORITY_POLICY,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_CONFIDENCE_POLICY,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_MODE,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VERSION,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_READY_TO_MIGRATE_CLAIM_POLICY,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_REQUIRED_HUMAN_REVIEW_RULES,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_SIMULATED_EXAMPLE_KEYS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_SOURCE,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_TYPE,
)
from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL
from workflow_manager.dashscope_request import DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS


EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_FIELDS = DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_FIELDS
EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_VERSION = DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VERSION
EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_TYPE = DASHSCOPE_OFFLINE_CONSUMER_DECISION_TYPE
EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_SOURCE = DASHSCOPE_OFFLINE_CONSUMER_DECISION_SOURCE
EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_MODE = DASHSCOPE_OFFLINE_CONSUMER_DECISION_MODE
EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_INTENDED_MODEL = DASHSCOPE_INTENDED_MODEL
EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES = DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES
EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS = DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS
EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_REQUIRED_HUMAN_REVIEW_RULES = (
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_REQUIRED_HUMAN_REVIEW_RULES
)
EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_CONFIDENCE_POLICY = DASHSCOPE_OFFLINE_CONSUMER_DECISION_CONFIDENCE_POLICY
EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_READY_TO_MIGRATE_CLAIM_POLICY = (
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_READY_TO_MIGRATE_CLAIM_POLICY
)
EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_AUTHORITY_POLICY = DASHSCOPE_OFFLINE_CONSUMER_DECISION_AUTHORITY_POLICY
EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_INPUT_SUMMARY_KEYS = DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS
EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_SIMULATED_EXAMPLE_KEYS = (
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_SIMULATED_EXAMPLE_KEYS
)
EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_SIMULATED_EXAMPLE_NAMES = (
    "valid_grounded_explanatory_response",
    "missing_evidence_for_recommendation",
    "unknown_evidence_reference",
    "source_of_truth_override_claim",
    "migration_write_authorization",
    "ready_to_migrate_without_gates",
    "hidden_reasoning_output",
    "secret_like_content",
    "target_repo_file_contents",
    "low_confidence_requires_human_review",
    "missing_confidence_requires_recheck",
    "confidence_cannot_override_missing_evidence",
    "deterministic_mismatch_requires_human_review",
    "unsafe_extra_field",
)
ALLOWED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_MODEL_POLICY_STATUSES = (
    "default",
    "explicit-match",
    "fallback-match",
    "mismatch",
)
ALLOWED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_EXPECTED_STATES = set(
    EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES
)


def verify_dashscope_offline_consumer_decision_contract(payload: dict | object) -> dict:
    decision = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)

    actual_keys = set(decision.keys())
    expected_keys = set(EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_FIELDS)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        parts = ["DashScope offline consumer-decision contract keys drifted."]
        if missing:
            parts.append(f"Missing keys: {missing}.")
        if unexpected:
            parts.append(f"Unexpected keys: {unexpected}.")
        raise AssertionError(" ".join(parts))

    if decision["consumer_decision_policy_version"] != EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_VERSION:
        raise AssertionError("DashScope offline consumer-decision version drifted.")
    if decision["decision_type"] != EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_TYPE:
        raise AssertionError("DashScope offline consumer-decision type drifted.")
    if decision["source"] != EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_SOURCE:
        raise AssertionError("DashScope offline consumer-decision source drifted.")
    if decision["mode"] != EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_MODE:
        raise AssertionError("DashScope offline consumer-decision mode drifted.")
    if decision["intended_model"] != EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_INTENDED_MODEL:
        raise AssertionError("DashScope offline consumer-decision intended model drifted.")
    if not isinstance(decision["selected_model"], str):
        raise AssertionError("DashScope offline consumer-decision selected_model must be a string.")
    if decision["model_policy_status"] not in ALLOWED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_MODEL_POLICY_STATUSES:
        raise AssertionError("DashScope offline consumer-decision model policy status drifted.")
    if not isinstance(decision["model_policy_ready"], bool):
        raise AssertionError("DashScope offline consumer-decision model_policy_ready must be a boolean.")
    if not isinstance(decision["model_policy_requires_update"], bool):
        raise AssertionError("DashScope offline consumer-decision model_policy_requires_update must be a boolean.")
    if not isinstance(decision["local_config_ready"], bool):
        raise AssertionError("DashScope offline consumer-decision local_config_ready must be a boolean.")
    if decision["runtime_enabled"] is not False:
        raise AssertionError("DashScope offline consumer-decision runtime_enabled must remain false.")
    if decision["network_calls_allowed"] is not False:
        raise AssertionError("DashScope offline consumer-decision network_calls_allowed must remain false.")
    if decision["qwen_dashscope_enabled"] is not False:
        raise AssertionError("DashScope offline consumer-decision qwen_dashscope_enabled must remain false.")
    if decision["graphify_enabled"] is not False:
        raise AssertionError("DashScope offline consumer-decision graphify_enabled must remain false.")
    if decision["migration_writes_enabled"] is not False:
        raise AssertionError("DashScope offline consumer-decision migration_writes_enabled must remain false.")

    if decision["response_consumer_policy_version"] != "1.0.0":
        raise AssertionError("DashScope offline consumer-decision response_consumer_policy_version drifted.")
    if decision["consumer_policy_type"] != "evidence_slot_response_consumer_policy":
        raise AssertionError("DashScope offline consumer-decision consumer_policy_type drifted.")
    if decision["consumer_policy_mode"] != "offline_response_consumer_policy_only":
        raise AssertionError("DashScope offline consumer-decision consumer_policy_mode drifted.")
    if decision["response_explanatory_only"] is not True:
        raise AssertionError("DashScope offline consumer-decision must remain explanatory-only.")
    if decision["live_response_parsing_enabled"] is not False:
        raise AssertionError("DashScope offline consumer-decision must keep live response parsing disabled.")

    if decision["allowed_decision_states"] != list(EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES):
        raise AssertionError("DashScope offline consumer-decision allowed_decision_states drifted.")
    if decision["allowed_decision_inputs"] != list(EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS):
        raise AssertionError("DashScope offline consumer-decision allowed_decision_inputs drifted.")
    if decision["required_human_review_rules"] != EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_REQUIRED_HUMAN_REVIEW_RULES:
        raise AssertionError("DashScope offline consumer-decision required_human_review_rules drifted.")
    if decision["confidence_policy"] != EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_CONFIDENCE_POLICY:
        raise AssertionError("DashScope offline consumer-decision confidence_policy drifted.")
    if decision["ready_to_migrate_claim_policy"] != EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_READY_TO_MIGRATE_CLAIM_POLICY:
        raise AssertionError("DashScope offline consumer-decision ready_to_migrate_claim_policy drifted.")
    if decision["decision_authority_policy"] != EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_AUTHORITY_POLICY:
        raise AssertionError("DashScope offline consumer-decision decision_authority_policy drifted.")
    if decision["decision_examples_in_memory_only"] is not True:
        raise AssertionError("DashScope offline consumer-decision examples must remain in-memory only.")

    simulated_examples = decision["simulated_decision_examples"]
    if not isinstance(simulated_examples, list):
        raise AssertionError("DashScope offline consumer-decision simulated_decision_examples must be a list.")
    if tuple(example.get("example_name") for example in simulated_examples) != EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_SIMULATED_EXAMPLE_NAMES:
        raise AssertionError("DashScope offline consumer-decision simulated example names drifted.")
    for example in simulated_examples:
        if not isinstance(example, dict):
            raise AssertionError("DashScope offline consumer-decision simulated examples must be objects.")
        if set(example.keys()) != set(EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_SIMULATED_EXAMPLE_KEYS):
            raise AssertionError("DashScope offline consumer-decision simulated example keys drifted.")
        if example["expected_decision_state"] not in ALLOWED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_EXPECTED_STATES:
            raise AssertionError("DashScope offline consumer-decision example state drifted.")
        if not isinstance(example["requires_human_review"], bool):
            raise AssertionError("DashScope offline consumer-decision example requires_human_review must be a boolean.")
        if not isinstance(example["requires_deterministic_recheck"], bool):
            raise AssertionError(
                "DashScope offline consumer-decision example requires_deterministic_recheck must be a boolean."
            )
        if not isinstance(example["decision_reason"], str) or not example["decision_reason"].strip():
            raise AssertionError("DashScope offline consumer-decision example decision_reason must be a non-empty string.")

        decision_inputs = example["decision_inputs"]
        if not isinstance(decision_inputs, dict):
            raise AssertionError("DashScope offline consumer-decision example decision_inputs must be an object.")
        if set(decision_inputs.keys()) != set(EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS):
            raise AssertionError("DashScope offline consumer-decision example decision_inputs keys drifted.")
        if not isinstance(decision_inputs["missing_evidence_fields"], list):
            raise AssertionError("DashScope offline consumer-decision missing_evidence_fields must be a list.")
        if not isinstance(decision_inputs["unknown_evidence_references"], list):
            raise AssertionError("DashScope offline consumer-decision unknown_evidence_references must be a list.")
        if not isinstance(decision_inputs["forbidden_content_flags"], list):
            raise AssertionError("DashScope offline consumer-decision forbidden_content_flags must be a list.")
        if not isinstance(decision_inputs["deterministic_reference_categories"], list):
            raise AssertionError("DashScope offline consumer-decision deterministic_reference_categories must be a list.")
        if not all(isinstance(item, str) for item in decision_inputs["deterministic_reference_categories"]):
            raise AssertionError("DashScope offline consumer-decision deterministic_reference_categories must contain strings.")
        if not all(isinstance(item, str) for item in decision_inputs["missing_evidence_fields"]):
            raise AssertionError("DashScope offline consumer-decision missing_evidence_fields must contain strings.")
        if not all(isinstance(item, str) for item in decision_inputs["unknown_evidence_references"]):
            raise AssertionError("DashScope offline consumer-decision unknown_evidence_references must contain strings.")
        if not all(isinstance(item, str) for item in decision_inputs["forbidden_content_flags"]):
            raise AssertionError("DashScope offline consumer-decision forbidden_content_flags must contain strings.")
        if not isinstance(decision_inputs["source_of_truth_override_flag"], bool):
            raise AssertionError("DashScope offline consumer-decision source_of_truth_override_flag must be a boolean.")
        if not isinstance(decision_inputs["migration_write_authorization_flag"], bool):
            raise AssertionError(
                "DashScope offline consumer-decision migration_write_authorization_flag must be a boolean."
            )
        if not isinstance(decision_inputs["ready_to_migrate_claim_flag"], bool):
            raise AssertionError("DashScope offline consumer-decision ready_to_migrate_claim_flag must be a boolean.")
        if not isinstance(decision_inputs["required_human_review_flag"], bool):
            raise AssertionError("DashScope offline consumer-decision required_human_review_flag must be a boolean.")
        if not isinstance(decision_inputs["blocked_actions_present"], bool):
            raise AssertionError("DashScope offline consumer-decision blocked_actions_present must be a boolean.")
        if not isinstance(decision_inputs["deterministic_mismatch_flag"], bool):
            raise AssertionError("DashScope offline consumer-decision deterministic_mismatch_flag must be a boolean.")

    if "qwen3.6-plus" not in decision["redaction_policy"]:
        raise AssertionError("DashScope offline consumer-decision redaction_policy must keep the intended model explicit.")

    input_summary = decision["input_summary"]
    if not isinstance(input_summary, dict):
        raise AssertionError("DashScope offline consumer-decision input_summary must be an object.")
    if set(input_summary.keys()) != set(EXPECTED_DASHSCOPE_OFFLINE_CONSUMER_DECISION_INPUT_SUMMARY_KEYS):
        raise AssertionError("DashScope offline consumer-decision input_summary keys drifted.")
    if input_summary["source_command"] != "hermes_inventory":
        raise AssertionError("DashScope offline consumer-decision input_summary.source_command must remain hermes_inventory.")
    if input_summary["source_mode"] != "inventory":
        raise AssertionError("DashScope offline consumer-decision input_summary.source_mode must remain inventory.")
    if input_summary["source_dry_run"] is not True:
        raise AssertionError("DashScope offline consumer-decision input_summary.source_dry_run must remain true.")

    return decision
