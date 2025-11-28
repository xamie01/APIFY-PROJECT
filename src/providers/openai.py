import asyncio
import logging
import os
import time
from typing import Optional, List

logger = logging.getLogger(__name__)


def _get_openai_key():
    """Get OpenAI API key from environment."""
    return os.environ.get('OPENAI_API_KEY') or os.environ.get('OPENAI_APIKEY')


class OpenAIProvider:
    """OpenAI ChatGPT provider with preflight model checks and retry handling."""

    # Commonly available models (used as fallback if API listing fails)
    DEFAULT_MODELS = ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo']

    def __init__(self, model: str = 'gpt-4o-mini', api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or _get_openai_key()
        self._client = None
        if not self.api_key:
            logger.warning('No OpenAI API key configured')
        else:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                logger.warning('openai package not installed')
        logger.info(f"OpenAIProvider initialized: model={model}")

    # ------------------------------------------------------------------ #
    # Preflight helpers
    # ------------------------------------------------------------------ #
    def get_available_models(self) -> List[str]:
        """Fetch available models from OpenAI API.

        Returns a list of model ids; falls back to DEFAULT_MODELS on error.
        """
        if not self._client:
            return list(self.DEFAULT_MODELS)
        try:
            resp = self._client.models.list()
            ids = [m.id for m in resp.data if hasattr(m, 'id')]
            # filter to chat-compatible models
            chat_ids = [mid for mid in ids if 'gpt' in mid.lower() or 'chat' in mid.lower()]
            return chat_ids if chat_ids else list(self.DEFAULT_MODELS)
        except Exception as e:
            logger.warning(f'Failed to list OpenAI models: {e}')
            return list(self.DEFAULT_MODELS)

    def validate_model(self, model_id: str) -> bool:
        """Return True if model_id appears valid (best effort)."""
        try:
            avail = self.get_available_models()
            if not avail:
                return True
            return model_id in avail
        except Exception:
            return True

    # ------------------------------------------------------------------ #
    # Query
    # ------------------------------------------------------------------ #
    def query(self, prompt: str, **kwargs) -> str:
        """Synchronous query method with retry logic."""
        if not self._client:
            raise RuntimeError('No OpenAI client (missing API key or package)')

        max_retries = int(kwargs.get('max_retries', 3))
        backoff = float(kwargs.get('backoff', 1.0))

        last_exc = None
        for attempt in range(1, max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[{'role': 'user', 'content': prompt}],
                    max_tokens=kwargs.get('max_tokens', 512),
                    temperature=kwargs.get('temperature', 0.2),
                )
                return response.choices[0].message.content
            except Exception as e:
                last_exc = e
                msg = str(e).lower()
                if '429' in msg or 'rate' in msg:
                    logger.warning(f'OpenAI rate limit, attempt {attempt}/{max_retries}')
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                raise
        raise last_exc  # type: ignore

    async def query_async(self, prompt: str, **kwargs) -> str:
        """Async query method."""
        return await asyncio.to_thread(self.query, prompt, **kwargs)
