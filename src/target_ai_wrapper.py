"""
Unified wrapper for interacting with multiple AI providers
Supports: OpenAI, Google Gemini, Anthropic, DeepSeek, Ollama, Cohere, 
         Hugging Face, Replicate, Together AI, Groq, Mistral, Perplexity
"""

import os
import time
import json
import asyncio
import sys
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import requests
from .logger import get_logger
from .utils import get_api_key, get_api_keys, load_config

# Lazy imports for providers
openai = None
genai = None
anthropic = None
cohere = None
replicate = None
groq = None
mistral = None

logger = get_logger(__name__)


class BaseAIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def query(self, prompt: str, **kwargs) -> str:
        """Send a query to the AI and return response"""
        pass
    
    @abstractmethod
    async def query_async(self, prompt: str, **kwargs) -> str:
        """Send an async query to the AI and return response"""
        pass


class OpenAIProvider(BaseAIProvider):
    """OpenAI API provider with retry/backoff support"""
    
    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or get_api_key("openai") or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found")

        # Lazy import the OpenAI SDK to avoid top-level dependency issues
        try:
            import openai as _openai
        except Exception:
            raise ImportError("openai package not installed. Run: pip install openai")

        # Set module-level reference so other code can use it
        global openai
        openai = _openai

        # New OpenAI client class exists in the modern SDK
        try:
            # Preferred: instantiate OpenAI client
            self.client = openai.OpenAI(api_key=self.api_key)
        except Exception:
            # Fallback for older openai package versions
            openai.api_key = self.api_key
            self.client = openai

        logger.info(f"OpenAI provider initialized with model: {model}")

    def _call_with_retries(self, func, max_retries: int = 5, initial_backoff: float = 1.0):
        """Call a function with exponential backoff for transient errors (429/503).

        The func should be a zero-arg callable that performs the HTTP/API request.
        """
        backoff = initial_backoff
        for attempt in range(1, max_retries + 1):
            try:
                return func()
            except Exception as e:
                # Try to infer HTTP status / retry-after
                status = None
                retry_after = None
                try:
                    status = getattr(e, 'http_status', None) or getattr(e, 'status_code', None) or getattr(e, 'code', None)
                    if hasattr(e, 'response') and getattr(e.response, 'headers', None):
                        retry_after = e.response.headers.get('Retry-After')
                    # some OpenAI errors expose args with status
                    if hasattr(e, 'status') and not status:
                        status = getattr(e, 'status')
                except Exception:
                    pass

                msg = str(e)
                transient = False
                if status in (429, 503):
                    transient = True
                if 'rate limit' in msg.lower() or 'quota' in msg.lower() or 'too many requests' in msg.lower():
                    transient = True

                if transient and attempt < max_retries:
                    wait = float(retry_after) if retry_after else backoff
                    logger.warning(f"Transient error (attempt {attempt}/{max_retries}), retrying in {wait}s: {e}")
                    time.sleep(wait)
                    backoff *= 2
                    continue

                # Not transient or max attempts reached
                logger.error(f"API call failed (attempt {attempt}/{max_retries}): {e}")
                raise

        raise RuntimeError(f"Max retries exceeded ({max_retries})")

    def _extract_openai_text(self, response: Any) -> str:
        """Extract text from various OpenAI response shapes."""
        try:
            # New OpenAI client response
            if hasattr(response, 'choices') and response.choices:
                first = response.choices[0]
                if hasattr(first, 'message') and hasattr(first.message, 'content'):
                    return first.message.content
                # older shape
                if hasattr(first, 'text'):
                    return first.text
            # dict-like
            if isinstance(response, dict):
                choices = response.get('choices')
                if choices and isinstance(choices, list):
                    first = choices[0]
                    msg = first.get('message') or first
                    if isinstance(msg, dict):
                        return msg.get('content') or msg.get('text') or str(msg)
            # fallback to text attribute
            if hasattr(response, 'text'):
                return getattr(response, 'text')
            return str(response)
        except Exception:
            return str(response)

    def query(self, prompt: str, **kwargs) -> str:
        """
        Send a query to OpenAI with retry/backoff for transient errors.
        """
        def _call():
            return self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
            )

        try:
            response = self._call_with_retries(_call)
            return self._extract_openai_text(response)
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def query_async(self, prompt: str, **kwargs) -> str:
        """
        Async wrapper: run sync query with retries in a thread to keep semantics.
        """
        return await asyncio.to_thread(self.query, prompt, **kwargs)


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude API provider"""
    
    def __init__(self, model: str = "claude-3-opus-20240229", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or get_api_key("anthropic")
        
        if not self.api_key:
            raise ValueError("Anthropic API key not found")
        
        self.client = Anthropic(api_key=self.api_key)
        logger.info(f"Anthropic provider initialized with model: {model}")
    
    def query(self, prompt: str, **kwargs) -> str:
        """
        Send a query to Anthropic Claude
        
        Args:
            prompt: User prompt
            **kwargs: Additional parameters
        
        Returns:
            AI response text
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 2000),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def query_async(self, prompt: str, **kwargs) -> str:
        """Async version of query"""
        return self.query(prompt, **kwargs)


class GeminiProvider(BaseAIProvider):
    """Google Gemini API provider (supports new google-genai SDK)

    This implementation imports the SDK flexibly (preferred: `from google import genai`),
    configures the client with the provided key, and normalizes responses across
    multiple SDK versions.
    """

    def __init__(self, model: str = "gemini-pro", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or get_api_key("google") or os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError("Google API key not found. Please set GOOGLE_API_KEY in your .env file")

        # Flexible import for different genai package layouts
        try:
            # Preferred import for the new SDK
            from google import genai as genai_module  # type: ignore
        except Exception:
            try:
                import google.genai as genai_module  # type: ignore
            except Exception:
                try:
                    # Fallback to older package name if present
                    import google.generativeai as genai_module  # type: ignore
                except Exception:
                    raise ImportError("google-genai SDK not installed. Run: pip install google-genai")

        self.genai = genai_module

        # Configure client depending on SDK version
        if hasattr(self.genai, "configure"):
            try:
                # older helper
                self.genai.configure(api_key=self.api_key)
            except Exception:
                # some versions may expose init
                if hasattr(self.genai, "init"):
                    self.genai.init(api_key=self.api_key)
        elif hasattr(self.genai, "init"):
            self.genai.init(api_key=self.api_key)

        logger.info(f"Gemini provider initialized with model: {model}")

    def _parse_genai_result(self, result: Any) -> str:
        """Try multiple ways to extract text from a genai response object/dict."""
        # If object has text attribute
        if hasattr(result, "text") and isinstance(getattr(result, "text"), str):
            return getattr(result, "text")

        # If object has 'output' attribute or key
        try:
            if isinstance(result, dict):
                # Common structures: {'output': [{'content': '...'}]} or {'candidates': [{'content': '...'}]}
                for key in ("output", "candidates", "candidates_output", "response"):
                    if key in result:
                        out = result[key]
                        if isinstance(out, list) and out:
                            first = out[0]
                            if isinstance(first, dict):
                                return first.get("content") or first.get("text") or str(first)
                            return str(first)
                # direct text
                for key in ("text", "content", "response"):
                    if key in result and isinstance(result[key], str):
                        return result[key]
            else:
                # Object-style responses
                if hasattr(result, "output"):
                    out = getattr(result, "output")
                    if isinstance(out, list) and out:
                        first = out[0]
                        if hasattr(first, "content"):
                            return first.content
                        if isinstance(first, dict):
                            return first.get("content") or str(first)
                if hasattr(result, "candidates"):
                    c = getattr(result, "candidates")
                    if c and hasattr(c[0], "content"):
                        return c[0].content
        except Exception:
            pass

        # Fallback to string conversion
        try:
            return str(result)
        except Exception:
            return ""

    def query(self, prompt: str, **kwargs) -> str:
        """
        Send a query to Google Gemini (synchronous) with broad SDK compatibility.
        """
        try:
            # 1) Newer google-genai: genai.Model.generate(model=..., input=...)
            if hasattr(self.genai, "Model") and hasattr(self.genai.Model, "generate"):
                gen_kwargs = {}
                if "temperature" in kwargs:
                    gen_kwargs["temperature"] = kwargs.get("temperature")
                if "max_tokens" in kwargs:
                    gen_kwargs["max_output_tokens"] = kwargs.get("max_tokens")

                result = self.genai.Model.generate(model=self.model, input=prompt, **gen_kwargs)
                return self._parse_genai_result(result)

            # 2) genai.generate(input=...)
            if hasattr(self.genai, "generate"):
                try:
                    # try named param
                    result = self.genai.generate(input=prompt)
                except TypeError:
                    # fallback to positional
                    result = self.genai.generate(prompt)
                return self._parse_genai_result(result)

            # 3) genai.generate_text(prompt)
            if hasattr(self.genai, "generate_text"):
                result = self.genai.generate_text(prompt)
                return self._parse_genai_result(result)

            # 4) Older google.generativeai: GenerativeModel
            if hasattr(self.genai, "GenerativeModel"):
                try:
                    gm = self.genai.GenerativeModel(self.model)
                    # some older helpers expect a different call
                    if hasattr(gm, "generate_content"):
                        result = gm.generate_content(prompt)
                    elif hasattr(gm, "generate"):
                        result = gm.generate(prompt)
                    else:
                        raise RuntimeError("GenerativeModel has no generate method")
                    return self._parse_genai_result(result)
                except Exception:
                    # fallthrough to error below
                    pass

            # 5) If SDK exposes a client object with .generate or .create
            if hasattr(self.genai, "client"):
                client = getattr(self.genai, "client")
                if hasattr(client, "generate"):
                    try:
                        result = client.generate(input=prompt)
                    except TypeError:
                        result = client.generate(prompt)
                    return self._parse_genai_result(result)

            # 5.1) genai module exposes a Client class (newer SDK layouts)
            if hasattr(self.genai, "Client"):
                try:
                    # Try to instantiate client with api_key if supported
                    try:
                        client = self.genai.Client(api_key=self.api_key)
                    except TypeError:
                        client = self.genai.Client()

                    # Preferred: client.responses.create(...) (new GenAI patterns)
                    if hasattr(client, "responses") and hasattr(client.responses, "create"):
                        try:
                            result = client.responses.create(model=self.model, input=prompt)
                        except TypeError:
                            result = client.responses.create(input=prompt, model=self.model)
                        return self._parse_genai_result(result)

                    # client.generate_text / client.generate
                    if hasattr(client, "generate_text"):
                        try:
                            result = client.generate_text(model=self.model, input=prompt)
                        except TypeError:
                            result = client.generate_text(input=prompt)
                        return self._parse_genai_result(result)

                    if hasattr(client, "generate"):
                        try:
                            result = client.generate(model=self.model, input=prompt)
                        except TypeError:
                            result = client.generate(prompt)
                        return self._parse_genai_result(result)

                    # client.chats.create or client.chat.create
                    chats_obj = getattr(client, "chats", None) or getattr(client, "chat", None)
                    if chats_obj and hasattr(chats_obj, "create"):
                        try:
                            result = chats_obj.create(model=self.model, messages=[{"author": "user", "content": prompt}])
                        except TypeError:
                            result = chats_obj.create(model=self.model, messages=[{"role": "user", "content": prompt}])
                        return self._parse_genai_result(result)

                except Exception:
                    # fallthrough to other handlers below
                    pass

            # 6) Module-level models.generate (another common layout)
            if hasattr(self.genai, "models") and hasattr(self.genai.models, "generate"):
                try:
                    result = self.genai.models.generate(model=self.model, input=prompt)
                except TypeError:
                    try:
                        result = self.genai.models.generate(self.model, prompt)
                    except Exception:
                        result = self.genai.models.generate(input=prompt)
                return self._parse_genai_result(result)

            # 7) Module-level chats.create (module exposes chats service)
            if hasattr(self.genai, "chats") and hasattr(self.genai.chats, "create"):
                try:
                    result = self.genai.chats.create(model=self.model, messages=[{"author": "user", "content": prompt}])
                except TypeError:
                    result = self.genai.chats.create(model=self.model, messages=[{"role": "user", "content": prompt}])
                return self._parse_genai_result(result)

            # 8) If module has a top-level 'client' object instance
            if hasattr(self.genai, "client"):
                try:
                    client = getattr(self.genai, "client")
                    # Try responses.create if available
                    if hasattr(client, "responses") and hasattr(client.responses, "create"):
                        result = client.responses.create(model=self.model, input=prompt)
                        return self._parse_genai_result(result)

                    # Try client.models.generate
                    if hasattr(client, "models") and hasattr(client.models, "generate"):
                        try:
                            result = client.models.generate(model=self.model, input=prompt)
                        except TypeError:
                            try:
                                result = client.models.generate(self.model, prompt)
                            except Exception:
                                result = client.models.generate(input=prompt)
                        return self._parse_genai_result(result)

                    # Try client.generate
                    if hasattr(client, "generate"):
                        try:
                            result = client.generate(model=self.model, input=prompt)
                        except TypeError:
                            result = client.generate(prompt)
                        return self._parse_genai_result(result)

                    # Try client.chats.create
                    chats_obj = getattr(client, "chats", None) or getattr(client, "chat", None)
                    if chats_obj and hasattr(chats_obj, "create"):
                        try:
                            result = chats_obj.create(model=self.model, messages=[{"author": "user", "content": prompt}])
                        except TypeError:
                            result = chats_obj.create(model=self.model, messages=[{"role": "user", "content": prompt}])
                        return self._parse_genai_result(result)

                except Exception:
                    pass

            # If none matched, provide a diagnostic error listing available attrs
            available = sorted([a for a in dir(self.genai) if not a.startswith("__")])
            raise RuntimeError(f"Unsupported google-genai client interface. Available attributes: {available[:20]}{'...' if len(available)>20 else ''}")

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    async def query_async(self, prompt: str, **kwargs) -> str:
        """
        Async wrapper for Gemini. Prefer native async generate if available,
        otherwise run sync call in a thread.
        """
        try:
            # Native async Model.generate_async
            if hasattr(self.genai, "Model") and hasattr(self.genai.Model, "generate_async"):
                gen_kwargs = {}
                if "temperature" in kwargs:
                    gen_kwargs["temperature"] = kwargs.get("temperature")
                if "max_tokens" in kwargs:
                    gen_kwargs["max_output_tokens"] = kwargs.get("max_tokens")

                result = await self.genai.Model.generate_async(model=self.model, input=prompt, **gen_kwargs)
                return self._parse_genai_result(result)

            # If module has an async generate function
            if hasattr(self.genai, "generate_async"):
                result = await self.genai.generate_async(input=prompt)
                return self._parse_genai_result(result)

            # Fallback to thread
            return await asyncio.to_thread(self.query, prompt, **kwargs)

        except Exception as e:
            logger.error(f"Gemini API error (async): {e}")
            raise


class DeepSeekProvider(BaseAIProvider):
    """DeepSeek API provider (OpenAI-compatible)"""
    
    def __init__(self, model: str = "deepseek-chat", api_key: Optional[str] = None, api_base: Optional[str] = None):
        self.model = model
        self.api_key = api_key or get_api_key("deepseek")
        self.api_base = api_base or "https://api.deepseek.com/v1"
        
        if not self.api_key:
            raise ValueError("DeepSeek API key not found")
        
        try:
            global openai
            import openai
            self.client = openai.OpenAI(api_key=self.api_key, base_url=self.api_base)
            logger.info(f"DeepSeek provider initialized with model: {model}")
        except ImportError:
            raise ImportError("Please install: pip install openai")
    
    def query(self, prompt: str, **kwargs) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise
    
    async def query_async(self, prompt: str, **kwargs) -> str:
        return self.query(prompt, **kwargs)  # DeepSeek doesn't support async yet


class OllamaProvider(BaseAIProvider):
    """Ollama local API provider"""
    
    def __init__(self, model: str = "llama2", api_base: Optional[str] = None):
        self.model = model
        self.api_base = api_base or get_api_key("ollama") or "http://localhost:11434"
        logger.info(f"Ollama provider initialized with model: {model}")
    
    def query(self, prompt: str, **kwargs) -> str:
        try:
            response = requests.post(
                f"{self.api_base}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2000),
                }
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise
    
    async def query_async(self, prompt: str, **kwargs) -> str:
        return self.query(prompt, **kwargs)


class CohereProvider(BaseAIProvider):
    """Cohere API provider"""
    
    def __init__(self, model: str = "command", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or get_api_key("cohere")
        
        if not self.api_key:
            raise ValueError("Cohere API key not found")
        
        try:
            global cohere
            import cohere
            self.client = cohere.Client(self.api_key)
            logger.info(f"Cohere provider initialized with model: {model}")
        except ImportError:
            raise ImportError("Please install: pip install cohere")
    
    def query(self, prompt: str, **kwargs) -> str:
        try:
            response = self.client.generate(
                prompt=prompt,
                model=self.model,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
            )
            return response.generations[0].text
        except Exception as e:
            logger.error(f"Cohere API error: {e}")
            raise
    
    async def query_async(self, prompt: str, **kwargs) -> str:
        return self.query(prompt, **kwargs)


class GroqProvider(BaseAIProvider):
    """Groq API provider"""
    
    def __init__(self, model: str = "mixtral-8x7b-32768", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or get_api_key("groq")
        
        if not self.api_key:
            raise ValueError("Groq API key not found")
        
        try:
            global groq
            import groq
            self.client = groq.Groq(api_key=self.api_key)
            logger.info(f"Groq provider initialized with model: {model}")
        except ImportError:
            raise ImportError("Please install: pip install groq")
    
    def query(self, prompt: str, **kwargs) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 2000),
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
    
    async def query_async(self, prompt: str, **kwargs) -> str:
        return self.query(prompt, **kwargs)


class OpenRouterProvider(BaseAIProvider):
    """OpenRouter API provider for free models"""
    
    def __init__(self, model: str = "deepseek/deepseek-chat", api_key: Optional[str] = None):
        self.model = model
        # support multiple keys via env or config
        provided_keys = []
        if api_key:
            provided_keys = [api_key]
        else:
            provided_keys = get_api_keys('openrouter') or ([] if not os.getenv('OPENROUTER_API_KEY') else [os.getenv('OPENROUTER_API_KEY')])

        # Fallback: single env var
        if not provided_keys:
            raise ValueError("OpenRouter API key not found (set OPENROUTER_API_KEY or target_ai.api_keys.openrouter)")

        self.api_keys = provided_keys[:5]  # limit to 5 keys as requested
        self._key_index = 0
        self._banned = {}  # key -> ban_until timestamp
        self._request_count = {}  # key -> number of successful requests
        self.requests_per_key = 45  # rotate after 45 successful requests per key
        self._rotation_cycle = 0  # track number of completed cycles through all keys
        self._keys_tried_in_cycle = set()  # track which keys have been tried in current cycle

        try:
            global openai
            import openai
            # store base url; we will create per-request clients with different keys
            self.openrouter_base = "https://openrouter.ai/api/v1"
            logger.info(f"OpenRouter provider initialized with model: {model} and {len(self.api_keys)} key(s) with 45-request rotation and sticky banning")
        except ImportError:
            raise ImportError("Please install: pip install openai")
    
    def query(self, prompt: str, **kwargs) -> str:
        # Pre-check: find at least one functional key before attempting request
        functional_key = self._find_functional_key()
        if not functional_key:
            # No functional keys available; raise 409-equivalent error
            error_msg = "All OpenRouter API keys are rate-limited or banned. No functional keys available."
            logger.error(error_msg)
            raise RuntimeError(f"409: {error_msg}")
        
        # Try each available key, retrying each key up to `per_key_retries` times
        per_key_retries = int(kwargs.get('per_key_retries', 3))
        initial_backoff = float(kwargs.get('initial_backoff', 1.0))

        # Number of configured keys
        total_keys = len(self.api_keys)

        # Outer loop: keep trying available keys until exhausted
        while True:
            key = self._get_next_key()
            if not key:
                # No non-banned keys available right now
                # If all keys appear banned, check if we've completed a full rotation cycle
                if len(self._banned) >= total_keys:
                    # All keys are banned; unban them and restart cycle
                    logger.warning(f"All OpenRouter keys are banned; unbanning all keys for retry (cycle: {self._rotation_cycle})")
                    self._banned.clear()
                    self._keys_tried_in_cycle.clear()
                    self._rotation_cycle += 1
                    time.sleep(2)  # wait before retry
                    continue
                # Otherwise wait briefly and re-check
                time.sleep(1)
                continue

            # Check if this key has reached 45 requests; if so, force rotate to next key
            request_count = self._request_count.get(key, 0)
            if request_count >= self.requests_per_key:
                logger.info(f"Key '{key}' has reached {self.requests_per_key} successful requests; rotating to next key")
                # Move to next key for the next call
                n = len(self.api_keys)
                self._key_index = (self._key_index + 1) % n
                continue

            # Try the chosen key multiple times before banning it
            backoff = initial_backoff
            for attempt in range(1, per_key_retries + 1):
                try:
                    client = openai.OpenAI(api_key=key, base_url=self.openrouter_base)
                    response = client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=kwargs.get("temperature", 0.7),
                        max_tokens=kwargs.get("max_tokens", 2000),
                    )

                    # on success, increment request count and track this key as tried in current cycle
                    self._request_count[key] = self._request_count.get(key, 0) + 1
                    self._keys_tried_in_cycle.add(key)
                    logger.debug(f"OpenRouter request successful with key '{key}' (total for this key: {self._request_count[key]})")
                    return response.choices[0].message.content

                except Exception as e:
                    msg = str(e).lower()
                    logger.warning(f"OpenRouter API error using key '{key}' (attempt {attempt}/{per_key_retries}): {e}")

                    # detect rate limit / 429
                    if ('429' in msg or 'rate limit' in msg or 'too many requests' in msg or 'rate_limited' in msg):
                        if attempt < per_key_retries:
                            # retry same key after backoff
                            logger.info(f"Retrying key '{key}' after {backoff}s backoff (attempt {attempt}/{per_key_retries})")
                            time.sleep(backoff)
                            backoff *= 2
                            continue
                        else:
                            # Exhausted retries for this key: ban it until full rotation cycle completes
                            # Ban duration extends until all other keys are tried
                            ban_seconds = 3600  # long ban until cycle completes
                            self._banned[key] = time.time() + ban_seconds
                            self._keys_tried_in_cycle.add(key)  # mark as tried (in banned state)
                            logger.warning(f"Key '{key}' rate-limited and banned for {ban_seconds}s (will stay banned until all keys are cycled)")
                            break
                    else:
                        # Non-rate-limit error: re-raise immediately
                        logger.error(f"OpenRouter non-rate error for key '{key}': {e}")
                        raise

    def _find_functional_key(self) -> Optional[str]:
        """
        Pre-check: find a functional (non-banned, non-rate-limited) key.
        Tries each key once to verify it works. Returns the first working key,
        or None if all keys are exhausted or failing.
        """
        now = time.time()
        n = len(self.api_keys)
        
        for i in range(n):
            idx = (self._key_index + i) % n
            key = self.api_keys[idx]
            
            # Skip if key is currently banned
            ban_until = self._banned.get(key)
            if ban_until and ban_until > now:
                logger.debug(f"Key '{key}' is still banned (until {ban_until})")
                continue
            
            # Try a quick 1-word test with this key
            try:
                client = openai.OpenAI(api_key=key, base_url=self.openrouter_base)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "ok"}],
                    temperature=0.5,
                    max_tokens=10,
                )
                # Key works!
                logger.info(f"Pre-check: Found functional key '{key}'")
                return key
            
            except Exception as e:
                msg = str(e).lower()
                if '429' in msg or 'rate limit' in msg or 'too many requests' in msg or 'rate_limited' in msg:
                    # This key is rate-limited; mark it
                    logger.warning(f"Pre-check: Key '{key}' is rate-limited (429)")
                    ban_seconds = 3600
                    self._banned[key] = time.time() + ban_seconds
                else:
                    logger.warning(f"Pre-check: Key '{key}' failed: {str(e)[:50]}")
        
        # No functional key found
        logger.error("Pre-check: No functional keys available")
        return None
    
    async def query_async(self, prompt: str, **kwargs) -> str:
        return await asyncio.to_thread(self.query, prompt, **kwargs)

    def _get_next_key(self) -> Optional[str]:
        """
        Return the current key if it's available and not banned.
        If current key is banned or exhausted (45+ requests), move to next available key.
        Returns None if none available.
        """
        now = time.time()
        n = len(self.api_keys)
        
        # Try to use the current key (sticky key selection)
        current_key = self.api_keys[self._key_index % n]
        ban_until = self._banned.get(current_key)
        
        # If current key is available (not banned), return it
        if not (ban_until and ban_until > now):
            return current_key
        
        # Current key is banned; find next available key
        for i in range(1, n):
            idx = (self._key_index + i) % n
            key = self.api_keys[idx]
            ban_until = self._banned.get(key)
            if not (ban_until and ban_until > now):
                # Found available key; switch to it
                self._key_index = idx
                return key
        
        return None


class TargetAIWrapper:
    """
    Main wrapper class that provides a unified interface to all AI providers
    """
    
    def __init__(self, target: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize AI wrapper
        
        Args:
            target: Target AI identifier (e.g., 'openai-gpt4', 'anthropic-claude')
            config: Optional configuration dictionary
        """
        self.config = config or load_config()
        self.target = target
        # Interactive selection state (only prompt when running in a TTY)
        self._interactive_model_selected = False
        self._interactive_enabled = sys.stdin.isatty()
        # Ensure API key is present for the selected provider before initializing
        provider_key_map = {
            'openai': 'openai',
            'gemini': 'google',
            'anthropic': 'anthropic',
            'deepseek': 'deepseek',
            'ollama': 'ollama',
            'cohere': 'cohere',
            'groq': 'groq',
            'openrouter': 'openrouter'
        }
        key_name = None
        for k in provider_key_map:
            if target.lower().startswith(k):
                key_name = provider_key_map[k]
                break

        if key_name:
            # If the caller provided an explicit config, require the API key
            # to be present in config['target_ai']['api_keys'] to avoid
            # quietly reading environment variables during tests.
            if config is not None:
                api_keys_cfg = self.config.get('target_ai', {}).get('api_keys', {})
                if not api_keys_cfg or not api_keys_cfg.get(key_name):
                    raise ValueError(f"API key for provider '{key_name}' not found in provided configuration")
            else:
                api_key = get_api_key(key_name)
                # Also check env fallback
                if not api_key and key_name == 'google':
                    api_key = os.getenv('GOOGLE_API_KEY')
                if not api_key and key_name == 'openai':
                    api_key = os.getenv('OPENAI_API_KEY')

                if not api_key:
                    raise ValueError(f"API key for provider '{key_name}' not found")

        self.provider = self._initialize_provider(target)
        
        # Request tracking
        self.request_count = 0
        self.total_tokens = 0
        self.request_history: List[Dict[str, Any]] = []
        
        logger.info(f"Target AI wrapper initialized: {target}")
    
    def _initialize_provider(self, target: str) -> BaseAIProvider:
        """
        Initialize the appropriate provider based on target
        
        Args:
            target: Target AI identifier (e.g., openai-gpt4, gemini-pro, anthropic-claude)
        
        Returns:
            Initialized provider instance
        """
        target_lower = target.lower()
        
        # OpenAI and compatible providers
        if target_lower.startswith("openai"):
            if "-" in target:
                model = target.split("-", 1)[1]
                if model == "gpt3.5":
                    model = "gpt-3.5-turbo"
                elif model == "gpt4":
                    model = "gpt-4"
                elif model.startswith("gpt"):
                    model = f"gpt-{model.replace('gpt', '')}"
                elif not model.startswith("gpt-"):
                    model = f"gpt-{model}"
            else:
                model = "gpt-4"
            return OpenAIProvider(model=model)
        
        # Google Gemini
        elif target_lower.startswith("gemini"):
            if target_lower.endswith("vision"):
                model = "gemini-pro-vision"
            else:
                model = "gemini-pro"
            return GeminiProvider(model=model)
        
        # Anthropic Claude
        elif target_lower.startswith("anthropic"):
            model = target.split("-", 1)[1] if "-" in target else "claude-3-opus-20240229"
            return AnthropicProvider(model=model)
            
        # DeepSeek
        elif target_lower.startswith("deepseek"):
            model = target.split("-", 1)[1] if "-" in target else "deepseek-chat"
            return DeepSeekProvider(model=model)
        
        # Ollama (local models)
        elif target_lower.startswith("ollama"):
            model = target.split("-", 1)[1] if "-" in target else "llama2"
            return OllamaProvider(model=model)
        
        # Cohere
        elif target_lower.startswith("cohere"):
            model = target.split("-", 1)[1] if "-" in target else "command"
            return CohereProvider(model=model)
        
        # Groq
        elif target_lower.startswith("groq"):
            model = target.split("-", 1)[1] if "-" in target else "mixtral-8x7b-32768"
            return GroqProvider(model=model)
        
        # OpenRouter free models
        elif target_lower.startswith("openrouter"):
            # Default mappings (kept as sensible fallbacks)
            default_model_map = {
                "llama-3b": "meta-llama/llama-3.2-3b-instruct:free",
                "llama-1b": "meta-llama/llama-3.2-1b-instruct:free",
                "deepseek-r1": "deepseek/deepseek-r1-distill-qwen-32b:free",
                "qwen-7b": "qwen/qwen-2-7b-instruct:free",
                "gemma-7b": "google/gemma-7b-it:free",
                "mistral-7b": "mistralai/mistral-7b-instruct:free",
                "openchat": "openchat/openchat-7b:free",
                "nous-hermes": "nousresearch/nous-hermes-llama2-13b:free",

                # Added mappings from fetched OpenRouter reasoning models
                "nemotron-nano-12b-v2-vl": "nvidia/nemotron-nano-12b-v2-vl:free",
                "minimax-m2": "minimax/minimax-m2:free",
                "deepseek-v3": "deepseek/deepseek-chat-v3-0324:free",
                "gpt-oss-20b": "openai/gpt-oss-20b:free",
                "gemma-3-27b": "google/gemma-3-27b-it:free",
                "qwen3-14b": "qwen/qwen3-14b:free",
                "llama-3.2-3b": "meta-llama/llama-3.2-3b-instruct:free",
                "deepseek-r1-base": "deepseek/deepseek-r1:free",
                "mistral-7b": "mistralai/mistral-7b-instruct:free",
                "llama-3.3-70b": "meta-llama/llama-3.3-70b-instruct:free",
            }

            # Merge with any user-provided mappings from config
            cfg_map = self.config.get('target_ai', {}).get('openrouter_model_map', {}) or {}
            # Normalize keys: allow users to specify either 'llama-3b' or 'openrouter-llama-3b'
            normalized_cfg_map = {}
            for k, v in cfg_map.items():
                nk = k
                if k.startswith('openrouter-'):
                    nk = k.split('openrouter-', 1)[1]
                normalized_cfg_map[nk] = v

            model_map = {**default_model_map, **normalized_cfg_map}

            # Helper to resolve a candidate string (could be friendly key, full id, or prefixed)
            def resolve_candidate(candidate: str) -> str:
                if not candidate:
                    return ""
                # If candidate already looks like an OpenRouter model id (contains '/'), use directly
                if '/' in candidate:
                    return candidate
                # If prefixed like 'openrouter-foo', extract suffix
                if candidate.startswith('openrouter-'):
                    candidate = candidate.split('openrouter-', 1)[1]
                # Map via model_map if available
                if candidate in model_map:
                    return model_map[candidate]
                # As a last resort return the candidate unchanged
                return candidate

            # If the caller provided a specific openrouter-<key>, resolve that
            if '-' in target:
                model_key = target.split('-', 1)[1]
                model = resolve_candidate(model_key)
            else:
                # No suffix provided: pick first configured openrouter model, or fallback_model
                configured_list = self.config.get('target_ai', {}).get('openrouter_models', [])
                fallback_cfg = self.config.get('target_ai', {}).get('fallback_model')

                chosen = None
                if configured_list:
                    chosen = configured_list[0]
                elif fallback_cfg:
                    chosen = fallback_cfg

                model = resolve_candidate(chosen) if chosen else default_model_map.get('llama-3b')

            return OpenRouterProvider(model=model)
        
        else:
            raise ValueError(f"Unsupported target AI: {target}")
    
    def _interactive_select_model_for_openai(self) -> None:
        """Prompt the user to choose an OpenAI model when running interactively.

        Uses config['target_ai']['openai_models'] if present, otherwise a sensible
        default list. Sets the provider.model to the chosen value.
        """
        if not self._interactive_enabled:
            logger.debug("Interactive model selection skipped (not a TTY)")
            return

        if self._interactive_model_selected:
            return

        models = self.config.get('target_ai', {}).get('openai_models') or [
            'gpt-4', 'gpt-3.5-turbo', 'gpt-4o', 'gpt-4o-mini'
        ]

        print("\nAvailable OpenAI models:")
        for i, m in enumerate(models, start=1):
            print(f"  {i}. {m}")
        print("  0. Use default configured model")

        try:
            choice = input("Select model (number or name) [default 0]: ").strip()
        except EOFError:
            logger.debug("No stdin available for interactive model selection; using default model")
            self._interactive_model_selected = True
            return

        if not choice or choice == '0':
            logger.info("Using default OpenAI model configuration")
            self._interactive_model_selected = True
            return

        # If numeric, map to list
        selected = None
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                selected = models[idx]
        else:
            # Treat as model name if provided
            if choice in models:
                selected = choice
            else:
                # Accept arbitrary model name as provided by user
                selected = choice

        if selected:
            try:
                if isinstance(self.provider, OpenAIProvider):
                    logger.info(f"Interactive selection: setting OpenAI model to '{selected}'")
                    self.provider.model = selected
                else:
                    logger.info(f"Interactive selection ignored: current provider is not OpenAI ({type(self.provider)})")
            except Exception as e:
                logger.warning(f"Failed to set interactive model selection: {e}")

        self._interactive_model_selected = True

    def query(self, prompt: str, **kwargs) -> str:
        """
        Send a query to the target AI provider.
        
        Providers like OpenRouter handle key rotation and fallback internally.
        No automatic fallback to different models—use the chosen provider and model.
        """
        start_time = time.time()

        try:
            # If using OpenAI provider and interactive selection enabled, prompt once
            if isinstance(self.provider, OpenAIProvider) and not self._interactive_model_selected:
                self._interactive_select_model_for_openai()

            self._apply_rate_limit()
            response = self.provider.query(prompt, **kwargs)

            execution_time = time.time() - start_time
            self._track_request(prompt, response, execution_time)

            logger.debug(f"Query completed in {execution_time:.2f}s")
            return response

        except Exception as e:
            # Log error and re-raise; no fallback to different models
            logger.error(f"Query failed: {e}")
            raise
    
    async def query_async(self, prompt: str, **kwargs) -> str:
        """
        Send an async query to the target AI
        
        Args:
            prompt: User prompt
            **kwargs: Additional parameters
        
        Returns:
            AI response text
        """
        start_time = time.time()
        
        try:
            self._apply_rate_limit()
            response = await self.provider.query_async(prompt, **kwargs)
            
            execution_time = time.time() - start_time
            self._track_request(prompt, response, execution_time)
            
            logger.debug(f"Async query completed in {execution_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Async query failed: {e}")
            raise
    
    def _apply_rate_limit(self) -> None:
        """Apply rate limiting based on configuration"""
        max_rpm = self.config.get("target_ai", {}).get("rate_limit_requests_per_minute", 30)
        
        if len(self.request_history) >= max_rpm:
            oldest_request = self.request_history[0]
            time_since_oldest = time.time() - oldest_request["timestamp"]
            
            if time_since_oldest < 60:
                sleep_time = 60 - time_since_oldest
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            cutoff_time = time.time() - 60
            self.request_history = [
                r for r in self.request_history 
                if r["timestamp"] > cutoff_time
            ]
    
    def _track_request(self, prompt: str, response: str, execution_time: float) -> None:
        """Track request metrics"""
        self.request_count += 1
        
        prompt_tokens = len(prompt.split()) * 1.3
        response_tokens = len(response.split()) * 1.3
        total_tokens = prompt_tokens + response_tokens
        
        self.total_tokens += total_tokens
        
        request_data = {
            "timestamp": time.time(),
            "prompt_length": len(prompt),
            "response_length": len(response),
            "estimated_tokens": total_tokens,
            "execution_time": execution_time
        }
        
        self.request_history.append(request_data)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get usage metrics"""
        return {
            "total_requests": self.request_count,
            "total_tokens": self.total_tokens,
            "average_response_time": sum(r["execution_time"] for r in self.request_history) / 
                                    len(self.request_history) if self.request_history else 0,
            "requests_last_minute": len([
                r for r in self.request_history 
                if time.time() - r["timestamp"] < 60
            ])
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self.request_count = 0
        self.total_tokens = 0
        self.request_history = []
        logger.info("Metrics reset")
