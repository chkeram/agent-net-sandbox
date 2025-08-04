# Multi-Protocol Discovery Strategy for Orchestrator

## Overview

This document details the unified discovery strategy that enables the orchestrator to discover and communicate with agents across different protocols (ACP, A2A, MCP) while respecting each protocol's native discovery mechanisms.

## Discovery Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Unified Discovery Service                  │
├─────────────────────────────────────────────────────────────┤
│  Container Discovery Layer (Docker)                         │
│  ├── Scan for labeled containers                           │
│  └── Extract protocol hints                                │
├─────────────────────────────────────────────────────────────┤
│  Protocol-Specific Discovery Strategies                     │
│  ├── ACP Discovery (Manifest + Endpoints)                  │
│  ├── A2A Discovery (Registry + Peer-to-Peer)              │
│  ├── MCP Discovery (Tools + Resources)                     │
│  └── Generic Discovery (Fallback)                          │
├─────────────────────────────────────────────────────────────┤
│  Unified Agent Registry                                     │
│  └── Normalized agent information                          │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. Base Discovery Interface

```python
# discovery.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import structlog
from .models import DiscoveredAgent, AgentStatus, ProtocolType

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
        labels = container_info.get("Labels", {})
        
        return {
            "container_id": container_info.get("Id"),
            "container_name": container_info.get("Names", ["/unknown"])[0].strip("/"),
            "protocol": labels.get("agent.protocol", "unknown"),
            "agent_type": labels.get("agent.type", "unknown"),
            "version": labels.get("agent.version", "0.0.0"),
            "port": self._extract_port(container_info),
            "labels": labels
        }
    
    def _extract_port(self, container_info: Dict[str, Any]) -> Optional[int]:
        """Extract the first exposed port from container"""
        ports = container_info.get("Ports", [])
        for port in ports:
            if port.get("PublicPort"):
                return port["PublicPort"]
        return None
```

### 2. ACP Discovery Strategy

```python
# protocols/acp_discovery.py
import httpx
import yaml
import json
from typing import Optional, Dict, Any
from ..discovery import DiscoveryStrategy
from ..models import DiscoveredAgent, AgentStatus, AgentCapability, ProtocolType

class ACPDiscoveryStrategy(DiscoveryStrategy):
    """Discovery strategy for ACP (Agent Connect Protocol) agents"""
    
    async def discover(self, container_info: Dict[str, Any]) -> Optional[DiscoveredAgent]:
        """Discover ACP agent using manifest and capability endpoints"""
        base_info = await self.extract_base_info(container_info)
        
        if not base_info["port"]:
            logger.warning("No port found for ACP agent", container=base_info["container_name"])
            return None
        
        endpoint = f"http://{base_info['container_name']}:8000"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try to fetch capabilities (ACP standard endpoint)
                capabilities_response = await client.get(f"{endpoint}/capabilities")
                capabilities_data = capabilities_response.json()
                
                # Try to fetch schema for more details
                schema_response = await client.get(f"{endpoint}/schema")
                schema_data = schema_response.json()
                
                # Parse capabilities
                capabilities = self._parse_acp_capabilities(
                    capabilities_data,
                    schema_data
                )
                
                return DiscoveredAgent(
                    agent_id=f"acp-{base_info['container_name']}",
                    name=capabilities_data.get("name", base_info["container_name"]),
                    protocol=ProtocolType.ACP,
                    endpoint=endpoint,
                    capabilities=capabilities,
                    status=AgentStatus.HEALTHY,
                    metadata={
                        "acp_version": capabilities_data.get("acp_version", "0"),
                        "auth_required": capabilities_data.get("auth", {}).get("required", False),
                        "streaming_supported": capabilities_data.get("streaming", False)
                    },
                    container_id=base_info["container_id"],
                    version=base_info["version"]
                )
                
        except Exception as e:
            logger.error("ACP discovery failed", error=str(e), container=base_info["container_name"])
            
            # Fallback to container labels
            return self._fallback_discovery(base_info, endpoint)
    
    async def health_check(self, agent: DiscoveredAgent) -> AgentStatus:
        """Check ACP agent health"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{agent.endpoint}/health")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "healthy":
                        return AgentStatus.HEALTHY
                    elif data.get("status") == "degraded":
                        return AgentStatus.DEGRADED
                    else:
                        return AgentStatus.UNHEALTHY
                else:
                    return AgentStatus.UNHEALTHY
                    
        except Exception:
            return AgentStatus.UNKNOWN
    
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
                    input_schema=schema_data.get("input_schema"),
                    output_schema=schema_data.get("output_schema")
                )
                capabilities.append(capability)
            elif isinstance(cap, str):
                # Simple string capability
                capability = AgentCapability(
                    name=cap,
                    description=f"Supports {cap}",
                    input_schema=schema_data.get("input_schema"),
                    output_schema=schema_data.get("output_schema")
                )
                capabilities.append(capability)
        
        return capabilities
    
    def _fallback_discovery(
        self,
        base_info: Dict[str, Any],
        endpoint: str
    ) -> DiscoveredAgent:
        """Create agent from container labels when discovery fails"""
        # Parse capabilities from labels
        cap_string = base_info["labels"].get("agent.capabilities", "")
        capabilities = []
        
        if cap_string:
            for cap_name in cap_string.split(","):
                capabilities.append(AgentCapability(
                    name=cap_name.strip(),
                    description=f"Capability: {cap_name.strip()}"
                ))
        
        return DiscoveredAgent(
            agent_id=f"acp-{base_info['container_name']}",
            name=base_info["labels"].get("agent.name", base_info["container_name"]),
            protocol=ProtocolType.ACP,
            endpoint=endpoint,
            capabilities=capabilities,
            status=AgentStatus.UNKNOWN,
            metadata={"discovery_method": "fallback"},
            container_id=base_info["container_id"],
            version=base_info["version"]
        )
```

### 3. A2A Discovery Strategy

```python
# protocols/a2a_discovery.py
from typing import Optional, Dict, Any, List
from ..discovery import DiscoveryStrategy
from ..models import DiscoveredAgent, AgentStatus, AgentCapability, ProtocolType

class A2ADiscoveryStrategy(DiscoveryStrategy):
    """Discovery strategy for A2A (Agent-to-Agent) protocol agents"""
    
    def __init__(self, registry_endpoint: Optional[str] = None):
        self.registry_endpoint = registry_endpoint
        # In a real implementation, this might connect to an A2A registry
        
    async def discover(self, container_info: Dict[str, Any]) -> Optional[DiscoveredAgent]:
        """Discover A2A agent using registry or peer discovery"""
        base_info = await self.extract_base_info(container_info)
        
        if not base_info["port"]:
            return None
            
        endpoint = f"http://{base_info['container_name']}:8000"
        
        try:
            # A2A agents typically register themselves
            # For now, we'll simulate discovery
            agent_info = await self._query_a2a_agent(endpoint)
            
            if agent_info:
                return DiscoveredAgent(
                    agent_id=agent_info.get("agent_id", f"a2a-{base_info['container_name']}"),
                    name=agent_info.get("name", base_info["container_name"]),
                    protocol=ProtocolType.A2A,
                    endpoint=endpoint,
                    capabilities=self._parse_a2a_capabilities(agent_info),
                    status=AgentStatus.HEALTHY,
                    metadata={
                        "a2a_version": agent_info.get("protocol_version", "1.0"),
                        "peer_discovery": agent_info.get("supports_peer_discovery", True),
                        "message_formats": agent_info.get("message_formats", ["json"])
                    },
                    container_id=base_info["container_id"],
                    version=base_info["version"]
                )
            else:
                return self._fallback_discovery(base_info, endpoint)
                
        except Exception as e:
            logger.error("A2A discovery failed", error=str(e))
            return self._fallback_discovery(base_info, endpoint)
    
    async def health_check(self, agent: DiscoveredAgent) -> AgentStatus:
        """Check A2A agent health using protocol-specific ping"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                # A2A might use a different health check mechanism
                response = await client.post(
                    f"{agent.endpoint}/ping",
                    json={"from": "orchestrator", "type": "health_check"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "alive":
                        return AgentStatus.HEALTHY
                        
            return AgentStatus.UNHEALTHY
            
        except Exception:
            return AgentStatus.UNKNOWN
    
    async def _query_a2a_agent(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Query A2A agent for its information"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # A2A agents might expose a discovery endpoint
                response = await client.get(f"{endpoint}/agent-info")
                if response.status_code == 200:
                    return response.json()
                    
                # Try alternative A2A discovery method
                response = await client.post(
                    f"{endpoint}/query",
                    json={"action": "describe_agent"}
                )
                if response.status_code == 200:
                    return response.json()
                    
        except Exception:
            pass
            
        return None
    
    def _parse_a2a_capabilities(self, agent_info: Dict[str, Any]) -> List[AgentCapability]:
        """Parse A2A capabilities into unified format"""
        capabilities = []
        
        # A2A might list capabilities differently
        services = agent_info.get("services", [])
        for service in services:
            capability = AgentCapability(
                name=service.get("name", "unknown"),
                description=service.get("description", ""),
                input_schema=service.get("input_format"),
                output_schema=service.get("output_format"),
                examples=service.get("examples", [])
            )
            capabilities.append(capability)
        
        # Also check for actions (another A2A pattern)
        actions = agent_info.get("supported_actions", [])
        for action in actions:
            if isinstance(action, str):
                capability = AgentCapability(
                    name=action,
                    description=f"Action: {action}"
                )
                capabilities.append(capability)
        
        return capabilities
    
    def _fallback_discovery(
        self,
        base_info: Dict[str, Any],
        endpoint: str
    ) -> DiscoveredAgent:
        """Fallback discovery for A2A agents"""
        return DiscoveredAgent(
            agent_id=f"a2a-{base_info['container_name']}",
            name=base_info["container_name"],
            protocol=ProtocolType.A2A,
            endpoint=endpoint,
            capabilities=[],
            status=AgentStatus.UNKNOWN,
            metadata={"discovery_method": "fallback"},
            container_id=base_info["container_id"],
            version=base_info["version"]
        )
```

### 4. MCP Discovery Strategy

```python
# protocols/mcp_discovery.py
from typing import Optional, Dict, Any, List
from ..discovery import DiscoveryStrategy
from ..models import DiscoveredAgent, AgentStatus, AgentCapability, ProtocolType

class MCPDiscoveryStrategy(DiscoveryStrategy):
    """Discovery strategy for MCP (Model Context Protocol) agents"""
    
    async def discover(self, container_info: Dict[str, Any]) -> Optional[DiscoveredAgent]:
        """Discover MCP agent tools and resources"""
        base_info = await self.extract_base_info(container_info)
        
        if not base_info["port"]:
            return None
            
        endpoint = f"http://{base_info['container_name']}:8000"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # MCP exposes tools and resources
                tools_response = await client.get(f"{endpoint}/tools")
                tools = tools_response.json() if tools_response.status_code == 200 else []
                
                resources_response = await client.get(f"{endpoint}/resources")
                resources = resources_response.json() if resources_response.status_code == 200 else []
                
                # Get server info
                info_response = await client.get(f"{endpoint}/")
                server_info = info_response.json() if info_response.status_code == 200 else {}
                
                capabilities = self._parse_mcp_capabilities(tools, resources)
                
                return DiscoveredAgent(
                    agent_id=f"mcp-{base_info['container_name']}",
                    name=server_info.get("name", base_info["container_name"]),
                    protocol=ProtocolType.MCP,
                    endpoint=endpoint,
                    capabilities=capabilities,
                    status=AgentStatus.HEALTHY,
                    metadata={
                        "mcp_version": server_info.get("version", "1.0"),
                        "tools_count": len(tools),
                        "resources_count": len(resources),
                        "supports_streaming": server_info.get("supports_streaming", False)
                    },
                    container_id=base_info["container_id"],
                    version=base_info["version"]
                )
                
        except Exception as e:
            logger.error("MCP discovery failed", error=str(e))
            return None
    
    async def health_check(self, agent: DiscoveredAgent) -> AgentStatus:
        """Check MCP agent health"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{agent.endpoint}/health")
                if response.status_code == 200:
                    return AgentStatus.HEALTHY
                    
            return AgentStatus.UNHEALTHY
        except Exception:
            return AgentStatus.UNKNOWN
    
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
                description=tool.get('description', ''),
                input_schema=tool.get('parameters'),
                output_schema=tool.get('returns')
            )
            capabilities.append(capability)
        
        # Convert resources to capabilities
        for resource in resources:
            capability = AgentCapability(
                name=f"resource:{resource.get('name', 'unknown')}",
                description=resource.get('description', ''),
                input_schema={"resource_id": "string"},
                output_schema=resource.get('schema')
            )
            capabilities.append(capability)
        
        return capabilities
```

### 5. Unified Discovery Service

```python
# discovery.py (continued)
import asyncio
import docker
from typing import Dict, List, Optional, Type
from datetime import datetime, timedelta

class UnifiedDiscoveryService:
    """Unified discovery service that orchestrates protocol-specific strategies"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.strategies: Dict[ProtocolType, DiscoveryStrategy] = {
            ProtocolType.ACP: ACPDiscoveryStrategy(),
            ProtocolType.A2A: A2ADiscoveryStrategy(),
            ProtocolType.MCP: MCPDiscoveryStrategy(),
        }
        self.agent_registry: Dict[str, DiscoveredAgent] = {}
        self.discovery_interval = 30  # seconds
        self._discovery_task = None
        self._running = False
        
    async def start(self):
        """Start the discovery service"""
        self._running = True
        self._discovery_task = asyncio.create_task(self._discovery_loop())
        # Do initial discovery
        await self.refresh()
        
    async def stop(self):
        """Stop the discovery service"""
        self._running = False
        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass
    
    async def _discovery_loop(self):
        """Continuous discovery loop"""
        while self._running:
            try:
                await asyncio.sleep(self.discovery_interval)
                await self.refresh()
            except Exception as e:
                logger.error("Discovery loop error", error=str(e))
    
    async def refresh(self):
        """Refresh the agent registry"""
        logger.info("Starting agent discovery")
        
        try:
            # Get all containers in the agent network
            containers = self.docker_client.containers.list(
                filters={"network": "agent-network"}
            )
            
            # Discover agents from containers
            discovered_agents = []
            for container in containers:
                agent = await self._discover_container(container)
                if agent:
                    discovered_agents.append(agent)
            
            # Update registry
            new_registry = {}
            for agent in discovered_agents:
                # Check health
                agent.status = await self._check_agent_health(agent)
                agent.last_health_check = datetime.utcnow()
                new_registry[agent.agent_id] = agent
            
            self.agent_registry = new_registry
            logger.info(f"Discovery complete. Found {len(new_registry)} agents")
            
        except Exception as e:
            logger.error("Discovery refresh failed", error=str(e))
    
    async def _discover_container(self, container) -> Optional[DiscoveredAgent]:
        """Discover agent from a container"""
        try:
            # Get container info
            container_info = container.attrs
            
            # Extract protocol from labels
            labels = container_info.get("Config", {}).get("Labels", {})
            protocol_str = labels.get("agent.protocol", "").lower()
            
            # Skip non-agent containers
            if not protocol_str or protocol_str == "orchestrator":
                return None
            
            # Get appropriate strategy
            try:
                protocol = ProtocolType(protocol_str)
                strategy = self.strategies.get(protocol)
            except ValueError:
                # Unknown protocol, use generic discovery
                strategy = GenericDiscoveryStrategy()
                protocol = ProtocolType.CUSTOM
            
            if strategy:
                agent = await strategy.discover(container_info)
                return agent
                
        except Exception as e:
            logger.error(
                "Failed to discover container",
                container_id=container.id[:12],
                error=str(e)
            )
            
        return None
    
    async def _check_agent_health(self, agent: DiscoveredAgent) -> AgentStatus:
        """Check agent health using protocol-specific method"""
        strategy = self.strategies.get(agent.protocol)
        if strategy:
            return await strategy.health_check(agent)
        return AgentStatus.UNKNOWN
    
    async def get_all_agents(self) -> List[DiscoveredAgent]:
        """Get all discovered agents"""
        return list(self.agent_registry.values())
    
    async def get_healthy_agents(self) -> List[DiscoveredAgent]:
        """Get only healthy agents"""
        return [
            agent for agent in self.agent_registry.values()
            if agent.status == AgentStatus.HEALTHY
        ]
    
    async def get_agent(self, agent_id: str) -> Optional[DiscoveredAgent]:
        """Get specific agent by ID"""
        return self.agent_registry.get(agent_id)
    
    async def get_agents_by_protocol(
        self,
        protocol: ProtocolType
    ) -> List[DiscoveredAgent]:
        """Get agents using specific protocol"""
        return [
            agent for agent in self.agent_registry.values()
            if agent.protocol == protocol
        ]
    
    async def is_healthy(self) -> bool:
        """Check if discovery service is healthy"""
        return self._running and len(self.agent_registry) > 0


class GenericDiscoveryStrategy(DiscoveryStrategy):
    """Fallback strategy for unknown protocols"""
    
    async def discover(self, container_info: Dict[str, Any]) -> Optional[DiscoveredAgent]:
        """Basic discovery using container labels only"""
        base_info = await self.extract_base_info(container_info)
        
        if not base_info["port"]:
            return None
            
        endpoint = f"http://{base_info['container_name']}:8000"
        
        # Try basic HTTP endpoint
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(endpoint)
                if response.status_code == 200:
                    return DiscoveredAgent(
                        agent_id=f"custom-{base_info['container_name']}",
                        name=base_info["container_name"],
                        protocol=ProtocolType.CUSTOM,
                        endpoint=endpoint,
                        capabilities=[],
                        status=AgentStatus.UNKNOWN,
                        metadata={"discovery_method": "generic"},
                        container_id=base_info["container_id"],
                        version=base_info["version"]
                    )
        except:
            pass
            
        return None
    
    async def health_check(self, agent: DiscoveredAgent) -> AgentStatus:
        """Basic HTTP health check"""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{agent.endpoint}/health")
                if response.status_code == 200:
                    return AgentStatus.HEALTHY
        except:
            pass
        return AgentStatus.UNKNOWN
```

## Docker Label Standards

To support unified discovery, all agents should use these Docker labels:

```yaml
labels:
  # Required
  - "agent.protocol=acp"           # Protocol type: acp, a2a, mcp, custom
  - "agent.type=hello-world"       # Agent type/function
  
  # Recommended
  - "agent.version=0.1.0"          # Agent version
  - "agent.capabilities=greeting,multilingual"  # Comma-separated capabilities
  - "agent.name=ACP Hello World"   # Human-readable name
  
  # Optional hints for discovery
  - "agent.discovery.endpoint=/capabilities"    # Where to find capabilities
  - "agent.discovery.health=/health"           # Health check endpoint
  - "agent.discovery.port=8000"                # Primary port if multiple
```

## Benefits of This Approach

1. **Protocol Respect**: Each protocol's native discovery is preserved
2. **Unified Interface**: Single registry for all agents
3. **Fallback Support**: Container labels provide baseline discovery
4. **Extensibility**: Easy to add new protocols
5. **Performance**: Async discovery with caching
6. **Resilience**: Health checks and status tracking

## Example Usage

```python
# In the orchestrator
discovery_service = UnifiedDiscoveryService()
await discovery_service.start()

# Get all healthy agents
healthy_agents = await discovery_service.get_healthy_agents()

# Get agents by protocol
acp_agents = await discovery_service.get_agents_by_protocol(ProtocolType.ACP)

# Refresh discovery
await discovery_service.refresh()
```

This unified discovery approach enables the orchestrator to work seamlessly with multiple protocols while respecting their individual discovery philosophies.