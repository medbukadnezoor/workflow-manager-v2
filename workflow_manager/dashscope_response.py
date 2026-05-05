from __future__ import annotations

from dataclasses import dataclass

from workflow_manager.dashscope_env import DASHSCOPE_INTENDED_MODEL
from workflow_manager.dashscope_prompt_preview import (
    DASHSCOPE_OFFLINE_PROMPT_PREVIEW_ALLOWED_FIELDS,
    DASHSCOPE_OFFLINE_PROMPT_PREVIEW_MODE,
    DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SOURCE,
    DASHSCOPE_OFFLINE_PROMPT_PREVIEW_TYPE,
    DASHSCOPE_OFFLINE_PROMPT_PREVIEW_VERSION,
)
from workflow_manager.dashscope_request import DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS


DASHSCOPE_OFFLINE_RESPONSE_SHAPE_VERSION = "1.0.0"
DASHSCOPE_OFFLINE_RESPONSE_TYPE = "explanatory_response_shape"
DASHSCOPE_OFFLINE_RESPONSE_SOURCE = "hermes_inventory"
DASHSCOPE_OFFLINE_RESPONSE_MODE = "offline_response_shape_only"
DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_FIELDS = (
    "response_shape_version",
    "response_type",
    "source",
    "mode",
    "intended_model",
    "selected_model",
    "model_policy_status",
    "model_policy_ready",
    "model_policy_requires_update",
    "local_config_ready",
    "runtime_enabled",
    "network_calls_allowed",
    "qwen_dashscope_enabled",
    "graphify_enabled",
    "migration_writes_enabled",
    "preview_type",
    "prompt_preview_mode",
    "preview_only",
    "response_explanatory_only",
    "live_response_parsing_enabled",
    "allowed_response_fields",
    "required_response_fields",
    "response_field_order",
    "response_slots",
    "forbidden_response_fields",
    "source_of_truth_policy",
    "forbidden_output_policy",
    "redaction_policy",
    "input_summary",
)
DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS = (
    "analysis_summary",
    "risk_summary",
    "recommended_next_step",
    "blocked_actions",
    "required_human_review",
    "confidence",
    "source_of_truth_policy",
    "forbidden_output_policy",
    "redaction_policy",
)
DASHSCOPE_OFFLINE_RESPONSE_REQUIRED_RESPONSE_FIELDS = DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS
DASHSCOPE_OFFLINE_RESPONSE_FIELD_ORDER = DASHSCOPE_OFFLINE_RESPONSE_REQUIRED_RESPONSE_FIELDS
DASHSCOPE_OFFLINE_RESPONSE_FORBIDDEN_RESPONSE_FIELDS = (
    "api_key_material",
    "raw_env",
    "env_values",
    "credentials",
    "tokens",
    "hidden_reasoning",
    "chain_of_thought",
    "migration_write_instructions",
    "target_repo_modification_instructions",
    "write_commands",
    "graphify_execution_instructions",
    "source_of_truth_override",
    "project_source_code",
    "target_repo_file_contents",
    "generated_shim_contents",
    "memory_state_file_bodies",
    "full_agents_claude_gemini_contents",
)
DASHSCOPE_OFFLINE_RESPONSE_FORBIDDEN_FIELD_FRAGMENTS = (
    "api_key",
    "secret",
    "token",
    "credential",
    "hidden_reasoning",
    "chain_of_thought",
    "migration_write",
    "target_repo_modification",
    "graphify",
    "source_of_truth_override",
    "project_source_code",
    "file_contents",
    "env_values",
)
DASHSCOPE_OFFLINE_RESPONSE_FORBIDDEN_OUTPUT_POLICY = (
    "api-key values",
    ".env values",
    "raw secrets",
    "partial secret prefixes or suffixes",
    "credentials and tokens",
    "hidden reasoning or chain-of-thought",
    "target-repo modification instructions",
    "migration-write instructions",
    "write-capable shell commands",
    "Graphify execution instructions",
    "claims that Qwen output is source of truth",
    "claims that migration is ready based on analysis alone",
    "arbitrary target-repo file contents",
    "project source code",
    "generated shim contents",
    "memory or state file bodies",
    "full AGENTS/CLAUDE/GEMINI contents from target repos",
)
DASHSCOPE_OFFLINE_RESPONSE_SOURCE_OF_TRUTH_POLICY = (
    "Deterministic Hermes inventory/status/doctor JSON remains the source of truth. "
    "Any future Qwen output is explanatory only, cannot override deterministic classifications, "
    "cannot authorize migration writes, cannot mark a repo ready for migration by itself, "
    "and must surface uncertainty instead of inventing facts."
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


def _assert_non_negative_int(label: str, value: object) -> int:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer.")
    return value


def _normalize_prompt_preview(payload: DashScopeOfflineResponseShape | dict[str, object] | object) -> dict[str, object]:
    prompt_preview = payload.to_safe_dict() if hasattr(payload, "to_safe_dict") else dict(payload)
    actual_keys = set(prompt_preview.keys())
    expected_keys = set(DASHSCOPE_OFFLINE_PROMPT_PREVIEW_ALLOWED_FIELDS)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        parts = ["Offline DashScope/Qwen response shape received a drifted prompt preview."]
        if missing:
            parts.append(f"Missing keys: {missing}.")
        if unexpected:
            parts.append(f"Unexpected keys: {unexpected}.")
        raise ValueError(" ".join(parts))

    if _assert_string("prompt preview source", prompt_preview["source"]) != DASHSCOPE_OFFLINE_PROMPT_PREVIEW_SOURCE:
        raise ValueError("Offline response shape requires hermes_inventory prompt-preview input.")
    if _assert_string("prompt preview mode", prompt_preview["mode"]) != DASHSCOPE_OFFLINE_PROMPT_PREVIEW_MODE:
        raise ValueError("Offline response shape requires offline_prompt_preview_only mode.")
    if _assert_string("prompt preview version", prompt_preview["prompt_preview_version"]) != DASHSCOPE_OFFLINE_PROMPT_PREVIEW_VERSION:
        raise ValueError("Offline response shape received an unexpected prompt-preview version.")
    if _assert_string("prompt preview type", prompt_preview["preview_type"]) != DASHSCOPE_OFFLINE_PROMPT_PREVIEW_TYPE:
        raise ValueError("Offline response shape requires assembled_prompt_preview input.")
    if _assert_string("prompt preview intended_model", prompt_preview["intended_model"]) != DASHSCOPE_INTENDED_MODEL:
        raise ValueError("Offline response shape requires the governed intended model.")
    if not _assert_bool("prompt preview preview_only", prompt_preview["preview_only"]):
        raise ValueError("Offline response shape requires preview_only=true.")
    if _assert_bool("prompt preview prompt_execution_enabled", prompt_preview["prompt_execution_enabled"]):
        raise ValueError("Offline response shape requires prompt_execution_enabled=false.")
    if _assert_bool("prompt preview runtime_enabled", prompt_preview["runtime_enabled"]):
        raise ValueError("Offline response shape requires runtime_enabled=false.")
    if _assert_bool("prompt preview network_calls_allowed", prompt_preview["network_calls_allowed"]):
        raise ValueError("Offline response shape requires network_calls_allowed=false.")
    if _assert_bool("prompt preview qwen_dashscope_enabled", prompt_preview["qwen_dashscope_enabled"]):
        raise ValueError("Offline response shape requires qwen_dashscope_enabled=false.")
    if _assert_bool("prompt preview graphify_enabled", prompt_preview["graphify_enabled"]):
        raise ValueError("Offline response shape requires graphify_enabled=false.")
    if _assert_bool("prompt preview migration_writes_enabled", prompt_preview["migration_writes_enabled"]):
        raise ValueError("Offline response shape requires migration_writes_enabled=false.")

    input_summary = _assert_json_object("prompt preview input_summary", prompt_preview["input_summary"])
    if set(input_summary.keys()) != set(DASHSCOPE_OFFLINE_REQUEST_INPUT_SUMMARY_KEYS):
        raise ValueError("Offline response shape received a drifted prompt-preview input summary.")
    if _assert_string("prompt preview input_summary.source_command", input_summary["source_command"]) != DASHSCOPE_OFFLINE_RESPONSE_SOURCE:
        raise ValueError("Offline response shape requires hermes_inventory as the source command.")
    if _assert_string("prompt preview input_summary.source_mode", input_summary["source_mode"]) != "inventory":
        raise ValueError("Offline response shape requires inventory mode.")
    if not _assert_bool("prompt preview input_summary.source_dry_run", input_summary["source_dry_run"]):
        raise ValueError("Offline response shape requires dry-run prompt-preview input.")
    classification_counts = _assert_json_object(
        "prompt preview input_summary.classification_counts",
        input_summary["classification_counts"],
    )
    for key, value in classification_counts.items():
        _assert_non_negative_int(f"prompt preview input_summary.classification_counts.{key}", value)
    return prompt_preview


def sanitize_dashscope_response_slots(candidate_output: dict[str, object] | None) -> dict[str, str]:
    if not candidate_output:
        return {}

    if not isinstance(candidate_output, dict):
        raise ValueError("Offline DashScope/Qwen response slot overrides must be an object.")

    forbidden = []
    custom = []
    unexpected = []
    for key, value in candidate_output.items():
        if not isinstance(value, str):
            raise ValueError(f"Offline DashScope/Qwen response slot `{key}` must be a string.")
        key_lower = key.lower()
        if key in DASHSCOPE_OFFLINE_RESPONSE_FORBIDDEN_RESPONSE_FIELDS or any(
            fragment in key_lower for fragment in DASHSCOPE_OFFLINE_RESPONSE_FORBIDDEN_FIELD_FRAGMENTS
        ):
            forbidden.append(key)
            continue
        if key in DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS:
            custom.append(key)
            continue
        unexpected.append(key)

    if forbidden:
        raise ValueError(
            "Offline DashScope/Qwen response shape contains forbidden output fields: "
            + ", ".join(sorted(forbidden))
            + "."
        )
    if custom:
        raise ValueError(
            "Offline DashScope/Qwen response shape does not allow custom response slot content yet: "
            + ", ".join(sorted(custom))
            + "."
        )
    if unexpected:
        raise ValueError(
            "Offline DashScope/Qwen response shape does not allow extra output fields yet: "
            + ", ".join(sorted(unexpected))
            + "."
        )
    return {}


@dataclass(frozen=True)
class DashScopeOfflineResponseShape:
    response_shape_version: str
    response_type: str
    source: str
    mode: str
    intended_model: str
    selected_model: str
    model_policy_status: str
    model_policy_ready: bool
    model_policy_requires_update: bool
    local_config_ready: bool
    runtime_enabled: bool
    network_calls_allowed: bool
    qwen_dashscope_enabled: bool
    graphify_enabled: bool
    migration_writes_enabled: bool
    preview_type: str
    prompt_preview_mode: str
    preview_only: bool
    response_explanatory_only: bool
    live_response_parsing_enabled: bool
    allowed_response_fields: tuple[str, ...]
    required_response_fields: tuple[str, ...]
    response_field_order: tuple[str, ...]
    response_slots: dict[str, str]
    forbidden_response_fields: tuple[str, ...]
    source_of_truth_policy: str
    forbidden_output_policy: tuple[str, ...]
    redaction_policy: str
    input_summary: dict[str, object]

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "response_shape_version": self.response_shape_version,
            "response_type": self.response_type,
            "source": self.source,
            "mode": self.mode,
            "intended_model": self.intended_model,
            "selected_model": self.selected_model,
            "model_policy_status": self.model_policy_status,
            "model_policy_ready": self.model_policy_ready,
            "model_policy_requires_update": self.model_policy_requires_update,
            "local_config_ready": self.local_config_ready,
            "runtime_enabled": self.runtime_enabled,
            "network_calls_allowed": self.network_calls_allowed,
            "qwen_dashscope_enabled": self.qwen_dashscope_enabled,
            "graphify_enabled": self.graphify_enabled,
            "migration_writes_enabled": self.migration_writes_enabled,
            "preview_type": self.preview_type,
            "prompt_preview_mode": self.prompt_preview_mode,
            "preview_only": self.preview_only,
            "response_explanatory_only": self.response_explanatory_only,
            "live_response_parsing_enabled": self.live_response_parsing_enabled,
            "allowed_response_fields": list(self.allowed_response_fields),
            "required_response_fields": list(self.required_response_fields),
            "response_field_order": list(self.response_field_order),
            "response_slots": dict(self.response_slots),
            "forbidden_response_fields": list(self.forbidden_response_fields),
            "source_of_truth_policy": self.source_of_truth_policy,
            "forbidden_output_policy": list(self.forbidden_output_policy),
            "redaction_policy": self.redaction_policy,
            "input_summary": dict(self.input_summary),
        }


def build_hermes_qwen_offline_response_shape(
    prompt_preview: DashScopeOfflineResponseShape | dict[str, object] | object,
    *,
    candidate_output: dict[str, object] | None = None,
) -> DashScopeOfflineResponseShape:
    sanitize_dashscope_response_slots(candidate_output)

    preview_payload = _normalize_prompt_preview(prompt_preview)
    input_summary = _assert_json_object("prompt preview input_summary", preview_payload["input_summary"])
    response_slots = {
        "analysis_summary": (
            "Explain the deterministic Hermes evidence without overriding the governed classifications "
            "or inventing missing facts."
        ),
        "risk_summary": (
            "Summarize the migration and safety risks already surfaced by deterministic Hermes inventory/status/doctor data."
        ),
        "recommended_next_step": (
            "Recommend one next safe step that preserves read-only behavior and does not authorize target-repo writes."
        ),
        "blocked_actions": (
            "List actions that remain blocked, including target-repo writes, migration writes, Graphify work, "
            "network calls, and live Qwen execution."
        ),
        "required_human_review": (
            "State whether human review is required before any broader migration decision and keep that review requirement explicit."
        ),
        "confidence": (
            "Use cautious confidence grounded only in deterministic Hermes evidence and surface uncertainty instead of guessing."
        ),
        "source_of_truth_policy": DASHSCOPE_OFFLINE_RESPONSE_SOURCE_OF_TRUTH_POLICY,
        "forbidden_output_policy": (
            "Do not include secrets, env values, hidden reasoning, write instructions, target-repo file contents, "
            "or claims that analysis alone is authoritative."
        ),
        "redaction_policy": (
            f"Treat {DASHSCOPE_INTENDED_MODEL} as non-secret model metadata. Exclude API-key material, env values, "
            "credentials, tokens, file bodies, and unconstrained repo text."
        ),
    }

    return DashScopeOfflineResponseShape(
        response_shape_version=DASHSCOPE_OFFLINE_RESPONSE_SHAPE_VERSION,
        response_type=DASHSCOPE_OFFLINE_RESPONSE_TYPE,
        source=DASHSCOPE_OFFLINE_RESPONSE_SOURCE,
        mode=DASHSCOPE_OFFLINE_RESPONSE_MODE,
        intended_model=_assert_string("prompt preview intended_model", preview_payload["intended_model"]),
        selected_model=_assert_string("prompt preview selected_model", preview_payload["selected_model"]),
        model_policy_status=_assert_string("prompt preview model_policy_status", preview_payload["model_policy_status"]),
        model_policy_ready=_assert_bool("prompt preview model_policy_ready", preview_payload["model_policy_ready"]),
        model_policy_requires_update=_assert_bool(
            "prompt preview model_policy_requires_update",
            preview_payload["model_policy_requires_update"],
        ),
        local_config_ready=_assert_bool("prompt preview local_config_ready", preview_payload["local_config_ready"]),
        runtime_enabled=False,
        network_calls_allowed=False,
        qwen_dashscope_enabled=False,
        graphify_enabled=False,
        migration_writes_enabled=False,
        preview_type=_assert_string("prompt preview preview_type", preview_payload["preview_type"]),
        prompt_preview_mode=_assert_string("prompt preview mode", preview_payload["mode"]),
        preview_only=True,
        response_explanatory_only=True,
        live_response_parsing_enabled=False,
        allowed_response_fields=DASHSCOPE_OFFLINE_RESPONSE_ALLOWED_RESPONSE_FIELDS,
        required_response_fields=DASHSCOPE_OFFLINE_RESPONSE_REQUIRED_RESPONSE_FIELDS,
        response_field_order=DASHSCOPE_OFFLINE_RESPONSE_FIELD_ORDER,
        response_slots=response_slots,
        forbidden_response_fields=DASHSCOPE_OFFLINE_RESPONSE_FORBIDDEN_RESPONSE_FIELDS,
        source_of_truth_policy=DASHSCOPE_OFFLINE_RESPONSE_SOURCE_OF_TRUTH_POLICY,
        forbidden_output_policy=DASHSCOPE_OFFLINE_RESPONSE_FORBIDDEN_OUTPUT_POLICY,
        redaction_policy=response_slots["redaction_policy"],
        input_summary=input_summary,
    )
