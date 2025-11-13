"""
TEST-AI: Comprehensive AI Safety Testing Platform
A comprehensive AI safety auditing framework
"""

__version__ = "0.1.0"
__author__ = "TEST-AI Contributors"
__license__ = "MIT"

from .logger import get_logger
from .utils import load_config

# Initialize package-level logger
logger = get_logger(__name__)
logger.info(f"TEST-AI v{__version__} initialized")
