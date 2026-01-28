"""Docker container log watcher"""
import asyncio
import re
from datetime import datetime
from typing import List, Callable, Awaitable, Optional
from .base import BaseWatcher, LogEvent
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

# Try to import docker, but make it optional
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    logger.warning("Docker SDK not available. Install with: pip install docker")


class DockerWatcher(BaseWatcher):
    """Watch Docker container logs for pattern matches"""
    
    def __init__(self, container_name: str, patterns: List[str],
                 callback: Callable[[LogEvent], Awaitable[None]],
                 follow_new_containers: bool = False):
        super().__init__(callback)
        self.container_name = container_name
        self.patterns = [re.compile(p) for p in patterns]
        self.follow_new_containers = follow_new_containers
        self.docker_client = None
        self.task = None
    
    async def start(self):
        """Start watching container logs"""
        if not DOCKER_AVAILABLE:
            logger.error("Cannot start DockerWatcher - Docker SDK not available")
            return
        
        try:
            self.docker_client = docker.from_env()
            logger.info(f"Docker client connected for watching: {self.container_name}")
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {e}")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._watch_container())
        logger.info(f"Started watching Docker container: {self.container_name}")
    
    async def stop(self):
        """Stop watching"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info(f"Stopped watching Docker container: {self.container_name}")
    
    async def _watch_container(self):
        """Main container log watching loop"""
        while self.running:
            try:
                # Find container
                container = None
                try:
                    # Try exact match first
                    container = self.docker_client.containers.get(self.container_name)
                except docker.errors.NotFound:
                    # Try partial match
                    containers = self.docker_client.containers.list(filters={"name": self.container_name})
                    if containers:
                        container = containers[0]
                
                if not container:
                    logger.warning(f"Container not found: {self.container_name}. Retrying in 30s...")
                    await asyncio.sleep(30)
                    continue
                
                logger.info(f"Watching logs for container: {container.name} ({container.short_id})")
                
                # Stream logs (this is blocking in a separate thread via run_in_executor)
                await self._stream_logs(container)
                
            except Exception as e:
                logger.error(f"Error in Docker watcher: {e}")
                await asyncio.sleep(10)
    
    async def _stream_logs(self, container):
        """Stream and process container logs"""
        try:
            # Get log stream (tail from now)
            log_stream = container.logs(stream=True, follow=True, timestamps=True)
            
            # Process logs in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            for log_line in log_stream:
                if not self.running:
                    break
                
                try:
                    # Decode log line
                    line = log_line.decode('utf-8').strip()
                    
                    # Parse timestamp if present (Docker format: 2026-01-28T04:00:00.000000000Z)
                    timestamp = datetime.utcnow()
                    if line and ' ' in line:
                        parts = line.split(' ', 1)
                        if 'T' in parts[0]:
                            try:
                                timestamp = datetime.fromisoformat(parts[0].replace('Z', '+00:00'))
                                line = parts[1] if len(parts) > 1 else line
                            except:
                                pass
                    
                    if not line:
                        continue
                    
                    # Check patterns
                    for pattern in self.patterns:
                        if pattern.search(line):
                            event = LogEvent(
                                source=f"docker://{container.name}",
                                message=line,
                                timestamp=timestamp,
                                matched_pattern=pattern.pattern
                            )
                            
                            # Schedule callback in the event loop
                            await self.callback(event)
                            break
                
                except Exception as e:
                    logger.error(f"Error processing log line: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error streaming logs from container: {e}")
