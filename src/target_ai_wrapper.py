"""
Unified wrapper for interacting with multiple AI providers
Supports: OpenAI, Google Gemini, Anthropic, DeepSeek, Ollama, Cohere, 
         Hugging Face, Replicate, Together AI, Groq, Mistral, Perplexity
"""

import os
import time
import json
import asyncio
import sys
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import requests
from .logger import get_logger
from .utils import get_api_key, get_api_keys, load_config

# Lazy imports for providers
openai = None
genai = None
anthropic = None
cohere = None
replicate = None
groq = None
mistral = None

logger = get_logger(__name__)


class BaseAIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def query(self, prompt: str, **kwargs) -> str:
        """Send a query to the AI and return response"""
        pass
    
    @abstractmethod
    async def query_async(self, prompt: str, **kwargs) -> str:
        """Send an async query to the AI and return response"""
        pass


# Use provider implementations from src/providers (migrated logic)
try:
    from src.providers import (
        OpenAIProvider as ProvidersOpenAI,
        GeminiProvider as ProvidersGemini,
        OpenRouterProvider as ProvidersOpenRouter,
        AnthropicProvider as ProvidersAnthropic,
        # Optional providers not yet implemented in src/providers/ can be added here
    )
except Exception:
    ProvidersOpenAI = ProvidersGemini = ProvidersOpenRouter = ProvidersAnthropic = None

# Provide fallbacks for providers not implemented in src/providers
def _missing_provider(name: str):
    class MissingProvider:
        def __init__(self, *args, **kwargs):
            raise RuntimeError(f"Provider '{name}' is not available. Please ensure it's implemented in src/providers and exported in src/providers/__init__.py")
    return MissingProvider

# Provide compatibility names so rest of the file can reference the familiar class names
OpenAIProvider = ProvidersOpenAI or _missing_provider('OpenAIProvider')
GeminiProvider = ProvidersGemini or _missing_provider('GeminiProvider')
OpenRouterProvider = ProvidersOpenRouter or _missing_provider('OpenRouterProvider')
AnthropicProvider = ProvidersAnthropic or _missing_provider('AnthropicProvider')

# Provide local stub classes for providers that are referenced but not migrated yet
DeepSeekProvider = _missing_provider('DeepSeekProvider')
OllamaProvider = _missing_provider('OllamaProvider')
CohereProvider = _missing_provider('CohereProvider')
GroqProvider = _missing_provider('GroqProvider')


# Apify integration shim
try:
    from apify import Actor
    APIFY_AVAILABLE = True
except Exception:
    APIFY_AVAILABLE = False


# Adapter to ensure providers expose an async query API
async def _call_provider_async(provider, prompt: str, **kwargs) -> str:
    if hasattr(provider, 'query_async') and callable(getattr(provider, 'query_async')):
        return await provider.query_async(prompt, **kwargs)
    # Fallback to running sync code in a threadpool
    return await asyncio.to_thread(provider.query, prompt, **kwargs)

# Lightweight async wrapper for sync query (used when calling from async contexts)
async def _call_provider_sync_compat(provider, prompt: str, **kwargs) -> str:
    return await _call_provider_async(provider, prompt, **kwargs)


class TargetAIWrapper:
    """
    Main wrapper class that provides a unified interface to all AI providers
    """
    
    def __init__(self, target: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize AI wrapper
        
        Args:
            target: Target AI identifier (e.g., 'openai-gpt4', 'anthropic-claude')
            config: Optional configuration dictionary
        """
        self.config = config or load_config()
        self.target = target
        # Interactive selection state (only prompt when running in a TTY)
        self._interactive_model_selected = False
        self._interactive_enabled = sys.stdin.isatty()
        # Ensure API key is present for the selected provider before initializing
        provider_key_map = {
            'openai': 'openai',
            'gemini': 'google',
            'anthropic': 'anthropic',
            'deepseek': 'deepseek',
            'ollama': 'ollama',
            'cohere': 'cohere',
            'groq': 'groq',
            'openrouter': 'openrouter'
        }
        key_name = None
        for k in provider_key_map:
            if target.lower().startswith(k):
                key_name = provider_key_map[k]
                break

        if key_name:
            # If the caller provided an explicit config, require the API key
            # to be present in config['target_ai']['api_keys'] to avoid
            # quietly reading environment variables during tests.
            if config is not None:
                api_keys_cfg = self.config.get('target_ai', {}).get('api_keys', {})
                if not api_keys_cfg or not api_keys_cfg.get(key_name):
                    raise ValueError(f"API key for provider '{key_name}' not found in provided configuration")
            else:
                api_key = get_api_key(key_name)
                # Also check env fallback
                if not api_key and key_name == 'google':
                    api_key = os.getenv('GOOGLE_API_KEY')
                if not api_key and key_name == 'openai':
                    api_key = os.getenv('OPENAI_API_KEY')

                if not api_key:
                    raise ValueError(f"API key for provider '{key_name}' not found")

        self.provider = self._initialize_provider(target)
        
        # Request tracking
        self.request_count = 0
        self.total_tokens = 0
        self.request_history: List[Dict[str, Any]] = []
        
        logger.info(f"Target AI wrapper initialized: {target}")
    
    def _initialize_provider(self, target: str) -> BaseAIProvider:
        """
        Initialize the appropriate provider based on target
        
        Args:
            target: Target AI identifier (e.g., openai-gpt4, gemini-pro, anthropic-claude)
        
        Returns:
            Initialized provider instance
        """
        target_lower = target.lower()
        
        # OpenAI and compatible providers
        if target_lower.startswith("openai"):
            if "-" in target:
                model = target.split("-", 1)[1]
                if model == "gpt3.5":
                    model = "gpt-3.5-turbo"
                elif model == "gpt4":
                    model = "gpt-4"
                elif model.startswith("gpt"):
                    model = f"gpt-{model.replace('gpt', '')}"
                elif not model.startswith("gpt-"):
                    model = f"gpt-{model}"
            else:
                model = "gpt-4"
            return OpenAIProvider(model=model)
        
        # Google Gemini
        elif target_lower.startswith("gemini"):
            if target_lower.endswith("vision"):
                model = "gemini-pro-vision"
            else:
                model = "gemini-pro"
            return GeminiProvider(model=model)
        
        # Anthropic Claude
        elif target_lower.startswith("anthropic"):
            model = target.split("-", 1)[1] if "-" in target else "claude-3-opus-20240229"
            # Use the in-file Anthropic provider if present, otherwise raise (keep compatibility)
            try:
                return AnthropicProvider(model=model)
            except Exception:
                raise ValueError("Anthropic provider unavailable in providers/ module")
            
        # DeepSeek
        elif target_lower.startswith("deepseek"):
            model = target.split("-", 1)[1] if "-" in target else "deepseek-chat"
            return DeepSeekProvider(model=model)
        
        # Ollama (local models)
        elif target_lower.startswith("ollama"):
            model = target.split("-", 1)[1] if "-" in target else "llama2"
            return OllamaProvider(model=model)
        
        # Cohere
        elif target_lower.startswith("cohere"):
            model = target.split("-", 1)[1] if "-" in target else "command"
            return CohereProvider(model=model)
        
        # Groq
        elif target_lower.startswith("groq"):
            model = target.split("-", 1)[1] if "-" in target else "mixtral-8x7b-32768"
            return GroqProvider(model=model)
        
        # OpenRouter free models
        elif target_lower.startswith("openrouter"):
            # Default mappings (kept as sensible fallbacks)
            default_model_map = {
                "llama-3b": "meta-llama/llama-3.2-3b-instruct:free",
                "llama-1b": "meta-llama/llama-3.2-1b-instruct:free",
                "deepseek-r1": "deepseek/deepseek-r1-distill-qwen-32b:free",
                "qwen-7b": "qwen/qwen-2-7b-instruct:free",
                "gemma-7b": "google/gemma-7b-it:free",
                "mistral-7b": "mistralai/mistral-7b-instruct:free",
                "openchat": "openchat/openchat-7b:free",
                "nous-hermes": "nousresearch/nous-hermes-llama2-13b:free",

                # Added mappings from fetched OpenRouter reasoning models
                "nemotron-nano-12b-v2-vl": "nvidia/nemotron-nano-12b-v2-vl:free",
                "minimax-m2": "minimax/minimax-m2:free",
                "deepseek-v3": "deepseek/deepseek-chat-v3-0324:free",
                "gpt-oss-20b": "openai/gpt-oss-20b:free",
                "gemma-3-27b": "google/gemma-3-27b-it:free",
                "qwen3-14b": "qwen/qwen3-14b:free",
                "llama-3.2-3b": "meta-llama/llama-3.2-3b-instruct:free",
                "deepseek-r1-base": "deepseek/deepseek-r1:free",
                "mistral-7b": "mistralai/mistral-7b-instruct:free",
                "llama-3.3-70b": "meta-llama/llama-3.3-70b-instruct:free",
            }

            # Merge with any user-provided mappings from config
            cfg_map = self.config.get('target_ai', {}).get('openrouter_model_map', {}) or {}
            # Normalize keys: allow users to specify either 'llama-3b' or 'openrouter-llama-3b'
            normalized_cfg_map = {}
            for k, v in cfg_map.items():
                nk = k
                if k.startswith('openrouter-'):
                    nk = k.split('openrouter-', 1)[1]
                normalized_cfg_map[nk] = v

            model_map = {**default_model_map, **normalized_cfg_map}

            # Helper to resolve a candidate string (could be friendly key, full id, or prefixed)
            def resolve_candidate(candidate: str) -> str:
                if not candidate:
                    return ""
                # If candidate already looks like an OpenRouter model id (contains '/'), use directly
                if '/' in candidate:
                    return candidate
                # If prefixed like 'openrouter-foo', extract suffix
                if candidate.startswith('openrouter-'):
                    candidate = candidate.split('openrouter-', 1)[1]
                # Map via model_map if available
                if candidate in model_map:
                    return model_map[candidate]
                # As a last resort return the candidate unchanged
                return candidate

            # If the caller provided a specific openrouter-<key>, resolve that
            if '-' in target:
                model_key = target.split('-', 1)[1]
                model = resolve_candidate(model_key)
            else:
                # No suffix provided: pick first configured openrouter model, or fallback_model
                configured_list = self.config.get('target_ai', {}).get('openrouter_models', [])
                fallback_cfg = self.config.get('target_ai', {}).get('fallback_model')

                chosen = None
                if configured_list:
                    chosen = configured_list[0]
                elif fallback_cfg:
                    chosen = fallback_cfg

                model = resolve_candidate(chosen) if chosen else default_model_map.get('llama-3b')

            return OpenRouterProvider(model=model)
        
        else:
            raise ValueError(f"Unsupported target AI: {target}")
    
    def _interactive_select_model_for_openai(self) -> None:
        """Prompt the user to choose an OpenAI model when running interactively.

        Uses config['target_ai']['openai_models'] if present, otherwise a sensible
        default list. Sets the provider.model to the chosen value.
        """
        if not self._interactive_enabled:
            logger.debug("Interactive model selection skipped (not a TTY)")
            return

        if self._interactive_model_selected:
            return

        models = self.config.get('target_ai', {}).get('openai_models') or [
            'gpt-4', 'gpt-3.5-turbo', 'gpt-4o', 'gpt-4o-mini'
        ]

        print("\nAvailable OpenAI models:")
        for i, m in enumerate(models, start=1):
            print(f"  {i}. {m}")
        print("  0. Use default configured model")

        try:
            choice = input("Select model (number or name) [default 0]: ").strip()
        except EOFError:
            logger.debug("No stdin available for interactive model selection; using default model")
            self._interactive_model_selected = True
            return

        if not choice or choice == '0':
            logger.info("Using default OpenAI model configuration")
            self._interactive_model_selected = True
            return

        # If numeric, map to list
        selected = None
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                selected = models[idx]
        else:
            # Treat as model name if provided
            if choice in models:
                selected = choice
            else:
                # Accept arbitrary model name as provided by user
                selected = choice

        if selected:
            try:
                if isinstance(self.provider, OpenAIProvider):
                    logger.info(f"Interactive selection: setting OpenAI model to '{selected}'")
                    self.provider.model = selected
                else:
                    logger.info(f"Interactive selection ignored: current provider is not OpenAI ({type(self.provider)})")
            except Exception as e:
                logger.warning(f"Failed to set interactive model selection: {e}")

        self._interactive_model_selected = True

    def query(self, prompt: str, **kwargs) -> str:
        """
        Send a query to the target AI provider.
        
        Providers like OpenRouter handle key rotation and fallback internally.
        No automatic fallback to different models—use the chosen provider and model.
        """
        start_time = time.time()

        try:
            # If using OpenAI provider and interactive selection enabled, prompt once
            if isinstance(self.provider, OpenAIProvider) and not self._interactive_model_selected:
                self._interactive_select_model_for_openai()

            self._apply_rate_limit()
            response = self.provider.query(prompt, **kwargs)

            execution_time = time.time() - start_time
            self._track_request(prompt, response, execution_time)

            logger.debug(f"Query completed in {execution_time:.2f}s")
            return response

        except Exception as e:
            # Log error and re-raise; no fallback to different models
            logger.error(f"Query failed: {e}")
            raise
    
    async def query_async(self, prompt: str, **kwargs) -> str:
        """
        Send an async query to the target AI
        
        Args:
            prompt: User prompt
            **kwargs: Additional parameters
        
        Returns:
            AI response text
        """
        start_time = time.time()
        
        try:
            self._apply_rate_limit()
            response = await self.provider.query_async(prompt, **kwargs)
            
            execution_time = time.time() - start_time
            self._track_request(prompt, response, execution_time)
            
            logger.debug(f"Async query completed in {execution_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Async query failed: {e}")
            raise
    
    def _apply_rate_limit(self) -> None:
        """Apply rate limiting based on configuration"""
        max_rpm = self.config.get("target_ai", {}).get("rate_limit_requests_per_minute", 30)
        
        if len(self.request_history) >= max_rpm:
            oldest_request = self.request_history[0]
            time_since_oldest = time.time() - oldest_request["timestamp"]
            
            if time_since_oldest < 60:
                sleep_time = 60 - time_since_oldest
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            cutoff_time = time.time() - 60
            self.request_history = [
                r for r in self.request_history 
                if r["timestamp"] > cutoff_time
            ]
    
    def _track_request(self, prompt: str, response: str, execution_time: float) -> None:
        """Track request metrics"""
        self.request_count += 1
        
        prompt_tokens = len(prompt.split()) * 1.3
        response_tokens = len(response.split()) * 1.3
        total_tokens = prompt_tokens + response_tokens
        
        self.total_tokens += total_tokens
        
        request_data = {
            "timestamp": time.time(),
            "prompt_length": len(prompt),
            "response_length": len(response),
            "estimated_tokens": total_tokens,
            "execution_time": execution_time
        }
        
        self.request_history.append(request_data)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get usage metrics"""
        return {
            "total_requests": self.request_count,
            "total_tokens": self.total_tokens,
            "average_response_time": sum(r["execution_time"] for r in self.request_history) / 
                                    len(self.request_history) if self.request_history else 0,
            "requests_last_minute": len([
                r for r in self.request_history 
                if time.time() - r["timestamp"] < 60
            ])
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self.request_count = 0
        self.total_tokens = 0
        self.request_history = []
        logger.info("Metrics reset")
