#!/usr/bin/env python3
"""
Interactive Apify Actor Test - Actually runs the actor with real API calls.

Usage:
    python scripts/interactive_actor_test.py
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.providers import registry as provider_registry
from src.utils.apify_helpers import count_prompts, get_prompt_categories


def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')


def get_user_input(prompt: str, default: str = "") -> str:
    """Get input with default value."""
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()


def get_int_input(prompt: str, default: int) -> int:
    """Get integer input with default."""
    try:
        result = input(f"{prompt} [{default}]: ").strip()
        return int(result) if result else default
    except ValueError:
        return default


async def run_interactive_test():
    """Interactive actor test with real API calls."""
    
    clear_screen()
    print("=" * 60)
    print("  O-SATE: AI Safety Testing Suite")
    print("  Interactive Actor Test")
    print("=" * 60)
    
    # Show available prompts
    prompt_counts = count_prompts()
    total_prompts = prompt_counts.get('_total', 0)
    categories = get_prompt_categories()
    
    print("\n📊 Available Prompts:")
    for cat in categories:
        cnt = prompt_counts.get(cat, 0)
        print(f"   - {cat}: {cnt} prompts")
    print(f"   TOTAL: {total_prompts} prompts")
    
    # Check API key
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("\n❌ No OPENROUTER_API_KEY found!")
        print("   Set it in .env file first.")
        return
    
    print(f"\n✅ API Key found: {api_key[:8]}...{api_key[-4:]}")
    
    # Configuration
    print("\n" + "-" * 60)
    print("CONFIGURATION")
    print("-" * 60)
    # Suggested cross-provider models (includes OpenRouter top models if present)
    providers = provider_registry.list_providers()
    suggested = []
    for p in providers:
        models = provider_registry.get_models(p) or []
        # take a couple of examples per provider, but include all OpenRouter top models
        if p == 'openrouter':
            for m in models:
                suggested.append((p, m))
        else:
            for m in models[:2]:
                suggested.append((p, m))

    print("\nSuggested models across providers:")
    for i, (prov, mdl) in enumerate(suggested, 1):
        disp = provider_registry.get_display_name(prov) or prov
        key_ok = provider_registry.has_api_key(prov)
        avail = "key" if key_ok else "no-key"
        print(f"  {i}. {prov}:{mdl} ({disp}) [{avail}]")
    print("  0. Continue to provider selection")

    pick = get_int_input("Choose a suggested model (number) or 0 to pick provider", 0)
    if pick and 1 <= pick <= len(suggested):
        selected_provider, selected_model = suggested[pick - 1]
        # provider key from env if present; will prompt later if absent
        provider_env_key = provider_registry.get_env_key_name(selected_provider)
        provider_key = os.environ.get(provider_env_key) if provider_env_key else None
    else:
        # Provider selection
        print("\nAvailable providers:")
        for i, p in enumerate(providers, 1):
            disp = provider_registry.get_display_name(p) or p
            key_ok = provider_registry.has_api_key(p)
            tag = "(key found)" if key_ok else "(no key)"
            print(f"  {i}. {disp} {tag} ({p})")

        prov_choice = get_int_input("Select provider (number)", 1)
        prov_idx = min(max(prov_choice - 1, 0), len(providers) - 1)
        selected_provider = providers[prov_idx]

    # Suggest env key for provider and allow entering a custom key if not already populated
    provider_env_key = provider_registry.get_env_key_name(selected_provider)
    suggested_key = os.environ.get(provider_env_key) if provider_env_key else None
    if suggested_key:
        if 'provider_key' not in locals() or not provider_key:
            print(f"\nFound {provider_env_key} in environment: {suggested_key[:8]}...{suggested_key[-4:]}")
            use_env = input("Use this key? (y/n) [y]: ").strip().lower() or 'y'
            if use_env.startswith('y'):
                provider_key = suggested_key
            else:
                provider_key = input(f"Enter API key for {selected_provider} (leave blank to simulate no key): ").strip() or None
    else:
        # If provider_key was selected earlier (via suggested model) keep it; otherwise prompt
        if 'provider_key' not in locals() or not provider_key:
            provider_key = input(f"Enter API key for {selected_provider} (leave blank to simulate no key): ").strip() or None

    # If selected_model already set (via suggested chooser), skip; otherwise prompt
    if 'selected_model' not in locals() or not selected_model:
        available_models = provider_registry.get_models(selected_provider)
        print("\nAvailable models for provider:")
        for i, m in enumerate(available_models, 1):
            print(f"  {i}. {m}")
        print(f"  {len(available_models)+1}. Enter custom model name")

        model_choice = get_int_input("Select model (number)", 1)
        if 1 <= model_choice <= len(available_models):
            selected_model = available_models[model_choice - 1]
        else:
            selected_model = input("Enter custom model identifier: ").strip()

    # Prompt count selection - show total available
    print(f"\n📝 Total prompts available: {total_prompts}")
    max_prompts = get_int_input(f"Number of prompts to test (1-{total_prompts}, 0=all)", 10)
    if max_prompts == 0:
        max_prompts = total_prompts
    max_prompts = min(max(max_prompts, 1), total_prompts)
    
    print("\n" + "-" * 60)
    print("YOUR CONFIGURATION")
    print("-" * 60)
    print(f"  Provider:    {selected_provider}")
    print(f"  Model:       {selected_model}")
    print(f"  Prompts:     {max_prompts} / {total_prompts}")
    key_preview = (provider_key[:8] + '...' + provider_key[-4:]) if provider_key and len(provider_key) > 12 else (provider_key or 'none')
    print(f"  API Key:     {key_preview}")
    
    confirm = input("\nStart test? (y/n) [y]: ").strip().lower()
    if confirm == 'n':
        print("Cancelled.")
        return
    
    # Run the actor
    print("\n" + "=" * 60)
    print("  RUNNING ACTOR")
    print("=" * 60 + "\n")
    
    # Build input_config in a provider-aware way. Most of the actor code expects
    # a flat `models` list and `apiKeys` map; we populate those using the
    # selected provider so the actor will use the correct provider key and model.
    input_config = {
        "models": [selected_model],
        "maxPrompts": max_prompts,
        "concurrency": 1,
        "apiKeys": {selected_provider: provider_key}
    }
    
    # Results collector
    results = []
    
    class LiveActor:
        """Actor that prints results live."""
        def log(self, *args):
            print(f"[LOG] {' '.join(str(a) for a in args)}")
        
        async def push_data(self, item):
            if "summary" in item:
                print(f"\n📊 Summary: {item['summary']}")
            else:
                results.append(item)
                pid = item.get('prompt_id', '?')
                prompt_short = item.get('prompt', '')[:40] + '...'
                print(f"\n✅ Prompt {pid}: {prompt_short}")
                
                for r in item.get('results', []):
                    if 'response' in r:
                        resp = r['response'][:100].replace('\n', ' ')
                        print(f"   → {r['model']}: {resp}...")
                    elif 'error' in r:
                        print(f"   → {r['model']}: ❌ {r['error'][:60]}")
        
        async def get_input(self):
            return input_config
        
        async def set_status_message(self, msg):
            pass
        
        async def get_value(self, key):
            return None
        
        async def set_value(self, key, val):
            pass
    
    # Patch and run
    import src.main as main_module
    original = main_module._get_actor
    main_module._get_actor = lambda: LiveActor()
    
    try:
        from src.main import _run_actor
        result = await _run_actor(input_config)
        
        print("\n" + "=" * 60)
        print("  RESULTS")
        print("=" * 60)
        
        if result:
            summary = result.get('summary', {})
            print(f"\n  Total prompts: {summary.get('total_prompts', 0)}")
            print(f"  Passed:        {summary.get('passes', 0)}")
            print(f"  Failed:        {summary.get('fails', 0)}")
            
            # Show detailed results
            print("\n" + "-" * 60)
            print("DETAILED RESPONSES")
            print("-" * 60)
            
            for item in result.get('results', []):
                print(f"\n[Prompt {item.get('prompt_id')}]")
                print(f"  Q: {item.get('prompt', '')[:80]}...")
                for r in item.get('results', []):
                    if 'response' in r:
                        print(f"  A: {r['response'][:200]}...")
                    elif 'error' in r:
                        print(f"  ERROR: {r['error']}")
        
        print("\n" + "=" * 60)
        print("  ✅ TEST COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        main_module._get_actor = original


if __name__ == "__main__":
    asyncio.run(run_interactive_test())
