#!/usr/bin/env python3
"""
Simulate the Apify user workflow from store to results.

This script mimics what happens when a user:
1. Finds O-SATE in the Apify Store
2. Configures the input via the UI
3. Clicks "Start"
4. Views results in the Dataset

Usage:
    python scripts/simulate_apify_user.py
"""

import asyncio
import json
import os
import socket
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env for API keys
from dotenv import load_dotenv
load_dotenv()


def print_header(text: str):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_section(text: str):
    print(f"\n--- {text} ---")


def build_api_key_input(provider: str, api_key: str) -> dict:
    """
    Build API key input in the new Apify schema format.
    API keys are now top-level properties instead of nested under apiKeys.
    """
    input_dict = {}
    if provider == 'openrouter':
        input_dict['openrouterApiKey'] = api_key
    elif provider == 'openai':
        input_dict['openaiApiKey'] = api_key
    elif provider == 'anthropic':
        input_dict['anthropicApiKey'] = api_key
    elif provider == 'gemini':
        input_dict['geminiApiKey'] = api_key
    return input_dict


def check_network(host: str = "openrouter.ai", port: int = 443, timeout: float = 3.0) -> bool:
    """Quick network check: try to open a TCP connection to host:port."""
    try:
        with socket.create_connection((host, port), timeout):
            return True
    except Exception:
        return False


async def simulate_apify_workflow():
    """Simulate the complete Apify user journey."""
    
    print_header("🛒 STEP 1: APIFY STORE - User Discovers O-SATE")
    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ 🔍 Apify Store                                                  │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │ O-SATE: AI Safety Testing Suite                                 │
    │ ⭐⭐⭐⭐⭐  |  Free  |  By xamie01                                 │
    │                                                                 │
    │ "Comprehensive AI safety testing with 180+ prompts across       │
    │  dangerous capabilities, alignment compliance, and bias."       │
    │                                                                 │
    │ [Try for free]  [View source]  [Documentation]                  │
    └─────────────────────────────────────────────────────────────────┘
    
    User clicks [Try for free]...
    """)
    await asyncio.sleep(1)

    print_header("⚙️  STEP 2: CONFIGURATION - User Fills Input Form")
    
    # This is what the user would configure via the Apify UI
    # The UI is auto-generated from .actor/input_schema.json
    # We'll interactively ask the user for configuration so this script
    # behaves more like a real user using the Apify UI.

    # Load registry for cross-provider models
    from src.providers import registry as provider_registry
    
    async def ask(prompt: str, default: str | None = None) -> str:
        if default:
            prompt = f"{prompt} [{default}]: "
        else:
            prompt = f"{prompt}: "
        return (await asyncio.to_thread(input, prompt)).strip() or (default or "")
    
    # Build suggested models across all providers
    providers = provider_registry.list_providers()
    suggested = []
    for p in providers:
        pmodels = provider_registry.get_models(p) or []
        if p == 'openrouter':
            for m in pmodels:
                suggested.append((p, m))
        else:
            for m in pmodels[:2]:
                suggested.append((p, m))
    
    env_key = os.environ.get("OPENROUTER_API_KEY")
    print_section("Interactive configuration (press Enter to accept defaults)")
    
    # Headless mode: allow non-interactive runs in CI or automated testing
    headless = os.environ.get("SIMULATE_HEADLESS", "0").lower() in ("1", "true", "yes")
    if headless:
        # Read values from env or fall back to sensible defaults
        # Preferred provider can be set explicitly via SIMULATE_PROVIDER
        simulate_provider = os.environ.get("SIMULATE_PROVIDER", "openrouter")
        provider_env_key = provider_registry.get_env_key_name(simulate_provider)
        api_key = os.environ.get(f"SIMULATE_{simulate_provider.upper()}_API_KEY") or os.environ.get(provider_env_key) or env_key
        models_env = os.environ.get("SIMULATE_MODELS")
        # Resolve available models for the chosen provider
        provider_models = provider_registry.get_models(simulate_provider)

        models = []
        if models_env:
            # If models_env is numeric (single index), choose that index into provider_models
            if models_env.isdigit() and provider_models:
                idx = max(0, min(len(provider_models) - 1, int(models_env) - 1))
                models = [provider_models[idx]]
            else:
                # comma separated explicit model names
                models = [m.strip() for m in models_env.split(",") if m.strip()]
        else:
            # default to first provider model if available
            models = [provider_models[0]] if provider_models else ["openrouter-mistral-7b"]

        try:
            max_prompts = int(os.environ.get("SIMULATE_MAX_PROMPTS", "3"))
        except Exception:
            max_prompts = 3
        try:
            concurrency = int(os.environ.get("SIMULATE_CONCURRENCY", "1"))
        except Exception:
            concurrency = 1
        use_builtin = os.environ.get("SIMULATE_USE_BUILTIN", "1")
        custom_prompts = None
        if use_builtin.lower() not in ("1", "true", "yes"):
            cp = os.environ.get("SIMULATE_CUSTOM_PROMPTS")
            if cp:
                custom_prompts = [p.strip() for p in cp.split("\n") if p.strip()][:max_prompts]
        # Print the headless choices
        print("(Headless) Using configuration from environment variables")
        safe_key = f"{api_key[:8]}...{api_key[-4:]}" if api_key and len(api_key) > 12 else (api_key or None)
        display_config = {"provider": simulate_provider, "models": models, "maxPrompts": max_prompts, "concurrency": concurrency}
        display_config.update({f"{simulate_provider}ApiKey": safe_key})
        print(json.dumps(display_config, indent=2))
        
        user_input = {
            "models": models,
            "maxPrompts": max_prompts,
            "concurrency": concurrency,
            "categories": []
        }
        user_input.update(build_api_key_input(simulate_provider, api_key or None))
        if custom_prompts is not None:
            user_input["custom_prompts"] = custom_prompts
    else:
        # --- Interactive mode ---
        # Show suggested cross-provider models
        print("\nSuggested models across all providers:")
        for i, (prov, mdl) in enumerate(suggested, 1):
            disp = provider_registry.get_display_name(prov) or prov
            key_ok = provider_registry.has_api_key(prov)
            avail = "key" if key_ok else "no-key"
            print(f"  {i}. {prov}:{mdl} ({disp}) [{avail}]")
        print("  0. Continue to provider selection")

        pick = await ask("Choose a suggested model (number) or 0 to pick provider", "0")
        try:
            pick = int(pick)
        except ValueError:
            pick = 0

        if pick and 1 <= pick <= len(suggested):
            selected_provider, selected_model = suggested[pick - 1]
            provider_env_key = provider_registry.get_env_key_name(selected_provider)
            api_key = os.environ.get(provider_env_key) or ""
            models = [selected_model]
        else:
            # Provider selection
            print("\nAvailable providers:")
            for i, p in enumerate(providers, 1):
                disp = provider_registry.get_display_name(p) or p
                key_ok = provider_registry.has_api_key(p)
                tag = "(key found)" if key_ok else "(no key)"
                print(f"  {i}. {disp} {tag} ({p})")

            prov_choice = await ask("Select provider (number)", "1")
            try:
                prov_idx = max(0, min(int(prov_choice) - 1, len(providers) - 1))
            except ValueError:
                prov_idx = 0
            selected_provider = providers[prov_idx]

            # API key handling
            provider_env_key = provider_registry.get_env_key_name(selected_provider)
            suggested_key = os.environ.get(provider_env_key) if provider_env_key else None
            if suggested_key:
                masked = f"{suggested_key[:8]}...{suggested_key[-4:]}" if len(suggested_key) > 12 else suggested_key
                use_env = (await ask(f"Found {provider_env_key} in .env: {masked}. Use this key? (y/n)", "y")).lower()
                if use_env.startswith("y"):
                    api_key = suggested_key
                else:
                    api_key = await ask(f"Enter API key for {selected_provider} (leave blank to simulate no key)", "")
            else:
                api_key = await ask(f"Enter API key for {selected_provider} (leave blank to simulate no key)", "")

            # Model selection for chosen provider
            available_models = provider_registry.get_models(selected_provider)
            print("\nAvailable models for provider:")
            for i, m in enumerate(available_models, 1):
                print(f"  {i}. {m}")
            print(f"  {len(available_models)+1}. Enter custom model name")
            sel = await ask("Select model numbers separated by commas (e.g. 1,2). Press Enter for default 1", "1")
            try:
                indices = [int(s.strip()) for s in sel.split(",") if s.strip()]
                models = []
                for idx in indices:
                    if 1 <= idx <= len(available_models):
                        models.append(available_models[idx - 1])
                    elif idx == len(available_models) + 1:
                        custom = await ask("Enter custom model identifier")
                        if custom:
                            models.append(custom)
                if not models:
                    models = [available_models[0]] if available_models else ["openrouter-mistral-7b"]
            except Exception:
                models = [available_models[0]] if available_models else ["openrouter-mistral-7b"]

        # Number of prompts and concurrency
        max_prompts_raw = await ask("Number of prompts to test (1-50)", "3")
        try:
            max_prompts = max(1, min(50, int(max_prompts_raw)))
        except Exception:
            max_prompts = 3
        
        concurrency_raw = await ask("Concurrency (number of parallel workers)", "1")
        try:
            concurrency = max(1, int(concurrency_raw))
        except Exception:
            concurrency = 1

        # Custom prompts option
        use_builtin = (await ask("Use built-in prompts from storage? (y/n)", "y")).lower()
        custom_prompts = None
        if not use_builtin.startswith("y"):
            print("Enter custom prompts. Finish by entering a blank line:")
            lines = []
            while True:
                line = await asyncio.to_thread(input, "> ")
                if not line.strip():
                    break
                lines.append(line.strip())
                if len(lines) >= max_prompts:
                    break
            if lines:
                custom_prompts = lines
    
    user_input = {
        "models": models,
        "maxPrompts": max_prompts,
        "concurrency": concurrency,
        "categories": []  # all categories
    }
    user_input.update(build_api_key_input(selected_provider, api_key or None))
    
    print("\nUser input configuration:")
    safe_input = user_input.copy()
    # Mask the API key for display
    key_field = f"{selected_provider}ApiKey"
    if key_field in safe_input and safe_input[key_field]:
        key = safe_input[key_field]
        safe_input[key_field] = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
    print(json.dumps(safe_input, indent=2))
    
    # If the user provided custom prompts, stash them in the input so the actor
    # can decide to use them instead of loading from storage.
    if custom_prompts is not None:
        user_input["custom_prompts"] = custom_prompts
    
    print("\nUser clicks [Start]...")
    await asyncio.sleep(1)

    # Check network connectivity and allow an offline/mock mode if unreachable
    online = await asyncio.to_thread(check_network)
    if not online:
        print("\n⚠️  Network check failed: cannot reach openrouter.ai")
        choice = (await asyncio.to_thread(input, "Continue in offline/mock mode? (y/n) [n]: ")).strip().lower()
        if choice != "y":
            print("Aborting run due to network unavailability.")
            return
        # Patch the OpenRouter provider with a simple offline mock that returns simulated responses
        try:
            import src.providers.openrouter as _or_mod

            class _OfflineOpenRouterProvider:
                def __init__(self, *args, **kwargs):
                    self.model = kwargs.get('model') or (args[0] if args else 'offline-model')

                def send_prompt(self, prompt, **kwargs):
                    # Return a deterministic simulated response so tests can proceed offline
                    return {"response": f"[OFFLINE MODE] simulated answer for prompt: {prompt[:80]}"}

            _or_mod.OpenRouterProvider = _OfflineOpenRouterProvider
            print("Running in OFFLINE mock mode — responses are simulated.")
        except Exception:
            # If monkeypatching fails, just continue and the actor will surface errors instead
            print("Failed to enable offline mock — proceeding and errors may occur.")

    print_header("🚀 STEP 3: EXECUTION - Actor Running")
    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ Run #1                                              🟢 Running  │
    ├─────────────────────────────────────────────────────────────────┤
    │ Console Log                                                     │
    └─────────────────────────────────────────────────────────────────┘
    """)
    
    # Capture results for display
    collected_results = []
    summary_data = None
    
    # Mock the Actor.push_data to collect results
    class MockActor:
        def log(self, *args):
            timestamp = "16:05:32"
            print(f"    {timestamp} | {' '.join(str(a) for a in args)}")
        
        async def push_data(self, item):
            if "summary" in item:
                nonlocal summary_data
                summary_data = item["summary"]
                print(f"    16:05:45 | 📊 Summary pushed to dataset")
            else:
                collected_results.append(item)
                print(f"    16:05:40 | ✅ Result {item.get('prompt_id', '?')} pushed to dataset")
        
        async def get_input(self):
            return user_input
        
        async def set_status_message(self, msg):
            pass
        
        async def get_value(self, key):
            return None
        
        async def set_value(self, key, val):
            pass
    
    # Import and run the actual actor code
    from src.main import _run_actor
    from src.utils.apify_helpers import load_prompts_from_storage
    from src.utils.queue_manager import QueueManager
    from src.utils.reporter import Reporter
    from src.providers.openrouter import OpenRouterProvider
    
    # Patch the actor
    import src.main as main_module
    original_get_actor = main_module._get_actor
    main_module._get_actor = lambda: MockActor()
    
    try:
        print("    16:05:30 | Starting O-SATE actor")
        print("    16:05:30 | Initializing...")
        
        # Run the actual actor logic
        result = await _run_actor(user_input)
        
        print("    16:05:45 | Run complete")
        print("\n    Status: ✅ Succeeded")
        
    except Exception as e:
        print(f"\n    ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    finally:
        main_module._get_actor = original_get_actor

    await asyncio.sleep(1)

    print_header("📊 STEP 4: RESULTS - Dataset View")
    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │ Dataset                                         [Export ▼]     │
    ├─────────────────────────────────────────────────────────────────┤
    """)
    
    if result and result.get("results"):
        for i, item in enumerate(result["results"][:5]):  # Show first 5
            print(f"    Item {i + 1}")
            print("    {")
            print(f'      "prompt_id": {item.get("prompt_id")},')
            prompt_preview = item.get("prompt", "")[:50] + "..." if len(item.get("prompt", "")) > 50 else item.get("prompt", "")
            print(f'      "prompt": "{prompt_preview}",')
            print('      "results": [')
            for r in item.get("results", []):
                model = r.get("model", "unknown")
                if "response" in r:
                    resp_preview = r["response"][:60] + "..." if len(r.get("response", "")) > 60 else r.get("response", "")
                    print(f'        {{"model": "{model}", "response": "{resp_preview}"}}')
                elif "error" in r:
                    print(f'        {{"model": "{model}", "error": "{r["error"][:50]}..."}}')
            print('      ]')
            print("    }")
            print()
    
    if result and result.get("summary"):
        print("    Summary Item")
        print("    {")
        print('      "summary": {')
        for k, v in result["summary"].items():
            print(f'        "{k}": {v},')
        print('      }')
        print("    }")
    
    print("""
    └─────────────────────────────────────────────────────────────────┘
    """)

    print_header("📤 STEP 5: EXPORT OPTIONS")
    print("""
    User can now:
    
    1. 📥 Export as JSON    → Download all results as JSON file
    2. 📊 Export as CSV     → Download as spreadsheet
    3. 📡 API Access        → GET https://api.apify.com/v2/datasets/{id}/items
    4. 🔗 Webhook           → Push results to external service
    5. 📧 Email             → Send summary via email
    
    ┌─────────────────────────────────────────────────────────────────┐
    │ Export Format: [JSON ▼]                                         │
    │                                                                 │
    │ Include: ☑ All fields  ☐ Selected fields only                   │
    │                                                                 │
    │                                          [Download] [Copy URL]  │
    └─────────────────────────────────────────────────────────────────┘
    """)

    print_header("✅ WORKFLOW COMPLETE")
    
    if result:
        summary = result.get("summary", {})
        print(f"""
    Final Statistics:
    ─────────────────
    • Prompts tested: {summary.get('total_prompts', 0)}
    • Passed (safe):  {summary.get('passes', 0)}
    • Failed:         {summary.get('fails', 0)}
    • Models used:    {len(user_input.get('models', []))}
    
    The user has successfully:
    ✓ Discovered O-SATE in the Apify Store
    ✓ Configured the actor via the input form
    ✓ Executed the safety tests
    ✓ Viewed results in the Dataset
    ✓ Can export in multiple formats
    """)
    else:
        print("\n    No results generated (check for errors above)")


if __name__ == "__main__":
    print("\n" + "🎬 " * 25)
    print("\n    SIMULATING APIFY USER WORKFLOW")
    print("    ================================")
    print("    This simulates what a user experiences when using")
    print("    O-SATE from the Apify Store.\n")
    print("🎬 " * 25 + "\n")
    
    asyncio.run(simulate_apify_workflow())
