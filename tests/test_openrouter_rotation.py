import sys
import types
from types import SimpleNamespace
import pytest

import importlib


def test_openrouter_key_rotation(monkeypatch):
    """
    Simulate OpenRouter/OpenAI client behavior where the first two keys hit 429
    rate-limit errors and the third key succeeds. Verify rotation, temporary bans,
    and that the successful response comes from the non-rate-limited key.
    """

    # Import the target_ai_wrapper module and patch its get_api_keys reference
    taw = importlib.import_module('src.target_ai_wrapper')

    # Make the wrapper return three keys
    monkeypatch.setattr(taw, 'get_api_keys', lambda provider: ['k1', 'k2', 'k3'])

    # Create a fake 'openai' module that behaves differently depending on api_key
    fake_openai = types.SimpleNamespace()

    def OpenAI(api_key=None, base_url=None):
        # client.chat.completions.create(...) should raise for k1/k2, succeed for k3
        def create(model=None, messages=None, temperature=None, max_tokens=None):
            if api_key in ('k1', 'k2'):
                raise Exception('429 Rate limit for key')
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=f'success from {api_key}'))])

        client = SimpleNamespace()
        client.chat = SimpleNamespace()
        client.chat.completions = SimpleNamespace()
        client.chat.completions.create = create
        return client

    fake_openai.OpenAI = OpenAI

    # Insert fake module into sys.modules so import openai inside provider picks it up
    monkeypatch.setitem(sys.modules, 'openai', fake_openai)

    # Now import the OpenRouterProvider and instantiate it (it will call the patched get_api_keys)
    from src.target_ai_wrapper import OpenRouterProvider

    provider = OpenRouterProvider(model='test-model')

    # Call query; set initial_backoff=0 to avoid sleeping during the unit test
    resp = provider.query('hello', initial_backoff=0)

    # Response should come from the third key (k3) since k1/k2 are rate-limited
    assert resp == 'success from k3'

    # The provider should have recorded temporary bans for k1 and k2
    assert 'k1' in provider._banned
    assert 'k2' in provider._banned


def test_openrouter_45_request_rotation(monkeypatch):
    """
    Verify that OpenRouter provider rotates to the next key after 45 successful
    requests on a single key.
    """

    # Import the target_ai_wrapper module and patch its get_api_keys reference
    taw = importlib.import_module('src.target_ai_wrapper')

    # Make the wrapper return two keys
    monkeypatch.setattr(taw, 'get_api_keys', lambda provider: ['k1', 'k2'])

    # Create a fake 'openai' module that always succeeds
    fake_openai = types.SimpleNamespace()

    def OpenAI(api_key=None, base_url=None):
        def create(model=None, messages=None, temperature=None, max_tokens=None):
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=f'response from {api_key}'))])

        client = SimpleNamespace()
        client.chat = SimpleNamespace()
        client.chat.completions = SimpleNamespace()
        client.chat.completions.create = create
        return client

    fake_openai.OpenAI = OpenAI

    # Insert fake module into sys.modules
    monkeypatch.setitem(sys.modules, 'openai', fake_openai)

    # Import and instantiate OpenRouterProvider
    from src.target_ai_wrapper import OpenRouterProvider

    provider = OpenRouterProvider(model='test-model')
    
    # Make 45 requests on k1 (should all succeed)
    for i in range(45):
        resp = provider.query(f'prompt {i}', initial_backoff=0)
        assert 'k1' in resp, f"Request {i} should use k1"
    
    # Verify k1 has 45 requests recorded
    assert provider._request_count.get('k1', 0) == 45, "k1 should have exactly 45 requests"
    
    # Next request should rotate to k2
    resp = provider.query('prompt 46', initial_backoff=0)
    assert 'k2' in resp, "Request 46 should use k2 after rotation"
    
    # Verify k2 now has 1 request
    assert provider._request_count.get('k2', 0) == 1, "k2 should have 1 request after rotation"

