#!/usr/bin/env python3
"""
Debug script to check if OpenRouterProvider is loading all keys correctly.
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Test get_api_keys
from src.utils import get_api_keys

print("\n" + "="*80)
print("Checking OpenRouter Key Loading")
print("="*80 + "\n")

# Check raw env var
raw_env = os.getenv('OPENROUTER_API_KEY', '')
print(f"Raw OPENROUTER_API_KEY from .env:")
print(f"  Value: {raw_env[:50]}...")
print(f"  Type: {type(raw_env)}")
print()

# Check parsed keys
keys = get_api_keys('openrouter')
print(f"Parsed keys from get_api_keys('openrouter'):")
print(f"  Count: {len(keys)}")
for idx, key in enumerate(keys, 1):
    print(f"  Key {idx}: {key[:30]}...")
print()

# Test OpenRouterProvider initialization
print("="*80)
print("Testing OpenRouterProvider Initialization")
print("="*80 + "\n")

from src.target_ai_wrapper import OpenRouterProvider

try:
    provider = OpenRouterProvider(model='meta-llama/llama-3.2-3b-instruct:free')
    
    print(f"Provider initialized successfully!")
    print(f"  Model: {provider.model}")
    print(f"  API Keys loaded: {len(provider.api_keys)}")
    print(f"  Keys:")
    for idx, key in enumerate(provider.api_keys, 1):
        print(f"    Key {idx}: {key[:30]}...")
    print()
    print(f"  Rotation threshold: {provider.requests_per_key} requests per key")
    print(f"  Current key index: {provider._key_index}")
    print()
    
except Exception as e:
    print(f"ERROR initializing provider: {e}")
    import traceback
    traceback.print_exc()

print("="*80 + "\n")
