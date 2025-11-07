"""
Logging configuration and utilities for O-SATE
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Optional
import yaml
from rich.logging import RichHandler


class OSATELogger:
    """Custom logger for O-SATE with enhanced formatting"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logging()
            self._initialized = True
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Load logging configuration
        config_path = Path("config/logging_config.yaml")
        
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                    logging.config.dictConfig(config)
            except Exception as e:
                print(f"Warning: Could not load logging config: {e}")
                self._setup_basic_logging()
        else:
            self._setup_basic_logging()
    
    def _setup_basic_logging(self):
        """Setup basic logging if config file not found"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                RichHandler(rich_tracebacks=True, markup=True),
                logging.FileHandler("logs/osate.log")
            ]
        )
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance"""
        return logging.getLogger(name)


# Singleton instance
_logger_instance = OSATELogger()


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    return _logger_instance.get_logger(name)


def set_log_level(level: str):
    """
    Set the global log level
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    logging.getLogger().setLevel(numeric_level)