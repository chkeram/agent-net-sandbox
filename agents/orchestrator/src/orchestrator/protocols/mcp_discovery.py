"""MCP (Model Context Protocol) discovery strategy"""

import httpx
import structlog
from typing import Optional, Dict, Any, List

from .base import DiscoveryStrategy
from ..models import DiscoveredAgent, AgentStatus, AgentCapability, ProtocolType

logger = structlog.get_logger()


class MCPDiscoveryStrategy(DiscoveryStrategy):
    """Discovery strategy for MCP (Model Context Protocol) agents"""
    
    async def discover(self, container_info: Dict[str, Any]) -> Optional[DiscoveredAgent]:
        """Discover MCP agent tools and resources"""
        base_info = await self.extract_base_info(container_info)
        
        if not base_info["port"]:
            logger.warning(
                "No port found for MCP agent",
                container=base_info["container_name"]
            )
            return None
            
        endpoint = self._build_endpoint_url(base_info)
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # MCP exposes tools and resources
                tools = await self._fetch_tools(client, endpoint)
                resources = await self._fetch_resources(client, endpoint)
                
                # Get server info
                server_info = await self._fetch_server_info(client, endpoint)
                
                capabilities = self._parse_mcp_capabilities(tools, resources)
                
                # Get agent name from server info or use container name
                agent_name = server_info.get("name", base_info["container_name"])
                if not agent_name or agent_name == "unknown":
                    agent_name = base_info["labels"].get("agent.name", base_info["container_name"])
                
                return DiscoveredAgent(
                    agent_id=f"mcp-{base_info['container_name']}",
                    name=agent_name,
                    protocol=ProtocolType.MCP,
                    endpoint=endpoint,
                    capabilities=capabilities,
                    status=AgentStatus.HEALTHY,
                    metadata={
                        "mcp_version": server_info.get("version", "unknown"),
                        "tools_count": len(tools),
                        "resources_count": len(resources),
                        "supports_streaming": server_info.get("supports_streaming", False),
                        "discovery_method": "mcp_native"
                    },
                    container_id=base_info["container_id"],
                    version=base_info["version"]
                )
                
        except Exception as e:
            logger.warning(
                "MCP native discovery failed, attempting fallback",
                error=str(e),
                container=base_info["container_name"]
            )
            return self._fallback_discovery(base_info, endpoint)
    
    async def health_check(self, agent: DiscoveredAgent) -> AgentStatus:
        """Check MCP agent health"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                # Try MCP-specific health endpoint
                try:
                    response = await client.get(f"{agent.endpoint}/health")
                    if response.status_code == 200:
                        data = response.json()
                        status = data.get("status", "").lower()
                        
                        if status == "healthy":
                            return AgentStatus.HEALTHY
                        elif status in ["degraded", "warning"]:
                            return AgentStatus.DEGRADED
                        elif status in ["unhealthy", "error"]:
                            return AgentStatus.UNHEALTHY
                        else:
                            # If response is 200 but no clear status, assume healthy
                            return AgentStatus.HEALTHY
                except httpx.RequestError:
                    pass
                
                # Fallback: check if tools endpoint is accessible
                try:
                    response = await client.get(f"{agent.endpoint}/tools")
                    if response.status_code == 200:
                        return AgentStatus.HEALTHY
                except httpx.RequestError:
                    pass
                
                # Final fallback: check root endpoint
                response = await client.get(agent.endpoint)
                if response.status_code == 200:
                    return AgentStatus.HEALTHY
                    
            return AgentStatus.UNHEALTHY
        except Exception as e:
            logger.debug(
                "MCP health check failed",
                agent_id=agent.agent_id,
                error=str(e)
            )
            return AgentStatus.UNKNOWN
    
    async def _fetch_tools(self, client: httpx.AsyncClient, endpoint: str) -> List[Dict[str, Any]]:
        """Fetch available tools from MCP agent"""
        try:
            response = await client.get(f"{endpoint}/tools")
            if response.status_code == 200:
                data = response.json()
                # Handle both direct array and wrapped response
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "tools" in data:
                    return data["tools"]
        except Exception as e:
            logger.debug("Failed to fetch MCP tools", error=str(e))
        
        return []
    
    async def _fetch_resources(self, client: httpx.AsyncClient, endpoint: str) -> List[Dict[str, Any]]:
        """Fetch available resources from MCP agent"""
        try:
            response = await client.get(f"{endpoint}/resources")
            if response.status_code == 200:
                data = response.json()
                # Handle both direct array and wrapped response
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "resources" in data:
                    return data["resources"]
        except Exception as e:
            logger.debug("Failed to fetch MCP resources", error=str(e))
        
        return []
    
    async def _fetch_server_info(self, client: httpx.AsyncClient, endpoint: str) -> Dict[str, Any]:
        """Fetch server information from MCP agent"""
        try:
            response = await client.get(f"{endpoint}/")
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.debug("Failed to fetch MCP server info", error=str(e))
        
        return {}
    
    def _parse_mcp_capabilities(
        self,
        tools: List[Dict[str, Any]],
        resources: List[Dict[str, Any]]
    ) -> List[AgentCapability]:
        """Parse MCP tools and resources into capabilities"""
        capabilities = []
        
        # Convert tools to capabilities
        for tool in tools:
            capability = AgentCapability(
                name=f"tool:{tool.get('name', 'unknown')}",
                description=tool.get('description', f"MCP tool: {tool.get('name', 'unknown')}"),
                input_schema=tool.get('parameters'),
                output_schema=tool.get('returns'),
                examples=tool.get('examples', []),
                tags=["mcp", "tool"] + tool.get("tags", [])
            )
            capabilities.append(capability)
        
        # Convert resources to capabilities
        for resource in resources:
            capability = AgentCapability(
                name=f"resource:{resource.get('name', 'unknown')}",
                description=resource.get('description', f"MCP resource: {resource.get('name', 'unknown')}"),
                input_schema={"resource_id": "string"},
                output_schema=resource.get('schema'),
                examples=resource.get('examples', []),
                tags=["mcp", "resource"] + resource.get("tags", [])
            )
            capabilities.append(capability)
        
        # If no tools or resources found, create a generic MCP capability
        if not capabilities:
            capability = AgentCapability(
                name="mcp-server",
                description="MCP server with unknown tools/resources",
                tags=["mcp", "generic"]
            )
            capabilities.append(capability)
        
        return capabilities
    
    def _fallback_discovery(
        self,
        base_info: Dict[str, Any],
        endpoint: str
    ) -> Optional[DiscoveredAgent]:
        """Fallback discovery for MCP agents using container labels"""
        
        # Parse capabilities from labels
        capabilities = []
        cap_string = base_info["labels"].get("agent.capabilities", "")
        if cap_string:
            for cap_name in cap_string.split(","):
                cap_name = cap_name.strip()
                if cap_name:
                    capability = AgentCapability(
                        name=cap_name,
                        description=f"MCP capability: {cap_name}",
                        tags=["mcp", "label-fallback"]
                    )
                    capabilities.append(capability)
        
        # Add generic MCP capability if none found
        if not capabilities:
            capability = AgentCapability(
                name="unknown",
                description="MCP agent with unknown capabilities",
                tags=["mcp", "fallback"]
            )
            capabilities.append(capability)
        
        return DiscoveredAgent(
            agent_id=f"mcp-{base_info['container_name']}",
            name=base_info["labels"].get("agent.name", base_info["container_name"]),
            protocol=ProtocolType.MCP,
            endpoint=endpoint,
            capabilities=capabilities,
            status=AgentStatus.UNKNOWN,
            metadata={
                "discovery_method": "fallback",
                "mcp_version": "unknown",
                "fallback_reason": "native_discovery_failed"
            },
            container_id=base_info["container_id"],
            version=base_info["version"]
        )