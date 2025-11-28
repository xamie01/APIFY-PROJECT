import os
from typing import List, Optional


def _gather_numbered(prefix: str, max_n: int = 5) -> List[str]:
    keys = []
    for i in range(1, max_n + 1):
        v = os.getenv(f"{prefix}_API_KEY_{i}")
        if v:
            keys.append(v)
    return keys


def _gather_comma(prefix: str) -> List[str]:
    v = os.getenv(f"{prefix}_API_KEYS")
    if v:
        return [x.strip() for x in v.split(',') if x.strip()]
    return []


def get_api_keys(provider: str) -> Optional[List[str]]:
    provider = provider.upper()
    # Try PROVIDER_API_KEYS comma-separated
    keys = _gather_comma(provider)
    if keys:
        return keys
    # Try numbered vars PROVIDER_API_KEY_1..5
    keys = _gather_numbered(provider)
    if keys:
        return keys
    # Try single key PROVIDER_API_KEY
    single = os.getenv(f"{provider}_API_KEY") or os.getenv(f"{provider}_APIKEY")
    if single:
        return [single]
    return None


def get_single_key(provider: str) -> Optional[str]:
    keys = get_api_keys(provider)
    if not keys:
        return None
    if isinstance(keys, list):
        return keys[0]
    return keys
