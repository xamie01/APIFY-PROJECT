"""
Tests for target AI wrapper
"""

import pytest
from src.target_ai_wrapper import TargetAIWrapper


class TestTargetAIWrapper:
    """Test suite for TargetAIWrapper"""
    
    def test_wrapper_initialization_error(self, test_config):
        """Test wrapper initialization without API keys"""
        with pytest.raises(ValueError):
            wrapper = TargetAIWrapper("openai-gpt4", test_config)
    
    def test_unsupported_provider(self, test_config):
        """Test initialization with unsupported provider"""
        with pytest.raises(ValueError, match="Unsupported target AI"):
            wrapper = TargetAIWrapper("unsupported-model", test_config)
    
    def test_query_tracking(self, mock_ai_wrapper):
        """Test that queries are tracked properly"""
        initial_count = mock_ai_wrapper.request_count
        
        mock_ai_wrapper.query("Test prompt")
        mock_ai_wrapper.query("Another test")
        
        assert mock_ai_wrapper.request_count == initial_count + 2
        assert len(mock_ai_wrapper.responses) == 2
    
    def test_get_metrics(self, mock_ai_wrapper):
        """Test metrics collection"""
        mock_ai_wrapper.query("Test 1")
        mock_ai_wrapper.query("Test 2")
        mock_ai_wrapper.query("Test 3")
        
        metrics = mock_ai_wrapper.get_metrics()
        
        assert metrics["total_requests"] == 3
        assert "average_response_time" in metrics