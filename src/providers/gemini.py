import asyncio
import logging
import os
import time
from typing import Optional, Any, List

logger = logging.getLogger(__name__)


def _get_gemini_key():
    """Get Gemini API key from environment."""
    return os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')


class GeminiProvider:
    """Google Gemini provider with optional support for multiple genai SDK layouts.

    If `google-genai` / `google.genai` / `google.generativeai` is installed, use it.
    Otherwise fall back to a lightweight echo placeholder so tests and local runs work
    without the real SDK.
    """

    # Known Gemini model names
    DEFAULT_MODELS = [
        'gemini-1.5-pro',
        'gemini-1.5-flash',
        'gemini-pro',
        'gemini-pro-vision',
    ]

    def __init__(self, model: str = 'gemini-1.5-flash', api_key: Optional[str] = None, **kwargs):
        self.model = model
        self.api_key = api_key or _get_gemini_key()
        self._client = None
        self._sdk = None

        # Try several known Gemini SDK layouts
        try:
            # Newer package layout
            from google import genai as genai_module  # type: ignore
            self._sdk = 'google.genai'
            self._client = genai_module
            try:
                # prefer configure/init if present
                if hasattr(self._client, 'configure'):
                    self._client.configure(api_key=api_key)
                elif hasattr(self._client, 'init'):
                    self._client.init(api_key=api_key)
            except Exception:
                pass
            logger.info('GeminiProvider: using google.genai')
        except Exception:
            try:
                import google.genai as genai_module  # type: ignore
                self._sdk = 'google.genai'
                self._client = genai_module
                logger.info('GeminiProvider: using google.genai')
            except Exception:
                try:
                    import google.generativeai as genai_module  # type: ignore
                    self._sdk = 'google.generativeai'
                    self._client = genai_module
                    # older package expects configure(api_key)
                    try:
                        if hasattr(self._client, 'configure'):
                            self._client.configure(api_key=api_key)
                    except Exception:
                        pass
                    logger.info('GeminiProvider: using google.generativeai')
                except Exception:
                    # No Gemini SDK available; remain as None and use fallback
                    self._client = None
                    logger.info('GeminiProvider: no genai SDK available, using fallback')

    def _parse_result(self, res: Any) -> str:
        # Try to extract canonical text from a variety of SDK responses
        try:
            if res is None:
                return ''
            # dict-like
            if isinstance(res, dict):
                for key in ('response', 'text', 'output', 'candidates'):
                    if key in res:
                        val = res[key]
                        if isinstance(val, list) and val:
                            first = val[0]
                            if isinstance(first, dict):
                                return str(first.get('content') or first.get('text') or first)
                            return str(first)
                        if isinstance(val, str):
                            return val
                # direct fallbacks
                if 'candidates' in res and isinstance(res['candidates'], list) and res['candidates']:
                    c = res['candidates'][0]
                    if isinstance(c, dict):
                        return str(c.get('content') or c.get('text') or c)
            # object-like responses
            if hasattr(res, 'output'):
                out = getattr(res, 'output')
                if isinstance(out, list) and out:
                    first = out[0]
                    if hasattr(first, 'content'):
                        return str(first.content)
                    if isinstance(first, dict):
                        return str(first.get('content') or first.get('text') or first)
            if hasattr(res, 'text'):
                return str(getattr(res, 'text'))
            if hasattr(res, 'candidates'):
                c = getattr(res, 'candidates')
                if c and hasattr(c[0], 'content'):
                    return str(c[0].content)
        except Exception:
            pass
        try:
            return str(res)
        except Exception:
            return ''

    async def query_async(self, prompt: str, **kwargs) -> str:
        """Async query method."""
        # Check if API key is available when SDK requires it
        if self._client and not self.api_key:
            # SDK is available but no API key configured
            logger.warning('GeminiProvider: No API key available. Please set GEMINI_API_KEY or use another model (e.g., openrouter-mistral-7b, openai-gpt-4).')
            return f"[GEMINI:{self.model}] ERROR: No Gemini API key available. Please configure GEMINI_API_KEY or use another model."

        # If SDK available, try to use its async or sync APIs
        if self._client:
            try:
                # newer google.genai: Model.generate or Model.generate_async
                if hasattr(self._client, 'Model') and hasattr(self._client.Model, 'generate_async'):
                    result = await self._client.Model.generate_async(model=self.model, input=prompt, **kwargs)
                    return self._parse_result(result) or f"[GEMINI:{self.model}] {prompt[:400]}"
                if hasattr(self._client, 'Model') and hasattr(self._client.Model, 'generate'):
                    # run in thread
                    return await asyncio.to_thread(lambda: self._parse_result(self._client.Model.generate(model=self.model, input=prompt, **kwargs)) or f"[GEMINI:{self.model}] {prompt[:400]}")
                # module-level async generate
                if hasattr(self._client, 'generate_async'):
                    result = await self._client.generate_async(input=prompt, **kwargs)
                    return self._parse_result(result) or f"[GEMINI:{self.model}] {prompt[:400]}"
                # module-level sync generate
                if hasattr(self._client, 'generate'):
                    return await asyncio.to_thread(lambda: self._parse_result(self._client.generate(input=prompt, **kwargs)) or f"[GEMINI:{self.model}] {prompt[:400]}")
                # older google.generativeai client with responses.create
                if hasattr(self._client, 'Client'):
                    def _call():
                        try:
                            client = self._client.Client(api_key=self.api_key)
                        except ValueError as ve:
                            # SDK requires API key but none provided
                            logger.warning(f'Gemini SDK requires API key: {ve}')
                            return None
                        except Exception:
                            return None
                        if hasattr(client, 'responses') and hasattr(client.responses, 'create'):
                            return client.responses.create(model=self.model, input=prompt)
                        if hasattr(client, 'generate_text'):
                            return client.generate_text(model=self.model, input=prompt)
                        return None
                    result = await asyncio.to_thread(_call)
                    if result is None:
                        return f"[GEMINI:{self.model}] ERROR: No Gemini API key available. Please configure GEMINI_API_KEY or use another model."
                    return self._parse_result(result) or f"[GEMINI:{self.model}] {prompt[:400]}"
            except ValueError as ve:
                # Catch "Missing key inputs argument" errors
                logger.warning(f'GeminiProvider: API key required but not provided: {ve}')
                return f"[GEMINI:{self.model}] ERROR: No Gemini API key available. Please configure GEMINI_API_KEY or use another model."
            except Exception as e:
                logger.warning(f'GeminiProvider SDK call failed, falling back: {e}')
                # fallback to simple echo

        # Fallback behavior (no SDK): lightweight echo so tests don't require real API
        await asyncio.sleep(0.001)
        return f"[GEMINI:{self.model}] {prompt[:400]}"

    def query(self, prompt: str, **kwargs) -> str:
        """Synchronous query method - required for API consistency."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If running inside an existing loop, use thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self.query_async(prompt, **kwargs))
                    return future.result()
            else:
                return loop.run_until_complete(self.query_async(prompt, **kwargs))
        except RuntimeError:
            # No running loop
            return asyncio.run(self.query_async(prompt, **kwargs))

    # ------------------------------------------------------------------ #
    # Preflight helpers
    # ------------------------------------------------------------------ #
    def get_available_models(self) -> List[str]:
        """Return list of known Gemini models (Google doesn't expose a public /models endpoint for genai)."""
        return list(self.DEFAULT_MODELS)

    def validate_model(self, model_id: str) -> bool:
        """Return True if model_id appears valid (best effort)."""
        # Gemini model ids typically start with 'gemini'
        if model_id.startswith('gemini'):
            return True
        return model_id in self.DEFAULT_MODELS
