"""
O-SATE: Open-Source AI Threat Evaluator
A comprehensive AI safety auditing framework
"""

__version__ = "0.1.0"
__author__ = "O-SATE Contributors"
__license__ = "MIT"

from .logger import get_logger
from .utils import load_config

# Initialize package-level logger
logger = get_logger(__name__)
logger.info(f"O-SATE v{__version__} initialized")
