#!/usr/bin/env python3
"""Fetch available OpenRouter models and save free text/reasoning models.

Saves a JSON file at `data/openrouter_models.json` which is used by the
provider registry when present. Run this script after you update your
`OPENROUTER_API_KEY` in the environment or .env file.

Usage:
    python scripts/fetch_openrouter_free_models.py
"""
import json
import os
import sys
from typing import Any, Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

import httpx

OUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "openrouter_models.json")


def _extract_id(item: Dict[str, Any]) -> str:
    return item.get("id") or item.get("model") or item.get("name") or item.get("slug") or ""


def _is_text_model(item: Dict[str, Any]) -> bool:
    # Heuristic: look at tags/capabilities/title/name for text/chat/instruction
    text_terms = ["chat", "instruction", "instruct", "text", "dialog", "conversation", "qa", "reason", "gpt", "llama", "mistral"]
    hay = " ".join(
        [
            str(item.get("title", "")),
            str(item.get("display_name", "")),
            str(item.get("id", "")),
            str(item.get("model", "")),
            " ".join(item.get("tags", []) if isinstance(item.get("tags"), list) else []),
            " ".join(item.get("capabilities", []) if isinstance(item.get("capabilities"), list) else []),
        ]
    ).lower()
    for t in text_terms:
        if t in hay:
            return True
    return False


def _is_free(item: Dict[str, Any]) -> bool:
    # Try common flags; if absent, look for pricing or free tag keywords
    try:
        if item.get("is_free") is True or item.get("free") is True:
            return True
        pricing = item.get("pricing")
        # If pricing is a dict, consider free if any numeric/string value equals zero
        if isinstance(pricing, dict):
            for v in pricing.values():
                try:
                    if isinstance(v, (int, float)) and float(v) == 0:
                        return True
                    if isinstance(v, str) and float(v) == 0:
                        return True
                except Exception:
                    # ignore non-numeric strings
                    pass
        else:
            pricing_s = str(pricing or "").lower()
            if "free" in pricing_s:
                return True
        tags = item.get("tags") or []
        if any("free" in str(t).lower() for t in tags):
            return True
        # Some providers embed availability into attributes
        meta = str(item.get("metadata", "") or "").lower()
        if "free" in meta:
            return True
        # Relaxed check: sometimes free is not labeled clearly — check whole payload for 'free'
        payload = json.dumps(item).lower()
        if "\"free\"" in payload or " free " in payload:
            return True
        # If no explicit free marker is present, consider models with no pricing field
        # as potentially free (relaxed heuristic). We'll still filter by text models later.
        if not item.get("pricing") and not item.get("price") and not item.get("cost"):
            return True
    except Exception:
        return False
    return False


def fetch_models(api_key: str) -> List[Dict[str, Any]]:
    url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/") + "/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(url, headers=headers)
            r.raise_for_status()
            data = r.json()
            # OpenRouter returns object with `data` array
            items = data.get("data") if isinstance(data, dict) and "data" in data else data
            if not isinstance(items, list):
                print("Unexpected /models response format", file=sys.stderr)
                return []
            results = []
            for it in items:
                mid = _extract_id(it)
                if not mid:
                    continue
                if _is_text_model(it) and _is_free(it):
                    results.append({"id": mid, "title": it.get("title") or it.get("display_name") or "", "raw": it})
            return results
    except httpx.HTTPStatusError as e:
        print(f"HTTP error fetching models: {e}", file=sys.stderr)
        try:
            print(e.response.text, file=sys.stderr)
        except Exception:
            pass
        return []
    except Exception as e:
        print(f"Error fetching models: {e}", file=sys.stderr)
        return []


def save_models(models: List[Dict[str, Any]]):
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump({"fetched_at": __import__("time").time(), "models": models}, f, indent=2)
    print(f"Saved {len(models)} models to {OUT_PATH}")


def main():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Please set OPENROUTER_API_KEY in your environment or .env", file=sys.stderr)
        sys.exit(2)
    models = fetch_models(api_key)
    if not models:
        print("No free text models found or failed to fetch.")
    else:
        for m in models:
            print("-", m["id"], "-", m.get("title", ""))
    save_models(models)


if __name__ == "__main__":
    main()
