"""Auto-discovery of running services"""
import subprocess
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

# Try to import docker
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


@dataclass
class DiscoveredService:
    """Discovered service information"""
    name: str
    service_type: str  # docker, systemd, process
    identifier: str  # container_id, unit_name, pid
    status: str
    metadata: Dict[str, Any]


class ServiceDiscovery:
    """Discover running services automatically"""
    
    def __init__(self):
        self.docker_client = None
        if DOCKER_AVAILABLE:
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                logger.warning(f"Could not connect to Docker for discovery: {e}")
    
    async def discover_all(self) -> List[DiscoveredService]:
        """Discover all services"""
        services = []
        
        # Discover Docker containers
        docker_services = await self.discover_docker_containers()
        services.extend(docker_services)
        
        # Discover systemd services
        systemd_services = await self.discover_systemd_services()
        services.extend(systemd_services)
        
        logger.info(f"Discovered {len(services)} services total")
        return services
    
    async def discover_docker_containers(self) -> List[DiscoveredService]:
        """Discover running Docker containers"""
        if not self.docker_client:
            return []
        
        try:
            containers = self.docker_client.containers.list(all=True)
            services = []
            
            for container in containers:
                service = DiscoveredService(
                    name=container.name,
                    service_type="docker",
                    identifier=container.id,
                    status=container.status,
                    metadata={
                        "short_id": container.short_id,
                        "image": container.image.tags[0] if container.image.tags else "unknown",
                        "created": container.attrs.get('Created'),
                        "ports": container.ports,
                        "labels": container.labels
                    }
                )
                services.append(service)
            
            logger.info(f"Discovered {len(services)} Docker containers")
            return services
        
        except Exception as e:
            logger.error(f"Failed to discover Docker containers: {e}")
            return []
    
    async def discover_systemd_services(self) -> List[DiscoveredService]:
        """Discover systemd services"""
        try:
            # List all systemd services
            cmd = ["systemctl", "list-units", "--type=service", "--all", "--no-legend", "--no-pager"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return []
            
            services = []
            for line in result.stdout.strip().split('\n'):
                if not line.strip():
                    continue
                
                parts = line.split()
                if len(parts) < 4:
                    continue
                
                unit_name = parts[0]
                load_state = parts[1]
                active_state = parts[2]
                sub_state = parts[3]
                
                # Only include loaded services
                if load_state == "loaded":
                    service = DiscoveredService(
                        name=unit_name,
                        service_type="systemd",
                        identifier=unit_name,
                        status=f"{active_state}/{sub_state}",
                        metadata={
                            "load_state": load_state,
                            "active_state": active_state,
                            "sub_state": sub_state
                        }
                    )
                    services.append(service)
            
            logger.info(f"Discovered {len(services)} systemd services")
            return services
        
        except Exception as e:
            logger.error(f"Failed to discover systemd services: {e}")
            return []
    
    async def find_service_by_name(self, name: str) -> Optional[DiscoveredService]:
        """Find a specific service by name"""
        all_services = await self.discover_all()
        
        for service in all_services:
            if name.lower() in service.name.lower():
                return service
        
        return None
    
    async def get_docker_container_by_name(self, name: str) -> Optional[Any]:
        """Get Docker container object by name"""
        if not self.docker_client:
            return None
        
        try:
            # Try exact match
            try:
                return self.docker_client.containers.get(name)
            except docker.errors.NotFound:
                pass
            
            # Try partial match
            containers = self.docker_client.containers.list(filters={"name": name})
            if containers:
                return containers[0]
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get Docker container: {e}")
            return None
