"""
Utility functions for O-SATE
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv, find_dotenv
from .logger import get_logger

logger = get_logger(__name__)


def load_env_variables() -> None:
    """Load environment variables from .env file if present.

    Skip loading when running under pytest to avoid reintroducing values
    that tests explicitly remove from os.environ.
    """
    # If running under pytest, do not auto-load .env to keep tests deterministic
    if os.getenv('PYTEST_CURRENT_TEST') is not None:
        logger.debug('Running under pytest; skipping automatic .env load')
        return

    try:
        env_path = find_dotenv()
    except Exception:
        env_path = None

    if env_path:
        load_dotenv(env_path)
        logger.info(f"Environment variables loaded from {env_path}")
        return

    # Fallback to local .env in current working directory
    local_dotenv = Path(".env")
    if local_dotenv.exists():
        load_dotenv(local_dotenv)
        logger.info("Environment variables loaded from .env")
    else:
        logger.warning(".env file not found, using system environment variables")


def load_config(config_path: str = "config/default_config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        Configuration dictionary
    """
    # Ensure environment variables are loaded before using get_api_key or config
    load_env_variables()

    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration loaded from {config_path}")
        return config
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {e}")
        raise


def load_thresholds(threshold_path: str = "config/thresholds.yaml") -> Dict[str, Any]:
    """
    Load risk thresholds configuration
    
    Args:
        threshold_path: Path to thresholds file
    
    Returns:
        Thresholds dictionary
    """
    return load_config(threshold_path)


def save_json(data: Dict[str, Any], output_path: str, indent: int = 2) -> None:
    """
    Save data to JSON file
    
    Args:
        data: Data to save
        output_path: Output file path
        indent: JSON indentation level
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_file, "w") as f:
            json.dump(data, f, indent=indent)
        logger.info(f"Data saved to {output_path}")
    except Exception as e:
        logger.error(f"Error saving JSON file: {e}")
        raise


def load_json(input_path: str) -> Dict[str, Any]:
    """
    Load data from JSON file
    
    Args:
        input_path: Input file path
    
    Returns:
        Loaded data dictionary
    """
    input_file = Path(input_path)
    
    if not input_file.exists():
        logger.error(f"JSON file not found: {input_path}")
        raise FileNotFoundError(f"JSON file not found: {input_path}")
    
    try:
        with open(input_file, "r") as f:
            data = json.load(f)
        logger.info(f"Data loaded from {input_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file: {e}")
        raise


def get_api_key(provider: str) -> Optional[str]:
    """
    Get API key for a specific provider
    
    Args:
        provider: Provider name (openai, anthropic, google, deepseek, etc.)
    
    Returns:
        API key or None if not found
    """
    key_mapping = {
        # Original providers
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        
        # New providers
        "deepseek": "DEEPSEEK_API_KEY",
        "ollama": "OLLAMA_API_BASE",  # Ollama uses base URL, not API key
        "cohere": "COHERE_API_KEY",
        "huggingface": "HUGGINGFACE_API_KEY",
        "replicate": "REPLICATE_API_KEY",
        "together": "TOGETHER_API_KEY",
        "groq": "GROQ_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "perplexity": "PERPLEXITY_API_KEY",
        "anyscale": "ANYSCALE_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }
    
    env_var = key_mapping.get(provider.lower())
    if not env_var:
        logger.warning(f"Unknown provider: {provider}")
        return None
    
    api_key = os.getenv(env_var)
    if not api_key:
        logger.warning(f"API key not found for {provider} (${env_var})")
    
    return api_key


def get_api_keys(provider: str) -> list:
    """
    Get one or more API keys for a provider.

    Returns a list of keys. Environment variables may contain a single key
    or multiple comma-separated keys. This allows rotating across keys when
    hitting rate limits.
    """
    env_var = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'google': 'GOOGLE_API_KEY',
        'openrouter': 'OPENROUTER_API_KEY'
    }.get(provider.lower())

    keys = []
    if env_var:
        raw = os.getenv(env_var, '')
        if raw:
            # support comma-separated keys
            parts = [p.strip() for p in raw.split(',') if p.strip()]
            keys.extend(parts)

    # Also allow config file to supply keys under target_ai.api_keys
    try:
        cfg = load_config()
        api_keys_cfg = cfg.get('target_ai', {}).get('api_keys', {})
        provider_keys = api_keys_cfg.get(provider.lower())
        if provider_keys:
            if isinstance(provider_keys, list):
                keys.extend([k for k in provider_keys if k])
            elif isinstance(provider_keys, str):
                keys.extend([p.strip() for p in provider_keys.split(',') if p.strip()])
    except Exception:
        # If config not available or parsing fails, ignore and rely on env
        pass

    # Deduplicate while preserving order
    seen = set()
    result = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            result.append(k)

    return result


def ensure_directory(directory: str) -> Path:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        directory: Directory path
    
    Returns:
        Path object
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename
