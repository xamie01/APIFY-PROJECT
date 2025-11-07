"""
Tests for sandbox manager
"""

import pytest
import docker
from src.sandbox_manager import SandboxManager


@pytest.mark.sandbox
class TestSandboxManager:
    """Test suite for SandboxManager"""
    
    def test_sandbox_initialization(self, test_config):
        """Test sandbox manager initialization"""
        manager = SandboxManager(test_config)
        assert manager is not None
        assert manager.docker_client is not None
        assert isinstance(manager.active_containers, dict)
        manager.cleanup_all()
    
    @pytest.mark.slow
    def test_create_sandbox(self, sandbox_manager):
        """Test creating a sandbox container"""
        try:
            container = sandbox_manager.create_sandbox("test-sandbox-1")
            
            assert container is not None
            assert "test-sandbox-1" in sandbox_manager.active_containers
            assert container.status in ["running", "created"]
        except docker.errors.ImageNotFound:
            pytest.skip("Docker image 'osate:latest' not built yet")
    
    @pytest.mark.slow
    def test_execute_in_sandbox(self, sandbox_manager):
        """Test executing commands in sandbox"""
        try:
            container = sandbox_manager.create_sandbox("test-sandbox-2")
            
            result = sandbox_manager.execute_in_sandbox(
                container, 
                "echo 'Hello World'"
            )
            
            assert result["success"] is True
            assert result["exit_code"] == 0
            assert "Hello World" in result["stdout"]
        except docker.errors.ImageNotFound:
            pytest.skip("Docker image 'osate:latest' not built yet")
    
    def test_cleanup_sandbox(self, sandbox_manager):
        """Test sandbox cleanup"""
        try:
            container = sandbox_manager.create_sandbox("test-sandbox-cleanup")
            container_id = container.id
            
            sandbox_manager.cleanup_sandbox("test-sandbox-cleanup")
            
            assert "test-sandbox-cleanup" not in sandbox_manager.active_containers
            
            # Verify container is removed
            with pytest.raises(docker.errors.NotFound):
                sandbox_manager.docker_client.containers.get(container_id)
        except docker.errors.ImageNotFound:
            pytest.skip("Docker image 'osate:latest' not built yet")
    
    def test_context_manager(self, test_config):
        """Test using sandbox manager as context manager"""
        with SandboxManager(test_config) as manager:
            assert manager is not None
        
        assert len(manager.active_containers) == 0

