"""ACP (Agent Connect Protocol) discovery strategy"""

import httpx
import structlog
from typing import Optional, Dict, Any, List

from .base import DiscoveryStrategy
from ..models import DiscoveredAgent, AgentStatus, AgentCapability, ProtocolType

logger = structlog.get_logger()


class ACPDiscoveryStrategy(DiscoveryStrategy):
    """Discovery strategy for ACP (Agent Connect Protocol) agents"""
    
    async def discover(self, container_info: Dict[str, Any]) -> Optional[DiscoveredAgent]:
        """Discover ACP agent using manifest and capability endpoints"""
        base_info = await self.extract_base_info(container_info)
        
        if not base_info["port"]:
            logger.warning(
                "No port found for ACP agent", 
                container=base_info["container_name"]
            )
            return None
        
        endpoint = self._build_endpoint_url(base_info)
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try to fetch capabilities (ACP standard endpoint)
                capabilities_data = await self._fetch_capabilities(client, endpoint)
                
                # Try to fetch schema for more details
                schema_data = await self._fetch_schema(client, endpoint)
                
                # Parse capabilities
                capabilities = self._parse_acp_capabilities(
                    capabilities_data,
                    schema_data
                )
                
                # Get agent name from capabilities or use container name
                agent_name = capabilities_data.get("name", base_info["container_name"])
                if not agent_name or agent_name == "unknown":
                    agent_name = base_info["labels"].get("agent.name", base_info["container_name"])
                
                return DiscoveredAgent(
                    agent_id=f"acp-{base_info['container_name']}",
                    name=agent_name,
                    protocol=ProtocolType.ACP,
                    endpoint=endpoint,
                    capabilities=capabilities,
                    status=AgentStatus.HEALTHY,
                    metadata={
                        "acp_version": capabilities_data.get("acp_version", "unknown"),
                        "auth_required": capabilities_data.get("auth", {}).get("required", False),
                        "streaming_supported": capabilities_data.get("streaming", False),
                        "discovery_method": "acp_native"
                    },
                    container_id=base_info["container_id"],
                    version=base_info["version"]
                )
                
        except Exception as e:
            logger.warning(
                "ACP native discovery failed, attempting fallback",
                error=str(e),
                container=base_info["container_name"]
            )
            
            # Fallback to container labels
            return self._fallback_discovery(base_info, endpoint)
    
    async def health_check(self, agent: DiscoveredAgent) -> AgentStatus:
        """Check ACP agent health using standard health endpoint"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{agent.endpoint}/health")
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "").lower()
                    
                    # Map ACP health status to our enum
                    if status == "healthy":
                        return AgentStatus.HEALTHY
                    elif status in ["degraded", "warning"]:
                        return AgentStatus.DEGRADED
                    elif status in ["unhealthy", "error", "critical"]:
                        return AgentStatus.UNHEALTHY
                    else:
                        # If status is present but unknown, assume healthy
                        return AgentStatus.HEALTHY if status else AgentStatus.UNKNOWN
                else:
                    return AgentStatus.UNHEALTHY
                    
        except Exception as e:
            logger.debug(
                "ACP health check failed",
                agent_id=agent.agent_id,
                error=str(e)
            )
            return AgentStatus.UNKNOWN
    
    async def _fetch_capabilities(self, client: httpx.AsyncClient, endpoint: str) -> Dict[str, Any]:
        """Fetch capabilities from ACP agent"""
        try:
            response = await client.get(f"{endpoint}/capabilities")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.debug("Failed to fetch capabilities", error=str(e))
        
        return {}
    
    async def _fetch_schema(self, client: httpx.AsyncClient, endpoint: str) -> Dict[str, Any]:
        """Fetch schema from ACP agent"""
        try:
            response = await client.get(f"{endpoint}/schema")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.debug("Failed to fetch schema", error=str(e))
        
        return {}
    
    def _parse_acp_capabilities(
        self,
        capabilities_data: Dict[str, Any],
        schema_data: Dict[str, Any]
    ) -> List[AgentCapability]:
        """Parse ACP capabilities into unified format"""
        capabilities = []
        
        # Extract from capabilities endpoint
        cap_list = capabilities_data.get("capabilities", [])
        for cap in cap_list:
            if isinstance(cap, dict):
                capability = AgentCapability(
                    name=cap.get("name", "unknown"),
                    description=cap.get("description", ""),
                    input_schema=cap.get("input_schema") or schema_data.get("input_schema"),
                    output_schema=cap.get("output_schema") or schema_data.get("output_schema"),
                    examples=cap.get("examples", []),
                    tags=["acp"] + cap.get("tags", [])
                )
                capabilities.append(capability)
            elif isinstance(cap, str):
                # Simple string capability
                capability = AgentCapability(
                    name=cap,
                    description=f"ACP capability: {cap}",
                    input_schema=schema_data.get("input_schema"),
                    output_schema=schema_data.get("output_schema"),
                    tags=["acp", "string-capability"]
                )
                capabilities.append(capability)
        
        # If no capabilities found in endpoint, try to infer from schema
        if not capabilities and schema_data:
            # Create a generic capability based on schema
            capability = AgentCapability(
                name="generic",
                description="Generic ACP agent capability",
                input_schema=schema_data.get("input_schema"),
                output_schema=schema_data.get("output_schema"),
                tags=["acp", "schema-inferred"]
            )
            capabilities.append(capability)
        
        return capabilities
    
    def _fallback_discovery(
        self,
        base_info: Dict[str, Any],
        endpoint: str
    ) -> Optional[DiscoveredAgent]:
        """Create agent from container labels when native discovery fails"""
        
        # Parse capabilities from labels
        capabilities = []
        cap_string = base_info["labels"].get("agent.capabilities", "")
        if cap_string:
            for cap_name in cap_string.split(","):
                cap_name = cap_name.strip()
                if cap_name:
                    capability = AgentCapability(
                        name=cap_name,
                        description=f"ACP capability: {cap_name}",
                        tags=["acp", "label-fallback"]
                    )
                    capabilities.append(capability)
        
        # If no capabilities in labels, create a generic one
        if not capabilities:
            capability = AgentCapability(
                name="unknown",
                description="ACP agent with unknown capabilities",
                tags=["acp", "fallback"]
            )
            capabilities.append(capability)
        
        return DiscoveredAgent(
            agent_id=f"acp-{base_info['container_name']}",
            name=base_info["labels"].get("agent.name", base_info["container_name"]),
            protocol=ProtocolType.ACP,
            endpoint=endpoint,
            capabilities=capabilities,
            status=AgentStatus.UNKNOWN,
            metadata={
                "discovery_method": "fallback",
                "acp_version": "unknown",
                "fallback_reason": "native_discovery_failed"
            },
            container_id=base_info["container_id"],
            version=base_info["version"]
        )