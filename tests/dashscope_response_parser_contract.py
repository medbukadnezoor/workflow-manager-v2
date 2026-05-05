from __future__ import annotations

from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL
from workflow_manager.dashscope_escalation import (
    DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_ACCEPTANCE_THRESHOLD_CATEGORIES,
    DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_MESSAGE_FIELDS,
    DASHSCOPE_OFFLINE_ESCALATION_FORBIDDEN_MESSAGE_CONTENT,
    DASHSCOPE_OFFLINE_ESCALATION_POLICY_VERSION,
    DASHSCOPE_OFFLINE_ESCALATION_SOURCE_OF_TRUTH_POLICY,
)
from workflow_manager.dashscope_request import DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS
from workflow_manager.dashscope_response import (
    DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS,
    DASHSCOPE_OFFLINE_RESPONSE_SHAPE_VERSION,
)
from workflow_manager.dashscope_response_parser import (
    DASHSCOPE_OFFLINE_RESPONSE_PARSER_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_RESPONSE_PARSER_CONSUMER_DECISION_KEYS,
    DASHSCOPE_OFFLINE_RESPONSE_PARSER_ESCALATION_SUMMARY_KEYS,
    DASHSCOPE_OFFLINE_RESPONSE_PARSER_EVIDENCE_VALIDATION_KEYS,
    DASHSCOPE_OFFLINE_RESPONSE_PARSER_INPUT_KIND,
    DASHSCOPE_OFFLINE_RESPONSE_PARSER_MODE,
    DASHSCOPE_OFFLINE_RESPONSE_PARSER_POLICY_VERSION,
    DASHSCOPE_OFFLINE_RESPONSE_PARSER_TYPE,
    DASHSCOPE_OFFLINE_RESPONSE_PARSER_VALIDATION_RESULTS,
)
from workflow_manager.dashscope_response_consumer import (
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_POLICY_VERSION,
)
from workflow_manager.dashscope_consumer_decision import (
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_CONFIDENCE_STATES,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_EVIDENCE_VALIDATION_RESULTS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VERSION,
)


EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_FIELDS = DASHSCOPE_OFFLINE_RESPONSE_PARSER_ALLOWED_FIELDS
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_VERSION = DASHSCOPE_OFFLINE_RESPONSE_PARSER_POLICY_VERSION
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_TYPE = DASHSCOPE_OFFLINE_RESPONSE_PARSER_TYPE
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_SOURCE = "hermes_inventory"
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_MODE = DASHSCOPE_OFFLINE_RESPONSE_PARSER_MODE
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_INTENDED_MODEL = DASHSCOPE_INTENDED_MODEL
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_INPUT_KIND = DASHSCOPE_OFFLINE_RESPONSE_PARSER_INPUT_KIND
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_PARSED_RESPONSE_KEYS = (
    DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS
)
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_EVIDENCE_VALIDATION_KEYS = (
    DASHSCOPE_OFFLINE_RESPONSE_PARSER_EVIDENCE_VALIDATION_KEYS
)
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_CONSUMER_DECISION_KEYS = (
    DASHSCOPE_OFFLINE_RESPONSE_PARSER_CONSUMER_DECISION_KEYS
)
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_ESCALATION_SUMMARY_KEYS = (
    DASHSCOPE_OFFLINE_RESPONSE_PARSER_ESCALATION_SUMMARY_KEYS
)
EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_VALIDATION_RESULTS = (
    DASHSCOPE_OFFLINE_RESPONSE_PARSER_VALIDATION_RESULTS
)


def verify_dashscope_offline_response_parser_contract(payload: dict | object) -> dict:
    parser_result = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)

    actual_keys = set(parser_result.keys())
    expected_keys = set(EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_FIELDS)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        parts = ["DashScope offline response parser contract keys drifted."]
        if missing:
            parts.append(f"Missing keys: {missing}.")
        if unexpected:
            parts.append(f"Unexpected keys: {unexpected}.")
        raise AssertionError(" ".join(parts))

    if parser_result["parser_policy_version"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_VERSION:
        raise AssertionError("DashScope offline response parser version drifted.")
    if parser_result["parser_type"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_TYPE:
        raise AssertionError("DashScope offline response parser type drifted.")
    if parser_result["source"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_SOURCE:
        raise AssertionError("DashScope offline response parser source drifted.")
    if parser_result["mode"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_MODE:
        raise AssertionError("DashScope offline response parser mode drifted.")
    if parser_result["intended_model"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_INTENDED_MODEL:
        raise AssertionError("DashScope offline response parser intended model drifted.")
    if parser_result["input_kind"] != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_INPUT_KIND:
        raise AssertionError("DashScope offline response parser input_kind drifted.")
    if not isinstance(parser_result["selected_model"], str):
        raise AssertionError("DashScope offline response parser selected_model must be a string.")
    if parser_result["runtime_enabled"] is not False:
        raise AssertionError("DashScope offline response parser runtime_enabled must remain false.")
    if parser_result["network_calls_allowed"] is not False:
        raise AssertionError("DashScope offline response parser network_calls_allowed must remain false.")
    if parser_result["qwen_dashscope_enabled"] is not False:
        raise AssertionError("DashScope offline response parser qwen_dashscope_enabled must remain false.")
    if parser_result["graphify_enabled"] is not False:
        raise AssertionError("DashScope offline response parser graphify_enabled must remain false.")
    if parser_result["migration_writes_enabled"] is not False:
        raise AssertionError("DashScope offline response parser migration_writes_enabled must remain false.")
    if parser_result["report_writing_enabled"] is not False:
        raise AssertionError("DashScope offline response parser report_writing_enabled must remain false.")
    if parser_result["response_explanatory_only"] is not True:
        raise AssertionError("DashScope offline response parser must remain explanatory only.")
    if parser_result["live_response_parsing_enabled"] is not False:
        raise AssertionError("DashScope offline response parser must keep live response parsing disabled.")
    if parser_result["response_shape_version"] != DASHSCOPE_OFFLINE_RESPONSE_SHAPE_VERSION:
        raise AssertionError("DashScope offline response parser response_shape_version drifted.")
    if parser_result["response_consumer_policy_version"] != DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_POLICY_VERSION:
        raise AssertionError("DashScope offline response parser response_consumer_policy_version drifted.")
    if parser_result["consumer_decision_policy_version"] != DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VERSION:
        raise AssertionError("DashScope offline response parser consumer_decision_policy_version drifted.")
    if parser_result["escalation_policy_version"] != DASHSCOPE_OFFLINE_ESCALATION_POLICY_VERSION:
        raise AssertionError("DashScope offline response parser escalation_policy_version drifted.")
    if parser_result["validation_result"] not in EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_VALIDATION_RESULTS:
        raise AssertionError("DashScope offline response parser validation_result drifted.")
    if parser_result["source_of_truth_policy"] != DASHSCOPE_OFFLINE_ESCALATION_SOURCE_OF_TRUTH_POLICY:
        raise AssertionError("DashScope offline response parser source_of_truth_policy drifted.")
    if "qwen3.6-plus" not in parser_result["redaction_policy"]:
        raise AssertionError("DashScope offline response parser redaction_policy must keep the intended model explicit.")

    parsed_response = parser_result["parsed_response"]
    if not isinstance(parsed_response, dict):
        raise AssertionError("DashScope offline response parser parsed_response must be an object.")
    if tuple(parsed_response.keys()) != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_PARSED_RESPONSE_KEYS:
        raise AssertionError("DashScope offline response parser parsed_response keys drifted.")

    evidence_validation_result = parser_result["evidence_validation_result"]
    if not isinstance(evidence_validation_result, dict):
        raise AssertionError("DashScope offline response parser evidence_validation_result must be an object.")
    if tuple(evidence_validation_result.keys()) != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_EVIDENCE_VALIDATION_KEYS:
        raise AssertionError("DashScope offline response parser evidence_validation_result keys drifted.")
    if evidence_validation_result["status"] not in (
        DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_EVIDENCE_VALIDATION_RESULTS + ("invalid-simulated-response",)
    ):
        raise AssertionError("DashScope offline response parser evidence_validation_result.status drifted.")
    if evidence_validation_result["grounding_status"] not in ("grounded", "ungrounded"):
        raise AssertionError("DashScope offline response parser grounding_status drifted.")
    if evidence_validation_result["expected_consumer_action"] not in ("accept", "reject"):
        raise AssertionError("DashScope offline response parser expected_consumer_action drifted.")

    consumer_decision = parser_result["consumer_decision"]
    if not isinstance(consumer_decision, dict):
        raise AssertionError("DashScope offline response parser consumer_decision must be an object.")
    if tuple(consumer_decision.keys()) != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_CONSUMER_DECISION_KEYS:
        raise AssertionError("DashScope offline response parser consumer_decision keys drifted.")
    if consumer_decision["decision_state"] not in DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES:
        raise AssertionError("DashScope offline response parser consumer_decision.decision_state drifted.")
    if not isinstance(consumer_decision["requires_human_review"], bool):
        raise AssertionError("DashScope offline response parser requires_human_review must be a boolean.")
    if not isinstance(consumer_decision["requires_deterministic_recheck"], bool):
        raise AssertionError("DashScope offline response parser requires_deterministic_recheck must be a boolean.")
    if not isinstance(consumer_decision["decision_reason"], str) or not consumer_decision["decision_reason"].strip():
        raise AssertionError("DashScope offline response parser decision_reason must be a non-empty string.")
    if tuple(consumer_decision["decision_inputs"].keys()) != DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS:
        raise AssertionError("DashScope offline response parser decision_inputs keys drifted.")
    if consumer_decision["decision_inputs"]["confidence_state"] not in DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_CONFIDENCE_STATES:
        raise AssertionError("DashScope offline response parser confidence_state drifted.")

    escalation_summary = parser_result["escalation_summary"]
    if not isinstance(escalation_summary, dict):
        raise AssertionError("DashScope offline response parser escalation_summary must be an object.")
    if tuple(escalation_summary.keys()) != EXPECTED_DASHSCOPE_OFFLINE_RESPONSE_PARSER_ESCALATION_SUMMARY_KEYS:
        raise AssertionError("DashScope offline response parser escalation_summary keys drifted.")
    if escalation_summary["acceptance_threshold_category"] not in (
        DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_ACCEPTANCE_THRESHOLD_CATEGORIES
    ):
        raise AssertionError("DashScope offline response parser escalation_summary.acceptance_threshold_category drifted.")
    if not isinstance(escalation_summary["accepted_explanatory_only"], bool):
        raise AssertionError("DashScope offline response parser accepted_explanatory_only must be a boolean.")
    escalation_fields = escalation_summary["escalation_fields"]
    if tuple(escalation_fields.keys()) != DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_MESSAGE_FIELDS:
        raise AssertionError("DashScope offline response parser escalation_fields keys drifted.")
    if escalation_fields["report_writing_enabled"] is not False:
        raise AssertionError("DashScope offline response parser escalation report_writing_enabled must remain false.")
    if escalation_fields["runtime_enabled"] is not False:
        raise AssertionError("DashScope offline response parser escalation runtime_enabled must remain false.")
    if escalation_fields["network_calls_allowed"] is not False:
        raise AssertionError("DashScope offline response parser escalation network_calls_allowed must remain false.")
    if escalation_fields["live_response_parsing_enabled"] is not False:
        raise AssertionError("DashScope offline response parser escalation live_response_parsing_enabled must remain false.")
    if tuple(escalation_fields["forbidden_message_content"]) != DASHSCOPE_OFFLINE_ESCALATION_FORBIDDEN_MESSAGE_CONTENT:
        raise AssertionError("DashScope offline response parser escalation forbidden_message_content drifted.")

    if not isinstance(parser_result["errors"], list):
        raise AssertionError("DashScope offline response parser errors must be a list.")
    if not isinstance(parser_result["warnings"], list):
        raise AssertionError("DashScope offline response parser warnings must be a list.")
    if set(parser_result["input_summary"].keys()) != set(DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS):
        raise AssertionError("DashScope offline response parser input_summary keys drifted.")

    return parser_result
