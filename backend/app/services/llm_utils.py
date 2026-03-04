"""Shared LLM provider configuration and utilities.

Centralizes provider URLs and provider-specific API parameters
so they don't need to be duplicated across websocket.py, scheduler.py,
task_executor.py, agent_tools.py, and feishu.py.
"""

# Default base URLs for each known provider.
# If a model has a custom base_url in DB, that takes precedence.
PROVIDER_URLS: dict[str, str | None] = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "zhipu": "https://open.bigmodel.cn/api/paas/v4",
    "openrouter": "https://openrouter.ai/api/v1",
    "custom": None,
}

# Providers that support OpenAI-compatible tool_choice and parallel_tool_calls
_TOOL_CHOICE_PROVIDERS = {"openai", "qwen", "deepseek", "zhipu", "openrouter", "custom"}


def get_provider_base_url(provider: str, custom_base_url: str | None = None) -> str | None:
    """Return the API base URL for a provider.

    If the model has a custom base_url configured, that takes precedence.
    Otherwise falls back to the default URL for the provider.
    """
    if custom_base_url:
        return custom_base_url
    return PROVIDER_URLS.get(provider, "https://api.openai.com/v1")


def get_tool_params(provider: str) -> dict:
    """Return provider-specific tool calling parameters.

    Qwen and OpenAI support `tool_choice` and `parallel_tool_calls`.
    Anthropic uses a different tool calling format, so we skip these params.
    """
    if provider in _TOOL_CHOICE_PROVIDERS:
        return {
            "tool_choice": "auto",
            "parallel_tool_calls": True,
        }
    return {}


# Per-provider / per-model max_tokens limits.
# Qwen models: qwen-max is limited to 8192; qwen-long/qwen-plus can do more.
_MAX_TOKENS_BY_PROVIDER: dict[str, int] = {
    "qwen": 8192,       # conservative default; qwen-max hard limit
    "anthropic": 4096,  # claude native max output
}
# Model-level overrides (model string prefix → limit)
_MAX_TOKENS_BY_MODEL: dict[str, int] = {
    "qwen-plus": 16384,
    "qwen-long": 16384,
    "qwen-turbo": 8192,
    "qwen-max": 8192,
}


def get_max_tokens(provider: str, model: str | None = None) -> int:
    """Return a safe max_tokens value for the given provider/model pair.

    Prevents 400 errors from providers that have strict upper limits
    (e.g. qwen-max rejects anything above 8192).
    """
    # Check model-level override first
    if model:
        for prefix, limit in _MAX_TOKENS_BY_MODEL.items():
            if model.lower().startswith(prefix):
                return limit
    # Fall back to provider-level default, otherwise use 16384
    return _MAX_TOKENS_BY_PROVIDER.get(provider, 16384)

