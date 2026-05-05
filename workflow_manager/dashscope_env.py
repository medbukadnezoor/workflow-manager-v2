from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DASHSCOPE_ACTIVE_ENV_KEYS = ("DASHSCOPE_API_KEY_WORKFLOW_MANAGER",)
DASHSCOPE_FALLBACK_ONLY_ENV_KEYS = ("DASHSCOPE_API_KEY",)
DASHSCOPE_OPTIONAL_MODEL_ENV_KEYS = ("QWEN_MODEL",)
DASHSCOPE_FALLBACK_MODEL_ENV_KEYS = ("DASHSCOPE_MODEL",)
DASHSCOPE_RESERVED_ENV_KEYS = ("DASHSCOPE_BASE_URL", "DASHSCOPE_REGION")
DASHSCOPE_IGNORED_ENV_KEYS: tuple[str, ...] = ()
DASHSCOPE_DISALLOWED_ENV_KEYS: tuple[str, ...] = ()
DASHSCOPE_MODEL_ENV_KEYS = DASHSCOPE_OPTIONAL_MODEL_ENV_KEYS + DASHSCOPE_FALLBACK_MODEL_ENV_KEYS
DASHSCOPE_LOCAL_ENV_KEYS = (
    DASHSCOPE_ACTIVE_ENV_KEYS
    + DASHSCOPE_FALLBACK_ONLY_ENV_KEYS
    + DASHSCOPE_MODEL_ENV_KEYS
    + DASHSCOPE_RESERVED_ENV_KEYS
)
DASHSCOPE_PRECEDENCE_POLICY = "workflow-manager-specific-over-generic"
DASHSCOPE_GENERIC_API_KEY_POLICY = "fallback-only"
DASHSCOPE_INTENDED_MODEL = "qwen3.6-plus"
DASHSCOPE_MODEL_PRECEDENCE_POLICY = "QWEN_MODEL-over-DASHSCOPE_MODEL-over-policy-default"
DASHSCOPE_MODEL_SELECTION_POLICY = "qwen3.6-plus-default-with-governed-model-env-override"
DASHSCOPE_ENV_KEY_CATEGORIES = {
    **{key: "active" for key in DASHSCOPE_ACTIVE_ENV_KEYS},
    **{key: "fallback-only" for key in DASHSCOPE_FALLBACK_ONLY_ENV_KEYS},
    **{key: "optional" for key in DASHSCOPE_OPTIONAL_MODEL_ENV_KEYS},
    **{key: "fallback-only" for key in DASHSCOPE_FALLBACK_MODEL_ENV_KEYS},
    **{key: "reserved" for key in DASHSCOPE_RESERVED_ENV_KEYS},
}
DASHSCOPE_REDACTED_VALUE = "<redacted>"


def _parse_env_assignments(env_path: Path) -> dict[str, str]:
    assignments: dict[str, str] = {}
    if not env_path.exists():
        return assignments

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        assignments[key.strip()] = value.strip()
    return assignments


@dataclass(frozen=True)
class DashScopeLocalReadiness:
    env_path: Path
    env_exists: bool
    expected_variable_names: tuple[str, ...]
    active_variable_names: tuple[str, ...]
    fallback_only_variable_names: tuple[str, ...]
    optional_model_variable_names: tuple[str, ...]
    fallback_model_variable_names: tuple[str, ...]
    reserved_variable_names: tuple[str, ...]
    ignored_variable_names: tuple[str, ...]
    disallowed_variable_names: tuple[str, ...]
    present_variable_names: tuple[str, ...]
    missing_variable_names: tuple[str, ...]
    present_model_variable_names: tuple[str, ...]
    missing_model_variable_names: tuple[str, ...]
    variable_categories: dict[str, str]
    non_empty_flags: dict[str, bool]
    selected_api_key_name: str | None
    selected_api_key_category: str | None
    precedence_policy: str
    generic_api_key_policy: str
    intended_model_name: str
    selected_model_name: str | None
    selected_model_variable_name: str | None
    selected_model_variable_category: str | None
    model_precedence_policy: str
    model_selection_policy: str
    model_policy_status: str
    model_policy_ready: bool
    model_policy_requires_update: bool
    redacted_values: dict[str, str]
    all_values_redacted: bool
    local_config_ready: bool
    runtime_enabled: bool
    network_calls_allowed: bool

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "env_path": str(self.env_path),
            "env_exists": self.env_exists,
            "expected_variable_names": list(self.expected_variable_names),
            "active_variable_names": list(self.active_variable_names),
            "fallback_only_variable_names": list(self.fallback_only_variable_names),
            "optional_model_variable_names": list(self.optional_model_variable_names),
            "fallback_model_variable_names": list(self.fallback_model_variable_names),
            "reserved_variable_names": list(self.reserved_variable_names),
            "ignored_variable_names": list(self.ignored_variable_names),
            "disallowed_variable_names": list(self.disallowed_variable_names),
            "present_variable_names": list(self.present_variable_names),
            "missing_variable_names": list(self.missing_variable_names),
            "present_model_variable_names": list(self.present_model_variable_names),
            "missing_model_variable_names": list(self.missing_model_variable_names),
            "variable_categories": dict(self.variable_categories),
            "non_empty_flags": dict(self.non_empty_flags),
            "selected_api_key_name": self.selected_api_key_name,
            "selected_api_key_category": self.selected_api_key_category,
            "precedence_policy": self.precedence_policy,
            "generic_api_key_policy": self.generic_api_key_policy,
            "intended_model_name": self.intended_model_name,
            "selected_model_name": self.selected_model_name,
            "selected_model_variable_name": self.selected_model_variable_name,
            "selected_model_variable_category": self.selected_model_variable_category,
            "model_precedence_policy": self.model_precedence_policy,
            "model_selection_policy": self.model_selection_policy,
            "model_policy_status": self.model_policy_status,
            "model_policy_ready": self.model_policy_ready,
            "model_policy_requires_update": self.model_policy_requires_update,
            "redacted_values": dict(self.redacted_values),
            "all_values_redacted": self.all_values_redacted,
            "local_config_ready": self.local_config_ready,
            "runtime_enabled": self.runtime_enabled,
            "network_calls_allowed": self.network_calls_allowed,
        }


def _select_dashscope_api_key(assignments: dict[str, str]) -> tuple[str | None, str | None]:
    for key in DASHSCOPE_ACTIVE_ENV_KEYS:
        if key in assignments:
            return key, DASHSCOPE_ENV_KEY_CATEGORIES[key]
    for key in DASHSCOPE_FALLBACK_ONLY_ENV_KEYS:
        if key in assignments:
            return key, DASHSCOPE_ENV_KEY_CATEGORIES[key]
    return None, None


def _select_dashscope_model(
    assignments: dict[str, str],
) -> tuple[str | None, str | None, str | None, str, bool, bool]:
    for key in DASHSCOPE_OPTIONAL_MODEL_ENV_KEYS:
        if key in assignments:
            value = assignments[key].strip() or None
            if value == DASHSCOPE_INTENDED_MODEL:
                return value, key, DASHSCOPE_ENV_KEY_CATEGORIES[key], "explicit-match", True, False
            return value, key, DASHSCOPE_ENV_KEY_CATEGORIES[key], "mismatch", False, True

    for key in DASHSCOPE_FALLBACK_MODEL_ENV_KEYS:
        if key in assignments:
            value = assignments[key].strip() or None
            if value == DASHSCOPE_INTENDED_MODEL:
                return value, key, DASHSCOPE_ENV_KEY_CATEGORIES[key], "fallback-match", True, False
            return value, key, DASHSCOPE_ENV_KEY_CATEGORIES[key], "mismatch", False, True

    return DASHSCOPE_INTENDED_MODEL, None, None, "default", True, False


def inspect_dashscope_local_readiness(repo_root: Path) -> DashScopeLocalReadiness:
    env_path = repo_root / ".env"
    assignments = _parse_env_assignments(env_path)
    present_variable_names = tuple(key for key in DASHSCOPE_LOCAL_ENV_KEYS if key in assignments)
    missing_variable_names = tuple(key for key in DASHSCOPE_ACTIVE_ENV_KEYS if key not in assignments)
    present_model_variable_names = tuple(key for key in DASHSCOPE_MODEL_ENV_KEYS if key in assignments)
    missing_model_variable_names = tuple(key for key in DASHSCOPE_MODEL_ENV_KEYS if key not in assignments)
    non_empty_flags = {
        key: bool(assignments.get(key, "").strip())
        for key in DASHSCOPE_LOCAL_ENV_KEYS
    }
    variable_categories = {
        key: DASHSCOPE_ENV_KEY_CATEGORIES[key]
        for key in DASHSCOPE_LOCAL_ENV_KEYS
    }
    selected_api_key_name, selected_api_key_category = _select_dashscope_api_key(assignments)
    (
        selected_model_name,
        selected_model_variable_name,
        selected_model_variable_category,
        model_policy_status,
        model_policy_ready,
        model_policy_requires_update,
    ) = _select_dashscope_model(assignments)
    redacted_values = {
        key: DASHSCOPE_REDACTED_VALUE
        for key in present_variable_names
    }
    all_values_redacted = all(value == DASHSCOPE_REDACTED_VALUE for value in redacted_values.values())
    local_config_ready = (
        env_path.exists()
        and all(non_empty_flags[key] for key in DASHSCOPE_ACTIVE_ENV_KEYS)
    )
    return DashScopeLocalReadiness(
        env_path=env_path,
        env_exists=env_path.exists(),
        expected_variable_names=DASHSCOPE_ACTIVE_ENV_KEYS,
        active_variable_names=DASHSCOPE_ACTIVE_ENV_KEYS,
        fallback_only_variable_names=DASHSCOPE_FALLBACK_ONLY_ENV_KEYS,
        optional_model_variable_names=DASHSCOPE_OPTIONAL_MODEL_ENV_KEYS,
        fallback_model_variable_names=DASHSCOPE_FALLBACK_MODEL_ENV_KEYS,
        reserved_variable_names=DASHSCOPE_RESERVED_ENV_KEYS,
        ignored_variable_names=DASHSCOPE_IGNORED_ENV_KEYS,
        disallowed_variable_names=DASHSCOPE_DISALLOWED_ENV_KEYS,
        present_variable_names=present_variable_names,
        missing_variable_names=missing_variable_names,
        present_model_variable_names=present_model_variable_names,
        missing_model_variable_names=missing_model_variable_names,
        variable_categories=variable_categories,
        non_empty_flags=non_empty_flags,
        selected_api_key_name=selected_api_key_name,
        selected_api_key_category=selected_api_key_category,
        precedence_policy=DASHSCOPE_PRECEDENCE_POLICY,
        generic_api_key_policy=DASHSCOPE_GENERIC_API_KEY_POLICY,
        intended_model_name=DASHSCOPE_INTENDED_MODEL,
        selected_model_name=selected_model_name,
        selected_model_variable_name=selected_model_variable_name,
        selected_model_variable_category=selected_model_variable_category,
        model_precedence_policy=DASHSCOPE_MODEL_PRECEDENCE_POLICY,
        model_selection_policy=DASHSCOPE_MODEL_SELECTION_POLICY,
        model_policy_status=model_policy_status,
        model_policy_ready=model_policy_ready,
        model_policy_requires_update=model_policy_requires_update,
        redacted_values=redacted_values,
        all_values_redacted=all_values_redacted,
        local_config_ready=local_config_ready,
        runtime_enabled=False,
        network_calls_allowed=False,
    )
