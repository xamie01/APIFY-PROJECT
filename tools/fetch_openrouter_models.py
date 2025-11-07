#!/usr/bin/env python3
"""
Fetch OpenRouter models and list "free" models that look like reasoning/chat/instruct models.
Saves JSON to outputs/openrouter_models.json and a plain list to outputs/openrouter_reasoning.txt

Run with your venv: venv/bin/python tools/fetch_openrouter_models.py
"""
import httpx
import json
from pathlib import Path

OUT_DIR = Path("outputs")
OUT_DIR.mkdir(exist_ok=True)

ENDPOINTS = [
    "https://openrouter.ai/api/v1/models",
    "https://openrouter.ai/api/models",
    "https://openrouter.ai/api/v1/list_models",
    "https://openrouter.ai/api/v1/catalog/models",
]

all_models = []

for url in ENDPOINTS:
    try:
        print(f"Trying {url}")
        r = httpx.get(url, timeout=15.0)
        if r.status_code != 200:
            print(f" -> {r.status_code} {r.text[:200]!r}")
            continue
        j = r.json()
        # normalize common shapes
        if isinstance(j, dict):
            # try common keys
            for key in ("models", "data", "results", "items"):
                if key in j and isinstance(j[key], list):
                    all_models.extend(j[key])
                    break
            else:
                # if dict of models
                if all(isinstance(v, dict) for v in j.values()):
                    for v in j.values():
                        all_models.append(v)
                else:
                    all_models.append(j)
        elif isinstance(j, list):
            all_models.extend(j)
    except Exception as e:
        print(f"Error fetching {url}: {e}")

# normalize entries to dicts with id/name/description/tags
normalized = []
for m in all_models:
    if not isinstance(m, dict):
        continue
    mid = m.get("id") or m.get("model") or m.get("name") or m.get("model_id")
    desc = (m.get("description") or m.get("summary") or "") if isinstance(m, dict) else ""
    tags = []
    if isinstance(m.get("tags"), list):
        tags = [t.lower() for t in m.get("tags")]
    normalized.append({"id": mid, "desc": desc, "tags": tags, "raw": m})

# heuristics to find free + reasoning models
reason_keywords = ("instruct", "reason", "chat", "assistant", "llama", "gemma", "gpt", "qwen", "mistral", "phi", "deepseek", "llam", "instruction")
candidates = []
for n in normalized:
    if not n["id"]:
        continue
    nid = n["id"].lower()
    desc = (n["desc"] or "").lower()
    tags = n.get("tags") or []
    is_free = ("free" in nid) or any("free" in t for t in tags) or (":free" in nid)
    is_reason = any(k in nid for k in reason_keywords) or any(k in desc for k in reason_keywords)
    if is_free and is_reason:
        candidates.append(n)

# deduplicate by id
seen = set()
uniq = []
for c in candidates:
    if c["id"] in seen:
        continue
    seen.add(c["id"])
    uniq.append(c)

OUT_JSON = OUT_DIR / "openrouter_models.json"
OUT_TXT = OUT_DIR / "openrouter_reasoning.txt"
OUT_JSON.write_text(json.dumps({"normalized": normalized, "candidates": uniq}, indent=2), encoding="utf-8")
with OUT_TXT.open("w", encoding="utf-8") as f:
    for c in uniq:
        f.write(f"{c['id']}\t# {c.get('desc','')[:200].replace('\n',' ')}\n")

print("Wrote:", OUT_JSON, OUT_TXT)
print(f"Found {len(uniq)} candidate free reasoning models")
