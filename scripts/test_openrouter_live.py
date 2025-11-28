#!/usr/bin/env python3
"""
OpenRouter Provider Live Test Suite
====================================

Comprehensive tests for the OpenRouterProvider with real API keys.
Tests key rotation, banning, quota exhaustion, and async functionality.

Usage:
    python scripts/test_openrouter_live.py           # Run all tests
    python scripts/test_openrouter_live.py --quick   # Run quick API test only
    python scripts/test_openrouter_live.py --help    # Show help

Requirements:
    - OPENROUTER_API_KEY set in .env or environment
    - Python packages: dotenv, httpx, openai
"""

import argparse
import asyncio
import os
import sys
import time

# Ensure src is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from src.providers.openrouter import OpenRouterProvider, _resolve_api_keys_runtime


# =============================================================================
# Utilities
# =============================================================================

def mask_key(key: str) -> str:
    """Mask API key for safe display (show first 8 and last 4 chars)."""
    if len(key) <= 12:
        return key[:4] + '...'
    return key[:8] + '...' + key[-4:]


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def print_result(passed: bool, message: str):
    """Print a test result."""
    icon = "✅" if passed else "❌"
    print(f"   {icon} {message}")


# =============================================================================
# Test: Quick API Connectivity
# =============================================================================

def test_quick_api():
    """Quick test to verify API connectivity and basic functionality."""
    print_header("Quick API Test")
    
    keys = _resolve_api_keys_runtime()
    if not keys:
        print_result(False, "No API keys found! Set OPENROUTER_API_KEY")
        return False
    
    print(f"   Found {len(keys)} key(s): {mask_key(keys[0])}")
    
    try:
        provider = OpenRouterProvider(
            model='mistralai/mistral-7b-instruct:free',
            api_keys=keys
        )
        
        start = time.time()
        response = provider.query("Say 'Hello!' in one word.", max_tokens=10)
        elapsed = time.time() - start
        
        print_result(True, f"Response in {elapsed:.2f}s: '{response.strip()[:50]}'")
        return True
    except Exception as e:
        print_result(False, f"Query failed: {e}")
        return False


# =============================================================================
# Test: Async Query
# =============================================================================

def test_async_query():
    """Test async query functionality."""
    print_header("Async Query Test")
    
    keys = _resolve_api_keys_runtime()
    if not keys:
        print_result(False, "No API keys found")
        return False
    
    provider = OpenRouterProvider(
        model='mistralai/mistral-7b-instruct:free',
        api_keys=keys
    )
    
    async def run_async():
        start = time.time()
        response = await provider.query_async("What is 2+2? Answer with just the number.")
        return response, time.time() - start
    
    try:
        response, elapsed = asyncio.run(run_async())
        print_result(True, f"Async response in {elapsed:.2f}s: '{response.strip()[:30]}'")
        return True
    except Exception as e:
        print_result(False, f"Async failed: {e}")
        return False


# =============================================================================
# Test: Key Rotation
# =============================================================================

def test_key_rotation():
    """Test that keys rotate after reaching per-key quota."""
    print_header("Key Rotation Test")
    
    real_key = os.environ.get('OPENROUTER_API_KEY')
    if not real_key:
        print_result(False, "No OPENROUTER_API_KEY set")
        return False
    
    # Create provider with 3 "keys" (same key, but tracked by index)
    provider = OpenRouterProvider(
        model='mistralai/mistral-7b-instruct:free',
        api_keys=[real_key, real_key, real_key]
    )
    provider.requests_per_key = 2  # Low quota for testing
    
    print(f"   Initialized with 3 keys, quota: {provider.requests_per_key}")
    print("   Sending 6 queries (should rotate every 2)...\n")
    
    rotations = 0
    for i in range(6):
        key_before = provider._key_idx
        try:
            provider.query("Say 'ok'", max_tokens=5)
            key_after = provider._key_idx
            if key_before != key_after:
                rotations += 1
            status = "🔄" if key_before != key_after else "  "
            print(f"   Query {i+1}: idx {key_before}→{key_after} {status}")
        except Exception as e:
            print_result(False, f"Query {i+1} failed: {e}")
            return False
    
    print(f"\n   Rotations observed: {rotations}")
    print_result(rotations >= 2, f"Key rotation working ({rotations} rotations)")
    return rotations >= 2


# =============================================================================
# Test: Key Banning
# =============================================================================

def test_key_banning():
    """Test that banned keys are skipped and recovered after expiry."""
    print_header("Key Banning Test")
    
    real_key = os.environ.get('OPENROUTER_API_KEY')
    if not real_key:
        print_result(False, "No OPENROUTER_API_KEY set")
        return False
    
    provider = OpenRouterProvider(
        model='mistralai/mistral-7b-instruct:free',
        api_keys=[real_key, real_key]
    )
    
    # Test 1: Ban key 0, should use key 1
    provider._banned[0] = time.time() + 10
    result = provider._get_next_key()
    
    if provider._key_idx != 1:
        print_result(False, "Should have skipped banned key 0")
        return False
    print_result(True, "Skipped banned key 0, using key 1")
    
    # Test 2: Ban both keys, should return None
    provider._banned[1] = time.time() + 10
    result = provider._get_next_key()
    
    if result is not None:
        print_result(False, "Should return None when all keys banned")
        return False
    print_result(True, "Correctly returned None (all keys banned)")
    
    # Test 3: Clear bans, should work again
    provider._banned = {}
    result = provider._get_next_key()
    
    if result is None:
        print_result(False, "Should have keys available after ban expiry")
        return False
    print_result(True, "Keys available after ban expiry")
    
    return True


# =============================================================================
# Test: Quota Exhaustion
# =============================================================================

def test_quota_exhaustion():
    """Test that proper error is raised when all keys exhaust their quota."""
    print_header("Quota Exhaustion Test")
    
    real_key = os.environ.get('OPENROUTER_API_KEY')
    if not real_key:
        print_result(False, "No OPENROUTER_API_KEY set")
        return False
    
    provider = OpenRouterProvider(
        model='mistralai/mistral-7b-instruct:free',
        api_keys=[real_key, real_key]
    )
    provider.requests_per_key = 1  # Very low quota
    
    print(f"   Initialized with 2 keys, quota: {provider.requests_per_key}")
    
    # Query 1: Should succeed on key 0
    try:
        provider.query("Say 'test1'", max_tokens=5)
        print_result(True, f"Query 1 succeeded (key {provider._key_idx})")
    except Exception as e:
        print_result(False, f"Query 1 failed: {e}")
        return False
    
    # Query 2: Should rotate to key 1
    try:
        provider.query("Say 'test2'", max_tokens=5)
        print_result(True, f"Query 2 succeeded (key {provider._key_idx})")
    except Exception as e:
        print_result(False, f"Query 2 failed: {e}")
        return False
    
    # Query 3: Should fail (all exhausted)
    try:
        provider.query("Say 'test3'", max_tokens=5)
        print_result(False, "Query 3 should have raised RuntimeError")
        return False
    except RuntimeError as e:
        if "exhausted" in str(e).lower() or "banned" in str(e).lower():
            print_result(True, f"Query 3 correctly raised: {e}")
            return True
        print_result(False, f"Wrong error: {e}")
        return False


# =============================================================================
# Test: Stress Test
# =============================================================================

def test_stress():
    """Stress test with 10 rapid queries."""
    print_header("Stress Test (10 rapid queries)")
    
    real_key = os.environ.get('OPENROUTER_API_KEY')
    if not real_key:
        print_result(False, "No OPENROUTER_API_KEY set")
        return False
    
    provider = OpenRouterProvider(
        model='mistralai/mistral-7b-instruct:free',
        api_keys=[real_key]
    )
    
    success = 0
    start_total = time.time()
    
    for i in range(10):
        try:
            start = time.time()
            provider.query(f"Reply with just the number {i}", max_tokens=10)
            elapsed = time.time() - start
            print(f"   Query {i+1}: ✅ ({elapsed:.2f}s)")
            success += 1
        except Exception as e:
            print(f"   Query {i+1}: ❌ {str(e)[:40]}")
    
    total_time = time.time() - start_total
    print(f"\n   Results: {success}/10 succeeded in {total_time:.2f}s")
    
    passed = success >= 8  # Allow some failures
    print_result(passed, f"Stress test {'passed' if passed else 'failed'}")
    return passed


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="OpenRouter Provider Live Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/test_openrouter_live.py           # Run all tests
    python scripts/test_openrouter_live.py --quick   # Quick connectivity test only
        """
    )
    parser.add_argument('--quick', action='store_true', help='Run quick API test only')
    args = parser.parse_args()
    
    print("=" * 60)
    print("OpenRouter Provider Live Test Suite")
    print("=" * 60)
    
    if args.quick:
        success = test_quick_api()
        sys.exit(0 if success else 1)
    
    # Run all tests
    results = [
        ("Quick API", test_quick_api()),
        ("Async Query", test_async_query()),
        ("Key Rotation", test_key_rotation()),
        ("Key Banning", test_key_banning()),
        ("Quota Exhaustion", test_quota_exhaustion()),
        ("Stress Test", test_stress()),
    ]
    
    # Summary
    print_header("SUMMARY")
    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
