"""Base interfaces for protocol clients and discovery strategies"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import httpx
import structlog
from datetime import datetime

from ..models import DiscoveredAgent, AgentStatus, ProtocolType, AgentCapability

logger = structlog.get_logger()


class DiscoveryStrategy(ABC):
    """Base class for protocol-specific discovery strategies"""
    
    @abstractmethod
    async def discover(self, container_info: Dict[str, Any]) -> Optional[DiscoveredAgent]:
        """Discover agent capabilities using protocol-specific methods"""
        pass
    
    @abstractmethod
    async def health_check(self, agent: DiscoveredAgent) -> AgentStatus:
        """Check agent health using protocol-specific methods"""
        pass
    
    async def extract_base_info(self, container_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract common information from container"""
        labels = container_info.get("Config", {}).get("Labels", {})
        if not labels:
            # Handle different container info formats
            labels = container_info.get("Labels", {})
        
        # Extract network info
        networks = container_info.get("NetworkSettings", {}).get("Networks", {})
        ip_address = None
        for network_name, network_info in networks.items():
            if network_info.get("IPAddress"):
                ip_address = network_info["IPAddress"]
                break
        
        # Extract container name
        names = container_info.get("Names", [])
        container_name = names[0].strip("/") if names else "unknown"
        
        return {
            "container_id": container_info.get("Id", "unknown"),
            "container_name": container_name,
            "protocol": labels.get("agent.protocol", "unknown"),
            "agent_type": labels.get("agent.type", "unknown"),
            "version": labels.get("agent.version", "0.0.0"),
            "port": self._extract_port(container_info),
            "ip_address": ip_address,
            "labels": labels
        }
    
    def _extract_port(self, container_info: Dict[str, Any]) -> Optional[int]:
        """Extract the first exposed port from container"""
        ports = container_info.get("Ports", [])
        for port_info in ports:
            # Check for public port mapping
            if port_info.get("PublicPort"):
                return port_info["PublicPort"]
            # Fallback to private port
            if port_info.get("PrivatePort"):
                return port_info["PrivatePort"]
        
        # Check in NetworkSettings if ports not found
        port_bindings = container_info.get("NetworkSettings", {}).get("Ports", {})
        for port_spec, bindings in port_bindings.items():
            if bindings and len(bindings) > 0:
                try:
                    return int(bindings[0].get("HostPort", "8000"))
                except (ValueError, TypeError):
                    continue
        
        return None  # No port found
    
    def _build_endpoint_url(self, base_info: Dict[str, Any]) -> str:
        """Build endpoint URL from container info"""
        container_name = base_info["container_name"]
        port = base_info["port"] or 8000
        
        # Use container name for Docker networking
        return f"http://{container_name}:{port}"


class ProtocolClient(ABC):
    """Base class for protocol-specific client implementations"""
    
    @abstractmethod
    async def execute(
        self, 
        agent: DiscoveredAgent, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Any:
        """Execute a request on the agent"""
        pass
    
    @abstractmethod 
    async def health_check(self, agent: DiscoveredAgent) -> bool:
        """Check if agent is healthy"""
        pass


class GenericDiscoveryStrategy(DiscoveryStrategy):
    """Fallback strategy for unknown protocols"""
    
    async def discover(self, container_info: Dict[str, Any]) -> Optional[DiscoveredAgent]:
        """Basic discovery using container labels and HTTP probing"""
        base_info = await self.extract_base_info(container_info)
        
        if not base_info["port"]:
            logger.warning(
                "No port found for container",
                container=base_info["container_name"]
            )
            return None
            
        endpoint = self._build_endpoint_url(base_info)
        
        # Try basic HTTP endpoint to see if service is responsive
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(endpoint)
                if response.status_code == 200:
                    
                    # Try to extract capabilities from container labels
                    capabilities = self._parse_label_capabilities(base_info["labels"])
                    
                    return DiscoveredAgent(
                        agent_id=f"generic-{base_info['container_name']}",
                        name=base_info["labels"].get("agent.name", base_info["container_name"]),
                        protocol=ProtocolType.CUSTOM,
                        endpoint=endpoint,
                        capabilities=capabilities,
                        status=AgentStatus.HEALTHY,
                        metadata={
                            "discovery_method": "generic",
                            "container_labels": base_info["labels"]
                        },
                        container_id=base_info["container_id"],
                        version=base_info["version"]
                    )
        except Exception as e:
            logger.debug(
                "Generic discovery probe failed", 
                error=str(e),
                container=base_info["container_name"]
            )
            
        return None
    
    async def health_check(self, agent: DiscoveredAgent) -> AgentStatus:
        """Basic HTTP health check"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                # Try standard health endpoint
                try:
                    response = await client.get(f"{agent.endpoint}/health")
                    if response.status_code == 200:
                        return AgentStatus.HEALTHY
                except httpx.RequestError:
                    pass
                
                # Fallback to root endpoint
                response = await client.get(agent.endpoint)
                if response.status_code == 200:
                    return AgentStatus.HEALTHY
                    
        except Exception as e:
            logger.debug(
                "Generic health check failed",
                agent_id=agent.agent_id,
                error=str(e)
            )
            
        return AgentStatus.UNKNOWN
    
    def _parse_label_capabilities(self, labels: Dict[str, str]) -> List[AgentCapability]:
        """Parse capabilities from container labels"""
        capabilities = []
        
        # Look for capabilities in labels
        cap_string = labels.get("agent.capabilities", "")
        if cap_string:
            for cap_name in cap_string.split(","):
                cap_name = cap_name.strip()
                if cap_name:
                    capability = AgentCapability(
                        name=cap_name,
                        description=f"Capability: {cap_name}",
                        tags=["container-label"]
                    )
                    capabilities.append(capability)
        
        # Add generic capability based on agent type
        agent_type = labels.get("agent.type", "")
        if agent_type and agent_type not in [cap.name for cap in capabilities]:
            capability = AgentCapability(
                name=agent_type,
                description=f"Agent type: {agent_type}",
                tags=["agent-type"]
            )
            capabilities.append(capability)
        
        return capabilities


class GenericProtocolClient(ProtocolClient):
    """Generic protocol client for unknown protocols"""
    
    async def execute(
        self, 
        agent: DiscoveredAgent, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Execute request via generic HTTP POST"""
        request_data = {
            "query": query,
            "context": context or {}
        }
        
        timeout_value = timeout or 30.0
        
        try:
            async with httpx.AsyncClient(timeout=timeout_value) as client:
                response = await client.post(
                    f"{agent.endpoint}/execute",
                    json=request_data
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise ValueError(f"Request failed with status {response.status_code}")
                    
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to agent: {str(e)}")
    
    async def health_check(self, agent: DiscoveredAgent) -> bool:
        """Check agent health"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{agent.endpoint}/health")
                return response.status_code == 200
        except:
            return False