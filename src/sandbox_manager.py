"""
Docker sandbox manager for isolated AI testing
"""

import docker
from docker.models.containers import Container
from typing import Dict, Any, Optional
from pathlib import Path
import time
from .logger import get_logger
from .utils import load_config

logger = get_logger(__name__)


class SandboxManager:
    """Manages Docker containers for isolated AI testing"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize sandbox manager
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or load_config()
        self.sandbox_config = self.config.get('sandbox', {})
        
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except docker.errors.DockerException as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise
        
        self.active_containers: Dict[str, Container] = {}
    
    def create_sandbox(self, name: str = "osate-sandbox") -> Container:
        """
        Create a new sandbox container
        
        Args:
            name: Container name
        
        Returns:
            Docker container instance
        """
        logger.info(f"Creating sandbox container: {name}")
        
        try:
            # Remove existing container if it exists
            self._cleanup_container(name)
            
            # Container configuration
            container_config = {
                'image': 'osate:latest',
                'name': name,
                'detach': True,
                # Ensure container stays running so we can exec into it
                'command': ['tail', '-f', '/dev/null'],
                'network_mode': 'bridge',
                'mem_limit': self.sandbox_config.get('memory_limit', '2g'),
                'cpu_quota': int(self.sandbox_config.get('cpu_limit', 1.0) * 100000),
                'cap_drop': ['ALL'],
                'security_opt': ['no-new-privileges:true'],
                'read_only': self.sandbox_config.get('read_only_filesystem', True),
                'tmpfs': {'/tmp': '', '/app/temp': ''},
                'environment': {
                    'SANDBOX_MODE': 'true',
                    'LOG_LEVEL': 'INFO'
                }
            }
            
            # Create container
            container = self.docker_client.containers.run(**container_config)
            self.active_containers[name] = container
            
            logger.info(f"Sandbox container created: {container.id[:12]}")
            return container
            
        except docker.errors.ImageNotFound:
            logger.error("Docker image 'osate:latest' not found. Please build it first.")
            raise
        except docker.errors.APIError as e:
            logger.error(f"Docker API error: {e}")
            raise
    
    def execute_in_sandbox(
        self, 
        container: Container, 
        command: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a command in the sandbox container
        
        Args:
            container: Docker container
            command: Command to execute
            timeout: Execution timeout in seconds
        
        Returns:
            Execution result dictionary
        """
        timeout = timeout or self.sandbox_config.get('timeout_seconds', 300)
        
        logger.debug(f"Executing command in sandbox: {command[:100]}...")
        
        try:
            # Ensure container is running (avoid race where created container exits)
            try:
                container.reload()
                status = getattr(container, 'status', None)
                if status != 'running':
                    logger.info(f"Container {getattr(container, 'name', '')} not running (status={status}), starting it before exec")
                    try:
                        container.start()
                    except Exception as start_exc:
                        logger.warning(f"Failed to start container before exec: {start_exc}")
                    # wait briefly for container to reach running state
                    for _ in range(10):
                        time.sleep(0.2)
                        try:
                            container.reload()
                            if getattr(container, 'status', None) == 'running':
                                break
                        except Exception:
                            pass
            except Exception:
                # If reload/start not supported or fails, continue and let exec call handle errors
                logger.debug("Could not verify container running state before exec; proceeding to exec")

            start_time = time.time()
            
            exec_result = container.exec_run(
                cmd=command,
                stdout=True,
                stderr=True,
                demux=True
            )
            
            execution_time = time.time() - start_time

            # Parse exec_result.output robustly for demuxed or raw output
            stdout = ""
            stderr = ""
            out = getattr(exec_result, 'output', None)
            if isinstance(out, tuple):
                if out[0]:
                    try:
                        stdout = out[0].decode('utf-8')
                    except Exception:
                        stdout = str(out[0])
                if out[1]:
                    try:
                        stderr = out[1].decode('utf-8')
                    except Exception:
                        stderr = str(out[1])
            elif isinstance(out, (bytes, bytearray)):
                try:
                    stdout = out.decode('utf-8')
                except Exception:
                    stdout = str(out)
            else:
                # Some docker versions return ExecResult with .output as an object or None
                try:
                    stdout = str(out)
                except Exception:
                    stdout = ""

            exit_code = getattr(exec_result, 'exit_code', None)
            if exit_code is None and hasattr(exec_result, 'exit_status'):
                exit_code = getattr(exec_result, 'exit_status')

            result = {
                'exit_code': exit_code,
                'stdout': stdout,
                'stderr': stderr,
                'execution_time': execution_time,
                'success': exit_code == 0
            }
            
            logger.debug(f"Command executed in {execution_time:.2f}s with exit code {exit_code}")
            return result
            
        except docker.errors.APIError as e:
            logger.error(f"Error executing command in sandbox: {e}")
            return {
                'exit_code': -1,
                'stdout': "",
                'stderr': str(e),
                'execution_time': 0,
                'success': False
            }
    
    def stop_sandbox(self, name: str) -> None:
        """
        Stop a sandbox container
        
        Args:
            name: Container name
        """
        logger.info(f"Stopping sandbox container: {name}")
        
        if name in self.active_containers:
            try:
                container = self.active_containers[name]
                container.stop(timeout=10)
                logger.info(f"Container stopped: {name}")
            except docker.errors.APIError as e:
                logger.error(f"Error stopping container: {e}")
    
    def cleanup_sandbox(self, name: str) -> None:
        """
        Stop and remove a sandbox container
        
        Args:
            name: Container name
        """
        logger.info(f"Cleaning up sandbox container: {name}")
        self.stop_sandbox(name)
        self._cleanup_container(name)
    
    def _cleanup_container(self, name: str) -> None:
        """
        Remove a container if it exists
        
        Args:
            name: Container name
        """
        try:
            existing = self.docker_client.containers.get(name)
            existing.remove(force=True)
            logger.debug(f"Removed existing container: {name}")
        except docker.errors.NotFound:
            pass
        except docker.errors.APIError as e:
            logger.warning(f"Error removing container: {e}")
        
        if name in self.active_containers:
            del self.active_containers[name]
    
    def cleanup_all(self) -> None:
        """Stop and remove all active sandbox containers"""
        logger.info("Cleaning up all sandbox containers")
        
        for name in list(self.active_containers.keys()):
            self.cleanup_sandbox(name)
    
    def get_container_stats(self, name: str) -> Dict[str, Any]:
        """
        Get resource usage statistics for a container
        
        Args:
            name: Container name
        
        Returns:
            Statistics dictionary
        """
        if name not in self.active_containers:
            logger.warning(f"Container not found: {name}")
            return {}
        
        try:
            container = self.active_containers[name]
            stats = container.stats(stream=False)
            
            # Calculate CPU usage percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0
            
            # Calculate memory usage
            memory_usage = stats['memory_stats'].get('usage', 0)
            memory_limit = stats['memory_stats'].get('limit', 0)
            memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0.0
            
            return {
                'cpu_percent': cpu_percent,
                'memory_usage_mb': memory_usage / (1024 * 1024),
                'memory_limit_mb': memory_limit / (1024 * 1024),
                'memory_percent': memory_percent,
                'network_rx_bytes': stats['networks']['eth0']['rx_bytes'],
                'network_tx_bytes': stats['networks']['eth0']['tx_bytes']
            }
            
        except (docker.errors.APIError, KeyError) as e:
            logger.error(f"Error getting container stats: {e}")
            return {}
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup all containers"""
        self.cleanup_all()