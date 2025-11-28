"""Utilities package for O-SATE - expose helper modules for easy imports"""

import importlib.util
import pathlib

# Dynamically load the top-level utils.py as a distinct module to avoid
# name collision between the package and module named `src.utils`.
_utils_path = pathlib.Path(__file__).parent.parent / 'utils.py'
_spec = importlib.util.spec_from_file_location('src._utils_module', str(_utils_path))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# Re-export commonly used functions from utils.py
load_config = getattr(_mod, 'load_config')
load_env_variables = getattr(_mod, 'load_env_variables')
get_api_key = getattr(_mod, 'get_api_key')
get_api_keys = getattr(_mod, 'get_api_keys')
ensure_directory = getattr(_mod, 'ensure_directory')
sanitize_filename = getattr(_mod, 'sanitize_filename')
save_json = getattr(_mod, 'save_json')
load_json = getattr(_mod, 'load_json')

# Import submodules in this package normally
from .env import get_api_keys as env_get_api_keys, get_single_key
from .queue_manager import QueueManager
from .rate_limiter import RateLimiter
from .reporter import Reporter
from .apify_helpers import load_prompts_from_storage

# Expose names
__all__ = [
    'load_config', 'load_env_variables', 'get_api_key', 'get_api_keys', 'ensure_directory', 'sanitize_filename',
    'save_json', 'load_json', 'get_single_key', 'QueueManager', 'RateLimiter', 'Reporter', 'load_prompts_from_storage'
]
