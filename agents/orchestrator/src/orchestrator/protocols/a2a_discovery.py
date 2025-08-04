"""A2A (Agent-to-Agent) discovery strategy"""

import httpx
import structlog
from typing import Optional, Dict, Any, List

from .base import DiscoveryStrategy
from ..models import DiscoveredAgent, AgentStatus, AgentCapability, ProtocolType

logger = structlog.get_logger()


class A2ADiscoveryStrategy(DiscoveryStrategy):
    """Discovery strategy for A2A (Agent-to-Agent) protocol agents"""
    
    def __init__(self, registry_endpoint: Optional[str] = None):
        self.registry_endpoint = registry_endpoint
        # In a real implementation, this might connect to an A2A registry
        
    async def discover(self, container_info: Dict[str, Any]) -> Optional[DiscoveredAgent]:
        """Discover A2A agent using registry or peer discovery"""
        base_info = await self.extract_base_info(container_info)
        
        if not base_info["port"]:
            logger.warning(
                "No port found for A2A agent",
                container=base_info["container_name"]
            )
            return None
            
        endpoint = self._build_endpoint_url(base_info)
        
        try:
            # A2A agents typically register themselves or expose discovery endpoints
            agent_info = await self._query_a2a_agent(endpoint)
            
            if agent_info:
                capabilities = self._parse_a2a_capabilities(agent_info)
                
                return DiscoveredAgent(
                    agent_id=agent_info.get("agent_id", f"a2a-{base_info['container_name']}"),
                    name=agent_info.get("name", base_info["container_name"]),
                    protocol=ProtocolType.A2A,
                    endpoint=endpoint,
                    capabilities=capabilities,
                    status=AgentStatus.HEALTHY,
                    metadata={
                        "a2a_version": agent_info.get("protocol_version", "1.0"),
                        "peer_discovery": agent_info.get("supports_peer_discovery", True),
                        "message_formats": agent_info.get("message_formats", ["json"]),
                        "discovery_method": "a2a_native"
                    },
                    container_id=base_info["container_id"],
                    version=base_info["version"]
                )
            else:
                return self._fallback_discovery(base_info, endpoint)
                
        except Exception as e:
            logger.warning(
                "A2A native discovery failed, attempting fallback",
                error=str(e),
                container=base_info["container_name"]
            )
            return self._fallback_discovery(base_info, endpoint)
    
    async def health_check(self, agent: DiscoveredAgent) -> AgentStatus:
        """Check A2A agent health using protocol-specific ping"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                # A2A might use a different health check mechanism
                # Try A2A-style ping first
                ping_payload = {
                    "from": "orchestrator",
                    "type": "health_check",
                    "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
                }
                
                try:
                    response = await client.post(
                        f"{agent.endpoint}/ping",
                        json=ping_payload
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        status = data.get("status", "").lower()
                        
                        # Map A2A status responses
                        if status in ["alive", "active", "ready"]:
                            return AgentStatus.HEALTHY
                        elif status in ["busy", "degraded"]:
                            return AgentStatus.DEGRADED
                        elif status in ["dead", "inactive", "error"]:
                            return AgentStatus.UNHEALTHY
                        else:
                            return AgentStatus.HEALTHY if status else AgentStatus.UNKNOWN
                            
                except httpx.RequestError:
                    # Fallback to standard health endpoint
                    response = await client.get(f"{agent.endpoint}/health")
                    if response.status_code == 200:
                        return AgentStatus.HEALTHY
            
            return AgentStatus.UNHEALTHY
            
        except Exception as e:
            logger.debug(
                "A2A health check failed",
                agent_id=agent.agent_id,
                error=str(e)
            )
            return AgentStatus.UNKNOWN
    
    async def _query_a2a_agent(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Query A2A agent for its information using various discovery methods"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                
                # Method 1: Try A2A discovery endpoint
                try:
                    response = await client.get(f"{endpoint}/agent-info")
                    if response.status_code == 200:
                        return response.json()
                except httpx.RequestError:
                    pass
                
                # Method 2: Try A2A query action
                try:
                    response = await client.post(
                        f"{endpoint}/query",
                        json={"action": "describe_agent"}
                    )
                    if response.status_code == 200:
                        return response.json()
                except httpx.RequestError:
                    pass
                    
                # Method 3: Try A2A capabilities endpoint
                try:
                    response = await client.get(f"{endpoint}/capabilities")
                    if response.status_code == 200:
                        return response.json()
                except httpx.RequestError:
                    pass
                
                # Method 4: Try root endpoint for agent info
                try:
                    response = await client.get(endpoint)
                    if response.status_code == 200:
                        data = response.json()
                        # Check if it looks like A2A agent info
                        if any(key in data for key in ["agent_id", "services", "supported_actions"]):
                            return data
                except httpx.RequestError:
                    pass
                    
        except Exception as e:
            logger.debug("A2A agent query failed", error=str(e))
            
        return None
    
    def _parse_a2a_capabilities(self, agent_info: Dict[str, Any]) -> List[AgentCapability]:
        """Parse A2A capabilities into unified format"""
        capabilities = []
        
        # A2A might list capabilities as services
        services = agent_info.get("services", [])
        for service in services:
            if isinstance(service, dict):
                capability = AgentCapability(
                    name=service.get("name", "unknown"),
                    description=service.get("description", ""),
                    input_schema=service.get("input_format"),
                    output_schema=service.get("output_format"),
                    examples=service.get("examples", []),
                    tags=["a2a", "service"] + service.get("tags", [])
                )
                capabilities.append(capability)
            elif isinstance(service, str):
                capability = AgentCapability(
                    name=service,
                    description=f"A2A service: {service}",
                    tags=["a2a", "service"]
                )
                capabilities.append(capability)
        
        # Also check for actions (another A2A pattern)
        actions = agent_info.get("supported_actions", [])
        for action in actions:
            if isinstance(action, dict):
                capability = AgentCapability(
                    name=action.get("name", "unknown"),
                    description=action.get("description", f"Action: {action.get('name', 'unknown')}"),
                    input_schema=action.get("parameters"),
                    output_schema=action.get("response"),
                    tags=["a2a", "action"]
                )
                capabilities.append(capability)
            elif isinstance(action, str):
                capability = AgentCapability(
                    name=action,
                    description=f"A2A action: {action}",
                    tags=["a2a", "action"]
                )
                capabilities.append(capability)
        
        # Check for capabilities array
        caps = agent_info.get("capabilities", [])
        for cap in caps:
            if isinstance(cap, dict):
                capability = AgentCapability(
                    name=cap.get("name", "unknown"),
                    description=cap.get("description", ""),
                    input_schema=cap.get("input_schema"),
                    output_schema=cap.get("output_schema"),
                    examples=cap.get("examples", []),
                    tags=["a2a"] + cap.get("tags", [])
                )
                capabilities.append(capability)
            elif isinstance(cap, str):
                capability = AgentCapability(
                    name=cap,
                    description=f"A2A capability: {cap}",
                    tags=["a2a"]
                )
                capabilities.append(capability)
        
        return capabilities
    
    def _fallback_discovery(
        self,
        base_info: Dict[str, Any],
        endpoint: str
    ) -> Optional[DiscoveredAgent]:
        """Fallback discovery for A2A agents using container labels"""
        
        # Parse capabilities from labels
        capabilities = []
        cap_string = base_info["labels"].get("agent.capabilities", "")
        if cap_string:
            for cap_name in cap_string.split(","):
                cap_name = cap_name.strip()
                if cap_name:
                    capability = AgentCapability(
                        name=cap_name,
                        description=f"A2A capability: {cap_name}",
                        tags=["a2a", "label-fallback"]
                    )
                    capabilities.append(capability)
        
        # Add generic A2A capability if none found
        if not capabilities:
            capability = AgentCapability(
                name="unknown",
                description="A2A agent with unknown capabilities",
                tags=["a2a", "fallback"]
            )
            capabilities.append(capability)
        
        return DiscoveredAgent(
            agent_id=f"a2a-{base_info['container_name']}",
            name=base_info["labels"].get("agent.name", base_info["container_name"]),
            protocol=ProtocolType.A2A,
            endpoint=endpoint,
            capabilities=capabilities,
            status=AgentStatus.UNKNOWN,
            metadata={
                "discovery_method": "fallback",
                "a2a_version": "unknown",
                "fallback_reason": "native_discovery_failed"
            },
            container_id=base_info["container_id"],
            version=base_info["version"]
        )