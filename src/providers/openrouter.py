import asyncio
import logging
import os
from typing import Optional
import httpx
import time
import socket

logger = logging.getLogger(__name__)


def _mask_key(key: str) -> str:
    """Mask API key for safe logging (show first 4 and last 4 chars)."""
    if not key or len(key) <= 8:
        return '***'
    return f"{key[:4]}...{key[-4:]}"


def _resolve_api_keys_runtime():
    # 1) Only read from the current process environment first (respect test deletions)
    keys = []
    raw = os.environ.get('OPENROUTER_API_KEYS')
    if raw:
        keys.extend([k.strip() for k in raw.split(',') if k.strip()])
    for i in range(1, 6):
        v = os.environ.get(f'OPENROUTER_API_KEY_{i}')
        if v:
            keys.append(v)
    single = os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENROUTER_APIKEY')
    if single:
        keys.append(single)
    if keys:
        seen = set(); out = []
        for k in keys:
            if k not in seen:
                seen.add(k); out.append(k)
        return out

    # 2) If not present in process env, prefer a monkeypatched taw.get_api_keys if already loaded
    try:
        import sys
        taw = sys.modules.get('src.target_ai_wrapper')
        if taw is not None:
            getter = getattr(taw, 'get_api_keys', None)
            if callable(getter):
                # Only call getter if it appears monkeypatched (module not the original)
                getter_mod = getattr(getter, '__module__', '')
                if getter_mod and getter_mod != 'src.target_ai_wrapper':
                    try:
                        keys = getter('openrouter') or getter('OPENROUTER')
                    except TypeError:
                        keys = getter('openrouter')
                    if keys:
                        return keys
    except Exception:
        pass

    return None


class OpenRouterProvider:
    def __init__(self, model: str = 'openrouter-mistral-7b', api_keys: Optional[list] = None):
        self.model = model
        provided_keys = api_keys if api_keys is not None else _resolve_api_keys_runtime()
        if isinstance(provided_keys, str):
            provided_keys = [provided_keys]
        if not provided_keys:
            raise RuntimeError('No OpenRouter API key configured')
        self.api_keys = list(provided_keys)
        self._key_idx = 0
        # Use index-based tracking to handle duplicate keys in testing
        self._banned = {}  # idx -> ban_until timestamp
        self._request_count = {}  # idx -> count
        self.requests_per_key = 45
        self._client = None
        self._lock = asyncio.Lock()
        
        logger.info(
            f"OpenRouterProvider initialized: model={model}, "
            f"keys={len(self.api_keys)}, quota={self.requests_per_key}/key"
        )

    def _current_key(self):
        return self.api_keys[self._key_idx % len(self.api_keys)]

    def _get_next_key(self) -> Optional[tuple]:
        """Returns (key_index, key_string) or None if all keys are banned."""
        now = time.time()
        n = len(self.api_keys)
        for i in range(n):
            idx = (self._key_idx + i) % n
            ban_until = self._banned.get(idx)
            if ban_until and ban_until > now:
                remaining = int(ban_until - now)
                logger.debug(f"Key {idx} ({_mask_key(self.api_keys[idx])}) banned for {remaining}s, skipping")
                continue
            # Check quota
            rc = self._request_count.get(idx, 0)
            if rc >= self.requests_per_key:
                logger.debug(f"Key {idx} ({_mask_key(self.api_keys[idx])}) quota exhausted ({rc}/{self.requests_per_key}), skipping")
                continue
            self._key_idx = idx
            return (idx, self.api_keys[idx])
        logger.warning("No available keys: all banned or quota exhausted")
        return None

    def query(self, prompt: str, **kwargs) -> str:
        per_key_retries = int(kwargs.get('per_key_retries', 3))
        initial_backoff = float(kwargs.get('initial_backoff', 1.0))
        total_keys = len(self.api_keys)
        start_time = time.time()

        logger.debug(f"Query started: model={self.model}, prompt_len={len(prompt)}")

        attempts = 0
        while attempts < total_keys:
            result = self._get_next_key()
            if not result:
                logger.error("All OpenRouter keys exhausted or banned")
                raise RuntimeError('All OpenRouter keys exhausted or banned')
            
            key_idx, key = result
            logger.debug(f"Using key {key_idx} ({_mask_key(key)}), requests so far: {self._request_count.get(key_idx, 0)}")

            backoff = initial_backoff
            for attempt in range(1, per_key_retries + 1):
                try:
                    import sys
                    openai = sys.modules.get('openai')
                    if openai and hasattr(openai, 'OpenAI'):
                        client = openai.OpenAI(api_key=key, base_url='https://openrouter.ai/api/v1')
                        response = client.chat.completions.create(
                            model=self.model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=kwargs.get('temperature', 0.7),
                            max_tokens=kwargs.get('max_tokens', 2000),
                        )
                        self._request_count[key_idx] = self._request_count.get(key_idx, 0) + 1
                        elapsed = time.time() - start_time
                        logger.info(f"Query success: key={key_idx}, elapsed={elapsed:.2f}s, total_requests={self._request_count[key_idx]}")
                        return response.choices[0].message.content

                    # fallback HTTP path (try multiple base URLs to avoid single-host DNS failure)
                    base_candidates = []
                    # allow explicit override
                    env_base = os.environ.get('OPENROUTER_BASE_URL')
                    if env_base:
                        base_candidates.append(env_base.rstrip('/'))
                    # prefer openrouter.ai host (observed to resolve) then api.openrouter.ai
                    base_candidates.extend([
                        'https://openrouter.ai/api/v1',
                        'https://api.openrouter.ai/v1',
                    ])

                    last_exc = None
                    for base in base_candidates:
                        try:
                            # quick DNS/resolve check
                            host = base.split('://', 1)[-1].split('/', 1)[0]
                            try:
                                socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
                            except Exception:
                                # skip this base if it doesn't resolve
                                logger.debug(f"Host {host} did not resolve; skipping base {base}")
                                continue

                            url = f"{base.rstrip('/')}/chat/completions"
                            r = httpx.post(url, json={
                                'model': self.model,
                                'messages': [{'role': 'user', 'content': prompt}],
                                'max_tokens': 512,
                            }, headers={'Authorization': f'Bearer {key}'}, timeout=30.0)

                            if r.status_code == 200:
                                data = r.json()
                                self._request_count[key_idx] = self._request_count.get(key_idx, 0) + 1
                                elapsed = time.time() - start_time
                                logger.info(f"Query success (httpx): key={key_idx}, elapsed={elapsed:.2f}s, base={base}")
                                return data.get('choices', [{}])[0].get('message', {}).get('content', '')
                            elif r.status_code in (429, 503):
                                logger.warning(f"Rate limit {r.status_code} on key {key_idx}, attempt {attempt}/{per_key_retries} (base={base})")
                                if attempt < per_key_retries:
                                    logger.debug(f"Retrying in {backoff}s...")
                                    time.sleep(backoff)
                                    backoff *= 2
                                    continue
                                logger.warning(f"Banning key {key_idx} ({_mask_key(key)}) for 1 hour")
                                self._banned[key_idx] = time.time() + 3600
                                break
                            else:
                                r.raise_for_status()

                        except httpx.RequestError as re:
                            last_exc = re
                            logger.debug(f"HTTP request error for base {base}: {re}")
                            # try next base
                            continue
                        except Exception as e:
                            last_exc = e
                            logger.error(f"Unexpected error when calling base {base}: {e}")
                            raise

                    # If we exhausted base_candidates without returning, treat as failure for this key
                    if last_exc:
                        # If it looks like DNS/connection issue, surface as that to potentially trigger offline/mock flows
                        raise last_exc
                    # otherwise continue to next key
                except Exception as e:
                    msg = str(e).lower()
                    if '429' in msg or 'rate limit' in msg or 'too many requests' in msg or 'rate_limited' in msg:
                        logger.warning(f"Rate limit exception on key {key_idx}, attempt {attempt}/{per_key_retries}: {str(e)[:100]}")
                        if attempt < per_key_retries:
                            logger.debug(f"Retrying in {backoff}s...")
                            time.sleep(backoff)
                            backoff *= 2
                            continue
                        logger.warning(f"Banning key {key_idx} ({_mask_key(key)}) for 1 hour")
                        self._banned[key_idx] = time.time() + 3600
                        break
                    else:
                        logger.error(f"Unexpected error on key {key_idx}: {e}")
                        raise
            attempts += 1

        logger.error("All OpenRouter keys exhausted or failed after all attempts")
        raise RuntimeError('All OpenRouter keys exhausted or failed')

    async def query_async(self, prompt: str) -> str:
        return await asyncio.to_thread(self.query, prompt)

    def get_available_models(self) -> list:
        """Fetch /models from OpenRouter using the first available key.

        Returns a list of model ids (strings). On error returns an empty list.
        """
        key = None
        if self.api_keys:
            key = self.api_keys[0]
        if not key:
            return []
        base = os.environ.get('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1').rstrip('/')
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.get(f"{base}/models", headers={'Authorization': f'Bearer {key}'})
                if r.status_code == 401:
                    logger.error('OpenRouter returned 401 Unauthorized when listing models — check API key')
                    return []
                if r.status_code == 429:
                    logger.warning('OpenRouter returned 429 Too Many Requests when listing models')
                    return []
                r.raise_for_status()
                data = r.json()
                items = data.get('data') if isinstance(data, dict) and 'data' in data else data
                if not isinstance(items, list):
                    return []
                out = []
                for it in items:
                    mid = it.get('id') or it.get('model') or it.get('name')
                    if mid:
                        out.append(mid)
                return out
        except Exception as e:
            logger.error(f"Failed to fetch models from OpenRouter: {e}")
            return []

    def validate_model(self, model_id: str) -> bool:
        """Return True if model_id appears valid for this key (best-effort).

        If we cannot fetch the live list, be permissive and return True (caller should warn).
        """
        try:
            avail = self.get_available_models()
            if not avail:
                return True
            return model_id in avail
        except Exception:
            return True
