#!/usr/bin/env python3
"""Check OpenRouter models for text responses and measure response time.

Reads `data/openrouter_models.json` (created by fetch_openrouter_free_models.py) or
falls back to calling OpenRouter /models. Sends a riddle prompt to each model,
measures response time and heuristically scores the response quality. Outputs
the top 15 models by combined score (quality/time) to `data/openrouter_model_checks.json`.

Features:
- Resume support: skips models already present in previous results
- Exponential backoff on 429 responses
- Partial result persistence after each batch

Usage:
    export OPENROUTER_API_KEY=sk-...
    python scripts/check_models_text_speed.py

Environment variables:
    CHECK_MODELS_LIMIT - max number of models to test (default 30)
    CHECK_TIMEOUT - per-request timeout seconds (default 12)
    CHECK_RESUME - if set to 1, skip models already tested in output file (default 1)
"""
import json
import os
import time
from typing import List, Dict, Any

import httpx
from dotenv import load_dotenv
load_dotenv()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT, 'data', 'openrouter_models.json')
OUT_FILE = os.path.join(ROOT, 'data', 'openrouter_model_checks.json')

DEFAULT_PROMPT = (
    "Riddle: I speak without a mouth and hear without ears. I have nobody, "
    "but I come alive with wind. What am I? Answer succinctly and explain in two sentences."
)


def load_models() -> List[str]:
    if os.path.exists(DATA_FILE):
        j = json.load(open(DATA_FILE))
        ms = [m.get('id') for m in j.get('models', []) if m.get('id')]
        if ms:
            return ms
    # fallback: call /models
    key = os.environ.get('OPENROUTER_API_KEY')
    if not key:
        raise RuntimeError('OPENROUTER_API_KEY not set')
    base = os.environ.get('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1').rstrip('/')
    with httpx.Client(timeout=10.0) as client:
        r = client.get(f"{base}/models", headers={'Authorization': f'Bearer {key}'}, timeout=10.0)
        r.raise_for_status()
        data = r.json()
        items = data.get('data') if isinstance(data, dict) and 'data' in data else data
        return [it.get('id') for it in items if it.get('id')]


def score_response(text: str) -> float:
    if not text:
        return 0.0
    t = text.strip()
    # quality based on length and presence of alphabetic chars
    alpha = sum(1 for c in t if c.isalpha())
    words = len(t.split())
    score = min(1.0, alpha / 200.0 + words / 200.0)
    # penalize obviously short/or error responses
    if words < 3:
        score *= 0.3
    return score


def test_model(model_id: str, api_key: str, timeout: int, max_retries: int = 3) -> Dict[str, Any]:
    base = os.environ.get('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1').rstrip('/')
    url = f"{base}/chat/completions"
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    payload = {
        'model': model_id,
        'messages': [{'role': 'user', 'content': DEFAULT_PROMPT}],
        'max_tokens': 200,
    }
    result = {'model': model_id, 'ok': False, 'error': None, 'response': None, 'time': None, 'score': 0.0}
    backoff = 1.0
    for attempt in range(1, max_retries + 1):
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=timeout) as client:
                r = client.post(url, json=payload, headers=headers)
                elapsed = time.perf_counter() - start
                result['time'] = elapsed
                if r.status_code == 200:
                    j = r.json()
                    # openrouter returns choices -> message -> content
                    text = None
                    try:
                        text = j.get('choices', [{}])[0].get('message', {}).get('content')
                    except Exception:
                        text = None
                    if not text:
                        # try alternative fields
                        text = j.get('output') or j.get('text') or ''
                    result['response'] = text
                    result['score'] = score_response(text)
                    result['ok'] = True
                    return result
                elif r.status_code in (429, 503):
                    result['error'] = f"HTTP {r.status_code}: {r.text[:200]}"
                    if attempt < max_retries:
                        print(f"    Rate limited ({r.status_code}), retrying in {backoff:.1f}s...")
                        time.sleep(backoff)
                        backoff *= 2
                        continue
                    return result
                else:
                    result['error'] = f"HTTP {r.status_code}: {r.text[:200]}"
                    return result
        except Exception as e:
            result['error'] = str(e)
            if attempt < max_retries:
                time.sleep(backoff)
                backoff *= 2
                continue
    return result


def load_previous_results() -> Dict[str, Any]:
    """Load previously saved results to enable resume."""
    if os.path.exists(OUT_FILE):
        try:
            return json.load(open(OUT_FILE))
        except Exception:
            pass
    return {}


def save_results(results: List[Dict], tested_models: set):
    """Save partial results (allows resume on interrupt)."""
    ranked = [t for t in results if t['ok'] and t['time'] and t['time'] > 0]
    ranked.sort(key=lambda x: (x['score'] / x['time']), reverse=True)
    top = ranked[:15]
    out = {'tested_at': time.time(), 'results': results, 'top': top}
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)


def main():
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print('Set OPENROUTER_API_KEY in environment')
        return
    models = load_models()
    limit = int(os.environ.get('CHECK_MODELS_LIMIT', '30'))
    timeout = int(os.environ.get('CHECK_TIMEOUT', '12'))
    resume = os.environ.get('CHECK_RESUME', '1') == '1'
    if not models:
        print('No models found to test')
        return

    # Resume support: load previous results and skip already-tested models
    prev = load_previous_results()
    prev_results = prev.get('results', [])
    already_tested = {r['model'] for r in prev_results}
    tests = list(prev_results)  # start with existing results

    to_test = [m for m in models if m not in already_tested][:limit] if resume else models[:limit]
    print(f'Resume={resume}. Already tested={len(already_tested)}. To test={len(to_test)} (limit={limit})')

    for i, m in enumerate(to_test):
        print(f'[{i+1}/{len(to_test)}] Testing {m}')
        res = test_model(m, api_key, timeout)
        status = 'ok' if res['ok'] else 'FAIL'
        tm = res.get('time') or 0
        print(f"    -> {status}, time={tm:.2f}s score={res['score']:.2f} err={res.get('error') or ''}")
        tests.append(res)
        # Save partial results after each model (enables safe resume)
        save_results(tests, already_tested | {m})
        # small pause to avoid spamming
        time.sleep(0.3)

    # Final ranking
    ranked = [t for t in tests if t['ok'] and t['time'] and t['time'] > 0]
    ranked.sort(key=lambda x: (x['score'] / x['time']), reverse=True)
    top = ranked[:15]
    save_results(tests, already_tested | set(to_test))
    print('\nTop models:')
    for i, t in enumerate(top, 1):
        print(f"{i}. {t['model']} - time={t['time']:.2f}s score={t['score']:.2f}")
    print(f'Wrote results to {OUT_FILE}')


if __name__ == '__main__':
    main()
