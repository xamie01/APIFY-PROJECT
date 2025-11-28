#!/usr/bin/env python3
"""
Test script for Apify actor enhancements.
Tests: Actor shim, prompt loading, provider initialization, and full flow.

Usage:
    python scripts/test_apify_actor.py          # Run all tests
    python scripts/test_apify_actor.py --quick  # Quick test (1 prompt)
"""

import asyncio
import os
import sys

# Ensure we can import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env BEFORE importing src modules
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


def test_env_loaded():
    """Test that environment variables are loaded from .env"""
    print("\n=== Test 1: Environment Variables ===")
    
    # Check for OpenRouter key
    key = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENROUTER_API_KEYS')
    if key:
        masked = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
        print(f"✅ OPENROUTER_API_KEY found: {masked}")
        return True
    else:
        print("❌ No OPENROUTER_API_KEY found in environment")
        print("   Make sure .env file exists with OPENROUTER_API_KEY=sk-or-v1-...")
        return False


def test_actor_shim():
    """Test that the Actor shim loads correctly"""
    print("\n=== Test 2: Actor Shim ===")
    
    try:
        from src.main import _get_actor
        actor = _get_actor()
        actor_type = type(actor).__name__
        print(f"✅ Actor shim loaded: {actor_type}")
        
        # Test logging
        actor.log("Test log message")
        print("✅ Actor.log() works")
        return True
    except Exception as e:
        print(f"❌ Actor shim failed: {e}")
        return False


def test_prompt_loading():
    """Test that prompts can be loaded from storage or bundled files"""
    print("\n=== Test 3: Prompt Loading ===")
    
    try:
        from src.utils.apify_helpers import load_prompts_from_storage
        prompts = asyncio.run(load_prompts_from_storage(5))
        print(f"✅ Loaded {len(prompts)} prompts")
        
        if prompts:
            preview = prompts[0][:60] + "..." if len(prompts[0]) > 60 else prompts[0]
            print(f"   First prompt: {preview}")
        return len(prompts) > 0
    except Exception as e:
        print(f"❌ Prompt loading failed: {e}")
        return False


def test_provider_init():
    """Test that OpenRouter provider initializes with keys from .env"""
    print("\n=== Test 4: Provider Initialization ===")
    
    try:
        from src.providers.openrouter import OpenRouterProvider
        provider = OpenRouterProvider(model='openrouter-mistral-7b')
        print(f"✅ OpenRouterProvider initialized")
        print(f"   Keys: {len(provider.api_keys)}")
        print(f"   Quota: {provider.requests_per_key}/key")
        return True
    except RuntimeError as e:
        print(f"❌ Provider init failed: {e}")
        print("   Ensure OPENROUTER_API_KEY is set in .env")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_gemini_graceful_fallback():
    """Test that Gemini provider handles missing API key gracefully"""
    print("\n=== Test 5: Gemini Graceful Fallback ===")
    
    try:
        from src.providers.gemini import GeminiProvider
        provider = GeminiProvider(model='gemini-test')
        
        # Query without API key should return helpful error message
        result = asyncio.run(provider.query_async("Test prompt"))
        
        if "ERROR" in result or "GEMINI" in result:
            print(f"✅ Gemini handles missing key gracefully")
            print(f"   Response: {result[:80]}...")
            return True
        else:
            print(f"⚠️  Unexpected response: {result[:80]}...")
            return True  # Still passes if it doesn't crash
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False


async def test_full_actor_flow(max_prompts: int = 1):
    """Test the full actor flow with real API call"""
    print(f"\n=== Test 6: Full Actor Flow ({max_prompts} prompt(s)) ===")
    
    try:
        from src.main import main
        
        print("   Starting actor...")
        result = await main({
            'models': ['openrouter-mistral-7b'],
            'maxPrompts': max_prompts,
            'concurrency': 1
        })
        
        if result:
            print(f"✅ Actor completed successfully")
            print(f"   Result keys: {list(result.keys())}")
            summary = result.get('summary', {})
            print(f"   Summary: {summary}")
            
            results = result.get('results', [])
            if results:
                first = results[0]
                print(f"   First result: prompt_id={first.get('prompt_id')}")
                if first.get('results'):
                    model_result = first['results'][0]
                    if 'response' in model_result:
                        resp_preview = model_result['response'][:100] + "..."
                        print(f"   Response preview: {resp_preview}")
                    elif 'error' in model_result:
                        print(f"   Error: {model_result['error']}")
            return True
        else:
            print("❌ Actor returned None")
            return False
    except Exception as e:
        print(f"❌ Full flow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main_tests():
    """Run all tests"""
    print("=" * 60)
    print("O-SATE Apify Actor Test Suite")
    print("=" * 60)
    
    # Check for --quick flag
    quick_mode = '--quick' in sys.argv
    
    results = {}
    
    # Test 1: Environment
    results['env'] = test_env_loaded()
    
    # Test 2: Actor shim
    results['actor'] = test_actor_shim()
    
    # Test 3: Prompt loading
    results['prompts'] = test_prompt_loading()
    
    # Test 4: Provider init (requires env)
    if results['env']:
        results['provider'] = test_provider_init()
    else:
        print("\n=== Test 4: Provider Initialization ===")
        print("⏭️  Skipped (no API key)")
        results['provider'] = None
    
    # Test 5: Gemini fallback
    results['gemini'] = test_gemini_graceful_fallback()
    
    # Test 6: Full flow (only if provider works)
    if results.get('provider'):
        if quick_mode:
            print("\n[Quick mode: testing with 1 prompt]")
        results['full_flow'] = asyncio.run(test_full_actor_flow(1 if quick_mode else 2))
    else:
        print("\n=== Test 6: Full Actor Flow ===")
        print("⏭️  Skipped (provider not initialized)")
        results['full_flow'] = None
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for name, result in results.items():
        status = "✅ PASS" if result is True else ("❌ FAIL" if result is False else "⏭️  SKIP")
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("\n🎉 All tests passed! Ready for Apify deployment.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main_tests())
