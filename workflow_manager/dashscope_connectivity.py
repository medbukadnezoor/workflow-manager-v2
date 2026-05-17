from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import socket
import ssl
from typing import Union
from urllib import error as urllib_error
from urllib import request as urllib_request

from workflow_manager.dashscope_env import (
    DASHSCOPE_ACTIVE_ENV_KEYS,
    DASHSCOPE_INTENDED_MODEL,
    _parse_env_assignments,
)


DASHSCOPE_CONNECTIVITY_POLICY_VERSION = "1.0.0"
DASHSCOPE_CONNECTIVITY_PROBE_TYPE = "dashscope_connectivity_probe"
DASHSCOPE_CONNECTIVITY_SOURCE = "dashscope_local_readiness"
DASHSCOPE_CONNECTIVITY_MODE = "explicit_opt_in_no_content_probe"
DASHSCOPE_CONNECTIVITY_PROBE_ENDPOINT_LABEL = "dashscope_models_list"
DASHSCOPE_CONNECTIVITY_PROBE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/models"
DASHSCOPE_CONNECTIVITY_REQUEST_METHOD = "GET"
DASHSCOPE_CONNECTIVITY_REQUEST_BODY_KIND = "none"
DASHSCOPE_CONNECTIVITY_DEFAULT_TIMEOUT_SECONDS = 5.0
DASHSCOPE_CONNECTIVITY_ALLOWED_FIELDS = (
    "connectivity_policy_version",
    "probe_type",
    "source",
    "mode",
    "probe_requested",
    "network_attempted",
    "local_config_ready",
    "selected_api_key_name",
    "selected_api_key_category",
    "intended_model",
    "selected_model",
    "model_policy_status",
    "model_policy_ready",
    "model_policy_requires_update",
    "probe_endpoint_label",
    "request_method",
    "request_body_kind",
    "request_body_bytes_length",
    "project_content_sent",
    "inventory_content_sent",
    "prompt_preview_content_sent",
    "target_repo_content_sent",
    "connectivity_status",
    "sanitized_error_category",
    "http_status_category",
    "qwen_analysis_enabled",
    "runtime_enabled",
    "report_writing_enabled",
    "health_surface_integration_enabled",
    "authorization_header_logged",
    "raw_request_headers_logged",
    "raw_response_body_logged",
    "redaction_policy",
)
DASHSCOPE_CONNECTIVITY_ALLOWED_STATUSES = (
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
DASHSCOPE_CONNECTIVITY_ALLOWED_HTTP_STATUS_CATEGORIES = (
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
DASHSCOPE_CONNECTIVITY_ALLOWED_ERROR_CATEGORIES = (
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
_READINESS_REQUIRED_KEYS = (
    "env_path",
    "local_config_ready",
    "selected_api_key_name",
    "selected_api_key_category",
    "intended_model_name",
    "selected_model_name",
    "model_policy_status",
    "model_policy_ready",
    "model_policy_requires_update",
)
_CONNECTIVITY_OK_MODEL_STATUSES = ("default", "explicit-match", "fallback-match")


def _assert_bool(label: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be a boolean.")
    return value


def _assert_string(label: str, value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string.")
    return value


def _assert_optional_string(label: str, value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string or null.")
    return value


def _assert_float(label: str, value: object) -> float:
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"{label} must be a positive number.")
    return float(value)


def _normalize_readiness(readiness: dict[str, object] | object) -> dict[str, object]:
    payload = readiness.to_safe_dict() if hasattr(readiness, "to_safe_dict") else dict(readiness)
    missing = [key for key in _READINESS_REQUIRED_KEYS if key not in payload]
    if missing:
        raise ValueError(f"DashScope connectivity probe readiness payload is missing required keys: {missing}.")
    if _assert_string("readiness intended_model_name", payload["intended_model_name"]) != DASHSCOPE_INTENDED_MODEL:
        raise ValueError("DashScope connectivity probe requires the governed intended model.")
    return payload


def _categorize_http_status(http_status: int | None) -> str:
    if http_status is None:
        return "not-attempted"
    if 200 <= http_status <= 299:
        return "2xx"
    if http_status == 401:
        return "401"
    if http_status == 403:
        return "403"
    if http_status == 404:
        return "404"
    if http_status == 429:
        return "429"
    if 400 <= http_status <= 499:
        return "4xx"
    if 500 <= http_status <= 599:
        return "5xx"
    return "other"


def _sanitize_transport_exception(error: BaseException) -> str:
    if isinstance(error, (socket.timeout, TimeoutError)):
        return "timeout"
    if isinstance(error, ssl.SSLError):
        return "ssl-error"
    if isinstance(error, socket.gaierror):
        return "dns-error"
    if isinstance(error, ConnectionError):
        return "connection-error"
    if isinstance(error, OSError):
        return "connection-error"
    return "unexpected-transport-error"


def _sanitize_http_error_category(http_status: int | None) -> str:
    category = _categorize_http_status(http_status)
    if category == "401":
        return "http-401"
    if category == "403":
        return "http-403"
    if category == "404":
        return "http-404"
    if category == "429":
        return "http-429"
    if category == "4xx":
        return "http-4xx"
    if category == "5xx":
        return "http-5xx"
    return "none"


def _derive_connectivity_status(http_status: int | None, sanitized_error_category: str) -> str:
    if sanitized_error_category in {"missing-api-key", "local-config-not-ready"}:
        return "not-configured"
    if sanitized_error_category == "model-policy-mismatch":
        return "model-policy-mismatch"
    if sanitized_error_category in {"timeout", "connection-error", "dns-error", "ssl-error"}:
        return "network-error"
    if sanitized_error_category == "unexpected-transport-error":
        return "transport-error"
    http_category = _categorize_http_status(http_status)
    if http_category == "2xx":
        return "reachable"
    if http_category in {"401", "403"}:
        return "auth-error"
    if http_category == "429":
        return "throttled"
    if http_category == "5xx":
        return "service-error"
    if http_category in {"404", "4xx", "other"}:
        return "http-error"
    return "transport-error"


@dataclass(frozen=True)
class DashScopeConnectivityProbeRequest:
    probe_endpoint_label: str
    url: str
    request_method: str
    request_body_kind: str
    request_body_bytes_length: int
    timeout_seconds: float
    intended_model: str
    selected_model: str
    project_content_sent: bool
    inventory_content_sent: bool
    prompt_preview_content_sent: bool
    target_repo_content_sent: bool
    qwen_analysis_enabled: bool

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "probe_endpoint_label": self.probe_endpoint_label,
            "url": self.url,
            "request_method": self.request_method,
            "request_body_kind": self.request_body_kind,
            "request_body_bytes_length": self.request_body_bytes_length,
            "timeout_seconds": self.timeout_seconds,
            "intended_model": self.intended_model,
            "selected_model": self.selected_model,
            "project_content_sent": self.project_content_sent,
            "inventory_content_sent": self.inventory_content_sent,
            "prompt_preview_content_sent": self.prompt_preview_content_sent,
            "target_repo_content_sent": self.target_repo_content_sent,
            "qwen_analysis_enabled": self.qwen_analysis_enabled,
        }


@dataclass(frozen=True)
class DashScopeConnectivityTransportResult:
    http_status: int | None
    error_category: str | None = None

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "http_status": self.http_status,
            "error_category": self.error_category,
        }


@dataclass(frozen=True)
class DashScopeConnectivityProbeResult:
    connectivity_policy_version: str
    probe_type: str
    source: str
    mode: str
    probe_requested: bool
    network_attempted: bool
    local_config_ready: bool
    selected_api_key_name: str | None
    selected_api_key_category: str | None
    intended_model: str
    selected_model: str
    model_policy_status: str
    model_policy_ready: bool
    model_policy_requires_update: bool
    probe_endpoint_label: str
    request_method: str
    request_body_kind: str
    request_body_bytes_length: int
    project_content_sent: bool
    inventory_content_sent: bool
    prompt_preview_content_sent: bool
    target_repo_content_sent: bool
    connectivity_status: str
    sanitized_error_category: str
    http_status_category: str
    qwen_analysis_enabled: bool
    runtime_enabled: bool
    report_writing_enabled: bool
    health_surface_integration_enabled: bool
    authorization_header_logged: bool
    raw_request_headers_logged: bool
    raw_response_body_logged: bool
    redaction_policy: str

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "connectivity_policy_version": self.connectivity_policy_version,
            "probe_type": self.probe_type,
            "source": self.source,
            "mode": self.mode,
            "probe_requested": self.probe_requested,
            "network_attempted": self.network_attempted,
            "local_config_ready": self.local_config_ready,
            "selected_api_key_name": self.selected_api_key_name,
            "selected_api_key_category": self.selected_api_key_category,
            "intended_model": self.intended_model,
            "selected_model": self.selected_model,
            "model_policy_status": self.model_policy_status,
            "model_policy_ready": self.model_policy_ready,
            "model_policy_requires_update": self.model_policy_requires_update,
            "probe_endpoint_label": self.probe_endpoint_label,
            "request_method": self.request_method,
            "request_body_kind": self.request_body_kind,
            "request_body_bytes_length": self.request_body_bytes_length,
            "project_content_sent": self.project_content_sent,
            "inventory_content_sent": self.inventory_content_sent,
            "prompt_preview_content_sent": self.prompt_preview_content_sent,
            "target_repo_content_sent": self.target_repo_content_sent,
            "connectivity_status": self.connectivity_status,
            "sanitized_error_category": self.sanitized_error_category,
            "http_status_category": self.http_status_category,
            "qwen_analysis_enabled": self.qwen_analysis_enabled,
            "runtime_enabled": self.runtime_enabled,
            "report_writing_enabled": self.report_writing_enabled,
            "health_surface_integration_enabled": self.health_surface_integration_enabled,
            "authorization_header_logged": self.authorization_header_logged,
            "raw_request_headers_logged": self.raw_request_headers_logged,
            "raw_response_body_logged": self.raw_response_body_logged,
            "redaction_policy": self.redaction_policy,
        }


DashScopeConnectivityTransport = Callable[
    [DashScopeConnectivityProbeRequest, Path, str],
    Union[DashScopeConnectivityTransportResult, dict[str, object]],
]


def _normalize_transport_result(result: DashScopeConnectivityTransportResult | dict[str, object] | object) -> DashScopeConnectivityTransportResult:
    payload = result.to_safe_dict() if hasattr(result, "to_safe_dict") else dict(result)
    actual = set(payload.keys())
    expected = {"http_status", "error_category"}
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        parts = ["DashScope connectivity probe transport result keys drifted."]
        if missing:
            parts.append(f"Missing keys: {missing}.")
        if unexpected:
            parts.append(f"Unexpected keys: {unexpected}.")
        raise ValueError(" ".join(parts))

    http_status = payload["http_status"]
    if http_status is not None and (not isinstance(http_status, int) or http_status < 100):
        raise ValueError("DashScope connectivity probe transport http_status must be null or an HTTP status code.")
    error_category = _assert_optional_string("transport error_category", payload["error_category"])
    if error_category is not None and error_category not in DASHSCOPE_CONNECTIVITY_ALLOWED_ERROR_CATEGORIES:
        raise ValueError(f"DashScope connectivity probe transport error_category `{error_category}` is not supported.")
    return DashScopeConnectivityTransportResult(http_status=http_status, error_category=error_category)


def _build_probe_request(selected_model: str, *, timeout_seconds: float) -> DashScopeConnectivityProbeRequest:
    return DashScopeConnectivityProbeRequest(
        probe_endpoint_label=DASHSCOPE_CONNECTIVITY_PROBE_ENDPOINT_LABEL,
        url=DASHSCOPE_CONNECTIVITY_PROBE_URL,
        request_method=DASHSCOPE_CONNECTIVITY_REQUEST_METHOD,
        request_body_kind=DASHSCOPE_CONNECTIVITY_REQUEST_BODY_KIND,
        request_body_bytes_length=0,
        timeout_seconds=timeout_seconds,
        intended_model=DASHSCOPE_INTENDED_MODEL,
        selected_model=selected_model,
        project_content_sent=False,
        inventory_content_sent=False,
        prompt_preview_content_sent=False,
        target_repo_content_sent=False,
        qwen_analysis_enabled=False,
    )


def dashscope_connectivity_default_transport(
    request: DashScopeConnectivityProbeRequest,
    env_path: Path,
    selected_api_key_name: str,
) -> DashScopeConnectivityTransportResult:
    assignments = _parse_env_assignments(env_path)
    api_key = assignments.get(selected_api_key_name, "").strip()
    if not api_key:
        raise ValueError("DashScope connectivity probe requires a non-empty selected API key.")

    http_request = urllib_request.Request(
        request.url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "workflow-manager-connectivity-probe/1.0",
        },
        method=request.request_method,
    )
    try:
        with urllib_request.urlopen(http_request, timeout=request.timeout_seconds) as response:
            return DashScopeConnectivityTransportResult(http_status=response.getcode())
    except urllib_error.HTTPError as error:
        return DashScopeConnectivityTransportResult(http_status=error.code)


def probe_dashscope_connectivity(
    readiness: dict[str, object] | object,
    *,
    probe_requested: bool = False,
    timeout_seconds: float = DASHSCOPE_CONNECTIVITY_DEFAULT_TIMEOUT_SECONDS,
    transport: DashScopeConnectivityTransport | None = None,
) -> DashScopeConnectivityProbeResult:
    readiness_payload = _normalize_readiness(readiness)
    timeout_seconds = _assert_float("DashScope connectivity timeout_seconds", timeout_seconds)
    env_path = Path(_assert_string("readiness env_path", readiness_payload["env_path"]))
    local_config_ready = _assert_bool("readiness local_config_ready", readiness_payload["local_config_ready"])
    selected_api_key_name = _assert_optional_string(
        "readiness selected_api_key_name",
        readiness_payload["selected_api_key_name"],
    )
    selected_api_key_category = _assert_optional_string(
        "readiness selected_api_key_category",
        readiness_payload["selected_api_key_category"],
    )
    selected_model = _assert_string("readiness selected_model_name", readiness_payload["selected_model_name"])
    model_policy_status = _assert_string("readiness model_policy_status", readiness_payload["model_policy_status"])
    model_policy_ready = _assert_bool("readiness model_policy_ready", readiness_payload["model_policy_ready"])
    model_policy_requires_update = _assert_bool(
        "readiness model_policy_requires_update",
        readiness_payload["model_policy_requires_update"],
    )
    probe_request = _build_probe_request(selected_model, timeout_seconds=timeout_seconds)

    network_attempted = False
    http_status: int | None = None
    sanitized_error_category = "none"
    connectivity_status = "not-requested"

    if probe_requested:
        if selected_api_key_name not in DASHSCOPE_ACTIVE_ENV_KEYS:
            sanitized_error_category = "missing-api-key"
            connectivity_status = "not-configured"
        elif not local_config_ready:
            sanitized_error_category = "local-config-not-ready"
            connectivity_status = "not-configured"
        elif model_policy_status not in _CONNECTIVITY_OK_MODEL_STATUSES or model_policy_requires_update or not model_policy_ready:
            sanitized_error_category = "model-policy-mismatch"
            connectivity_status = "model-policy-mismatch"
        else:
            network_attempted = True
            chosen_transport = transport or dashscope_connectivity_default_transport
            try:
                transport_result = _normalize_transport_result(
                    chosen_transport(probe_request, env_path, selected_api_key_name)
                )
                http_status = transport_result.http_status
                sanitized_error_category = transport_result.error_category or _sanitize_http_error_category(http_status)
            except BaseException as error:
                sanitized_error_category = _sanitize_transport_exception(error)
            connectivity_status = _derive_connectivity_status(http_status, sanitized_error_category)

    return DashScopeConnectivityProbeResult(
        connectivity_policy_version=DASHSCOPE_CONNECTIVITY_POLICY_VERSION,
        probe_type=DASHSCOPE_CONNECTIVITY_PROBE_TYPE,
        source=DASHSCOPE_CONNECTIVITY_SOURCE,
        mode=DASHSCOPE_CONNECTIVITY_MODE,
        probe_requested=probe_requested,
        network_attempted=network_attempted,
        local_config_ready=local_config_ready,
        selected_api_key_name=selected_api_key_name,
        selected_api_key_category=selected_api_key_category,
        intended_model=DASHSCOPE_INTENDED_MODEL,
        selected_model=selected_model,
        model_policy_status=model_policy_status,
        model_policy_ready=model_policy_ready,
        model_policy_requires_update=model_policy_requires_update,
        probe_endpoint_label=probe_request.probe_endpoint_label,
        request_method=probe_request.request_method,
        request_body_kind=probe_request.request_body_kind,
        request_body_bytes_length=probe_request.request_body_bytes_length,
        project_content_sent=probe_request.project_content_sent,
        inventory_content_sent=probe_request.inventory_content_sent,
        prompt_preview_content_sent=probe_request.prompt_preview_content_sent,
        target_repo_content_sent=probe_request.target_repo_content_sent,
        connectivity_status=connectivity_status,
        sanitized_error_category=sanitized_error_category,
        http_status_category=_categorize_http_status(http_status),
        qwen_analysis_enabled=probe_request.qwen_analysis_enabled,
        runtime_enabled=False,
        report_writing_enabled=False,
        health_surface_integration_enabled=False,
        authorization_header_logged=False,
        raw_request_headers_logged=False,
        raw_response_body_logged=False,
        redaction_policy=(
            "Exclude API-key values, partial secret fragments, Authorization headers, raw request headers, raw "
            "response bodies, project content, Hermes inventory content, prompt preview content, target-repo "
            "content, and hidden reasoning from connectivity-probe output while keeping qwen3.6-plus explicit as "
            "non-secret intended model metadata."
        ),
    )
