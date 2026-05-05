from __future__ import annotations

from dataclasses import dataclass

from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL
from workflow_manager.dashscope_request import DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS
from workflow_manager.dashscope_response import (
    DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS,
    DASHSCOPE_OFFLINE_RESPONSE_FORBIDDEN_OUTPUT_POLICY,
    DASHSCOPE_OFFLINE_RESPONSE_MODE,
    DASHSCOPE_OFFLINE_RESPONSE_REQUIRED_RESPONSE_FIELDS,
    DASHSCOPE_OFFLINE_RESPONSE_SHAPE_VERSION,
    DASHSCOPE_OFFLINE_RESPONSE_SOURCE,
    DASHSCOPE_OFFLINE_RESPONSE_TYPE,
)
from workflow_manager.dashscope_response_consumer import (
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_MODE,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_POLICY_VERSION,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SOURCE,
    DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_TYPE,
    sanitize_dashscope_response_consumer_examples,
)
from workflow_manager.dashscope_consumer_decision import (
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_CONFIDENCE_STATES,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_EVIDENCE_VALIDATION_RESULTS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_INPUTS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_MODEL_POLICY_STATUSES,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_STATES,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_MODE,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VERSION,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VIOLATION_FLAGS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_REJECT_FORBIDDEN_FLAGS,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_SOURCE,
    DASHSCOPE_OFFLINE_CONSUMER_DECISION_TYPE,
    _derive_decision_state as governed_consumer_decision_state,
    sanitize_dashscope_consumer_decision_examples,
)
from workflow_manager.dashscope_escalation import (
    DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_ACCEPTANCE_THRESHOLD_CATEGORIES,
    DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_MESSAGE_FIELDS,
    DASHSCOPE_OFFLINE_ESCALATION_FORBIDDEN_MESSAGE_CONTENT,
    DASHSCOPE_OFFLINE_ESCALATION_MODE,
    DASHSCOPE_OFFLINE_ESCALATION_POLICY_VERSION,
    DASHSCOPE_OFFLINE_ESCALATION_SOURCE,
    DASHSCOPE_OFFLINE_ESCALATION_SOURCE_OF_TRUTH_POLICY,
    DASHSCOPE_OFFLINE_ESCALATION_TYPE,
    _derive_acceptance_threshold_category as governed_acceptance_threshold_category,
    _derive_escalation_fields as governed_escalation_fields,
    sanitize_dashscope_escalation_examples,
)


DASHSCOPE_OFFLINE_RESPONSE_PARSER_POLICY_VERSION = "1.0.0"
DASHSCOPE_OFFLINE_RESPONSE_PARSER_TYPE = "offline_response_parser_validation_dry_run"
DASHSCOPE_OFFLINE_RESPONSE_PARSER_SOURCE = "hermes_inventory"
DASHSCOPE_OFFLINE_RESPONSE_PARSER_MODE = "offline_response_parser_validation_only"
DASHSCOPE_OFFLINE_RESPONSE_PARSER_INPUT_KIND = "simulated_response_only"
DASHSCOPE_OFFLINE_RESPONSE_PARSER_ALLOWED_FIELDS = (
    "parser_policy_version",
    "parser_type",
    "source",
    "mode",
    "intended_model",
    "selected_model",
    "model_policy_status",
    "model_policy_ready",
    "model_policy_requires_update",
    "local_config_ready",
    "input_kind",
    "runtime_enabled",
    "network_calls_allowed",
    "qwen_dashscope_enabled",
    "graphify_enabled",
    "migration_writes_enabled",
    "report_writing_enabled",
    "response_explanatory_only",
    "live_response_parsing_enabled",
    "response_shape_version",
    "response_consumer_policy_version",
    "consumer_decision_policy_version",
    "escalation_policy_version",
    "parsed_response",
    "validation_result",
    "evidence_validation_result",
    "consumer_decision",
    "escalation_summary",
    "errors",
    "warnings",
    "source_of_truth_policy",
    "redaction_policy",
    "input_summary",
)
DASHSCOPE_OFFLINE_RESPONSE_PARSER_INPUT_FIELDS = (
    "response_payload",
    "evidence_references",
    "forbidden_content_flags",
    "deterministic_mismatch_flag",
    "deterministic_evidence_metadata",
)
DASHSCOPE_OFFLINE_RESPONSE_PARSER_VALIDATION_RESULTS = (
    "accepted-explanatory-only",
    "human-review-required",
    "deterministic-recheck-required",
    "blocked-missing-evidence",
    "blocked-policy-violation",
    "rejected-unsafe",
    "rejected-invalid-simulated-response",
)
DASHSCOPE_OFFLINE_RESPONSE_PARSER_EVIDENCE_VALIDATION_KEYS = (
    "status",
    "grounding_status",
    "expected_consumer_action",
    "missing_evidence_fields",
    "unknown_evidence_references",
    "deterministic_reference_categories",
    "forbidden_content_flags",
)
DASHSCOPE_OFFLINE_RESPONSE_PARSER_CONSUMER_DECISION_KEYS = (
    "decision_state",
    "requires_human_review",
    "requires_deterministic_recheck",
    "decision_reason",
    "decision_inputs",
)
DASHSCOPE_OFFLINE_RESPONSE_PARSER_ESCALATION_SUMMARY_KEYS = (
    "acceptance_threshold_category",
    "accepted_explanatory_only",
    "escalation_fields",
)


def _assert_json_object(label: str, value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object.")
    return dict(value)


def _assert_bool(label: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be a boolean.")
    return value


def _assert_string(label: str, value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string.")
    return value


def _assert_string_list(label: str, value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{label} must be a list of strings.")
    return list(value)


def _assert_exact_keys(label: str, payload: dict[str, object], expected_keys: tuple[str, ...]) -> None:
    actual = set(payload.keys())
    expected = set(expected_keys)
    if actual == expected:
        return
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    parts = [f"{label} keys drifted."]
    if missing:
        parts.append(f"Missing keys: {missing}.")
    if unexpected:
        parts.append(f"Unexpected keys: {unexpected}.")
    raise ValueError(" ".join(parts))


def _assert_unique_strings(label: str, values: list[str]) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must not contain duplicates.")


def _normalize_response_shape_policy(payload: dict[str, object] | object) -> dict[str, object]:
    response_shape = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)
    _assert_exact_keys(
        "Offline response parser response-shape policy",
        response_shape,
        DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_FIELDS,
    )
    if _assert_string("response shape source", response_shape["source"]) != DASHSCOPE_OFFLINE_RESPONSE_SOURCE:
        raise ValueError("Offline response parser requires hermes_inventory response-shape input.")
    if _assert_string("response shape mode", response_shape["mode"]) != DASHSCOPE_OFFLINE_RESPONSE_MODE:
        raise ValueError("Offline response parser requires offline_response_shape_only mode.")
    if (
        _assert_string("response shape version", response_shape["response_shape_version"])
        != DASHSCOPE_OFFLINE_RESPONSE_SHAPE_VERSION
    ):
        raise ValueError("Offline response parser received an unexpected response-shape version.")
    if _assert_string("response shape type", response_shape["response_type"]) != DASHSCOPE_OFFLINE_RESPONSE_TYPE:
        raise ValueError("Offline response parser requires explanatory_response_shape input.")
    if _assert_string("response shape intended_model", response_shape["intended_model"]) != DASHSCOPE_INTENDED_MODEL:
        raise ValueError("Offline response parser requires the governed intended model.")
    if not _assert_bool("response shape response_explanatory_only", response_shape["response_explanatory_only"]):
        raise ValueError("Offline response parser requires response_explanatory_only=true.")
    if _assert_bool("response shape live_response_parsing_enabled", response_shape["live_response_parsing_enabled"]):
        raise ValueError("Offline response parser requires live_response_parsing_enabled=false.")
    if _assert_bool("response shape runtime_enabled", response_shape["runtime_enabled"]):
        raise ValueError("Offline response parser requires runtime_enabled=false.")
    if _assert_bool("response shape network_calls_allowed", response_shape["network_calls_allowed"]):
        raise ValueError("Offline response parser requires network_calls_allowed=false.")
    return response_shape


def _normalize_response_consumer_policy(payload: dict[str, object] | object) -> dict[str, object]:
    consumer_policy = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)
    _assert_exact_keys(
        "Offline response parser response-consumer policy",
        consumer_policy,
        DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_FIELDS,
    )
    if _assert_string("response-consumer source", consumer_policy["source"]) != DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_SOURCE:
        raise ValueError("Offline response parser requires hermes_inventory response-consumer input.")
    if _assert_string("response-consumer mode", consumer_policy["mode"]) != DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_MODE:
        raise ValueError("Offline response parser requires offline_response_consumer_policy_only mode.")
    if (
        _assert_string("response-consumer version", consumer_policy["response_consumer_policy_version"])
        != DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_POLICY_VERSION
    ):
        raise ValueError("Offline response parser received an unexpected response-consumer policy version.")
    if _assert_string("response-consumer type", consumer_policy["consumer_type"]) != DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_TYPE:
        raise ValueError("Offline response parser requires evidence_slot_response_consumer_policy input.")
    if not _assert_bool("response-consumer response_explanatory_only", consumer_policy["response_explanatory_only"]):
        raise ValueError("Offline response parser requires response_explanatory_only=true in the response-consumer policy.")
    if _assert_bool("response-consumer live_response_parsing_enabled", consumer_policy["live_response_parsing_enabled"]):
        raise ValueError("Offline response parser requires live_response_parsing_enabled=false in the response-consumer policy.")
    if _assert_bool("response-consumer runtime_enabled", consumer_policy["runtime_enabled"]):
        raise ValueError("Offline response parser requires runtime_enabled=false in the response-consumer policy.")
    if _assert_bool("response-consumer network_calls_allowed", consumer_policy["network_calls_allowed"]):
        raise ValueError("Offline response parser requires network_calls_allowed=false in the response-consumer policy.")
    return consumer_policy


def _normalize_consumer_decision_policy(payload: dict[str, object] | object) -> dict[str, object]:
    decision_policy = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)
    _assert_exact_keys(
        "Offline response parser consumer-decision policy",
        decision_policy,
        DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_FIELDS,
    )
    if _assert_string("consumer-decision source", decision_policy["source"]) != DASHSCOPE_OFFLINE_CONSUMER_DECISION_SOURCE:
        raise ValueError("Offline response parser requires hermes_inventory consumer-decision input.")
    if _assert_string("consumer-decision mode", decision_policy["mode"]) != DASHSCOPE_OFFLINE_CONSUMER_DECISION_MODE:
        raise ValueError("Offline response parser requires offline_consumer_decision_policy_only mode.")
    if (
        _assert_string("consumer-decision version", decision_policy["consumer_decision_policy_version"])
        != DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VERSION
    ):
        raise ValueError("Offline response parser received an unexpected consumer-decision policy version.")
    if _assert_string("consumer-decision type", decision_policy["decision_type"]) != DASHSCOPE_OFFLINE_CONSUMER_DECISION_TYPE:
        raise ValueError("Offline response parser requires consumer_decision_human_review_policy input.")
    if not _assert_bool("consumer-decision response_explanatory_only", decision_policy["response_explanatory_only"]):
        raise ValueError("Offline response parser requires response_explanatory_only=true in the consumer-decision policy.")
    if _assert_bool("consumer-decision live_response_parsing_enabled", decision_policy["live_response_parsing_enabled"]):
        raise ValueError("Offline response parser requires live_response_parsing_enabled=false in the consumer-decision policy.")
    if _assert_bool("consumer-decision runtime_enabled", decision_policy["runtime_enabled"]):
        raise ValueError("Offline response parser requires runtime_enabled=false in the consumer-decision policy.")
    if _assert_bool("consumer-decision network_calls_allowed", decision_policy["network_calls_allowed"]):
        raise ValueError("Offline response parser requires network_calls_allowed=false in the consumer-decision policy.")
    return decision_policy


def _normalize_escalation_policy(payload: dict[str, object] | object) -> dict[str, object]:
    escalation_policy = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)
    _assert_exact_keys(
        "Offline response parser escalation policy",
        escalation_policy,
        DASHSCOPE_OFFLINE_ESCALATION_ALLOWED_FIELDS,
    )
    if _assert_string("escalation source", escalation_policy["source"]) != DASHSCOPE_OFFLINE_ESCALATION_SOURCE:
        raise ValueError("Offline response parser requires hermes_inventory escalation input.")
    if _assert_string("escalation mode", escalation_policy["mode"]) != DASHSCOPE_OFFLINE_ESCALATION_MODE:
        raise ValueError("Offline response parser requires offline_escalation_policy_only mode.")
    if (
        _assert_string("escalation version", escalation_policy["escalation_policy_version"])
        != DASHSCOPE_OFFLINE_ESCALATION_POLICY_VERSION
    ):
        raise ValueError("Offline response parser received an unexpected escalation policy version.")
    if _assert_string("escalation type", escalation_policy["escalation_type"]) != DASHSCOPE_OFFLINE_ESCALATION_TYPE:
        raise ValueError("Offline response parser requires acceptance_threshold_escalation_report_policy input.")
    if not _assert_bool("escalation response_explanatory_only", escalation_policy["response_explanatory_only"]):
        raise ValueError("Offline response parser requires response_explanatory_only=true in the escalation policy.")
    if _assert_bool("escalation live_response_parsing_enabled", escalation_policy["live_response_parsing_enabled"]):
        raise ValueError("Offline response parser requires live_response_parsing_enabled=false in the escalation policy.")
    if _assert_bool("escalation report_writing_enabled", escalation_policy["report_writing_enabled"]):
        raise ValueError("Offline response parser requires report_writing_enabled=false in the escalation policy.")
    if _assert_bool("escalation runtime_enabled", escalation_policy["runtime_enabled"]):
        raise ValueError("Offline response parser requires runtime_enabled=false in the escalation policy.")
    if _assert_bool("escalation network_calls_allowed", escalation_policy["network_calls_allowed"]):
        raise ValueError("Offline response parser requires network_calls_allowed=false in the escalation policy.")
    return escalation_policy


def _normalize_deterministic_evidence_metadata(candidate: object) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    metadata: dict[str, str] = {}
    if not isinstance(candidate, dict):
        return {}, ["deterministic_evidence_metadata must be an object."]

    for key, value in candidate.items():
        if not isinstance(key, str):
            errors.append("deterministic_evidence_metadata keys must be strings.")
            continue
        if key not in DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES:
            errors.append(f"deterministic_evidence_metadata contains unsupported evidence key `{key}`.")
            continue
        if not isinstance(value, str) or not value.strip():
            errors.append(f"deterministic_evidence_metadata.`{key}` must be a non-empty string.")
            continue
        metadata[key] = value
    return metadata, errors


def _normalize_simulated_response_wrapper(candidate: object) -> tuple[dict[str, object], list[str]]:
    if not isinstance(candidate, dict):
        return {}, ["simulated_response must be an object."]
    payload = dict(candidate)
    errors: list[str] = []
    actual = set(payload.keys())
    expected = set(DASHSCOPE_OFFLINE_RESPONSE_PARSER_INPUT_FIELDS)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        errors.append(f"simulated_response is missing required input keys: {missing}.")
    if unexpected:
        errors.append(f"simulated_response contains unsupported input keys: {unexpected}.")
    return payload, errors


def _normalize_response_payload(
    candidate: object,
    response_shape: dict[str, object],
) -> tuple[dict[str, object], list[str], list[str]]:
    errors: list[str] = []
    derived_forbidden_flags: list[str] = []
    if not isinstance(candidate, dict):
        return {}, ["response_payload must be an object."], derived_forbidden_flags

    payload = dict(candidate)
    actual = set(payload.keys())
    expected = set(DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        errors.append(f"response_payload is missing required response fields: {missing}.")
    if unexpected:
        errors.append(f"response_payload contains unsupported response fields: {unexpected}.")
        derived_forbidden_flags.append("unknown_output_field")

    normalized: dict[str, object] = {}
    string_fields = ("analysis_summary", "risk_summary", "recommended_next_step", "source_of_truth_policy", "redaction_policy")
    for field in string_fields:
        value = payload.get(field)
        if field not in payload:
            continue
        if not isinstance(value, str) or not value.strip():
            errors.append(f"response_payload.`{field}` must be a non-empty string.")
            continue
        normalized[field] = value

    blocked_actions = payload.get("blocked_actions")
    if "blocked_actions" in payload:
        if not isinstance(blocked_actions, list) or not all(isinstance(item, str) and item.strip() for item in blocked_actions):
            errors.append("response_payload.`blocked_actions` must be a list of non-empty strings.")
        else:
            normalized["blocked_actions"] = list(blocked_actions)

    required_human_review = payload.get("required_human_review")
    if "required_human_review" in payload:
        if not isinstance(required_human_review, bool):
            errors.append("response_payload.`required_human_review` must be a boolean.")
        else:
            normalized["required_human_review"] = required_human_review

    confidence = payload.get("confidence")
    if "confidence" in payload:
        if not isinstance(confidence, str):
            errors.append("response_payload.`confidence` must be a string.")
        elif confidence not in DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_CONFIDENCE_STATES:
            errors.append(
                "response_payload.`confidence` must be one of "
                + ", ".join(DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_CONFIDENCE_STATES)
                + "."
            )
        else:
            normalized["confidence"] = confidence

    forbidden_output_policy = payload.get("forbidden_output_policy")
    if "forbidden_output_policy" in payload:
        if not isinstance(forbidden_output_policy, list) or not all(
            isinstance(item, str) and item.strip() for item in forbidden_output_policy
        ):
            errors.append("response_payload.`forbidden_output_policy` must be a list of non-empty strings.")
        elif tuple(forbidden_output_policy) != tuple(response_shape["forbidden_output_policy"]):
            errors.append("response_payload.`forbidden_output_policy` must match the governed forbidden-output policy.")
        else:
            normalized["forbidden_output_policy"] = list(forbidden_output_policy)

    if normalized.get("source_of_truth_policy") is not None and normalized["source_of_truth_policy"] != response_shape["source_of_truth_policy"]:
        errors.append("response_payload.`source_of_truth_policy` must match the governed source-of-truth policy.")
        derived_forbidden_flags.append("source_of_truth_override")
    if normalized.get("redaction_policy") is not None and normalized["redaction_policy"] != response_shape["redaction_policy"]:
        errors.append("response_payload.`redaction_policy` must match the governed redaction policy.")

    return normalized, errors, derived_forbidden_flags


def _normalize_forbidden_flags(candidate: object) -> tuple[list[str], list[str]]:
    if not isinstance(candidate, list) or not all(isinstance(item, str) for item in candidate):
        return [], ["forbidden_content_flags must be a list of strings."]
    flags = list(candidate)
    _assert_unique_strings("forbidden_content_flags", flags)
    allowed = set(DASHSCOPE_OFFLINE_CONSUMER_DECISION_REJECT_FORBIDDEN_FLAGS + DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VIOLATION_FLAGS)
    unsupported = [flag for flag in flags if flag not in allowed]
    if unsupported:
        return flags, [f"forbidden_content_flags contains unsupported flags: {unsupported}."]
    return flags, []


def _normalize_evidence_references(
    candidate: object,
    parsed_response: dict[str, object],
    deterministic_evidence_metadata: dict[str, str],
) -> tuple[dict[str, list[str]], list[str], list[str], list[str]]:
    errors: list[str] = []
    missing_evidence_fields: list[str] = []
    unknown_evidence_references: list[str] = []
    normalized: dict[str, list[str]] = {}
    if not isinstance(candidate, dict):
        return {}, [], [], ["evidence_references must be an object."]

    allowed_categories = set(DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_ALLOWED_EVIDENCE_REFERENCE_CATEGORIES)
    provided = dict(candidate)
    fields_with_invalid_references: set[str] = set()
    for field_name, references_value in provided.items():
        if field_name not in DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE:
            errors.append(f"evidence_references contains unsupported response field `{field_name}`.")
            continue
        if field_name not in parsed_response:
            errors.append(f"evidence_references cites `{field_name}` without a parsed response field.")
            continue
        if not isinstance(references_value, list) or not all(isinstance(item, str) for item in references_value):
            errors.append(f"evidence_references.`{field_name}` must be a list of strings.")
            continue
        references = list(references_value)
        if not references:
            errors.append(f"evidence_references.`{field_name}` must not be empty.")
            continue
        _assert_unique_strings(f"evidence_references.`{field_name}`", references)
        unknown = [
            reference
            for reference in references
            if reference not in allowed_categories or reference not in deterministic_evidence_metadata
        ]
        if unknown:
            fields_with_invalid_references.add(field_name)
            unknown_evidence_references.extend(unknown)
            continue
        normalized[field_name] = references

    for field_name in DASHSCOPE_OFFLINE_RESPONSE_CONSUMER_RESPONSE_FIELDS_REQUIRING_EVIDENCE:
        if (
            field_name in parsed_response
            and field_name not in normalized
            and field_name not in fields_with_invalid_references
        ):
            missing_evidence_fields.append(field_name)

    missing_evidence_fields = list(dict.fromkeys(missing_evidence_fields))
    unknown_evidence_references = list(dict.fromkeys(unknown_evidence_references))
    return normalized, missing_evidence_fields, unknown_evidence_references, errors


def _determine_evidence_status(
    *,
    structural_errors: list[str],
    missing_evidence_fields: list[str],
    unknown_evidence_references: list[str],
    forbidden_content_flags: list[str],
    deterministic_mismatch_flag: bool,
) -> str:
    if structural_errors:
        return "invalid-simulated-response"
    if forbidden_content_flags:
        return "policy-violation"
    if missing_evidence_fields:
        return "missing-evidence"
    if unknown_evidence_references:
        return "unknown-evidence"
    if deterministic_mismatch_flag:
        return "deterministic-mismatch"
    return "grounded"


def _derive_consumer_decision_state(decision_inputs: dict[str, object]) -> tuple[str, bool, bool]:
    missing_evidence_fields = list(decision_inputs["missing_evidence_fields"])
    unknown_evidence_references = list(decision_inputs["unknown_evidence_references"])
    forbidden_content_flags = list(decision_inputs["forbidden_content_flags"])
    source_of_truth_override_flag = bool(decision_inputs["source_of_truth_override_flag"])
    migration_write_authorization_flag = bool(decision_inputs["migration_write_authorization_flag"])
    ready_to_migrate_claim_flag = bool(decision_inputs["ready_to_migrate_claim_flag"])
    confidence_state = str(decision_inputs["confidence_state"])
    required_human_review_flag = bool(decision_inputs["required_human_review_flag"])
    model_policy_status = str(decision_inputs["model_policy_status"])
    deterministic_mismatch_flag = bool(decision_inputs["deterministic_mismatch_flag"])

    reject_flags = set(DASHSCOPE_OFFLINE_CONSUMER_DECISION_REJECT_FORBIDDEN_FLAGS)
    policy_violation_flags = set(DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VIOLATION_FLAGS)

    if source_of_truth_override_flag or "source_of_truth_override" in forbidden_content_flags:
        return "reject_unsafe", False, False
    if migration_write_authorization_flag or "migration_write_instructions" in forbidden_content_flags:
        return "reject_unsafe", False, False
    if ready_to_migrate_claim_flag or "ready_to_migrate_without_deterministic_gates" in forbidden_content_flags:
        return "reject_unsafe", False, False
    if any(flag in reject_flags for flag in forbidden_content_flags):
        return "reject_unsafe", False, False
    if any(flag in policy_violation_flags for flag in forbidden_content_flags):
        return "blocked_by_policy_violation", True, False
    if missing_evidence_fields:
        return "blocked_by_missing_evidence", False, False
    if unknown_evidence_references:
        return "requires_deterministic_recheck", False, True
    if deterministic_mismatch_flag:
        return "escalate_human_review", True, False
    if model_policy_status == "mismatch":
        return "escalate_human_review", True, False
    if confidence_state == "missing":
        return "requires_deterministic_recheck", False, True
    if confidence_state == "low":
        return "escalate_human_review", True, False
    if required_human_review_flag:
        return "escalate_human_review", True, False
    return "accept_explanatory_only", False, False


def _derive_acceptance_threshold_category(decision_state: str) -> str:
    mapping = {
        "accept_explanatory_only": "explanatory_only_acceptance",
        "escalate_human_review": "human_review_required",
        "requires_deterministic_recheck": "deterministic_recheck_required",
        "reject_unsafe": "unsafe_rejection",
        "blocked_by_missing_evidence": "missing_evidence_block",
        "blocked_by_policy_violation": "policy_violation_block",
    }
    return mapping[decision_state]


def _derive_blocked_reason(decision_state: str, decision_inputs: dict[str, object]) -> str:
    forbidden_flags = set(decision_inputs["forbidden_content_flags"])
    if decision_inputs["source_of_truth_override_flag"] or "source_of_truth_override" in forbidden_flags:
        return "source-of-truth-override"
    if decision_inputs["migration_write_authorization_flag"] or "migration_write_instructions" in forbidden_flags:
        return "migration-write-authorization"
    if decision_inputs["ready_to_migrate_claim_flag"] or "ready_to_migrate_without_deterministic_gates" in forbidden_flags:
        return "ready-to-migrate-claim-without-deterministic-gates"
    if "hidden_reasoning" in forbidden_flags or "chain_of_thought" in forbidden_flags:
        return "hidden-reasoning-or-chain-of-thought"
    if forbidden_flags.intersection({"api_key_material", "raw_env", "env_values", "credentials", "tokens"}):
        return "secret-like-content"
    if forbidden_flags.intersection({"project_source_code", "target_repo_file_contents"}):
        return "target-repo-or-source-content"
    if forbidden_flags.intersection(set(DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VIOLATION_FLAGS)):
        return "policy-violation"
    if decision_inputs["missing_evidence_fields"]:
        return "missing-deterministic-evidence"
    if decision_inputs["unknown_evidence_references"]:
        return "unknown-evidence-reference"
    if decision_inputs["deterministic_mismatch_flag"]:
        return "deterministic-mismatch"
    if decision_inputs["model_policy_status"] == "mismatch":
        return "model-policy-mismatch"
    if decision_inputs["confidence_state"] == "missing":
        return "missing-confidence"
    if decision_inputs["confidence_state"] == "low":
        return "low-confidence"
    if decision_state == "accept_explanatory_only":
        return "explanatory-only-acceptance"
    return "human-review-required"


def _derive_blocked_actions_summary(blocked_actions: list[str], blocked_actions_present: bool) -> str:
    if blocked_actions_present:
        return (
            "Blocked actions remain blocked: "
            + ", ".join(blocked_actions)
            + ". Do not authorize target-repo writes, migration writes, ready-to-migrate claims, Graphify actions, "
            + "network calls, or report writing."
        )
    return (
        "No additional blocked actions were surfaced. This message still cannot authorize target-repo writes, "
        "migration writes, ready-to-migrate claims, Graphify actions, network calls, or report writing."
    )


def _derive_allowed_human_message(decision_state: str, decision_inputs: dict[str, object], decision_reason: str) -> str:
    if decision_state == "accept_explanatory_only":
        prefix = "Accept only as explanatory output."
    elif decision_state == "blocked_by_missing_evidence":
        prefix = "Blocked pending deterministic recheck because deterministic evidence is missing."
    elif decision_state == "blocked_by_policy_violation":
        prefix = "Blocked for policy violation and escalate to human review."
    elif decision_state == "reject_unsafe":
        prefix = "Blocked as unsafe and escalate to human review."
    elif decision_state == "requires_deterministic_recheck":
        prefix = "Do not accept. Deterministic recheck is required before trust."
    else:
        prefix = "Do not accept. Human review is required before trust."

    confidence_state = str(decision_inputs["confidence_state"])
    confidence_note = ""
    if confidence_state == "low":
        confidence_note = " Low confidence stays advisory only."
    elif confidence_state == "missing":
        confidence_note = " Missing confidence requires deterministic recheck."

    return (
        f"{prefix} {decision_reason}{confidence_note} Deterministic Hermes inventory/status/doctor data remains the "
        "source of truth. Do not authorize writes, migration, Graphify actions, or report writing from this message."
    )


def _derive_escalation_fields(
    decision_state: str,
    decision_inputs: dict[str, object],
    decision_reason: str,
    blocked_actions: list[str],
) -> dict[str, object]:
    human_review_required = decision_state in {
        "reject_unsafe",
        "blocked_by_policy_violation",
        "escalate_human_review",
    }
    deterministic_recheck_required = decision_state in {
        "blocked_by_missing_evidence",
        "requires_deterministic_recheck",
    }
    blocked = decision_state in {
        "reject_unsafe",
        "blocked_by_missing_evidence",
        "blocked_by_policy_violation",
    }
    return {
        "decision_state": decision_state,
        "human_review_required": human_review_required,
        "deterministic_recheck_required": deterministic_recheck_required,
        "blocked": blocked,
        "blocked_reason": _derive_blocked_reason(decision_state, decision_inputs),
        "evidence_status": str(decision_inputs["evidence_validation_result"]),
        "confidence_status": str(decision_inputs["confidence_state"]),
        "blocked_actions_summary": _derive_blocked_actions_summary(
            blocked_actions,
            bool(decision_inputs["blocked_actions_present"]),
        ),
        "allowed_human_message": _derive_allowed_human_message(decision_state, decision_inputs, decision_reason),
        "forbidden_message_content": list(DASHSCOPE_OFFLINE_ESCALATION_FORBIDDEN_MESSAGE_CONTENT),
        "source_of_truth_policy": DASHSCOPE_OFFLINE_ESCALATION_SOURCE_OF_TRUTH_POLICY,
        "redaction_policy": (
            "Keep API-key values, .env values, raw secrets, partial secret fragments, source code, target-repo file "
            f"contents, and live model text out of parser output while keeping {DASHSCOPE_INTENDED_MODEL} explicit as "
            "non-secret intended model metadata."
        ),
        "report_writing_enabled": False,
        "runtime_enabled": False,
        "network_calls_allowed": False,
        "live_response_parsing_enabled": False,
    }


def _derive_validation_result(decision_state: str, structural_errors: list[str]) -> str:
    if structural_errors:
        return "rejected-invalid-simulated-response"
    mapping = {
        "accept_explanatory_only": "accepted-explanatory-only",
        "escalate_human_review": "human-review-required",
        "requires_deterministic_recheck": "deterministic-recheck-required",
        "reject_unsafe": "rejected-unsafe",
        "blocked_by_missing_evidence": "blocked-missing-evidence",
        "blocked_by_policy_violation": "blocked-policy-violation",
    }
    return mapping[decision_state]


def _build_evidence_reason(
    evidence_status: str,
    missing_evidence_fields: list[str],
    unknown_evidence_references: list[str],
    forbidden_content_flags: list[str],
) -> str:
    if evidence_status == "grounded":
        return "Accept as explanatory-only because all governed evidence-required fields cite deterministic evidence."
    if evidence_status == "missing-evidence":
        return "Reject because governed response fields are missing deterministic evidence references."
    if evidence_status == "unknown-evidence":
        return "Reject because one or more evidence references fall outside the governed deterministic vocabulary."
    if evidence_status == "deterministic-mismatch":
        return "Reject because the simulated explanation conflicts with deterministic Hermes data."
    if forbidden_content_flags:
        return "Reject because forbidden or unsafe content was detected in the simulated response path."
    if missing_evidence_fields:
        return "Reject because required deterministic evidence is incomplete."
    if unknown_evidence_references:
        return "Reject because unknown evidence references were supplied."
    return "Reject because the simulated response payload is structurally invalid."


def _derive_parser_messages(
    validation_result: str,
    decision_state: str,
    *,
    structural_errors: list[str],
    missing_evidence_fields: list[str],
    unknown_evidence_references: list[str],
    forbidden_content_flags: list[str],
    decision_reason: str,
) -> tuple[list[str], list[str]]:
    errors = list(structural_errors)
    warnings: list[str] = []
    if validation_result == "accepted-explanatory-only":
        return errors, warnings
    if decision_state == "blocked_by_missing_evidence":
        errors.append(
            "Missing deterministic evidence for governed response fields: "
            + ", ".join(missing_evidence_fields)
            + "."
        )
        return errors, warnings
    if decision_state == "requires_deterministic_recheck":
        warnings.append(decision_reason)
        if unknown_evidence_references:
            warnings.append(
                "Unknown evidence references require deterministic recheck: "
                + ", ".join(unknown_evidence_references)
                + "."
            )
        return errors, warnings
    if decision_state == "escalate_human_review":
        warnings.append(decision_reason)
        return errors, warnings
    if decision_state == "reject_unsafe":
        if forbidden_content_flags:
            errors.append(
                "Rejected unsafe simulated response content: " + ", ".join(sorted(forbidden_content_flags)) + "."
            )
        else:
            errors.append(decision_reason)
        return errors, warnings
    errors.append(decision_reason)
    return errors, warnings


@dataclass(frozen=True)
class DashScopeOfflineResponseParserResult:
    parser_policy_version: str
    parser_type: str
    source: str
    mode: str
    intended_model: str
    selected_model: str
    model_policy_status: str
    model_policy_ready: bool
    model_policy_requires_update: bool
    local_config_ready: bool
    input_kind: str
    runtime_enabled: bool
    network_calls_allowed: bool
    qwen_dashscope_enabled: bool
    graphify_enabled: bool
    migration_writes_enabled: bool
    report_writing_enabled: bool
    response_explanatory_only: bool
    live_response_parsing_enabled: bool
    response_shape_version: str
    response_consumer_policy_version: str
    consumer_decision_policy_version: str
    escalation_policy_version: str
    parsed_response: dict[str, object]
    validation_result: str
    evidence_validation_result: dict[str, object]
    consumer_decision: dict[str, object]
    escalation_summary: dict[str, object]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    source_of_truth_policy: str
    redaction_policy: str
    input_summary: dict[str, object]

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "parser_policy_version": self.parser_policy_version,
            "parser_type": self.parser_type,
            "source": self.source,
            "mode": self.mode,
            "intended_model": self.intended_model,
            "selected_model": self.selected_model,
            "model_policy_status": self.model_policy_status,
            "model_policy_ready": self.model_policy_ready,
            "model_policy_requires_update": self.model_policy_requires_update,
            "local_config_ready": self.local_config_ready,
            "input_kind": self.input_kind,
            "runtime_enabled": self.runtime_enabled,
            "network_calls_allowed": self.network_calls_allowed,
            "qwen_dashscope_enabled": self.qwen_dashscope_enabled,
            "graphify_enabled": self.graphify_enabled,
            "migration_writes_enabled": self.migration_writes_enabled,
            "report_writing_enabled": self.report_writing_enabled,
            "response_explanatory_only": self.response_explanatory_only,
            "live_response_parsing_enabled": self.live_response_parsing_enabled,
            "response_shape_version": self.response_shape_version,
            "response_consumer_policy_version": self.response_consumer_policy_version,
            "consumer_decision_policy_version": self.consumer_decision_policy_version,
            "escalation_policy_version": self.escalation_policy_version,
            "parsed_response": {
                key: list(value) if isinstance(value, list) else value
                for key, value in self.parsed_response.items()
            },
            "validation_result": self.validation_result,
            "evidence_validation_result": {
                "status": self.evidence_validation_result["status"],
                "grounding_status": self.evidence_validation_result["grounding_status"],
                "expected_consumer_action": self.evidence_validation_result["expected_consumer_action"],
                "missing_evidence_fields": list(self.evidence_validation_result["missing_evidence_fields"]),
                "unknown_evidence_references": list(self.evidence_validation_result["unknown_evidence_references"]),
                "deterministic_reference_categories": list(
                    self.evidence_validation_result["deterministic_reference_categories"]
                ),
                "forbidden_content_flags": list(self.evidence_validation_result["forbidden_content_flags"]),
            },
            "consumer_decision": {
                "decision_state": self.consumer_decision["decision_state"],
                "requires_human_review": self.consumer_decision["requires_human_review"],
                "requires_deterministic_recheck": self.consumer_decision["requires_deterministic_recheck"],
                "decision_reason": self.consumer_decision["decision_reason"],
                "decision_inputs": {
                    key: (
                        list(value)
                        if isinstance(value, list)
                        else value
                    )
                    for key, value in self.consumer_decision["decision_inputs"].items()
                },
            },
            "escalation_summary": {
                "acceptance_threshold_category": self.escalation_summary["acceptance_threshold_category"],
                "accepted_explanatory_only": self.escalation_summary["accepted_explanatory_only"],
                "escalation_fields": {
                    key: (
                        list(value)
                        if isinstance(value, list)
                        else value
                    )
                    for key, value in self.escalation_summary["escalation_fields"].items()
                },
            },
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "source_of_truth_policy": self.source_of_truth_policy,
            "redaction_policy": self.redaction_policy,
            "input_summary": dict(self.input_summary),
        }


def parse_hermes_qwen_offline_simulated_response(
    simulated_response: dict[str, object] | object,
    response_shape: dict[str, object] | object,
    response_consumer_policy: dict[str, object] | object,
    consumer_decision_policy: dict[str, object] | object,
    escalation_policy: dict[str, object] | object,
) -> DashScopeOfflineResponseParserResult:
    response_shape_payload = _normalize_response_shape_policy(response_shape)
    response_consumer_payload = _normalize_response_consumer_policy(response_consumer_policy)
    consumer_decision_payload = _normalize_consumer_decision_policy(consumer_decision_policy)
    escalation_payload = _normalize_escalation_policy(escalation_policy)

    wrapper, wrapper_errors = _normalize_simulated_response_wrapper(simulated_response)
    parsed_response: dict[str, object] = {}
    structural_errors = list(wrapper_errors)
    derived_forbidden_flags: list[str] = []

    deterministic_evidence_metadata, deterministic_metadata_errors = _normalize_deterministic_evidence_metadata(
        wrapper.get("deterministic_evidence_metadata", {})
    )
    structural_errors.extend(deterministic_metadata_errors)

    normalized_forbidden_flags, forbidden_flag_errors = _normalize_forbidden_flags(
        wrapper.get("forbidden_content_flags", [])
    )
    structural_errors.extend(forbidden_flag_errors)

    if "deterministic_mismatch_flag" in wrapper:
        try:
            deterministic_mismatch_flag = _assert_bool(
                "deterministic_mismatch_flag",
                wrapper["deterministic_mismatch_flag"],
            )
        except ValueError as exc:
            deterministic_mismatch_flag = False
            structural_errors.append(str(exc))
    else:
        deterministic_mismatch_flag = False

    payload, payload_errors, payload_derived_flags = _normalize_response_payload(
        wrapper.get("response_payload", {}),
        response_shape_payload,
    )
    parsed_response = {
        field: payload[field]
        for field in DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS
        if field in payload
    }
    structural_errors.extend(payload_errors)
    derived_forbidden_flags.extend(payload_derived_flags)

    evidence_references, missing_evidence_fields, unknown_evidence_references, evidence_errors = _normalize_evidence_references(
        wrapper.get("evidence_references", {}),
        parsed_response,
        deterministic_evidence_metadata,
    )
    structural_errors.extend(evidence_errors)

    combined_forbidden_flags = list(dict.fromkeys(normalized_forbidden_flags + derived_forbidden_flags))
    if structural_errors and not any(
        flag in set(DASHSCOPE_OFFLINE_CONSUMER_DECISION_POLICY_VIOLATION_FLAGS) for flag in combined_forbidden_flags
    ):
        combined_forbidden_flags.append("unsafe_extra_field")

    evidence_status = _determine_evidence_status(
        structural_errors=structural_errors,
        missing_evidence_fields=missing_evidence_fields,
        unknown_evidence_references=unknown_evidence_references,
        forbidden_content_flags=combined_forbidden_flags,
        deterministic_mismatch_flag=deterministic_mismatch_flag,
    )

    deterministic_reference_categories = sorted(
        {
            reference
            for references in evidence_references.values()
            for reference in references
        }
    )

    if not structural_errors:
        grounding_status = "grounded" if evidence_status == "grounded" else "ungrounded"
        consumer_reason = _build_evidence_reason(
            evidence_status,
            missing_evidence_fields,
            unknown_evidence_references,
            combined_forbidden_flags,
        )
        consumer_example = {
            "example_name": "parsed_simulated_response",
            "grounding_status": grounding_status,
            "expected_consumer_action": "accept" if evidence_status == "grounded" else "reject",
            "response_fields_present": [
                field for field in DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS if field in parsed_response
            ],
            "evidence_references": evidence_references,
            "invalid_evidence_references": unknown_evidence_references,
            "forbidden_or_unexpected_fields": combined_forbidden_flags,
            "consumer_reason": consumer_reason,
        }
        sanitize_dashscope_response_consumer_examples([consumer_example])

    evidence_validation_result = {
        "status": evidence_status,
        "grounding_status": "grounded" if evidence_status == "grounded" else "ungrounded",
        "expected_consumer_action": "accept" if evidence_status == "grounded" else "reject",
        "missing_evidence_fields": list(missing_evidence_fields),
        "unknown_evidence_references": list(unknown_evidence_references),
        "deterministic_reference_categories": list(deterministic_reference_categories),
        "forbidden_content_flags": list(combined_forbidden_flags),
    }

    confidence_state = parsed_response.get("confidence", "missing")
    required_human_review_flag = bool(parsed_response.get("required_human_review", True))
    blocked_actions = list(parsed_response.get("blocked_actions", [])) if isinstance(parsed_response.get("blocked_actions"), list) else []
    blocked_actions_present = bool(blocked_actions)

    decision_inputs = {
        "evidence_validation_result": (
            evidence_status
            if evidence_status in DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_EVIDENCE_VALIDATION_RESULTS
            else "policy-violation"
        ),
        "missing_evidence_fields": list(missing_evidence_fields),
        "unknown_evidence_references": list(unknown_evidence_references),
        "forbidden_content_flags": list(combined_forbidden_flags),
        "source_of_truth_override_flag": "source_of_truth_override" in combined_forbidden_flags,
        "migration_write_authorization_flag": "migration_write_instructions" in combined_forbidden_flags,
        "ready_to_migrate_claim_flag": "ready_to_migrate_without_deterministic_gates" in combined_forbidden_flags,
        "confidence_state": (
            confidence_state
            if confidence_state in DASHSCOPE_OFFLINE_CONSUMER_DECISION_ALLOWED_CONFIDENCE_STATES
            else "missing"
        ),
        "required_human_review_flag": required_human_review_flag,
        "blocked_actions_present": blocked_actions_present,
        "deterministic_reference_categories": list(deterministic_reference_categories),
        "model_policy_status": _assert_string("response shape model_policy_status", response_shape_payload["model_policy_status"]),
        "deterministic_mismatch_flag": deterministic_mismatch_flag,
    }

    decision_state, requires_human_review, requires_deterministic_recheck = governed_consumer_decision_state(
        decision_inputs
    )
    decision_reason = _build_evidence_reason(
        evidence_status,
        missing_evidence_fields,
        unknown_evidence_references,
        combined_forbidden_flags,
    )
    if decision_state == "accept_explanatory_only":
        decision_reason = (
            "Accept only as explanatory output because the simulated response stays grounded in deterministic Hermes "
            "evidence and does not override governed source-of-truth rules."
        )
    elif decision_state == "blocked_by_missing_evidence":
        decision_reason = "Block because governed response fields are missing deterministic evidence references."
    elif decision_state == "requires_deterministic_recheck":
        decision_reason = "Require deterministic recheck because evidence references or confidence remain unresolved."
    elif decision_state == "escalate_human_review":
        decision_reason = "Require human review because governed confidence, model-policy, or deterministic-mismatch rules were triggered."
    elif decision_state == "blocked_by_policy_violation":
        decision_reason = "Block because the simulated response violates the governed response contract."
    elif decision_state == "reject_unsafe":
        decision_reason = "Reject because forbidden content or unauthorized claims were detected in the simulated response."

    decision_example = {
        "example_name": "parsed_simulated_response",
        "decision_inputs": decision_inputs,
        "expected_decision_state": decision_state,
        "requires_human_review": requires_human_review,
        "requires_deterministic_recheck": requires_deterministic_recheck,
        "decision_reason": decision_reason,
    }
    sanitize_dashscope_consumer_decision_examples([decision_example])

    escalation_fields = governed_escalation_fields(decision_state, decision_inputs, decision_reason)
    escalation_example = {
        "example_name": "parsed_simulated_response",
        "decision_inputs": decision_inputs,
        "decision_state": decision_state,
        "acceptance_threshold_category": governed_acceptance_threshold_category(decision_state),
        "accepted_explanatory_only": decision_state == "accept_explanatory_only",
        "escalation_fields": escalation_fields,
        "example_reason": decision_reason,
    }
    sanitize_dashscope_escalation_examples([decision_example], [escalation_example])

    validation_result = _derive_validation_result(decision_state, structural_errors)
    errors, warnings = _derive_parser_messages(
        validation_result,
        decision_state,
        structural_errors=structural_errors,
        missing_evidence_fields=missing_evidence_fields,
        unknown_evidence_references=unknown_evidence_references,
        forbidden_content_flags=combined_forbidden_flags,
        decision_reason=decision_reason,
    )

    return DashScopeOfflineResponseParserResult(
        parser_policy_version=DASHSCOPE_OFFLINE_RESPONSE_PARSER_POLICY_VERSION,
        parser_type=DASHSCOPE_OFFLINE_RESPONSE_PARSER_TYPE,
        source=DASHSCOPE_OFFLINE_RESPONSE_PARSER_SOURCE,
        mode=DASHSCOPE_OFFLINE_RESPONSE_PARSER_MODE,
        intended_model=DASHSCOPE_INTENDED_MODEL,
        selected_model=_assert_string("response shape selected_model", response_shape_payload["selected_model"]),
        model_policy_status=_assert_string("response shape model_policy_status", response_shape_payload["model_policy_status"]),
        model_policy_ready=_assert_bool("response shape model_policy_ready", response_shape_payload["model_policy_ready"]),
        model_policy_requires_update=_assert_bool(
            "response shape model_policy_requires_update",
            response_shape_payload["model_policy_requires_update"],
        ),
        local_config_ready=_assert_bool("response shape local_config_ready", response_shape_payload["local_config_ready"]),
        input_kind=DASHSCOPE_OFFLINE_RESPONSE_PARSER_INPUT_KIND,
        runtime_enabled=False,
        network_calls_allowed=False,
        qwen_dashscope_enabled=False,
        graphify_enabled=False,
        migration_writes_enabled=False,
        report_writing_enabled=False,
        response_explanatory_only=True,
        live_response_parsing_enabled=False,
        response_shape_version=_assert_string(
            "response shape response_shape_version",
            response_shape_payload["response_shape_version"],
        ),
        response_consumer_policy_version=_assert_string(
            "response-consumer response_consumer_policy_version",
            response_consumer_payload["response_consumer_policy_version"],
        ),
        consumer_decision_policy_version=_assert_string(
            "consumer-decision consumer_decision_policy_version",
            consumer_decision_payload["consumer_decision_policy_version"],
        ),
        escalation_policy_version=_assert_string(
            "escalation escalation_policy_version",
            escalation_payload["escalation_policy_version"],
        ),
        parsed_response=parsed_response,
        validation_result=validation_result,
        evidence_validation_result=evidence_validation_result,
        consumer_decision={
            "decision_state": decision_state,
            "requires_human_review": requires_human_review,
            "requires_deterministic_recheck": requires_deterministic_recheck,
            "decision_reason": decision_reason,
            "decision_inputs": decision_inputs,
        },
        escalation_summary={
            "acceptance_threshold_category": escalation_example["acceptance_threshold_category"],
            "accepted_explanatory_only": escalation_example["accepted_explanatory_only"],
            "escalation_fields": escalation_fields,
        },
        errors=tuple(errors),
        warnings=tuple(warnings),
        source_of_truth_policy=DASHSCOPE_OFFLINE_ESCALATION_SOURCE_OF_TRUTH_POLICY,
        redaction_policy=(
            "Exclude API-key values, .env values, raw secrets, secret fragments, target-repo file contents, source "
            f"code, and live model text from parser output while keeping {DASHSCOPE_INTENDED_MODEL} explicit as "
            "non-secret intended model metadata."
        ),
        input_summary=_assert_json_object("response shape input_summary", response_shape_payload["input_summary"]),
    )
