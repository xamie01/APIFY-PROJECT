"""
Tests for logging functionality
"""

import pytest
import logging
from pathlib import Path
from src.logger import get_logger, set_log_level


class TestLogger:
    """Test suite for logging"""
    
    def test_get_logger(self):
        """Test getting a logger instance"""
        logger = get_logger(__name__)
        assert logger is not None
        assert isinstance(logger, logging.Logger)
    
    def test_set_log_level(self):
        """Test setting log level"""
        set_log_level("DEBUG")
        logger = get_logger(__name__)
        assert logger.getEffectiveLevel() <= logging.DEBUG
        
        set_log_level("INFO")
        assert logger.getEffectiveLevel() <= logging.INFO
    
    def test_invalid_log_level(self):
        """Test setting invalid log level"""
        with pytest.raises(ValueError):
            set_log_level("INVALID")
    
    def test_logger_output(self, caplog):
        """Test logger actually logs messages"""
        logger = get_logger(__name__)
        
        with caplog.at_level(logging.INFO):
            logger.info("Test message")
        
        assert "Test message" in caplog.text
