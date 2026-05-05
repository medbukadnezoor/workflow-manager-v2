from __future__ import annotations

from workflow_manager.dashscope_consumer_decision import (
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_DEFAULT_SIMULATED_EXAMPLES,
)
from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL
from workflow_manager.dashscope_escalation import (
    DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_ACCEPTANCE_THRESHOLD_CATEGORIES,
    DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_MESSAGE_FIELDS,
    DASHSCOPE_OFFLINE_ESCALATION_BLOCKED_ACTION_SUMMARY_POLICY,
    DASHSCOPE_OFFLINE_ESCALATION_CONFIDENCE_MESSAGING_POLICY,
    DASHSCOPE_OFFLINE_ESCALATION_FORBIDDEN_MESSAGE_CONTENT,
    DASHSCOPE_OFFLINE_ESCALATION_MODE,
    DASHSCOPE_OFFLINE_ESCALATION_POLICY_VERSION,
    DASHSCOPE_OFFLINE_ESCALATION_READY_TO_MIGRATE_CLAIM_POLICY,
    DASHSCOPE_OFFLINE_ESCALATION_REQUIRED_HUMAN_REVIEW_RULES,
    DASHSCOPE_OFFLINE_ESCALATION_REQUIRED_MESSAGE_FIELDS,
    DASHSCOPE_OFFLINE_ESCALATION_SIMULATED_EXAMPLE_KEYS,
    DASHSCOPE_OFFLINE_ESCALATION_SOURCE,
    DASHSCOPE_OFFLINE_ESCALATION_SOURCE_OF_TRUTH_POLICY,
    DASHSCOPE_OFFLINE_ESCALATION_TYPE,
)
from workflow_manager.dashscope_request import DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS


EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_FIELDS = DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_FIELDS
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_VERSION = DASHSCOPE_OFFLINE_ESCALATION_POLICY_VERSION
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_TYPE = DASHSCOPE_OFFLINE_ESCALATION_TYPE
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_SOURCE = DASHSCOPE_OFFLINE_ESCALATION_SOURCE
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_MODE = DASHSCOPE_OFFLINE_ESCALATION_MODE
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_INTENDED_MODEL = DASHSCOPE_INTENDED_MODEL
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_ACCEPTANCE_THRESHOLD_CATEGORIES = (
    DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_ACCEPTANCE_THRESHOLD_CATEGORIES
)
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_MESSAGE_FIELDS = (
    DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_MESSAGE_FIELDS
)
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_REQUIRED_MESSAGE_FIELDS = (
    DASHSCOPE_OFFLINE_ESCALATION_REQUIRED_MESSAGE_FIELDS
)
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_REQUIRED_HUMAN_REVIEW_RULES = (
    DASHSCOPE_OFFLINE_ESCALATION_REQUIRED_HUMAN_REVIEW_RULES
)
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_CONFIDENCE_MESSAGING_POLICY = (
    DASHSCOPE_OFFLINE_ESCALATION_CONFIDENCE_MESSAGING_POLICY
)
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_BLOCKED_ACTION_SUMMARY_POLICY = (
    DASHSCOPE_OFFLINE_ESCALATION_BLOCKED_ACTION_SUMMARY_POLICY
)
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_READY_TO_MIGRATE_CLAIM_POLICY = (
    DASHSCOPE_OFFLINE_ESCALATION_READY_TO_MIGRATE_CLAIM_POLICY
)
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_SOURCE_OF_TRUTH_POLICY = (
    DASHSCOPE_OFFLINE_ESCALATION_SOURCE_OF_TRUTH_POLICY
)
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_FORBIDDEN_MESSAGE_CONTENT = (
    DASHSCOPE_OFFLINE_ESCALATION_FORBIDDEN_MESSAGE_CONTENT
)
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_INPUT_SUMMARY_KEYS = DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_SIMULATED_EXAMPLE_KEYS = (
    DASHSCOPE_OFFLINE_ESCALATION_SIMULATED_EXAMPLE_KEYS
)
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_SIMULATED_EXAMPLE_NAMES = tuple(
    example["example_name"] for example in DASHSCOPE_OFFLINE_CONSUMER_DECISION_DEFAULT_SIMULATED_EXAMPLES
)
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_DECISION_STATES = DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES
EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_DECISION_INPUTS = DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS
ALLOWED_DASHSCOPE_OFFLINE_ESCALATION_MODEL_POLICY_STATUSES = (
    "default",
    "explicit-match",
    "fallback-match",
    "mismatch",
)


def verify_dashscope_offline_escalation_contract(payload: dict | object) -> dict:
    escalation = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)

    actual_keys = set(escalation.keys())
    expected_keys = set(EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_FIELDS)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        parts = ["DashScope offline escalation contract keys drifted."]
        if missing:
            parts.append(f"Missing keys: {missing}.")
        if unexpected:
            parts.append(f"Unexpected keys: {unexpected}.")
        raise AssertionError(" ".join(parts))

    if escalation["escalation_policy_version"] != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_VERSION:
        raise AssertionError("DashScope offline escalation version drifted.")
    if escalation["escalation_type"] != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_TYPE:
        raise AssertionError("DashScope offline escalation type drifted.")
    if escalation["source"] != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_SOURCE:
        raise AssertionError("DashScope offline escalation source drifted.")
    if escalation["mode"] != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_MODE:
        raise AssertionError("DashScope offline escalation mode drifted.")
    if escalation["intended_model"] != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_INTENDED_MODEL:
        raise AssertionError("DashScope offline escalation intended model drifted.")
    if not isinstance(escalation["selected_model"], str):
        raise AssertionError("DashScope offline escalation selected_model must be a string.")
    if escalation["model_policy_status"] not in ALLOWED_DASHSCOPE_OFFLINE_ESCALATION_MODEL_POLICY_STATUSES:
        raise AssertionError("DashScope offline escalation model policy status drifted.")
    if not isinstance(escalation["model_policy_ready"], bool):
        raise AssertionError("DashScope offline escalation model_policy_ready must be a boolean.")
    if not isinstance(escalation["model_policy_requires_update"], bool):
        raise AssertionError("DashScope offline escalation model_policy_requires_update must be a boolean.")
    if not isinstance(escalation["local_config_ready"], bool):
        raise AssertionError("DashScope offline escalation local_config_ready must be a boolean.")
    if escalation["runtime_enabled"] is not False:
        raise AssertionError("DashScope offline escalation runtime_enabled must remain false.")
    if escalation["network_calls_allowed"] is not False:
        raise AssertionError("DashScope offline escalation network_calls_allowed must remain false.")
    if escalation["qwen_dashscope_enabled"] is not False:
        raise AssertionError("DashScope offline escalation qwen_dashscope_enabled must remain false.")
    if escalation["graphify_enabled"] is not False:
        raise AssertionError("DashScope offline escalation graphify_enabled must remain false.")
    if escalation["migration_writes_enabled"] is not False:
        raise AssertionError("DashScope offline escalation migration_writes_enabled must remain false.")
    if escalation["report_writing_enabled"] is not False:
        raise AssertionError("DashScope offline escalation report_writing_enabled must remain false.")
    if escalation["consumer_decision_policy_version"] != "1.0.0":
        raise AssertionError("DashScope offline escalation consumer_decision_policy_version drifted.")
    if escalation["decision_type"] != "consumer_decision_human_review_policy":
        raise AssertionError("DashScope offline escalation decision_type drifted.")
    if escalation["decision_mode"] != "offline_consumer_decision_policy_only":
        raise AssertionError("DashScope offline escalation decision_mode drifted.")
    if escalation["response_explanatory_only"] is not True:
        raise AssertionError("DashScope offline escalation must remain explanatory-only.")
    if escalation["live_response_parsing_enabled"] is not False:
        raise AssertionError("DashScope offline escalation must keep live response parsing disabled.")

    if tuple(escalation["allowed_acceptance_threshold_categories"]) != (
        EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_ACCEPTANCE_THRESHOLD_CATEGORIES
    ):
        raise AssertionError("DashScope offline escalation allowed_acceptance_threshold_categories drifted.")
    if tuple(escalation["allowed_escalation_fields"]) != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_MESSAGE_FIELDS:
        raise AssertionError("DashScope offline escalation allowed_escalation_fields drifted.")
    if tuple(escalation["required_escalation_fields"]) != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_REQUIRED_MESSAGE_FIELDS:
        raise AssertionError("DashScope offline escalation required_escalation_fields drifted.")
    if escalation["required_human_review_rules"] != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_REQUIRED_HUMAN_REVIEW_RULES:
        raise AssertionError("DashScope offline escalation required_human_review_rules drifted.")
    if escalation["confidence_messaging_policy"] != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_CONFIDENCE_MESSAGING_POLICY:
        raise AssertionError("DashScope offline escalation confidence_messaging_policy drifted.")
    if escalation["blocked_action_summary_policy"] != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_BLOCKED_ACTION_SUMMARY_POLICY:
        raise AssertionError("DashScope offline escalation blocked_action_summary_policy drifted.")
    if escalation["ready_to_migrate_claim_policy"] != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_READY_TO_MIGRATE_CLAIM_POLICY:
        raise AssertionError("DashScope offline escalation ready_to_migrate_claim_policy drifted.")
    if escalation["source_of_truth_policy"] != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_SOURCE_OF_TRUTH_POLICY:
        raise AssertionError("DashScope offline escalation source_of_truth_policy drifted.")
    if "explanatory only" not in escalation["source_of_truth_policy"]:
        raise AssertionError("DashScope offline escalation must keep Qwen output explanatory only.")
    if "cannot authorize writes" not in escalation["source_of_truth_policy"]:
        raise AssertionError("DashScope offline escalation must keep write authority blocked.")
    if tuple(escalation["forbidden_message_content"]) != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_FORBIDDEN_MESSAGE_CONTENT:
        raise AssertionError("DashScope offline escalation forbidden_message_content drifted.")
    if "hidden reasoning or chain-of-thought" not in escalation["forbidden_message_content"]:
        raise AssertionError("DashScope offline escalation must keep hidden reasoning blocked.")
    if "report-writing instructions" not in escalation["forbidden_message_content"]:
        raise AssertionError("DashScope offline escalation must keep report-writing instructions blocked.")
    if "qwen3.6-plus" not in escalation["redaction_policy"]:
        raise AssertionError("DashScope offline escalation redaction_policy must keep the intended model explicit.")
    if escalation["escalation_examples_in_memory_only"] is not True:
        raise AssertionError("DashScope offline escalation examples must remain in-memory only.")

    examples = escalation["simulated_escalation_examples"]
    if not isinstance(examples, list) or not examples:
        raise AssertionError("DashScope offline escalation simulated_escalation_examples must be a non-empty list.")
    if tuple(example["example_name"] for example in examples) != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_SIMULATED_EXAMPLE_NAMES:
        raise AssertionError("DashScope offline escalation simulated example names drifted.")
    for example in examples:
        if tuple(example.keys()) != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_SIMULATED_EXAMPLE_KEYS:
            raise AssertionError("DashScope offline escalation simulated example keys drifted.")
        if example["decision_state"] not in EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_DECISION_STATES:
            raise AssertionError("DashScope offline escalation example decision_state drifted.")
        if example["acceptance_threshold_category"] not in EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_ACCEPTANCE_THRESHOLD_CATEGORIES:
            raise AssertionError("DashScope offline escalation example acceptance_threshold_category drifted.")
        if not isinstance(example["accepted_explanatory_only"], bool):
            raise AssertionError("DashScope offline escalation example accepted_explanatory_only must be a boolean.")
        if not isinstance(example["example_reason"], str) or not example["example_reason"].strip():
            raise AssertionError("DashScope offline escalation example example_reason must be a non-empty string.")

        decision_inputs = example["decision_inputs"]
        if not isinstance(decision_inputs, dict):
            raise AssertionError("DashScope offline escalation example decision_inputs must be an object.")
        if tuple(decision_inputs.keys()) != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_DECISION_INPUTS:
            raise AssertionError("DashScope offline escalation example decision_inputs keys drifted.")

        escalation_fields = example["escalation_fields"]
        if not isinstance(escalation_fields, dict):
            raise AssertionError("DashScope offline escalation example escalation_fields must be an object.")
        if tuple(escalation_fields.keys()) != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_MESSAGE_FIELDS:
            raise AssertionError("DashScope offline escalation example escalation_fields keys drifted.")
        if escalation_fields["decision_state"] != example["decision_state"]:
            raise AssertionError("DashScope offline escalation example escalation_fields.decision_state drifted.")
        if escalation_fields["report_writing_enabled"] is not False:
            raise AssertionError("DashScope offline escalation example escalation_fields.report_writing_enabled must remain false.")
        if escalation_fields["runtime_enabled"] is not False:
            raise AssertionError("DashScope offline escalation example escalation_fields.runtime_enabled must remain false.")
        if escalation_fields["network_calls_allowed"] is not False:
            raise AssertionError("DashScope offline escalation example escalation_fields.network_calls_allowed must remain false.")
        if escalation_fields["live_response_parsing_enabled"] is not False:
            raise AssertionError(
                "DashScope offline escalation example escalation_fields.live_response_parsing_enabled must remain false."
            )
        if tuple(escalation_fields["forbidden_message_content"]) != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_FORBIDDEN_MESSAGE_CONTENT:
            raise AssertionError("DashScope offline escalation example forbidden_message_content drifted.")
        if escalation_fields["source_of_truth_policy"] != EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_SOURCE_OF_TRUTH_POLICY:
            raise AssertionError("DashScope offline escalation example source_of_truth_policy drifted.")
        if "qwen3.6-plus" not in escalation_fields["redaction_policy"]:
            raise AssertionError("DashScope offline escalation example redaction_policy must keep the intended model explicit.")

    input_summary = escalation["input_summary"]
    if not isinstance(input_summary, dict):
        raise AssertionError("DashScope offline escalation input_summary must be an object.")
    if set(input_summary.keys()) != set(EXPECTED_DASHSCOPE_OFFLINE_ESCALATION_INPUT_SUMMARY_KEYS):
        raise AssertionError("DashScope offline escalation input_summary keys drifted.")
    if input_summary["source_command"] != "hermes_inventory":
        raise AssertionError("DashScope offline escalation input_summary.source_command must remain hermes_inventory.")
    if input_summary["source_mode"] != "inventory":
        raise AssertionError("DashScope offline escalation input_summary.source_mode must remain inventory.")
    if input_summary["source_dry_run"] is not True:
        raise AssertionError("DashScope offline escalation input_summary.source_dry_run must remain true.")

    return escalation
