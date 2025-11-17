#!/usr/bin/env python3
"""
Test script to check each OpenRouter API key for rate limits.
Makes 2 requests per key and reports status.
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API keys from environment
api_keys_str = os.getenv('OPENROUTER_API_KEY', '')
if not api_keys_str:
    print("ERROR: OPENROUTER_API_KEY not found in .env")
    sys.exit(1)

# Parse comma-separated keys
api_keys = [key.strip() for key in api_keys_str.split(',')]
print(f"\n{'='*80}")
print(f"Testing {len(api_keys)} OpenRouter API Keys")
print(f"{'='*80}\n")

# Import OpenAI to make requests
try:
    import openai
except ImportError:
    print("ERROR: openai package not installed. Run: pip install openai")
    sys.exit(1)

results = {}
base_url = "https://openrouter.ai/api/v1"
model = "meta-llama/llama-3.2-3b-instruct:free"

for idx, key in enumerate(api_keys, 1):
    print(f"[Key {idx}/{len(api_keys)}] Testing: {key[:30]}...")
    
    client = openai.OpenAI(api_key=key, base_url=base_url)
    key_status = {"success": 0, "rate_limit": 0, "other_error": 0}
    
    for req_num in range(1, 3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": f"Say hello (request {req_num})"}],
                temperature=0.7,
                max_tokens=100,
            )
            key_status["success"] += 1
            print(f"  Request {req_num}: ✅ SUCCESS")
            
        except Exception as e:
            error_msg = str(e).lower()
            if '429' in error_msg or 'rate limit' in error_msg or 'too many requests' in error_msg:
                key_status["rate_limit"] += 1
                print(f"  Request {req_num}: ❌ RATE LIMIT (429)")
            else:
                key_status["other_error"] += 1
                print(f"  Request {req_num}: ❌ ERROR: {str(e)[:60]}")
        
        # Brief pause between requests
        time.sleep(0.5)
    
    results[key] = key_status
    print()

# Summary
print(f"{'='*80}")
print("SUMMARY")
print(f"{'='*80}\n")

for idx, (key, status) in enumerate(results.items(), 1):
    key_short = key[:30] + "..."
    success = status["success"]
    rate_limit = status["rate_limit"]
    errors = status["other_error"]
    
    if rate_limit > 0:
        status_badge = "❌ RATE LIMITED"
    elif success == 2:
        status_badge = "✅ WORKING"
    else:
        status_badge = "⚠️ PARTIAL/ERROR"
    
    print(f"Key {idx}: {key_short}")
    print(f"  Status: {status_badge}")
    print(f"  Success: {success}/2, Rate Limit: {rate_limit}/2, Other Errors: {errors}/2")
    print()

# Count available keys
available_keys = sum(1 for s in results.values() if s["success"] > 0)
rate_limited_keys = sum(1 for s in results.values() if s["rate_limit"] > 0)

print(f"Available Keys: {available_keys}/{len(api_keys)}")
print(f"Rate-Limited Keys: {rate_limited_keys}/{len(api_keys)}")
print(f"\n{'='*80}\n")

if available_keys == 0:
    print("⚠️  ALL KEYS ARE RATE LIMITED!")
    print("Consider: Adding credits, creating more free accounts, or waiting for daily reset.\n")
    sys.exit(1)
else:
    print(f"✅ {available_keys} key(s) still available for testing.\n")
    sys.exit(0)
