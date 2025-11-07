"""
Tests for utility functions
"""

import pytest
import json
from pathlib import Path
from src.utils import (
    save_json,
    load_json,
    ensure_directory,
    sanitize_filename,
    get_api_key
)


class TestUtils:
    """Test suite for utility functions"""
    
    def test_save_and_load_json(self, temp_test_dir):
        """Test JSON save and load functions"""
        test_data = {"key": "value", "number": 42}
        test_file = temp_test_dir / "test.json"
        
        save_json(test_data, str(test_file))
        assert test_file.exists()
        
        loaded_data = load_json(str(test_file))
        assert loaded_data == test_data
    
    def test_load_json_not_found(self, temp_test_dir):
        """Test loading non-existent JSON file"""
        with pytest.raises(FileNotFoundError):
            load_json(str(temp_test_dir / "nonexistent.json"))
    
    def test_ensure_directory(self, temp_test_dir):
        """Test directory creation"""
        new_dir = temp_test_dir / "new" / "nested" / "dir"
        result = ensure_directory(str(new_dir))
        
        assert result.exists()
        assert result.is_dir()
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        dirty_name = 'test<file>:name?.txt'
        clean_name = sanitize_filename(dirty_name)
        
        assert '<' not in clean_name
        assert '>' not in clean_name
        assert ':' not in clean_name
        assert '?' not in clean_name
    
    def test_get_api_key_not_set(self):
        """Test getting API key when not set"""
        # This will return None if not set
        key = get_api_key("nonexistent_provider")
        assert key is None