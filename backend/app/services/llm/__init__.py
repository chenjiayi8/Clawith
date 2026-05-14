"""LLM service module - unified LLM calling interface.

This package intentionally resolves its public exports lazily so leaf modules
like ``app.services.llm.finish`` can be imported without triggering ``caller``
and recreating import cycles with ``app.services.agent_tools``.
"""

from __future__ import annotations

from importlib import import_module

_EXPORTS: dict[str, tuple[str, str | None]] = {
    # Caller module / functions
    "caller": (".caller", None),
    "call_llm": (".caller", "call_llm"),
    "call_llm_with_failover": (".caller", "call_llm_with_failover"),
    "call_agent_llm": (".caller", "call_agent_llm"),
    "call_agent_llm_with_tools": (".caller", "call_agent_llm_with_tools"),
    "FailoverGuard": (".caller", "FailoverGuard"),
    "is_retryable_error": (".caller", "is_retryable_error"),
    # Client classes
    "LLMClient": (".client", "LLMClient"),
    "LLMResponse": (".client", "LLMResponse"),
    "LLMError": (".client", "LLMError"),
    "LLMMessage": (".client", "LLMMessage"),
    # Failover utilities
    "classify_error": (".failover", "classify_error"),
    "FailoverErrorType": (".failover", "FailoverErrorType"),
    # Shared helpers
    "create_llm_client": (".utils", "create_llm_client"),
    "get_max_tokens": (".utils", "get_max_tokens"),
    "get_model_api_key": (".utils", "get_model_api_key"),
    "get_provider_base_url": (".utils", "get_provider_base_url"),
    "get_provider_manifest": (".utils", "get_provider_manifest"),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    try:
        module_name, attr_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    module = import_module(module_name, __name__)
    value = module if attr_name is None else getattr(module, attr_name)
    globals()[name] = value
    return value
