#!/usr/bin/env python3
"""
Test models listed in config/default_config.yaml (openrouter_models).
For each model this script will attempt up to 3 tries with 5s interval.
Saves outputs to outputs/test_models/<model>.out
"""
from pathlib import Path
import time
import json
import traceback
import sys
import os

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.utils import load_env_variables, load_config
from src.target_ai_wrapper import TargetAIWrapper


def safe_model_name(raw: str) -> str:
    # Accept entries like "openrouter-llama-3b" or just "llama-3b"
    if raw.startswith("openrouter-"):
        return raw
    return f"openrouter-{raw}"


def run_test(prompt: str, model_target: str, attempts: int = 3, interval: int = 5):
    out_dir = ROOT / "outputs" / "test_models"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / (model_target.replace('/', '_').replace(':', '_') + ".out")

    result_meta = {
        "model_target": model_target,
        "attempts": attempts,
        "interval_seconds": interval,
        "start_time": time.time(),
        "success": False,
        "error": None,
        "response": None,
    }

    last_exc = None
    for attempt in range(1, attempts + 1):
        print(f"[{model_target}] Attempt {attempt}/{attempts}...")
        try:
            wrapper = TargetAIWrapper(model_target)
            resp = wrapper.query(prompt, temperature=0.2, max_tokens=200)
            result_meta.update({
                "success": True,
                "attempt": attempt,
                "response": resp,
                "end_time": time.time(),
            })
            out_file.write_text(json.dumps(result_meta, indent=2), encoding="utf-8")
            print(f"[{model_target}] Success (saved to {out_file})")
            return True
        except Exception as e:
            last_exc = e
            tb = traceback.format_exc()
            print(f"[{model_target}] Error on attempt {attempt}: {e}\n{tb}")
            result_meta["error"] = {
                "attempt": attempt,
                "message": str(e),
                "traceback": tb,
            }
            # save intermediate failure
            out_file.write_text(json.dumps(result_meta, indent=2), encoding="utf-8")
            if attempt < attempts:
                print(f"[{model_target}] Waiting {interval}s before retrying...")
                time.sleep(interval)

    # exhausted OpenRouter attempts -> attempt global fallback (Gemini) if configured
    cfg = load_config()
    fb = cfg.get('target_ai', {}).get('fallback_model') or 'gemini-pro'
    google_key = None
    try:
        from src.utils import get_api_key
        google_key = get_api_key('google') or os.getenv('GOOGLE_API_KEY')
    except Exception:
        google_key = os.getenv('GOOGLE_API_KEY')

    if google_key:
        print(f"[{model_target}] OpenRouter attempts exhausted. Attempting global fallback to {fb} (Gemini)...")
        try:
            gem_wrapper = TargetAIWrapper(fb)
            resp = gem_wrapper.query(prompt, temperature=0.2, max_tokens=200)
            result_meta.update({
                "success": True,
                "fallback_to": fb,
                "response": resp,
                "end_time": time.time(),
            })
            out_file.write_text(json.dumps(result_meta, indent=2), encoding="utf-8")
            print(f"[{model_target}] Fallback to {fb} succeeded (saved to {out_file})")
            return True
        except Exception as e:
            tb = traceback.format_exc()
            result_meta.update({
                "success": False,
                "fallback_error": str(e),
                "fallback_traceback": tb,
                "end_time": time.time()
            })
            out_file.write_text(json.dumps(result_meta, indent=2), encoding="utf-8")
            print(f"[{model_target}] Fallback to {fb} failed: {e}")

    # exhausted
    result_meta.update({"success": False, "end_time": time.time(), "last_error": str(last_exc)})
    out_file.write_text(json.dumps(result_meta, indent=2), encoding="utf-8")
    print(f"[{model_target}] Failed after {attempts} attempts. See {out_file}")
    return False


def main():
    load_env_variables()
    cfg = load_config()

    models = cfg.get("target_ai", {}).get("openrouter_models")
    if not models:
        print("No openrouter_models found in config/default_config.yaml")
        return 1

    prompt = "In one sentence, explain what AI safety is and why it matters."
    attempts = 3
    interval = 5

    summary = {"total": len(models), "succeeded": [], "failed": []}

    for raw in models:
        model = safe_model_name(raw)
        ok = run_test(prompt, model, attempts=attempts, interval=interval)
        if ok:
            summary["succeeded"].append(model)
        else:
            summary["failed"].append(model)

    print("\n== Summary ==")
    print(f"Total models: {summary['total']}")
    print(f"Succeeded: {len(summary['succeeded'])}")
    for m in summary['succeeded']:
        print(f"  - {m}")
    print(f"Failed: {len(summary['failed'])}")
    for m in summary['failed']:
        print(f"  - {m}")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
