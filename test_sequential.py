#!/usr/bin/env python3
"""
Test script to simulate sequential requests and verify key rotation.
Makes 10 requests in sequence and logs which key each uses.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from src.target_ai_wrapper import OpenRouterProvider

print("\n" + "="*80)
print("Testing Sequential Requests with Same Provider Instance")
print("="*80 + "\n")

provider = OpenRouterProvider(model='meta-llama/llama-3.2-3b-instruct:free')

print(f"Provider initialized with {len(provider.api_keys)} keys:")
for idx, key in enumerate(provider.api_keys, 1):
    print(f"  Key {idx}: {key[:30]}...")
print()

# Make 10 sequential requests
for req_num in range(1, 11):
    print(f"[Request {req_num}] Attempting to query...")
    print(f"  Current key index: {provider._key_index}")
    print(f"  Current key: {provider.api_keys[provider._key_index][:30]}...")
    print(f"  Request count per key: {provider._request_count}")
    print(f"  Banned keys: {provider._banned}")
    
    try:
        response = provider.query(
            f"Say 'Hello request {req_num}' in one sentence",
            initial_backoff=0
        )
        print(f"  Result: ✅ SUCCESS")
        print(f"  Response preview: {response[:50]}...")
        
    except Exception as e:
        error_msg = str(e).lower()
        if '429' in error_msg or 'rate limit' in error_msg:
            print(f"  Result: ❌ RATE LIMITED (all keys exhausted)")
        else:
            print(f"  Result: ❌ ERROR: {str(e)[:50]}")
    
    print()

print("="*80)
print("Final State")
print("="*80)
print(f"Final key index: {provider._key_index}")
print(f"Request count per key: {provider._request_count}")
print(f"Banned keys: {provider._banned}")
print(f"Rotation cycles completed: {provider._rotation_cycle}")
print("="*80 + "\n")
