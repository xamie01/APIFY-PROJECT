import asyncio
import os
import json
from typing import List, Dict, Any

# Minimal Apify compatibility shim if apify SDK isn't installed.
try:
    from apify import Actor
    APIFY_AVAILABLE = True
except Exception:
    APIFY_AVAILABLE = False

from src.utils.apify_helpers import load_prompts_from_storage, load_prompts_with_metadata, count_prompts
from src.utils.queue_manager import QueueManager
from src.utils.reporter import Reporter
from src.providers.openrouter import OpenRouterProvider
from src.providers.openai import OpenAIProvider
from src.providers.gemini import GeminiProvider
from src.providers.anthropic import AnthropicProvider


def _get_actor():
    # If Apify Actor is available, wrap it to normalize API surface
    if APIFY_AVAILABLE:
        # If apify Actor exists but not initialized, fall back to DummyActor
        try:
            default_inst = None
            if hasattr(Actor, '_get_default_instance'):
                default_inst = Actor._get_default_instance()
            if default_inst is not None and getattr(default_inst, '_is_initialized', False) is False:
                # Not initialized, use DummyActor instead
                raise RuntimeError('Apify Actor not initialized')
        except Exception:
            # Use local dummy actor when apify actor not initialized
            class DummyActor:
                def log(self, *args, **kwargs):
                    print(*args)
                async def push_data(self, item):
                    print('PUSH_DATA:', json.dumps(item)[:200])
                async def get_value(self, key):
                    return None
                async def set_value(self, key, val):
                    return None
                async def set_status_message(self, msg):
                    print('STATUS:', msg)
            return DummyActor()

        class ActorProxy:
            def __init__(self, actor_module):
                self._actor = actor_module
            def log(self, *args, **kwargs):
                # Actor.log may be a function or logger-like
                fn = getattr(self._actor, 'log', None)
                if callable(fn):
                    try:
                        return fn(*args, **kwargs)
                    except TypeError:
                        # maybe logger object: call .info
                        if hasattr(fn, 'info'):
                            return fn.info(*args, **kwargs)
                # fallback to print
                print(*args)
            async def push_data(self, item):
                if hasattr(self._actor, 'push_data'):
                    maybe = getattr(self._actor, 'push_data')
                    if callable(maybe):
                        res = maybe(item)
                        if asyncio.iscoroutine(res):
                            await res
                        return
                # fallback
                print('PUSH_DATA:', json.dumps(item)[:200])
            async def get_value(self, key):
                fn = getattr(self._actor, 'get_value', None)
                if callable(fn):
                    res = fn(key)
                    if asyncio.iscoroutine(res):
                        return await res
                    return res
                return None
            async def set_value(self, key, val):
                fn = getattr(self._actor, 'set_value', None)
                if callable(fn):
                    res = fn(key, val)
                    if asyncio.iscoroutine(res):
                        await res
            async def set_status_message(self, msg):
                fn = getattr(self._actor, 'set_status_message', None)
                if callable(fn):
                    res = fn(msg)
                    if asyncio.iscoroutine(res):
                        await res
                else:
                    print('STATUS:', msg)
        return ActorProxy(Actor)

    # Lightweight dummy actor for local/test runs
    class DummyActor:
        def log(self, *args, **kwargs):
            print(*args)
        async def push_data(self, item):
            print('PUSH_DATA:', json.dumps(item)[:200])
        async def get_value(self, key):
            return None
        async def set_value(self, key, val):
            return None
        async def set_status_message(self, msg):
            print('STATUS:', msg)
    return DummyActor()


async def main(input_data: Dict[str, Any] = None):
    """
    Main actor entry point.
    
    When running on Apify:
    - Input comes from Actor.get_input() (user configuration from the UI)
    - Results are pushed via Actor.push_data() (visible in Dataset tab)
    
    When running locally:
    - Input comes from ACTOR_INPUT env var or function parameter
    - Results are printed to console
    """
    
    # Initialize actor context (required for Apify platform)
    if APIFY_AVAILABLE:
        try:
            async with Actor:
                return await _run_actor(input_data)
        except Exception as e:
            # If Actor context fails, run without it
            print(f'Actor context unavailable, running standalone: {e}')
            return await _run_actor(input_data)
    else:
        return await _run_actor(input_data)


async def _run_actor(input_data: Dict[str, Any] = None):
    """Core actor logic."""
    ActorShim = _get_actor()
    ActorShim.log('Starting O-SATE actor')

    # Get input from Apify platform or fallback
    if input_data is None:
        if APIFY_AVAILABLE:
            try:
                # This is how Apify passes user input from the UI
                input_data = await Actor.get_input() or {}
            except Exception:
                input_data = {}
        
        # Fallback to environment variable (for local testing)
        if not input_data:
            try:
                raw = os.environ.get('ACTOR_INPUT')
                input_data = json.loads(raw) if raw else {}
            except Exception:
                input_data = {}

    # Handle both 'model' (singular) and 'models' (plural) for flexibility
    models: List[str] = input_data.get('models', [])
    if not models:
        # Check for singular 'model' parameter
        single_model = input_data.get('model')
        if single_model:
            models = [single_model]
        else:
            # Default model
            # Use DEFAULT_MODEL from config/.env, fallback to free Gemma
            from src.utils import load_config
            try:
                config = load_config('config/default_config.yaml')
                default_model = config.get('DEFAULT_MODEL', 'google/gemma-3-4b-it:free')
            except Exception:
                default_model = 'google/gemma-3-4b-it:free'
            models = [default_model]
    
    max_prompts: int = input_data.get('maxPrompts', 180)
    concurrency: int = input_data.get('concurrency', 4)
    api_keys_overrides: Dict[str, Any] = input_data.get('apiKeys', {}) or {}
    
    ActorShim.log(f'🎯 Target models: {models}')

    # Show available prompts
    prompt_counts = count_prompts()
    ActorShim.log(f'📊 Available prompts: {prompt_counts.get("_total", 0)} total')
    for cat, cnt in prompt_counts.items():
        if cat != '_total':
            ActorShim.log(f'   - {cat}: {cnt} prompts')

    prompts = await load_prompts_from_storage(max_prompts)
    ActorShim.log(f'📝 Loaded {len(prompts)} prompts (max: {max_prompts})')

    queue = QueueManager(max_concurrency=concurrency)
    reporter = Reporter()

    # Initialize providers (simple selection: first model prefix decides provider)
    providers = {}
    for m in models:
        # Allow per-model override of api keys via input apiKeys (keyed by provider name)
        model_lower = m.lower()
        if model_lower.startswith('openrouter') or '/' in m:
            # OpenRouter models often use org/model format
            override = api_keys_overrides.get('openrouter')
            providers[m] = OpenRouterProvider(model=m, api_keys=override) if override else OpenRouterProvider(model=m)
        elif model_lower.startswith('gpt') or model_lower.startswith('openai'):
            override = api_keys_overrides.get('openai')
            providers[m] = OpenAIProvider(model=m, api_key=override) if override else OpenAIProvider(model=m)
        elif model_lower.startswith('claude') or model_lower.startswith('anthropic'):
            override = api_keys_overrides.get('anthropic')
            providers[m] = AnthropicProvider(model=m, api_key=override) if override else AnthropicProvider(model=m)
        elif model_lower.startswith('gemini'):
            override = api_keys_overrides.get('gemini')
            providers[m] = GeminiProvider(model=m, api_key=override) if override else GeminiProvider(model=m)
        else:
            # Default to OpenRouter for unknown prefixes (most flexible)
            override = api_keys_overrides.get('openrouter')
            providers[m] = OpenRouterProvider(model=m, api_keys=override) if override else OpenRouterProvider(model=m)

    results = []

    async def _call_provider(provider, prompt):
        # prefer native async method if available
        if hasattr(provider, 'query_async') and callable(getattr(provider, 'query_async')):
            return await provider.query_async(prompt)
        # otherwise run sync query in a thread
        return await asyncio.to_thread(provider.query, prompt)

    async def process_prompt(prompt_idx_prompt):
        idx, prompt = prompt_idx_prompt
        record = {'prompt_id': idx, 'prompt': prompt, 'results': []}
        for model, provider in providers.items():
            try:
                resp = await _call_provider(provider, prompt)
                record['results'].append({'model': model, 'response': resp})
            except Exception as e:
                record['results'].append({'model': model, 'error': str(e)})
        await ActorShim.push_data(record)
        results.append(record)

    await queue.process_parallel(list(enumerate(prompts)), process_prompt)

    summary = reporter.generate_summary(results)
    await ActorShim.push_data({'summary': summary})
    ActorShim.log('Run complete')
    return {'results': results, 'summary': summary}


if __name__ == '__main__':
    asyncio.run(main())
