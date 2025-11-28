"""Provider registry for interactive selection and extensibility.

This module centralizes provider metadata used by the interactive
tests and the CLI. Providers can register themselves here or the
registry can be extended with new entries.

Usage:
    from src.providers import registry
    registry.list_providers()
    registry.get_models('openrouter')
    registry.register_provider('myprov', env_key='MYPROV_KEY', models=[...])
"""
from typing import Dict, List, Optional
import os
import json
# Built-in provider specs. Keep this small and editable.
_PROVIDERS: Dict[str, Dict] = {
    "openrouter": {
        "display": "OpenRouter",
        "env_key": "OPENROUTER_API_KEY",
        "models": [
            "openrouter-mistral-7b",
            "openrouter-llama-3.3-70b",
            "openrouter-gemma-3-27b",
            "openrouter-deepseek-v3",
        ],
    },
    "openai": {
        "display": "OpenAI (ChatGPT)",
        "env_key": "OPENAI_API_KEY",
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-5.1-chat",
        ],
    },
    "gemini": {
        "display": "Google Gemini",
        "env_key": "GEMINI_API_KEY",
        "models": [
            "gemini-pro",
            "gemini-advanced",
        ],
    },
    "anthropic": {
        "display": "Anthropic (Claude)",
        "env_key": "ANTHROPIC_API_KEY",
        "models": [
            "claude-3",
            "claude-2.1",
        ],
    },
}


# Attempt to load dynamic OpenRouter model lists if present in the repo `data/` folder.
# There are two potential files produced by the tooling:
# - data/openrouter_models.json       (raw/fetched model list)
# - data/openrouter_model_checks.json (ranked checks; may include a `top_models` list)
# Navigate from src/providers/ up two levels to the project root
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_OR_MODELS_PATH = os.path.join(_ROOT, "data", "openrouter_models.json")
_OR_CHECKS_PATH = os.path.join(_ROOT, "data", "openrouter_model_checks.json")


def _load_openrouter_dynamic():
    """If dynamic files exist, try to extract model ids (prefer ranked top list).
    This is permissive: tolerant to different JSON shapes produced by the scripts.
    """
    models = []

    # First prefer the checks file (ranked top models)
    if os.path.exists(_OR_CHECKS_PATH):
        try:
            with open(_OR_CHECKS_PATH, "r", encoding="utf-8") as fh:
                j = json.load(fh)
                # Common shapes: {'top_models': ['id', ...]} or {'top': [...]}
                for key in ("top_models", "top", "models", "results", "checked"):
                    val = j.get(key) if isinstance(j, dict) else None
                    if isinstance(val, list) and val:
                        # items might be dicts with 'model' or 'id' keys
                        extracted = []
                        for it in val:
                            if isinstance(it, str):
                                extracted.append(it)
                            elif isinstance(it, dict):
                                extracted.append(it.get("model") or it.get("id") or it.get("name"))
                        models = [m for m in extracted if m]
                        if models:
                            return models
        except Exception:
            pass

    # Fallback to the raw models file (list under 'models')
    if os.path.exists(_OR_MODELS_PATH):
        try:
            with open(_OR_MODELS_PATH, "r", encoding="utf-8") as fh:
                j = json.load(fh)
                arr = j.get("models") if isinstance(j, dict) else None
                if isinstance(arr, list):
                    extracted = [m.get("id") if isinstance(m, dict) else None for m in arr]
                    models = [m for m in extracted if m]
        except Exception:
            pass

    return models


# Apply dynamic overrides (if present)
_dynamic = _load_openrouter_dynamic()
if _dynamic:
    _PROVIDERS.get("openrouter", {}).setdefault("models", [])
    # prefer to show only the top N for UI clarity
    _PROVIDERS["openrouter"]["models"] = _dynamic[:15]


def list_providers() -> List[str]:
    """Return provider keys in registry order."""
    return list(_PROVIDERS.keys())


def get_display_name(provider: str) -> Optional[str]:
    return _PROVIDERS.get(provider, {}).get("display")


def get_models(provider: str) -> List[str]:
    return list(_PROVIDERS.get(provider, {}).get("models", []))


def has_api_key(provider: str) -> bool:
    """Return True if the environment contains the provider's configured API key.

    This is a convenience for interactive UIs to show availability.
    """
    env = get_env_key_name(provider)
    if not env:
        return False
    return bool(os.environ.get(env))


def get_env_key_name(provider: str) -> Optional[str]:
    return _PROVIDERS.get(provider, {}).get("env_key")


def register_provider(name: str, *, display: str, env_key: str, models: Optional[List[str]] = None):
    """Register a new provider or update existing metadata."""
    _PROVIDERS[name] = {
        "display": display,
        "env_key": env_key,
        "models": list(models or []),
    }


def unregister_provider(name: str):
    _PROVIDERS.pop(name, None)
