import asyncio
import logging
import os
import time
from typing import Optional, List

logger = logging.getLogger(__name__)


def _get_anthropic_key():
    """Get Anthropic API key from environment."""
    return os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_APIKEY')


class AnthropicProvider:
    """Anthropic Claude provider with preflight model checks and retry handling."""

    # Commonly available Claude models
    DEFAULT_MODELS = [
        'claude-3-5-sonnet-20241022',
        'claude-3-opus-20240229',
        'claude-3-sonnet-20240229',
        'claude-3-haiku-20240307',
        'claude-2.1',
    ]

    def __init__(self, model: str = 'claude-3-5-sonnet-20241022', api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or _get_anthropic_key()
        self._client = None

        try:
            import anthropic
            if self.api_key:
                self._client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            logger.warning('anthropic package not installed')

        logger.info(f"AnthropicProvider initialized: model={model}")

    # ------------------------------------------------------------------ #
    # Preflight helpers
    # ------------------------------------------------------------------ #
    def get_available_models(self) -> List[str]:
        """Return list of known models (Anthropic doesn't expose /models endpoint)."""
        return list(self.DEFAULT_MODELS)

    def validate_model(self, model_id: str) -> bool:
        """Return True if model_id appears valid (best effort).""" 
        # Anthropic model ids typically start with 'claude'
        if model_id.startswith('claude'):
            return True
        return model_id in self.DEFAULT_MODELS

    # ------------------------------------------------------------------ #
    # Query
    # ------------------------------------------------------------------ #
    def query(self, prompt: str, **kwargs) -> str:
        """Synchronous query method with retry logic."""
        if not self._client:
            raise RuntimeError('Anthropic client not available (missing API key or package). pip install anthropic')

        max_retries = int(kwargs.get('max_retries', 3))
        backoff = float(kwargs.get('backoff', 1.0))

        last_exc = None
        for attempt in range(1, max_retries + 1):
            try:
                response = self._client.messages.create(
                    model=self.model,
                    max_tokens=kwargs.get('max_tokens', 512),
                    messages=[{'role': 'user', 'content': prompt}]
                )
                # Parse response
                if hasattr(response, 'content') and response.content:
                    if hasattr(response.content[0], 'text'):
                        return response.content[0].text
                return str(response)
            except Exception as e:
                last_exc = e
                msg = str(e).lower()
                if '429' in msg or 'rate' in msg or 'overloaded' in msg:
                    logger.warning(f'Anthropic rate limit, attempt {attempt}/{max_retries}')
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                raise
        raise last_exc  # type: ignore

    async def query_async(self, prompt: str, **kwargs) -> str:
        """Async query method."""
        return await asyncio.to_thread(self.query, prompt, **kwargs)
