"""Service management executor"""
import time
import subprocess
import asyncio
from typing import Dict, Any, Optional
from .base import BaseExecutor, ExecutionResult
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

# Try to import docker, but make it optional
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    logger.warning("Docker SDK not available. Install with: pip install docker")


class ServiceRestartExecutor(BaseExecutor):
    """Restart services (Docker, systemd, K8s)"""
    
    def __init__(self, dry_run: bool = False, max_retries: int = 3):
        super().__init__(dry_run, max_retries)
        self.docker_client = None
        if DOCKER_AVAILABLE:
            try:
                self.docker_client = docker.from_env()
                logger.info("Docker client initialized successfully")
            except Exception as e:
                logger.warning(f"Could not connect to Docker: {e}")
    
    async def execute(self, parameters: Dict[str, Any]) -> ExecutionResult:
        """Execute service restart"""
        start_time = time.time()
        
        service_name = parameters.get("service_name", "app")
        service_type = parameters.get("service_type", "docker")  # docker, systemd, k8s
        grace_period = parameters.get("grace_period", 5)
        container_id = parameters.get("container_id")  # Optional: specific container ID
        
        if self.dry_run:
            return ExecutionResult(
                success=True,
                message=f"[DRY RUN] Would restart {service_type} service: {service_name}",
                duration_seconds=time.time() - start_time
            )
        
        try:
            logger.info(f"Restarting {service_type} service: {service_name}")
            
            if service_type == "docker":
                return await self._restart_docker_container(service_name, container_id, grace_period, start_time)
            elif service_type == "systemd":
                return await self._restart_systemd_service(service_name, start_time)
            elif service_type == "k8s":
                return await self._restart_k8s_pod(service_name, start_time)
            else:
                return ExecutionResult(
                    success=False,
                    message=f"Unknown service type: {service_type}",
                    error=f"Supported types: docker, systemd, k8s",
                    duration_seconds=time.time() - start_time
                )
        
        except Exception as e:
            logger.error(f"Service restart failed: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                message=f"Failed to restart {service_name}",
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def _restart_docker_container(self, service_name: str, container_id: Optional[str], 
                                       grace_period: int, start_time: float) -> ExecutionResult:
        """Restart a Docker container"""
        if not self.docker_client:
            return ExecutionResult(
                success=False,
                message="Docker client not available",
                error="Docker SDK not installed or Docker daemon not running",
                duration_seconds=time.time() - start_time
            )
        
        try:
            # Find container by ID or name
            container = None
            if container_id:
                container = self.docker_client.containers.get(container_id)
            else:
                # Try to find by name
                containers = self.docker_client.containers.list(filters={"name": service_name})
                if containers:
                    container = containers[0]
            
            if not container:
                return ExecutionResult(
                    success=False,
                    message=f"Container not found: {service_name}",
                    error="No container found with that name or ID",
                    duration_seconds=time.time() - start_time
                )
            
            # Check if container is running
            container.reload()
            original_status = container.status
            
            # Restart the container
            logger.info(f"Restarting Docker container: {container.name} (ID: {container.short_id})")
            container.restart(timeout=grace_period)
            
            # Wait a moment and verify it's running
            await asyncio.sleep(2)
            container.reload()
            
            success = container.status == "running"
            
            return ExecutionResult(
                success=success,
                message=f"Restarted Docker container: {container.name}",
                output=f"Container: {container.name}, ID: {container.short_id}, Status: {original_status} → {container.status}",
                duration_seconds=time.time() - start_time
            )
        
        except docker.errors.NotFound:
            return ExecutionResult(
                success=False,
                message=f"Container not found: {service_name}",
                error="Container does not exist",
                duration_seconds=time.time() - start_time
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Docker restart failed: {service_name}",
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def _restart_systemd_service(self, service_name: str, start_time: float) -> ExecutionResult:
        """Restart a systemd service"""
        try:
            # Check if service exists
            check_cmd = ["systemctl", "list-units", "--all", service_name, "--no-legend"]
            check_result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=5)
            
            if not check_result.stdout.strip():
                return ExecutionResult(
                    success=False,
                    message=f"Systemd service not found: {service_name}",
                    error="Service does not exist",
                    duration_seconds=time.time() - start_time
                )
            
            # Restart the service
            restart_cmd = ["systemctl", "restart", service_name]
            result = subprocess.run(restart_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Verify service is active
                await asyncio.sleep(2)
                status_cmd = ["systemctl", "is-active", service_name]
                status_result = subprocess.run(status_cmd, capture_output=True, text=True, timeout=5)
                
                is_active = status_result.stdout.strip() == "active"
                
                return ExecutionResult(
                    success=is_active,
                    message=f"Restarted systemd service: {service_name}",
                    output=f"Service: {service_name}, Active: {is_active}",
                    duration_seconds=time.time() - start_time
                )
            else:
                return ExecutionResult(
                    success=False,
                    message=f"Failed to restart systemd service: {service_name}",
                    error=result.stderr or "systemctl restart failed",
                    duration_seconds=time.time() - start_time
                )
        
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                message=f"Systemd restart timeout: {service_name}",
                error="Command timed out after 30 seconds",
                duration_seconds=time.time() - start_time
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Systemd restart failed: {service_name}",
                error=str(e),
                duration_seconds=time.time() - start_time
            )
    
    async def _restart_k8s_pod(self, service_name: str, start_time: float) -> ExecutionResult:
        """Restart a Kubernetes pod (delete and let controller recreate)"""
        # This would require kubernetes Python client
        # For now, return a placeholder that it's not implemented
        return ExecutionResult(
            success=False,
            message="Kubernetes restart not yet implemented",
            error="Install kubernetes Python client and implement K8s API calls",
            duration_seconds=time.time() - start_time
        )


# Try to import psutil, but make it optional
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available. Install with: pip install psutil")


class ProcessKillExecutor(BaseExecutor):
    """Kill processes using psutil"""
    
    def __init__(self, dry_run: bool = False, max_retries: int = 3):
        super().__init__(dry_run, max_retries)
        self.psutil_available = PSUTIL_AVAILABLE
    
    async def execute(self, parameters: Dict[str, Any]) -> ExecutionResult:
        """Execute process kill"""
        start_time = time.time()
        
        process_name = parameters.get("process_name")
        pid = parameters.get("pid")
        signal_type = parameters.get("signal", "SIGTERM")  # SIGTERM or SIGKILL
        timeout = parameters.get("timeout", 10)  # Wait N seconds for graceful shutdown
        
        if not process_name and not pid:
            return ExecutionResult(
                success=False,
                message="Must provide either process_name or pid",
                error="Missing required parameter",
                duration_seconds=time.time() - start_time
            )
        
        if self.dry_run:
            return ExecutionResult(
                success=True,
                message=f"[DRY RUN] Would kill process: {process_name or pid}",
                duration_seconds=time.time() - start_time
            )
        
        if not self.psutil_available:
            return ExecutionResult(
                success=False,
                message="psutil not available",
                error="Install psutil library for process management",
                duration_seconds=time.time() - start_time
            )
        
        try:
            processes_killed = []
            
            # Find processes to kill
            processes = []
            if pid:
                # Kill specific PID
                try:
                    proc = psutil.Process(pid)
                    processes.append(proc)
                except psutil.NoSuchProcess:
                    return ExecutionResult(
                        success=False,
                        message=f"Process not found: PID {pid}",
                        error="No such process",
                        duration_seconds=time.time() - start_time
                    )
            else:
                # Find by name
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if proc.info['name'] == process_name or \
                           (proc.info['cmdline'] and process_name in ' '.join(proc.info['cmdline'])):
                            processes.append(proc)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            
            if not processes:
                return ExecutionResult(
                    success=False,
                    message=f"No processes found matching: {process_name or pid}",
                    error="Process not found",
                    duration_seconds=time.time() - start_time
                )
            
            # Kill processes (graceful then forceful)
            for proc in processes:
                try:
                    proc_info = f"PID {proc.pid}, Name: {proc.name()}"
                    logger.info(f"Terminating process: {proc_info}")
                    
                    if signal_type == "SIGKILL":
                        # Immediate kill
                        proc.kill()
                        processes_killed.append(proc_info)
                    else:
                        # Graceful termination (SIGTERM)
                        proc.terminate()
                        
                        # Wait for process to terminate
                        try:
                            proc.wait(timeout=timeout)
                            processes_killed.append(proc_info)
                        except psutil.TimeoutExpired:
                            # Force kill if still running
                            logger.warning(f"Process {proc.pid} did not terminate, forcing kill")
                            proc.kill()
                            proc.wait(timeout=5)
                            processes_killed.append(f"{proc_info} (forced)")
                
                except psutil.NoSuchProcess:
                    logger.info(f"Process {proc.pid} already terminated")
                    processes_killed.append(f"PID {proc.pid} (already dead)")
                except psutil.AccessDenied:
                    return ExecutionResult(
                        success=False,
                        message=f"Access denied: Cannot kill PID {proc.pid}",
                        error="Insufficient permissions",
                        duration_seconds=time.time() - start_time
                    )
            
            return ExecutionResult(
                success=True,
                message=f"Killed {len(processes_killed)} process(es)",
                output=f"Processes killed: {', '.join(processes_killed)}",
                duration_seconds=time.time() - start_time
            )
        
        except Exception as e:
            logger.error(f"Process kill failed: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                message=f"Failed to kill process",
                error=str(e),
                duration_seconds=time.time() - start_time
            )
